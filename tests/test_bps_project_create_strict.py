from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.errors import ValidationError
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"


def make_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(tmp_path / "project-create.db"),
        auth_secret="c" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
    )
    actor = rt.governance.create_actor("HUMAN", "creator", [], [])
    rt.auth.register_human(actor, "creator", "creator-password-long")
    tenant_id = rt.tenancy.create_tenant(
        "Creator Tenant", actor, tenant_id="tenant_creator"
    )
    workspace_id = rt.tenancy.create_workspace(
        tenant_id,
        "Creator Workspace",
        actor,
        workspace_id="workspace_creator",
    )
    return rt, actor, tenant_id, workspace_id


def app_for(rt):
    return create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "test-version",
            "build_sha": "project-create-build",
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "canonical",
        },
        web_root=WEB,
    )


def publish_domain(rt, tenant_id, actor, *, name="Creator Domain"):
    package_id = rt.domains.create_package(
        tenant_id, rt.domain.domain_id, name, actor
    )
    revision_id = rt.domains.add_revision(
        package_id,
        (ROOT / "domains" / "example.workflow.yaml").read_text(encoding="utf-8"),
        actor,
    )
    rt.domains.publish_revision(revision_id, actor)
    return package_id, revision_id


def test_scoped_project_create_rolls_back_late_domain_failure(tmp_path, monkeypatch):
    rt, actor, tenant_id, workspace_id = make_runtime(tmp_path, monkeypatch)

    original_pin = rt.domains.pin_project

    def fail_pin(project_id, revision_id, actor_id, *, commit=True):
        assert commit is False
        raise ValidationError("forced late pin failure")

    monkeypatch.setattr(rt.domains, "pin_project", fail_pin)

    with pytest.raises(ValidationError, match="forced late pin failure"):
        rt.create_scoped_project(
            "Must Roll Back",
            tenant_id,
            workspace_id,
            actor,
            project_id="project_must_rollback",
            domain_revision_id="revision_forced_failure",
        )

    assert rt.db.one(
        "SELECT 1 FROM projects WHERE id='project_must_rollback'"
    ) is None
    assert rt.db.one(
        "SELECT 1 FROM project_lifecycle WHERE project_id='project_must_rollback'"
    ) is None
    assert rt.db.one(
        "SELECT 1 FROM project_scopes WHERE project_id='project_must_rollback'"
    ) is None
    assert rt.db.one(
        "SELECT 1 FROM project_memberships WHERE project_id='project_must_rollback'"
    ) is None
    assert rt.db.one(
        "SELECT 1 FROM project_domain_bindings WHERE project_id='project_must_rollback'"
    ) is None
    assert rt.db.one(
        "SELECT 1 FROM security_events WHERE resource_id='project_must_rollback'"
    ) is None

    monkeypatch.setattr(rt.domains, "pin_project", original_pin)
    rt.close()


def test_browser_project_create_options_and_mutation_preserve_authority(tmp_path, monkeypatch):
    rt, actor, tenant_id, workspace_id = make_runtime(tmp_path, monkeypatch)
    package_id, revision_id = publish_domain(rt, tenant_id, actor)

    outsider = rt.governance.create_actor("HUMAN", "outsider", [], [])
    hidden_tenant = rt.tenancy.create_tenant(
        "Hidden Tenant", outsider, tenant_id="tenant_hidden_create"
    )
    hidden_workspace = rt.tenancy.create_workspace(
        hidden_tenant,
        "Hidden Workspace",
        outsider,
        workspace_id="workspace_hidden_create",
    )
    _, hidden_revision = publish_domain(
        rt, hidden_tenant, outsider, name="Hidden Domain"
    )

    client = TestClient(app_for(rt))
    assert client.get("/browser/projects/create-options").status_code == 401
    assert client.post(
        "/browser/projects",
        json={"workspace_id": workspace_id, "name": "No Session"},
    ).status_code == 401

    login = client.post(
        "/browser/auth/login",
        json={"username": "creator", "password": "creator-password-long"},
    )
    assert login.status_code == 200

    options = client.get("/browser/projects/create-options")
    assert options.status_code == 200
    body = options.json()
    assert body["query_status"] == "COMPLETE"
    assert body["build_sha"] == "project-create-build"
    assert body["contract"] == {
        "project_id": "SERVER_GENERATED",
        "domain_binding": "OPTIONAL_PUBLISHED_IMMUTABLE",
        "success_destination": "/app/projects/:projectId/overview",
    }
    assert body["scopes"] == [{
        "tenant_id": tenant_id,
        "tenant_name": "Creator Tenant",
        "workspace_id": workspace_id,
        "workspace_name": "Creator Workspace",
    }]
    assert {x["revision_id"] for x in body["published_domain_revisions"]} == {
        revision_id
    }
    assert all(
        x["tenant_id"] == tenant_id
        for x in body["published_domain_revisions"]
    )
    assert hidden_revision not in {
        x["revision_id"] for x in body["published_domain_revisions"]
    }

    before = int(rt.db.one("SELECT COUNT(*) n FROM projects")["n"])

    hidden_scope = client.post(
        "/browser/projects",
        json={"workspace_id": hidden_workspace, "name": "Must Stay Hidden"},
    )
    assert hidden_scope.status_code == 404
    assert hidden_scope.json()["detail"] == "workspace not found"
    assert int(rt.db.one("SELECT COUNT(*) n FROM projects")["n"]) == before

    invalid_domain = client.post(
        "/browser/projects",
        json={
            "workspace_id": workspace_id,
            "name": "Cross Tenant Domain",
            "domain_revision_id": hidden_revision,
        },
    )
    assert invalid_domain.status_code == 422
    assert invalid_domain.json()["detail"] == (
        "domain revision is not eligible for selected workspace"
    )
    assert int(rt.db.one("SELECT COUNT(*) n FROM projects")["n"]) == before

    created = client.post(
        "/browser/projects",
        json={
            "workspace_id": workspace_id,
            "name": "Created From Browser",
            "domain_revision_id": revision_id,
        },
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["ok"] is True
    project_id = payload["project"]["project_id"]
    assert project_id.startswith("project_")
    assert payload["project"]["name"] == "Created From Browser"
    assert payload["project"]["scope"]["tenant_id"] == tenant_id
    assert payload["project"]["scope"]["workspace_id"] == workspace_id
    assert payload["project"]["domain"]["package_id"] == package_id
    assert payload["project"]["domain"]["revision_id"] == revision_id
    assert payload["destination"] == f"/app/projects/{project_id}/overview"

    scope = rt.tenancy.scope_for_project(project_id)
    assert scope is not None
    assert scope.tenant_id == tenant_id
    assert scope.workspace_id == workspace_id
    assert rt.domains.project_binding(project_id)["domain_revision_id"] == revision_id

    owner = rt.db.one(
        "SELECT role,status FROM project_memberships "
        "WHERE project_id=? AND actor_id=?",
        (project_id, actor),
    )
    assert dict(owner) == {"role": "OWNER", "status": "ACTIVE"}

    security = rt.db.one(
        "SELECT action,outcome FROM security_events "
        "WHERE resource_type='Project' AND resource_id=? "
        "ORDER BY created_at DESC LIMIT 1",
        (project_id,),
    )
    assert dict(security) == {"action": "BIND_PROJECT", "outcome": "SUCCESS"}

    refreshed = client.get("/browser/projects-index").json()
    assert project_id in {x["project_id"] for x in refreshed["projects"]}

    rt.close()


def test_existing_bearer_project_create_contract_still_works(tmp_path, monkeypatch):
    rt, actor, tenant_id, workspace_id = make_runtime(tmp_path, monkeypatch)
    client = TestClient(app_for(rt))

    token = client.post(
        "/auth/login",
        json={"username": "creator", "password": "creator-password-long"},
    ).json()["access_token"]

    response = client.post(
        f"/workspaces/{workspace_id}/projects",
        json={"name": "Bearer Project"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    project_id = response.json()["project_id"]
    assert rt.tenancy.scope_for_project(project_id).tenant_id == tenant_id
    assert rt.db.one(
        "SELECT role FROM project_memberships "
        "WHERE project_id=? AND actor_id=?",
        (project_id, actor),
    )["role"] == "OWNER"
    rt.close()
