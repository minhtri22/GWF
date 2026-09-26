from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"


def home_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    monkeypatch.delenv("GWR_TEST_DATABASE_URL", raising=False)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(tmp_path / "home.db"),
        auth_secret="h" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
    )
    actor = rt.governance.create_actor("HUMAN", "home-operator", [], [])
    rt.auth.register_human(actor, "home-operator", "home-operator-password")
    tenant_id = rt.tenancy.create_tenant("Research Tenant", actor)
    workspace_id = rt.tenancy.create_workspace(tenant_id, "Primary", actor)
    return rt, actor, tenant_id, workspace_id


def home_app(rt):
    return create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "test-version",
            "build_sha": "home-build-sha",
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "canonical",
        },
        web_root=WEB,
    )


def seed_home_activity(rt, actor, tenant_id, workspace_id):
    p1 = rt.create_scoped_project(
        "Executing Project", tenant_id, workspace_id, actor, project_id="project_home_1"
    )
    p2 = rt.create_scoped_project(
        "Archived Project", tenant_id, workspace_id, actor, project_id="project_home_2"
    )
    rt.db.conn.execute("UPDATE project_lifecycle SET status='ARCHIVED' WHERE project_id=?", (p2,))
    rt.db.conn.execute(
        "INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "wu_home_1", p1, "ANALYZE", "[]", "[]", "[]", "[]", "[]",
            "{}", "{}", "{}", "{}", "[]", "RUNNING", 0,
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "run_home_1", "wu_home_1", 1, actor, "[]",
            "2026-09-23T12:00:00+00:00", None, "RUNNING", None,
            "[]", "[]", None, "corr-home",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "orch_home_1", p1, rt.domain.domain_id, "RUNNING", "phase-alpha",
            0, None, 0, "2026-09-23T12:00:00+00:00",
            "2026-09-23T12:00:00+00:00", None, "{}",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "phase_home_1", "orch_home_1", "phase-alpha", 0, 0,
            "wu_home_1", "run_home_1", "RUNNING", None, None, None,
            "2026-09-23T12:00:00+00:00", None, "{}",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO proposals VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            "proposal_home_1", p1, actor, "APPROVE_TEST", "[]", "{}",
            "hash-home", None, "PENDING_APPROVAL",
            "2026-09-23T12:01:00+00:00", "idem-home",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO failures VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "failure_home_1", p1, "wu_home_1", "TEST_FAILURE", "EXECUTION",
            "run_home_1", None, None, "[]", None, None, "UNRESOLVED",
            None, "HIGH", "sig-home", "OPEN",
            "2026-09-23T12:02:00+00:00", None,
        ),
    )
    rt.governance.append_audit(
        p1, actor, "RUN_STARTED", "ExecutionRun", "run_home_1", run_id="run_home_1"
    )
    rt.db.conn.commit()
    return p1, p2


def test_home_summary_exact_semantics_and_authorization(tmp_path, monkeypatch):
    rt, actor, tenant_id, workspace_id = home_runtime(tmp_path, monkeypatch)
    p1, _ = seed_home_activity(rt, actor, tenant_id, workspace_id)
    client = TestClient(home_app(rt))

    assert client.get("/browser/home-summary").status_code == 401

    login = client.post(
        "/browser/auth/login",
        json={"username": "home-operator", "password": "home-operator-password"},
    )
    assert login.status_code == 200

    response = client.get("/browser/home-summary")
    assert response.status_code == 200
    body = response.json()

    assert body["build_sha"] == "home-build-sha"
    assert body["scope"] == {
        "mode": "ALL_AUTHORIZED",
        "label": "All authorized projects",
        "project_count": 2,
    }
    assert body["query_status"] == "COMPLETE"
    assert body["kpis"] == {
        "total_projects": 2,
        "lifecycle_active": 1,
        "executing_now": 1,
        "running_runs": 1,
        "pending_approvals": 1,
        "attention_required": 2,
        "core_health": "HEALTHY",
    }

    assert [row["project_id"] for row in body["executing_projects"]] == [p1]
    project = body["executing_projects"][0]
    assert project["lifecycle"] == "ACTIVE"
    assert project["execution_activity"] == "EXECUTING"
    assert project["orchestration_id"] == "orch_home_1"
    assert project["phase_execution_id"] == "phase_home_1"
    assert project["phase_label"] == "phase-alpha"
    assert project["current_actor"] == actor
    assert project["running_run_id"] == "run_home_1"
    assert project["attention_count"] == 2

    assert len(body["live_runs"]) == 1
    assert body["live_runs"][0]["run_id"] == "run_home_1"
    assert body["live_runs"][0]["status"] == "RUNNING"
    assert {item["kind"] for item in body["attention"]} == {
        "PENDING_APPROVAL", "FAILURE"
    }
    assert body["recent_activity"]
    assert body["generated_at"]
    rt.close()


def test_home_capability_is_live_module(tmp_path, monkeypatch):
    rt, _, _, _ = home_runtime(tmp_path, monkeypatch)
    client = TestClient(home_app(rt))
    capabilities = {
        item["id"]: item for item in client.get("/browser/bootstrap").json()["capabilities"]
    }
    assert capabilities["home"]["state"] == "LIVE_MODULE"
    assert capabilities["home"]["slice"] == "BPS-M01"
    assert capabilities["home"]["route"] == "/app/home"
    rt.close()
