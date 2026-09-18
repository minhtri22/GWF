import pytest
from gwr.errors import InvalidTransition, IdempotencyConflict

def make_plan(rt,p,planner,approver):
    a=rt.knowledge.create_artifact(p,"plan","plan",planner)
    prop=rt.governance.prepare_proposal(p,planner,"CREATE_REVISION",[a],{"artifact_id":a,"payload":{"step":"do"}},"normative_change")
    h=rt.db.one("SELECT payload_hash FROM proposals WHERE proposal_id=?",(prop,))["payload_hash"]
    rt.governance.approve_proposal(prop,approver,h)
    r=rt.knowledge.commit_revision_from_proposal(prop,planner,0)["revision_id"]
    rt.knowledge.set_validity_system(r,"VALID")
    return a,r

def test_workunit_needs_gate_and_valid_inputs(seeded):
    rt,p,planner,operator,approver=seeded
    _,r=make_plan(rt,p,planner,approver)
    wu=rt.execution.create_workunit(p,"execute_plan",[r],operator)
    chk=rt.execution.recompute_readiness(wu,{})
    assert chk["status"]=="BLOCKED"
    gate=rt.decision.evaluate_gate(p,"plan_ready",{"workunit":wu},[r])
    assert gate["result"]=="PASS"
    chk=rt.execution.recompute_readiness(wu,{"plan_ready":"PASS"})
    assert chk["status"]=="READY"

def test_run_idempotency_runtime_success_not_business_success(seeded):
    rt,p,planner,operator,approver=seeded
    _,r=make_plan(rt,p,planner,approver)
    wu=rt.execution.create_workunit(p,"execute_plan",[r],operator)
    rt.execution.recompute_readiness(wu,{"plan_ready":"PASS"})
    v=rt.db.one("SELECT version FROM workunits WHERE workunit_id=?",(wu,))["version"]
    rr=rt.execution.start_run(wu,operator,v,"run-key","corr-1")
    same=rt.execution.start_run(wu,operator,v,"run-key","corr-1")
    assert rr==same
    rt.execution.finish_run(rr["run_id"],"COMPLETED",{"exit_code":0})
    ev=rt.execution.add_evidence(p,"automated_result",operator,[r],{"pass":False},"AUTHORITATIVE",rr["run_id"])
    gate=rt.decision.evaluate_gate(p,"result_verified",{"workunit":wu},[r],[ev])
    assert gate["result"]=="FAIL"
    assert rt.db.one("SELECT status FROM workunits WHERE workunit_id=?",(wu,))["status"]=="SUCCEEDED"

def test_failure_root_recovery_checkpoint_resume(seeded):
    rt,p,planner,operator,approver=seeded
    intent=rt.knowledge.create_artifact(p,"intent","intent",planner)
    plan=rt.knowledge.create_artifact(p,"plan","plan",planner)
    def rev(a,payload,ver):
        prop=rt.governance.prepare_proposal(p,planner,"CREATE_REVISION",[a],{"artifact_id":a,"payload":payload},"normative_change")
        h=rt.db.one("SELECT payload_hash FROM proposals WHERE proposal_id=?",(prop,))["payload_hash"]
        rt.governance.approve_proposal(prop,approver,h); return rt.knowledge.commit_revision_from_proposal(prop,planner,ver)["revision_id"]
    ri=rev(intent,{"goal":"g"},0); rp=rev(plan,{"bad":True},0)
    rt.knowledge.set_validity_system(ri,"VALID"); rt.knowledge.set_validity_system(rp,"FAILED")
    rt.knowledge.create_trace_link(p,rp,"REVISION",ri,"DERIVED_FROM","HARD",True,"MARK_STALE",planner)
    fid=rt.decision.record_failure(p,"scope-1","contract_mismatch","VERIFY","test-1",detected_revision_id=rp,violations=["MISMATCH"])
    # detection point retained separately from root/resume
    rt.decision.confirm_root(fid,rp,"REVISE_PLAN",approver)
    impact=rt.knowledge.compute_impact(p,"FAILURE",fid,rp,apply=True)
    rec=rt.decision.create_recovery_plan(fid,impact["impact_id"])
    cp=rt.execution.create_checkpoint(p,"scope-1")
    resume=rt.execution.reconcile_checkpoint(cp)
    assert rec and rp in resume["current_non_valid"][0].values() or any(x["revision_id"]==rp for x in resume["current_non_valid"])
    f=rt.db.one("SELECT * FROM failures WHERE failure_id=?",(fid,))
    assert f["detected_ref"]=="test-1" and f["root_revision_id"]==rp and f["resume_candidate"]=="REVISE_PLAN"

def test_loopguard_escalates_same_signature(seeded):
    rt,p,planner,operator,approver=seeded
    f1=rt.decision.record_failure(p,"scope","tool_timeout","EXEC","tool",violations=["TIMEOUT"])
    f2=rt.decision.record_failure(p,"scope","tool_timeout","EXEC","tool",violations=["TIMEOUT"])
    assert rt.decision.route_failure(f2)=="ESCALATE"

def test_checkpoint_resume_api_reconciles_current_truth(seeded):
    rt,p,planner,operator,approver=seeded
    _,r=make_plan(rt,p,planner,approver)
    cp=rt.execution.create_checkpoint(p,"scope")
    rt.knowledge.set_validity_system(r,"STALE")
    resumed=rt.execution.resume_from_checkpoint(cp)
    assert any(x["revision_id"]==r and x["validity_state"]=="STALE" for x in resumed["current_non_valid"])
