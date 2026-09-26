from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.product import ProjectDashboardService
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
PASSWORD = "operations-audit-password"


def _fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(tmp_path / "operations-audit.db"),
        auth_secret="u" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
    )
    actor = rt.governance.create_actor("HUMAN", "audit-user", [], [])
    outsider = rt.governance.create_actor("HUMAN", "audit-outsider", [], [])
    rt.auth.register_human(actor, "audit-user", PASSWORD)
    rt.auth.register_human(outsider, "audit-outsider", PASSWORD)
    tenant = rt.tenancy.create_tenant("Audit Tenant", actor, tenant_id="tenant_audit")
    workspace = rt.tenancy.create_workspace(tenant, "Audit Workspace", actor, workspace_id="workspace_audit")
    project = rt.create_scoped_project("Audit Project", tenant, workspace, actor, project_id="project_audit")
    hidden_tenant = rt.tenancy.create_tenant("Hidden Audit Tenant", outsider, tenant_id="tenant_audit_hidden")
    hidden_workspace = rt.tenancy.create_workspace(hidden_tenant, "Hidden Audit Workspace", outsider, workspace_id="workspace_audit_hidden")
    hidden_project = rt.create_scoped_project("Hidden Audit Project", hidden_tenant, hidden_workspace, outsider, project_id="project_audit_hidden")
    return rt, actor, outsider, project, hidden_project


def _app(rt):
    return create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "test-version",
            "build_sha": "audit-build-sha",
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "canonical",
        },
        web_root=WEB,
    )


def test_operations_audit_projection_preserves_exact_linkage_and_scope(tmp_path, monkeypatch):
    rt, actor, outsider, project, hidden_project = _fixture(tmp_path, monkeypatch)
    event_id = rt.governance.append_audit(
        project, actor, "TEST_AUDIT_ACTION", "Artifact", "artifact_visible",
        before_version="v1", after_version="v2",
        proposal_id="proposal_visible", approval_id="approval_visible",
        run_id="run_visible", decision_id="decision_visible",
        correlation_id="corr_visible", reason_code="EXACT_REASON",
        metadata={"source": "test"},
    )
    hidden_event = rt.governance.append_audit(
        hidden_project, outsider, "HIDDEN_ACTION", "Artifact", "artifact_hidden",
        reason_code="HIDDEN_REASON",
    )
    rt.db.conn.commit()

    client = TestClient(_app(rt))
    assert client.get("/browser/operations/audit").status_code == 401
    assert client.post("/browser/auth/login", json={"username": "audit-user", "password": PASSWORD}).status_code == 200
    body = client.get("/browser/operations/audit").json()
    assert body["query_status"] == "COMPLETE"
    assert body["build_sha"] == "audit-build-sha"
    ids = {row["event_id"] for row in body["events"]}
    assert event_id in ids
    assert hidden_event not in ids
    row = next(row for row in body["events"] if row["event_id"] == event_id)
    assert row["project_id"] == project
    assert row["actor_id"] == actor
    assert row["action"] == "TEST_AUDIT_ACTION"
    assert row["resource_type"] == "Artifact"
    assert row["resource_id"] == "artifact_visible"
    assert row["proposal_id"] == "proposal_visible"
    assert row["approval_id"] == "approval_visible"
    assert row["run_id"] == "run_visible"
    assert row["decision_id"] == "decision_visible"
    assert row["correlation_id"] == "corr_visible"
    assert row["reason_code"] == "EXACT_REASON"
    assert row["before_version"] == "v1"
    assert row["after_version"] == "v2"
    assert row["metadata_hash"]
    assert "outcome" not in row
    rt.close()


def test_operations_audit_zero_and_unavailable_are_distinct(tmp_path, monkeypatch):
    rt, _, _, _, _ = _fixture(tmp_path, monkeypatch)
    client = TestClient(_app(rt))
    assert client.post("/browser/auth/login", json={"username": "audit-user", "password": PASSWORD}).status_code == 200
    body = client.get("/browser/operations/audit").json()
    assert body["query_status"] == "COMPLETE"
    assert isinstance(body["events"], list)

    def unavailable(self, actor_id, *, build_sha):
        raise RuntimeError("controlled audit outage")

    monkeypatch.setattr(ProjectDashboardService, "operations_audit", unavailable)
    broken = TestClient(_app(rt), raise_server_exceptions=False)
    assert broken.post("/browser/auth/login", json={"username": "audit-user", "password": PASSWORD}).status_code == 200
    assert broken.get("/browser/operations/audit").status_code == 500
    rt.close()


def test_operations_audit_ui_does_not_invent_outcome():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert 'id="operationsAuditView"' in html
    assert "no generic outcome is inferred" in html
    assert 'api("/browser/operations/audit")' in js
    assert "event.reason_code" in js
    assert "event.outcome" not in js
