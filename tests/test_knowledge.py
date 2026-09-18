import pytest
from gwr.errors import ValidationError, StaleVersion

def approved_revision(rt,p,proposer,approver,artifact,payload,version):
    prop=rt.governance.prepare_proposal(p,proposer,"CREATE_REVISION",[artifact],{"artifact_id":artifact,"payload":payload},"normative_change")
    h=rt.db.one("SELECT payload_hash FROM proposals WHERE proposal_id=?",(prop,))["payload_hash"]
    rt.governance.approve_proposal(prop,approver,h)
    return rt.knowledge.commit_revision_from_proposal(prop,proposer,version)["revision_id"]

def test_revision_immutable_and_stale_version(seeded):
    rt,p,planner,_,approver=seeded
    a=rt.knowledge.create_artifact(p,"intent","intent",planner)
    r1=approved_revision(rt,p,planner,approver,a,{"v":1},0)
    with pytest.raises(ValidationError): rt.knowledge.create_revision(a,{"v":2},planner,1)
    # stale expected version on approved proposal
    prop=rt.governance.prepare_proposal(p,planner,"CREATE_REVISION",[a],{"artifact_id":a,"payload":{"v":2}},"normative_change")
    h=rt.db.one("SELECT payload_hash FROM proposals WHERE proposal_id=?",(prop,))["payload_hash"]
    rt.governance.approve_proposal(prop,approver,h)
    with pytest.raises(StaleVersion): rt.knowledge.commit_revision_from_proposal(prop,planner,0)
    assert rt.knowledge.get_revision(r1)["structured_payload"]=={"v":1}

def test_hard_dependency_invalidation_propagates(seeded):
    rt,p,planner,_,approver=seeded
    intent=rt.knowledge.create_artifact(p,"intent","intent",planner)
    plan=rt.knowledge.create_artifact(p,"plan","plan",planner)
    r_int=approved_revision(rt,p,planner,approver,intent,{"goal":"a"},0)
    r_plan=approved_revision(rt,p,planner,approver,plan,{"steps":[1]},0)
    rt.knowledge.set_validity_system(r_int,"VALID"); rt.knowledge.set_validity_system(r_plan,"VALID")
    rt.knowledge.create_trace_link(p,r_plan,"REVISION",r_int,"DERIVED_FROM","HARD",True,"MARK_STALE",planner)
    r_int2=approved_revision(rt,p,planner,approver,intent,{"goal":"b"},1)
    assert rt.knowledge.get_validity(r_plan)=="STALE"
    impacts=rt.db.all("SELECT * FROM impacts WHERE project_id=?",(p,))
    assert any(r_plan in row["affected_nodes"] for row in impacts)
    assert rt.knowledge.get_validity(r_int)=="SUPERSEDED"
    assert rt.knowledge.get_validity(r_int2)=="UNVERIFIED"
