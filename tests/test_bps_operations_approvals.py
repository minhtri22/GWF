from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
PASSWORD = "operations-approvals-password"


def _fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(tmp_path / "operations-approvals.db"),
        auth_secret="q" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
    )
    approver = rt.governance.create_actor("HUMAN", "approver-user", ["approver"], [])
    proposer = rt.governance.create_actor("HUMAN", "proposer-user", ["operator"], [])
    reviewer = rt.governance.create_actor("HUMAN", "reviewer-user", [], [])
    outsider = rt.governance.create_actor("HUMAN", "outsider-user", ["approver"], [])
    for actor, username in (
        (approver, "approver-user"), (proposer, "proposer-user"),
        (reviewer, "reviewer-user"), (outsider, "outsider-user"),
    ):
        rt.auth.register_human(actor, username, PASSWORD)

    tenant = rt.tenancy.create_tenant("Approval Tenant", approver, tenant_id="tenant_approval")
    workspace = rt.tenancy.create_workspace(tenant, "Approval Workspace", approver, workspace_id="workspace_approval")
    project = rt.create_scoped_project("Approval Project", tenant, workspace, approver, project_id="project_approval")
    rt.tenancy.add_project_member(project, proposer, "RESEARCHER", approver)
    rt.tenancy.add_project_member(project, reviewer, "REVIEWER", approver)

    hidden_tenant = rt.tenancy.create_tenant("Hidden Approval Tenant", outsider, tenant_id="tenant_approval_hidden")
    hidden_workspace = rt.tenancy.create_workspace(hidden_tenant, "Hidden Approval Workspace", outsider, workspace_id="workspace_approval_hidden")
    hidden_project = rt.create_scoped_project("Hidden Approval Project", hidden_tenant, hidden_workspace, outsider, project_id="project_approval_hidden")

    def proposal(pid_project, who, suffix):
        return rt.governance.prepare_proposal(
            pid_project, who, "CREATE_REVISION",
            [{"kind": "Artifact", "id": "artifact_" + suffix}],
            {"revision": suffix, "content": "frozen-" + suffix},
            required_approval_policy="normative_change",
            idempotency_key="approval-" + suffix,
        )

    pending = proposal(project, proposer, "pending")
    rejectable = proposal(project, proposer, "rejectable")
    self_pending = proposal(project, approver, "self")
    hidden = proposal(hidden_project, outsider, "hidden")
    return rt, approver, reviewer, project, pending, rejectable, self_pending, hidden


def _app(rt):
    return create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "test-version",
            "build_sha": "approvals-build-sha",
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "canonical",
        },
        web_root=WEB,
    )


def _login(client, username):
    response = client.post("/browser/auth/login", json={"username": username, "password": PASSWORD})
    assert response.status_code == 200


def test_approvals_projection_authority_hash_and_decision_history(tmp_path, monkeypatch):
    rt, approver, reviewer, project, pending, rejectable, self_pending, hidden = _fixture(tmp_path, monkeypatch)

    reviewer_client = TestClient(_app(rt))
    _login(reviewer_client, "reviewer-user")
    reviewer_body = reviewer_client.get("/browser/operations/approvals").json()
    ids = {x["proposal_id"] for x in reviewer_body["pending"]}
    assert pending in ids and rejectable in ids
    assert hidden not in ids
    assert all(x["can_approve"] is False for x in reviewer_body["pending"])
    assert reviewer_client.post(
        f"/browser/operations/approvals/{pending}/approve",
        json={"expected_hash": next(x["payload_hash"] for x in reviewer_body["pending"] if x["proposal_id"] == pending)},
    ).status_code == 404

    client = TestClient(_app(rt))
    _login(client, "approver-user")
    body = client.get("/browser/operations/approvals").json()
    pending_row = next(x for x in body["pending"] if x["proposal_id"] == pending)
    assert pending_row["can_approve"] is True
    assert pending_row["frozen_payload"] == {"revision": "pending", "content": "frozen-pending"}
    assert pending_row["resource_refs"] == [{"kind": "Artifact", "id": "artifact_pending"}]

    mismatch = client.post(
        f"/browser/operations/approvals/{pending}/approve",
        json={"expected_hash": "not-the-frozen-hash"},
    )
    assert mismatch.status_code == 400
    assert rt.db.one("SELECT status FROM proposals WHERE proposal_id=?", (pending,))["status"] == "PENDING_APPROVAL"

    self_row = next(x for x in body["pending"] if x["proposal_id"] == self_pending)
    self_denied = client.post(
        f"/browser/operations/approvals/{self_pending}/approve",
        json={"expected_hash": self_row["payload_hash"]},
    )
    assert self_denied.status_code == 403
    assert rt.db.one("SELECT status FROM proposals WHERE proposal_id=?", (self_pending,))["status"] == "PENDING_APPROVAL"

    approved = client.post(
        f"/browser/operations/approvals/{pending}/approve",
        json={"expected_hash": pending_row["payload_hash"]},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"

    refreshed = client.get("/browser/operations/approvals").json()
    assert pending not in {x["proposal_id"] for x in refreshed["pending"]}
    decision = next(x for x in refreshed["decisions"] if x["proposal_id"] == pending)
    assert decision["decision"] == "APPROVED"
    assert decision["proposal_hash"] == pending_row["payload_hash"]
    assert decision["approver_actor_id"] == approver

    reject_row = next(x for x in refreshed["pending"] if x["proposal_id"] == rejectable)
    empty_reason = client.post(
        f"/browser/operations/approvals/{rejectable}/reject",
        json={"expected_hash": reject_row["payload_hash"], "reason": "   "},
    )
    assert empty_reason.status_code == 422
    rejected = client.post(
        f"/browser/operations/approvals/{rejectable}/reject",
        json={"expected_hash": reject_row["payload_hash"], "reason": "insufficient evidence"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["reason"] == "insufficient evidence"
    after_reject = client.get("/browser/operations/approvals").json()
    rejected_decision = next(x for x in after_reject["decisions"] if x["proposal_id"] == rejectable)
    assert rejected_decision["conditions"]["reason"] == "insufficient evidence"

    actions = [
        row["action"] for row in rt.db.all(
            "SELECT action FROM audit_events WHERE project_id=? ORDER BY timestamp,event_id",
            (project,),
        )
    ]
    assert "APPROVE_PROPOSAL" in actions
    assert "AUTHENTICATED_APPROVAL" in actions
    assert "REJECT_PROPOSAL" in actions
    assert "AUTHENTICATED_REJECTION" in actions
    rt.close()


def test_existing_bearer_approval_api_remains_valid(tmp_path, monkeypatch):
    rt, _, _, _, pending, _, _, _ = _fixture(tmp_path, monkeypatch)
    client = TestClient(_app(rt))
    token = client.post(
        "/auth/login",
        json={"username": "approver-user", "password": PASSWORD},
    ).json()["access_token"]
    proposal = client.get(
        f"/proposals/{pending}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert proposal.status_code == 200
    approved = client.post(
        f"/proposals/{pending}/approve",
        json={"expected_hash": proposal.json()["payload_hash"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert approved.status_code == 200
    rt.close()


def test_approvals_ui_preserves_decision_vs_apply_boundary():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert 'id="operationsApprovalsView"' in html
    assert "A decision changes proposal status only." in html
    assert 'api("/browser/operations/approvals")' in js
    assert "Approve exact proposal hash" in js
    assert "It does not apply the underlying governed change." in js
    assert "Reject requires a reason." in js
