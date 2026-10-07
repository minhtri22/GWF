from __future__ import annotations

from pathlib import Path

import pytest

from gwr.errors import StaleVersion, ValidationError
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import canonical_json, uid, utcnow


ROOT = Path(__file__).parents[1]
DOMAIN = ROOT / "domains" / "research.workflow.yaml"


@pytest.fixture
def configured(tmp_path):
    rt = GovernedWorkflowRuntime(str(DOMAIN), str(tmp_path / "p7.db"))
    owner = rt.governance.create_actor("HUMAN", "owner-p7", ["human_approver"], [])
    tenant = rt.tenancy.create_tenant("p7 tenant", owner)
    workspace = rt.tenancy.create_workspace(tenant, "p7 workspace", owner)
    project = rt.create_scoped_project("p7 project", tenant, workspace, owner)

    lead = rt.governance.create_actor("AGENT", "lead-p7", ["research_lead"], [])
    rt.tenancy.add_project_member(project, lead, "RESEARCHER", owner)

    d1, r1 = _new_document(rt, project, owner, "p7-one", "1" * 64, "ACTIVE")
    yield rt, project, owner, lead, d1, r1
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


def _new_document(rt, project, actor, key, source_hash, lifecycle="ACTIVE"):
    document_id = rt.knowledge.create_artifact(
        project,
        "governed_document",
        f"gwr:document:{key}",
        actor,
        lifecycle_status=lifecycle,
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
    row = rt.db.one("SELECT payload_hash FROM proposals WHERE proposal_id=?", (proposal_id,))
    return rt.governance.approve_proposal(proposal_id, owner, row["payload_hash"])


def _primary(rt, document_id, scope, key, lead, owner):
    proposal = rt.document_authority.prepare_primary_claim(document_id, scope, key, lead)
    approval = _approve(rt, proposal, owner)
    result = rt.document_authority.apply_approved_grant(proposal, lead)
    return result["claim_ids"][0], proposal, approval


def _composition(rt, project, members, scope, key, lead, owner):
    proposal = rt.document_authority.prepare_composed_claims(project, scope, key, members, lead)
    _approve(rt, proposal, owner)
    result = rt.document_authority.apply_approved_grant(proposal, lead)
    return result["claim_ids"], proposal


def _import_primary(rt, project, document_id, revision_id, scope, key):
    claim_id = uid("claim")
    now = utcnow()
    rt.db.conn.execute(
        "INSERT INTO document_authority_claims VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            claim_id,
            project,
            document_id,
            scope,
            key,
            "PRIMARY",
            None,
            None,
            None,
            "ACTIVE",
            revision_id,
            "imported",
            None,
            0,
            now,
            now,
            None,
        ),
    )
    rt.db.conn.commit()
    return claim_id


def _clean_qa(rt, project, document_id, revision_id, actor, source_hash):
    return rt.document_qa.create_qa_record(
        project,
        document_id,
        revision_id,
        actor,
        qa_policy_ref={"policy_id": "p7-content", "policy_version": "1", "policy_hash": "locked"},
        validator_executions=[
            {
                "validator_id": "markdownlint-cli2",
                "validator_version": "0.23.3",
                "config_hash": "locked",
                "subject_hash": source_hash,
                "execution_status": "SUCCEEDED",
                "content_status": "PASS",
                "findings": [],
                "started_at": "2026-09-21T00:00:00+00:00",
                "finished_at": "2026-09-21T00:00:01+00:00",
            }
        ],
    )


def test_d7_f1_zero_claims_supported(configured):
    rt, _, _, _, d1, _ = configured
    assert rt.document_authority.list_claims(document_id=d1) == []


def test_d7_f2_one_primary_claim(configured):
    rt, _, owner, lead, d1, r1 = configured
    claim_id, proposal, _ = _primary(rt, d1, "research.protocol", "execution-amendment", lead, owner)
    claim = rt.document_authority.get_claim(claim_id)
    assert claim["status"] == "ACTIVE"
    assert claim["mode"] == "PRIMARY"
    assert claim["document_id"] == d1
    assert claim["granted_revision_id"] == r1
    assert claim["grant_proposal_id"] == proposal


def test_d7_f3_multiple_non_conflicting_claims(configured):
    rt, _, owner, lead, d1, _ = configured
    _primary(rt, d1, "research.protocol", "execution-amendment", lead, owner)
    _primary(rt, d1, "research.protocol", "report-contract", lead, owner)
    claims = rt.document_authority.list_claims(document_id=d1)
    assert len(claims) == 2
    assert {x["authority_key"] for x in claims} == {"execution-amendment", "report-contract"}


def test_d7_f4_same_scope_different_keys_do_not_collide(configured):
    rt, project, owner, lead, d1, _ = configured
    d2, _ = _new_document(rt, project, owner, "p7-two", "2" * 64)
    _primary(rt, d1, "research.protocol", "alpha", lead, owner)
    _primary(rt, d2, "research.protocol", "beta", lead, owner)
    assert rt.document_authority.inspect_collision(project, "research.protocol", "alpha")["collision"] is False
    assert rt.document_authority.inspect_collision(project, "research.protocol", "beta")["collision"] is False


def test_d7_f5_duplicate_primary_produces_duplicate_authority(configured):
    rt, project, owner, lead, d1, _ = configured
    d2, r2 = _new_document(rt, project, owner, "p7-two", "2" * 64)
    _primary(rt, d1, "research.protocol", "alpha", lead, owner)
    _import_primary(rt, project, d2, r2, "research.protocol", "alpha")
    scan = rt.document_authority.scan_authority_key(project, "research.protocol", "alpha", lead)
    assert scan["collision"] is True
    assert len(scan["finding_refs"]) == 2
    assert {
        rt.document_qa.get_finding(fid)["finding_class"] for fid in scan["finding_refs"]
    } == {"DUPLICATE_AUTHORITY"}


def test_d7_f6_informative_summary_has_no_implicit_authority(configured):
    rt, _, _, _, d1, _ = configured
    doc = rt.documents.get_document(d1)
    assert doc["title"].startswith("Document")
    assert rt.document_authority.list_claims(document_id=d1) == []


def test_d7_f7_actor_authority_is_not_document_authority(configured):
    rt, project, _, lead, d1, _ = configured
    assert rt.governance.authorize(lead, "CREATE_REVISION", {"project_id": project, "artifact_type": "governed_document"})
    assert rt.document_authority.list_claims(document_id=d1) == []


def test_d7_f8_authority_policies_remain_actor_authorization_only(configured):
    rt, _, owner, lead, d1, _ = configured
    before = [dict(x) for x in rt.db.all("SELECT * FROM authority_policies ORDER BY policy_id")]
    _primary(rt, d1, "research.protocol", "alpha", lead, owner)
    after = [dict(x) for x in rt.db.all("SELECT * FROM authority_policies ORDER BY policy_id")]
    assert after == before


def test_d7_f9_claim_provenance_is_exact(configured):
    rt, _, owner, lead, d1, r1 = configured
    claim_id, proposal, approval = _primary(rt, d1, "research.protocol", "alpha", lead, owner)
    claim = rt.document_authority.get_claim(claim_id)
    assert claim["granted_revision_id"] == r1
    assert claim["grant_proposal_id"] == proposal
    audit = rt.db.one(
        "SELECT * FROM audit_events WHERE action='DOCUMENT_AUTHORITY_GRANTED' AND resource_id=?",
        (claim_id,),
    )
    assert audit["proposal_id"] == proposal
    assert audit["approval_id"] == approval


def test_d7_f10_stale_claim_retirement_rejected(configured):
    rt, _, owner, lead, d1, _ = configured
    claim_id, _, _ = _primary(rt, d1, "research.protocol", "alpha", lead, owner)
    p1 = rt.document_authority.prepare_retirement(claim_id, lead, expected_version=0)
    p2 = rt.document_authority.prepare_retirement(claim_id, lead, expected_version=0)
    _approve(rt, p1, owner)
    _approve(rt, p2, owner)
    rt.document_authority.apply_approved_retirement(p1, lead)
    with pytest.raises(StaleVersion):
        rt.document_authority.apply_approved_retirement(p2, lead)


def test_d7_f11_retirement_preserves_history(configured):
    rt, project, owner, lead, d1, _ = configured
    claim_id, _, _ = _primary(rt, d1, "research.protocol", "alpha", lead, owner)
    proposal = rt.document_authority.prepare_retirement(claim_id, lead, expected_version=0)
    _approve(rt, proposal, owner)
    retired = rt.document_authority.apply_approved_retirement(proposal, lead)
    assert retired["status"] == "RETIRED"
    assert retired["version"] == 1
    assert retired["retired_by_proposal_id"] == proposal
    assert rt.document_authority.effective_claims(project, "research.protocol", "alpha") == []
    assert rt.document_authority.get_claim(claim_id)["claim_id"] == claim_id


def test_d7_f12_draft_and_in_review_claims_are_not_effective(configured):
    rt, project, owner, lead, _, _ = configured
    for state, key in [("DRAFT", "draft-owner"), ("IN_REVIEW", "review-owner")]:
        doc, _ = _new_document(rt, project, owner, f"p7-{key}", "3" * 64, state)
        _primary(rt, doc, "research.protocol", key, lead, owner)
        assert rt.document_authority.effective_claims(project, "research.protocol", key) == []


def test_d7_f13_deprecated_owner_remains_effective(configured):
    rt, project, owner, lead, _, _ = configured
    doc, _ = _new_document(rt, project, owner, "p7-deprecated", "4" * 64, "DEPRECATED")
    claim_id, _, _ = _primary(rt, doc, "research.protocol", "deprecated-owner", lead, owner)
    effective = rt.document_authority.effective_claims(project, "research.protocol", "deprecated-owner")
    assert [x["claim_id"] for x in effective] == [claim_id]


def test_d7_f14_superseded_and_archived_owners_are_ineffective(configured):
    rt, project, owner, lead, _, _ = configured
    for state, key in [("SUPERSEDED", "sup-owner"), ("ARCHIVED", "arch-owner")]:
        doc, _ = _new_document(rt, project, owner, f"p7-{key}", "5" * 64, state)
        _primary(rt, doc, "research.protocol", key, lead, owner)
        assert rt.document_authority.effective_claims(project, "research.protocol", key) == []


def test_d7_f15_valid_composed_cluster(configured):
    rt, project, owner, lead, d1, _ = configured
    d2, _ = _new_document(rt, project, owner, "p7-two", "2" * 64)
    claims, proposal = _composition(
        rt,
        project,
        [{"document_id": d1, "role": "normative"}, {"document_id": d2, "role": "constraints"}],
        "research.protocol",
        "composed",
        lead,
        owner,
    )
    assert len(claims) == 2
    state = rt.document_authority.inspect_collision(project, "research.protocol", "composed")
    assert state["collision"] is False
    assert state["reason"] == "VALID_COMPOSITION"
    rows = [rt.document_authority.get_claim(x) for x in claims]
    assert {x["composition_policy_ref"] for x in rows} == {proposal}
    assert len({x["composition_policy_hash"] for x in rows}) == 1


def test_d7_f16_composition_mismatches_collide(configured):
    rt, project, owner, lead, d1, _ = configured
    d2, r2 = _new_document(rt, project, owner, "p7-two", "2" * 64)
    claims, _ = _composition(
        rt,
        project,
        [{"document_id": d1, "role": "normative"}, {"document_id": d2, "role": "constraints"}],
        "research.protocol",
        "composed",
        lead,
        owner,
    )
    rt.db.conn.execute(
        "UPDATE document_authority_claims SET composition_role='wrong-role' WHERE claim_id=?",
        (claims[1],),
    )
    rt.db.conn.commit()
    assert rt.document_authority.inspect_collision(project, "research.protocol", "composed")["collision"] is True

    rt.db.conn.execute(
        "UPDATE document_authority_claims SET composition_role='constraints' WHERE claim_id=?",
        (claims[1],),
    )
    rt.db.conn.execute("UPDATE artifacts SET lifecycle_status='DRAFT' WHERE artifact_id=?", (d2,))
    rt.db.conn.commit()
    missing = rt.document_authority.inspect_collision(project, "research.protocol", "composed")
    assert missing["collision"] is True

    rt.db.conn.execute("UPDATE artifacts SET lifecycle_status='ACTIVE' WHERE artifact_id=?", (d2,))
    outsider, _ = _new_document(rt, project, owner, "p7-outsider", "6" * 64)
    outsider_rev = rt.knowledge.get_artifact(outsider)["current_revision_id"]
    _import_primary(rt, project, outsider, outsider_rev, "research.protocol", "composed")
    mixed = rt.document_authority.inspect_collision(project, "research.protocol", "composed")
    assert mixed["collision"] is True


def test_d7_f17_duplicate_authority_is_non_waivable(configured):
    rt, project, owner, lead, d1, _ = configured
    d2, r2 = _new_document(rt, project, owner, "p7-two", "2" * 64)
    _primary(rt, d1, "research.protocol", "alpha", lead, owner)
    _import_primary(rt, project, d2, r2, "research.protocol", "alpha")
    scan = rt.document_authority.scan_authority_key(project, "research.protocol", "alpha", lead)
    with pytest.raises(ValidationError):
        rt.document_qa.prepare_waiver(
            scan["finding_refs"][0],
            lead,
            expected_version=0,
            reason="must not waive",
            scope={"authority_key": "alpha"},
            expiration_or_review_condition={"condition": "never"},
            required_approval_policy="normative_research_change",
        )


def test_d7_f18_duplicate_finding_blocks_effective_validity(configured):
    rt, project, owner, lead, d1, r1 = configured
    _clean_qa(rt, project, d1, r1, lead, "1" * 64)
    assert rt.document_state.reconcile_document_validity(d1)["kernel_validity_state"] == "VALID"

    d2, r2 = _new_document(rt, project, owner, "p7-two", "2" * 64)
    _primary(rt, d1, "research.protocol", "alpha", lead, owner)
    _import_primary(rt, project, d2, r2, "research.protocol", "alpha")
    rt.document_authority.scan_authority_key(project, "research.protocol", "alpha", lead)
    state = rt.document_state.reconcile_document_validity(d1)
    assert state["effective_validity_state"] == "BLOCKED"
    assert state["kernel_validity_state"] != "VALID"
    assert any(x.startswith("FINDING_OPEN:") for x in state["blocker_codes"])


def test_d7_f19_new_revision_does_not_duplicate_claim(configured):
    rt, _, owner, lead, d1, r1 = configured
    claim_id, _, _ = _primary(rt, d1, "research.protocol", "alpha", lead, owner)
    r2 = _new_revision(rt, d1, owner, "7" * 64)
    claims = rt.document_authority.list_claims(document_id=d1)
    assert [x["claim_id"] for x in claims] == [claim_id]
    assert claims[0]["granted_revision_id"] == r1
    assert rt.knowledge.get_revision(r2)["validity_state"] == "UNVERIFIED"
    assert rt.document_qa.get_current_qa_status(d1) is None


def test_d7_f20_no_later_wave_side_effects(configured):
    rt, project, owner, lead, d1, _ = configured
    trace_before = rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"]
    tables_before = set(rt.db.list_tables())
    relation_rows_before = (
        rt.db.one("SELECT COUNT(*) n FROM document_relations WHERE project_id=?", (project,))["n"]
        if "document_relations" in tables_before
        else None
    )

    _primary(rt, d1, "research.protocol", "alpha", lead, owner)
    no_collision = rt.document_authority.scan_authority_key(project, "research.protocol", "alpha", lead)

    assert no_collision["collision"] is False
    assert no_collision["qa_records"] == []
    assert rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"] == trace_before

    tables_after = set(rt.db.list_tables())
    assert "document_authority_claims" in tables_after
    if relation_rows_before is not None:
        assert rt.db.one(
            "SELECT COUNT(*) n FROM document_relations WHERE project_id=?",
            (project,),
        )["n"] == relation_rows_before

    for forbidden in {
        "document_relation_bindings",
        "document_change_sets",
        "catalog_entries",
        "document_authority_composition",
        "duplicate_authority",
    }:
        assert forbidden not in tables_after
