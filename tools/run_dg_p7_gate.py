from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import uid, utcnow


ROOT = Path(__file__).resolve().parents[1]


def payload(key: str, source_hash: str) -> dict:
    return {
        "schema": "DG-P4-DOCUMENT-REVISION-v1",
        "document_key": key,
        "title": key,
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
            "content_size_bytes": 1,
        },
        "source_resolved_at": "2026-09-21T00:00:00+00:00",
    }


def make_document(rt, project, actor, key, source_hash):
    document_id = rt.knowledge.create_artifact(
        project, "governed_document", f"gwr:document:{key}", actor
    )
    revision_id = rt.knowledge.create_revision(
        document_id,
        payload(key, source_hash),
        actor,
        expected_artifact_version=0,
    )["revision_id"]
    return document_id, revision_id


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="gwr-dg-p7-") as td:
        rt = GovernedWorkflowRuntime(
            str(ROOT / "domains" / "research.workflow.yaml"),
            str(Path(td) / "p7.db"),
        )
        owner = rt.governance.create_actor("HUMAN", "dg-p7-owner", ["human_approver"], [])
        tenant = rt.tenancy.create_tenant("dg-p7 tenant", owner)
        workspace = rt.tenancy.create_workspace(tenant, "dg-p7 workspace", owner)
        project = rt.create_scoped_project("dg-p7 project", tenant, workspace, owner)
        lead = rt.governance.create_actor("AGENT", "dg-p7-lead", ["research_lead"], [])
        rt.tenancy.add_project_member(project, lead, "RESEARCHER", owner)

        d1, r1 = make_document(rt, project, owner, "dg-p7-one", "1" * 64)
        policy_before = [dict(x) for x in rt.db.all("SELECT * FROM authority_policies ORDER BY policy_id")]

        proposal = rt.document_authority.prepare_primary_claim(
            d1, "research.protocol", "execution-amendment", lead
        )
        p = rt.db.one("SELECT payload_hash FROM proposals WHERE proposal_id=?", (proposal,))
        approval = rt.governance.approve_proposal(proposal, owner, p["payload_hash"])
        grant = rt.document_authority.apply_approved_grant(proposal, lead)
        claim_id = grant["claim_ids"][0]

        no_collision = rt.document_authority.scan_authority_key(
            project, "research.protocol", "execution-amendment", lead
        )
        evidence_after_clean_scan = rt.db.one(
            "SELECT COUNT(*) n FROM evidence WHERE project_id=?", (project,)
        )["n"]

        d2, r2 = make_document(rt, project, owner, "dg-p7-two", "2" * 64)
        imported = uid("claim")
        now = utcnow()
        rt.db.conn.execute(
            "INSERT INTO document_authority_claims VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                imported, project, d2, "research.protocol", "execution-amendment",
                "PRIMARY", None, None, None, "ACTIVE", r2, "imported", None, 0, now, now, None,
            ),
        )
        rt.db.conn.commit()
        collision = rt.document_authority.scan_authority_key(
            project, "research.protocol", "execution-amendment", lead
        )

        tables = set(rt.db.list_tables())
        policy_after = [dict(x) for x in rt.db.all("SELECT * FROM authority_policies ORDER BY policy_id")]
        claim = rt.document_authority.get_claim(claim_id)
        checks = {
            "p7_migration_applied": "0009_v086_dg_p7_document_authority_claims" in rt.db.migrations.status()["applied"],
            "claim_table_present": "document_authority_claims" in tables,
            "no_composition_table": "document_authority_composition" not in tables,
            "no_duplicate_table": "duplicate_authority" not in tables,
            "authority_policies_unchanged": policy_after == policy_before,
            "primary_claim_exact_revision": claim["granted_revision_id"] == r1,
            "primary_claim_proposal_bound": claim["grant_proposal_id"] == proposal,
            "grant_approval_audited": rt.db.one(
                "SELECT approval_id FROM audit_events WHERE action='DOCUMENT_AUTHORITY_GRANTED' AND resource_id=?",
                (claim_id,),
            )["approval_id"] == approval,
            "clean_scan_is_read_only_evidence": no_collision["collision"] is False and evidence_after_clean_scan == 0,
            "duplicate_scan_detected": collision["collision"] is True,
            "duplicate_scan_emitted_two_findings": len(collision["finding_refs"]) == 2,
            "duplicate_findings_nonwaivable_class": all(
                rt.document_qa.get_finding(fid)["finding_class"] == "DUPLICATE_AUTHORITY"
                for fid in collision["finding_refs"]
            ),
            "no_trace_relation_side_effect": rt.db.one(
                "SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,)
            )["n"] == 0,
        }
        result = {
            "schema": "DG-P7-GATE-v1",
            "status": "PASS" if all(checks.values()) else "FAIL",
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "checks": checks,
            "migration_ids": rt.db.migrations.status()["applied"],
            "document_tables": sorted(t for t in tables if t.startswith("document_")),
        }
        rt.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
