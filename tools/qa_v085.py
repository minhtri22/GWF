from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from gwr.domain_sdk import DomainSDK
from gwr.linear_orchestrator import LinearDomainOrchestrator
from gwr.research_demo import DeterministicResearchExecutor
from gwr.research_orchestrator import ResearchOrchestrator
from gwr.runtime import GovernedWorkflowRuntime
from gwr.software_demo import DeterministicSoftwareExecutor

from gwr_pilot import validate_profile


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROLES = [
    "research_lead",
    "literature_reviewer",
    "protocol_designer",
    "experimenter",
    "analyst",
    "adversarial_reviewer",
    "reproducibility_reviewer",
]


def add(checks, name, passed, **metadata):
    checks.append({"name": name, "pass": bool(passed), **metadata})


def actors_for(rt, project):
    roles = sorted({w["executor_role"] for w in rt.domain.workunits()})
    actors = {
        role: rt.governance.create_actor(
            "AGENT",
            f"qa-v085-{rt.domain.domain_id}-{role}",
            [role],
            [project],
        )
        for role in roles
    }
    human = rt.governance.create_actor(
        "HUMAN",
        f"qa-v085-{rt.domain.domain_id}-human",
        ["human_approver"],
        [project],
    )
    return actors, human


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    checks = []

    with tempfile.TemporaryDirectory() as td:
        research_path = ROOT / "domains" / "research.workflow.yaml"
        software_path = ROOT / "domains" / "software.workflow.yaml"

        research_validation = DomainSDK.validate(research_path)
        software_validation = DomainSDK.validate(software_path)
        add(
            checks,
            "domain_packages_validate",
            research_validation.ok and software_validation.ok,
            research_errors=research_validation.errors,
            software_errors=software_validation.errors,
        )

        rt = GovernedWorkflowRuntime(
            str(research_path),
            str(Path(td) / "research-v085.db"),
        )
        backend = rt.db.backend_name
        study = rt.domain.artifact("study_lock")
        refs = {w["skill_ref"] for w in rt.domain.workunits()}
        lock_inputs_ok = all(
            "study_lock" in {
                x["artifact_type"] if isinstance(x, dict) else x
                for x in rt.domain.workunit(pid).get("inputs", [])
            }
            for pid in (
                "phase_05_prepare_dataset_and_benchmark",
                "phase_06_plan_and_implement_experiment",
                "phase_07_preflight",
                "phase_08_pilot",
                "phase_09_main_experiment",
                "phase_10_analyze_results",
                "phase_11_adversarial_falsification_review",
                "phase_12_decide_pass_fail_pivot",
                "phase_14_replication_or_replay",
                "phase_15_write_final_report",
            )
        )
        add(
            checks,
            "research_study_lock_contract",
            study is not None
            and all(x.endswith("_v2") for x in refs)
            and lock_inputs_ok
            and "no_rescue_policy" in set(study["required_fields"]),
        )

        project = rt.create_project("qa-v085-research")
        actors, human = actors_for(rt, project)
        research_result = ResearchOrchestrator(
            rt,
            actors,
            human_approver_id=human,
        ).start(project, DeterministicResearchExecutor("pass"))
        completed_protocols = rt.db.one(
            "SELECT COUNT(*) n FROM phase_execution_protocols p "
            "JOIN phase_executions e ON e.phase_execution_id=p.phase_execution_id "
            "WHERE e.orchestration_id=? AND p.status='COMPLETED'",
            (research_result["orchestration_id"],),
        )["n"]
        add(
            checks,
            "research_governed_execution",
            research_result["status"] == "COMPLETED"
            and research_result["outcome"] == "PASS"
            and int(completed_protocols) == 16,
            completed_protocols=int(completed_protocols),
        )
        rt.close()

        sw = GovernedWorkflowRuntime(
            str(software_path),
            str(Path(td) / "software-v085.db"),
        )
        phases = sw.domain.workunits()
        add(
            checks,
            "software_domain_contract",
            sw.domain.domain_id == "software.delivery"
            and sw.domain.data.get("orchestration_mode") == "linear"
            and len(phases) == 11
            and phases[-2]["id"] == "phase_09_exact_main_verify"
            and phases[-1]["id"] == "phase_10_release_handoff",
            phase_count=len(phases),
        )
        sw_project = sw.create_project("qa-v085-software")
        sw_actors, sw_human = actors_for(sw, sw_project)
        sw_result = LinearDomainOrchestrator(
            sw,
            sw_actors,
            human_approver_id=sw_human,
        ).start(sw_project, DeterministicSoftwareExecutor())
        sw_completed = sw.db.one(
            "SELECT COUNT(*) n FROM phase_execution_protocols p "
            "JOIN phase_executions e ON e.phase_execution_id=p.phase_execution_id "
            "WHERE e.orchestration_id=? AND p.status='COMPLETED'",
            (sw_result["orchestration_id"],),
        )["n"]
        exact = sw.db.one(
            "SELECT current_revision_id FROM artifacts "
            "WHERE project_id=? AND artifact_type='exact_main_verification'",
            (sw_project,),
        )
        exact_payload = sw.knowledge.get_revision(exact["current_revision_id"])[
            "structured_payload"
        ] if exact and exact["current_revision_id"] else {}
        add(
            checks,
            "software_governed_execution",
            sw_result["status"] == "COMPLETED"
            and int(sw_completed) == 11
            and exact_payload.get("all_required_pass") is True,
            completed_protocols=int(sw_completed),
        )
        sw.close()

        cqg = validate_profile(ROOT / "pilots" / "cqg.research.yaml")
        gwf = validate_profile(ROOT / "pilots" / "gwf.self-upgrade.yaml")
        add(
            checks,
            "pilot_profiles",
            cqg["ok"] and gwf["ok"],
            cqg_errors=cqg["errors"],
            gwf_errors=gwf["errors"],
        )

        installer = (ROOT / "install.ps1").read_text(encoding="utf-8")
        add(
            checks,
            "one_click_installer_contract",
            all(
                token in installer
                for token in (
                    "[switch]$Qualification",
                    '$InstallTarget = if ($QualificationMode) { ".[dev,postgres]" } else { "." }',
                    '"tools/gwr_domain.py", "validate", "domains/research.workflow.yaml"',
                    '"tools/gwr_domain.py", "validate", "domains/software.workflow.yaml"',
                    '"tools/gwr_pilot.py", "validate", "pilots/cqg.research.yaml"',
                    '"tools/gwr_pilot.py", "validate", "pilots/gwf.self-upgrade.yaml"',
                    'if ($QualificationMode -and -not $SkipTests)',
                    'if ($QualificationMode -and -not $SkipUat)',
                    "timings_seconds = $Timings",
                    "install-report.json",
                    "dsn_persisted = $false",
                )
            ),
        )

    errors = [x for x in checks if not x["pass"]]
    result = {
        "version": "0.8.5",
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
