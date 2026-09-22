from __future__ import annotations

from pathlib import Path

import pytest

from gwr.document_relation import (
    DEFAULT_INVALIDATION_POLICIES,
    RELATION_TYPES,
    TARGET_KINDS,
)
from gwr.errors import StaleVersion, ValidationError
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).parents[1]
DOMAIN = ROOT / "domains" / "research.workflow.yaml"


@pytest.fixture
def configured(tmp_path):
    rt = GovernedWorkflowRuntime(str(DOMAIN), str(tmp_path / "p8.db"))
    owner = rt.governance.create_actor("HUMAN", "owner-p8", ["human_approver"], [])
    tenant = rt.tenancy.create_tenant("p8 tenant", owner)
    workspace = rt.tenancy.create_workspace(tenant, "p8 workspace", owner)
    project = rt.create_scoped_project("p8 project", tenant, workspace, owner)

    lead = rt.governance.create_actor("AGENT", "lead-p8", ["research_lead"], [])
    rt.tenancy.add_project_member(project, lead, "RESEARCHER", owner)

    d1, r1 = _new_document(rt, project, owner, "p8-one", "1" * 64)
    d2, r2 = _new_document(rt, project, owner, "p8-two", "2" * 64)
    yield rt, project, owner, lead, d1, r1, d2, r2
    rt.close()


def _payload(key: str, source_hash: str, *, title: str | None = None):
    return {
        "schema": "DG-P4-DOCUMENT-REVISION-v1",
        "document_key": key,
        "title": title or f"Document {key}",
        "storage_locator": {
            "provider": "github",
            "repository_id": 1374857546,
            "repository_full_name_at_resolution": "minhtri22/GWF",
            "path": f"docs/{key}.md",
        },
        "source_identity": {
            "commit_sha": source_hash[:40],
            "blob_sha": source_hash[:40],
            "content_sha256": source_hash,
            "content_size_bytes": 10,
        },
        "source_resolved_at": "2026-09-21T00:00:00+00:00",
    }


def _new_document(rt, project, actor, key, source_hash, *, title=None):
    document_id = rt.knowledge.create_artifact(
        project,
        "governed_document",
        f"gwr:document:{key}",
        actor,
    )
    revision_id = rt.knowledge.create_revision(
        document_id,
        _payload(key, source_hash, title=title),
        actor,
        expected_artifact_version=0,
    )["revision_id"]
    return document_id, revision_id


def _new_revision(rt, document_id, actor, source_hash):
    artifact = rt.knowledge.get_artifact(document_id)
    key = artifact["logical_key"].split("gwr:document:", 1)[1]
    return rt.knowledge.create_revision(
        document_id,
        _payload(key, source_hash),
        actor,
        expected_artifact_version=artifact["version"],
    )["revision_id"]


def _approve(rt, proposal_id, owner):
    row = rt.db.one(
        "SELECT payload_hash FROM proposals WHERE proposal_id=?",
        (proposal_id,),
    )
    return rt.governance.approve_proposal(
        proposal_id,
        owner,
        row["payload_hash"],
    )


def _relation(
    rt,
    source_document_id,
    relation_type,
    target_kind,
    target_ref,
    lead,
    owner,
    *,
    invalidation_policy=None,
):
    if target_kind != "DOCUMENT":
        raise AssertionError("P8 regression helper only declares native DOCUMENT targets after P9")
    if relation_type == "MUST_ALIGN_WITH":
        binding_mode = "LOGICAL_CURRENT"
        target_revision_or_hash = None
    elif relation_type in {"SUPERSEDES", "DERIVED_FROM", "VALIDATES", "GENERATED_FROM"}:
        binding_mode = "PINNED_REVISION"
        target_revision_or_hash = rt.knowledge.get_artifact(target_ref)["current_revision_id"]
    else:
        binding_mode = "LOGICAL_CURRENT"
        target_revision_or_hash = None
    proposal = rt.document_relations.prepare_relation(
        source_document_id,
        relation_type,
        target_kind,
        target_ref,
        lead,
        binding_mode=binding_mode,
        target_revision_or_hash=target_revision_or_hash,
        invalidation_policy=invalidation_policy,
    )
    approval = _approve(rt, proposal, owner)
    row = rt.document_relations.apply_approved_declaration(proposal, lead)
    return row, proposal, approval


def _primary_claim(rt, document_id, scope, key, lead, owner):
    proposal = rt.document_authority.prepare_primary_claim(
        document_id,
        scope,
        key,
        lead,
    )
    _approve(rt, proposal, owner)
    result = rt.document_authority.apply_approved_grant(proposal, lead)
    return result["claim_ids"][0]


def test_d8_f1_explicit_direction(configured):
    rt, _, owner, lead, d1, _, d2, _ = configured
    row, _, _ = _relation(rt, d1, "DEPENDS_ON", "DOCUMENT", d2, lead, owner)
    assert row["source_document_id"] == d1
    assert row["target_kind"] == "DOCUMENT"
    assert row["target_ref"] == d2


def test_d8_f2_required_relation_vocabulary():
    assert RELATION_TYPES == {
        "DEPENDS_ON",
        "REFERENCES",
        "MUST_ALIGN_WITH",
        "SUPERSEDES",
        "DERIVED_FROM",
        "VALIDATES",
        "IMPLEMENTS",
        "GENERATED_FROM",
    }
    assert TARGET_KINDS == {
        "DOCUMENT",
        "SOURCE_CODE",
        "SCHEMA",
        "API",
        "WORKFLOW",
        "DATASET",
        "STUDY_LOCK",
        "OTHER_ARTIFACT",
    }


def test_d8_f3_markdown_link_does_not_create_relation(configured):
    rt, project, owner, _, _, _, d2, _ = configured
    d3, _ = _new_document(
        rt,
        project,
        owner,
        "p8-link-summary",
        "3" * 64,
        title=f"See [target](document:{d2})",
    )
    assert rt.document_relations.list_relations(source_document_id=d3) == []


def test_d8_f4_existing_trace_link_does_not_create_document_relation(configured):
    rt, project, _, lead, d1, r1, _, r2 = configured
    trace_id = rt.knowledge.create_trace_link(
        project,
        r1,
        "REVISION",
        r2,
        "derived_from",
        "SOFT",
        True,
        "REVIEW",
        lead,
    )
    assert trace_id
    assert rt.document_relations.list_relations(source_document_id=d1) == []


def test_d8_f5_logical_source_identity(configured):
    rt, _, owner, lead, d1, r1, d2, _ = configured
    row, _, _ = _relation(rt, d1, "REFERENCES", "DOCUMENT", d2, lead, owner)
    assert row["source_document_id"] == d1
    assert row["created_revision_id"] == r1


def test_d8_f6_creation_provenance_exact(configured):
    rt, _, owner, lead, d1, r1, d2, _ = configured
    row, proposal, approval = _relation(
        rt, d1, "DEPENDS_ON", "DOCUMENT", d2, lead, owner
    )
    assert row["created_revision_id"] == r1
    assert row["create_proposal_id"] == proposal
    audit = rt.db.one(
        "SELECT * FROM audit_events "
        "WHERE action='DOCUMENT_RELATION_DECLARED' AND resource_id=?",
        (row["relation_id"],),
    )
    assert audit["proposal_id"] == proposal
    assert audit["approval_id"] == approval


def test_d8_f7_new_source_revision_preserves_relation_identity(configured):
    rt, _, owner, lead, d1, r1, d2, _ = configured
    row, _, _ = _relation(rt, d1, "DEPENDS_ON", "DOCUMENT", d2, lead, owner)
    r2 = _new_revision(rt, d1, owner, "7" * 64)
    rows = rt.document_relations.list_relations(source_document_id=d1)
    assert [x["relation_id"] for x in rows] == [row["relation_id"]]
    assert rows[0]["created_revision_id"] == r1
    assert rt.knowledge.get_revision(r2)["validity_state"] == "UNVERIFIED"


def test_d8_f8_active_to_retired_preserves_history(configured):
    rt, _, owner, lead, d1, _, d2, _ = configured
    row, _, _ = _relation(rt, d1, "REFERENCES", "DOCUMENT", d2, lead, owner)
    proposal = rt.document_relations.prepare_retirement(
        row["relation_id"],
        lead,
        expected_version=0,
    )
    _approve(rt, proposal, owner)
    retired = rt.document_relations.apply_approved_retirement(proposal, lead)
    assert retired["status"] == "RETIRED"
    assert retired["version"] == 1
    assert retired["retired_by_proposal_id"] == proposal
    assert retired["retired_revision_id"] is not None
    assert rt.document_relations.get_relation(row["relation_id"])["status"] == "RETIRED"


def test_d8_f9_stale_retirement_rejected(configured):
    rt, _, owner, lead, d1, _, d2, _ = configured
    row, _, _ = _relation(rt, d1, "REFERENCES", "DOCUMENT", d2, lead, owner)
    p1 = rt.document_relations.prepare_retirement(
        row["relation_id"], lead, expected_version=0
    )
    p2 = rt.document_relations.prepare_retirement(
        row["relation_id"], lead, expected_version=0
    )
    _approve(rt, p1, owner)
    _approve(rt, p2, owner)
    rt.document_relations.apply_approved_retirement(p1, lead)
    with pytest.raises(StaleVersion):
        rt.document_relations.apply_approved_retirement(p2, lead)


def test_d8_f10_exact_duplicate_active_relation_rejected(configured):
    rt, _, owner, lead, d1, _, d2, _ = configured
    p1 = rt.document_relations.prepare_relation(
        d1, "DEPENDS_ON", "DOCUMENT", d2, lead, binding_mode="LOGICAL_CURRENT"
    )
    p2 = rt.document_relations.prepare_relation(
        d1, "DEPENDS_ON", "DOCUMENT", d2, lead, binding_mode="LOGICAL_CURRENT"
    )
    _approve(rt, p1, owner)
    _approve(rt, p2, owner)
    rt.document_relations.apply_approved_declaration(p1, lead)
    with pytest.raises(ValidationError):
        rt.document_relations.apply_approved_declaration(p2, lead)


def test_d8_f11_self_document_relation_rejected(configured):
    rt, _, _, lead, d1, _, _, _ = configured
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_relation(
            d1,
            "MUST_ALIGN_WITH",
            "DOCUMENT",
            d1,
            lead,
            binding_mode="LOGICAL_CURRENT",
        )


def test_d8_f12_document_target_integrity(configured):
    rt, _, owner, lead, d1, _, _, _ = configured
    tenant2 = rt.tenancy.create_tenant("p8 tenant 2", owner)
    workspace2 = rt.tenancy.create_workspace(tenant2, "p8 workspace 2", owner)
    project2 = rt.create_scoped_project(
        "p8 other project", tenant2, workspace2, owner
    )
    foreign_doc, _ = _new_document(
        rt, project2, owner, "p8-foreign", "8" * 64
    )
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_relation(
            d1,
            "REFERENCES",
            "DOCUMENT",
            foreign_doc,
            lead,
            binding_mode="LOGICAL_CURRENT",
        )


def test_d8_f13_external_target_vocabulary_preserved_and_p9_fails_closed(configured):
    rt, _, _, lead, d1, _, _, _ = configured
    assert "SCHEMA" in TARGET_KINDS
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_relation(
            d1,
            "IMPLEMENTS",
            "SCHEMA",
            "schema://research/protocol-v1",
            lead,
            binding_mode="LOGICAL_CURRENT",
        )


def test_d8_f14_relation_semantics_remain_distinct(configured):
    rt, _, owner, lead, d1, _, d2, _ = configured
    ref, _, _ = _relation(rt, d1, "REFERENCES", "DOCUMENT", d2, lead, owner)
    dep, _, _ = _relation(rt, d1, "DEPENDS_ON", "DOCUMENT", d2, lead, owner)
    align, _, _ = _relation(
        rt, d1, "MUST_ALIGN_WITH", "DOCUMENT", d2, lead, owner
    )
    assert ref["relation_type"] == "REFERENCES"
    assert dep["relation_type"] == "DEPENDS_ON"
    assert align["relation_type"] == "MUST_ALIGN_WITH"
    assert {
        ref["invalidation_policy"],
        dep["invalidation_policy"],
        align["invalidation_policy"],
    } == {
        DEFAULT_INVALIDATION_POLICIES["REFERENCES"],
        DEFAULT_INVALIDATION_POLICIES["DEPENDS_ON"],
        DEFAULT_INVALIDATION_POLICIES["MUST_ALIGN_WITH"],
    }


def test_d8_f15_supersedes_has_no_p7_or_lifecycle_side_effect(configured):
    rt, _, owner, lead, d1, _, d2, _ = configured
    claim_id = _primary_claim(
        rt,
        d2,
        "research.protocol",
        "source-of-truth",
        lead,
        owner,
    )
    claim_before = rt.document_authority.get_claim(claim_id)
    d1_before = rt.knowledge.get_artifact(d1)["lifecycle_status"]
    d2_before = rt.knowledge.get_artifact(d2)["lifecycle_status"]
    row, _, _ = _relation(rt, d1, "SUPERSEDES", "DOCUMENT", d2, lead, owner)
    assert row["status"] == "ACTIVE"
    assert rt.document_authority.get_claim(claim_id) == claim_before
    assert rt.knowledge.get_artifact(d1)["lifecycle_status"] == d1_before
    assert rt.knowledge.get_artifact(d2)["lifecycle_status"] == d2_before


def test_d8_f16_validates_not_evidence_before_p9_binding(configured):
    rt, project, owner, lead, d1, _, d2, _ = configured
    before = rt.db.one(
        "SELECT COUNT(*) n FROM evidence WHERE project_id=?",
        (project,),
    )["n"]
    row, _, _ = _relation(rt, d1, "VALIDATES", "DOCUMENT", d2, lead, owner)
    after = rt.db.one(
        "SELECT COUNT(*) n FROM evidence WHERE project_id=?",
        (project,),
    )["n"]
    assert after == before
    assert row["invalidation_policy"] == "REQUIRES_PINNED_BINDING"
    assert row["target_binding_mode"] == "PINNED_REVISION"
    assert row["target_revision_or_hash"] is not None


def test_d8_f17_generated_from_not_reproducibility_proof(configured):
    rt, project, owner, lead, d1, _, d2, _ = configured
    evidence_before = rt.db.one(
        "SELECT COUNT(*) n FROM evidence WHERE project_id=?",
        (project,),
    )["n"]
    trace_before = rt.db.one(
        "SELECT COUNT(*) n FROM trace_links WHERE project_id=?",
        (project,),
    )["n"]
    row, _, _ = _relation(
        rt, d1, "GENERATED_FROM", "DOCUMENT", d2, lead, owner
    )
    assert row["invalidation_policy"] == "REQUIRES_PINNED_BINDING"
    assert rt.db.one(
        "SELECT COUNT(*) n FROM evidence WHERE project_id=?",
        (project,),
    )["n"] == evidence_before
    assert rt.db.one(
        "SELECT COUNT(*) n FROM trace_links WHERE project_id=?",
        (project,),
    )["n"] == trace_before


def test_d8_f18_no_trace_link_projection_in_p8(configured):
    rt, project, owner, lead, d1, _, d2, _ = configured
    before = rt.db.one(
        "SELECT COUNT(*) n FROM trace_links WHERE project_id=?",
        (project,),
    )["n"]
    row, _, _ = _relation(rt, d1, "DEPENDS_ON", "DOCUMENT", d2, lead, owner)
    proposal = rt.document_relations.prepare_retirement(
        row["relation_id"], lead, expected_version=0
    )
    _approve(rt, proposal, owner)
    rt.document_relations.apply_approved_retirement(proposal, lead)
    after = rt.db.one(
        "SELECT COUNT(*) n FROM trace_links WHERE project_id=?",
        (project,),
    )["n"]
    assert after == before


def test_d8_f19_zero_additional_p8_graph_tables(configured):
    rt, *_ = configured
    tables = set(rt.db.list_tables())
    assert "document_relations" in tables
    for forbidden in {
        "document_relation_nodes",
        "document_relation_types",
        "document_relation_events",
        "document_trace_projection",
        "document_relation_findings",
    }:
        assert forbidden not in tables
    known = rt.db.migrations.status()["known"]
    assert [x for x in known if "dg_p8" in x.lower()] == [
        "0010_v086_dg_p8_document_relations"
    ]


def test_d8_f20_no_later_wave_side_effects(configured):
    rt, project, owner, lead, d1, _, d2, _ = configured
    trace_before = rt.db.one(
        "SELECT COUNT(*) n FROM trace_links WHERE project_id=?",
        (project,),
    )["n"]
    evidence_before = rt.db.one(
        "SELECT COUNT(*) n FROM evidence WHERE project_id=?",
        (project,),
    )["n"]
    row, _, _ = _relation(rt, d1, "VALIDATES", "DOCUMENT", d2, lead, owner)
    assert row["status"] == "ACTIVE"
    assert rt.db.one(
        "SELECT COUNT(*) n FROM trace_links WHERE project_id=?",
        (project,),
    )["n"] == trace_before
    assert rt.db.one(
        "SELECT COUNT(*) n FROM evidence WHERE project_id=?",
        (project,),
    )["n"] == evidence_before
    tables = set(rt.db.list_tables())
    for forbidden in {
        "document_relation_bindings",
        "document_change_sets",
        "catalog_entries",
        "document_trace_projection",
    }:
        assert forbidden not in tables
