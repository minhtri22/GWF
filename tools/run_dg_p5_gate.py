from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="gwr-dg-p5-") as td:
        rt = GovernedWorkflowRuntime(
            str(ROOT / "domains" / "research.workflow.yaml"),
            str(Path(td) / "p5.db"),
        )
        owner = rt.governance.create_actor("HUMAN", "dg-p5-owner", ["human_approver"], [])
        tenant = rt.tenancy.create_tenant("dg-p5 tenant", owner)
        workspace = rt.tenancy.create_workspace(tenant, "dg-p5 workspace", owner)
        project = rt.create_scoped_project("dg-p5 project", tenant, workspace, owner)
        qa_actor = rt.governance.create_actor("AGENT", "dg-p5-qa", ["research_lead"], [])
        rt.tenancy.add_project_member(project, qa_actor, "RESEARCHER", owner)

        document_id = rt.knowledge.create_artifact(
            project, "governed_document", "gwr:document:dg-p5-gate", owner
        )
        source_hash = "d" * 64
        revision_id = rt.knowledge.create_revision(
            document_id,
            {
                "schema": "DG-P4-DOCUMENT-REVISION-v1",
                "document_key": "dg-p5-gate",
                "title": "DG-P5 gate",
                "storage_locator": {
                    "provider": "github",
                    "repository_id": 1374857546,
                    "repository_full_name_at_resolution": "minhtri22/GWF",
                    "path": "docs/DG_P5_QA_FINDING_PERSISTENCE_SPEC.md",
                },
                "source_identity": {
                    "commit_sha": "d" * 40,
                    "blob_sha": "d" * 40,
                    "content_sha256": source_hash,
                    "content_size_bytes": 1,
                },
                "source_resolved_at": "2026-09-21T00:00:00+00:00",
            },
            owner,
            expected_artifact_version=0,
        )["revision_id"]

        qa = rt.document_qa.create_qa_record(
            project,
            document_id,
            revision_id,
            qa_actor,
            qa_policy_ref={"policy_id": "dg-p5-gate", "policy_version": "1", "policy_hash": "locked"},
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

        tables = set(rt.db.list_tables())
        qa_row = rt.db.one("SELECT * FROM evidence WHERE evidence_id=?", (qa["qa_record_id"],))
        checks = {
            "document_findings_table_present": "document_findings" in tables,
            "no_document_qa_records_table": "document_qa_records" not in tables,
            "no_validator_execution_table": "document_validator_executions" not in tables,
            "qa_record_is_evidence": qa_row is not None and qa_row["evidence_type"] == "document_qa_record",
            "clean_qa_pass": qa["overall_status"] == "PASS" and qa["finding_refs"] == [],
            "revision_remains_unverified": rt.knowledge.get_revision(revision_id)["validity_state"] == "UNVERIFIED",
            "no_gate_side_effect": rt.db.one("SELECT COUNT(*) n FROM gates WHERE project_id=?", (project,))["n"] == 0,
            "no_relation_side_effect": rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"] == 0,
        }
        result = {
            "schema": "DG-P5-GATE-v1",
            "status": "PASS" if all(checks.values()) else "FAIL",
            "migration_ids": rt.db.migrations.status()["applied"],
            "checks": checks,
        }
        rt.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
