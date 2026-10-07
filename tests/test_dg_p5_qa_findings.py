from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from gwr.domain import validate_domain
from gwr.errors import InvalidTransition, StaleVersion, ValidationError
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import content_hash


ROOT = Path(__file__).parents[1]
DOMAIN = ROOT / "domains" / "research.workflow.yaml"


@pytest.fixture
def configured(tmp_path):
    rt = GovernedWorkflowRuntime(str(DOMAIN), str(tmp_path / "p5.db"))
    owner = rt.governance.create_actor("HUMAN", "owner-p5", ["human_approver"], [])
    tenant = rt.tenancy.create_tenant("p5 tenant", owner)
    workspace = rt.tenancy.create_workspace(tenant, "p5 workspace", owner)
    project = rt.create_scoped_project("p5 project", tenant, workspace, owner)

    qa_actor = rt.governance.create_actor("AGENT", "qa-p5", ["research_lead"], [])
    rt.tenancy.add_project_member(project, qa_actor, "RESEARCHER", owner)

    document_id = rt.knowledge.create_artifact(
        project,
        "governed_document",
        "gwr:document:p5-doc",
        owner,
    )
    r1 = _create_revision(rt, document_id, owner, 0, "a" * 64, "docs/p5.md")
    yield rt, project, owner, qa_actor, document_id, r1
    rt.close()


def _payload(source_hash: str, path: str):
    return {
        "schema": "DG-P4-DOCUMENT-REVISION-v1",
        "document_key": "p5-doc",
        "title": "P5 document",
        "storage_locator": {
            "provider": "github",
            "repository_id": 1374857546,
            "repository_full_name_at_resolution": "minhtri22/GWF",
            "path": path,
        },
        "source_identity": {
            "commit_sha": source_hash[:40],
            "blob_sha": source_hash[:40],
            "content_sha256": source_hash,
            "content_size_bytes": 10,
        },
        "source_resolved_at": "2026-09-21T00:00:00+00:00",
    }


def _create_revision(rt, document_id, actor, expected_version, source_hash, path):
    return rt.knowledge.create_revision(
        document_id,
        _payload(source_hash, path),
        actor,
        expected_artifact_version=expected_version,
    )["revision_id"]


def _execution(source_hash, *, validator="markdownlint-cli2", findings=None, status="SUCCEEDED", content_status=None):
    findings = findings or []
    if content_status is None:
        content_status = "FINDINGS" if findings else "PASS"
    return {
        "validator_id": validator,
        "validator_version": "test",
        "config_hash": "cfg",
        "subject_path": "docs/p5.md",
        "subject_hash": source_hash,
        "execution_status": status,
        "content_status": content_status,
        "findings": findings,
        "error_code": None if status == "SUCCEEDED" else "TEST_TOOL_FAILURE",
        "started_at": "2026-09-21T00:00:00+00:00",
        "finished_at": "2026-09-21T00:00:01+00:00",
    }


def _finding(*, message="heading failure", rule="MD001", finding_class=None, severity="ERROR", line=1, issue_key=None):
    out = {
        "rule_id": rule,
        "message": message,
        "severity": severity,
        "line": line,
        "column": 1,
    }
    if finding_class:
        out["finding_class"] = finding_class
    if issue_key:
        out["issue_key"] = issue_key
    return out


def _policy():
    return {"policy_id": "doc-qa", "policy_version": "1", "policy_hash": "policyhash"}


def _qa(rt, project, document_id, revision_id, qa_actor, source_hash, execution):
    return rt.document_qa.create_qa_record(
        project,
        document_id,
        revision_id,
        qa_actor,
        qa_policy_ref=_policy(),
        validator_executions=[execution],
    )


def test_d5_f1_qa_record_reuses_evidence(configured):
    rt, project, _, qa_actor, document_id, r1 = configured
    result = _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64))
    row = rt.db.one("SELECT * FROM evidence WHERE evidence_id=?", (result["qa_record_id"],))
    assert row["evidence_type"] == "document_qa_record"
    assert result["qa_record_id"] == row["evidence_id"]


def test_d5_f2_validator_execution_reuses_evidence(configured):
    rt, project, _, qa_actor, document_id, r1 = configured
    result = _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64))
    eid = result["validator_execution_refs"][0]
    row = rt.db.one("SELECT * FROM evidence WHERE evidence_id=?", (eid,))
    assert row["evidence_type"] == "document_validator_execution"


def test_d5_f3_zero_finding_pass(configured):
    rt, project, _, qa_actor, document_id, r1 = configured
    result = _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64))
    assert result["overall_status"] == "PASS"
    assert result["finding_refs"] == []


def test_d5_f4_one_qa_owns_multiple_findings(configured):
    rt, project, _, qa_actor, document_id, r1 = configured
    ex = _execution("a" * 64, findings=[_finding(rule="MD001"), _finding(rule="MD002", line=2)])
    result = _qa(rt, project, document_id, r1, qa_actor, "a" * 64, ex)
    findings = rt.document_qa.list_findings_by_qa(result["qa_record_id"])
    assert result["overall_status"] == "FAIL"
    assert len(findings) == 2
    assert {x["qa_record_id"] for x in findings} == {result["qa_record_id"]}


def test_d5_f5_exact_revision_binding_current(configured):
    rt, project, _, qa_actor, document_id, r1 = configured
    result = _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64))
    current = rt.document_qa.get_current_qa_status(document_id)
    assert current["qa_record_id"] == result["qa_record_id"]
    assert current["subject"]["exact_subject_id"] == r1


def test_d5_f6_prior_pass_does_not_transfer_to_new_revision(configured):
    rt, project, owner, qa_actor, document_id, r1 = configured
    _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64))
    r2 = _create_revision(rt, document_id, owner, 1, "b" * 64, "docs/p5.md")
    assert r2 != r1
    assert rt.document_qa.get_current_qa_status(document_id) is None
    assert len(rt.document_qa.list_qa_records_for_revision(r1)) == 1


def test_d5_f7_tool_failure_is_not_document_finding(configured):
    rt, project, _, qa_actor, document_id, r1 = configured
    ex = _execution("a" * 64, status="TOOL_ERROR", content_status="NOT_EVALUATED")
    result = _qa(rt, project, document_id, r1, qa_actor, "a" * 64, ex)
    assert result["overall_status"] == "NOT_EVALUATED"
    assert result["finding_refs"] == []
    assert rt.document_qa.list_findings_by_qa(result["qa_record_id"]) == []


def test_d5_f8_legal_resolution_lifecycle(configured):
    rt, project, owner, qa_actor, document_id, r1 = configured
    origin = _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64, findings=[_finding()]))
    fid = origin["finding_refs"][0]
    r2 = _create_revision(rt, document_id, owner, 1, "b" * 64, "docs/p5.md")
    pending = rt.document_qa.mark_resolved_pending_verify(fid, r2, qa_actor, expected_version=0)
    assert pending["status"] == "RESOLVED_PENDING_VERIFY"
    verify = _qa(rt, project, document_id, r2, qa_actor, "b" * 64, _execution("b" * 64))
    resolved = rt.document_qa.verify_resolved(fid, verify["qa_record_id"], qa_actor, expected_version=1)
    assert resolved["status"] == "VERIFIED_RESOLVED"


def test_d5_f9_direct_open_to_verified_resolved_rejected(configured):
    rt, project, _, qa_actor, document_id, r1 = configured
    origin = _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64, findings=[_finding()]))
    with pytest.raises(InvalidTransition):
        rt.document_qa.verify_resolved(origin["finding_refs"][0], origin["qa_record_id"], qa_actor, expected_version=0)


def test_d5_f10_stale_finding_version_fails_closed(configured):
    rt, project, owner, qa_actor, document_id, r1 = configured
    origin = _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64, findings=[_finding()]))
    fid = origin["finding_refs"][0]
    r2 = _create_revision(rt, document_id, owner, 1, "b" * 64, "docs/p5.md")
    rt.document_qa.mark_resolved_pending_verify(fid, r2, qa_actor, expected_version=0)
    with pytest.raises(StaleVersion):
        rt.document_qa.reopen_finding(fid, qa_actor, expected_version=0)


def test_d5_f11_resolution_qa_must_target_resolution_revision(configured):
    rt, project, owner, qa_actor, document_id, r1 = configured
    origin = _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64, findings=[_finding()]))
    fid = origin["finding_refs"][0]
    r2 = _create_revision(rt, document_id, owner, 1, "b" * 64, "docs/p5.md")
    rt.document_qa.mark_resolved_pending_verify(fid, r2, qa_actor, expected_version=0)
    r3 = _create_revision(rt, document_id, owner, 2, "c" * 64, "docs/p5.md")
    wrong = _qa(rt, project, document_id, r3, qa_actor, "c" * 64, _execution("c" * 64))
    with pytest.raises(ValidationError):
        rt.document_qa.verify_resolved(fid, wrong["qa_record_id"], qa_actor, expected_version=1)


def test_d5_f12_originating_qa_cannot_self_verify(configured):
    rt, project, owner, qa_actor, document_id, r1 = configured
    origin = _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64, findings=[_finding()]))
    fid = origin["finding_refs"][0]
    r2 = _create_revision(rt, document_id, owner, 1, "b" * 64, "docs/p5.md")
    rt.document_qa.mark_resolved_pending_verify(fid, r2, qa_actor, expected_version=0)
    with pytest.raises(ValidationError):
        rt.document_qa.verify_resolved(fid, origin["qa_record_id"], qa_actor, expected_version=1)


def test_d5_f13_fingerprint_ignores_description_wording(configured):
    rt, project, owner, qa_actor, document_id, r1 = configured
    origin = _qa(
        rt, project, document_id, r1, qa_actor, "a" * 64,
        _execution("a" * 64, findings=[_finding(message="old wording", issue_key="heading-one")]),
    )
    fid = origin["finding_refs"][0]
    original_fp = rt.document_qa.get_finding(fid)["fingerprint"]
    r2 = _create_revision(rt, document_id, owner, 1, "b" * 64, "docs/p5.md")
    rt.document_qa.mark_resolved_pending_verify(fid, r2, qa_actor, expected_version=0)
    repeated = _qa(
        rt, project, document_id, r2, qa_actor, "b" * 64,
        _execution("b" * 64, findings=[_finding(message="rewritten message", issue_key="heading-one")]),
    )
    repeated_fp = rt.document_qa.get_finding(repeated["finding_refs"][0])["fingerprint"]
    assert repeated_fp == original_fp
    with pytest.raises(ValidationError):
        rt.document_qa.verify_resolved(fid, repeated["qa_record_id"], qa_actor, expected_version=1)


def test_d5_f14_waiver_reuses_proposal_and_approval(configured):
    rt, project, owner, qa_actor, document_id, r1 = configured
    origin = _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64, findings=[_finding()]))
    fid = origin["finding_refs"][0]
    proposal = rt.document_qa.prepare_waiver(
        fid,
        qa_actor,
        expected_version=0,
        reason="accepted bounded exception",
        scope={"revision_id": r1},
        expiration_or_review_condition={"condition": "review on next revision"},
        required_approval_policy="normative_research_change",
    )
    p = rt.db.one("SELECT * FROM proposals WHERE proposal_id=?", (proposal,))
    approval = rt.governance.approve_proposal(proposal, owner, p["payload_hash"])
    waived = rt.document_qa.apply_approved_waiver(fid, proposal, qa_actor, expected_version=0)
    assert waived["status"] == "WAIVED"
    assert waived["waiver_ref"] == approval
    assert waived["waiver_effective"] is True


def test_d5_f15_non_waivable_class_rejects_waiver(configured):
    rt, project, _, qa_actor, document_id, r1 = configured
    ex = _execution(
        "a" * 64,
        validator="semantic",
        findings=[_finding(rule="SEC-1", finding_class="SECURITY_LEAK", severity="CRITICAL")],
    )
    origin = _qa(rt, project, document_id, r1, qa_actor, "a" * 64, ex)
    with pytest.raises(ValidationError):
        rt.document_qa.prepare_waiver(
            origin["finding_refs"][0],
            qa_actor,
            expected_version=0,
            reason="not allowed",
            scope={"revision_id": r1},
            expiration_or_review_condition={"condition": "never"},
            required_approval_policy="normative_research_change",
        )


def test_d5_f16_expired_waiver_is_not_effective_clean_state(configured):
    rt, project, owner, qa_actor, document_id, r1 = configured
    origin = _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64, findings=[_finding()]))
    fid = origin["finding_refs"][0]
    expired = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    proposal = rt.document_qa.prepare_waiver(
        fid,
        qa_actor,
        expected_version=0,
        reason="temporary exception",
        scope={"revision_id": r1},
        expiration_or_review_condition={"expires_at": expired},
        required_approval_policy="normative_research_change",
    )
    p = rt.db.one("SELECT * FROM proposals WHERE proposal_id=?", (proposal,))
    rt.governance.approve_proposal(proposal, owner, p["payload_hash"])
    waived = rt.document_qa.apply_approved_waiver(fid, proposal, qa_actor, expected_version=0)
    assert waived["status"] == "WAIVED"
    assert waived["waiver_effective"] is False
    assert [x["finding_id"] for x in rt.document_qa.list_active_findings_for_revision(r1)] == [fid]


def test_d5_f17_qa_creation_is_atomic_on_finding_failure(configured, monkeypatch):
    rt, project, _, qa_actor, document_id, r1 = configured
    before_evidence = rt.db.one("SELECT COUNT(*) n FROM evidence")["n"]
    before_findings = rt.db.one("SELECT COUNT(*) n FROM document_findings")["n"]
    before_audit = rt.db.one("SELECT COUNT(*) n FROM audit_events")["n"]

    def fail_insert(*args, **kwargs):
        raise RuntimeError("injected finding persistence failure")

    monkeypatch.setattr(rt.document_qa, "_insert_finding", fail_insert)
    with pytest.raises(RuntimeError):
        _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64, findings=[_finding()]))

    assert rt.db.one("SELECT COUNT(*) n FROM evidence")["n"] == before_evidence
    assert rt.db.one("SELECT COUNT(*) n FROM document_findings")["n"] == before_findings
    assert rt.db.one("SELECT COUNT(*) n FROM audit_events")["n"] == before_audit


def test_d5_f18_reserved_evidence_collision_rejected():
    data = yaml.safe_load(DOMAIN.read_text(encoding="utf-8"))
    data["evidence_types"].append(
        {"id": "document_qa_record", "maps_to": "PRIM-EVIDENCE", "trust_class": "SUPPORTED"}
    )
    with pytest.raises(ValidationError):
        validate_domain(data)


def test_d5_f19_existing_add_evidence_behavior_preserved(configured):
    rt, project, _, qa_actor, *_ = configured
    eid = rt.execution.add_evidence(
        project,
        "goal_review_evidence",
        qa_actor,
        [{"scope": "regression"}],
        {"pass": True, "checks": {"legacy": True}},
        trust_class="SUPPORTED",
    )
    row = rt.db.one("SELECT * FROM evidence WHERE evidence_id=?", (eid,))
    assert row is not None
    assert row["evidence_type"] == "goal_review_evidence"


def test_d5_f20_no_later_wave_state_mutation(configured):
    rt, project, _, qa_actor, document_id, r1 = configured
    _qa(rt, project, document_id, r1, qa_actor, "a" * 64, _execution("a" * 64))
    revision = rt.knowledge.get_revision(r1)
    assert revision["validity_state"] == "UNVERIFIED"
    assert rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"] == 0
    assert rt.db.one("SELECT COUNT(*) n FROM gates WHERE project_id=?", (project,))["n"] == 0
    assert "document_findings" in rt.db.list_tables()
    assert "document_qa_records" not in rt.db.list_tables()
    assert "document_validator_executions" not in rt.db.list_tables()
