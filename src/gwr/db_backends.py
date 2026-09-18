from __future__ import annotations

from contextlib import contextmanager
from typing import Any
import re


def qmark_to_format(sql: str) -> str:
    # Runtime SQL is controlled and contains no literal question-mark operators.
    return sql.replace("?", "%s")


def postgres_base_schema_from_sqlite(sqlite_schema: str) -> str:
    lines=[]
    for line in sqlite_schema.splitlines():
        stripped=line.strip()
        if not stripped or stripped.startswith("PRAGMA "):
            continue
        if stripped.startswith("CREATE TRIGGER IF NOT EXISTS audit_no_update"):
            continue
        if stripped.startswith("CREATE TRIGGER IF NOT EXISTS audit_no_delete"):
            continue
        if stripped.startswith("CREATE TRIGGER IF NOT EXISTS revision_content_immutable"):
            continue
        lines.append(line)
    schema="\n".join(lines)
    # PostgreSQL reserves WINDOW as a keyword. SQLite accepts it unquoted in
    # the loopguards table, so quote only the schema identifier while keeping
    # the persisted column name and SELECT * row contract unchanged.
    schema=re.sub(r"\\bwindow\\s+TEXT\\s+NOT\\s+NULL", '"window" TEXT NOT NULL', schema, flags=re.IGNORECASE)
    return schema


POSTGRES_GUARD_DDL = r'''
CREATE OR REPLACE FUNCTION gwr_reject_audit_mutation() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit_events are append-only';
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS audit_no_update ON audit_events;
CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit_events FOR EACH ROW EXECUTE FUNCTION gwr_reject_audit_mutation();
DROP TRIGGER IF EXISTS audit_no_delete ON audit_events;
CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit_events FOR EACH ROW EXECUTE FUNCTION gwr_reject_audit_mutation();

CREATE OR REPLACE FUNCTION gwr_revision_immutable() RETURNS trigger AS $$
BEGIN
  IF NEW.structured_payload IS DISTINCT FROM OLD.structured_payload OR
     NEW.content_hash IS DISTINCT FROM OLD.content_hash OR
     NEW.artifact_id IS DISTINCT FROM OLD.artifact_id OR
     NEW.revision_number IS DISTINCT FROM OLD.revision_number OR
     NEW.created_by_actor_id IS DISTINCT FROM OLD.created_by_actor_id OR
     NEW.created_at IS DISTINCT FROM OLD.created_at OR
     NEW.supersedes_revision_id IS DISTINCT FROM OLD.supersedes_revision_id THEN
    RAISE EXCEPTION 'revision content is immutable';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS revision_content_immutable ON revisions;
CREATE TRIGGER revision_content_immutable BEFORE UPDATE ON revisions FOR EACH ROW EXECUTE FUNCTION gwr_revision_immutable();
'''


def _safe_identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"unsafe PostgreSQL identifier: {value!r}")
    return value


class PostgresConnectionFacade:
    def __init__(self, raw): self.raw=raw
    def execute(self, sql: str, params=()):
        cur=self.raw.cursor(); cur.execute(qmark_to_format(sql), params); return cur
    def commit(self): self.raw.commit()
    def rollback(self): self.raw.rollback()
    def executescript(self, script: str):
        # Canonical migrations intentionally contain simple DDL only. PL/pgSQL
        # guard functions are installed separately as full statements.
        cur=self.raw.cursor()
        for stmt in script.split(";"):
            if stmt.strip(): cur.execute(stmt)
        return cur


class PostgresDatabase:
    backend_name="postgresql"
    def __init__(self, url: str, *, namespace: str | None = None, reset_namespace: bool = False):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except Exception as exc:
            raise RuntimeError("PostgreSQL backend requires psycopg>=3; install the production database extra") from exc
        self._psycopg=psycopg
        self._raw=psycopg.connect(url,row_factory=dict_row)
        self.namespace=_safe_identifier(namespace) if namespace else None
        if self.namespace:
            cur=self._raw.cursor()
            if reset_namespace:
                cur.execute(f'DROP SCHEMA IF EXISTS "{self.namespace}" CASCADE')
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{self.namespace}"')
            cur.execute(f'SET search_path TO "{self.namespace}"')
            self._raw.commit()
        self.conn=PostgresConnectionFacade(self._raw)
        from .db import SCHEMA
        base=postgres_base_schema_from_sqlite(SCHEMA)
        self.conn.executescript(base)
        self._raw.commit()
        # Install PL/pgSQL guards as independent statements. Psycopg's extended
        # protocol deliberately rejects multi-command prepared statements, so do
        # not depend on a monolithic script execution here.
        self._install_guards()
        self._raw.commit()
        from .migrations import MigrationManager
        self.migrations=MigrationManager(self); self.migrations.apply_all()
    def _install_guards(self):
        cur=self._raw.cursor()
        cur.execute(r"""
CREATE OR REPLACE FUNCTION gwr_reject_audit_mutation() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit_events are append-only';
END;
$$ LANGUAGE plpgsql
""")
        cur.execute("DROP TRIGGER IF EXISTS audit_no_update ON audit_events")
        cur.execute("CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit_events FOR EACH ROW EXECUTE FUNCTION gwr_reject_audit_mutation()")
        cur.execute("DROP TRIGGER IF EXISTS audit_no_delete ON audit_events")
        cur.execute("CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit_events FOR EACH ROW EXECUTE FUNCTION gwr_reject_audit_mutation()")
        cur.execute(r"""
CREATE OR REPLACE FUNCTION gwr_revision_immutable() RETURNS trigger AS $$
BEGIN
  IF NEW.structured_payload IS DISTINCT FROM OLD.structured_payload OR
     NEW.content_hash IS DISTINCT FROM OLD.content_hash OR
     NEW.artifact_id IS DISTINCT FROM OLD.artifact_id OR
     NEW.revision_number IS DISTINCT FROM OLD.revision_number OR
     NEW.created_by_actor_id IS DISTINCT FROM OLD.created_by_actor_id OR
     NEW.created_at IS DISTINCT FROM OLD.created_at OR
     NEW.supersedes_revision_id IS DISTINCT FROM OLD.supersedes_revision_id THEN
    RAISE EXCEPTION 'revision content is immutable';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql
""")
        cur.execute("DROP TRIGGER IF EXISTS revision_content_immutable ON revisions")
        cur.execute("CREATE TRIGGER revision_content_immutable BEFORE UPDATE ON revisions FOR EACH ROW EXECUTE FUNCTION gwr_revision_immutable()")

    @contextmanager
    def tx(self):
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback(); raise
    def one(self, sql, params=()):
        cur=self.conn.execute(sql,params); return cur.fetchone()
    def all(self, sql, params=()):
        cur=self.conn.execute(sql,params); return cur.fetchall()
    def list_tables(self) -> list[str]:
        rows=self.all("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname=current_schema() ORDER BY tablename")
        return [r["tablename"] for r in rows]
    def close(self): self._raw.close()
