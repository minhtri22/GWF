from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path

import pytest

from gwr.errors import AuthorityDenied, NotFound, StaleVersion, ValidationError
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).parents[1]


def git_blob_sha(content: str) -> str:
    raw = content.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def tree_sha(label: str) -> str:
    return hashlib.sha1(("tree:" + label).encode("utf-8")).hexdigest()


class ResolverAdapter:
    def __init__(self):
        self.repository_id = 1374857546
        self.full_name = "example/research"
        self.branch_heads = {"feature/current": "a" * 40}
        self.snapshots = {
            "a" * 40: {
                "docs/a.md": "alpha\n",
                "docs/rename-source.md": "same\n",
            },
            "b" * 40: {
                "docs/a.md": "beta\n",
                "docs/renamed.md": "same\n",
            },
        }
        self.commits = {
            "a" * 40: {"sha": "a" * 40, "parents": [], "tree_sha": tree_sha("a")},
            "b" * 40: {"sha": "b" * 40, "parents": ["a" * 40], "tree_sha": tree_sha("b")},
        }
        self.fail_repository = False
        self.fail_file = False
        self.commit_calls = 0

    def get_repository_identity(self, repository_full_name: str):
        if self.fail_repository:
            raise ValidationError("provider unavailable")
        return {"repository_id": self.repository_id, "full_name": self.full_name}

    def get_branch_head(self, repository_full_name: str, branch: str) -> str:
        return self.branch_heads[branch]

    def get_commit(self, repository_full_name: str, commit_sha: str):
        return deepcopy(self.commits[commit_sha])

    def get_file(self, repository_full_name: str, path: str, ref: str):
        if self.fail_file:
            raise ValidationError("provider unavailable")
        content = self.snapshots.get(ref, {}).get(path)
        if content is None:
            return None
        return {"sha": git_blob_sha(content), "content": content}

    def commit_files(self, repository_full_name, branch, expected_head_sha, message, changes):
        self.commit_calls += 1
        return {"commit_sha": "c" * 40, "parent_sha": expected_head_sha}


@pytest.fixture
def configured(tmp_path):
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "research.workflow.yaml"),
        str(tmp_path / "p3.db"),
    )
    human = rt.governance.create_actor("HUMAN", "owner-p3", ["human_approver"], [])
    tenant = rt.tenancy.create_tenant("p3 tenant", human)
    workspace = rt.tenancy.create_workspace(tenant, "p3 workspace", human)
    project = rt.create_scoped_project("p3 project", tenant, workspace, human)
    agent = rt.governance.create_actor("AGENT", "agent-p3", ["research_lead"], [])
    rt.tenancy.add_project_member(project, agent, "RESEARCHER", human)
    connection = rt.plugins.create_connection(
        project,
        "github",
        "github-readonly-opaque-ref",
        ["REPO_READ"],
        human,
        metadata={"provider": "github"},
    )
    adapter = ResolverAdapter()
    rt.plugins.attach_runtime_adapter(connection, adapter)
    binding = rt.github.bind_repository(
        project,
        connection,
        "example/research",
        "main",
        human,
        allowed_branches=["feature/*"],
    )
    yield rt, project, human, agent, connection, binding, adapter
    rt.close()


def resolve(rt, project, agent, binding, **kwargs):
    return rt.github.resolve_blob_revision(
        project,
        binding,
        agent,
        ref_kind=kwargs.pop("ref_kind", "COMMIT"),
        ref_value=kwargs.pop("ref_value", "a" * 40),
        path=kwargs.pop("path", "docs/a.md"),
        **kwargs,
    )


def test_f1_exact_repository_branch_blob_success(configured):
    rt, project, _, agent, _, binding, adapter = configured
    result = resolve(
        rt, project, agent, binding,
        ref_kind="BRANCH",
        ref_value="feature/current",
        expected_repository_id=adapter.repository_id,
        expected_commit_sha="a" * 40,
        expected_blob_sha=git_blob_sha("alpha\n"),
    )
    assert result["repository_id"] == adapter.repository_id
    assert result["resolved_commit_sha"] == "a" * 40
    assert result["blob_sha"] == git_blob_sha("alpha\n")
    assert result["content_sha256"] == hashlib.sha256(b"alpha\n").hexdigest()
    assert "content" not in result


def test_f2_exact_commit_does_not_consult_branch(configured):
    rt, project, _, agent, _, binding, adapter = configured
    adapter.branch_heads["feature/current"] = "b" * 40
    result = resolve(rt, project, agent, binding, ref_kind="COMMIT", ref_value="a" * 40)
    assert result["resolved_commit_sha"] == "a" * 40
    assert result["blob_sha"] == git_blob_sha("alpha\n")


def test_f3_stale_repository_identity_fails_closed(configured):
    rt, project, _, agent, _, binding, _ = configured
    with pytest.raises(StaleVersion):
        resolve(rt, project, agent, binding, expected_repository_id="999")


def test_f4_stale_expected_commit_does_not_refresh(configured):
    rt, project, _, agent, _, binding, adapter = configured
    adapter.branch_heads["feature/current"] = "b" * 40
    with pytest.raises(StaleVersion):
        resolve(
            rt, project, agent, binding,
            ref_kind="BRANCH",
            ref_value="feature/current",
            expected_commit_sha="a" * 40,
        )


def test_f5_stale_expected_blob_fails_closed(configured):
    rt, project, _, agent, _, binding, _ = configured
    with pytest.raises(StaleVersion):
        resolve(rt, project, agent, binding, expected_blob_sha="0" * 40)


def test_f6_same_path_at_two_commits_has_different_blob_identity(configured):
    rt, project, _, agent, _, binding, _ = configured
    a = resolve(rt, project, agent, binding, ref_value="a" * 40, path="docs/a.md")
    b = resolve(rt, project, agent, binding, ref_value="b" * 40, path="docs/a.md")
    assert a["path_locator"] == b["path_locator"]
    assert a["blob_sha"] != b["blob_sha"]


def test_f7_same_blob_can_survive_locator_change(configured):
    rt, project, _, agent, _, binding, _ = configured
    before = resolve(rt, project, agent, binding, ref_value="a" * 40, path="docs/rename-source.md")
    after = resolve(rt, project, agent, binding, ref_value="b" * 40, path="docs/renamed.md")
    assert before["path_locator"] != after["path_locator"]
    assert before["blob_sha"] == after["blob_sha"]


def test_f8_missing_subject_is_not_empty_success(configured):
    rt, project, _, agent, _, binding, _ = configured
    with pytest.raises(NotFound):
        resolve(rt, project, agent, binding, path="docs/missing.md")


def test_f9_short_sha_is_rejected(configured):
    rt, project, _, agent, _, binding, _ = configured
    with pytest.raises(ValidationError):
        resolve(rt, project, agent, binding, ref_value="abc1234")
    with pytest.raises(ValidationError):
        resolve(rt, project, agent, binding, expected_blob_sha="deadbeef")


def test_f10_readonly_binding_can_resolve_but_cannot_prepare_write(configured):
    rt, project, _, agent, _, binding, adapter = configured
    assert resolve(rt, project, agent, binding)["blob_sha"] == git_blob_sha("alpha\n")
    with pytest.raises(AuthorityDenied):
        rt.github.prepare_change_set(
            project,
            binding,
            "feature/current",
            "a" * 40,
            [{"path": "docs/new.md", "operation": "CREATE", "content": "x\n"}],
            "docs: should be denied",
            agent,
        )
    assert adapter.commit_calls == 0


def test_f11_runtime_credential_material_is_not_in_normalized_evidence(configured):
    rt, project, _, agent, _, binding, _ = configured
    result = resolve(rt, project, agent, binding)
    rendered = repr(result)
    assert "github-readonly-opaque-ref" not in rendered
    assert "ghp_" not in rendered
    assert "Authorization" not in rendered


def test_f12_provider_failure_emits_no_success_evidence(configured):
    rt, project, _, agent, _, binding, adapter = configured
    adapter.fail_file = True
    with pytest.raises(ValidationError):
        resolve(rt, project, agent, binding)


def test_f13_exact_resolution_normalizes_deterministically(configured):
    rt, project, _, agent, _, binding, _ = configured
    one = resolve(rt, project, agent, binding)
    two = resolve(rt, project, agent, binding)
    one.pop("resolved_at")
    two.pop("resolved_at")
    assert one == two


def test_existing_write_connection_still_prepares_after_capability_separation(tmp_path):
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "research.workflow.yaml"),
        str(tmp_path / "p3-write.db"),
    )
    human = rt.governance.create_actor("HUMAN", "owner-p3-write", ["human_approver"], [])
    tenant = rt.tenancy.create_tenant("p3 write tenant", human)
    workspace = rt.tenancy.create_workspace(tenant, "p3 write workspace", human)
    project = rt.create_scoped_project("p3 write project", tenant, workspace, human)
    agent = rt.governance.create_actor("AGENT", "agent-p3-write", ["research_lead"], [])
    rt.tenancy.add_project_member(project, agent, "RESEARCHER", human)
    connection = rt.plugins.create_connection(
        project,
        "github",
        "github-write-opaque-ref",
        ["REPO_READ", "CONTENT_WRITE"],
        human,
    )
    adapter = ResolverAdapter()
    rt.plugins.attach_runtime_adapter(connection, adapter)
    binding = rt.github.bind_repository(
        project, connection, "example/research", "main", human, allowed_branches=["feature/*"]
    )
    change_set = rt.github.prepare_change_set(
        project,
        binding,
        "feature/current",
        "a" * 40,
        [{"path": "docs/new.md", "operation": "CREATE", "content": "x\n"}],
        "docs: writable connection",
        agent,
    )
    assert rt.github.inspect(change_set)["status"] == "PREPARED"
    rt.close()
