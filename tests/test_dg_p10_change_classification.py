from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from gwr.document_change import CHANGE_CLASSES, CHANGE_RANK, normalize_document_governance
from gwr.errors import InvalidTransition, StaleVersion, ValidationError
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import uid

ROOT = Path(__file__).parents[1]


def make_runtime(tmp_path):
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "research.workflow.yaml"),
        str(tmp_path / "p10.db"),
    )
    human = rt.governance.create_actor("HUMAN", "p10-owner", ["human_approver"], [])
    tenant = rt.tenancy.create_tenant("p10 tenant", human)
    workspace = rt.tenancy.create_workspace(tenant, "p10 workspace", human)
    project = rt.create_scoped_project("p10 project", tenant, workspace, human)
    agent = rt.governance.create_actor("AGENT", "p10-agent", ["research_lead"], [])
    rt.tenancy.add_project_member(project, agent, "RESEARCHER", human)
    return rt, project, human, agent


def add_phase(rt, project, actor, mode="AUTO", phase_id="phase_09_main_experiment"):
    oid = uid("orch")
    peid = uid("phaseexec")
    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (oid, project, rt.domain.domain_id, "RUNNING", phase_id, 0, None, 0,
         "2026-09-22T00:00:00+00:00", "2026-09-22T00:00:00+00:00", None, "{}"),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (peid, oid, phase_id, 9, 0, None, None, "RUNNING", None, None, None,
         "2026-09-22T00:00:00+00:00", None, "{}"),
    )
    rt.db.conn.commit()
    pkg = rt.agent_protocol.create_skill_package(f"p10-{peid}", "P10 test skill", actor)
    skill = rt.agent_protocol.add_skill_revision(pkg, "1", "# P10", actor)
    rt.agent_protocol.create_protocol(peid, skill, actor, recovery_mode=mode, retry_budget=2)
    return peid


def make_doc(rt, project, actor, *, role="PHASE", state="MUTABLE",
             owner="phase_09_main_experiment", version=1, stem="protocol"):
    folder = "gov" if role == "GOV" else "phase_09_main_experiment"
    path = f"docs/{folder}/{stem}.v{version}.md"
    gov = {
        "document_role": role,
        "governance_state": state,
        "owner_phase_id_or_workunit_type": owner,
        "document_version": version,
        "previous_revision_id": None if version == 1 else "rev-old",
        "previous_archive_path": None if version == 1 else f"docs/{folder}/archive/{stem}.v{version-1}.md",
    }
    aid = rt.knowledge.create_artifact(project, "governed_document", f"gwr:document:{stem}-{uid('k')}", actor)
    payload = {
        "schema": "DG-P4-DOCUMENT-REVISION-v1",
        "document_key": stem,
        "title": stem,
        "storage_locator": {
            "provider": "github",
            "repository_id": 1374857546,
            "repository_full_name_at_resolution": "example/project",
            "path": path,
        },
        "source_identity": {
            "commit_sha": "a" * 40,
            "blob_sha": "b" * 40,
            "content_sha256": "c" * 64,
            "content_size_bytes": 10,
        },
        "source_resolved_at": "2026-09-22T00:00:00+00:00",
        "document_governance": gov,
    }
    rid = rt.knowledge.create_revision(aid, payload, actor, 0)["revision_id"]
    return aid, rid, path


def qa_ref(rt, project, actor, status="PASS"):
    return rt.execution.add_evidence(
        project, "document_qa_record", actor,
        {"kind": "DG-P10-SEMANTIC-REVIEW"},
        {"overall_status": status, "policy": "p10-test"},
    )


def proposal(path, text="# v2\n\n[Previous version](archive/protocol.v1.md)\n"):
    return path.replace(".v1.md", ".v2.md"), text


def classify(rt, project, actor, doc, path, phase, **kw):
    proposed_path, content = proposal(path, kw.pop("content", "# v2\n\n[Previous version](archive/protocol.v1.md)\n"))
    review = kw.pop("review", qa_ref(rt, project, actor))
    return rt.document_changes.classify(
        doc, actor,
        expected_artifact_version=kw.pop("expected_artifact_version", 1),
        proposed_active_path=kw.pop("proposed_active_path", proposed_path),
        proposed_content=content,
        declared_change_class=kw.pop("declared_change_class", "EDITORIAL"),
        declared_triggers=kw.pop("declared_triggers", []),
        qa_status=kw.pop("qa_status", "EVALUATED"),
        qa_review_refs=kw.pop("qa_review_refs", [review] if review else []),
        qa_escalation_classes=kw.pop("qa_escalation_classes", []),
        ambiguity_status=kw.pop("ambiguity_status", "CLEAR"),
        phase_execution_id=kw.pop("phase_execution_id", phase),
        **kw,
    )


def test_d10_f1_exact_class_vocabulary(tmp_path):
    assert CHANGE_CLASSES == ("EDITORIAL", "CLARIFICATION", "NORMATIVE", "STRUCTURAL", "SUPERSESSION")
    rt, project, _, agent = make_runtime(tmp_path)
    doc, _, path = make_doc(rt, project, agent)
    phase = add_phase(rt, project, agent)
    with pytest.raises(ValidationError):
        classify(rt, project, agent, doc, path, phase, declared_change_class="COSMETIC")
    rt.close()


def test_d10_f2_governance_rank_is_deterministic():
    assert CHANGE_RANK == {"EDITORIAL": 0, "CLARIFICATION": 1, "NORMATIVE": 2, "STRUCTURAL": 3, "SUPERSESSION": 4}


def test_d10_f3_no_implicit_declaration(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, _, path = make_doc(rt, project, agent)
    phase = add_phase(rt, project, agent)
    with pytest.raises(ValidationError):
        classify(rt, project, agent, doc, path, phase, declared_change_class="")
    rt.close()


def test_d10_f4_editorial_clean_case(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, _, path = make_doc(rt, project, agent); phase = add_phase(rt, project, agent)
    result = classify(rt, project, agent, doc, path, phase)
    assert result["effective_change_class"] == "EDITORIAL"
    assert result["mutation_authority_decision"] == "ALLOW_AUTO"
    rt.close()


def test_d10_f5_clarification_clean_case(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, _, path = make_doc(rt, project, agent); phase = add_phase(rt, project, agent)
    result = classify(rt, project, agent, doc, path, phase, declared_change_class="CLARIFICATION")
    assert result["effective_change_class"] == "CLARIFICATION"
    rt.close()


def test_d10_f6_clarification_ambiguity_escalates(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, _, path = make_doc(rt, project, agent); phase = add_phase(rt, project, agent)
    result = classify(rt, project, agent, doc, path, phase, declared_change_class="CLARIFICATION", ambiguity_status="UNRESOLVED")
    assert result["effective_change_class"] == "NORMATIVE"
    rt.close()


def test_d10_f7_normative_trigger_escalation(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, _, path = make_doc(rt, project, agent); phase = add_phase(rt, project, agent)
    result = classify(rt, project, agent, doc, path, phase, declared_triggers=["THRESHOLD_CHANGE"])
    assert result["effective_change_class"] == "NORMATIVE"
    rt.close()


def test_d10_f8_structural_trigger_escalation(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, _, path = make_doc(rt, project, agent); phase = add_phase(rt, project, agent)
    result = classify(rt, project, agent, doc, path, phase, declared_triggers=["RELATION_TOPOLOGY_CHANGE"])
    assert result["effective_change_class"] == "STRUCTURAL"
    rt.close()


def test_d10_f9_supersession_trigger_escalation(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, _, path = make_doc(rt, project, agent); phase = add_phase(rt, project, agent)
    result = classify(rt, project, agent, doc, path, phase, declared_triggers=["AUTHORITY_REPLACEMENT"])
    assert result["effective_change_class"] == "SUPERSESSION"
    rt.close()


def test_d10_f10_diff_size_cannot_downgrade(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, _, path = make_doc(rt, project, agent); phase = add_phase(rt, project, agent)
    tiny = "[Previous version](archive/protocol.v1.md)"
    result = classify(rt, project, agent, doc, path, phase, content=tiny, declared_change_class="EDITORIAL", declared_triggers=["INVARIANT_CHANGE"])
    assert result["effective_change_class"] == "NORMATIVE"
    rt.close()


def test_d10_f11_qa_escalation_is_monotonic(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, _, path = make_doc(rt, project, agent); phase = add_phase(rt, project, agent)
    result = classify(rt, project, agent, doc, path, phase, qa_escalation_classes=["STRUCTURAL"])
    assert result["effective_change_class"] == "STRUCTURAL"
    rt.close()


def test_d10_f12_agent_cannot_counteract_qa_escalation(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, _, path = make_doc(rt, project, agent); phase = add_phase(rt, project, agent)
    result = classify(rt, project, agent, doc, path, phase, declared_change_class="EDITORIAL", qa_escalation_classes=["SUPERSESSION"])
    assert result["effective_change_class"] == "SUPERSESSION"
    rt.close()


def test_d10_f13_exact_base_required(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, _, path = make_doc(rt, project, agent); phase = add_phase(rt, project, agent)
    with pytest.raises(StaleVersion):
        classify(rt, project, agent, doc, path, phase, expected_artifact_version=0)
    rt.close()


def test_d10_f14_precommit_candidate_digest_and_path_are_frozen(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, _, path = make_doc(rt, project, agent); phase = add_phase(rt, project, agent)
    result = classify(rt, project, agent, doc, path, phase)
    plan = result["lineage_plan"]
    assert plan["proposed_content_sha256"] == hashlib.sha256("# v2\n\n[Previous version](archive/protocol.v1.md)\n".encode()).hexdigest()
    with pytest.raises(ValidationError):
        classify(rt, project, agent, doc, path, phase, proposed_active_path="docs/phase_09_main_experiment/protocol.v3.md")
    rt.close()


def test_d10_f15_not_evaluated_blocks_without_revision_side_effect(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, rid, path = make_doc(rt, project, agent); phase = add_phase(rt, project, agent)
    result = classify(rt, project, agent, doc, path, phase, qa_status="NOT_EVALUATED", review=None, qa_review_refs=[])
    assert result["mutation_authority_decision"] == "BLOCK_NOT_EVALUATED"
    assert rt.knowledge.get_artifact(doc)["current_revision_id"] == rid
    assert rt.knowledge.get_artifact(doc)["version"] == 1
    rt.close()


def test_d10_f16_workflow_mode_authority_is_orthogonal_to_class(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    auto_doc, _, auto_path = make_doc(rt, project, agent)
    auto_phase = add_phase(rt, project, agent, "AUTO")
    auto = classify(rt, project, agent, auto_doc, auto_path, auto_phase, declared_triggers=["PROTOCOL_CHANGE"])
    assert auto["effective_change_class"] == "NORMATIVE"
    assert auto["mutation_authority_decision"] == "ALLOW_AUTO"

    manual_doc, _, manual_path = make_doc(rt, project, agent, stem="manual")
    manual_phase = add_phase(rt, project, agent, "HUMAN_APPROVE")
    manual_content = "# v2\n\n[Previous version](archive/manual.v1.md)\n"
    manual = classify(rt, project, agent, manual_doc, manual_path, manual_phase, content=manual_content, declared_change_class="EDITORIAL")
    assert manual["mutation_authority_decision"] == "REQUIRE_HUMAN_APPROVAL"
    rt.close()


def test_d10_f17_evidence_reuse_and_no_table(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, _, path = make_doc(rt, project, agent); phase = add_phase(rt, project, agent)
    result = classify(rt, project, agent, doc, path, phase)
    row = rt.db.one("SELECT evidence_type FROM evidence WHERE evidence_id=?", (result["classification_evidence_id"],))
    assert row["evidence_type"] == "document_change_classification"
    assert "document_change_classifications" not in rt.db.list_tables()
    rt.close()


def test_d10_f18_deterministic_version_archive_lineage(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, _, path = make_doc(rt, project, agent); phase = add_phase(rt, project, agent)
    result = classify(rt, project, agent, doc, path, phase)
    assert result["lineage_plan"] == {
        "current_active_path": "docs/phase_09_main_experiment/protocol.v1.md",
        "current_document_version": 1,
        "next_active_path": "docs/phase_09_main_experiment/protocol.v2.md",
        "next_document_version": 2,
        "expected_archive_path": "docs/phase_09_main_experiment/archive/protocol.v1.md",
        "previous_version_link": "archive/protocol.v1.md",
        "proposed_content_sha256": hashlib.sha256("# v2\n\n[Previous version](archive/protocol.v1.md)\n".encode()).hexdigest(),
    }
    with pytest.raises(ValidationError):
        classify(rt, project, agent, doc, path, phase, content="# v2 without lineage link")
    rt.close()


def test_d10_f19_gov_frozen_blocks_even_under_auto_and_has_no_side_effect(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, rid, path = make_doc(rt, project, agent, role="GOV", state="FROZEN", stem="governance")
    phase = add_phase(rt, project, agent, "AUTO")
    content = "# gov v2\n\n[Previous version](archive/governance.v1.md)\n"
    before_rel = rt.db.one("SELECT COUNT(*) n FROM document_relations WHERE project_id=?", (project,))["n"]
    result = classify(rt, project, agent, doc, path, phase, content=content)
    assert result["mutation_authority_decision"] == "BLOCK_REQUIRES_EXPLICIT_USER_AUTHORIZATION"
    assert rt.knowledge.get_artifact(doc)["current_revision_id"] == rid
    assert rt.db.one("SELECT COUNT(*) n FROM document_relations WHERE project_id=?", (project,))["n"] == before_rel
    rt.close()


def test_d10_f20_no_dg_p11_or_source_mutation_side_effects(tmp_path):
    rt, project, _, agent = make_runtime(tmp_path)
    doc, rid, path = make_doc(rt, project, agent); phase = add_phase(rt, project, agent)
    before = {
        "gh": rt.db.one("SELECT COUNT(*) n FROM github_change_sets WHERE project_id=?", (project,))["n"],
        "trace": rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"],
        "impact": rt.db.one("SELECT COUNT(*) n FROM impacts WHERE project_id=?", (project,))["n"],
    }
    classify(rt, project, agent, doc, path, phase)
    assert rt.knowledge.get_artifact(doc)["current_revision_id"] == rid
    assert rt.db.one("SELECT COUNT(*) n FROM github_change_sets WHERE project_id=?", (project,))["n"] == before["gh"]
    assert rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"] == before["trace"]
    assert rt.db.one("SELECT COUNT(*) n FROM impacts WHERE project_id=?", (project,))["n"] == before["impact"]
    rt.close()


def test_enrolled_document_metadata_path_consistency_and_direct_revision_bypass_blocked(tmp_path):
    assert normalize_document_governance({
        "document_role": "GOV", "governance_state": "FROZEN",
        "owner_phase_id_or_workunit_type": "phase_gov", "document_version": 1,
    }, "docs/gov/control.v1.md")["document_role"] == "GOV"
    with pytest.raises(ValidationError):
        normalize_document_governance({
            "document_role": "PHASE", "governance_state": "MUTABLE",
            "owner_phase_id_or_workunit_type": "x", "document_version": 1,
        }, "docs/gov/control.v1.md")



def test_p10_enrollment_registration_api_binds_metadata_without_breaking_p4_path():
    from gwr.document_facade import DocumentFacadeService

    class FakeKnowledge:
        def __init__(self):
            self.payload = None
        def create_artifact(self, project_id, artifact_type, logical_key, actor_id):
            assert artifact_type == "governed_document"
            return "art-doc"
        def create_revision(self, document_id, payload, actor_id, expected_artifact_version):
            self.payload = payload
            return {"revision_id": "rev-doc"}

    class FakeGithub:
        def resolve_blob_revision(self, *args, **kwargs):
            return {
                "provider": "github",
                "repository_id": 1374857546,
                "repository_full_name_at_resolution": "example/project",
                "path_locator": "docs/gov/control.v1.md",
                "resolved_commit_sha": "a" * 40,
                "blob_sha": "b" * 40,
                "content_sha256": "c" * 64,
                "content_size_bytes": 12,
                "resolved_at": "2026-09-22T00:00:00+00:00",
            }

    knowledge = FakeKnowledge()
    svc = DocumentFacadeService(knowledge, FakeGithub())
    result = svc.register_document(
        "project-1",
        "binding-1",
        "actor-1",
        document_key="control",
        title="Control",
        ref_kind="COMMIT",
        ref_value="a" * 40,
        path="docs/gov/control.v1.md",
        expected_repository_id=1374857546,
        expected_commit_sha="a" * 40,
        expected_blob_sha="b" * 40,
        document_governance={
            "document_role": "GOV",
            "governance_state": "FROZEN",
            "owner_phase_id_or_workunit_type": "phase_governance",
            "document_version": 1,
        },
    )
    assert result["document_id"] == "art-doc"
    assert knowledge.payload["document_governance"] == {
        "document_role": "GOV",
        "governance_state": "FROZEN",
        "owner_phase_id_or_workunit_type": "phase_governance",
        "document_version": 1,
        "phase_id": None,
        "previous_revision_id": None,
        "previous_archive_path": None,
    }
