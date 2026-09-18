from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import hashlib

from .utils import utcnow


@dataclass(frozen=True)
class Migration:
    migration_id: str
    sql: str

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.sql.encode("utf-8")).hexdigest()


MIGRATIONS = [
    Migration(
        "0001_v05_production_foundation",
        """
CREATE TABLE IF NOT EXISTS object_refs(
  ref_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  owner_kind TEXT NOT NULL,
  owner_id TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  content_type TEXT NOT NULL,
  object_key TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(project_id, owner_kind, owner_id, sha256)
);
CREATE TABLE IF NOT EXISTS provider_events(
  provider_event_id TEXT PRIMARY KEY,
  project_id TEXT,
  provider_name TEXT NOT NULL,
  operation TEXT NOT NULL,
  outcome TEXT NOT NULL,
  latency_ms INTEGER,
  error_code TEXT,
  metadata TEXT NOT NULL,
  created_at TEXT NOT NULL
);
""".strip(),
    ),    Migration(
        "0002_v06_identity_multitenancy",
        """
CREATE TABLE IF NOT EXISTS tenants(
  tenant_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  status TEXT NOT NULL,
  created_by_actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workspaces(
  workspace_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  status TEXT NOT NULL,
  created_by_actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(tenant_id, name)
);
CREATE TABLE IF NOT EXISTS project_scopes(
  project_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  workspace_id TEXT NOT NULL,
  created_by_actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tenant_memberships(
  tenant_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  role TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(tenant_id, actor_id)
);
CREATE TABLE IF NOT EXISTS workspace_memberships(
  workspace_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  role TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(workspace_id, actor_id)
);
CREATE TABLE IF NOT EXISTS project_memberships(
  project_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  role TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(project_id, actor_id)
);
CREATE TABLE IF NOT EXISTS external_identities(
  external_identity_id TEXT PRIMARY KEY,
  actor_id TEXT NOT NULL,
  provider_id TEXT NOT NULL,
  issuer TEXT NOT NULL,
  subject TEXT NOT NULL,
  email TEXT,
  claims_metadata TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(provider_id, issuer, subject)
);
CREATE TABLE IF NOT EXISTS security_events(
  security_event_id TEXT PRIMARY KEY,
  actor_id TEXT NOT NULL,
  tenant_id TEXT,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  outcome TEXT NOT NULL,
  metadata TEXT NOT NULL,
  created_at TEXT NOT NULL
);
""".strip(),
    ),
    Migration(
        "0003_v07_distributed_runtime",
        """
CREATE TABLE IF NOT EXISTS worker_nodes(
  worker_id TEXT PRIMARY KEY,
  actor_id TEXT NOT NULL,
  status TEXT NOT NULL,
  capabilities TEXT NOT NULL,
  resources_total TEXT NOT NULL,
  heartbeat_ttl_seconds INTEGER NOT NULL,
  last_heartbeat_at TEXT NOT NULL,
  registered_at TEXT NOT NULL,
  metadata TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS distributed_jobs(
  job_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  workunit_id TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL,
  priority INTEGER NOT NULL,
  required_resources TEXT NOT NULL,
  required_capabilities TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  payload_hash TEXT NOT NULL,
  available_at TEXT NOT NULL,
  lease_worker_id TEXT,
  lease_token TEXT,
  lease_expires_at TEXT,
  attempt_count INTEGER NOT NULL,
  max_attempts INTEGER NOT NULL,
  result_json TEXT,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS job_attempts(
  attempt_id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  attempt_number INTEGER NOT NULL,
  worker_id TEXT NOT NULL,
  lease_token TEXT NOT NULL,
  run_id TEXT,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  heartbeat_at TEXT NOT NULL,
  lease_expires_at TEXT NOT NULL,
  finished_at TEXT,
  error_code TEXT,
  metadata TEXT NOT NULL,
  UNIQUE(job_id, attempt_number)
);
CREATE TABLE IF NOT EXISTS effect_commits(
  effect_key TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  result_json TEXT NOT NULL,
  committed_by_worker_id TEXT NOT NULL,
  committed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scheduler_events(
  event_id TEXT PRIMARY KEY,
  project_id TEXT,
  job_id TEXT,
  worker_id TEXT,
  event_type TEXT NOT NULL,
  metadata TEXT NOT NULL,
  created_at TEXT NOT NULL
);
""".strip(),
    ),

]


class MigrationManager:
    def __init__(self, db):
        self.db = db

    def ensure_table(self):
        self.db.conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations("
            "migration_id TEXT PRIMARY KEY, checksum TEXT NOT NULL, applied_at TEXT NOT NULL)"
        )
        self.db.conn.commit()

    def applied(self) -> dict[str, str]:
        self.ensure_table()
        return {r["migration_id"]: r["checksum"] for r in self.db.all("SELECT migration_id,checksum FROM schema_migrations")}

    def apply_all(self) -> list[str]:
        self.ensure_table()
        applied = self.applied()
        done: list[str] = []
        for migration in MIGRATIONS:
            existing = applied.get(migration.migration_id)
            if existing:
                if existing != migration.checksum:
                    raise RuntimeError(f"migration checksum mismatch: {migration.migration_id}")
                continue
            with self.db.tx():
                self.db.conn.executescript(migration.sql)
                self.db.conn.execute(
                    "INSERT INTO schema_migrations VALUES(?,?,?)",
                    (migration.migration_id, migration.checksum, utcnow()),
                )
            done.append(migration.migration_id)
        return done

    def status(self) -> dict[str, Any]:
        applied = self.applied()
        return {
            "known": [m.migration_id for m in MIGRATIONS],
            "applied": sorted(applied),
            "pending": [m.migration_id for m in MIGRATIONS if m.migration_id not in applied],
        }
