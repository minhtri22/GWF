from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from gwr.runtime import GovernedWorkflowRuntime
from gwr.domain import PRIMITIVES, load_domain

root=Path(__file__).parents[1]
domain=load_domain(root/'domains/example.workflow.yaml')
rt=GovernedWorkflowRuntime(domain)
errors=[]
expected_tables={
'projects','actors','authority_policies','artifacts','revisions','trace_links','impacts','workunits','runs','evidence','gates','decisions','failures','recoveries','loopguards','checkpoints','proposals','approvals','audit_events','idempotency'}
tables=set(rt.db.list_tables())
missing=expected_tables-tables
if missing: errors.append(f"missing tables: {sorted(missing)}")
required_methods={
'knowledge':['create_artifact','create_revision','create_trace_link','get_artifact','get_revision','get_current_revision','get_trace_graph','get_validity','get_validity_frontier','compute_impact','get_affected_subgraph'],
'execution':['create_workunit','get_ready_workunits','start_run','add_evidence','finish_run','create_checkpoint','resume_from_checkpoint','cancel_run','get_execution_status'],
'decision':['evaluate_gate','get_gate_status','record_failure','diagnose_failure','compute_decision','create_recovery_plan','evaluate_loop_guard','get_pending_decisions','resolve_failure'],
'governance':['authenticate_actor','authorize','prepare_proposal','approve_proposal','reject_proposal','get_pending_approvals','append_audit','query_audit','resolve_escalation_target']}
for kernel,methods in required_methods.items():
    obj=getattr(rt,kernel)
    for m in methods:
        if not hasattr(obj,m): errors.append(f"{kernel} missing {m}")
# primitive ownership coverage by physical entities/services
primitive_map={
'PRIM-ARTIFACT':'artifacts','PRIM-REVISION':'revisions','PRIM-TRACE':'trace_links','PRIM-VALIDITY':'revisions.validity_state','PRIM-IMPACT':'impacts',
'PRIM-WORKUNIT':'workunits','PRIM-RUN':'runs','PRIM-CHECKPOINT':'checkpoints','PRIM-EVIDENCE':'evidence',
'PRIM-GATE':'gates','PRIM-DECISION':'decisions','PRIM-FAILURE':'failures','PRIM-RECOVERY':'recoveries','PRIM-LOOPGUARD':'loopguards',
'PRIM-ACTOR':'actors','PRIM-AUTHORITY':'authority_policies','PRIM-APPROVAL':'approvals','PRIM-AUDIT':'audit_events','PRIM-DOMAIN':'DomainPackage'}
if set(primitive_map)!=PRIMITIVES: errors.append('primitive physical mapping does not cover registry exactly')
# source specification presence
for f in ['README.md','01-knowledge-kernel.md','02-execution-kernel.md','03-decision-kernel.md','04-governance-kernel.md','05-domain-package.md']:
    if not (root/'spec'/f).exists(): errors.append(f"missing source spec {f}")
rt.close()
print('GWR implementation QA')
print('=====================')
print('Canonical primitives:',len(PRIMITIVES))
print('Mapped primitives:',len(primitive_map))
print('Schema tables:',len(tables))
print('Required API methods checked:',sum(map(len,required_methods.values())))
print('Errors:',len(errors))
for e in errors: print('ERROR:',e)
print('RESULT:', 'PASS' if not errors else 'FAIL')
raise SystemExit(1 if errors else 0)
