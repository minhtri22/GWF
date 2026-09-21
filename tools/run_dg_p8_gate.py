from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from gwr.document_relation import RELATION_TYPES, TARGET_KINDS
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
        project,
        "governed_document",
        f"gwr:document:{key}",
        actor,
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
        proposal_id,
        owner,
        row["payload_hash"],
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="gwr-dg-p8-") as td:
        rt = GovernedWorkflowRuntime(
            str(ROOT / "domains" / "research.workflow.yaml"),
            str(Path(td) / "p8.db"),
        )
        owner = rt.governance.create_actor(
            "HUMAN", "dg-p8-owner", ["human_approver"], []
        )
        tenant = rt.tenancy.create_tenant("dg-p8 tenant", owner)
        workspace = rt.tenancy.create_workspace(
            tenant, "dg-p8 workspace", owner
        )
        project = rt.create_scoped_project(
            "dg-p8 project", tenant, workspace, owner
        )
        lead = rt.governance.create_actor(
            "AGENT", "dg-p8-lead", ["research_lead"], []
        )
        rt.tenancy.add_project_member(project, lead, "RESEARCHER", owner)

        d1, r1 = make_document(rt, project, owner, "dg-p8-one", "1" * 64)
        d2, _ = make_document(rt, project, owner, "dg-p8-two", "2" * 64)

        trace_before = rt.db.one(
            "SELECT COUNT(*) n FROM trace_links WHERE project_id=?",
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
        )
        approval = approve(rt, proposal, owner)
        relation = rt.document_relations.apply_approved_declaration(
            proposal, lead
        )

        tables = set(rt.db.list_tables())
        after_trace = rt.db.one(
            "SELECT COUNT(*) n FROM trace_links WHERE project_id=?",
            (project,),
        )["n"]
        after_evidence = rt.db.one(
            "SELECT COUNT(*) n FROM evidence WHERE project_id=?",
            (project,),
        )["n"]
        audit = rt.db.one(
            "SELECT * FROM audit_events "
            "WHERE action='DOCUMENT_RELATION_DECLARED' AND resource_id=?",
            (relation["relation_id"],),
        )

        checks = {
            "p8_migration_applied":
                "0010_v086_dg_p8_document_relations"
                in rt.db.migrations.status()["applied"],
            "relation_table_present": "document_relations" in tables,
            "no_relation_nodes_table": "document_relation_nodes" not in tables,
            "no_relation_types_table": "document_relation_types" not in tables,
            "no_relation_events_table": "document_relation_events" not in tables,
            "no_projection_table": "document_trace_projection" not in tables,
            "required_relation_types_exact": RELATION_TYPES == {
                "DEPENDS_ON",
                "REFERENCES",
                "MUST_ALIGN_WITH",
                "SUPERSEDES",
                "DERIVED_FROM",
                "VALIDATES",
                "IMPLEMENTS",
                "GENERATED_FROM",
            },
            "required_target_kinds_exact": TARGET_KINDS == {
                "DOCUMENT",
                "SOURCE_CODE",
                "SCHEMA",
                "API",
                "WORKFLOW",
                "DATASET",
                "STUDY_LOCK",
                "OTHER_ARTIFACT",
            },
            "source_is_logical_document":
                relation["source_document_id"] == d1,
            "creation_revision_exact":
                relation["created_revision_id"] == r1,
            "proposal_bound":
                relation["create_proposal_id"] == proposal,
            "approval_audited":
                audit["approval_id"] == approval,
            "validates_not_binding":
                "target_binding_mode" not in relation
                and "target_revision_or_hash" not in relation,
            "no_trace_projection": after_trace == trace_before,
            "no_validation_evidence_side_effect":
                after_evidence == evidence_before,
        }

        result = {
            "schema": "DG-P8-GATE-v1",
            "status": "PASS" if all(checks.values()) else "FAIL",
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "checks": checks,
            "migration_ids": rt.db.migrations.status()["applied"],
            "document_tables": sorted(
                t for t in tables if t.startswith("document_")
            ),
        }
        rt.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
