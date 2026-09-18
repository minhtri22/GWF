from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from gwr.errors import InvalidTransition
from gwr.research_demo import DeterministicResearchExecutor
from gwr.research_orchestrator import ResearchOrchestrator
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).resolve().parents[1]
ROLES = [
    "research_lead",
    "literature_reviewer",
    "protocol_designer",
    "experimenter",
    "analyst",
    "adversarial_reviewer",
    "reproducibility_reviewer",
]


def make_project(rt, label: str):
    project = rt.create_project(f"qa-v083-{label}")
    actors = {
        role: rt.governance.create_actor("AGENT", f"qa-{label}-{role}", [role], [project])
        for role in ROLES
    }
    human = rt.governance.create_actor("HUMAN", f"qa-{label}-human", ["human_approver"], [project])
    return project, actors, human


def add(checks, name, passed, **metadata):
    checks.append({"name": name, "pass": bool(passed), **metadata})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    checks = []

    with tempfile.TemporaryDirectory() as td:
        rt = GovernedWorkflowRuntime(
            str(ROOT / "domains" / "research.workflow.yaml"),
            str(Path(td) / "qa-v083.db"),
        )
        backend = rt.db.backend_name
        tables = set(rt.db.list_tables())
        required = {
            "domain_skill_bindings",
            "phase_handoff_links",
            "project_agent_protocol_settings",
        }
        add(checks, "v083_tables", required.issubset(tables), missing=sorted(required - tables))
        add(
            checks,
            "v083_migration",
            "0006_v083_orchestrator_integration" in rt.db.migrations.status()["applied"],
        )

        bindings = rt.db.all(
            "SELECT * FROM domain_skill_bindings WHERE domain_id=?",
            (rt.domain.domain_id,),
        )
        add(
            checks,
            "domain_skill_binding",
            len(bindings) == len(rt.domain.workunits()) == 17
            and all(x["skill_revision_id"] and x["skill_hash"] for x in bindings),
            binding_count=len(bindings),
        )

        project, actors, human = make_project(rt, "pass")
        orch = ResearchOrchestrator(rt, actors, human_approver_id=human)
        result = orch.start(project, DeterministicResearchExecutor("pass"))
        succeeded = rt.db.all(
            "SELECT * FROM phase_executions WHERE orchestration_id=? AND status='SUCCEEDED'",
            (result["orchestration_id"],),
        )
        completed_protocols = 0
        valid_links = 0
        stage_sequences = 0
        for phase in succeeded:
            protocol = rt.db.one(
                "SELECT * FROM phase_execution_protocols WHERE phase_execution_id=?",
                (phase["phase_execution_id"],),
            )
            if protocol and protocol["status"] == "COMPLETED" and protocol["current_stage"] == "COMPLETE":
                completed_protocols += 1
            link = rt.db.one(
                "SELECT * FROM phase_handoff_links WHERE phase_execution_id=?",
                (phase["phase_execution_id"],),
            )
            if link and (
                int(phase["phase_index"]) == 0
                or (link["previous_phase_execution_id"] and link["previous_handoff_id"] and link["handoff_hash"])
            ):
                valid_links += 1
            ev = [
                x["event_type"]
                for x in rt.db.all(
                    "SELECT * FROM phase_stage_events WHERE phase_execution_id=? ORDER BY created_at,event_id",
                    (phase["phase_execution_id"],),
                )
            ]
            required_events = [
                "SKILL_LOADED",
                "PREFLIGHT_PASS",
                "PLAN_FROZEN",
                "EXECUTION_STARTED",
                "QA_PASS",
                "HANDOFF_WRITTEN",
                "PROTOCOL_COMPLETED",
            ]
            if all(x in ev for x in required_events) and [ev.index(x) for x in required_events] == sorted(ev.index(x) for x in required_events):
                stage_sequences += 1
        add(
            checks,
            "protocol_driven_orchestration",
            result["status"] == "COMPLETED"
            and completed_protocols == len(succeeded)
            and stage_sequences == len(succeeded),
            succeeded=len(succeeded),
            completed_protocols=completed_protocols,
        )
        add(
            checks,
            "handoff_chain",
            valid_links == len(succeeded),
            valid_links=valid_links,
            succeeded=len(succeeded),
        )

        retry_project, retry_actors, retry_human = make_project(rt, "retry")
        retry_orch = ResearchOrchestrator(rt, retry_actors, human_approver_id=retry_human)
        retry_result = retry_orch.start(retry_project, DeterministicResearchExecutor("runtime_retry"))
        attempts = rt.db.all(
            "SELECT * FROM phase_executions WHERE orchestration_id=? AND phase_id='phase_09_main_experiment' ORDER BY started_at,phase_execution_id",
            (retry_result["orchestration_id"],),
        )
        retry_order_ok = False
        if len(attempts) == 2:
            first_view = rt.agent_protocol.inspect(attempts[0]["phase_execution_id"])
            ev = [x["event_type"] for x in first_view["events"]]
            retry_order_ok = (
                attempts[0]["status"] == "FAILED"
                and attempts[1]["status"] == "SUCCEEDED"
                and first_view["protocol"]["status"] == "FAILED"
                and ev.index("PROBLEM_RECORDED") < ev.index("RECOVERY_APPLIED") < ev.index("ATTEMPT_FAILED")
            )
        add(checks, "problem_before_retry", retry_result["status"] == "COMPLETED" and retry_order_ok)

        hierarchy_project, _, hierarchy_human = make_project(rt, "hierarchy")
        rt.agent_protocol.set_project_defaults(
            hierarchy_project,
            "SYSTEM",
            recovery_mode="AUTO",
            retry_budget=5,
        )
        phase = rt.domain.workunit("phase_09_main_experiment")
        original_phase_protocol = dict(phase.get("agent_protocol", {}) or {})
        phase["agent_protocol"] = {"minimum_recovery_mode": "HUMAN_APPROVE", "retry_budget": 3}
        hierarchy = rt.agent_protocol.resolve_recovery_config(
            hierarchy_project,
            "phase_09_main_experiment",
            requested_mode="AUTO",
        )
        phase["agent_protocol"] = original_phase_protocol
        add(
            checks,
            "recovery_hierarchy",
            hierarchy["recovery_mode"] == "HUMAN_APPROVE" and hierarchy["retry_budget"] == 3,
            effective=hierarchy,
        )

        archive_project, archive_actors, archive_human = make_project(rt, "archive")
        archive_orch = ResearchOrchestrator(rt, archive_actors, human_approver_id=archive_human)
        archived = rt.project_governance.archive(archive_project, archive_human)
        blocked = False
        try:
            archive_orch.start(archive_project, DeterministicResearchExecutor("pass"))
        except InvalidTransition:
            blocked = True
        add(checks, "archive_blocks_orchestration_start", archived["status"] == "ARCHIVED" and blocked)

        rt.close()

    errors = [c for c in checks if not c["pass"]]
    result = {
        "version": "0.8.3",
        "backend": backend,
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
