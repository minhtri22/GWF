from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from gwr.knowledge import VALIDITY
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VALIDITY = ["DIRTY", "FAILED", "STALE", "SUPERSEDED", "UNVERIFIED", "VALID"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="gwr-dg-p6-") as td:
        rt = GovernedWorkflowRuntime(
            str(ROOT / "domains" / "research.workflow.yaml"),
            str(Path(td) / "p6.db"),
        )
        owner = rt.governance.create_actor("HUMAN", "dg-p6-owner", ["human_approver"], [])
        tenant = rt.tenancy.create_tenant("dg-p6 tenant", owner)
        workspace = rt.tenancy.create_workspace(tenant, "dg-p6 workspace", owner)
        project = rt.create_scoped_project("dg-p6 project", tenant, workspace, owner)

        document_id = rt.knowledge.create_artifact(
            project,
            "governed_document",
            "gwr:document:dg-p6-gate",
            owner,
            lifecycle_status="ACTIVE",
        )
        source_hash = "f" * 64
        revision_id = rt.knowledge.create_revision(
            document_id,
            {
                "schema": "DG-P4-DOCUMENT-REVISION-v1",
                "document_key": "dg-p6-gate",
                "title": "DG-P6 gate",
                "storage_locator": {
                    "provider": "github",
                    "repository_id": 1374857546,
                    "repository_full_name_at_resolution": "minhtri22/GWF",
                    "path": "docs/DG_P6_LIFECYCLE_VALIDITY_MAPPING_SPEC.md",
                },
                "source_identity": {
                    "commit_sha": "f" * 40,
                    "blob_sha": "f" * 40,
                    "content_sha256": source_hash,
                    "content_size_bytes": 1,
                },
                "source_resolved_at": "2026-09-21T00:00:00+00:00",
            },
            owner,
            expected_artifact_version=0,
        )["revision_id"]

        inspected = rt.document_state.inspect_document_state(document_id)
        facade = rt.documents.get_document(document_id)
        tables = set(rt.db.list_tables())
        checks = {
            "global_validity_exact": sorted(VALIDITY) == EXPECTED_VALIDITY,
            "blocked_not_global_validity": "BLOCKED" not in VALIDITY,
            "no_p6_migration": not any("dg_p6" in x.lower() for x in rt.db.migrations.status()["known"]),
            "no_document_state_table": not ({"document_lifecycle", "document_validity", "document_state"} & tables),
            "new_revision_unverified": rt.knowledge.get_revision(revision_id)["validity_state"] == "UNVERIFIED",
            "active_unverified_separate": inspected["lifecycle_state"] == "ACTIVE" and inspected["effective_validity_state"] == "UNVERIFIED",
            "facade_exposes_lifecycle": facade["lifecycle_state"] == "ACTIVE",
            "facade_exposes_kernel_validity": facade["kernel_validity_state"] == "UNVERIFIED",
            "facade_exposes_effective_validity": facade["effective_validity_state"] == "UNVERIFIED",
            "no_gate_side_effect": rt.db.one("SELECT COUNT(*) n FROM gates WHERE project_id=?", (project,))["n"] == 0,
            "no_relation_side_effect": rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"] == 0,
        }
        result = {
            "schema": "DG-P6-GATE-v1",
            "status": "PASS" if all(checks.values()) else "FAIL",
            "checks": checks,
            "migration_ids": rt.db.migrations.status()["applied"],
            "validity_vocabulary": sorted(VALIDITY),
        }
        rt.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
