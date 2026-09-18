from __future__ import annotations
import json, shutil, sqlite3, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from gwr.db import Database, SCHEMA
from gwr.object_store import LocalContentAddressedStore, ObjectRefService
from gwr.observability import JsonlObserver
from gwr.provider_chain import ProviderFailoverChain
from gwr.db_backends import postgres_base_schema_from_sqlite, POSTGRES_GUARD_DDL

def main():
    out=ROOT/'evidence'/'v0.5'; out.mkdir(parents=True,exist_ok=True)
    checks=[]
    # Legacy migration preservation.
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'legacy.db'; c=sqlite3.connect(p); c.executescript(SCHEMA); c.execute("INSERT INTO projects VALUES(?,?,?,?)",('legacy','Legacy','research.workflow','t')); c.commit(); c.close()
        db=Database(str(p)); ok=db.one("SELECT name FROM projects WHERE id='legacy'")['name']=='Legacy' and not db.migrations.status()['pending']; checks.append({'name':'legacy_migration_preserves_state','pass':ok,'status':db.migrations.status()}); db.close()
    # Content addressed store.
    with tempfile.TemporaryDirectory() as td:
        db=Database(':memory:'); db.conn.execute("INSERT INTO projects VALUES(?,?,?,?)",('p','P','d','t')); db.conn.commit(); store=LocalContentAddressedStore(Path(td)/'objects'); svc=ObjectRefService(db,store); r=svc.attach_bytes('p','Experiment','x',b'raw-evidence',content_type='application/octet-stream'); checks.append({'name':'object_store_hash_roundtrip','pass':svc.read(r['ref_id'])==b'raw-evidence' and store.verify(r['sha256']),'sha256':r['sha256']}); db.close()
    # Provider failover.
    class Bad:
        def retrieve(self,q): raise TimeoutError('simulated primary outage')
    class Good:
        def retrieve(self,q): return {'records':[q]}
    with tempfile.TemporaryDirectory() as td:
        db=Database(':memory:'); obs=JsonlObserver(Path(td)/'obs.jsonl'); chain=ProviderFailoverChain([('primary',Bad()),('secondary',Good())],db=db,observer=obs); r=chain.call('retrieve','x',accept=lambda v:bool(v.get('records'))); checks.append({'name':'provider_failover','pass':r['provider']=='secondary' and r['degraded'] and len(r['attempts'])==2,'attempts':r['attempts']}); db.close()
    # PostgreSQL code contract; no live server/driver in this execution environment.
    pg=postgres_base_schema_from_sqlite(SCHEMA); pg_ok='PRAGMA' not in pg and 'RAISE(ABORT' not in pg and 'LANGUAGE plpgsql' in POSTGRES_GUARD_DDL
    checks.append({'name':'postgres_contract','pass':pg_ok,'live_integration_tested':False,'blocker':'psycopg and PostgreSQL server unavailable in QA container'})
    bench=json.loads((out/'benchmark_run'/'BENCHMARK_SUMMARY.json').read_text())
    checks.append({'name':'research_benchmark_semantic_acceptance','pass':bench['pass'],'case_outcomes':[{'id':c['case_id'],'outcome':c['outcome'],'pivot_count':c['pivot_count']} for c in bench['cases']]})
    summary={'version':'0.5','checks':checks,'pass':all(c['pass'] for c in checks),'production_foundation_status':'PASS_WITH_POSTGRES_LIVE_VALIDATION_OPEN'}
    (out/'FOUNDATION_ACCEPTANCE.json').write_text(json.dumps(summary,indent=2),encoding='utf-8'); print(json.dumps(summary,indent=2))
    if not summary['pass']: raise SystemExit(1)
if __name__=='__main__': main()
