from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repository", required=True)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--path", required=True)
    ap.add_argument("--expected-repository-id", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if not os.environ.get("GITHUB_TOKEN"):
        raise SystemExit("GITHUB_TOKEN is required for real DG-P4 qualification")

    with tempfile.TemporaryDirectory(prefix="gwr-dg-p4-") as td:
        rt = GovernedWorkflowRuntime(
            str(ROOT / "domains" / "research.workflow.yaml"),
            str(Path(td) / "p4.db"),
        )
        human = rt.governance.create_actor("HUMAN", "dg-p4-gate-owner", ["human_approver"], [])
        tenant = rt.tenancy.create_tenant("dg-p4 gate tenant", human)
        workspace = rt.tenancy.create_workspace(tenant, "dg-p4 gate workspace", human)
        project = rt.create_scoped_project("dg-p4 gate project", tenant, workspace, human)
        connection = rt.plugins.create_connection(
            project,
            "github",
            "github-actions-runtime-token",
            ["REPO_READ"],
            human,
            metadata={"provider": "github", "purpose": "dg-p4-real-smoke"},
        )
        rt.plugins.attach_github_rest_adapter(connection, lambda _: os.environ["GITHUB_TOKEN"])
        binding = rt.github.bind_repository(
            project,
            connection,
            args.repository,
            "main",
            human,
            allowed_branches=["v0.8.6-*", "docs/*"],
        )

        source = rt.github.resolve_blob_revision(
            project,
            binding,
            human,
            ref_kind="COMMIT",
            ref_value=args.commit,
            path=args.path,
            expected_repository_id=args.expected_repository_id,
            expected_commit_sha=args.commit,
        )

        registered = rt.documents.register_document(
            project,
            binding,
            human,
            document_key="dg-p4-real-smoke",
            title="DG-P4 real provider smoke",
            ref_kind="COMMIT",
            ref_value=args.commit,
            path=args.path,
            expected_repository_id=args.expected_repository_id,
            expected_commit_sha=args.commit,
            expected_blob_sha=source["blob_sha"],
        )
        document = rt.documents.get_document(registered["document_id"])
        artifact = rt.knowledge.get_artifact(registered["document_id"])
        revision = rt.knowledge.get_revision(registered["revision_id"])

        checks = {
            "document_id_is_artifact_id": document["document_id"] == artifact["artifact_id"],
            "revision_id_is_kernel_revision": document["current_revision_id"] == revision["revision_id"],
            "reserved_core_type": artifact["artifact_type"] == "governed_document",
            "logical_key_path_independent": artifact["logical_key"] == "gwr:document:dg-p4-real-smoke",
            "exact_repository_bound": str(document["storage_locator"]["repository_id"]) == str(args.expected_repository_id),
            "exact_commit_bound": document["source_identity"]["commit_sha"] == args.commit,
            "exact_blob_bound": document["source_identity"]["blob_sha"] == source["blob_sha"],
            "source_sha256_bound": document["source_identity"]["content_sha256"] == source["content_sha256"],
            "payload_hash_distinct_from_source": revision["content_hash"] != source["content_sha256"],
            "new_revision_unverified": revision["validity_state"] == "UNVERIFIED",
            "no_relations_created": rt.db.one("SELECT COUNT(*) n FROM trace_links WHERE project_id=?", (project,))["n"] == 0,
            "no_qa_evidence_created": rt.db.one("SELECT COUNT(*) n FROM evidence WHERE project_id=?", (project,))["n"] == 0,
            "no_gates_created": rt.db.one("SELECT COUNT(*) n FROM gates WHERE project_id=?", (project,))["n"] == 0,
        }

        result = {
            "schema": "DG-P4-GATE-v1",
            "status": "PASS" if all(checks.values()) else "FAIL",
            "commit": args.commit,
            "repository": args.repository,
            "path": args.path,
            "repository_id": document["storage_locator"]["repository_id"],
            "blob_sha": document["source_identity"]["blob_sha"],
            "source_content_sha256": document["source_identity"]["content_sha256"],
            "document_id": document["document_id"],
            "revision_id": document["current_revision_id"],
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
