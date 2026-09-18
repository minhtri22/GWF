from __future__ import annotations
import argparse, json, os, secrets, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from gwr.runtime import GovernedWorkflowRuntime
from gwr.research_orchestrator import ResearchOrchestrator
from gwr.datasets import DatasetRegistry
from gwr.research_benchmark import ResearchBenchmarkSuite, BenchmarkResearchExecutor

ROLES=["research_lead","literature_reviewer","protocol_designer","experimenter","analyst","adversarial_reviewer","reproducibility_reviewer"]
TABLES=['projects','actors','artifacts','revisions','evidence','checkpoints','orchestrations','phase_executions','failures','recoveries','gates','decisions','proposals','approvals']

def rowdict(r): return dict(r)
def stable_snapshot(db, project_id, orchestration_id):
    out={}
    for table in TABLES:
        if table in {'projects','actors'}:
            if table=='projects': rows=db.all("SELECT * FROM projects WHERE id=? ORDER BY id",(project_id,))
            else: rows=db.all("SELECT * FROM actors WHERE project_scope LIKE ? ORDER BY actor_id",(f'%{project_id}%',))
        elif table=='orchestrations': rows=db.all("SELECT * FROM orchestrations WHERE orchestration_id=? ORDER BY orchestration_id",(orchestration_id,))
        elif table=='phase_executions': rows=db.all("SELECT * FROM phase_executions WHERE orchestration_id=? ORDER BY phase_index,generation,started_at",(orchestration_id,))
        elif table in {'artifacts','evidence','checkpoints','failures','recoveries','gates','decisions','proposals','approvals'}:
            rows=db.all(f"SELECT * FROM {table} WHERE project_id=? ORDER BY 1",(project_id,))
        elif table=='revisions':
            rows=db.all("SELECT r.* FROM revisions r JOIN artifacts a ON a.artifact_id=r.artifact_id WHERE a.project_id=? ORDER BY r.revision_id",(project_id,))
        else: rows=[]
        out[table]=[rowdict(r) for r in rows]
    return out

def approve(rt,project,token):
    prop=rt.db.one("SELECT * FROM proposals WHERE project_id=? AND status='PENDING_APPROVAL' ORDER BY created_at DESC LIMIT 1",(project,))
    if not prop: raise RuntimeError('pause without pending proposal')
    rt.governance.approve_proposal_authenticated(prop['proposal_id'],token,prop['payload_hash'])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--restart-after-phases',type=int,default=8)
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    if not os.environ.get('GWR_TEST_DATABASE_URL'): raise SystemExit('GWR_TEST_DATABASE_URL is required: this is a live PostgreSQL probe')
    logical=out/'postgres-restart-runtime.db'; secret=secrets.token_urlsafe(48); password=secrets.token_urlsafe(20)
    reg=DatasetRegistry(ROOT/'datasets'); suite=ResearchBenchmarkSuite(ROOT/'benchmarks'/'research_reliability.yaml'); case=suite.case('synth_underpowered_pivot')
    rt=GovernedWorkflowRuntime(str(ROOT/'domains'/'research.workflow.yaml'),str(logical),auth_secret=secret)
    if rt.db.backend_name!='postgresql': raise RuntimeError('restart probe did not bind to PostgreSQL')
    project=rt.create_project('v0.5.1-postgres-restart-probe')
    actors={r:rt.governance.create_actor('AGENT',f'{r}-restart',[r],[project]) for r in ROLES}
    human=rt.governance.create_actor('HUMAN','human-restart',['human_approver'],[project]); username='restart-approver'
    rt.auth.register_human(human,username,password); token=rt.auth.authenticate(username,password,client_metadata={'client':'v0.5.1-restart-probe'})
    orch=ResearchOrchestrator(rt,actors); executor=BenchmarkResearchExecutor(reg,case); result=orch.start(project,executor,max_steps=500)
    restarted=False; equality=None; before=None; after=None; approvals=0
    while result['status']=='PAUSED':
        status=orch.get_status(result['orchestration_id'])
        if not restarted and len(status['phases'])>=args.restart_after_phases:
            before=stable_snapshot(rt.db,project,result['orchestration_id'])
            cp=result['checkpoint_id']; oid=result['orchestration_id']
            rt.close()
            rt=GovernedWorkflowRuntime(str(ROOT/'domains'/'research.workflow.yaml'),str(logical),auth_secret=secret)
            if rt.db.backend_name!='postgresql': raise RuntimeError('reopened runtime is not PostgreSQL')
            after=stable_snapshot(rt.db,project,oid); equality=(before==after); restarted=True
            if not equality:
                (out/'restart_before.json').write_text(json.dumps(before,indent=2),encoding='utf-8'); (out/'restart_after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
                raise RuntimeError('state/evidence/checkpoint changed across PostgreSQL connection restart')
            token=rt.auth.authenticate(username,password,client_metadata={'client':'v0.5.1-restart-probe-reopened'})
            orch=ResearchOrchestrator(rt,actors); executor=BenchmarkResearchExecutor(reg,case); result={'status':'PAUSED','reason':result['reason'],'checkpoint_id':cp,'orchestration_id':oid,'project_id':project}
        approve(rt,project,token); approvals+=1
        result=orch.resume(result['checkpoint_id'],executor,max_steps=500)
    if not restarted: raise RuntimeError('probe completed without exercising restart')
    if result['status']!='COMPLETED': raise RuntimeError(f'non-completed probe: {result}')
    final=orch.get_status(result['orchestration_id'])
    summary={'version':'0.5.1','backend':rt.db.backend_name,'result':'PASS','restart_exercised':restarted,'restart_persistence_equal':equality,'outcome':result['outcome'],'pivot_count':result['pivot_count'],'phase_executions':len(final['phases']),'approvals_after_start':approvals,'terminal_checkpoint_id':result.get('terminal_checkpoint_id')}
    (out/'RESTART_PROBE.json').write_text(json.dumps(summary,indent=2),encoding='utf-8'); print(json.dumps(summary,indent=2)); rt.close()
if __name__=='__main__': main()
