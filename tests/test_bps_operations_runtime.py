from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.product import ProjectDashboardService
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import canonical_json


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
PASSWORD = "runtime-test-password"


def _workunit(rt, project_id: str, workunit_id: str, *, conflict=None):
    rt.db.conn.execute(
        "INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            workunit_id, project_id, "execute_plan",
            "[]", "[]", "[]", "[]", "[]",
            canonical_json({"role": "operator"}),
            canonical_json({}),
            canonical_json({"max_attempts": 3}),
            canonical_json({}),
            canonical_json(conflict or []),
            "READY", 0,
        ),
    )
    rt.db.conn.commit()
    return workunit_id


def _runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(tmp_path / "ops-runtime.db"),
        auth_secret="r" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
    )
    owner = rt.governance.create_actor("HUMAN", "runtime-owner", [], [])
    outsider = rt.governance.create_actor("HUMAN", "runtime-outsider", [], [])
    rt.auth.register_human(owner, "runtime-owner", PASSWORD)
    rt.auth.register_human(outsider, "runtime-outsider", PASSWORD)
    tenant = rt.tenancy.create_tenant("Runtime Tenant", owner, tenant_id="tenant_runtime")
    workspace = rt.tenancy.create_workspace(
        tenant, "Runtime Workspace", owner, workspace_id="workspace_runtime"
    )
    project = rt.create_scoped_project(
        "Runtime Project", tenant, workspace, owner, project_id="project_runtime"
    )
    hidden_tenant = rt.tenancy.create_tenant(
        "Hidden Runtime Tenant", outsider, tenant_id="tenant_runtime_hidden"
    )
    hidden_workspace = rt.tenancy.create_workspace(
        hidden_tenant, "Hidden Runtime Workspace", outsider,
        workspace_id="workspace_runtime_hidden",
    )
    hidden_project = rt.create_scoped_project(
        "Hidden Runtime Project", hidden_tenant, hidden_workspace, outsider,
        project_id="project_runtime_hidden",
    )
    return rt, owner, outsider, tenant, workspace, project, hidden_project


def _app(rt):
    return create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "test-version",
            "build_sha": "runtime-build-sha",
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "canonical",
        },
        web_root=WEB,
    )


def _login(client, username):
    response = client.post(
        "/browser/auth/login",
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 200


def _worker(rt, project_id: str, name: str, *, labels=None):
    actor = rt.governance.create_actor("AGENT", name, ["operator"], [project_id])
    worker = rt.distributed.register_worker(
        actor,
        capabilities={"labels": labels or ["python"], "workunit_types": ["execute_plan"]},
        resources={"cpu": 4, "memory_mb": 4096, "gpu": 0},
        heartbeat_ttl_seconds=120,
    )
    return actor, worker


def test_operations_runtime_projection_is_authorized_redacted_and_historical(tmp_path, monkeypatch):
    rt, owner, outsider, tenant, workspace, project, hidden_project = _runtime(tmp_path, monkeypatch)

    _, worker_old = _worker(rt, project, "old-worker")
    _, worker_new = _worker(rt, project, "new-worker")
    _, worker_orphan = _worker(rt, project, "unreferenced-worker")
    _, hidden_worker = _worker(rt, hidden_project, "hidden-worker")

    recovery_wu = _workunit(rt, project, "wu_runtime_recovery", conflict=["dataset:alpha"])
    recovery_job = rt.distributed.enqueue_workunit(
        recovery_wu,
        idempotency_key="runtime-recovery",
        required_resources={"cpu": 2, "memory_mb": 1024},
        required_capabilities=["python"],
        max_attempts=3,
    )
    first = rt.distributed.lease_next(worker_old, lease_seconds=5)
    assert first["job_id"] == recovery_job
    first_run = rt.distributed.start_job(recovery_job, worker_old, first["lease_token"])
    rt.db.conn.execute(
        "UPDATE distributed_jobs SET lease_expires_at='2000-01-01T00:00:00+00:00' WHERE job_id=?",
        (recovery_job,),
    )
    rt.db.conn.commit()
    assert recovery_job in rt.distributed.recover_expired_leases()
    second = rt.distributed.lease_next(worker_new)
    assert second["job_id"] == recovery_job

    ready_wu = _workunit(rt, project, "wu_runtime_ready")
    ready_job = rt.distributed.enqueue_workunit(ready_wu, idempotency_key="runtime-ready")

    running_wu = _workunit(rt, project, "wu_runtime_running")
    running_job = rt.distributed.enqueue_workunit(running_wu, idempotency_key="runtime-running")
    running_lease = rt.distributed.lease_next(worker_new)
    assert running_lease["job_id"] == running_job
    running_started = rt.distributed.start_job(running_job, worker_new, running_lease["lease_token"])

    succeeded_wu = _workunit(rt, project, "wu_runtime_succeeded")
    succeeded_job = rt.distributed.enqueue_workunit(succeeded_wu, idempotency_key="runtime-succeeded")
    succeeded_lease = rt.distributed.lease_next(worker_new)
    assert succeeded_lease["job_id"] == succeeded_job
    rt.distributed.start_job(succeeded_job, worker_new, succeeded_lease["lease_token"])
    rt.distributed.complete_job(
        succeeded_job, worker_new, succeeded_lease["lease_token"],
        effect_key="runtime-effect", result={"ok": True},
    )

    failed_wu = _workunit(rt, project, "wu_runtime_failed")
    failed_job = rt.distributed.enqueue_workunit(failed_wu, idempotency_key="runtime-failed")
    failed_lease = rt.distributed.lease_next(worker_new)
    assert failed_lease["job_id"] == failed_job
    rt.distributed.start_job(failed_job, worker_new, failed_lease["lease_token"])
    rt.distributed.fail_job(
        failed_job, worker_new, failed_lease["lease_token"],
        error_code="RUNTIME_TEST_FAILURE", retryable=False,
    )

    hidden_wu = _workunit(rt, hidden_project, "wu_runtime_hidden")
    hidden_job = rt.distributed.enqueue_workunit(hidden_wu, idempotency_key="runtime-hidden")
    hidden_lease = rt.distributed.lease_next(hidden_worker)
    assert hidden_lease["job_id"] == hidden_job

    client = TestClient(_app(rt))
    assert client.get("/browser/operations/runtime").status_code == 401
    _login(client, "runtime-owner")
    response = client.get("/browser/operations/runtime")
    assert response.status_code == 200
    body = response.json()

    assert body["build_sha"] == "runtime-build-sha"
    assert body["query_status"] == "COMPLETE"
    assert body["scope"] == {
        "mode": "ALL_AUTHORIZED",
        "label": "All authorized projects",
        "project_count": 1,
    }

    jobs = {item["job_id"]: item for item in body["jobs"]}
    assert set(jobs) == {recovery_job, ready_job, running_job, succeeded_job, failed_job}
    assert hidden_job not in jobs
    assert {item["status"] for item in body["jobs"]} == {
        "READY", "LEASED", "RUNNING", "SUCCEEDED", "FAILED"
    }

    recovered = jobs[recovery_job]
    assert recovered["scope"] == {
        "tenant_id": tenant,
        "tenant_name": "Runtime Tenant",
        "workspace_id": workspace,
        "workspace_name": "Runtime Workspace",
    }
    assert recovered["resource_conflict_keys"] == ["dataset:alpha"]
    assert recovered["required_resources"]["cpu"] == 2.0
    assert recovered["required_capabilities"] == ["python"]
    assert recovered["lease"]["worker_id"] == worker_new
    assert recovered["lease"]["has_token"] is True
    assert "token" not in recovered["lease"]
    assert [a["status"] for a in recovered["attempts"]] == ["ABANDONED", "LEASED"]
    assert recovered["attempts"][0]["run_id"] == first_run["run_id"]
    assert recovered["attempts"][0]["run_status"] == "ABANDONED"
    assert {e["event_type"] for e in recovered["scheduler_events"]} >= {
        "JOB_ENQUEUED", "JOB_LEASED", "JOB_STARTED", "JOB_LEASE_EXPIRED_REQUEUED"
    }

    running = jobs[running_job]
    assert running["attempts"][0]["run_id"] == running_started["run_id"]
    assert running["attempts"][0]["run_status"] == "RUNNING"

    workers = {item["worker_id"]: item for item in body["workers"]}
    assert set(workers) == {worker_old, worker_new}
    assert worker_orphan not in workers
    assert hidden_worker not in workers
    assert workers[worker_new]["actor_id"]
    assert workers[worker_new]["resources_total"]["cpu"] == 4.0
    assert workers[worker_new]["capabilities"]["labels"] == ["python"]

    encoded = json.dumps(body)
    assert "lease_token" not in encoded
    assert '"metadata"' not in json.dumps(recovered["attempts"])
    assert first["lease_token"] not in encoded
    assert second["lease_token"] not in encoded

    rt.close()


def test_operations_runtime_zero_state_is_truthful(tmp_path, monkeypatch):
    rt, _, _, _, _, _, _ = _runtime(tmp_path, monkeypatch)
    client = TestClient(_app(rt))
    _login(client, "runtime-owner")
    body = client.get("/browser/operations/runtime").json()
    assert body["query_status"] == "COMPLETE"
    assert body["jobs"] == []
    assert body["workers"] == []
    rt.close()


def test_operations_runtime_unavailable_is_not_fake_zero(tmp_path, monkeypatch):
    rt, _, _, _, _, _, _ = _runtime(tmp_path, monkeypatch)
    client = TestClient(_app(rt), raise_server_exceptions=False)
    _login(client, "runtime-owner")

    def unavailable(*_args, **_kwargs):
        raise RuntimeError("forced runtime projection failure")

    monkeypatch.setattr(ProjectDashboardService, "operations_runtime", unavailable)
    response = client.get("/browser/operations/runtime")
    assert response.status_code == 500
    assert response.json() != {"jobs": [], "workers": []}
    rt.close()


def test_operations_runtime_browser_surface_is_read_only():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")

    assert 'id="operationsRuntimeView"' in html
    assert 'id="operationsRuntimeJobsBody"' in html
    assert 'id="operationsRuntimeWorkersBody"' in html
    assert 'api("/browser/operations/runtime")' in js
    assert 'path === "/app/operations/runtime"' in js
    assert 'data-operations-route="/app/operations/runtime"' in html
    assert "<small>Live</small>" in html
    for forbidden in (
        "register_worker", "heartbeat_worker", "set_worker_status",
        "lease_next", "heartbeat_job", "commit_effect",
    ):
        assert forbidden not in js
