from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import pytest
import yaml

from gwr.domain import validate_domain
from gwr.errors import AuthorityDenied, StaleVersion, ValidationError
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).parents[1]
RESEARCH_DOMAIN = ROOT / "domains" / "research.workflow.yaml"


def git_blob_sha(content: str) -> str:
    raw = content.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def tree_sha(label: str) -> str:
    return hashlib.sha1(("tree:" + label).encode("utf-8")).hexdigest()


class DocumentGitAdapter:
    def __init__(self):
        self.repository_id = 1374857546
        self.full_name = "example/research"
        self.branch_heads = {"docs/current": "a" * 40}
        self.snapshots = {
            "a" * 40: {"docs/a.md": "alpha\n", "docs/shared.md": "shared\n"},
            "b" * 40: {"docs/renamed.md": "alpha\n", "docs/shared.md": "shared\n"},
            "c" * 40: {"docs/renamed.md": "beta\n", "docs/shared.md": "shared\n"},
        }
        self.commits = {
            "a" * 40: {"sha": "a" * 40, "parents": [], "tree_sha": tree_sha("a")},
            "b" * 40: {"sha": "b" * 40, "parents": ["a" * 40], "tree_sha": tree_sha("b")},
            "c" * 40: {"sha": "c" * 40, "parents": ["b" * 40], "tree_sha": tree_sha("c")},
        }

    def get_repository_identity(self, repository_full_name: str):
        return {"repository_id": self.repository_id, "full_name": self.full_name}

    def get_branch_head(self, repository_full_name: str, branch: str) -> str:
        return self.branch_heads[branch]

    def get_commit(self, repository_full_name: str, commit_sha: str):
        return copy.deepcopy(self.commits[commit_sha])

    def get_file(self, repository_full_name: str, path: str, ref: str):
        content = self.snapshots.get(ref, {}).get(path)
        if content is None:
            return None
        return {"sha": git_blob_sha(content), "content": content}


@pytest.fixture
def configured(tmp_path):
    rt = GovernedWorkflowRuntime(str(RESEARCH_DOMAIN), str(tmp_path / "p4.db"))
    human = rt.governance.create_actor("HUMAN", "owner-p4", ["human_approver"], [])
    tenant = rt.tenancy.create_tenant("p4 tenant", human)
    workspace = rt.tenancy.create_workspace(tenant, "p4 workspace", human)
    project = rt.create_scoped_project("p4 project", tenant, workspace, human)
    connection = rt.plugins.create_connection(
        project,
        "github",
        "github-readonly-opaque-ref",
        ["REPO_READ"],
        human,
        metadata={"provider": "github"},
    )
    adapter = DocumentGitAdapter()
    rt.plugins.attach_runtime_adapter(connection, adapter)
    binding = rt.github.bind_repository(
        project,
        connection,
        "example/research",
        "main",
        human,
        allowed_branches=["docs/*"],
    )
    yield rt, project, human, connection, binding, adapter
    rt.close()


def register(rt, project, human, binding, adapter, *, key="alpha-doc", path="docs/a.md", commit=None):
    commit = commit or "a" * 40
    content = adapter.snapshots[commit][path]
    return rt.documents.register_document(
        project,
        binding,
        human,
        document_key=key,
        title="Alpha document",
        ref_kind="COMMIT",
        ref_value=commit,
        path=path,
        expected_repository_id=adapter.repository_id,
        expected_commit_sha=commit,
        expected_blob_sha=git_blob_sha(content),
    )


def revise(rt, project, human, binding, adapter, document_id, version, *, commit, path):
    content = adapter.snapshots[commit][path]
    return rt.documents.revise_document(
        project,
        document_id,
        binding,
        human,
        expected_artifact_version=version,
        ref_kind="COMMIT",
        ref_value=commit,
        path=path,
        expected_repository_id=adapter.repository_id,
        expected_commit_sha=commit,
        expected_blob_sha=git_blob_sha(content),
    )


def test_d4_f1_f2_stable_document_and_exact_revision_identity(configured):
    rt, project, human, _, binding, adapter = configured
    result = register(rt, project, human, binding, adapter)
    artifact = rt.knowledge.get_artifact(result["document_id"])
    revision = rt.knowledge.get_current_revision(result["document_id"])
    assert result["document_id"] == artifact["artifact_id"]
    assert result["revision_id"] == revision["revision_id"]
    assert artifact["artifact_type"] == "governed_document"
    assert revision["validity_state"] == "UNVERIFIED"


def test_d4_f3_path_rename_preserves_document_identity(configured):
    rt, project, human, _, binding, adapter = configured
    first = register(rt, project, human, binding, adapter)
    second = revise(
        rt, project, human, binding, adapter,
        first["document_id"], 1, commit="b" * 40, path="docs/renamed.md",
    )
    assert second["document_id"] == first["document_id"]
    assert second["revision_id"] != first["revision_id"]
    doc = rt.documents.get_document(first["document_id"])
    assert doc["storage_locator"]["path"] == "docs/renamed.md"


def test_d4_f4_content_change_preserves_document_identity(configured):
    rt, project, human, _, binding, adapter = configured
    first = register(rt, project, human, binding, adapter)
    renamed = revise(
        rt, project, human, binding, adapter,
        first["document_id"], 1, commit="b" * 40, path="docs/renamed.md",
    )
    changed = revise(
        rt, project, human, binding, adapter,
        first["document_id"], renamed["artifact_version"], commit="c" * 40, path="docs/renamed.md",
    )
    assert changed["document_id"] == first["document_id"]
    assert changed["revision_id"] not in {first["revision_id"], renamed["revision_id"]}
    assert changed["source_identity"]["blob_sha"] == git_blob_sha("beta\n")


def test_d4_f5_same_path_does_not_define_logical_identity(configured):
    rt, project, human, _, binding, adapter = configured
    one = register(rt, project, human, binding, adapter, key="doc-one", path="docs/shared.md")
    two = register(rt, project, human, binding, adapter, key="doc-two", path="docs/shared.md")
    assert one["document_id"] != two["document_id"]


def test_d4_f6_logical_key_is_namespaced_and_path_independent(configured):
    rt, project, human, _, binding, adapter = configured
    first = register(rt, project, human, binding, adapter, key="stable-key")
    artifact = rt.knowledge.get_artifact(first["document_id"])
    assert artifact["logical_key"] == "gwr:document:stable-key"
    revise(rt, project, human, binding, adapter, first["document_id"], 1, commit="b" * 40, path="docs/renamed.md")
    assert rt.knowledge.get_artifact(first["document_id"])["logical_key"] == "gwr:document:stable-key"


def test_d4_f7_stale_expected_version_fails_closed(configured):
    rt, project, human, _, binding, adapter = configured
    first = register(rt, project, human, binding, adapter)
    revise(rt, project, human, binding, adapter, first["document_id"], 1, commit="b" * 40, path="docs/renamed.md")
    with pytest.raises(StaleVersion):
        revise(rt, project, human, binding, adapter, first["document_id"], 1, commit="c" * 40, path="docs/renamed.md")
    assert rt.knowledge.get_artifact(first["document_id"])["version"] == 2


def test_d4_f8_exact_source_expectations_are_required(configured):
    rt, project, human, _, binding, _ = configured
    with pytest.raises(ValidationError):
        rt.documents.register_document(
            project,
            binding,
            human,
            document_key="not-exact",
            title="Not exact",
            ref_kind="BRANCH",
            ref_value="docs/current",
            path="docs/a.md",
            expected_repository_id=None,
            expected_commit_sha=None,
            expected_blob_sha=None,
        )
    assert rt.db.one("SELECT COUNT(*) n FROM artifacts WHERE artifact_type='governed_document'")["n"] == 0


def test_d4_f9_hash_namespaces_remain_distinct(configured):
    rt, project, human, _, binding, adapter = configured
    result = register(rt, project, human, binding, adapter)
    revision = rt.knowledge.get_revision(result["revision_id"])
    source = revision["structured_payload"]["source_identity"]
    assert revision["content_hash"] != source["content_sha256"]
    assert revision["content_hash"] != source["blob_sha"]
    assert source["content_sha256"] != source["blob_sha"]


def test_d4_f10_runtime_startup_does_not_silently_migrate_markdown(configured):
    rt, *_ = configured
    assert rt.db.one("SELECT COUNT(*) n FROM artifacts WHERE artifact_type='governed_document'")["n"] == 0


def test_d4_f11_existing_domain_artifact_behavior_is_preserved(configured):
    rt, project, human, *_ = configured
    artifact = rt.knowledge.create_artifact(project, "prior_art_landscape", "prior-art", human)
    revision = rt.knowledge.create_revision(artifact, {"sources": []}, human, expected_artifact_version=0)
    assert rt.knowledge.get_artifact(artifact)["artifact_type"] == "prior_art_landscape"
    assert rt.knowledge.get_revision(revision["revision_id"])["artifact_id"] == artifact


def test_d4_f12_unknown_non_core_artifact_still_rejected(configured):
    rt, project, human, *_ = configured
    with pytest.raises(ValidationError):
        rt.knowledge.create_artifact(project, "unknown_document_like_type", "x", human)


def test_d4_f13_reserved_core_type_collision_fails_closed():
    data = yaml.safe_load(RESEARCH_DOMAIN.read_text(encoding="utf-8"))
    data["artifact_types"].append(
        {
            "id": "governed_document",
            "maps_to": "PRIM-ARTIFACT",
            "revision_model": "PRIM-REVISION",
            "normative": False,
            "hard_dependencies": [],
            "required_fields": [],
        }
    )
    with pytest.raises(ValidationError):
        validate_domain(data)


def test_d4_f14_existing_authority_and_audit_path_is_preserved(configured):
    rt, project, human, _, binding, adapter = configured
    result = register(rt, project, human, binding, adapter)
    actions = [row["action"] for row in rt.db.all("SELECT action FROM audit_events WHERE project_id=?", (project,))]
    assert "CREATE_ARTIFACT" in actions
    assert "CREATE_REVISION" in actions

    unauthorized = rt.governance.create_actor("AGENT", "unauthorized-p4", ["unrecognized_role"], [])
    rt.tenancy.add_project_member(project, unauthorized, "RESEARCHER", human)
    before = rt.db.one("SELECT COUNT(*) n FROM artifacts WHERE artifact_type='governed_document'")["n"]
    with pytest.raises(AuthorityDenied):
        register(rt, project, unauthorized, binding, adapter, key="denied-doc")
    after = rt.db.one("SELECT COUNT(*) n FROM artifacts WHERE artifact_type='governed_document'")["n"]
    assert before == after
    assert result["document_id"]


def test_d4_f15_registration_does_not_create_later_wave_state(configured):
    rt, project, human, _, binding, adapter = configured
    register(rt, project, human, binding, adapter)
    assert rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"] == 0
    assert rt.db.one("SELECT COUNT(*) n FROM evidence WHERE project_id=?", (project,))["n"] == 0
    assert rt.db.one("SELECT COUNT(*) n FROM gates WHERE project_id=?", (project,))["n"] == 0
