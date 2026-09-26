from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import canonical_json, uid


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
PASSWORD = "github-read-password"


class ReadAdapter:
    def __init__(self, head="a" * 40):
        self.head = head

    def get_branch_head(self, repository_full_name, branch):
        return self.head

    def get_file(self, repository_full_name, path, ref):
        return None

    def get_commit(self, repository_full_name, commit_sha):
        return {
            "sha": commit_sha,
            "parents": ["b" * 40],
            "tree_sha": "c" * 40,
        }


class ReadyAdapter(ReadAdapter):
    def __init__(self, full_name, *, repository_id=123, head="a" * 40):
        super().__init__(head=head)
        self.full_name = full_name
        self.repository_id = repository_id

    def get_repository_identity(self, repository_full_name):
        return {
            "repository_id": self.repository_id,
            "full_name": self.full_name,
        }


class ExplodingAdapter(ReadAdapter):
    def get_repository_identity(self, repository_full_name):
        raise RuntimeError("host adapter internal failure must stay sanitized")


def _runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(tmp_path / "bps-github-read.db"),
        auth_secret="g" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
    )
    owner = rt.governance.create_actor("HUMAN", "github-owner", [], [])
    outsider = rt.governance.create_actor("HUMAN", "github-outsider", [], [])
    rt.auth.register_human(owner, "github-owner", PASSWORD)

    tenant = rt.tenancy.create_tenant(
        "GitHub Tenant", owner, tenant_id="tenant_github"
    )
    workspace = rt.tenancy.create_workspace(
        tenant, "GitHub Workspace", owner, workspace_id="workspace_github"
    )
    project = rt.create_scoped_project(
        "GitHub Project",
        tenant,
        workspace,
        owner,
        project_id="project_github",
    )

    hidden_tenant = rt.tenancy.create_tenant(
        "Hidden GitHub Tenant",
        outsider,
        tenant_id="tenant_github_hidden",
    )
    hidden_workspace = rt.tenancy.create_workspace(
        hidden_tenant,
        "Hidden GitHub Workspace",
        outsider,
        workspace_id="workspace_github_hidden",
    )
    hidden_project = rt.create_scoped_project(
        "Hidden GitHub Project",
        hidden_tenant,
        hidden_workspace,
        outsider,
        project_id="project_github_hidden",
    )
    return rt, owner, outsider, project, hidden_project


def _app(rt):
    return create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "test-version",
            "build_sha": "github-read-build-sha",
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "canonical",
        },
        web_root=WEB,
    )


def _login(client):
    response = client.post(
        "/browser/auth/login",
        json={"username": "github-owner", "password": PASSWORD},
    )
    assert response.status_code == 200


def _connection(
    rt,
    project,
    actor,
    suffix,
    *,
    capabilities=None,
    repository=None,
):
    capabilities = capabilities or ["REPO_READ"]
    connection = rt.plugins.create_connection(
        project,
        "github",
        f"opaque-github-{suffix}",
        capabilities,
        actor,
        metadata={"label": f"{suffix} connection", "purpose": "QA"},
    )
    binding = None
    if repository:
        binding = rt.github.bind_repository(
            project,
            connection,
            repository,
            "main",
            actor,
            allowed_branches=["feature/*", "docs/*"],
        )
    return connection, binding


def _change_set(rt, project, binding, actor, suffix):
    return rt.github.prepare_change_set(
        project,
        binding,
        "feature/bps-" + suffix,
        (suffix[0] if suffix else "a") * 40,
        [
            {
                "path": f"docs/{suffix}.md",
                "operation": "CREATE",
                "content": f"PRIVATE CHANGE CONTENT {suffix}",
            }
        ],
        f"change {suffix}",
        actor,
    )


def _seed(rt, owner, outsider, project, hidden_project):
    main_connection, main_binding = _connection(
        rt,
        project,
        owner,
        "main",
        capabilities=["REPO_READ", "CONTENT_WRITE"],
        repository="minhtri22/GWF",
    )

    change_sets = {}
    for suffix, status in (
        ("prepared", "PREPARED"),
        ("preflight", "PREFLIGHT_PASS"),
        ("committed", "COMMITTED"),
        ("verified", "VERIFIED"),
        ("stale", "STALE"),
        ("verifyfail", "VERIFICATION_FAILED"),
    ):
        change_set = _change_set(
            rt, project, main_binding, owner, suffix
        )
        change_sets[status] = change_set
        committed_sha = None
        verified_at = None
        if status in {"COMMITTED", "VERIFIED", "VERIFICATION_FAILED"}:
            committed_sha = {
                "COMMITTED": "c" * 40,
                "VERIFIED": "d" * 40,
                "VERIFICATION_FAILED": "e" * 40,
            }[status]
        if status == "VERIFIED":
            verified_at = "2026-09-26T12:30:00+00:00"
        rt.db.conn.execute(
            "UPDATE github_change_sets SET status=?,committed_sha=?,verified_at=? "
            "WHERE change_set_id=?",
            (status, committed_sha, verified_at, change_set),
        )
        rt.db.conn.execute(
            "INSERT INTO github_sha_checks VALUES(?,?,?,?,?,?,?,?)",
            (
                "ghcheck_" + suffix,
                change_set,
                "BRANCH_HEAD_PRE",
                "a" * 40,
                "a" * 40 if status not in {"STALE", "VERIFICATION_FAILED"} else "f" * 40,
                "PASS" if status not in {"STALE", "VERIFICATION_FAILED"} else "FAIL",
                canonical_json({
                    "branch": "feature/bps-" + suffix,
                    "note": "persisted exact SHA check",
                }),
                "2026-09-26T12:00:00+00:00",
            ),
        )
    rt.db.conn.commit()

    readiness = {}
    connection, binding = _connection(
        rt, project, owner, "disabled", repository="example/disabled"
    )
    rt.plugins.disable(connection, owner)
    readiness["DISABLED"] = binding

    connection, binding = _connection(
        rt, project, owner, "unattached", repository="example/unattached"
    )
    readiness["NOT_ATTACHED"] = binding

    connection, binding = _connection(
        rt, project, owner, "capability", repository="example/capability"
    )
    rt.db.conn.execute(
        "UPDATE plugin_connections SET capabilities=? WHERE connection_id=?",
        (canonical_json(["CONTENT_WRITE"]), connection),
    )
    rt.db.conn.commit()
    readiness["CAPABILITY_MISSING"] = binding

    connection, binding = _connection(
        rt, project, owner, "unsupported", repository="example/unsupported"
    )
    rt.plugins.attach_runtime_adapter(connection, ReadAdapter())
    readiness["IDENTITY_UNSUPPORTED"] = binding

    connection, binding = _connection(
        rt, project, owner, "ready", repository="example/ready"
    )
    rt.plugins.attach_runtime_adapter(
        connection, ReadyAdapter("example/ready", repository_id=42, head="1" * 40)
    )
    readiness["READY"] = binding

    connection, binding = _connection(
        rt, project, owner, "mismatch", repository="example/mismatch"
    )
    rt.plugins.attach_runtime_adapter(
        connection, ReadyAdapter("other/repository", repository_id=43, head="2" * 40)
    )
    readiness["IDENTITY_MISMATCH"] = binding

    connection, binding = _connection(
        rt, project, owner, "badhead", repository="example/badhead"
    )
    rt.plugins.attach_runtime_adapter(
        connection, ReadyAdapter("example/badhead", repository_id=44, head="bad")
    )
    readiness["BAD_HEAD"] = binding

    connection, binding = _connection(
        rt, project, owner, "provider-error", repository="example/provider-error"
    )
    rt.plugins.attach_runtime_adapter(connection, ExplodingAdapter())
    readiness["PROVIDER_ERROR"] = binding

    hidden_connection, hidden_binding = _connection(
        rt,
        hidden_project,
        outsider,
        "hidden",
        capabilities=["REPO_READ", "CONTENT_WRITE"],
        repository="secretorg/hidden",
    )
    hidden_change = _change_set(
        rt, hidden_project, hidden_binding, outsider, "hidden"
    )
    rt.db.conn.commit()

    return {
        "main_connection": main_connection,
        "main_binding": main_binding,
        "change_sets": change_sets,
        "readiness": readiness,
        "hidden_connection": hidden_connection,
        "hidden_binding": hidden_binding,
        "hidden_change": hidden_change,
    }


def _fixture(tmp_path, monkeypatch):
    rt, owner, outsider, project, hidden_project = _runtime(
        tmp_path, monkeypatch
    )
    seeded = _seed(rt, owner, outsider, project, hidden_project)
    return rt, owner, project, hidden_project, seeded


def _assert_no_secret_keys(value):
    forbidden = {
        "token",
        "access_token",
        "refresh_token",
        "password",
        "secret",
        "client_secret",
        "private_key",
        "authorization",
        "api_key",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            assert str(key).lower() not in forbidden
            _assert_no_secret_keys(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_secret_keys(child)


def test_github_summary_is_authorized_exact_and_content_minimized(
    tmp_path, monkeypatch
):
    rt, _, project, hidden_project, seeded = _fixture(
        tmp_path, monkeypatch
    )
    client = TestClient(_app(rt))
    assert client.get("/browser/github").status_code == 401
    _login(client)

    response = client.get("/browser/github")
    assert response.status_code == 200
    body = response.json()
    assert body["build_sha"] == "github-read-build-sha"
    assert body["query_status"] == "COMPLETE"
    assert body["scope"]["project_count"] == 1
    assert [item["project_id"] for item in body["projects"]] == [project]
    assert hidden_project not in str(body)
    assert seeded["hidden_connection"] not in str(body)
    assert seeded["hidden_binding"] not in str(body)
    assert seeded["hidden_change"] not in str(body)
    assert "secretorg/hidden" not in str(body)

    visible = body["projects"][0]
    by_connection = {
        item["connection_id"]: item for item in visible["connections"]
    }
    main = by_connection[seeded["main_connection"]]
    assert main["external_connection_ref"] == "opaque-github-main"
    assert main["capabilities"] == ["CONTENT_WRITE", "REPO_READ"]
    assert main["status"] == "ACTIVE"
    assert main["metadata"] == {"label": "main connection", "purpose": "QA"}
    assert main["adapter_attached"] is False

    by_binding = {item["binding_id"]: item for item in visible["bindings"]}
    binding = by_binding[seeded["main_binding"]]
    assert binding["repository_full_name"] == "minhtri22/GWF"
    assert binding["default_branch"] == "main"
    assert binding["write_policy"] == "FEATURE_BRANCH_ONLY"
    assert binding["allowed_branches"] == ["docs/*", "feature/*"]
    assert binding["connection_status"] == "ACTIVE"
    assert binding["connection_capabilities"] == [
        "CONTENT_WRITE", "REPO_READ"
    ]

    by_status = {item["status"]: item for item in visible["change_sets"]}
    for status in (
        "PREPARED",
        "PREFLIGHT_PASS",
        "COMMITTED",
        "VERIFIED",
        "STALE",
        "VERIFICATION_FAILED",
    ):
        assert status in by_status
    assert by_status["VERIFIED"]["qa_complete"] is True
    for status in (
        "PREPARED",
        "PREFLIGHT_PASS",
        "COMMITTED",
        "STALE",
        "VERIFICATION_FAILED",
    ):
        assert by_status[status]["qa_complete"] is False

    for item in visible["change_sets"]:
        assert item["manifest"]
        assert "content" not in item["manifest"][0]
        assert item["manifest"][0]["content_sha256"]
        assert item["checks"][0]["stage"] == "BRANCH_HEAD_PRE"
        assert "details_json" not in item["checks"][0]

    serialized = str(body)
    assert "PRIVATE CHANGE CONTENT" not in serialized
    assert "_adapters" not in serialized
    _assert_no_secret_keys(body)
    rt.close()


def test_github_binding_readiness_states_are_explicit(
    tmp_path, monkeypatch
):
    rt, _, project, hidden_project, seeded = _fixture(
        tmp_path, monkeypatch
    )
    client = TestClient(_app(rt))
    _login(client)

    expected = {
        "DISABLED": "DISABLED",
        "NOT_ATTACHED": "NOT_ATTACHED",
        "CAPABILITY_MISSING": "CAPABILITY_MISSING",
        "IDENTITY_UNSUPPORTED": "IDENTITY_UNSUPPORTED",
        "READY": "READY",
        "IDENTITY_MISMATCH": "IDENTITY_MISMATCH",
        "BAD_HEAD": "PROVIDER_ERROR",
        "PROVIDER_ERROR": "PROVIDER_ERROR",
    }
    bodies = {}
    for key, expected_status in expected.items():
        response = client.get(
            f"/browser/github/bindings/{seeded['readiness'][key]}/readiness"
        )
        assert response.status_code == 200
        bodies[key] = response.json()
        assert bodies[key]["status"] == expected_status

    assert bodies["READY"]["repository_identity"] == {
        "repository_id": "42",
        "full_name": "example/ready",
    }
    assert bodies["READY"]["default_branch_head"] == "1" * 40
    assert bodies["READY"]["adapter_attached"] is True
    assert bodies["IDENTITY_MISMATCH"]["repository_identity"]["full_name"] == (
        "other/repository"
    )
    assert bodies["BAD_HEAD"]["error"]["code"] == "VALIDATION_ERROR"
    assert bodies["PROVIDER_ERROR"]["error"] == {
        "code": "ADAPTER_READ_FAILED",
        "message": "GitHub readiness probe failed",
    }
    assert "host adapter internal failure" not in str(bodies["PROVIDER_ERROR"])

    hidden = client.get(
        f"/browser/github/bindings/{seeded['hidden_binding']}/readiness"
    )
    assert hidden.status_code == 404
    assert client.get(
        "/browser/github/bindings/missing-binding/readiness"
    ).status_code == 404
    rt.close()


def test_dangling_connection_is_partial_and_readiness_is_not_zero(
    tmp_path, monkeypatch
):
    rt, _, project, _, seeded = _fixture(tmp_path, monkeypatch)
    dangling_connection, dangling_binding = _connection(
        rt,
        project,
        rt.db.one(
            "SELECT actor_id FROM actors WHERE principal_id='github-owner'"
        )["actor_id"],
        "dangling",
        repository="example/dangling",
    )
    rt.db.conn.execute(
        "DELETE FROM plugin_connections WHERE connection_id=?",
        (dangling_connection,),
    )
    rt.db.conn.commit()

    client = TestClient(_app(rt))
    _login(client)
    summary = client.get("/browser/github").json()
    assert summary["query_status"] == "PARTIAL"
    project_row = summary["projects"][0]
    binding = next(
        item for item in project_row["bindings"]
        if item["binding_id"] == dangling_binding
    )
    assert binding["connection_identity_status"] == "MISSING"
    assert binding["connection_status"] is None

    readiness = client.get(
        f"/browser/github/bindings/{dangling_binding}/readiness"
    )
    assert readiness.status_code == 200
    assert readiness.json()["status"] == "CONNECTION_MISSING"
    rt.close()


def test_existing_bearer_plugin_and_github_reads_remain_compatible(
    tmp_path, monkeypatch
):
    rt, _, project, _, seeded = _fixture(tmp_path, monkeypatch)
    client = TestClient(_app(rt))
    token = client.post(
        "/auth/login",
        json={"username": "github-owner", "password": PASSWORD},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    plugins = client.get(
        f"/product/projects/{project}/plugins",
        headers=headers,
    )
    assert plugins.status_code == 200
    assert seeded["main_connection"] in {
        item["connection_id"] for item in plugins.json()["plugins"]
    }

    change = client.get(
        f"/product/github/change-sets/{seeded['change_sets']['VERIFIED']}",
        headers=headers,
    )
    assert change.status_code == 200
    assert change.json()["status"] == "VERIFIED"
    assert change.json()["qa_complete"] is True
    rt.close()
