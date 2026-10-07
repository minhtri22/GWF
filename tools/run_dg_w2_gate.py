from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from gwr.knowledge import VALIDITY
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VALIDITY = {"VALID", "STALE", "DIRTY", "FAILED", "UNVERIFIED", "SUPERSEDED"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def payload(key: str, source_hash: str, path: str) -> dict:
    return {
        "schema": "DG-P4-DOCUMENT-REVISION-v1",
        "document_key": key,
        "title": f"Wave 2 {key}",
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
            "content_size_bytes": 1,
        },
        "source_resolved_at": "2026-09-21T00:00:00+00:00",
    }


def qa_execution(source_hash: str, findings=None) -> dict:
    findings = findings or []
    return {
        "validator_id": "markdownlint-cli2",
        "validator_version": "0.23.3",
        "config_hash": "wave2-locked",
        "subject_hash": source_hash,
        "execution_status": "SUCCEEDED",
        "content_status": "FINDINGS" if findings else "PASS",
        "findings": findings,
        "started_at": "2026-09-21T00:00:00+00:00",
        "finished_at": "2026-09-21T00:00:01+00:00",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", required=True)
    ap.add_argument("--p4", required=True)
    ap.add_argument("--p5", required=True)
    ap.add_argument("--p6", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    p4 = read_json(Path(args.p4))
    p5 = read_json(Path(args.p5))
    p6 = read_json(Path(args.p6))

    with tempfile.TemporaryDirectory(prefix="gwr-dg-w2-") as td:
        rt = GovernedWorkflowRuntime(
            str(ROOT / "domains" / "research.workflow.yaml"),
            str(Path(td) / "w2.db"),
        )
        owner = rt.governance.create_actor("HUMAN", "dg-w2-owner", ["human_approver"], [])
        tenant = rt.tenancy.create_tenant("dg-w2 tenant", owner)
        workspace = rt.tenancy.create_workspace(tenant, "dg-w2 workspace", owner)
        project = rt.create_scoped_project("dg-w2 project", tenant, workspace, owner)
        qa_actor = rt.governance.create_actor("AGENT", "dg-w2-qa", ["research_lead"], [])
        rt.tenancy.add_project_member(project, qa_actor, "RESEARCHER", owner)

        document_id = rt.knowledge.create_artifact(
            project,
            "governed_document",
            "gwr:document:dg-w2-cross-wave",
            owner,
            lifecycle_status="ACTIVE",
        )
        r1_hash = "1" * 64
        r1 = rt.knowledge.create_revision(
            document_id,
            payload("dg-w2-cross-wave", r1_hash, "docs/w2-r1.md"),
            owner,
            expected_artifact_version=0,
        )["revision_id"]

        qa1 = rt.document_qa.create_qa_record(
            project,
            document_id,
            r1,
            qa_actor,
            qa_policy_ref={"policy_id": "dg-w2", "policy_version": "1", "policy_hash": "locked"},
            validator_executions=[qa_execution(r1_hash)],
        )
        valid_r1 = rt.document_state.reconcile_document_validity(document_id)

        art_after_r1 = rt.knowledge.get_artifact(document_id)
        r2_hash = "2" * 64
        r2 = rt.knowledge.create_revision(
            document_id,
            payload("dg-w2-cross-wave", r2_hash, "docs/w2-r2-renamed.md"),
            owner,
            expected_artifact_version=art_after_r1["version"],
        )["revision_id"]

        current_before_qa2 = rt.document_state.inspect_document_state(document_id)
        current_qa_before_qa2 = rt.document_qa.get_current_qa_status(document_id)

        finding = {
            "finding_class": "STRUCTURAL_ERROR",
            "rule_id": "W2-XREV",
            "message": "wave-2 integrated blocker",
            "severity": "ERROR",
            "line": 1,
            "column": 1,
            "issue_key": "W2-XREV",
        }
        qa2 = rt.document_qa.create_qa_record(
            project,
            document_id,
            r2,
            qa_actor,
            qa_policy_ref={"policy_id": "dg-w2", "policy_version": "1", "policy_hash": "locked"},
            validator_executions=[qa_execution(r2_hash, [finding])],
        )
        blocked_r2 = rt.document_state.reconcile_document_validity(document_id)
        facade = rt.documents.get_document(document_id)

        tables = set(rt.db.list_tables())
        migrations = rt.db.migrations.status()["applied"]
        forbidden_parallel_tables = {
            "document_records",
            "document_revisions",
            "document_qa_records",
            "document_validator_executions",
            "document_validity",
            "document_lifecycle",
            "document_state",
            "document_waivers",
            "document_authority_claims",
            "document_relations",
            "document_change_sets",
            "catalog_entries",
        }
        unexpected_document_tables = sorted((tables & forbidden_parallel_tables))
        dg_p4_migrations = [m for m in migrations if "dg_p4" in m.lower()]
        dg_p5_migrations = [m for m in migrations if "dg_p5" in m.lower()]
        dg_p6_migrations = [m for m in migrations if "dg_p6" in m.lower()]

        checks = {
            "p4_component_pass": p4.get("status") == "PASS",
            "p5_component_pass": p5.get("status") == "PASS",
            "p6_component_pass": p6.get("status") == "PASS",
            "p4_bound_to_exact_wave2_head": p4.get("commit") == args.commit,
            "p4_repository_identity_bound": str(p4.get("repository_id")) == "1374857546",
            "r1_qa_pass": qa1["overall_status"] == "PASS",
            "r1_reconciles_valid": valid_r1["kernel_validity_state"] == "VALID" and valid_r1["effective_validity_state"] == "VALID",
            "new_revision_identity_distinct": r2 != r1,
            "old_revision_superseded": (
                rt.knowledge.get_revision(r1)["status"] == "SUPERSEDED"
                and rt.knowledge.get_revision(r1)["validity_state"] == "SUPERSEDED"
            ),
            "r2_begins_unverified": rt.knowledge.get_revision(r2)["validity_state"] == "UNVERIFIED",
            "prior_qa_not_current_for_r2": current_qa_before_qa2 is None,
            "r2_effective_unverified_before_new_qa": current_before_qa2["effective_validity_state"] == "UNVERIFIED",
            "document_identity_stable_across_revision": facade["document_id"] == document_id,
            "logical_key_stable_across_path_change": rt.knowledge.get_artifact(document_id)["logical_key"] == "gwr:document:dg-w2-cross-wave",
            "r2_fail_qa_recorded": qa2["overall_status"] == "FAIL" and len(qa2["finding_refs"]) == 1,
            "r2_effective_blocked": blocked_r2["effective_validity_state"] == "BLOCKED",
            "r2_kernel_non_valid": blocked_r2["kernel_validity_state"] != "VALID",
            "blocked_not_global_validity": "BLOCKED" not in VALIDITY,
            "global_validity_exact": VALIDITY == EXPECTED_VALIDITY,
            "p4_has_no_migration": dg_p4_migrations == [],
            "p5_has_exactly_one_bounded_migration": dg_p5_migrations == ["0008_v086_dg_p5_document_findings"],
            "p6_has_no_migration": dg_p6_migrations == [],
            "document_findings_is_only_document_specific_table": "document_findings" in tables and unexpected_document_tables == [],
            "qa_records_reuse_evidence": rt.db.one(
                "SELECT evidence_type FROM evidence WHERE evidence_id=?", (qa2["qa_record_id"],)
            )["evidence_type"] == "document_qa_record",
            "no_wave3_authority_or_relation_state_created": (
                rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"] == 0
            ),
            "finding_ledger_open_zero": "**OPEN = 0**" in (ROOT / "docs/Finding_checklist.md").read_text(encoding="utf-8"),
        }

        result = {
            "schema": "DG-W2-QA-v1",
            "status": "PASS" if all(checks.values()) else "FAIL",
            "commit": args.commit,
            "component_status": {
                "DG-P4": p4.get("status"),
                "DG-P5": p5.get("status"),
                "DG-P6": p6.get("status"),
            },
            "checks": checks,
            "schema_state": {
                "applied_migrations": migrations,
                "document_specific_tables": sorted(t for t in tables if t.startswith("document_")),
                "unexpected_parallel_tables": unexpected_document_tables,
            },
            "cross_wave_identity": {
                "document_id": document_id,
                "r1": r1,
                "r1_qa": qa1["qa_record_id"],
                "r2": r2,
                "r2_qa": qa2["qa_record_id"],
                "r2_finding": qa2["finding_refs"][0],
            },
        }
        rt.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
