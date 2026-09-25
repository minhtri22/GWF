from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"


def projects_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    monkeypatch.delenv("GWR_TEST_DATABASE_URL", raising=False)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(tmp_path / "projects-index.db"),
        auth_secret="p" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
    )

    actor = rt.governance.create_actor("HUMAN", "projects-operator", [], [])
    rt.auth.register_human(actor, "projects-operator", "projects-operator-password")
    tenant_id = rt.tenancy.create_tenant("Projects Tenant", actor, tenant_id="tenant_projects")
    workspace_id = rt.tenancy.create_workspace(
        tenant_id, "Projects Workspace", actor, workspace_id="workspace_projects"
    )

    outsider = rt.governance.create_actor("HUMAN", "projects-outsider", [], [])
    outsider_tenant = rt.tenancy.create_tenant(
        "Hidden Tenant", outsider, tenant_id="tenant_hidden"
    )
    outsider_workspace = rt.tenancy.create_workspace(
        outsider_tenant, "Hidden Workspace", outsider, workspace_id="workspace_hidden"
    )
    rt.create_scoped_project(
        "Hidden Project", outsider_tenant, outsider_workspace, outsider,
        project_id="project_hidden",
    )

    return rt, actor, tenant_id, workspace_id


def projects_app(rt):
    return create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "test-version",
            "build_sha": "projects-build-sha",
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "canonical",
        },
        web_root=WEB,
    )


def seed_projects_index(rt, actor, tenant_id, workspace_id):
    executing = rt.create_scoped_project(
        "Executing Project", tenant_id, workspace_id, actor,
        project_id="project_executing",
    )
    paused = rt.create_scoped_project(
        "Paused Project", tenant_id, workspace_id, actor,
        project_id="project_paused",
    )
    queued = rt.create_scoped_project(
        "Queued Project", tenant_id, workspace_id, actor,
        project_id="project_queued",
    )
    archived = rt.create_scoped_project(
        "Archived Project", tenant_id, workspace_id, actor,
        project_id="project_archived",
    )
    rt.db.conn.execute(
        "UPDATE project_lifecycle SET status='ARCHIVED' WHERE project_id=?",
        (archived,),
    )

    package_id = rt.domains.create_package(
        tenant_id, rt.domain.domain_id, "Pinned Example Domain", actor
    )
    revision_id = rt.domains.add_revision(
        package_id,
        (ROOT / "domains" / "example.workflow.yaml").read_text(encoding="utf-8"),
        actor,
    )
    rt.domains.publish_revision(revision_id, actor)
    rt.domains.pin_project(executing, revision_id, actor)

    rt.db.conn.execute(
        "INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "wu_projects_executing", executing, "ANALYZE", "[]", "[]", "[]", "[]", "[]",
            "{}", "{}", "{}", "{}", "[]", "RUNNING", 0,
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "run_projects_executing", "wu_projects_executing", 1, actor, "[]",
            "2026-09-25T10:00:00+00:00", None, "RUNNING", None,
            "[]", "[]", None, "corr-projects",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "orch_projects_executing", executing, rt.domain.domain_id, "RUNNING",
            "phase-alpha", 0, None, 0,
            "2026-09-25T10:00:00+00:00",
            "2026-09-25T10:00:00+00:00", None, "{}",
        ),
    )

    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "orch_projects_paused", paused, rt.domain.domain_id, "PAUSED",
            "phase-beta", 0, None, 0,
            "2026-09-25T10:01:00+00:00",
            "2026-09-25T10:01:00+00:00", None, "{}",
        ),
    )

    rt.db.conn.execute(
        "INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "wu_projects_queued", queued, "ANALYZE", "[]", "[]", "[]", "[]", "[]",
            "{}", "{}", "{}", "{}", "[]", "READY", 0,
        ),
    )
    rt.db.conn.commit()
    rt.distributed.enqueue_workunit(
        "wu_projects_queued",
        idempotency_key="projects-index-queued",
    )

    rt.db.conn.execute(
        "INSERT INTO proposals VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            "proposal_projects_1", executing, actor, "APPROVE_TEST", "[]", "{}",
            "hash-projects", None, "PENDING_APPROVAL",
            "2026-09-25T10:02:00+00:00", "idem-projects",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO failures VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "failure_projects_1", executing, "wu_projects_executing",
            "PROJECTS_TEST_FAILURE", "EXECUTION", "run_projects_executing",
            None, None, "[]", None, None, "UNRESOLVED", None,
            "HIGH", "sig-projects", "OPEN",
            "2026-09-25T10:03:00+00:00", None,
        ),
    )
    rt.governance.append_audit(
        executing, actor, "RUN_STARTED", "ExecutionRun",
        "run_projects_executing", run_id="run_projects_executing",
    )
    rt.db.conn.commit()

    return {
        "executing": executing,
        "paused": paused,
        "queued": queued,
        "archived": archived,
        "package_id": package_id,
        "revision_id": revision_id,
    }


def test_projects_index_projection_is_authorized_and_exact(tmp_path, monkeypatch):
    rt, actor, tenant_id, workspace_id = projects_runtime(tmp_path, monkeypatch)
    seeded = seed_projects_index(rt, actor, tenant_id, workspace_id)
    client = TestClient(projects_app(rt))

    assert client.get("/browser/projects-index").status_code == 401
    login = client.post(
        "/browser/auth/login",
        json={"username": "projects-operator", "password": "projects-operator-password"},
    )
    assert login.status_code == 200

    response = client.get("/browser/projects-index")
    assert response.status_code == 200
    body = response.json()

    assert body["build_sha"] == "projects-build-sha"
    assert body["query_status"] == "COMPLETE"
    assert body["scope"] == {
        "mode": "ALL_AUTHORIZED",
        "label": "All authorized projects",
        "project_count": 4,
    }

    projects = {item["project_id"]: item for item in body["projects"]}
    assert "project_hidden" not in projects
    assert set(projects) == {
        seeded["executing"], seeded["paused"], seeded["queued"], seeded["archived"]
    }

    executing = projects[seeded["executing"]]
    assert executing["name"] == "Executing Project"
    assert executing["scope"] == {
        "tenant_id": tenant_id,
        "tenant_name": "Projects Tenant",
        "workspace_id": workspace_id,
        "workspace_name": "Projects Workspace",
    }
    assert executing["lifecycle"] == "ACTIVE"
    assert executing["execution_activity"] == "EXECUTING"
    assert executing["running_runs"] == 1
    assert executing["active_jobs"] == 0
    assert executing["pending_approvals"] == 1
    assert executing["attention_required"] == 2
    assert executing["latest_event"]["action"] == "RUN_STARTED"
    assert executing["created_at"]

    assert executing["domain"]["bound"] is True
    assert executing["domain"]["package_id"] == seeded["package_id"]
    assert executing["domain"]["revision_id"] == seeded["revision_id"]
    assert executing["domain"]["revision_status"] == "PUBLISHED"

    assert projects[seeded["paused"]]["execution_activity"] == "PAUSED"
    assert projects[seeded["queued"]]["execution_activity"] == "QUEUED"
    assert projects[seeded["queued"]]["active_jobs"] == 1
    assert projects[seeded["archived"]]["lifecycle"] == "ARCHIVED"
    assert projects[seeded["archived"]]["execution_activity"] == "IDLE"
    rt.close()


def test_projects_index_capability_and_browser_surface(tmp_path, monkeypatch):
    rt, _, _, _ = projects_runtime(tmp_path, monkeypatch)
    client = TestClient(projects_app(rt))

    capabilities = {
        item["id"]: item for item in client.get("/browser/bootstrap").json()["capabilities"]
    }
    assert capabilities["projects"] == {
        "id": "projects",
        "label": "Projects",
        "state": "LIVE_MODULE",
        "slice": "BPS-M02",
        "route": "/app/projects",
    }

    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")

    assert 'id="projectsRouteView"' in html
    assert 'id="projectsTableBody"' in html
    assert 'id="projectsLifecycleFilter"' in html
    assert 'id="projectsTenantFilter"' in html
    assert 'id="projectsWorkspaceFilter"' in html
    assert 'id="projectsDomainFilter"' in html
    assert 'id="projectsActivityFilter"' in html
    assert 'id="projectsAttentionFilter"' in html

    assert 'api("/browser/projects-index")' in js
    assert 'item.id === "projects"' in js
    assert "Create Project" not in html
    assert "Rename Project" not in html
    assert "Archive Project" not in html
    assert "Restore Project" not in html
    assert "/app/projects/" not in js
    rt.close()
