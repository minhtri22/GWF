from pathlib import Path
import json
import os
import sqlite3

import pytest

from gwr.db import Database, SCHEMA, create_database
from gwr.db_backends import qmark_to_format, postgres_base_schema_from_sqlite, POSTGRES_GUARD_DDL
from gwr.object_store import LocalContentAddressedStore, ObjectRefService
from gwr.observability import JsonlObserver
from gwr.provider_chain import ProviderFailoverChain
from gwr.runtime import GovernedWorkflowRuntime

ROOT=Path(__file__).resolve().parents[1]


def test_migration_applies_and_is_idempotent(tmp_path):
    db=create_database(str(tmp_path/'a.db'))
    status=db.migrations.status()
    assert status['pending']==[]
    assert '0001_v05_production_foundation' in status['applied']
    assert 'object_refs' in db.list_tables()
    before=db.one("SELECT count(*) n FROM schema_migrations")['n']
    assert db.migrations.apply_all()==[]
    assert db.one("SELECT count(*) n FROM schema_migrations")['n']==before
    db.close()


def test_legacy_v04_database_upgrades_without_losing_project(tmp_path):
    path=tmp_path/'legacy.db'
    if not os.environ.get('GWR_TEST_DATABASE_URL'):
        con=sqlite3.connect(path); con.executescript(SCHEMA)
        con.execute("INSERT INTO projects VALUES(?,?,?,?)",('legacy','Legacy','research.workflow','2026-01-01T00:00:00+00:00')); con.commit(); con.close()
        db=create_database(str(path))
    else:
        # Build a logical pre-v0.5 state inside the isolated PostgreSQL test schema,
        # then reopen the same logical target so MigrationManager has to restore it.
        db=create_database(str(path))
        db.conn.execute("INSERT INTO projects VALUES(?,?,?,?)",('legacy','Legacy','research.workflow','2026-01-01T00:00:00+00:00'))
        db.conn.execute("DROP TABLE IF EXISTS object_refs")
        db.conn.execute("DROP TABLE IF EXISTS provider_events")
        db.conn.execute("DELETE FROM schema_migrations WHERE migration_id=?",('0001_v05_production_foundation',))
        db.conn.commit(); db.close()
        db=create_database(str(path))
    assert db.one("SELECT name FROM projects WHERE id='legacy'")['name']=='Legacy'
    assert db.one("SELECT migration_id FROM schema_migrations WHERE migration_id='0001_v05_production_foundation'")
    assert {'object_refs','provider_events'}.issubset(set(db.list_tables()))
    db.close()


def test_content_addressed_store_and_object_ref(tmp_path):
    db=create_database(str(tmp_path/'o.db'))
    db.conn.execute("INSERT INTO projects VALUES(?,?,?,?)",('p','P','d','now')); db.conn.commit()
    store=LocalContentAddressedStore(tmp_path/'objects'); svc=ObjectRefService(db,store)
    r1=svc.attach_bytes('p','Experiment','run1',b'abc',content_type='text/plain')
    r2=svc.attach_bytes('p','Experiment','run1',b'abc',content_type='text/plain')
    assert r1['ref_id']==r2['ref_id']
    assert svc.read(r1['ref_id'])==b'abc'
    assert store.verify(r1['sha256'])
    db.close()


def test_provider_failover_records_degradation(tmp_path):
    class Bad:
        def search(self,q): raise TimeoutError('boom')
    class Good:
        def search(self,q): return {'q':q,'hits':[1]}
    db=create_database(str(tmp_path/'p.db'))
    obs=JsonlObserver(tmp_path/'obs.jsonl')
    chain=ProviderFailoverChain([('bad',Bad()),('good',Good())],db=db,observer=obs)
    out=chain.call('search','x',project_id=None,accept=lambda x:bool(x['hits']))
    assert out['provider']=='good' and out['degraded'] is True
    rows=db.all('SELECT * FROM provider_events ORDER BY created_at')
    assert [r['outcome'] for r in rows]==['FAILED','SUCCESS']
    assert obs.metrics()['by_event']['provider_attempt']==2
    db.close()


def test_observer_runtime_emits_structured_events(tmp_path):
    rt=GovernedWorkflowRuntime(str(ROOT/'domains'/'example.workflow.yaml'),str(tmp_path/'r.db'),object_store_root=tmp_path/'objects',observability_path=tmp_path/'runtime.jsonl')
    p=rt.create_project('P')
    ref=rt.attach_blob(p,'Project',p,b'payload','text/plain')
    assert rt.object_store.verify(ref['sha256'])
    m=rt.observer.metrics(); assert m['by_event']['runtime_initialized']==1; assert m['by_event']['project_created']==1; assert m['by_event']['object_attached']==1
    rt.close()
    events=[json.loads(x) for x in (tmp_path/'runtime.jsonl').read_text().splitlines()]
    assert all('timestamp' in e and 'event' in e for e in events)


def test_postgres_contract_has_portable_schema_and_qmark_translation():
    p=postgres_base_schema_from_sqlite(SCHEMA)
    assert 'PRAGMA' not in p
    assert "RAISE(ABORT" not in p
    assert 'CREATE TABLE IF NOT EXISTS projects' in p
    assert 'LANGUAGE plpgsql' in POSTGRES_GUARD_DDL
    assert qmark_to_format('SELECT * FROM x WHERE a=? AND b=?')=='SELECT * FROM x WHERE a=%s AND b=%s'


def test_postgres_backend_driver_contract():
    live=os.environ.get('GWR_TEST_DATABASE_URL')
    if live:
        db=create_database(live)
        assert db.backend_name=='postgresql'
        assert 'projects' in db.list_tables()
        db.close()
    else:
        with pytest.raises(RuntimeError,match='psycopg'):
            create_database('postgresql://user:pass@127.0.0.1/db')
