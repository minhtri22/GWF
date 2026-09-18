from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gwr.runtime import GovernedWorkflowRuntime
from gwr.research_orchestrator import ResearchOrchestrator
from gwr.research_demo import DeterministicResearchExecutor

ROLES = [
    "research_lead", "literature_reviewer", "protocol_designer", "experimenter",
    "analyst", "adversarial_reviewer", "reproducibility_reviewer",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", choices=["pass", "fail", "pivot", "runtime_retry", "runtime_recovery"], default="pass")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    out = Path(args.out) if args.out else ROOT / "evidence" / "research_v02" / args.scenario
    out.mkdir(parents=True, exist_ok=True)
    db_path = out / "runtime.db"
    if db_path.exists():
        db_path.unlink()
    rt = GovernedWorkflowRuntime(str(ROOT / "domains" / "research.workflow.yaml"), str(db_path))
    project = rt.create_project(f"v0.2-{args.scenario}")
    actors = {role: rt.governance.create_actor("AGENT", f"{role}-demo", [role], [project]) for role in ROLES}
    human = rt.governance.create_actor("HUMAN", "human-demo", ["human_approver"], [project])
    orch = ResearchOrchestrator(rt, actors, human_approver_id=human)
    result = orch.start(project, DeterministicResearchExecutor(args.scenario))
    report = orch.write_report(result["orchestration_id"], out / "REPORT.md")
    (out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (out / "status.json").write_text(json.dumps(orch.get_status(result["orchestration_id"]), indent=2), encoding="utf-8")
    audit = rt.governance.query_audit(project)
    (out / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"report={report}")
    rt.close()


if __name__ == "__main__":
    main()
