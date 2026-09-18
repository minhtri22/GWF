from __future__ import annotations
import argparse, json, os, re, sys, uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def redact_dsn(dsn: str) -> str:
    # Avoid writing credentials to evidence/logs.
    return re.sub(r'(?i)(postgres(?:ql)?://[^:/?#]+:)[^@/]+@', r'\1***@', dsn)


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--postgres-url', default=os.environ.get('GWR_TEST_DATABASE_URL'))
    ap.add_argument('--out', required=True)
    args=ap.parse_args()
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    result={
        'version':'0.5.1r1',
        'status':'BLOCKED_ENVIRONMENT',
        'driver':'psycopg>=3',
        'dsn_present':bool(args.postgres_url),
        'dsn_redacted':redact_dsn(args.postgres_url) if args.postgres_url else None,
        'server_reachable':False,
        'server_version_num':None,
        'server_version':None,
        'transaction_probe':False,
        'schema_probe':False,
    }
    try:
        if not args.postgres_url:
            raise RuntimeError('GWR_TEST_DATABASE_URL / --postgres-url is required')
        import psycopg
        from psycopg.rows import dict_row
        with psycopg.connect(args.postgres_url,row_factory=dict_row,connect_timeout=15) as conn:
            result['server_reachable']=True
            row=conn.execute("SELECT current_setting('server_version_num')::int AS version_num, version() AS version").fetchone()
            result['server_version_num']=int(row['version_num'])
            result['server_version']=row['version']
            if result['server_version_num'] < 140000:
                raise RuntimeError(f"PostgreSQL >=14 required for production gate; got {result['server_version_num']}")
            probe=f"gwr_preflight_{uuid.uuid4().hex[:12]}"
            conn.execute(f'CREATE SCHEMA "{probe}"')
            conn.execute(f'SET search_path TO "{probe}"')
            conn.execute('CREATE TABLE probe(id TEXT PRIMARY KEY, value TEXT NOT NULL)')
            conn.execute("INSERT INTO probe VALUES ('a','before')")
            conn.commit()
            result['schema_probe']=True
            try:
                with conn.transaction():
                    conn.execute("UPDATE probe SET value='after' WHERE id='a'")
                    raise RuntimeError('intentional rollback')
            except RuntimeError as e:
                if str(e)!='intentional rollback': raise
            value=conn.execute("SELECT value FROM probe WHERE id='a'").fetchone()['value']
            result['transaction_probe']=(value=='before')
            conn.execute('SET search_path TO public')
            conn.execute(f'DROP SCHEMA "{probe}" CASCADE')
            conn.commit()
            if not result['transaction_probe']:
                raise RuntimeError('rollback probe failed')
        result['status']='PASS'
    except Exception as exc:
        result['error_type']=type(exc).__name__
        result['error']=str(exc)
    (out/'POSTGRES_PREFLIGHT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 2

if __name__=='__main__':
    raise SystemExit(main())
