import pytest
from gwr.errors import AuthorityDenied, ApprovalMismatch, ValidationError, IdempotencyConflict

def test_role_prompt_is_not_authority_boundary(seeded):
    rt,p,planner,operator,approver=seeded
    with pytest.raises(AuthorityDenied):
        rt.governance.authorize(planner,"APPROVE",{})
    assert rt.governance.authorize(approver,"APPROVE",{})

def test_frozen_proposal_hash_and_self_approval(seeded):
    rt,p,planner,operator,approver=seeded
    aid=rt.knowledge.create_artifact(p,"intent","intent-1",planner)
    payload={"artifact_id":aid,"payload":{"goal":"x"}}
    prop=rt.governance.prepare_proposal(p,planner,"CREATE_REVISION",[aid],payload,"normative_change")
    row=rt.db.one("SELECT * FROM proposals WHERE proposal_id=?",(prop,))
    with pytest.raises(ApprovalMismatch): rt.governance.approve_proposal(prop,approver,"bad-hash")
    appr=rt.governance.approve_proposal(prop,approver,row["payload_hash"])
    out=rt.knowledge.commit_revision_from_proposal(prop,planner,0)
    assert out["revision_id"]
    assert rt.db.one("SELECT status FROM proposals WHERE proposal_id=?",(prop,))["status"]=="COMMITTED"

def test_proposal_idempotency_conflict(seeded):
    rt,p,planner,_,_=seeded
    a=rt.knowledge.create_artifact(p,"intent","k",planner)
    rt.governance.prepare_proposal(p,planner,"CREATE_REVISION",[a],{"artifact_id":a,"payload":{"x":1}},"normative_change","idem")
    with pytest.raises(IdempotencyConflict):
        rt.governance.prepare_proposal(p,planner,"CREATE_REVISION",[a],{"artifact_id":a,"payload":{"x":2}},"normative_change","idem")

def test_audit_is_database_append_only(seeded):
    rt,p,planner,_,_=seeded
    rt.knowledge.create_artifact(p,"intent","audit-key",planner)
    ev=rt.db.one("SELECT event_id FROM audit_events WHERE project_id=? ORDER BY timestamp DESC LIMIT 1",(p,))["event_id"]
    # Backend-neutral assertion: SQLite raises sqlite3.IntegrityError while
    # PostgreSQL raises a server-side trigger exception. The semantic contract
    # is the immutable append-only guard and its reason, not a driver-specific
    # exception class.
    with pytest.raises(Exception, match="append-only"):
        rt.db.conn.execute("DELETE FROM audit_events WHERE event_id=?",(ev,))
