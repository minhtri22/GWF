from pathlib import Path
import json, sqlite3, sys

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence'/'v0.4'/'real_run'
errors=[]
required=['runtime.db','result.json','status.json','audit.json','artifacts.json','RUNTIME_REPORT.md','auth_evidence.json','retrieval_evidence.json','verifier_evidence.json']
for name in required:
    if not (RUN/name).exists(): errors.append(f'missing:{name}')
if not errors:
    result=json.loads((RUN/'result.json').read_text())
    arts=json.loads((RUN/'artifacts.json').read_text())
    auth=json.loads((RUN/'auth_evidence.json').read_text())
    retrieval=json.loads((RUN/'retrieval_evidence.json').read_text())
    verifier=json.loads((RUN/'verifier_evidence.json').read_text())
    if result.get('status')!='COMPLETED': errors.append('run_not_completed')
    if result.get('outcome')!='PASS': errors.append('outcome_not_pass')
    if result.get('generation',0)<1: errors.append('semantic_recovery_not_exercised')
    if not verifier.get('independent_process'): errors.append('verifier_not_independent')
    if verifier.get('worker_pid') is None: errors.append('verifier_worker_pid_missing')
    if not verifier.get('input_sha256') or not verifier.get('result_sha256'): errors.append('verifier_hashes_missing')
    av=arts.get('analysis_result',{}).get('statistical_results',[{}])[0]
    if not av.get('pass'): errors.append('statistical_verifier_not_pass')
    if not av.get('independent_process'): errors.append('analysis_did_not_record_process_isolation')
    if not retrieval: errors.append('retrieval_evidence_missing')
    else:
        meta=retrieval[-1].get('retrieval') or {}
        if meta.get('provider') not in {'crossref','offline-provenance-snapshot'}: errors.append(f'unexpected_retrieval_provider:{meta.get("provider")}')
        if meta.get('degraded') and not meta.get('live_error'): errors.append('degraded_retrieval_not_explicit')
    if auth.get('authenticated_approval_count',0)<1: errors.append('no_authenticated_approvals')
    if auth.get('authenticated_approval_audit_events') != auth.get('authenticated_approval_count'): errors.append('authenticated_approval_audit_mismatch')
    if not auth.get('all_sessions_revoked_after_use'): errors.append('auth_sessions_not_revoked')
    con=sqlite3.connect(RUN/'runtime.db'); con.row_factory=sqlite3.Row
    openf=con.execute("select count(*) n from failures where status!='RESOLVED'").fetchone()['n']
    rec=con.execute('select count(*) n from recoveries').fetchone()['n']
    rootp=con.execute("select count(*) n from proposals where action='CONFIRM_ROOT' and status='APPROVED'").fetchone()['n']
    approvals=con.execute('select count(*) n from approvals').fetchone()['n']
    auth_events=con.execute("select count(*) n from audit_events where action='AUTHENTICATED_APPROVAL'").fetchone()['n']
    sessions=con.execute('select count(*) n from auth_sessions').fetchone()['n']
    if openf: errors.append(f'open_failures:{openf}')
    if rec<1: errors.append('semantic_recovery_missing')
    if rootp<1: errors.append('authenticated_root_confirmation_missing')
    if approvals != auth_events: errors.append(f'approvals_without_auth_audit:{approvals}!={auth_events}')
    if sessions != approvals: errors.append(f'one_time_session_count_mismatch:{sessions}!={approvals}')
    con.close()
print('GWR v0.4 hardening QA')
print('======================')
print('RESULT:', 'PASS' if not errors else 'FAIL')
print('errors:',len(errors))
for e in errors: print('-',e)
sys.exit(1 if errors else 0)
