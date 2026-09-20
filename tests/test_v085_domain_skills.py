from __future__ import annotations

from pathlib import Path
import secrets
import subprocess
import sys

from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.domain_sdk import DomainSDK
from gwr.linear_orchestrator import LinearDomainOrchestrator
from gwr.research_demo import DeterministicResearchExecutor
from gwr.research_orchestrator import ResearchOrchestrator
from gwr.runtime import GovernedWorkflowRuntime
from gwr.software_demo import DeterministicSoftwareExecutor


ROOT = Path(__file__).parents[1]


def _actors(rt, project, roles):
    return {
        role: rt.governance.create_actor(
            "AGENT",
            f"v085-{role}",
            [role],
            [project],
        )
        for role in roles
    }


def test_research_domain_v05_matches_frozen_study_workflow(tmp_path):
    domain_path = ROOT / "domains" / "research.workflow.yaml"
    report = DomainSDK.validate(domain_path)
    assert report.ok, report.to_dict()

    rt = GovernedWorkflowRuntime(str(domain_path), str(tmp_path / "research-v085.db"))
    assert rt.domain.data["version"] == "0.5.0"
    assert rt.domain.data["compatible_runtime_versions"] == ["0.8.x"]

    lock = rt.domain.artifact("study_lock")
    assert lock is not None
    required = set(lock["required_fields"])
    assert {
        "preregistration_sha256",
        "source_commit",
        "frozen_artifacts",
        "fresh_data_policy",
        "seed_or_cohort_policy",
        "forbidden_adaptations",
        "amendment_policy",
        "branch_stop_rules",
        "repair_budget",
        "no_rescue_policy",
    }.issubset(required)

    phase04 = rt.domain.workunit("phase_04_design_protocol")
    outputs = {
        x["artifact_type"] if isinstance(x, dict) else x
        for x in phase04["outputs"]
    }
    assert {"protocol", "study_lock"}.issubset(outputs)
    assert "study_lock_evidence" in phase04["evidence_required"]
    for phase_id in (
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
    ):
        phase = rt.domain.workunit(phase_id)
        inputs = {
            x["artifact_type"] if isinstance(x, dict) else x
            for x in phase.get("inputs", [])
        }
        assert "study_lock" in inputs, phase_id

    refs = {w["skill_ref"] for w in rt.domain.workunits()}
    assert refs
    assert all(x.endswith("_v2") for x in refs)

    project = rt.create_project("research-v085")
    roles = sorted({w["executor_role"] for w in rt.domain.workunits()})
    actors = _actors(rt, project, roles)
    human = rt.governance.create_actor(
        "HUMAN",
        "v085-research-human",
        ["human_approver"],
        [project],
    )
    orch = ResearchOrchestrator(rt, actors, human_approver_id=human)
    result = orch.start(project, DeterministicResearchExecutor("pass"))
    assert result["status"] == "COMPLETED"
    assert result["outcome"] == "PASS"

    study = rt.db.one(
        "SELECT current_revision_id FROM artifacts WHERE project_id=? AND artifact_type='study_lock'",
        (project,),
    )
    assert study and study["current_revision_id"]

    phases = rt.db.all(
        "SELECT * FROM phase_executions WHERE orchestration_id=? AND status='SUCCEEDED'",
        (result["orchestration_id"],),
    )
    assert len(phases) == 16
    for phase in phases:
        protocol = rt.db.one(
            "SELECT * FROM phase_execution_protocols WHERE phase_execution_id=?",
            (phase["phase_execution_id"],),
        )
        assert protocol["status"] == "COMPLETED"
    rt.close()


def test_research_multiple_normative_outputs_resume_without_duplicate_revisions(tmp_path):
    domain_path = ROOT / "domains" / "research.workflow.yaml"
    rt = GovernedWorkflowRuntime(
        str(domain_path),
        str(tmp_path / "research-v085-manual-approval.db"),
        auth_secret=secrets.token_urlsafe(48),
    )
    project = rt.create_project("research-v085-manual-approval")
    roles = sorted({w["executor_role"] for w in rt.domain.workunits()})
    actors = _actors(rt, project, roles)
    human = rt.governance.create_actor(
        "HUMAN",
        "v085-manual-approver",
        ["human_approver"],
        [project],
    )
    password = secrets.token_urlsafe(20)
    username = "v085-manual-approver"
    rt.auth.register_human(human, username, password)
    token = rt.auth.authenticate(
        username,
        password,
        client_metadata={"client": "v085-multi-normative-test"},
    )

    orch = ResearchOrchestrator(rt, actors)
    result = orch.start(project, DeterministicResearchExecutor("pass"))
    approvals = 0
    safety = 0
    while result["status"] == "PAUSED":
        safety += 1
        assert safety < 80, result
        assert result["reason"] in {
            "WAITING_APPROVAL",
            "WAITING_HUMAN_CONFIRMATION",
        }, result
        proposal = rt.db.one(
            "SELECT * FROM proposals WHERE project_id=? AND status='PENDING_APPROVAL' "
            "ORDER BY created_at DESC LIMIT 1",
            (project,),
        )
        assert proposal is not None, result
        rt.governance.approve_proposal_authenticated(
            proposal["proposal_id"],
            token,
            proposal["payload_hash"],
        )
        approvals += 1
        result = orch.resume(
            result["checkpoint_id"],
            DeterministicResearchExecutor("pass"),
        )

    assert result["status"] == "COMPLETED"
    assert result["outcome"] == "PASS"
    assert approvals >= 2

    for artifact_type in ("protocol", "study_lock"):
        count = rt.db.one(
            "SELECT COUNT(*) n FROM revisions r "
            "JOIN artifacts a ON a.artifact_id=r.artifact_id "
            "WHERE a.project_id=? AND a.artifact_type=?",
            (project, artifact_type),
        )["n"]
        assert int(count) == 1, artifact_type

    phase04 = rt.db.all(
        "SELECT status FROM phase_executions "
        "WHERE orchestration_id=? AND phase_id='phase_04_design_protocol' "
        "ORDER BY started_at",
        (result["orchestration_id"],),
    )
    assert [row["status"] for row in phase04].count("SUCCEEDED") == 1
    assert len(phase04) >= 3
    rt.auth.revoke(token)
    rt.close()


def test_software_domain_runs_governed_linear_delivery_end_to_end(tmp_path):
    domain_path = ROOT / "domains" / "software.workflow.yaml"
    report = DomainSDK.validate(domain_path)
    assert report.ok, report.to_dict()

    rt = GovernedWorkflowRuntime(str(domain_path), str(tmp_path / "software-v085.db"))
    assert rt.domain.domain_id == "software.delivery"
    assert rt.domain.data["orchestration_mode"] == "linear"

    phases = rt.domain.workunits()
    assert [p["id"] for p in phases] == [
        "phase_00_audit_baseline",
        "phase_01_lock_scope",
        "phase_02_plan_change",
        "phase_03_implement",
        "phase_04_local_verify",
        "phase_05_integration_regression",
        "phase_06_independent_qa",
        "phase_07_candidate_verify",
        "phase_08_merge_candidate",
        "phase_09_exact_main_verify",
        "phase_10_release_handoff",
    ]

    project = rt.create_project("software-v085")
    roles = sorted({w["executor_role"] for w in phases})
    actors = _actors(rt, project, roles)
    human = rt.governance.create_actor(
        "HUMAN",
        "v085-software-human",
        ["human_approver"],
        [project],
    )
    orch = LinearDomainOrchestrator(rt, actors, human_approver_id=human)
    result = orch.start(project, DeterministicSoftwareExecutor())
    assert result["status"] == "COMPLETED"
    assert result["domain_id"] == "software.delivery"

    succeeded = rt.db.all(
        "SELECT * FROM phase_executions WHERE orchestration_id=? AND status='SUCCEEDED' ORDER BY phase_index",
        (result["orchestration_id"],),
    )
    assert len(succeeded) == len(phases)
    for phase in succeeded:
        protocol = rt.db.one(
            "SELECT * FROM phase_execution_protocols WHERE phase_execution_id=?",
            (phase["phase_execution_id"],),
        )
        assert protocol is not None
        assert protocol["status"] == "COMPLETED"
        assert protocol["current_stage"] == "COMPLETE"
        handoff = rt.db.one(
            "SELECT * FROM phase_handoffs WHERE phase_execution_id=?",
            (phase["phase_execution_id"],),
        )
        assert handoff is not None

    exact_main = rt.db.one(
        "SELECT current_revision_id FROM artifacts WHERE project_id=? AND artifact_type='exact_main_verification'",
        (project,),
    )
    assert exact_main and exact_main["current_revision_id"]
    payload = rt.knowledge.get_revision(exact_main["current_revision_id"])[
        "structured_payload"
    ]
    assert payload["all_required_pass"] is True

    handoff = rt.db.one(
        "SELECT current_revision_id FROM artifacts WHERE project_id=? AND artifact_type='handoff_package'",
        (project,),
    )
    assert handoff and handoff["current_revision_id"]
    rt.close()


def test_example_domain_remains_scaffold_not_software_package():
    example = DomainSDK.validate(ROOT / "domains" / "example.workflow.yaml")
    assert example.ok
    inspected = DomainSDK.inspect(ROOT / "domains" / "example.workflow.yaml")
    assert inspected["domain_id"] != "software.delivery"


def test_pilot_profiles_validate_and_preserve_feature_branch_boundary():
    for profile in (
        ROOT / "pilots" / "cqg.research.yaml",
        ROOT / "pilots" / "gwf.self-upgrade.yaml",
    ):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "gwr_pilot.py"), "validate", str(profile)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert proc.returncode == 0, proc.stdout
        text = profile.read_text(encoding="utf-8")
        assert "baseline_policy: RESOLVE_AT_START" in text
        assert "write_policy: FEATURE_BRANCH_ONLY" in text
        assert "direct_main_write: false" in text


def test_install_script_is_one_click_full_qualification_by_default():
    script = (ROOT / "install.ps1").read_text(encoding="utf-8")
    assert '"pip", "install", "-e", ".[dev,postgres]"' in script
    assert '"tools/gwr_domain.py", "validate", "domains/research.workflow.yaml"' in script
    assert '"tools/gwr_domain.py", "validate", "domains/software.workflow.yaml"' in script
    assert '"tools/gwr_pilot.py", "validate", "pilots/cqg.research.yaml"' in script
    assert '"tools/gwr_pilot.py", "validate", "pilots/gwf.self-upgrade.yaml"' in script
    assert '"-m", "pytest", "-q"' in script
    assert "install-report.json" in script
    assert "dsn_persisted = $false" in script


def test_v085_product_meta_advertises_domain_and_install_capabilities(tmp_path):
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "software.workflow.yaml"),
        str(tmp_path / "v085-meta.db"),
    )
    client = TestClient(create_app(rt))
    meta = client.get("/product/meta")
    assert meta.status_code == 200
    payload = meta.json()
    assert tuple(map(int, payload["version"].split("."))) >= (0, 8, 5)
    for capability in (
        "research_study_lock",
        "software_delivery_domain",
        "linear_domain_orchestration",
        "pilot_profiles",
        "one_click_windows_install",
    ):
        assert capability in payload["capabilities"]
    rt.close()
