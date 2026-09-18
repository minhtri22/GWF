from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.errors import AuthorityDenied, InvalidTransition, StaleVersion, ValidationError
from gwr.github_rest_adapter import GitHubRestAdapter
from gwr.research_demo import DeterministicResearchExecutor
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).parents[1]


def blob_sha(content: str) -> str:
    return hashlib.sha1(content.encode("utf-8")).hexdigest()


class FakeGitHubAdapter:
    def __init__(self):
        self.branch_heads = {"feature/safe": "a" * 40, "main": "a" * 40}
        self.snapshots = {
            "a" * 40: {
                "README.md": "old readme\n",
                "src/app.py": "print('old')\n",
            }
        }
        self.commits = {}
        self.commit_calls = 0
        self.race_on_commit = False
        self.tamper_after_commit = False

    def get_branch_head(self, repository_full_name: str, branch: str) -> str:
        return self.branch_heads[branch]

    def get_file(self, repository_full_name: str, path: str, ref: str):
        files = self.snapshots.get(ref, {})
        if path not in files:
            return None
        content = files[path]
        return {"sha": blob_sha(content), "content": content}

    def commit_files(self, repository_full_name, branch, expected_head_sha, message, changes):
        if self.race_on_commit:
            raced = "c" * 40
            self.snapshots[raced] = deepcopy(self.snapshots[self.branch_heads[branch]])
            self.branch_heads[branch] = raced
            self.race_on_commit = False
        current = self.branch_heads[branch]
        if current != expected_head_sha:
            raise StaleVersion(
                "provider rejected stale head",
                details={"expected": expected_head_sha, "observed": current},
            )
        files = deepcopy(self.snapshots[current])
        for change in changes:
            if change["operation"] == "DELETE":
                files.pop(change["path"], None)
            else:
                files[change["path"]] = change["content"]
        material = expected_head_sha + message + repr(sorted(files.items()))
        commit_sha = hashlib.sha1(material.encode("utf-8")).hexdigest()
        self.snapshots[commit_sha] = files
        if self.tamper_after_commit and files:
            first_path = sorted(files)[0]
            self.snapshots[commit_sha][first_path] = "tampered-after-provider-write\n"
            self.tamper_after_commit = False
        self.commits[commit_sha] = {"parents": [expected_head_sha]}
        self.branch_heads[branch] = commit_sha
        self.commit_calls += 1
        return {"commit_sha": commit_sha, "parent_sha": expected_head_sha}

    def get_commit(self, repository_full_name: str, commit_sha: str):
        return self.commits[commit_sha]


@pytest.fixture
def configured(tmp_path):
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "research.workflow.yaml"),
        str(tmp_path / "v084.db"),
        auth_secret="g" * 64,
    )
    human = rt.governance.create_actor("HUMAN", "owner-v084", ["human_approver"], [])
    tenant = rt.tenancy.create_tenant("v084 tenant", human)
    workspace = rt.tenancy.create_workspace(tenant, "v084 workspace", human)
    project = rt.create_scoped_project("v084 project", tenant, workspace, human)
    agent = rt.governance.create_actor("AGENT", "agent-v084", ["research_lead"], [])
    rt.tenancy.add_project_member(project, agent, "RESEARCHER", human)
    connection = rt.plugins.create_connection(
        project,
        "github",
        "github-connection-opaque-1",
        ["REPO_READ", "CONTENT_WRITE"],
        human,
        metadata={"provider": "github", "account_label": "qa"},
    )
    adapter = FakeGitHubAdapter()
    rt.plugins.attach_runtime_adapter(connection, adapter)
    binding = rt.github.bind_repository(
        project,
        connection,
        "example/research",
        "main",
        human,
        write_policy="FEATURE_BRANCH_ONLY",
        allowed_branches=["feature/*", "docs/*"],
    )
    yield rt, project, human, agent, connection, binding, adapter
    rt.close()


def test_recovery_mode_is_optional_auto_or_human_approve(tmp_path):
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "research.workflow.yaml"),
        str(tmp_path / "recovery.db"),
    )
    project = rt.create_project("recovery")
    default_cfg = rt.agent_protocol.resolve_recovery_config(project, "phase_09_main_experiment")
    assert default_cfg["recovery_mode"] == "AUTO"

    rt.agent_protocol.set_project_defaults(
        project,
        "SYSTEM",
        recovery_mode="HUMAN_APPROVE",
        retry_budget=2,
    )
    manual_cfg = rt.agent_protocol.resolve_recovery_config(project, "phase_09_main_experiment")
    assert manual_cfg["recovery_mode"] == "HUMAN_APPROVE"

    rt.agent_protocol.set_project_defaults(
        project,
        "SYSTEM",
        recovery_mode="AUTO",
        retry_budget=2,
    )
    auto_cfg = rt.agent_protocol.resolve_recovery_config(project, "phase_09_main_experiment")
    assert auto_cfg["recovery_mode"] == "AUTO"
    rt.close()


def test_plugin_registry_refuses_persisted_secrets(configured):
    rt, project, human, *_ = configured
    with pytest.raises(ValidationError):
        rt.plugins.create_connection(
            project,
            "github",
            "github_pat_this_is_not_an_opaque_ref",
            ["REPO_READ"],
            human,
        )
    with pytest.raises(ValidationError):
        rt.plugins.create_connection(
            project,
            "github",
            "safe-ref-2",
            ["REPO_READ"],
            human,
            metadata={"access_token": "should-never-be-here"},
        )


def test_plugin_management_requires_human_and_known_capabilities(configured):
    rt, project, human, agent, *_ = configured
    with pytest.raises(AuthorityDenied):
        rt.plugins.create_connection(
            project,
            "github",
            "agent-created-ref",
            ["REPO_READ"],
            agent,
        )
    with pytest.raises(ValidationError):
        rt.plugins.create_connection(
            project,
            "github",
            "human-unknown-cap-ref",
            ["REPO_READ", "ADMIN_REPOSITORY"],
            human,
        )


def test_reference_rest_adapter_builds_git_data_commit_with_non_force_ref_update():
    expected = "a" * 40
    calls = []
    adapter = GitHubRestAdapter(lambda: "runtime-only-token")

    def fake_request(method, path, payload=None, query=None):
        calls.append({"method": method, "path": path, "payload": payload, "query": query})
        if method == "GET" and "/git/ref/heads/feature/safe" in path:
            return {"object": {"sha": expected}}
        if method == "GET" and f"/git/commits/{expected}" in path:
            return {"sha": expected, "tree": {"sha": "b" * 40}, "parents": []}
        if method == "GET" and "/git/trees/" in path:
            return {
                "sha": "b" * 40,
                "truncated": False,
                "tree": [{"path": "README.md", "mode": "100644", "type": "blob", "sha": "c" * 40}],
            }
        if method == "POST" and path.endswith("/git/blobs"):
            return {"sha": "d" * 40}
        if method == "POST" and path.endswith("/git/trees"):
            return {"sha": "e" * 40}
        if method == "POST" and path.endswith("/git/commits"):
            return {"sha": "f" * 40}
        if method == "PATCH" and "/git/refs/heads/feature/safe" in path:
            return {"object": {"sha": "f" * 40}}
        raise AssertionError((method, path, payload, query))

    adapter._request = fake_request
    result = adapter.commit_files(
        "example/research",
        "feature/safe",
        expected,
        "docs: adapter contract",
        [{
            "path": "README.md",
            "operation": "UPDATE",
            "expected_blob_sha": "c" * 40,
            "content_sha256": "not-used-by-provider",
            "content": "after\n",
        }],
    )
    assert result == {"commit_sha": "f" * 40, "parent_sha": expected}
    commit_call = next(x for x in calls if x["method"] == "POST" and x["path"].endswith("/git/commits"))
    assert commit_call["payload"]["parents"] == [expected]
    patch_call = next(x for x in calls if x["method"] == "PATCH")
    assert patch_call["payload"] == {"sha": "f" * 40, "force": False}


def test_reference_rest_adapter_resolves_credentials_only_at_request_time(configured):
    rt, project, human, agent, connection, binding, fake_adapter = configured
    calls = []

    def resolver(external_ref):
        calls.append(external_ref)
        return "ghp_runtime_only_secret"

    adapter = rt.plugins.attach_github_rest_adapter(connection, resolver)
    assert isinstance(adapter, GitHubRestAdapter)
    assert calls == []
    stored = rt.plugins.get(connection)
    assert stored["external_connection_ref"] == "github-connection-opaque-1"
    assert "ghp_runtime_only_secret" not in repr(stored)
    assert stored["adapter_attached"] is True


def test_sha_safe_commit_is_verified_end_to_end(configured):
    rt, project, human, agent, _, binding, adapter = configured
    base = adapter.get_branch_head("example/research", "feature/safe")
    before = adapter.get_file("example/research", "README.md", base)
    changes = [
        {
            "path": "README.md",
            "operation": "UPDATE",
            "expected_blob_sha": before["sha"],
            "content": "new readme\n",
        },
        {
            "path": "docs/qa.md",
            "operation": "CREATE",
            "content": "sha-safe\n",
        },
    ]
    change_set = rt.github.prepare_change_set(
        project,
        binding,
        "feature/safe",
        base,
        changes,
        "docs: update QA evidence",
        agent,
    )
    result = rt.github.execute(change_set, changes, agent)
    assert result["status"] == "VERIFIED"
    assert result["qa_complete"] is True
    assert result["committed_sha"] == adapter.get_branch_head("example/research", "feature/safe")
    assert adapter.commit_calls == 1

    stages = [x["stage"] for x in result["checks"]]
    assert "BRANCH_HEAD_PRE" in stages
    assert "FILE_BLOB_PRE" in stages
    assert "BRANCH_HEAD_IMMEDIATE_PRE" in stages
    assert "COMMIT_PARENT_POST" in stages
    assert "BRANCH_HEAD_POST" in stages
    assert "FILE_CONTENT_POST" in stages
    assert all(x["status"] == "PASS" for x in result["checks"])


def test_short_git_sha_is_rejected_before_changeset_freeze(configured):
    rt, project, human, agent, _, binding, adapter = configured
    changes = [{"path": "docs/new.md", "operation": "CREATE", "content": "x\n"}]
    with pytest.raises(ValidationError):
        rt.github.prepare_change_set(
            project,
            binding,
            "feature/safe",
            "abc1234",
            changes,
            "docs: reject short SHA",
            agent,
        )


def test_branch_sha_change_blocks_commit_before_write(configured):
    rt, project, human, agent, _, binding, adapter = configured
    base = adapter.get_branch_head("example/research", "feature/safe")
    before = adapter.get_file("example/research", "README.md", base)
    changes = [{
        "path": "README.md",
        "operation": "UPDATE",
        "expected_blob_sha": before["sha"],
        "content": "new readme\n",
    }]
    change_set = rt.github.prepare_change_set(
        project,
        binding,
        "feature/safe",
        base,
        changes,
        "docs: stale head test",
        agent,
    )
    adapter.branch_heads["feature/safe"] = "b" * 40
    adapter.snapshots["b" * 40] = deepcopy(adapter.snapshots[base])

    with pytest.raises(StaleVersion):
        rt.github.execute(change_set, changes, agent)
    assert rt.github.inspect(change_set)["status"] == "STALE"
    assert adapter.commit_calls == 0


def test_provider_side_expected_head_race_is_persisted_as_stale(configured):
    rt, project, human, agent, _, binding, adapter = configured
    base = adapter.get_branch_head("example/research", "feature/safe")
    before = adapter.get_file("example/research", "README.md", base)
    changes = [{
        "path": "README.md",
        "operation": "UPDATE",
        "expected_blob_sha": before["sha"],
        "content": "race safe\n",
    }]
    change_set = rt.github.prepare_change_set(
        project,
        binding,
        "feature/safe",
        base,
        changes,
        "docs: provider race test",
        agent,
    )
    adapter.race_on_commit = True
    with pytest.raises(StaleVersion):
        rt.github.execute(change_set, changes, agent)
    inspected = rt.github.inspect(change_set)
    assert inspected["status"] == "STALE"
    assert any(
        x["stage"] == "PROVIDER_EXPECTED_HEAD" and x["status"] == "FAIL"
        for x in inspected["checks"]
    )
    assert adapter.commit_calls == 0


def test_blob_sha_change_blocks_commit_even_when_branch_expectation_is_frozen(configured):
    rt, project, human, agent, _, binding, adapter = configured
    base = adapter.get_branch_head("example/research", "feature/safe")
    changes = [{
        "path": "README.md",
        "operation": "UPDATE",
        "expected_blob_sha": "0" * 40,
        "content": "new readme\n",
    }]
    change_set = rt.github.prepare_change_set(
        project,
        binding,
        "feature/safe",
        base,
        changes,
        "docs: stale blob test",
        agent,
    )
    with pytest.raises(StaleVersion):
        rt.github.execute(change_set, changes, agent)
    assert rt.github.inspect(change_set)["status"] == "STALE"
    assert adapter.commit_calls == 0


def test_frozen_manifest_prevents_content_substitution(configured):
    rt, project, human, agent, _, binding, adapter = configured
    base = adapter.get_branch_head("example/research", "feature/safe")
    before = adapter.get_file("example/research", "README.md", base)
    frozen = [{
        "path": "README.md",
        "operation": "UPDATE",
        "expected_blob_sha": before["sha"],
        "content": "approved content\n",
    }]
    change_set = rt.github.prepare_change_set(
        project,
        binding,
        "feature/safe",
        base,
        frozen,
        "docs: frozen manifest",
        agent,
    )
    changed = [{
        "path": "README.md",
        "operation": "UPDATE",
        "expected_blob_sha": before["sha"],
        "content": "different content\n",
    }]
    with pytest.raises(ValidationError):
        rt.github.execute(change_set, changed, agent)
    assert adapter.commit_calls == 0
    assert rt.github.inspect(change_set)["status"] == "PREPARED"


def test_post_commit_content_mismatch_is_not_qa_complete(configured):
    rt, project, human, agent, _, binding, adapter = configured
    base = adapter.get_branch_head("example/research", "feature/safe")
    before = adapter.get_file("example/research", "README.md", base)
    changes = [{
        "path": "README.md",
        "operation": "UPDATE",
        "expected_blob_sha": before["sha"],
        "content": "expected-after\n",
    }]
    change_set = rt.github.prepare_change_set(
        project,
        binding,
        "feature/safe",
        base,
        changes,
        "docs: verify provider content",
        agent,
    )
    adapter.tamper_after_commit = True
    with pytest.raises(ValidationError):
        rt.github.execute(change_set, changes, agent)
    inspected = rt.github.inspect(change_set)
    assert inspected["status"] == "VERIFICATION_FAILED"
    assert inspected["qa_complete"] is False
    assert adapter.commit_calls == 1
    assert any(
        x["stage"] == "FILE_CONTENT_POST" and x["status"] == "FAIL"
        for x in inspected["checks"]
    )


def test_archived_project_blocks_new_github_changeset(configured):
    rt, project, human, agent, _, binding, adapter = configured
    base = adapter.get_branch_head("example/research", "feature/safe")
    rt.project_governance.archive(project, human)
    changes = [{"path": "docs/archive.md", "operation": "CREATE", "content": "blocked\n"}]
    with pytest.raises(InvalidTransition):
        rt.github.prepare_change_set(
            project,
            binding,
            "feature/safe",
            base,
            changes,
            "docs: should not write",
            agent,
        )


def test_default_branch_direct_write_requires_human(configured):
    rt, project, human, agent, connection, _, adapter = configured
    binding = rt.github.bind_repository(
        project,
        connection,
        "example/direct",
        "main",
        human,
        write_policy="DIRECT",
        allowed_branches=["main"],
    )
    adapter.branch_heads["main"] = "a" * 40
    changes = [{"path": "docs/direct.md", "operation": "CREATE", "content": "x\n"}]
    with pytest.raises(AuthorityDenied):
        rt.github.prepare_change_set(
            project,
            binding,
            "main",
            "a" * 40,
            changes,
            "docs: direct",
            agent,
        )


def test_api_executes_sha_safe_github_changeset(configured, monkeypatch):
    rt, project, human, agent, connection, binding, adapter = configured
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1000)
    rt.auth.register_human(human, "owner-v084-api", "owner-v084-api-password")
    client = TestClient(create_app(rt))
    login = client.post(
        "/auth/login",
        json={"username": "owner-v084-api", "password": "owner-v084-api-password"},
    )
    assert login.status_code == 200
    auth = {"Authorization": "Bearer " + login.json()["access_token"]}

    plugins = client.get(f"/product/projects/{project}/plugins", headers=auth)
    assert plugins.status_code == 200
    assert any(x["connection_id"] == connection for x in plugins.json()["plugins"])

    base = adapter.get_branch_head("example/research", "feature/safe")
    before = adapter.get_file("example/research", "README.md", base)
    changes = [{
        "path": "README.md",
        "operation": "UPDATE",
        "expected_blob_sha": before["sha"],
        "content": "api verified\n",
    }]
    prepared = client.post(
        f"/product/projects/{project}/github/change-sets",
        headers=auth,
        json={
            "binding_id": binding,
            "branch": "feature/safe",
            "expected_head_sha": base,
            "changes": changes,
            "commit_message": "docs: API SHA-safe commit",
        },
    )
    assert prepared.status_code == 200, prepared.text
    change_set_id = prepared.json()["change_set_id"]

    executed = client.post(
        f"/product/github/change-sets/{change_set_id}/execute",
        headers=auth,
        json={"changes": changes},
    )
    assert executed.status_code == 200, executed.text
    payload = executed.json()
    assert payload["status"] == "VERIFIED"
    assert payload["qa_complete"] is True


def test_api_advertises_v084_plugin_capabilities(configured, monkeypatch):
    rt, project, human, *_ = configured
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1000)
    rt.auth.register_human(human, "owner-v084", "owner-v084-password")
    client = TestClient(create_app(rt))
    meta = client.get("/product/meta")
    assert meta.status_code == 200
    payload = meta.json()
    assert tuple(map(int, payload["version"].split("."))) >= (0, 8, 4)
    assert "plugin_registry" in payload["capabilities"]
    assert "github_sha_safe_commit" in payload["capabilities"]
    assert "standard_sha_qa" in payload["capabilities"]
