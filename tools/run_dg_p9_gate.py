from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from gwr.runtime import GovernedWorkflowRuntime


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


def approve(rt, proposal_id, owner):
    row = rt.db.one(
        "SELECT payload_hash FROM proposals WHERE proposal_id=?",
        (proposal_id,),
    )
    return rt.governance.approve_proposal(
        proposal_id, owner, row["payload_hash"]
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="gwr-dg-p9-") as td:
        rt = GovernedWorkflowRuntime(
            str(ROOT / "domains" / "research.workflow.yaml"),
            str(Path(td) / "p9.db"),
        )
        owner = rt.governance.create_actor(
            "HUMAN", "dg-p9-owner", ["human_approver"], []
        )
        tenant = rt.tenancy.create_tenant("dg-p9 tenant", owner)
        workspace = rt.tenancy.create_workspace(
            tenant, "dg-p9 workspace", owner
        )
        project = rt.create_scoped_project(
            "dg-p9 project", tenant, workspace, owner
        )
        lead = rt.governance.create_actor(
            "AGENT", "dg-p9-lead", ["research_lead"], []
        )
        rt.tenancy.add_project_member(project, lead, "RESEARCHER", owner)

        d1, _ = make_document(rt, project, owner, "dg-p9-one", "1" * 64)
        d2, r2 = make_document(rt, project, owner, "dg-p9-two", "2" * 64)

        trace_before = rt.db.one(
            "SELECT COUNT(*) n FROM trace_links WHERE project_id=?",
            (project,),
        )["n"]
        impact_before = rt.db.one(
            "SELECT COUNT(*) n FROM impacts WHERE project_id=?",
            (project,),
        )["n"]
        evidence_before = rt.db.one(
            "SELECT COUNT(*) n FROM evidence WHERE project_id=?",
            (project,),
        )["n"]

        proposal = rt.document_relations.prepare_relation(
            d1,
            "VALIDATES",
            "DOCUMENT",
            d2,
            lead,
            target_binding_mode="PINNED_REVISION",
            target_revision_or_hash=r2,
        )
        approval = approve(rt, proposal, owner)
        relation = rt.document_relations.apply_approved_declaration(
            proposal, lead
        )
        resolved = rt.document_relations.resolve_relation(
            relation["relation_id"]
        )

        checks = {
            "migration_present": (
                "0011_v086_dg_p9_relation_binding"
                in rt.db.migrations.status()["known"]
            ),
            "binding_columns_present": all(
                key in relation
                for key in (
                    "target_binding_mode",
                    "target_revision_or_hash",
                )
            ),
            "validates_pinned": (
                relation["target_binding_mode"] == "PINNED_REVISION"
                and relation["target_revision_or_hash"] == r2
            ),
            "exact_resolution": (
                resolved["resolved_revision_id"] == r2
                and bool(resolved["resolved_content_hash"])
            ),
            "proposal_approval_attributed": bool(
                rt.db.one(
                    "SELECT 1 FROM audit_events "
                    "WHERE action='DOCUMENT_RELATION_DECLARED' "
                    "AND resource_id=? AND proposal_id=? AND approval_id=?",
                    (
                        relation["relation_id"],
                        proposal,
                        approval,
                    ),
                )
            ),
            "no_trace_projection": (
                rt.db.one(
                    "SELECT COUNT(*) n FROM trace_links WHERE project_id=?",
                    (project,),
                )["n"]
                == trace_before
            ),
            "no_impact_side_effect": (
                rt.db.one(
                    "SELECT COUNT(*) n FROM impacts WHERE project_id=?",
                    (project,),
                )["n"]
                == impact_before
            ),
            "no_evidence_side_effect": (
                rt.db.one(
                    "SELECT COUNT(*) n FROM evidence WHERE project_id=?",
                    (project,),
                )["n"]
                == evidence_before
            ),
            "no_binding_table": "document_relation_bindings"
            not in rt.db.list_tables(),
            "no_cache_table": "document_binding_cache"
            not in rt.db.list_tables(),
        }

        result = {
            "schema": "DG-P9-GATE-v1",
            "status": "PASS" if all(checks.values()) else "FAIL",
            "backend": rt.db.backend_name,
            "checks": checks,
            "migration_ids": rt.db.migrations.status()["known"],
            "document_tables": [
                t for t in rt.db.list_tables() if t.startswith("document_")
            ],
            "relation_id": relation["relation_id"],
            "binding_mode": relation["target_binding_mode"],
            "resolved_revision_id": resolved["resolved_revision_id"],
        }
        rt.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
