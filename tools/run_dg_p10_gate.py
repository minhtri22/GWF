from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import uid

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="gwr-dg-p10-") as td:
        rt = GovernedWorkflowRuntime(
            str(ROOT / "domains" / "research.workflow.yaml"),
            str(Path(td) / "p10.db"),
        )
        human = rt.governance.create_actor("HUMAN", "p10-gate-owner", ["human_approver"], [])
        tenant = rt.tenancy.create_tenant("p10 gate tenant", human)
        workspace = rt.tenancy.create_workspace(tenant, "p10 gate workspace", human)
        project = rt.create_scoped_project("p10 gate project", tenant, workspace, human)
        agent = rt.governance.create_actor("AGENT", "p10-gate-agent", ["research_lead"], [])
        rt.tenancy.add_project_member(project, agent, "RESEARCHER", human)

        oid, peid = uid("orch"), uid("phaseexec")
        phase_id = "phase_09_main_experiment"
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
        pkg = rt.agent_protocol.create_skill_package("p10-gate-skill", "P10 gate", agent)
        skill = rt.agent_protocol.add_skill_revision(pkg, "1", "# P10 gate", agent)
        rt.agent_protocol.create_protocol(peid, skill, agent, recovery_mode="AUTO", retry_budget=2)

        document = rt.knowledge.create_artifact(project, "governed_document", "gwr:document:p10-gate", agent)
        base = rt.knowledge.create_revision(
            document,
            {
                "schema": "DG-P4-DOCUMENT-REVISION-v1",
                "document_key": "p10-gate",
                "title": "P10 Gate",
                "storage_locator": {
                    "provider": "github", "repository_id": 1374857546,
                    "repository_full_name_at_resolution": "example/project",
                    "path": "docs/phase_09_main_experiment/p10-gate.v1.md",
                },
                "source_identity": {
                    "commit_sha": "a" * 40, "blob_sha": "b" * 40,
                    "content_sha256": "c" * 64, "content_size_bytes": 1,
                },
                "source_resolved_at": "2026-09-22T00:00:00+00:00",
                "document_governance": {
                    "document_role": "PHASE", "governance_state": "MUTABLE",
                    "owner_phase_id_or_workunit_type": phase_id, "document_version": 1,
                    "previous_revision_id": None, "previous_archive_path": None,
                },
            },
            agent, 0,
        )["revision_id"]
        qa = rt.execution.add_evidence(
            project, "document_qa_record", agent,
            {"kind": "DG-P10-GATE"}, {"overall_status": "PASS"},
        )
        result = rt.document_changes.classify(
            document, agent,
            expected_artifact_version=1,
            proposed_active_path="docs/phase_09_main_experiment/p10-gate.v2.md",
            proposed_content="# P10 v2\n\n[Previous version](archive/p10-gate.v1.md)\n",
            declared_change_class="NORMATIVE",
            declared_triggers=["PROTOCOL_CHANGE"],
            qa_status="EVALUATED",
            qa_review_refs=[qa],
            phase_execution_id=peid,
        )
        evidence = rt.db.one(
            "SELECT evidence_type FROM evidence WHERE evidence_id=?",
            (result["classification_evidence_id"],),
        )
        checks = {
            "classification_evidence": evidence["evidence_type"] == "document_change_classification",
            "normative_auto_allowed": result["effective_change_class"] == "NORMATIVE" and result["mutation_authority_decision"] == "ALLOW_AUTO",
            "mode_snapshot_auto": result["workflow_mutation_mode"] == "AUTO",
            "archive_plan_exact": result["lineage_plan"]["expected_archive_path"] == "docs/phase_09_main_experiment/archive/p10-gate.v1.md",
            "next_version_exact": result["lineage_plan"]["next_document_version"] == 2,
            "no_revision_side_effect": rt.knowledge.get_artifact(document)["current_revision_id"] == base,
            "no_p10_table": "document_change_classifications" not in rt.db.list_tables(),
            "no_dg_p11_changeset": rt.db.one("SELECT COUNT(*) n FROM github_change_sets WHERE project_id=?", (project,))["n"] == 0,
        }
        output = {
            "schema": "DG-P10-GATE-v1",
            "status": "PASS" if all(checks.values()) else "FAIL",
            "backend": rt.db.backend_name,
            "checks": checks,
            "classification_evidence_id": result["classification_evidence_id"],
            "decision": result["mutation_authority_decision"],
            "lineage_plan": result["lineage_plan"],
        }
        rt.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if output["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
