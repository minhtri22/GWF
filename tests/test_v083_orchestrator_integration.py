from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.errors import InvalidTransition
from gwr.research_demo import DeterministicResearchExecutor
from gwr.research_orchestrator import ResearchOrchestrator
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import parse_json


ROOT = Path(__file__).parents[1]
ROLES = [
    "research_lead",
    "literature_reviewer",
    "protocol_designer",
    "experimenter",
    "analyst",
    "adversarial_reviewer",
    "reproducibility_reviewer",
]


def make_runtime(tmp_path, scenario="pass"):
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "research.workflow.yaml"),
        str(tmp_path / f"v083-{scenario}.db"),
    )
    project = rt.create_project(f"v083-{scenario}")
    actors = {
        role: rt.governance.create_actor("AGENT", f"{role}-{scenario}", [role], [project])
        for role in ROLES
    }
    human = rt.governance.create_actor("HUMAN", f"human-{scenario}", ["human_approver"], [project])
    return rt, project, actors, human, ResearchOrchestrator(rt, actors, human_approver_id=human)


def test_runtime_bootstraps_exact_domain_skill_bindings(tmp_path):
    rt, *_ = make_runtime(tmp_path)
    bindings = rt.db.all(
        "SELECT * FROM domain_skill_bindings WHERE domain_id=? ORDER BY workunit_type",
        (rt.domain.domain_id,),
    )
    assert len(bindings) == len(rt.domain.workunits()) == 17
    for workunit in rt.domain.workunits():
        resolved = rt.agent_protocol.resolve_skill_revision(workunit["id"])
        assert resolved["skill_revision_id"]
        assert resolved["skill_hash"]
        skill_ref = workunit["skill_ref"]
        assert resolved["version"] == rt.domain.data["skill_contracts"][skill_ref]["version"]
        assert rt.db.one(
            "SELECT content_hash FROM skill_revisions WHERE skill_revision_id=?",
            (resolved["skill_revision_id"],),
        )["content_hash"] == resolved["skill_hash"]
    rt.close()


def test_pass_orchestration_is_protocol_driven_and_handoff_chained(tmp_path):
    rt, project, _, _, orch = make_runtime(tmp_path, "pass")
    result = orch.start(project, DeterministicResearchExecutor("pass"))
    assert result["status"] == "COMPLETED"
    assert result["outcome"] == "PASS"

    succeeded = rt.db.all(
        "SELECT * FROM phase_executions WHERE orchestration_id=? AND status='SUCCEEDED' ORDER BY generation,phase_index,started_at",
        (result["orchestration_id"],),
    )
    assert succeeded
    for phase in succeeded:
        protocol = rt.db.one(
            "SELECT * FROM phase_execution_protocols WHERE phase_execution_id=?",
            (phase["phase_execution_id"],),
        )
        assert protocol is not None
        assert protocol["status"] == "COMPLETED"
        assert protocol["current_stage"] == "COMPLETE"
        binding = rt.agent_protocol.resolve_skill_revision(phase["phase_id"])
        assert protocol["skill_revision_id"] == binding["skill_revision_id"]
        assert protocol["skill_hash"] == binding["skill_hash"]

        link = rt.db.one(
            "SELECT * FROM phase_handoff_links WHERE phase_execution_id=?",
            (phase["phase_execution_id"],),
        )
        assert link is not None
        if int(phase["phase_index"]) == 0:
            assert link["previous_phase_execution_id"] is None
            assert link["previous_handoff_id"] is None
        else:
            assert link["previous_phase_execution_id"]
            assert link["previous_handoff_id"]
            handoff = rt.db.one("SELECT * FROM phase_handoffs WHERE handoff_id=?", (link["previous_handoff_id"],))
            assert handoff["payload_hash"] == link["handoff_hash"]

        events = [
            x["event_type"]
            for x in rt.db.all(
                "SELECT * FROM phase_stage_events WHERE phase_execution_id=? ORDER BY created_at,event_id",
                (phase["phase_execution_id"],),
            )
        ]
        for expected in (
            "SKILL_LOADED",
            "PREFLIGHT_PASS",
            "PLAN_FROZEN",
            "EXECUTION_STARTED",
            "QA_PASS",
            "HANDOFF_WRITTEN",
            "PROTOCOL_COMPLETED",
        ):
            assert expected in events
    rt.close()


def test_auto_retry_records_problem_before_recovery_and_closes_failed_attempt(tmp_path):
    rt, project, _, _, orch = make_runtime(tmp_path, "runtime_retry")
    result = orch.start(project, DeterministicResearchExecutor("runtime_retry"))
    assert result["status"] == "COMPLETED"
    attempts = rt.db.all(
        "SELECT p.* FROM phase_executions p WHERE p.orchestration_id=? AND p.phase_id='phase_09_main_experiment' ORDER BY p.started_at,p.phase_execution_id",
        (result["orchestration_id"],),
    )
    assert len(attempts) == 2
    assert [x["status"] for x in attempts] == ["FAILED", "SUCCEEDED"]

    failed_view = rt.agent_protocol.inspect(attempts[0]["phase_execution_id"])
    assert failed_view["protocol"]["status"] == "FAILED"
    assert failed_view["attention"] == "FAIL"
    event_types = [x["event_type"] for x in failed_view["events"]]
    assert event_types.index("PROBLEM_RECORDED") < event_types.index("RECOVERY_APPLIED")
    assert event_types.index("RECOVERY_APPLIED") < event_types.index("ATTEMPT_FAILED")

    passed_view = rt.agent_protocol.inspect(attempts[1]["phase_execution_id"])
    assert passed_view["protocol"]["status"] == "COMPLETED"
    rt.close()


def test_human_recovery_pauses_before_retry_and_resume_keeps_logical_attempt(tmp_path):
    rt, project, _, human, orch = make_runtime(tmp_path, "runtime_retry-human")
    rt.agent_protocol.set_project_defaults(project, "SYSTEM", recovery_mode="HUMAN_APPROVE", retry_budget=2)

    first = orch.start(project, DeterministicResearchExecutor("runtime_retry"))
    assert first["status"] == "PAUSED"
    assert first["reason"] == "WAITING_PROTOCOL_RECOVERY"

    proposal = rt.db.one(
        "SELECT * FROM phase_recovery_proposals WHERE status='WAITING_HUMAN' ORDER BY created_at DESC LIMIT 1"
    )
    assert proposal is not None
    failed_phase = rt.db.one(
        "SELECT * FROM phase_executions WHERE orchestration_id=? AND phase_id='phase_09_main_experiment' ORDER BY started_at DESC LIMIT 1",
        (first["orchestration_id"],),
    )
    waiting = rt.agent_protocol.inspect(failed_phase["phase_execution_id"])
    assert waiting["attention"] == "WAITING_FOR_YOU"
    assert "PROBLEM_RECORDED" in [x["event_type"] for x in waiting["events"]]

    rt.agent_protocol.decide_recovery(proposal["proposal_id"], human, "APPROVED", reason="controlled retry")
    resumed = orch.resume(first["checkpoint_id"], DeterministicResearchExecutor("runtime_retry"), max_steps=100)
    assert resumed["status"] == "COMPLETED"
    assert resumed["outcome"] == "PASS"

    attempt_evidence = []
    for row in rt.db.all(
        "SELECT structured_payload FROM evidence WHERE project_id=? AND evidence_type='raw_metrics_evidence'",
        (project,),
    ):
        payload = parse_json(row["structured_payload"], {})
        if payload.get("phase") == "phase_09_main_experiment":
            attempt_evidence.append(payload.get("attempt"))
    assert 2 in attempt_evidence
    rt.close()


def test_domain_minimum_wins_project_or_requested_auto(tmp_path):
    rt, project, *_ = make_runtime(tmp_path, "recovery-hierarchy")
    rt.agent_protocol.set_project_defaults(project, "SYSTEM", recovery_mode="AUTO", retry_budget=5)
    phase = rt.domain.workunit("phase_09_main_experiment")
    phase["agent_protocol"] = {"minimum_recovery_mode": "HUMAN_APPROVE", "retry_budget": 3}
    cfg = rt.agent_protocol.resolve_recovery_config(
        project,
        "phase_09_main_experiment",
        requested_mode="AUTO",
    )
    assert cfg["recovery_mode"] == "HUMAN_APPROVE"
    assert cfg["domain_minimum"] == "HUMAN_APPROVE"
    assert cfg["retry_budget"] == 3
    rt.close()


def test_archived_project_cannot_start_new_orchestration(tmp_path):
    rt, project, _, human, orch = make_runtime(tmp_path, "archive")
    assert rt.project_governance.archive(project, human)["status"] == "ARCHIVED"
    with pytest.raises(InvalidTransition):
        orch.start(project, DeterministicResearchExecutor("pass"))
    rt.close()


def test_live_event_stream_and_project_protocol_settings_api(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1000)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "research.workflow.yaml"),
        str(tmp_path / "v083-api.db"),
        auth_secret="z" * 64,
    )
    human = rt.governance.create_actor("HUMAN", "owner-v083", ["human_approver"], [])
    rt.auth.register_human(human, "owner-v083", "owner-v083-password")
    tenant = rt.tenancy.create_tenant("v083 tenant", human)
    workspace = rt.tenancy.create_workspace(tenant, "v083 workspace", human)
    project = rt.create_scoped_project("v083 live ops", tenant, workspace, human)
    rt.tenancy.add_project_member(project, human, "APPROVER", human)
    actors = {}
    for role in ROLES:
        actor = rt.governance.create_actor("AGENT", f"api-{role}", [role], [])
        rt.tenancy.add_project_member(project, actor, "RESEARCHER", human)
        actors[role] = actor

    orch = ResearchOrchestrator(rt, actors, human_approver_id=human)
    result = orch.start(project, DeterministicResearchExecutor("pass"))
    assert result["status"] == "COMPLETED"
    phase = rt.db.one(
        "SELECT * FROM phase_executions WHERE orchestration_id=? AND status='SUCCEEDED' ORDER BY phase_index LIMIT 1",
        (result["orchestration_id"],),
    )

    client = TestClient(create_app(rt))
    login = client.post("/auth/login", json={"username": "owner-v083", "password": "owner-v083-password"})
    assert login.status_code == 200
    auth = {"Authorization": "Bearer " + login.json()["access_token"]}

    settings = client.put(
        f"/product/projects/{project}/agent-protocol-settings",
        headers=auth,
        json={"recovery_mode": "HUMAN_APPROVE", "retry_budget": 1},
    )
    assert settings.status_code == 200
    assert settings.json()["recovery_mode"] == "HUMAN_APPROVE"
    assert settings.json()["retry_budget"] == 1

    stream = client.get(
        f"/product/phases/{phase['phase_execution_id']}/events/stream?follow=false",
        headers=auth,
    )
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    assert "event: SKILL_LOADED" in stream.text
    assert "event: PROTOCOL_COMPLETED" in stream.text

    meta = client.get("/product/meta")
    assert meta.status_code == 200
    assert tuple(map(int, meta.json()["version"].split("."))) >= (0, 8, 3)
    assert "live_operational_events" in meta.json()["capabilities"]
    rt.close()
