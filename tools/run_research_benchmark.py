from __future__ import annotations

import argparse, json, secrets, sys, hashlib
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

from gwr.runtime import GovernedWorkflowRuntime
from gwr.research_orchestrator import ResearchOrchestrator
from gwr.datasets import DatasetRegistry
from gwr.research_benchmark import ResearchBenchmarkSuite, BenchmarkResearchExecutor
from gwr.utils import parse_json

ROLES=["research_lead","literature_reviewer","protocol_designer","experimenter","analyst","adversarial_reviewer","reproducibility_reviewer"]

def semantic_snapshot(rt, project_id, orchestration_id, outcome, pivot_count):
    phases=[]
    for r in rt.db.all("SELECT phase_id,generation,status,decision_outcome FROM phase_executions WHERE orchestration_id=? ORDER BY phase_index,generation,started_at",(orchestration_id,)):
        phases.append({"phase_id":r["phase_id"],"generation":int(r["generation"]),"status":r["status"],"decision_outcome":r["decision_outcome"]})
    failures=[]
    for r in rt.db.all("SELECT failure_class,detected_stage,root_status,severity,status FROM failures WHERE project_id=? ORDER BY created_at",(project_id,)):
        failures.append({k:r[k] for k in ["failure_class","detected_stage","root_status","severity","status"]})
    gates=[]
    for r in rt.db.all("SELECT gate_type,result,violation_codes FROM gates WHERE project_id=? ORDER BY evaluated_at",(project_id,)):
        gates.append({"gate_type":r["gate_type"],"result":r["result"],"violation_codes":sorted(parse_json(r["violation_codes"],[]))})
    decisions=[]
    for r in rt.db.all("SELECT decision_type,reason_codes FROM decisions WHERE project_id=? ORDER BY created_at",(project_id,)):
        decisions.append({"decision_type":r["decision_type"],"reason_codes":sorted(parse_json(r["reason_codes"],[]))})
    ev=Counter(r["evidence_type"] for r in rt.db.all("SELECT evidence_type FROM evidence WHERE project_id=?",(project_id,)))
    rev_counts={}
    for r in rt.db.all("SELECT a.artifact_type,COUNT(*) n FROM revisions r JOIN artifacts a ON a.artifact_id=r.artifact_id WHERE a.project_id=? GROUP BY a.artifact_type ORDER BY a.artifact_type",(project_id,)):
        rev_counts[r["artifact_type"]]=int(r["n"])
    cp_count=int(rt.db.one("SELECT COUNT(*) n FROM checkpoints WHERE project_id=?",(project_id,))["n"])
    recovery_count=int(rt.db.one("SELECT COUNT(*) n FROM recoveries WHERE project_id=?",(project_id,))["n"])
    snap={
        "outcome":outcome,"pivot_count":int(pivot_count),"phase_trace":phases,
        "failure_trace":failures,"gate_trace":gates,"decision_trace":decisions,
        "evidence_type_counts":dict(sorted(ev.items())),"artifact_revision_counts":rev_counts,
        "checkpoint_count":cp_count,"recovery_count":recovery_count,
    }
    raw=json.dumps(snap,sort_keys=True,separators=(",",":"))
    return snap,hashlib.sha256(raw.encode()).hexdigest()

def approve_one(rt, project_id, token):
    prop=rt.db.one("SELECT * FROM proposals WHERE project_id=? AND status='PENDING_APPROVAL' ORDER BY created_at DESC LIMIT 1",(project_id,))
    if not prop: raise RuntimeError('paused but no pending proposal')
    principal=rt.auth.verify(token)
    aid=rt.governance.approve_proposal_authenticated(prop['proposal_id'],token,prop['payload_hash'])
    return {'proposal_id':prop['proposal_id'],'approval_id':aid,'actor_id':principal.actor_id,'action':prop['action']}

def run_case(case_id, suite, registry, out):
    case=suite.case(case_id)
    case_dir=out/case_id; case_dir.mkdir(parents=True,exist_ok=True)
    db=case_dir/'runtime.db'
    if db.exists(): db.unlink()
    password=secrets.token_urlsafe(20)
    rt=GovernedWorkflowRuntime(str(ROOT/'domains'/'research.workflow.yaml'),str(db),auth_secret=secrets.token_urlsafe(48))
    project=rt.create_project(f'benchmark-{case_id}')
    actors={r:rt.governance.create_actor('AGENT',f'{r}-{case_id}',[r],[project]) for r in ROLES}
    human=rt.governance.create_actor('HUMAN',f'human-{case_id}',['human_approver'],[project])
    username=f'qa-{case_id}'; rt.auth.register_human(human,username,password)
    approval_token=rt.auth.authenticate(username,password,client_metadata={'client':'v0.4.1-benchmark-driver'})
    orch=ResearchOrchestrator(rt,actors)
    executor=BenchmarkResearchExecutor(registry,case)
    result=orch.start(project,executor,max_steps=500)
    approvals=[]; safety=0
    while result['status']=='PAUSED' and result.get('reason') in {'WAITING_APPROVAL','WAITING_HUMAN_CONFIRMATION'}:
        safety+=1
        if safety>80: raise RuntimeError(f'approval loop {case_id}')
        approvals.append(approve_one(rt,project,approval_token))
        result=orch.resume(result['checkpoint_id'],executor,max_steps=500)
    if result['status']!='COMPLETED': raise RuntimeError(f'{case_id} terminal {result}')
    status=orch.get_status(result['orchestration_id'])
    orch.write_report(result['orchestration_id'],case_dir/'RUNTIME_REPORT.md')
    (case_dir/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (case_dir/'status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    (case_dir/'audit.json').write_text(json.dumps(rt.governance.query_audit(project),indent=2),encoding='utf-8')
    artifacts={}
    for row in rt.db.all("SELECT artifact_type,current_revision_id FROM artifacts WHERE project_id=? ORDER BY artifact_type",(project,)):
        artifacts[row['artifact_type']]=rt.knowledge.get_revision(row['current_revision_id'])['structured_payload']
    (case_dir/'artifacts.json').write_text(json.dumps(artifacts,indent=2),encoding='utf-8')
    got=result['outcome']; exp=case.data['expected_terminal_outcome']; exp_pivot=int(case.data.get('expected_pivot_count',0))
    sem,sem_hash=semantic_snapshot(rt,project,result['orchestration_id'],got,result['pivot_count'])
    (case_dir/'semantic_snapshot.json').write_text(json.dumps(sem,indent=2,sort_keys=True),encoding='utf-8')
    summary={'case_id':case_id,'status':result['status'],'outcome':got,'expected_outcome':exp,'pivot_count':result['pivot_count'],'expected_pivot_count':exp_pivot,'pass':got==exp and result['pivot_count']==exp_pivot,'authenticated_approvals':len(approvals),'phase_executions':len(status['phases']),'terminal_checkpoint_id':result.get('terminal_checkpoint_id'),'backend':rt.db.backend_name,'semantic_sha256':sem_hash}
    rt.auth.revoke(approval_token)
    rt.close(); return summary

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default=str(ROOT/'evidence'/'v0.4.1'/'benchmark_run')); ap.add_argument('--case',action='append')
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    registry=DatasetRegistry(ROOT/'datasets'); suite=ResearchBenchmarkSuite(ROOT/'benchmarks'/'research_reliability.yaml')
    ids=args.case or list(suite.cases)
    case_results=[run_case(cid,suite,registry,out) for cid in ids]
    quality=[]
    for q in suite.quality_cases:
        res=registry.quality_assessment(q['dataset_id'],target_column=q.get('target_column'),max_target_missing=float(q.get('max_target_missing',0.10)),expected_columns=q.get('expected_columns'),confounder=q.get('confounder'))
        quality.append({'id':q['id'],'dataset_id':q['dataset_id'],'expected_issue':q['expected_issue'],'issues':res['issues'],'pass':q['expected_issue'] in res['issues'],'details':res})
    integrity=[registry.validate_integrity(i) for i in registry.ids()]
    summary={'version':'0.5.1','cases':case_results,'quality_cases':quality,'dataset_integrity':integrity,'pass':all(x['pass'] for x in case_results+quality) and all(x['ok'] for x in integrity)}
    (out/'BENCHMARK_SUMMARY.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    if not summary['pass']: raise SystemExit(1)

if __name__=='__main__': main()
