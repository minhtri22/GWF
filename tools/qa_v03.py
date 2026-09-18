from pathlib import Path
import json, sqlite3, sys
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence'/'v0.3'/'real_run'
errors=[]
for name in ['runtime.db','result.json','status.json','audit.json','artifacts.json','RUNTIME_REPORT.md']:
    if not (RUN/name).exists(): errors.append(f'missing:{name}')
if not errors:
    result=json.loads((RUN/'result.json').read_text())
    arts=json.loads((RUN/'artifacts.json').read_text())
    if result.get('status')!='COMPLETED': errors.append('run_not_completed')
    if result.get('outcome')!='PASS': errors.append('outcome_not_pass')
    if result.get('generation',0)<1: errors.append('semantic_recovery_not_exercised')
    v=arts.get('analysis_result',{}).get('statistical_results',[{}])[0]
    if not v.get('pass'): errors.append('statistical_verifier_not_pass')
    con=sqlite3.connect(RUN/'runtime.db'); con.row_factory=sqlite3.Row
    openf=con.execute("select count(*) n from failures where status!='RESOLVED'").fetchone()['n']
    rec=con.execute('select count(*) n from recoveries').fetchone()['n']
    cps=con.execute('select count(*) n from checkpoints').fetchone()['n']
    if openf: errors.append(f'open_failures:{openf}')
    if rec<1: errors.append('no_semantic_recovery_plan')
    if cps<17: errors.append(f'checkpoint_count_too_low:{cps}')
    fcs={r['failure_class'] for r in con.execute('select failure_class from failures')}
    if 'pilot_degenerate' not in fcs: errors.append('pilot_recovery_failure_missing')
    con.close()
print('GWR v0.3 QA')
print('RESULT:', 'PASS' if not errors else 'FAIL')
print('errors:', len(errors))
for e in errors: print('-',e)
sys.exit(1 if errors else 0)
