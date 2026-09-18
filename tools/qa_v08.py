from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from gwr.auth import HumanAuthService
from gwr.domain_sdk import DomainSDK
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import uid, utcnow

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    HumanAuthService.PASSWORD_ITERATIONS = 1000
    checks = []

    report = DomainSDK.validate(ROOT / "domains" / "research.workflow.yaml")
    checks.append({"name": "domain_sdk_validate", "pass": report.ok, "warnings": len(report.warnings)})
    scaffold = DomainSDK.scaffold("qa.product")
    import yaml
    scaffold_report = DomainSDK.validate(yaml.safe_load(scaffold))
    checks.append({"name": "domain_sdk_scaffold", "pass": scaffold_report.ok})

    with tempfile.TemporaryDirectory() as td:
        rt = GovernedWorkflowRuntime(str(ROOT / "domains" / "research.workflow.yaml"), str(Path(td) / "v08.db"), auth_secret="z" * 64)
        backend = rt.db.backend_name
        human = rt.governance.create_actor("HUMAN", "qa-operator", ["human_approver"], [])
        rt.auth.register_human(human, "qa-operator", "qa-operator-password")
        tenant = rt.tenancy.create_tenant("QA Tenant", human)
        workspace = rt.tenancy.create_workspace(tenant, "QA Workspace", human)
        project = rt.create_scoped_project("QA Product", tenant, workspace, human)
        rt.tenancy.add_project_member(project, human, "APPROVER", human)

        proposal = rt.governance.prepare_system_proposal(
            project, "CONFIRM_ROOT", ["artifact:experiment_plan"],
            {"failure_id": "qa-failure", "root": "experiment_plan"},
            "human_recovery_confirmation",
        )
        failure_id = uid("fail")
        rt.db.conn.execute(
            "INSERT INTO failures VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (failure_id, project, "wu-qa", "pilot_degenerate", "PILOT", "run-qa", None, None, "[]",
             "experiment_plan", None, "PROPOSED", "phase_06_plan_and_implement_experiment", "MEDIUM",
             "qa-signature", "OPEN", utcnow(), None),
        )
        recovery_id = uid("rec")
        rt.db.conn.execute(
            "INSERT INTO recoveries VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (recovery_id, project, failure_id, "experiment_plan", "phase_06_plan_and_implement_experiment",
             "[]", "[]", '["pilot_result"]', "[]", "[]", "[]", "[]",
             "AFTER_INVALIDATION", "PLANNED", utcnow()),
        )
        rt.db.conn.commit()

        summary = __import__("gwr.product", fromlist=["ProjectDashboardService"]).ProjectDashboardService(rt).summary(project)
        checks.append({"name": "dashboard_read_model", "pass": summary["metrics"]["pending_approvals"] == 1 and summary["metrics"]["open_failures"] == 1})
        checks.append({"name": "failure_recovery_graph", "pass": len(summary["failure_graph"]["edges"]) >= 2})

        token = rt.auth.authenticate("qa-operator", "qa-operator-password")
        row = rt.db.one("SELECT payload_hash FROM proposals WHERE proposal_id=?", (proposal,))
        rejected = rt.governance.reject_proposal_authenticated(proposal, token, row["payload_hash"], "QA_REJECT")
        decision = rt.db.one("SELECT decision FROM approvals WHERE approval_id=?", (rejected,))
        checks.append({"name": "authenticated_exact_hash_rejection", "pass": decision["decision"] == "REJECTED"})
        rt.close()

    data = json.loads((ROOT / "web" / "demo-data.json").read_text(encoding="utf-8"))
    primary = data["projects"][0]
    checks.append({"name": "uat_fixture_approval", "pass": bool(primary["approvals"])})
    checks.append({"name": "uat_fixture_failure_recovery", "pass": bool(primary["failures"])})
    checks.append({"name": "uat_fixture_distributed", "pass": bool(primary["distributed"]["jobs"])})

    errors = [c for c in checks if not c["pass"]]
    result = {"version": "0.8.0", "backend": backend, "status": "PASS" if not errors else "FAIL", "checks": checks, "errors": errors}
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
