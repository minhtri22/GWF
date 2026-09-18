from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from gwr.db import Database, SCHEMA
from gwr.db_backends import postgres_base_schema_from_sqlite, POSTGRES_GUARD_DDL
from gwr.datasets import DatasetRegistry
from gwr.research_benchmark import ResearchBenchmarkSuite

def main():
    errors=[]; warnings=[]
    db=Database(':memory:')
    tables=set(db.list_tables())
    for t in ['schema_migrations','object_refs','provider_events']:
        if t not in tables: errors.append(f'missing v0.5 table {t}')
    st=db.migrations.status()
    if st['pending']: errors.append(f'pending migrations {st["pending"]}')
    db.close()
    pg=postgres_base_schema_from_sqlite(SCHEMA)
    if 'PRAGMA' in pg or 'RAISE(ABORT' in pg: errors.append('postgres base schema contains SQLite-only syntax')
    if 'gwr_reject_audit_mutation' not in POSTGRES_GUARD_DDL or 'gwr_revision_immutable' not in POSTGRES_GUARD_DDL: errors.append('postgres guard DDL incomplete')
    reg=DatasetRegistry(ROOT/'datasets'); suite=ResearchBenchmarkSuite(ROOT/'benchmarks'/'research_reliability.yaml')
    if len(reg.ids())<10: errors.append('dataset foundation missing')
    if len(suite.cases)<6: errors.append('research benchmark cases missing')
    summary={'result':'PASS' if not errors else 'FAIL','errors':errors,'warnings':warnings,'sqlite_tables':len(tables),'migrations':st,'datasets':len(reg.ids()),'research_cases':len(suite.cases),'postgres_contract':'READY_NOT_LIVE_TESTED'}
    print(json.dumps(summary,indent=2)); raise SystemExit(1 if errors else 0)
if __name__=='__main__': main()
