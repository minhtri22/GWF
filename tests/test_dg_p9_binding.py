from __future__ import annotations

from pathlib import Path

import pytest

from gwr.document_relation import BINDING_LEGALITY, BINDING_MODES
from gwr.errors import ValidationError
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import uid, utcnow


ROOT = Path(__file__).parents[1]
DOMAIN = ROOT / "domains" / "research.workflow.yaml"


@pytest.fixture
def configured(tmp_path):
    rt = GovernedWorkflowRuntime(str(DOMAIN), str(tmp_path / "p9.db"))
    owner = rt.governance.create_actor("HUMAN", "owner-p9", ["human_approver"], [])
    tenant = rt.tenancy.create_tenant("p9 tenant", owner)
    workspace = rt.tenancy.create_workspace(tenant, "p9 workspace", owner)
    project = rt.create_scoped_project("p9 project", tenant, workspace, owner)

    lead = rt.governance.create_actor("AGENT", "lead-p9", ["research_lead"], [])
    rt.tenancy.add_project_member(project, lead, "RESEARCHER", owner)

    d1, r1 = _new_document(rt, project, owner, "p9-one", "1" * 64)
    d2, r2 = _new_document(rt, project, owner, "p9-two", "2" * 64)
    d3, r3 = _new_document(rt, project, owner, "p9-three", "3" * 64)
    yield rt, project, owner, lead, d1, r1, d2, r2, d3, r3
    rt.close()


def _payload(key: str, source_hash: str):
    return {
        "schema": "DG-P4-DOCUMENT-REVISION-v1",
        "document_key": key,
        "title": f"Document {key}",
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
        "source_resolved_at": "2026-09-23T00:00:00+00:00",
    }


def _new_document(rt, project, actor, key, source_hash):
    document_id = rt.knowledge.create_artifact(
        project,
        "governed_document",
        f"gwr:document:{key}",
        actor,
    )
    revision_id = rt.knowledge.create_revision(
        document_id,
        _payload(key, source_hash),
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
    return rt.governance.approve_proposal(proposal_id, owner, row["payload_hash"])


def _declare(
    rt,
    source,
    relation_type,
    target,
    lead,
    owner,
    *,
    mode,
    exact=None,
):
    proposal = rt.document_relations.prepare_relation(
        source,
        relation_type,
        "DOCUMENT",
        target,
        lead,
        binding_mode=mode,
        target_revision_or_hash=exact,
    )
    approval = _approve(rt, proposal, owner)
    row = rt.document_relations.apply_approved_declaration(proposal, lead)
    return row, proposal, approval


def _legacy_relation(
    rt,
    project,
    source_document_id,
    created_revision_id,
    relation_type,
    target_kind,
    target_ref,
):
    relation_id = uid("drel")
    now = utcnow()
    rt.db.conn.execute(
        "INSERT INTO document_relations("
        "relation_id,project_id,source_document_id,relation_type,target_kind,target_ref,"
        "invalidation_policy,status,created_revision_id,create_proposal_id,"
        "retired_revision_id,retired_by_proposal_id,version,created_at,updated_at,retired_at"
        ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            relation_id,
            project,
            source_document_id,
            relation_type,
            target_kind,
            target_ref,
            "LEGACY_P8_POLICY",
            "ACTIVE",
            created_revision_id,
            "legacy-p8-proposal",
            None,
            None,
            0,
            now,
            now,
            None,
        ),
    )
    rt.db.conn.commit()
    return rt.document_relations.get_relation(relation_id)


def _bind(rt, relation_id, lead, owner, *, mode, exact=None, expected_version=0):
    proposal = rt.document_relations.prepare_binding(
        relation_id,
        lead,
        expected_version=expected_version,
        binding_mode=mode,
        target_revision_or_hash=exact,
    )
    approval = _approve(rt, proposal, owner)
    row = rt.document_relations.apply_approved_binding(proposal, lead)
    return row, proposal, approval


def test_d9_f1_only_two_bound_modes_are_legal(configured):
    rt, _, _, lead, d1, _, d2, _, _, _ = configured
    assert BINDING_MODES == {"LOGICAL_CURRENT", "PINNED_REVISION"}
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_relation(
            d1,
            "DEPENDS_ON",
            "DOCUMENT",
            d2,
            lead,
            binding_mode="UNBOUND",
        )


def test_d9_f2_legacy_rows_are_not_auto_backfilled(configured):
    rt, project, _, _, d1, r1, d2, _, _, _ = configured
    row = _legacy_relation(rt, project, d1, r1, "DEPENDS_ON", "DOCUMENT", d2)
    assert row["target_binding_mode"] is None
    assert row["target_revision_or_hash"] is None
    with pytest.raises(ValidationError):
        rt.document_relations.resolve_target(row["relation_id"])


def test_d9_f3_one_time_governed_legacy_binding(configured):
    rt, project, owner, lead, d1, r1, d2, _, _, _ = configured
    legacy = _legacy_relation(rt, project, d1, r1, "DEPENDS_ON", "DOCUMENT", d2)
    row, proposal, approval = _bind(
        rt, legacy["relation_id"], lead, owner, mode="LOGICAL_CURRENT"
    )
    assert row["target_binding_mode"] == "LOGICAL_CURRENT"
    assert row["target_revision_or_hash"] is None
    assert row["version"] == 1
    audit = rt.db.one(
        "SELECT * FROM audit_events WHERE action='DOCUMENT_RELATION_BOUND' "
        "AND resource_id=?",
        (row["relation_id"],),
    )
    assert audit["proposal_id"] == proposal
    assert audit["approval_id"] == approval


def test_d9_f4_rebinding_is_forbidden(configured):
    rt, project, owner, lead, d1, r1, d2, r2, _, _ = configured
    legacy = _legacy_relation(rt, project, d1, r1, "DEPENDS_ON", "DOCUMENT", d2)
    row, _, _ = _bind(rt, legacy["relation_id"], lead, owner, mode="LOGICAL_CURRENT")
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_binding(
            row["relation_id"],
            lead,
            expected_version=1,
            binding_mode="PINNED_REVISION",
            target_revision_or_hash=r2,
        )


@pytest.mark.parametrize("mode", ["LOGICAL_CURRENT", "PINNED_REVISION"])
def test_d9_f5_depends_on_dual_mode(configured, mode):
    rt, project, owner, lead, _, _, d2, r2, _, _ = configured
    source, _ = _new_document(rt, project, owner, f"dep-{mode}", "4" * 64)
    row, _, _ = _declare(
        rt, source, "DEPENDS_ON", d2, lead, owner,
        mode=mode, exact=r2 if mode == "PINNED_REVISION" else None,
    )
    assert row["target_binding_mode"] == mode


@pytest.mark.parametrize("mode", ["LOGICAL_CURRENT", "PINNED_REVISION"])
def test_d9_f6_references_dual_mode(configured, mode):
    rt, project, owner, lead, _, _, d2, r2, _, _ = configured
    source, _ = _new_document(rt, project, owner, f"ref-{mode}", "5" * 64)
    row, _, _ = _declare(
        rt, source, "REFERENCES", d2, lead, owner,
        mode=mode, exact=r2 if mode == "PINNED_REVISION" else None,
    )
    assert row["target_binding_mode"] == mode


def test_d9_f7_must_align_with_is_current_only(configured):
    rt, _, owner, lead, d1, _, d2, r2, _, _ = configured
    row, _, _ = _declare(
        rt, d1, "MUST_ALIGN_WITH", d2, lead, owner, mode="LOGICAL_CURRENT"
    )
    assert row["target_binding_mode"] == "LOGICAL_CURRENT"
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_relation(
            d1, "MUST_ALIGN_WITH", "DOCUMENT", d2, lead,
            binding_mode="PINNED_REVISION", target_revision_or_hash=r2,
        )


@pytest.mark.parametrize("relation_type", ["SUPERSEDES", "DERIVED_FROM", "VALIDATES"])
def test_d9_f8_to_f10_pinned_only_types(configured, relation_type):
    rt, project, owner, lead, _, _, d2, r2, _, _ = configured
    source, _ = _new_document(rt, project, owner, f"pin-{relation_type}", "6" * 64)
    row, _, _ = _declare(
        rt, source, relation_type, d2, lead, owner,
        mode="PINNED_REVISION", exact=r2,
    )
    assert row["target_binding_mode"] == "PINNED_REVISION"
    other, _ = _new_document(rt, project, owner, f"float-{relation_type}", "7" * 64)
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_relation(
            other, relation_type, "DOCUMENT", d2, lead,
            binding_mode="LOGICAL_CURRENT",
        )


@pytest.mark.parametrize("mode", ["LOGICAL_CURRENT", "PINNED_REVISION"])
def test_d9_f11_implements_dual_mode(configured, mode):
    rt, project, owner, lead, _, _, d2, r2, _, _ = configured
    source, _ = _new_document(rt, project, owner, f"impl-{mode}", "8" * 64)
    row, _, _ = _declare(
        rt, source, "IMPLEMENTS", d2, lead, owner,
        mode=mode, exact=r2 if mode == "PINNED_REVISION" else None,
    )
    assert row["target_binding_mode"] == mode


def test_d9_f12_generated_from_is_pinned_only(configured):
    rt, project, owner, lead, _, _, d2, r2, _, _ = configured
    source, _ = _new_document(rt, project, owner, "gen-pin", "9" * 64)
    row, _, _ = _declare(
        rt, source, "GENERATED_FROM", d2, lead, owner,
        mode="PINNED_REVISION", exact=r2,
    )
    assert row["target_revision_or_hash"] == r2
    other, _ = _new_document(rt, project, owner, "gen-float", "a" * 64)
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_relation(
            other, "GENERATED_FROM", "DOCUMENT", d2, lead,
            binding_mode="LOGICAL_CURRENT",
        )


def test_d9_f13_pinned_document_ownership_integrity(configured):
    rt, _, _, lead, d1, _, d2, _, _, r3 = configured
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_relation(
            d1,
            "DEPENDS_ON",
            "DOCUMENT",
            d2,
            lead,
            binding_mode="PINNED_REVISION",
            target_revision_or_hash=r3,
        )


def test_d9_f14_logical_current_document_exact_snapshot(configured):
    rt, _, owner, lead, d1, _, d2, r2, _, _ = configured
    row, _, _ = _declare(
        rt, d1, "DEPENDS_ON", d2, lead, owner, mode="LOGICAL_CURRENT"
    )
    resolved = rt.document_relations.resolve_target(row["relation_id"])
    assert resolved["binding_mode"] == "LOGICAL_CURRENT"
    assert resolved["resolved_revision_id"] == r2
    assert resolved["resolved_content_hash"] == rt.knowledge.get_revision(r2)["content_hash"]
    assert resolved["target_artifact_version"] == rt.knowledge.get_artifact(d2)["version"]
    assert resolved["is_current"] is True


def test_d9_f15_historical_pin_remains_exact_after_target_advances(configured):
    rt, _, owner, lead, d1, _, d2, r2, _, _ = configured
    row, _, _ = _declare(
        rt, d1, "DEPENDS_ON", d2, lead, owner,
        mode="PINNED_REVISION", exact=r2,
    )
    r2b = _new_revision(rt, d2, owner, "b" * 64)
    resolved = rt.document_relations.resolve_target(row["relation_id"])
    assert resolved["resolved_revision_id"] == r2
    assert resolved["current_revision_id"] == r2b
    assert resolved["is_current"] is False


def test_d9_f16_validates_never_floats(configured):
    rt, _, owner, lead, d1, _, d2, r2, _, _ = configured
    row, _, _ = _declare(
        rt, d1, "VALIDATES", d2, lead, owner,
        mode="PINNED_REVISION", exact=r2,
    )
    _new_revision(rt, d2, owner, "c" * 64)
    resolved = rt.document_relations.resolve_target(row["relation_id"])
    assert resolved["resolved_revision_id"] == r2
    assert resolved["is_current"] is False


def test_d9_f17_generated_from_exactness(configured):
    rt, _, owner, lead, d1, _, d2, r2, _, _ = configured
    expected_hash = rt.knowledge.get_revision(r2)["content_hash"]
    row, _, _ = _declare(
        rt, d1, "GENERATED_FROM", d2, lead, owner,
        mode="PINNED_REVISION", exact=r2,
    )
    resolved = rt.document_relations.resolve_target(row["relation_id"])
    assert resolved["resolved_revision_id"] == r2
    assert resolved["resolved_content_hash"] == expected_hash


def test_d9_f18_external_targets_fail_closed(configured):
    rt, project, owner, lead, d1, r1, _, _, _, _ = configured
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_relation(
            d1,
            "IMPLEMENTS",
            "SCHEMA",
            "schema://research/protocol-v1",
            lead,
            binding_mode="LOGICAL_CURRENT",
        )
    legacy = _legacy_relation(
        rt, project, d1, r1, "IMPLEMENTS", "SCHEMA", "schema://research/protocol-v1"
    )
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_binding(
            legacy["relation_id"],
            lead,
            expected_version=0,
            binding_mode="PINNED_REVISION",
            target_revision_or_hash="opaque-caller-token",
        )


def test_d9_f19_resolution_has_zero_governed_side_effects(configured):
    rt, project, owner, lead, d1, _, d2, r2, _, _ = configured
    row, _, _ = _declare(
        rt, d1, "VALIDATES", d2, lead, owner,
        mode="PINNED_REVISION", exact=r2,
    )
    before = {
        "trace": rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"],
        "impact": rt.db.one("SELECT COUNT(*) n FROM impacts WHERE project_id=?", (project,))["n"],
        "evidence": rt.db.one("SELECT COUNT(*) n FROM evidence WHERE project_id=?", (project,))["n"],
        "finding": rt.db.one("SELECT COUNT(*) n FROM document_findings WHERE project_id=?", (project,))["n"],
        "validity": rt.knowledge.get_revision(r2)["validity_state"],
    }
    rt.document_relations.resolve_target(row["relation_id"])
    after = {
        "trace": rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"],
        "impact": rt.db.one("SELECT COUNT(*) n FROM impacts WHERE project_id=?", (project,))["n"],
        "evidence": rt.db.one("SELECT COUNT(*) n FROM evidence WHERE project_id=?", (project,))["n"],
        "finding": rt.db.one("SELECT COUNT(*) n FROM document_findings WHERE project_id=?", (project,))["n"],
        "validity": rt.knowledge.get_revision(r2)["validity_state"],
    }
    assert after == before


def test_d9_f20_no_dg_p10_or_later_wave_side_effects(configured):
    rt, project, owner, lead, d1, r1, d2, _, _, _ = configured
    legacy = _legacy_relation(rt, project, d1, r1, "DEPENDS_ON", "DOCUMENT", d2)
    _bind(rt, legacy["relation_id"], lead, owner, mode="LOGICAL_CURRENT")
    tables = set(rt.db.list_tables())
    assert "document_relations" in tables
    for forbidden in {
        "document_relation_bindings",
        "document_binding_events",
        "document_binding_resolutions",
        "document_binding_cache",
        "document_trace_bindings",
        "document_change_sets",
        "document_trace_projection",
        "catalog_entries",
    }:
        assert forbidden not in tables
    assert BINDING_LEGALITY["VALIDATES"] == {"PINNED_REVISION"}
    assert BINDING_LEGALITY["GENERATED_FROM"] == {"PINNED_REVISION"}
    assert BINDING_LEGALITY["DERIVED_FROM"] == {"PINNED_REVISION"}
    assert BINDING_LEGALITY["SUPERSEDES"] == {"PINNED_REVISION"}
    assert BINDING_LEGALITY["MUST_ALIGN_WITH"] == {"LOGICAL_CURRENT"}
