from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from gwr.auth import HumanAuthService
from gwr.domain_sdk import DomainSDK
from gwr.runtime import GovernedWorkflowRuntime

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    HumanAuthService.PASSWORD_ITERATIONS = 1000
    checks = []
    with tempfile.TemporaryDirectory() as td:
        rt = GovernedWorkflowRuntime(str(ROOT / "domains" / "research.workflow.yaml"), str(Path(td) / "v081.db"), auth_secret="q" * 64)
        backend = rt.db.backend_name
        required = {"domain_packages", "domain_package_revisions", "project_domain_bindings"}
        tables = set(rt.db.list_tables())
        checks.append({"name": "lifecycle_tables", "pass": required.issubset(tables), "missing": sorted(required - tables)})
        checks.append({"name": "migration_0004", "pass": "0004_v081_domain_project_lifecycle" in rt.db.migrations.status()["applied"]})

        human = rt.governance.create_actor("HUMAN", "qa-v081", ["human_approver"], [])
        rt.auth.register_human(human, "qa-v081", "qa-v081-password-long")
        tenant = rt.tenancy.create_tenant("QA 081", human)
        workspace = rt.tenancy.create_workspace(tenant, "Lifecycle", human)
        package = rt.domains.create_package(tenant, "qa.lifecycle", "QA Lifecycle", human)
        revision = rt.domains.add_revision(package, DomainSDK.scaffold("qa.lifecycle"), human)
        checks.append({"name": "domain_validate", "pass": rt.domains.validate_revision(revision, human)["ok"] is True})
        published = rt.domains.publish_revision(revision, human)
        checks.append({"name": "domain_publish", "pass": published["status"] == "PUBLISHED"})
        project = rt.create_scoped_project("QA Project", tenant, workspace, human, domain_revision_id=revision)
        binding = rt.domains.project_binding(project)
        checks.append({"name": "project_pin", "pass": binding and binding["domain_revision_id"] == revision})
        process = rt.process.process(project)
        checks.append({"name": "process_ready", "pass": process["status"] == "READY" and process["domain_binding"]["domain_revision_id"] == revision})
        rt.close()

    errors = [x for x in checks if not x["pass"]]
    result = {"version": "0.8.1", "backend": backend, "status": "PASS" if not errors else "FAIL", "checks": checks, "errors": errors}
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
