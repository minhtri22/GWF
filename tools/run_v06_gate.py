from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, *, env, log):
    p = subprocess.run(cmd, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    Path(log).parent.mkdir(parents=True, exist_ok=True)
    Path(log).write_text(p.stdout, encoding='utf-8')
    print(p.stdout, end='')
    if p.returncode:
        raise RuntimeError(f'command failed ({p.returncode}): {cmd}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--postgres-url', default=os.environ.get('GWR_TEST_DATABASE_URL'))
    ap.add_argument('--out', default=str(ROOT / 'evidence' / 'v0.6' / 'live_gate'))
    a = ap.parse_args()
    if not a.postgres_url:
        raise SystemExit('v0.6 live gate requires PostgreSQL URL')
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    base = os.environ.copy(); base.pop('GWR_TEST_DATABASE_URL', None); base.pop('GWR_TEST_NAMESPACE_PREFIX', None)
    pg = base.copy(); pg['GWR_TEST_DATABASE_URL'] = a.postgres_url; pg['GWR_TEST_NAMESPACE_PREFIX'] = 'gwr_v06_gate'

    # Preserve the full v0.5.1 equivalence/restart/research regression gate.
    run([sys.executable,'tools/run_v051_gate.py','--postgres-url',a.postgres_url,'--out',str(out/'v051_regression')], env=base, log=out/'v051_regression.log')
    run([sys.executable,'-m','pytest','-q','tests/test_v06_identity_multitenancy.py'], env=base, log=out/'v06_sqlite_tests.txt')
    run([sys.executable,'tools/qa_v06.py','--out',str(out/'QA_SQLITE.json')], env=base, log=out/'qa_sqlite.log')
    run([sys.executable,'-m','pytest','-q','tests/test_v06_identity_multitenancy.py'], env=pg, log=out/'v06_postgres_tests.txt')
    run([sys.executable,'tools/qa_v06.py','--out',str(out/'QA_POSTGRES.json')], env=pg, log=out/'qa_postgres.log')
    run([sys.executable,'-m','compileall','-q','src','tests','tools'], env=base, log=out/'compileall.txt')

    v051 = json.loads((out/'v051_regression'/'POSTGRES_GATE.json').read_text())
    qs = json.loads((out/'QA_SQLITE.json').read_text())
    qp = json.loads((out/'QA_POSTGRES.json').read_text())
    result = {
        'version':'0.6.0',
        'status':'PASS' if v051.get('status')=='PASS' and qs.get('status')=='PASS' and qp.get('status')=='PASS' else 'FAIL',
        'v051_regression_pass':v051.get('status')=='PASS',
        'postgres_live_tested':True,
        'sqlite_identity_multitenancy_pass':qs.get('status')=='PASS',
        'postgres_identity_multitenancy_pass':qp.get('status')=='PASS',
        'tenant_isolation_pass':all(next(c['pass'] for c in q['checks'] if c['name']=='cross_tenant_denied') for q in (qs,qp)),
        'oidc_binding_pass':all(next(c['pass'] for c in q['checks'] if c['name']=='oidc_subject_binding') for q in (qs,qp)),
        'revocation_pass':all(next(c['pass'] for c in q['checks'] if c['name']=='revoked_session_denied') for q in (qs,qp)),
        'ready_for_v07':False,
    }
    result['ready_for_v07'] = result['status']=='PASS'
    (out/'V06_GATE.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status']=='PASS' else 1)

if __name__ == '__main__':
    main()
