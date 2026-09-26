from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.product import ProjectDashboardService
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import canonical_json, utcnow


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
PASSWORD = "project-overview-password"


def _fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(tmp_path / "project-overview.db"),
        auth_secret="o" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
    )
    owner = rt.governance.create_actor("HUMAN", "overview-owner", [], [])
    outsider = rt.governance.create_actor("HUMAN", "overview-outsider", [], [])
    phase_actor = rt.governance.create_actor("AGENT", "phase-actor", ["operator"], ["project_overview"])
    rt.auth.register_human(owner, "overview-owner", PASSWORD)
    rt.auth.register_human(outsider, "overview-outsider", PASSWORD)

    tenant = rt.tenancy.create_tenant("Overview Tenant", owner, tenant_id="tenant_overview")
    workspace = rt.tenancy.create_workspace(
        tenant, "Overview Workspace", owner, workspace_id="workspace_overview"
    )
    project = rt.create_scoped_project(
        "Overview Project", tenant, workspace, owner, project_id="project_overview"
    )

    hidden_tenant = rt.tenancy.create_tenant(
        "Hidden Overview Tenant", outsider, tenant_id="tenant_overview_hidden"
    )
    hidden_workspace = rt.tenancy.create_workspace(
        hidden_tenant, "Hidden Overview Workspace", outsider,
        workspace_id="workspace_overview_hidden",
    )
    hidden_project = rt.create_scoped_project(
        "Hidden Overview Project", hidden_tenant, hidden_workspace, outsider,
        project_id="project_overview_hidden",
    )
    return rt, owner, outsider, phase_actor, tenant, workspace, project, hidden_project


def _app(rt):
    return create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "test-version",
            "build_sha": "overview-build-sha",
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


def _seed_populated(rt, owner, phase_actor, tenant, project):
    package = rt.domains.create_package(
        tenant, rt.domain.domain_id, "Overview Domain", owner
    )
    revision = rt.domains.add_revision(
        package,
        (ROOT / "domains" / "example.workflow.yaml").read_text(encoding="utf-8"),
        owner,
    )
    rt.domains.publish_revision(revision, owner)
    rt.domains.pin_project(project, revision, owner)

    rt.db.conn.execute(
        "INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "wu_overview_run", project, "execute_plan", "[]", "[]", "[]", "[]", "[]",
            "{}", "{}", "{}", "{}", "[]", "RUNNING", 0,
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "run_overview", "wu_overview_run", 1, owner, "[]",
            "2026-09-26T01:00:00+00:00", None, "RUNNING", None,
            "[]", "[]", None, "corr-overview",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "orch_overview", project, rt.domain.domain_id, "RUNNING",
            "phase-overview", 2, None, 1,
            "2026-09-26T00:59:00+00:00",
            "2026-09-26T01:01:00+00:00", None, "{}",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "phase_exec_overview", "orch_overview", "phase-overview", 3, 2,
            "wu_overview_run", "run_overview", "RUNNING", None, None, None,
            "2026-09-26T01:00:30+00:00", None, "{}",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_stage_events VALUES(?,?,?,?,?,?,?,?)",
        (
            "phaseevt_overview", "phase_exec_overview", "EXECUTE", "STEP_PROGRESS",
            phase_actor, "working", "{}", "2026-09-26T01:02:00+00:00",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_handoffs VALUES(?,?,?,?,?,?,?)",
        (
            "handoff_overview", "phase_exec_overview", "{}",
            "handoff-hash-overview", phase_actor,
            "2026-09-26T01:03:00+00:00", "handoff",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO proposals VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            "proposal_overview", project, owner, "OVERVIEW_APPROVAL", "[]", "{}",
            "overview-proposal-hash", None, "PENDING_APPROVAL",
            "2026-09-26T01:04:00+00:00", "overview-proposal-idem",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO failures VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "failure_overview", project, "wu_overview_run", "OVERVIEW_FAILURE",
            "VERIFY", "run_overview", None, None, "[]", "root-overview", None,
            "UNRESOLVED", "phase-overview", "HIGH", "sig-overview", "OPEN",
            "2026-09-26T01:05:00+00:00", None,
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO recoveries VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "recovery_overview", project, "failure_overview", "root-overview",
            "phase-overview", "[]", "[]", "[]", "[]", "[]", "[]", "[]",
            "RESUME", "READY", "2026-09-26T01:06:00+00:00",
        ),
    )
    rt.governance.append_audit(
        project, phase_actor, "OVERVIEW_ACTIVITY", "Project", project,
        reason_code="TEST",
    )

    rt.db.conn.execute(
        "INSERT INTO artifacts VALUES(?,?,?,?,?,?,?,?,?)",
        (
            "artifact_overview", project, "REPORT", "overview-report",
            utcnow(), owner, "revision_overview", "ACTIVE", 1,
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO revisions VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            "revision_overview", "artifact_overview", 1, "{}", "revhash-overview",
            owner, utcnow(), None, "CURRENT", "VALID",
        ),
    )
    rt.db.conn.commit()

    connection = rt.plugins.create_connection(
        project, "github", "overview-connection", ["REPO_READ"], owner
    )
    binding = rt.github.bind_repository(
        project, connection, "minhtri22/GWF", "main", owner,
        allowed_branches=["feature/*"],
    )

    rt.db.conn.execute(
        "INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "wu_overview_queue", project, "execute_plan", "[]", "[]", "[]", "[]", "[]",
            "{}", "{}", "{}", "{}", '["dataset:overview"]', "READY", 0,
        ),
    )
    rt.db.conn.commit()
    job = rt.distributed.enqueue_workunit(
        "wu_overview_queue",
        idempotency_key="overview-job",
        required_resources={"cpu": 1, "memory_mb": 256},
        required_capabilities=["python"],
    )
    return package, revision, binding, job


def test_project_overview_projection_is_authorized_exact_and_minimal(tmp_path, monkeypatch):
    rt, owner, outsider, phase_actor, tenant, workspace, project, hidden_project = _fixture(tmp_path, monkeypatch)
    package, revision, binding, job = _seed_populated(rt, owner, phase_actor, tenant, project)
    client = TestClient(_app(rt))

    assert client.get(f"/browser/projects/{project}/overview").status_code == 401
    _login(client, "overview-owner")

    response = client.get(f"/browser/projects/{project}/overview")
    assert response.status_code == 200
    body = response.json()

    assert body["build_sha"] == "overview-build-sha"
    assert body["query_status"] == "COMPLETE"
    assert body["project"]["project_id"] == project
    assert body["project"]["name"] == "Overview Project"
    assert body["project"]["scope"] == {
        "tenant_id": tenant,
        "tenant_name": "Overview Tenant",
        "workspace_id": workspace,
        "workspace_name": "Overview Workspace",
    }
    assert body["lifecycle"]["status"] == "ACTIVE"
    assert body["execution_activity"] == "EXECUTING"

    assert body["domain"]["package_id"] == package
    assert body["domain"]["domain_revision_id"] == revision
    assert body["domain"]["revision_status"] == "PUBLISHED"
    assert body["domain"]["payload_hash"]

    assert body["current_orchestration"]["orchestration_id"] == "orch_overview"
    assert body["current_phase"]["phase_execution_id"] == "phase_exec_overview"
    assert body["active_run"]["run_id"] == "run_overview"
    assert body["current_actor"] == phase_actor
    assert body["current_actor_source"]["kind"] == "PHASE_EVENT"

    assert body["approvals"]["pending_count"] == 1
    assert body["approvals"]["pending"][0]["proposal_id"] == "proposal_overview"
    assert body["failures"]["open_count"] == 1
    assert body["failures"]["open"][0]["failure_id"] == "failure_overview"
    assert body["failures"]["open"][0]["recoveries"][0]["recovery_id"] == "recovery_overview"

    assert body["latest_handoff"]["handoff_id"] == "handoff_overview"
    assert body["latest_handoff"]["payload_hash"] == "handoff-hash-overview"
    assert body["recent_activity"]

    assert body["github"]["binding_count"] == 1
    assert body["github"]["bindings"][0]["binding_id"] == binding
    assert body["github"]["bindings"][0]["repository_full_name"] == "minhtri22/GWF"
    encoded = str(body["github"])
    assert "overview-connection" not in encoded
    assert "token" not in encoded.lower()

    assert body["validity_frontier"] == {
        "valid_count": 1,
        "non_valid_count": 0,
        "valid_revision_ids": ["revision_overview"],
        "non_valid": [],
    }
    assert body["distributed"]["active_jobs"] == 1
    assert body["distributed"]["status_counts"]["READY"] == 1
    assert body["distributed"]["recent_jobs"][0]["job_id"] == job
    assert "lease_token" not in str(body["distributed"])
    assert body["document_governance"]["status"] == "UNAVAILABLE"
    assert body["document_governance"]["maturity"] == "BPS-M09_PENDING"

    assert client.get(f"/browser/projects/{hidden_project}/overview").status_code == 404
    assert client.get("/browser/projects/project_does_not_exist/overview").status_code == 404
    rt.close()


def test_project_overview_empty_state_is_truthful(tmp_path, monkeypatch):
    rt, _, _, _, _, _, project, _ = _fixture(tmp_path, monkeypatch)
    client = TestClient(_app(rt))
    _login(client, "overview-owner")

    body = client.get(f"/browser/projects/{project}/overview").json()
    assert body["query_status"] == "COMPLETE"
    assert body["execution_activity"] == "IDLE"
    assert body["current_orchestration"] is None
    assert body["current_phase"] is None
    assert body["active_run"] is None
    assert body["current_actor"] == "SYSTEM"
    assert body["approvals"]["pending_count"] == 0
    assert body["failures"]["open_count"] == 0
    assert body["latest_handoff"] is None
    assert body["github"]["binding_count"] == 0
    assert body["validity_frontier"]["valid_count"] == 0
    assert body["distributed"]["active_jobs"] == 0
    rt.close()


def test_project_overview_partial_and_unavailable_are_not_fake_empty(tmp_path, monkeypatch):
    rt, _, _, _, _, _, project, _ = _fixture(tmp_path, monkeypatch)
    client = TestClient(_app(rt))
    _login(client, "overview-owner")

    rt.db.conn.execute("DELETE FROM project_lifecycle WHERE project_id=?", (project,))
    rt.db.conn.commit()
    partial = client.get(f"/browser/projects/{project}/overview")
    assert partial.status_code == 200
    assert partial.json()["query_status"] == "PARTIAL"
    assert partial.json()["lifecycle"] is None

    def unavailable(*_args, **_kwargs):
        raise RuntimeError("forced project overview outage")

    monkeypatch.setattr(ProjectDashboardService, "project_overview", unavailable)
    failed_client = TestClient(_app(rt), raise_server_exceptions=False)
    _login(failed_client, "overview-owner")
    failed = failed_client.get(f"/browser/projects/{project}/overview")
    assert failed.status_code == 500
    assert failed.text
    rt.close()


def test_project_overview_dangling_bound_identity_is_partial_not_zero(tmp_path, monkeypatch):
    rt, owner, _, _, _, _, project, _ = _fixture(tmp_path, monkeypatch)
    rt.db.conn.execute(
        "INSERT INTO project_domain_bindings VALUES(?,?,?,?)",
        (project, "missing_domain_revision", owner, utcnow()),
    )
    rt.db.conn.execute(
        "INSERT INTO github_repository_bindings VALUES(?,?,?,?,?,?,?,?,?)",
        (
            "binding_missing_connection", project, "missing_connection",
            "minhtri22/GWF", "main", "FEATURE_BRANCH_ONLY",
            canonical_json(["feature/*"]), owner, utcnow(),
        ),
    )
    rt.db.conn.commit()

    client = TestClient(_app(rt))
    _login(client, "overview-owner")
    body = client.get(f"/browser/projects/{project}/overview").json()

    assert body["query_status"] == "PARTIAL"
    assert body["domain"]["domain_revision_id"] == "missing_domain_revision"
    assert body["domain"]["revision_status"] is None
    assert body["github"]["binding_count"] == 1
    assert body["github"]["bindings"][0]["binding_id"] == "binding_missing_connection"
    assert body["github"]["bindings"][0]["connection_status"] is None
    rt.close()


def test_project_overview_deep_link_is_served_by_browser_shell(tmp_path, monkeypatch):
    rt, _, _, _, _, _, project, _ = _fixture(tmp_path, monkeypatch)
    client = TestClient(_app(rt))
    response = client.get(f"/app/projects/{project}/overview")
    assert response.status_code == 200
    assert 'id="appView"' in response.text
    rt.close()

def test_project_workspace_browser_contract_is_dynamic_and_truthful():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")

    assert 'id="projectWorkspaceView"' in html
    assert 'id="projectOverviewLiveView"' in html
    assert 'id="projectLocalLockedView"' in html
    for section in ("overview", "execution", "library", "governance", "configuration"):
        assert f'data-project-section="{section}"' in html

    assert 'path.startsWith("/app/projects/")' in js
    assert 'projectWorkspacePath(button.dataset.projectOpen, "overview")' in js
    assert '"/browser/projects/"' in js and '"/overview"' in js
    assert 'Overview is not substituted silently.' in js
    assert 'activeRoute.projectId !== route.projectId' in js
    assert 'void refreshProjectOverview(activeRoute, true)' in js
    assert 'const requestActorId = state.me?.actor_id || null;' in js
    assert 'state.me.actor_id !== requestActorId' in js

    for forbidden in ("Rename Project", "Archive Project", "Restore Project"):
        assert forbidden not in html

