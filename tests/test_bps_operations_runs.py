from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.runtime import GovernedWorkflowRuntime
from gwr.product import ProjectDashboardService


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
PASSWORD = "operations-runs-password"


def _runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(tmp_path / "operations-runs.db"),
        auth_secret="r" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
    )
    actor = rt.governance.create_actor("HUMAN", "runs-operator", [], [])
    outsider = rt.governance.create_actor("HUMAN", "runs-outsider", [], [])
    rt.auth.register_human(actor, "runs-operator", PASSWORD)
    rt.auth.register_human(outsider, "runs-outsider", PASSWORD)

    tenant = rt.tenancy.create_tenant("Runs Tenant", actor, tenant_id="tenant_runs")
    workspace = rt.tenancy.create_workspace(tenant, "Runs Workspace", actor, workspace_id="workspace_runs")
    project = rt.create_scoped_project("Visible Runs", tenant, workspace, actor, project_id="project_runs")

    hidden_tenant = rt.tenancy.create_tenant("Hidden Runs Tenant", outsider, tenant_id="tenant_runs_hidden")
    hidden_workspace = rt.tenancy.create_workspace(hidden_tenant, "Hidden Runs Workspace", outsider, workspace_id="workspace_runs_hidden")
    hidden_project = rt.create_scoped_project("Hidden Runs", hidden_tenant, hidden_workspace, outsider, project_id="project_runs_hidden")
    return rt, actor, project, hidden_project


def _app(rt):
    return create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "test-version",
            "build_sha": "runs-build-sha",
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "canonical",
        },
        web_root=WEB,
    )


def _insert_run(rt, project_id, actor_id, suffix, status, started, finished=None):
    workunit_id = "wu_" + suffix
    run_id = "run_" + suffix
    rt.db.conn.execute(
        "INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            workunit_id, project_id, "ANALYZE", '["rev_in_' + suffix + '"]',
            "[]", "[]", "[]", "[]", "{}", "{}", "{}", "{}", "[]",
            "RUNNING" if status == "RUNNING" else "SUCCEEDED", 0,
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            run_id, workunit_id, 1, actor_id, '["rev_in_' + suffix + '"]',
            started, finished, status, "{}", '["rev_out_' + suffix + '"]',
            '["ev_' + suffix + '"]', None, "corr_" + suffix,
        ),
    )
    return workunit_id, run_id


def test_operations_runs_projection_is_cross_project_authorized(tmp_path, monkeypatch):
    rt, actor, project, hidden_project = _runtime(tmp_path, monkeypatch)
    _, running = _insert_run(rt, project, actor, "running", "RUNNING", "2026-09-26T01:00:00+00:00")
    wu_done, completed = _insert_run(rt, project, actor, "completed", "COMPLETED", "2026-09-26T00:00:00+00:00", "2026-09-26T00:03:00+00:00")
    _, failed = _insert_run(rt, project, actor, "failed", "FAILED", "2026-09-25T23:00:00+00:00", "2026-09-25T23:01:00+00:00")
    _, hidden = _insert_run(rt, hidden_project, "SYSTEM", "hidden", "RUNNING", "2026-09-26T02:00:00+00:00")

    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "orch_completed", project, rt.domain.domain_id, "COMPLETED",
            "phase-done", 0, "PASS", 0, "2026-09-26T00:00:00+00:00",
            "2026-09-26T00:03:00+00:00", None, "{}",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "phase_completed", "orch_completed", "phase-done", 0, 0,
            wu_done, completed, "COMPLETED", "PASS", None, None,
            "2026-09-26T00:00:00+00:00", "2026-09-26T00:03:00+00:00", "{}",
        ),
    )
    rt.governance.append_audit(
        project, actor, "RUN_SUCCEEDED_RUNTIME", "ExecutionRun", completed,
        run_id=completed,
    )
    rt.db.conn.commit()

    client = TestClient(_app(rt))
    assert client.get("/browser/operations/runs").status_code == 401
    assert client.post(
        "/browser/auth/login",
        json={"username": "runs-operator", "password": PASSWORD},
    ).status_code == 200

    response = client.get("/browser/operations/runs")
    assert response.status_code == 200
    body = response.json()
    assert body["query_status"] == "COMPLETE"
    assert body["build_sha"] == "runs-build-sha"
    assert body["scope"]["project_count"] == 1

    runs = {row["run_id"]: row for row in body["runs"]}
    assert set(runs) == {running, completed, failed}
    assert hidden not in runs
    assert runs[running]["runtime_status"] == "RUNNING"
    assert runs[completed]["runtime_status"] == "COMPLETED"
    assert runs[failed]["runtime_status"] == "FAILED"
    assert runs[completed]["phase"] == {
        "phase_execution_id": "phase_completed",
        "orchestration_id": "orch_completed",
        "phase_id": "phase-done",
        "status": "COMPLETED",
    }
    assert runs[completed]["input_revision_ids"] == ["rev_in_completed"]
    assert runs[completed]["produced_revision_ids"] == ["rev_out_completed"]
    assert runs[completed]["evidence_ids"] == ["ev_completed"]
    assert runs[completed]["latest_event"]["action"] == "RUN_SUCCEEDED_RUNTIME"
    rt.close()


def test_operations_runs_zero_and_browser_contract(tmp_path, monkeypatch):
    rt, _, _, _ = _runtime(tmp_path, monkeypatch)
    client = TestClient(_app(rt))
    assert client.post(
        "/browser/auth/login",
        json={"username": "runs-operator", "password": PASSWORD},
    ).status_code == 200
    body = client.get("/browser/operations/runs").json()
    assert body["query_status"] == "COMPLETE"
    assert body["runs"] == []

    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert 'id="operationsRouteView"' in html
    assert 'id="operationsRunsView"' in html
    assert 'api("/browser/operations/runs")' in js
    assert 'item.id === "operations"' in js
    assert '"/app/operations/runs"' in js
    assert "No runs exist in the current authorized scope." in js
    assert "/app/projects/" not in js
    rt.close()


def test_operations_runs_unavailable_is_not_encoded_as_empty(tmp_path, monkeypatch):
    rt, _, _, _ = _runtime(tmp_path, monkeypatch)

    def unavailable(self, actor_id, *, build_sha):
        raise RuntimeError("controlled operations-runs outage")

    monkeypatch.setattr(ProjectDashboardService, "operations_runs", unavailable)
    client = TestClient(_app(rt), raise_server_exceptions=False)
    assert client.post(
        "/browser/auth/login",
        json={"username": "runs-operator", "password": PASSWORD},
    ).status_code == 200
    response = client.get("/browser/operations/runs")
    assert response.status_code == 500

    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert "Runs data unavailable — " in js
    assert 'homeEmpty("Runs index unavailable.", 7)' in js
    rt.close()


def test_operations_route_renderers_hide_each_other():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    for fn in (
        "renderLockedRoute", "renderDiagnosticsRoute", "renderHomeRoute",
        "renderProjectsRoute", "renderAccessRoute",
    ):
        start = js.index("function " + fn)
        end = js.find("\nfunction ", start + 10)
        block = js[start:end if end >= 0 else len(js)]
        assert '$("#operationsRouteView").hidden = true;' in block
