from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from gwr.errors import AuthorityDenied
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repository", required=True)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--path", required=True)
    ap.add_argument("--expected-repository-id", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required for real DG-P3 qualification")

    with tempfile.TemporaryDirectory(prefix="gwr-dg-p3-") as td:
        rt = GovernedWorkflowRuntime(
            str(ROOT / "domains" / "research.workflow.yaml"),
            str(Path(td) / "p3.db"),
        )
        human = rt.governance.create_actor("HUMAN", "dg-p3-gate-owner", ["human_approver"], [])
        tenant = rt.tenancy.create_tenant("dg-p3 gate tenant", human)
        workspace = rt.tenancy.create_workspace(tenant, "dg-p3 gate workspace", human)
        project = rt.create_scoped_project("dg-p3 gate project", tenant, workspace, human)
        agent = rt.governance.create_actor("AGENT", "dg-p3-gate-agent", ["research_lead"], [])
        rt.tenancy.add_project_member(project, agent, "RESEARCHER", human)

        connection = rt.plugins.create_connection(
            project,
            "github",
            "github-actions-runtime-token",
            ["REPO_READ"],
            human,
            metadata={"provider": "github", "purpose": "dg-p3-real-smoke"},
        )
        rt.plugins.attach_github_rest_adapter(connection, lambda _: os.environ["GITHUB_TOKEN"])
        binding = rt.github.bind_repository(
            project,
            connection,
            args.repository,
            "main",
            human,
            allowed_branches=["v0.8.6-*", "feature/*", "docs/*"],
        )

        first = rt.github.resolve_blob_revision(
            project,
            binding,
            agent,
            ref_kind="COMMIT",
            ref_value=args.commit,
            path=args.path,
            expected_repository_id=args.expected_repository_id,
            expected_commit_sha=args.commit,
        )
        second = rt.github.resolve_blob_revision(
            project,
            binding,
            agent,
            ref_kind="COMMIT",
            ref_value=args.commit,
            path=args.path,
            expected_repository_id=args.expected_repository_id,
            expected_commit_sha=args.commit,
            expected_blob_sha=first["blob_sha"],
        )

        denied = False
        try:
            rt.github.prepare_change_set(
                project,
                binding,
                "v0.8.6-dg-p3-git-blob-resolver",
                args.commit,
                [{"path": "docs/forbidden.md", "operation": "CREATE", "content": "forbidden\n"}],
                "docs: forbidden read-only write",
                agent,
            )
        except AuthorityDenied:
            denied = True

        stable_keys = [
            "provider",
            "repository_id",
            "repository_full_name_at_resolution",
            "resolved_commit_sha",
            "commit_tree_sha",
            "path_locator",
            "blob_sha",
            "content_sha256",
            "content_size_bytes",
        ]
        deterministic = all(first[k] == second[k] for k in stable_keys)
        serialized = json.dumps({"first": first, "second": second}, sort_keys=True)
        secret_absent = token not in serialized and "Authorization" not in serialized and '"content":' not in serialized

        checks = {
            "provider_repository_identity": str(first["repository_id"]) == str(args.expected_repository_id),
            "exact_commit_bound": first["resolved_commit_sha"] == args.commit,
            "exact_blob_bound": bool(first["blob_sha"]),
            "independent_content_sha256": len(first["content_sha256"]) == 64,
            "raw_content_not_normalized": "content" not in first,
            "read_only_write_denied": denied,
            "deterministic_exact_resolution": deterministic,
            "credential_material_absent": secret_absent,
        }
        result = {
            "status": "PASS" if all(checks.values()) else "FAIL",
            "repository": args.repository,
            "commit": args.commit,
            "path": args.path,
            "repository_id": first["repository_id"],
            "blob_sha": first["blob_sha"],
            "content_sha256": first["content_sha256"],
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
