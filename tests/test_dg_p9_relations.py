from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from gwr.db import SCHEMA
from gwr.document_relation import (
    BINDING_LEGALITY,
    BINDING_MODES,
)
from gwr.errors import StaleVersion, ValidationError
from gwr.migrations import MIGRATIONS
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import uid, utcnow


ROOT = Path(__file__).parents[1]
DOMAIN = ROOT / "domains" / "research.workflow.yaml"


@pytest.fixture
def configured(tmp_path):
    rt = GovernedWorkflowRuntime(str(DOMAIN), str(tmp_path / "p9.db"))
    owner = rt.governance.create_actor(
        "HUMAN", "owner-p9", ["human_approver"], []
    )
    tenant = rt.tenancy.create_tenant("p9 tenant", owner)
    workspace = rt.tenancy.create_workspace(tenant, "p9 workspace", owner)
    project = rt.create_scoped_project(
        "p9 project", tenant, workspace, owner
    )
    lead = rt.governance.create_actor(
        "AGENT", "lead-p9", ["research_lead"], []
    )
    rt.tenancy.add_project_member(project, lead, "RESEARCHER", owner)
    d1, r1 = _new_document(rt, project, owner, "p9-one", "1" * 64)
    d2, r2 = _new_document(rt, project, owner, "p9-two", "2" * 64)
    yield rt, project, owner, lead, d1, r1, d2, r2
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
        "source_resolved_at": "2026-09-21T00:00:00+00:00",
    }


def _new_document(rt, project, actor, key, source_hash):
    document_id = rt.knowledge.create_artifact(
        project, "governed_document", f"gwr:document:{key}", actor
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
    return rt.governance.approve_proposal(
        proposal_id, owner, row["payload_hash"]
    )


def _declare(
    rt,
    source,
    relation_type,
    target,
    lead,
    owner,
    mode,
    pin=None,
):
    proposal = rt.document_relations.prepare_relation(
        source,
        relation_type,
        "DOCUMENT",
        target,
        lead,
        target_binding_mode=mode,
        target_revision_or_hash=pin,
    )
    _approve(rt, proposal, owner)
    return rt.document_relations.apply_approved_declaration(
        proposal, lead
    )


def _legacy_relation(
    rt,
    project,
    source_document_id,
    source_revision_id,
    relation_type,
    target_kind,
    target_ref,
):
    relation_id = uid("legacy-drel")
    now = utcnow()
    rt.db.conn.execute(
        "INSERT INTO document_relations("
        "relation_id,project_id,source_document_id,relation_type,"
        "target_kind,target_ref,invalidation_policy,status,"
        "created_revision_id,create_proposal_id,retired_revision_id,"
        "retired_by_proposal_id,version,created_at,updated_at,retired_at,"
        "target_binding_mode,target_revision_or_hash"
        ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            relation_id,
            project,
            source_document_id,
            relation_type,
            target_kind,
            target_ref,
            "LEGACY_P8_POLICY",
            "ACTIVE",
            source_revision_id,
            "legacy-p8-proposal",
            None,
            None,
            0,
            now,
            now,
            None,
            None,
            None,
        ),
    )
    rt.db.conn.commit()
    return relation_id


def _counts(rt, project):
    return {
        "trace": rt.db.one(
            "SELECT COUNT(*) n FROM trace_links WHERE project_id=?",
            (project,),
        )["n"],
        "impact": rt.db.one(
            "SELECT COUNT(*) n FROM impacts WHERE project_id=?",
            (project,),
        )["n"],
        "evidence": rt.db.one(
            "SELECT COUNT(*) n FROM evidence WHERE project_id=?",
            (project,),
        )["n"],
        "finding": rt.db.one(
            "SELECT COUNT(*) n FROM document_findings",
        )["n"],
    }


def test_d9_f1_binding_modes_are_distinct_and_new_relation_requires_explicit_mode(
    configured,
):
    rt, _, _, lead, d1, _, d2, _ = configured
    assert BINDING_MODES == {"LOGICAL_CURRENT", "PINNED_REVISION"}
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_relation(
            d1, "DEPENDS_ON", "DOCUMENT", d2, lead
        )


def test_d9_f2_no_legacy_auto_backfill():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    for migration in MIGRATIONS:
        if migration.migration_id == "0011_v086_dg_p9_relation_binding":
            break
        conn.executescript(migration.sql)
    conn.execute(
        "INSERT INTO document_relations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "legacy",
            "p",
            "s",
            "DEPENDS_ON",
            "DOCUMENT",
            "t",
            "x",
            "ACTIVE",
            "r",
            "proposal",
            None,
            None,
            0,
            "now",
            "now",
            None,
        ),
    )
    p9 = next(
        m for m in MIGRATIONS
        if m.migration_id == "0011_v086_dg_p9_relation_binding"
    )
    conn.executescript(p9.sql)
    row = conn.execute(
        "SELECT target_binding_mode,target_revision_or_hash "
        "FROM document_relations WHERE relation_id='legacy'"
    ).fetchone()
    assert row == (None, None)
    conn.close()


def test_d9_f3_one_time_governed_legacy_binding(configured):
    rt, project, owner, lead, d1, r1, d2, _ = configured
    relation_id = _legacy_relation(
        rt, project, d1, r1, "DEPENDS_ON", "DOCUMENT", d2
    )
    p = rt.document_relations.prepare_binding(
        relation_id,
        lead,
        expected_version=0,
        target_binding_mode="LOGICAL_CURRENT",
    )
    approval = _approve(rt, p, owner)
    bound = rt.document_relations.apply_approved_binding(p, lead)
    assert bound["target_binding_mode"] == "LOGICAL_CURRENT"
    assert bound["target_revision_or_hash"] is None
    assert bound["version"] == 1
    audit = rt.db.one(
        "SELECT * FROM audit_events "
        "WHERE action='DOCUMENT_RELATION_BOUND' AND resource_id=?",
        (relation_id,),
    )
    assert audit["proposal_id"] == p
    assert audit["approval_id"] == approval


def test_d9_f4_no_rebind(configured):
    rt, project, owner, lead, d1, r1, d2, _ = configured
    relation_id = _legacy_relation(
        rt, project, d1, r1, "DEPENDS_ON", "DOCUMENT", d2
    )
    p = rt.document_relations.prepare_binding(
        relation_id,
        lead,
        expected_version=0,
        target_binding_mode="LOGICAL_CURRENT",
    )
    _approve(rt, p, owner)
    rt.document_relations.apply_approved_binding(p, lead)
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_binding(
            relation_id,
            lead,
            expected_version=1,
            target_binding_mode="PINNED_REVISION",
            target_revision_or_hash=rt.knowledge.get_artifact(d2)[
                "current_revision_id"
            ],
        )


def test_d9_f5_depends_on_dual_mode(configured):
    rt, project, owner, lead, d1, _, d2, r2 = configured
    current = _declare(
        rt, d1, "DEPENDS_ON", d2, lead, owner, "LOGICAL_CURRENT"
    )
    d3, r3 = _new_document(rt, project, owner, "p9-three", "3" * 64)
    pinned = _declare(
        rt, d1, "DEPENDS_ON", d3, lead, owner, "PINNED_REVISION", r3
    )
    assert current["target_binding_mode"] == "LOGICAL_CURRENT"
    assert pinned["target_revision_or_hash"] == r3


def test_d9_f6_references_dual_mode(configured):
    rt, project, owner, lead, d1, _, d2, _ = configured
    a = _declare(
        rt, d1, "REFERENCES", d2, lead, owner, "LOGICAL_CURRENT"
    )
    d3, r3 = _new_document(rt, project, owner, "p9-ref", "4" * 64)
    b = _declare(
        rt, d1, "REFERENCES", d3, lead, owner, "PINNED_REVISION", r3
    )
    assert {a["target_binding_mode"], b["target_binding_mode"]} == {
        "LOGICAL_CURRENT",
        "PINNED_REVISION",
    }


def test_d9_f7_must_align_with_current_only(configured):
    rt, _, _, lead, d1, _, d2, r2 = configured
    assert BINDING_LEGALITY["MUST_ALIGN_WITH"] == {"LOGICAL_CURRENT"}
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_relation(
            d1,
            "MUST_ALIGN_WITH",
            "DOCUMENT",
            d2,
            lead,
            target_binding_mode="PINNED_REVISION",
            target_revision_or_hash=r2,
        )


@pytest.mark.parametrize(
    "relation_type",
    ["SUPERSEDES", "DERIVED_FROM", "VALIDATES", "GENERATED_FROM"],
)
def test_d9_f8_to_f10_and_f12_pinned_only(
    configured, relation_type
):
    rt, _, _, lead, d1, _, d2, _ = configured
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_relation(
            d1,
            relation_type,
            "DOCUMENT",
            d2,
            lead,
            target_binding_mode="LOGICAL_CURRENT",
        )


def test_d9_f11_implements_dual_mode(configured):
    rt, project, owner, lead, d1, _, d2, _ = configured
    a = _declare(
        rt, d1, "IMPLEMENTS", d2, lead, owner, "LOGICAL_CURRENT"
    )
    d3, r3 = _new_document(rt, project, owner, "p9-impl", "5" * 64)
    b = _declare(
        rt, d1, "IMPLEMENTS", d3, lead, owner, "PINNED_REVISION", r3
    )
    assert a["target_binding_mode"] != b["target_binding_mode"]


def test_d9_f13_pinned_document_ownership_integrity(configured):
    rt, project, _, lead, d1, _, d2, _ = configured
    _, foreign_revision = _new_document(
        rt, project, rt.knowledge.get_artifact(d1)["created_by_actor_id"],
        "p9-other-target", "6" * 64
    )
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_relation(
            d1,
            "VALIDATES",
            "DOCUMENT",
            d2,
            lead,
            target_binding_mode="PINNED_REVISION",
            target_revision_or_hash=foreign_revision,
        )


def test_d9_f14_logical_current_document_resolution(configured):
    rt, _, owner, lead, d1, _, d2, r2 = configured
    row = _declare(
        rt, d1, "DEPENDS_ON", d2, lead, owner, "LOGICAL_CURRENT"
    )
    first = rt.document_relations.resolve_relation(row["relation_id"])
    assert first["resolved_revision_id"] == r2
    before_row = rt.document_relations.get_relation(row["relation_id"])
    r3 = _new_revision(rt, d2, owner, "7" * 64)
    second = rt.document_relations.resolve_relation(row["relation_id"])
    after_row = rt.document_relations.get_relation(row["relation_id"])
    assert second["resolved_revision_id"] == r3
    assert second["is_current"] is True
    assert before_row == after_row


def test_d9_f15_pinned_historical_resolution(configured):
    rt, _, owner, lead, d1, _, d2, r2 = configured
    row = _declare(
        rt, d1, "DEPENDS_ON", d2, lead, owner, "PINNED_REVISION", r2
    )
    r3 = _new_revision(rt, d2, owner, "8" * 64)
    resolved = rt.document_relations.resolve_relation(row["relation_id"])
    assert resolved["resolved_revision_id"] == r2
    assert resolved["current_revision_id"] == r3
    assert resolved["is_current"] is False


def test_d9_f16_validates_never_floats(configured):
    rt, _, owner, lead, d1, _, d2, r2 = configured
    row = _declare(
        rt, d1, "VALIDATES", d2, lead, owner, "PINNED_REVISION", r2
    )
    _new_revision(rt, d2, owner, "9" * 64)
    resolved = rt.document_relations.resolve_relation(row["relation_id"])
    assert resolved["resolved_revision_id"] == r2
    assert row["target_revision_or_hash"] == r2


def test_d9_f17_generated_from_exactness(configured):
    rt, _, owner, lead, d1, _, d2, r2 = configured
    with pytest.raises(ValidationError):
        rt.document_relations.prepare_relation(
            d1,
            "GENERATED_FROM",
            "DOCUMENT",
            d2,
            lead,
            target_binding_mode="PINNED_REVISION",
        )
    row = _declare(
        rt,
        d1,
        "GENERATED_FROM",
        d2,
        lead,
        owner,
        "PINNED_REVISION",
        r2,
    )
    resolved = rt.document_relations.resolve_relation(row["relation_id"])
    assert resolved["resolved_revision_id"] == r2
    assert resolved["resolved_content_hash"]


def test_d9_f18_external_resolver_fail_closed(configured):
    rt, _, _, lead, d1, _, _, _ = configured
    for mode, pin in (
        ("LOGICAL_CURRENT", None),
        ("PINNED_REVISION", "opaque-caller-token"),
    ):
        with pytest.raises(ValidationError):
            rt.document_relations.prepare_relation(
                d1,
                "IMPLEMENTS",
                "SCHEMA",
                "schema://research/protocol-v1",
                lead,
                target_binding_mode=mode,
                target_revision_or_hash=pin,
            )


def test_d9_f19_zero_tracelink_impact_validity_side_effects(configured):
    rt, project, owner, lead, d1, r1, d2, r2 = configured
    relation_id = _legacy_relation(
        rt, project, d1, r1, "VALIDATES", "DOCUMENT", d2
    )
    before = _counts(rt, project)
    validity_before = rt.knowledge.get_revision(r2)["validity_state"]
    p = rt.document_relations.prepare_binding(
        relation_id,
        lead,
        expected_version=0,
        target_binding_mode="PINNED_REVISION",
        target_revision_or_hash=r2,
    )
    _approve(rt, p, owner)
    rt.document_relations.apply_approved_binding(p, lead)
    rt.document_relations.resolve_relation(relation_id)
    assert _counts(rt, project) == before
    assert rt.knowledge.get_revision(r2)["validity_state"] == validity_before


def test_d9_f20_no_later_wave_side_effects(configured):
    rt, *_ = configured
    tables = set(rt.db.list_tables())
    for forbidden in {
        "document_relation_bindings",
        "document_binding_events",
        "document_binding_resolutions",
        "document_binding_cache",
        "document_trace_bindings",
        "document_change_sets",
        "document_impact_reports",
        "catalog_entries",
        "document_trace_projection",
    }:
        assert forbidden not in tables
    known = rt.db.migrations.status()["known"]
    assert [x for x in known if "dg_p9" in x.lower()] == [
        "0011_v086_dg_p9_relation_binding"
    ]
