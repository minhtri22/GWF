from __future__ import annotations

import argparse
import json
import os
import tempfile
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from gwr.errors import AuthorityDenied
from gwr.runtime import GovernedWorkflowRuntime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(ROOT / 'evidence' / 'v0.6' / 'qa_v06.json'))
    args = ap.parse_args()
    checks = []
    with tempfile.TemporaryDirectory() as td:
        rt = GovernedWorkflowRuntime(str(ROOT / 'domains' / 'research.workflow.yaml'), str(Path(td) / 'qa.db'), auth_secret='q' * 64)
        backend = rt.db.backend_name
        tables = set(rt.db.list_tables())
        required = {'tenants','workspaces','project_scopes','tenant_memberships','workspace_memberships','project_memberships','external_identities','security_events'}
        checks.append({'name':'v06_tables','pass':required.issubset(tables),'missing':sorted(required-tables)})
        checks.append({'name':'v06_migration_applied','pass':'0002_v06_identity_multitenancy' in rt.db.migrations.status()['applied']})

        a = rt.governance.create_actor('HUMAN','qa-a',['human_approver'],[])
        b = rt.governance.create_actor('HUMAN','qa-b',['human_approver'],[])
        ta = rt.tenancy.create_tenant('A', a); tb = rt.tenancy.create_tenant('B', b)
        wa = rt.tenancy.create_workspace(ta,'WA',a); wb = rt.tenancy.create_workspace(tb,'WB',b)
        pa = rt.create_scoped_project('PA',ta,wa,a); pb = rt.create_scoped_project('PB',tb,wb,b)
        isolated = False
        try:
            rt.tenancy.require_project_access(a,pb,'VIEW')
        except AuthorityDenied:
            isolated = True
        checks.append({'name':'cross_tenant_denied','pass':isolated})
        checks.append({'name':'accessible_project_filter','pass':[x['id'] for x in rt.tenancy.list_accessible_projects(a)] == [pa]})

        exp = (datetime.now(timezone.utc)+timedelta(minutes=5)).timestamp()
        rt.auth.register_oidc_provider('qa','https://id.qa.example',lambda token:{'iss':'https://id.qa.example','sub':'qa-sub','exp':exp,'actor_id':b})
        rt.auth.bind_external_identity(a,'qa','https://id.qa.example','qa-sub')
        tok = rt.auth.authenticate_oidc('qa','opaque-verified-token')
        principal = rt.auth.verify(tok)
        checks.append({'name':'oidc_subject_binding','pass':principal.actor_id == a and principal.actor_id != b and principal.auth_method == 'OIDC'})
        rt.auth.revoke(tok)
        revoked = False
        try: rt.auth.verify(tok)
        except AuthorityDenied: revoked = True
        checks.append({'name':'revoked_session_denied','pass':revoked})

        sec = rt.db.all('SELECT * FROM security_events')
        checks.append({'name':'security_events_recorded','pass':len(sec) >= 6,'count':len(sec)})
        rt.close()

    errors = [c for c in checks if not c['pass']]
    result = {'version':'0.6.0','backend':backend,'status':'PASS' if not errors else 'FAIL','checks':checks,'errors':errors}
    out = Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if not errors else 1)

if __name__ == '__main__':
    main()
