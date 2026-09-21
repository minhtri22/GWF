from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from gwr.errors import InvalidTransition, StaleVersion
from gwr.knowledge import VALIDITY
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).parents[1]
DOMAIN = ROOT / "domains" / "research.workflow.yaml"
EXPECTED_VALIDITY = {"VALID", "STALE", "DIRTY", "FAILED", "UNVERIFIED", "SUPERSEDED"}


@pytest.fixture
def configured(tmp_path):
    rt = GovernedWorkflowRuntime(str(DOMAIN), str(tmp_path / "p6.db"))
    owner = rt.governance.create_actor("HUMAN", "owner-p6", ["human_approver"], [])
    tenant = rt.tenancy.create_tenant("p6 tenant", owner)
    workspace = rt.tenancy.create_workspace(tenant, "p6 workspace", owner)
    project = rt.create_scoped_project("p6 project", tenant, workspace, owner)

    qa_actor = rt.governance.create_actor("AGENT", "qa-p6", ["research_lead"], [])
    rt.tenancy.add_project_member(project, qa_actor, "RESEARCHER", owner)

    document_id, r1 = _new_document(rt, project, owner, "p6-main", "a" * 64, "ACTIVE")
    yield rt, project, owner, qa_actor, document_id, r1
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


def _new_document(rt, project, actor, key, source_hash, lifecycle):
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


def _execution(source_hash, *, findings=None, status="SUCCEEDED", content_status=None):
    findings = findings or []
    if content_status is None:
        content_status = "FINDINGS" if findings else "PASS"
    return {
        "validator_id": "markdownlint-cli2",
        "validator_version": "0.23.3",
        "config_hash": "locked",
        "subject_hash": source_hash,
        "execution_status": status,
        "content_status": content_status,
        "findings": findings,
        "error_code": None if status == "SUCCEEDED" else "TEST_TOOL_FAILURE",
        "started_at": "2026-09-21T00:00:00+00:00",
        "finished_at": "2026-09-21T00:00:01+00:00",
    }


def _finding(rule="MD001", finding_class=None):
    item = {
        "rule_id": rule,
        "message": "document finding",
        "severity": "ERROR",
        "line": 1,
        "column": 1,
        "issue_key": rule,
    }
    if finding_class:
        item["finding_class"] = finding_class
    return item


def _qa(rt, project, document_id, revision_id, qa_actor, source_hash, execution):
    return rt.document_qa.create_qa_record(
        project,
        document_id,
        revision_id,
        qa_actor,
        qa_policy_ref={"policy_id": "dg-p6", "policy_version": "1", "policy_hash": "locked"},
        validator_executions=[execution],
    )


def test_d6_f1_lifecycle_and_validity_are_independent(configured):
    rt, _, _, _, document_id, _ = configured
    state = rt.document_state.inspect_document_state(document_id)
    assert state["lifecycle_state"] == "ACTIVE"
    assert state["kernel_validity_state"] == "UNVERIFIED"
    assert state["effective_validity_state"] == "UNVERIFIED"


def test_d6_f2_new_revision_begins_unverified(configured):
    rt, _, _, _, _, r1 = configured
    assert rt.knowledge.get_revision(r1)["validity_state"] == "UNVERIFIED"


def test_d6_f3_parent_valid_never_transfers(configured):
    rt, project, owner, qa_actor, document_id, r1 = configured
    _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64))
    assert rt.document_state.reconcile_document_validity(document_id)["kernel_validity_state"] == "VALID"
    r2 = _new_revision(rt, document_id, owner, "b" * 64)
    assert rt.knowledge.get_revision(r1)["validity_state"] == "SUPERSEDED"
    assert rt.knowledge.get_revision(r1)["status"] == "SUPERSEDED"
    assert rt.knowledge.get_revision(r2)["validity_state"] == "UNVERIFIED"
    assert rt.knowledge.get_artifact(document_id)["lifecycle_status"] == "ACTIVE"


def test_d6_f4_exact_pass_promotes_only_unverified(configured):
    rt, project, _, qa_actor, document_id, r1 = configured
    _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64))
    result = rt.document_state.reconcile_document_validity(document_id)
    assert result["effective_validity_state"] == "VALID"
    assert result["kernel_validity_state"] == "VALID"
    assert result["kernel_transition"]["before"] == "UNVERIFIED"
    assert result["kernel_transition"]["after"] == "VALID"
    audit = rt.db.one(
        "SELECT * FROM audit_events WHERE action='REVISION_VALIDITY_RECONCILED' AND resource_id=? ORDER BY timestamp DESC LIMIT 1",
        (r1,),
    )
    assert audit is not None


def test_d6_f5_no_exact_qa_cannot_promote(configured):
    rt, _, _, _, document_id, _ = configured
    result = rt.document_state.reconcile_document_validity(document_id)
    assert result["effective_validity_state"] == "UNVERIFIED"
    assert result["kernel_validity_state"] == "UNVERIFIED"
    assert result["kernel_transition"] is None


def test_d6_f6_not_evaluated_cannot_promote(configured):
    rt, project, _, qa_actor, document_id, r1 = configured
    _qa(
        rt,
        project,
        document_id,
        r1,
        qa_actor,
        "a" * 64,
        _execution("a" * 64, status="TOOL_ERROR", content_status="NOT_EVALUATED"),
    )
    result = rt.document_state.reconcile_document_validity(document_id)
    assert result["effective_validity_state"] == "UNVERIFIED"
    assert result["kernel_validity_state"] == "UNVERIFIED"


def test_d6_f7_active_finding_blocks_and_demotes_valid(configured):
    rt, project, _, qa_actor, document_id, r1 = configured
    _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64))
    rt.document_state.reconcile_document_validity(document_id)
    failed = _qa(
        rt,
        project,
        document_id,
        r1,
        qa_actor,
        "a" * 64,
        _execution("a" * 64, findings=[_finding()]),
    )
    result = rt.document_state.reconcile_document_validity(document_id)
    assert failed["overall_status"] == "FAIL"
    assert result["effective_validity_state"] == "BLOCKED"
    assert result["kernel_validity_state"] == "UNVERIFIED"
    assert any(x.startswith("FINDING_OPEN:") for x in result["blocker_codes"])


def test_d6_f8_fail_qa_remains_blocked_despite_effective_waiver(configured):
    rt, project, owner, qa_actor, document_id, r1 = configured
    failed = _qa(
        rt,
        project,
        document_id,
        r1,
        qa_actor,
        "a" * 64,
        _execution("a" * 64, findings=[_finding()]),
    )
    fid = failed["finding_refs"][0]
    proposal = rt.document_qa.prepare_waiver(
        fid,
        qa_actor,
        expected_version=0,
        reason="bounded exception",
        scope={"revision_id": r1},
        expiration_or_review_condition={"condition": "review on next revision"},
        required_approval_policy="normative_research_change",
    )
    p = rt.db.one("SELECT payload_hash FROM proposals WHERE proposal_id=?", (proposal,))
    rt.governance.approve_proposal(proposal, owner, p["payload_hash"])
    waived = rt.document_qa.apply_approved_waiver(fid, proposal, qa_actor, expected_version=0)
    assert waived["waiver_effective"] is True
    result = rt.document_state.reconcile_document_validity(document_id)
    assert result["effective_validity_state"] == "BLOCKED"
    assert "QA_FAIL" in result["blocker_codes"]


def test_d6_f9_stale_dominates_clean_pass(configured):
    rt, project, _, qa_actor, document_id, r1 = configured
    _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64))
    rt.knowledge.set_validity_system(r1, "STALE")
    result = rt.document_state.reconcile_document_validity(document_id)
    assert result["effective_validity_state"] == "STALE"
    assert result["kernel_validity_state"] == "STALE"
    assert result["kernel_transition"] is None


def test_d6_f10_dirty_projects_to_stale(configured):
    rt, _, _, _, document_id, r1 = configured
    rt.knowledge.set_validity_system(r1, "DIRTY")
    result = rt.document_state.reconcile_document_validity(document_id)
    assert result["effective_validity_state"] == "STALE"
    assert result["kernel_validity_state"] == "DIRTY"


def test_d6_f11_failed_projects_to_blocked(configured):
    rt, _, _, _, document_id, r1 = configured
    rt.knowledge.set_validity_system(r1, "FAILED")
    result = rt.document_state.reconcile_document_validity(document_id)
    assert result["effective_validity_state"] == "BLOCKED"
    assert result["kernel_validity_state"] == "FAILED"
    assert "KERNEL_FAILED" in result["blocker_codes"]


def test_d6_f12_blocked_not_added_to_global_validity():
    assert VALIDITY == EXPECTED_VALIDITY
    assert "BLOCKED" not in VALIDITY


def test_d6_f13_generic_gate_remains_blocked(configured):
    rt, project, _, qa_actor, document_id, r1 = configured
    _qa(
        rt,
        project,
        document_id,
        r1,
        qa_actor,
        "a" * 64,
        _execution("a" * 64, findings=[_finding()]),
    )
    result = rt.document_state.reconcile_document_validity(document_id)
    assert result["effective_validity_state"] == "BLOCKED"
    gate = rt.decision.evaluate_gate(project, "prior_art_ready", {"document_id": document_id}, [r1])
    assert gate["result"] == "BLOCKED"
    assert "INPUT_UNVERIFIED" in gate["violations"]


def test_d6_f14_legal_lifecycle_transition_uses_version_and_audit(configured):
    rt, project, owner, _, _, _ = configured
    document_id, revision_id = _new_document(rt, project, owner, "draft-doc", "d" * 64, "DRAFT")
    before = rt.knowledge.get_artifact(document_id)
    first = rt.document_state.transition_lifecycle(
        document_id, "IN_REVIEW", owner, expected_artifact_version=before["version"]
    )
    second = rt.document_state.transition_lifecycle(
        document_id, "ACTIVE", owner, expected_artifact_version=first["artifact_version"]
    )
    assert first["current_revision_id"] == revision_id
    assert second["lifecycle_state"] == "ACTIVE"
    assert second["artifact_version"] == before["version"] + 2
    audits = rt.db.all(
        "SELECT * FROM audit_events WHERE action='DOCUMENT_LIFECYCLE_TRANSITION' AND resource_id=?",
        (document_id,),
    )
    assert len(audits) == 2
    with pytest.raises(StaleVersion):
        rt.document_state.transition_lifecycle(
            document_id, "DEPRECATED", owner, expected_artifact_version=before["version"]
        )


def test_d6_f15_invalid_lifecycle_transition_fails_closed(configured):
    rt, project, owner, _, _, _ = configured
    document_id, _ = _new_document(rt, project, owner, "invalid-life", "e" * 64, "DRAFT")
    version = rt.knowledge.get_artifact(document_id)["version"]
    with pytest.raises(InvalidTransition):
        rt.document_state.transition_lifecycle(
            document_id, "ARCHIVED", owner, expected_artifact_version=version
        )


def test_d6_f16_direct_archival_is_deferred(configured):
    rt, _, owner, _, document_id, _ = configured
    version = rt.knowledge.get_artifact(document_id)["version"]
    with pytest.raises(InvalidTransition):
        rt.document_state.transition_lifecycle(
            document_id, "ARCHIVED", owner, expected_artifact_version=version
        )


def test_d6_f17_revision_and_document_supersession_are_distinct(configured):
    rt, _, owner, _, document_id, r1 = configured
    r2 = _new_revision(rt, document_id, owner, "b" * 64)
    assert r2 != r1
    assert rt.knowledge.get_revision(r1)["status"] == "SUPERSEDED"
    assert rt.knowledge.get_revision(r1)["validity_state"] == "SUPERSEDED"
    assert rt.knowledge.get_artifact(document_id)["lifecycle_status"] == "ACTIVE"


def test_d6_f18_no_authority_or_relation_side_effect(configured):
    rt, project, owner, _, document_id, _ = configured
    trace_before = rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"]
    gate_before = rt.db.one("SELECT COUNT(*) n FROM gates WHERE project_id=?", (project,))["n"]
    version = rt.knowledge.get_artifact(document_id)["version"]
    rt.document_state.transition_lifecycle(
        document_id, "DEPRECATED", owner, expected_artifact_version=version
    )
    rt.document_state.reconcile_document_validity(document_id)
    assert rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"] == trace_before
    assert rt.db.one("SELECT COUNT(*) n FROM gates WHERE project_id=?", (project,))["n"] == gate_before


def test_d6_f19_no_p6_schema_migration(configured):
    rt, *_ = configured
    known = rt.db.migrations.status()["known"]
    assert not any("dg_p6" in x.lower() for x in known)
    tables = set(rt.db.list_tables())
    assert "document_lifecycle" not in tables
    assert "document_validity" not in tables
    assert "document_state" not in tables


def test_d6_f20_p5_semantics_remain_intact(configured):
    rt, project, _, qa_actor, document_id, r1 = configured
    failed = _qa(
        rt,
        project,
        document_id,
        r1,
        qa_actor,
        "a" * 64,
        _execution("a" * 64, findings=[_finding(rule="MD009")]),
    )
    qa_before = rt.document_qa.get_qa_record(failed["qa_record_id"])
    finding_before = rt.document_qa.get_finding(failed["finding_refs"][0])
    state = rt.document_state.inspect_document_state(document_id)
    qa_after = rt.document_qa.get_qa_record(failed["qa_record_id"])
    finding_after = rt.document_qa.get_finding(failed["finding_refs"][0])
    assert state["effective_validity_state"] == "BLOCKED"
    assert qa_after["content_hash"] == qa_before["content_hash"]
    assert finding_after["status"] == finding_before["status"] == "OPEN"
    assert finding_after["version"] == finding_before["version"] == 0
