from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
PASSWORD = "access-test-password"


def _fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(tmp_path / "access.db"),
        auth_secret="a" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
    )
    owner = rt.governance.create_actor("HUMAN", "owner", [], [])
    member = rt.governance.create_actor("HUMAN", "member", [], [])
    outsider = rt.governance.create_actor("HUMAN", "outsider", [], [])
    for actor, username in ((owner, "owner"), (member, "member"), (outsider, "outsider")):
        rt.auth.register_human(actor, username, PASSWORD)

    tenant = rt.tenancy.create_tenant("Visible Tenant", owner, tenant_id="tenant_visible")
    workspace = rt.tenancy.create_workspace(
        tenant, "Visible Workspace", owner, workspace_id="workspace_visible"
    )
    project = rt.create_scoped_project(
        "Visible Project", tenant, workspace, owner, project_id="project_visible"
    )

    hidden_tenant = rt.tenancy.create_tenant(
        "Hidden Tenant", outsider, tenant_id="tenant_hidden_access"
    )
    hidden_workspace = rt.tenancy.create_workspace(
        hidden_tenant, "Hidden Workspace", outsider, workspace_id="workspace_hidden_access"
    )
    hidden_project = rt.create_scoped_project(
        "Hidden Project", hidden_tenant, hidden_workspace, outsider,
        project_id="project_hidden_access",
    )
    return rt, owner, member, outsider, tenant, workspace, project, hidden_tenant, hidden_workspace, hidden_project


def _client(rt):
    return TestClient(create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "test-version",
            "build_sha": "access-build-sha",
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "canonical",
        },
        web_root=WEB,
    ))


def _login(client, username):
    response = client.post(
        "/browser/auth/login",
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 200


def test_access_projection_hides_other_scopes_and_member_directory(tmp_path, monkeypatch):
    rt, owner, member, _, tenant, workspace, project, hidden_tenant, hidden_workspace, hidden_project = _fixture(tmp_path, monkeypatch)
    rt.tenancy.add_project_member(project, member, "VIEWER", owner)

    owner_client = _client(rt)
    assert owner_client.get("/browser/access-summary").status_code == 401
    _login(owner_client, "owner")
    body = owner_client.get("/browser/access-summary").json()

    assert body["query_status"] == "COMPLETE"
    assert body["session"]["principal_id"] == "owner"
    assert {x["tenant_id"] for x in body["tenants"]} == {tenant}
    assert {x["workspace_id"] for x in body["workspaces"]} == {workspace}
    assert {x["project_id"] for x in body["projects"]} == {project}
    assert hidden_tenant not in {x["tenant_id"] for x in body["tenants"]}
    assert hidden_workspace not in {x["workspace_id"] for x in body["workspaces"]}
    assert hidden_project not in {x["project_id"] for x in body["projects"]}
    assert {m["actor_id"] for m in body["projects"][0]["members"]} == {owner, member}

    member_client = _client(rt)
    _login(member_client, "member")
    member_body = member_client.get("/browser/access-summary").json()
    assert member_body["tenants"] == []
    assert member_body["workspaces"] == []
    assert member_body["projects"][0]["can_manage_members"] is False
    assert member_body["projects"][0]["members"] == []
    rt.close()


def test_access_browser_mutations_and_negative_paths(tmp_path, monkeypatch):
    rt, owner, member, outsider, tenant, workspace, project, _, hidden_workspace, _ = _fixture(tmp_path, monkeypatch)
    client = _client(rt)
    _login(client, "owner")

    new_tenant = client.post("/browser/access/tenants", json={"name": "Browser Tenant"})
    assert new_tenant.status_code == 200
    tenant_id = new_tenant.json()["tenant_id"]
    new_workspace = client.post(
        f"/browser/access/tenants/{tenant_id}/workspaces",
        json={"name": "Browser Workspace"},
    )
    assert new_workspace.status_code == 200

    assert client.post(
        f"/browser/access/tenants/{tenant}/members",
        json={"actor_id": member, "role": "MEMBER"},
    ).status_code == 200
    assert client.post(
        f"/browser/access/workspaces/{workspace}/members",
        json={"actor_id": member, "role": "VIEWER"},
    ).status_code == 200
    assert client.post(
        f"/browser/access/projects/{project}/members",
        json={"actor_id": member, "role": "RESEARCHER"},
    ).status_code == 200

    assert client.delete(f"/browser/access/projects/{project}/members/{member}").status_code == 200
    assert client.delete(f"/browser/access/workspaces/{workspace}/members/{member}").status_code == 200
    assert client.delete(f"/browser/access/tenants/{tenant}/members/{member}").status_code == 200

    bad_role = client.post(
        f"/browser/access/projects/{project}/members",
        json={"actor_id": member, "role": "INVALID_ROLE"},
    )
    assert bad_role.status_code == 422

    outsider_client = _client(rt)
    _login(outsider_client, "outsider")
    assert outsider_client.post(
        f"/browser/access/workspaces/{workspace}/members",
        json={"actor_id": outsider, "role": "VIEWER"},
    ).status_code == 404
    assert outsider_client.post(
        f"/browser/access/tenants/{tenant}/workspaces",
        json={"name": "Forbidden"},
    ).status_code == 404

    assert rt.db.one(
        "SELECT status FROM tenant_memberships WHERE tenant_id=? AND actor_id=?",
        (tenant, member),
    )["status"] == "REVOKED"
    assert rt.db.one(
        "SELECT status FROM workspace_memberships WHERE workspace_id=? AND actor_id=?",
        (workspace, member),
    )["status"] == "REVOKED"
    assert rt.db.one(
        "SELECT status FROM project_memberships WHERE project_id=? AND actor_id=?",
        (project, member),
    )["status"] == "REVOKED"
    assert rt.db.one(
        "SELECT tenant_id FROM workspaces WHERE workspace_id=?",
        (hidden_workspace,),
    ) is not None
    rt.close()


def test_access_ui_contract():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert 'id="accessRouteView"' in html
    assert "No global actor directory" in html
    assert 'api("/browser/access-summary")' in js
    assert 'item.id === "access"' in js
    assert "/browser/access/tenants" in js
    assert "/browser/access/workspaces/" in js
    assert "/browser/access/projects/" in js
