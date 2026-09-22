from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from gwr.document_relation import BINDING_LEGALITY, BINDING_MODES
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
        "source_resolved_at": "2026-09-23T00:00:00+00:00",
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
    row = rt.db.one("SELECT payload_hash FROM proposals WHERE proposal_id=?", (proposal_id,))
    return rt.governance.approve_proposal(proposal_id, owner, row["payload_hash"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="gwr-dg-p9-") as td:
        rt = GovernedWorkflowRuntime(
            str(ROOT / "domains" / "research.workflow.yaml"),
            str(Path(td) / "p9.db"),
        )
        owner = rt.governance.create_actor("HUMAN", "dg-p9-owner", ["human_approver"], [])
        tenant = rt.tenancy.create_tenant("dg-p9 tenant", owner)
        workspace = rt.tenancy.create_workspace(tenant, "dg-p9 workspace", owner)
        project = rt.create_scoped_project("dg-p9 project", tenant, workspace, owner)
        lead = rt.governance.create_actor("AGENT", "dg-p9-lead", ["research_lead"], [])
        rt.tenancy.add_project_member(project, lead, "RESEARCHER", owner)

        d1, r1 = make_document(rt, project, owner, "dg-p9-one", "1" * 64)
        d2, r2 = make_document(rt, project, owner, "dg-p9-two", "2" * 64)

        relation_id = uid("drel")
        now = utcnow()
        rt.db.conn.execute(
            "INSERT INTO document_relations("
            "relation_id,project_id,source_document_id,relation_type,target_kind,target_ref,"
            "invalidation_policy,status,created_revision_id,create_proposal_id,"
            "retired_revision_id,retired_by_proposal_id,version,created_at,updated_at,retired_at"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                relation_id, project, d1, "DEPENDS_ON", "DOCUMENT", d2,
                "LEGACY_P8_POLICY", "ACTIVE", r1, "legacy-p8-proposal",
                None, None, 0, now, now, None,
            ),
        )
        rt.db.conn.commit()
        legacy = rt.document_relations.get_relation(relation_id)

        proposal = rt.document_relations.prepare_binding(
            relation_id,
            lead,
            expected_version=0,
            binding_mode="PINNED_REVISION",
            target_revision_or_hash=r2,
        )
        approval = approve(rt, proposal, owner)
        bound = rt.document_relations.apply_approved_binding(proposal, lead)

        counts_before = {
            "trace": rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"],
            "impact": rt.db.one("SELECT COUNT(*) n FROM impacts WHERE project_id=?", (project,))["n"],
            "evidence": rt.db.one("SELECT COUNT(*) n FROM evidence WHERE project_id=?", (project,))["n"],
            "finding": rt.db.one("SELECT COUNT(*) n FROM document_findings WHERE project_id=?", (project,))["n"],
        }
        resolved = rt.document_relations.resolve_target(relation_id)
        counts_after = {
            "trace": rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"],
            "impact": rt.db.one("SELECT COUNT(*) n FROM impacts WHERE project_id=?", (project,))["n"],
            "evidence": rt.db.one("SELECT COUNT(*) n FROM evidence WHERE project_id=?", (project,))["n"],
            "finding": rt.db.one("SELECT COUNT(*) n FROM document_findings WHERE project_id=?", (project,))["n"],
        }
        audit = rt.db.one(
            "SELECT * FROM audit_events WHERE action='DOCUMENT_RELATION_BOUND' AND resource_id=?",
            (relation_id,),
        )
        tables = set(rt.db.list_tables())
        migration_ids = rt.db.migrations.status()["applied"]

        checks = {
            "p9_migration_applied": "0011_v086_dg_p9_relation_binding" in migration_ids,
            "legacy_binding_mode_null": legacy["target_binding_mode"] is None,
            "legacy_exact_target_null": legacy["target_revision_or_hash"] is None,
            "two_bound_modes_exact": BINDING_MODES == {"LOGICAL_CURRENT", "PINNED_REVISION"},
            "validates_pinned_only": BINDING_LEGALITY["VALIDATES"] == {"PINNED_REVISION"},
            "generated_from_pinned_only": BINDING_LEGALITY["GENERATED_FROM"] == {"PINNED_REVISION"},
            "derived_from_pinned_only": BINDING_LEGALITY["DERIVED_FROM"] == {"PINNED_REVISION"},
            "supersedes_pinned_only": BINDING_LEGALITY["SUPERSEDES"] == {"PINNED_REVISION"},
            "must_align_current_only": BINDING_LEGALITY["MUST_ALIGN_WITH"] == {"LOGICAL_CURRENT"},
            "depends_dual": BINDING_LEGALITY["DEPENDS_ON"] == {"LOGICAL_CURRENT", "PINNED_REVISION"},
            "references_dual": BINDING_LEGALITY["REFERENCES"] == {"LOGICAL_CURRENT", "PINNED_REVISION"},
            "implements_dual": BINDING_LEGALITY["IMPLEMENTS"] == {"LOGICAL_CURRENT", "PINNED_REVISION"},
            "one_time_bind_persisted": bound["target_binding_mode"] == "PINNED_REVISION",
            "pin_exact": bound["target_revision_or_hash"] == r2,
            "binding_version_incremented": bound["version"] == 1,
            "proposal_audited": audit["proposal_id"] == proposal,
            "approval_audited": audit["approval_id"] == approval,
            "resolver_exact": resolved["resolved_revision_id"] == r2,
            "resolver_hash_exact": resolved["resolved_content_hash"] == rt.knowledge.get_revision(r2)["content_hash"],
            "resolution_side_effect_free": counts_after == counts_before,
            "no_binding_table": "document_relation_bindings" not in tables,
            "no_binding_cache": "document_binding_cache" not in tables,
            "no_trace_projection": "document_trace_projection" not in tables,
            "no_change_set": "document_change_sets" not in tables,
            "no_catalog": "catalog_entries" not in tables,
        }

        result = {
            "schema": "DG-P9-GATE-v1",
            "status": "PASS" if all(checks.values()) else "FAIL",
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "checks": checks,
            "migration_ids": migration_ids,
            "document_tables": sorted(t for t in tables if t.startswith("document_")),
            "binding_relation_id": relation_id,
            "binding_proposal_id": proposal,
            "binding_approval_id": approval,
        }
        rt.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
