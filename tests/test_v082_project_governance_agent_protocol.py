from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.errors import AuthorityDenied, InvalidTransition
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import canonical_json, uid

ROOT = Path(__file__).parents[1]


def make_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1000)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "research.workflow.yaml"),
        str(tmp_path / "v082.db"),
        auth_secret="v" * 64,
    )
    human = rt.governance.create_actor("HUMAN", "owner-v082", ["human_approver"], [])
    rt.auth.register_human(human, "owner-v082", "owner-v082-password")
    tenant = rt.tenancy.create_tenant("Agent Lab", human)
    workspace = rt.tenancy.create_workspace(tenant, "Execution", human)
    project = rt.create_scoped_project("Observable Project", tenant, workspace, human)
    rt.tenancy.add_project_member(project, human, "APPROVER", human)
    agent = rt.governance.create_actor("AGENT", "agent-v082", ["research_lead"], [])
    rt.tenancy.add_project_member(project, agent, "RESEARCHER", human)
    return rt, human, agent, tenant, workspace, project


def add_phase(rt, project, status="RUNNING"):
    oid = uid("orch")
    peid = uid("phaseexec")
    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (oid, project, rt.domain.domain_id, status, "phase_09_main_experiment", 0, None, 0,
         "2026-09-18T05:00:00+00:00", "2026-09-18T05:00:00+00:00", None, "{}"),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (peid, oid, "phase_09_main_experiment", 9, 0, None, None, "RUNNING", None, None, None,
         "2026-09-18T05:00:00+00:00", None, "{}"),
    )
    rt.db.conn.commit()
    return oid, peid


def skill_revision(rt, actor):
    pkg = rt.agent_protocol.create_skill_package("experiment-execution", "Experiment Execution", actor)
    return rt.agent_protocol.add_skill_revision(
        pkg, "1.0.0",
        "# Experiment Execution\nLoad inputs, verify environment, execute plan, persist evidence, QA, handoff.",
        actor,
        tool_requirements=["python"],
        qa_contract={"requires_evidence": True},
    )


def login(client):
    r = client.post("/auth/login", json={"username": "owner-v082", "password": "owner-v082-password"})
    assert r.status_code == 200
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def test_v082_migration_installs_governance_and_protocol_tables(tmp_path, monkeypatch):
    rt, *_ = make_runtime(tmp_path, monkeypatch)
    expected = {
        "project_lifecycle", "project_name_history", "skill_packages", "skill_revisions",
        "phase_execution_protocols", "phase_preflights", "phase_plans",
        "phase_checklist_items", "phase_stage_events", "phase_problem_records",
        "phase_recovery_proposals", "phase_recovery_decisions", "phase_handoffs",
    }
    assert expected.issubset(set(rt.db.list_tables()))
    assert "0005_v082_project_governance_agent_protocol" in rt.db.migrations.status()["applied"]
    rt.close()


def test_project_rename_archive_restore_and_read_only_guard(tmp_path, monkeypatch):
    rt, human, agent, _, _, project = make_runtime(tmp_path, monkeypatch)
    renamed = rt.project_governance.rename(project, "Renamed Research Project", human)
    assert renamed["old_name"] == "Observable Project"
    assert rt.db.one("SELECT name FROM projects WHERE id=?", (project,))["name"] == "Renamed Research Project"
    assert rt.project_governance.name_history(project)[0]["new_name"] == "Renamed Research Project"

    archived = rt.project_governance.archive(project, human, reason="UAT archive")
    assert archived["status"] == "ARCHIVED"
    with pytest.raises(InvalidTransition):
        rt.governance.prepare_system_proposal(project, "CONFIRM_ROOT", [], {"x": 1}, "human_recovery_confirmation")

    restored = rt.project_governance.restore(project, human)
    assert restored["status"] == "ACTIVE"
    proposal = rt.governance.prepare_system_proposal(project, "CONFIRM_ROOT", [], {"x": 2}, "human_recovery_confirmation")
    assert proposal
    rt.close()


def test_archive_requires_drain_when_project_has_active_orchestration(tmp_path, monkeypatch):
    rt, human, _, _, _, project = make_runtime(tmp_path, monkeypatch)
    oid, _ = add_phase(rt, project)
    with pytest.raises(InvalidTransition):
        rt.project_governance.archive(project, human)
    result = rt.project_governance.archive(project, human, drain=True)
    assert result["status"] == "ARCHIVING"
    with pytest.raises(InvalidTransition):
        rt.project_governance.require_mutable(project)
    rt.db.conn.execute("UPDATE orchestrations SET status='COMPLETED' WHERE orchestration_id=?", (oid,))
    rt.db.conn.commit()
    assert rt.project_governance.refresh_archive(project)["status"] == "ARCHIVED"
    rt.close()


def test_auto_mode_records_problem_before_retry_and_completes_protocol(tmp_path, monkeypatch):
    rt, human, agent, _, _, project = make_runtime(tmp_path, monkeypatch)
    _, phase = add_phase(rt, project)
    skill = skill_revision(rt, agent)
    rt.agent_protocol.create_protocol(phase, skill, agent, recovery_mode="AUTO", retry_budget=2)

    with pytest.raises(InvalidTransition):
        rt.agent_protocol.create_plan(phase, "Run experiment", [{"title": "Execute"}], agent)

    pf = rt.agent_protocol.record_preflight(
        phase,
        [
            {"name": "skill_loaded", "pass": True},
            {"name": "inputs_valid", "pass": True},
            {"name": "worker_available", "pass": True},
        ],
        agent,
    )
    assert pf["status"] == "PASS"
    rt.agent_protocol.create_plan(
        phase, "Run controlled experiment",
        [{"title": "Resolve inputs"}, {"title": "Run treatment"}, {"title": "Persist evidence"}],
        agent,
    )
    rt.agent_protocol.start_execution(phase, agent)
    rt.agent_protocol.update_step(phase, 1, "PASS", agent, note="inputs locked")
    rt.agent_protocol.update_step(phase, 2, "FAIL", agent, note="worker timeout")

    problem = rt.agent_protocol.record_problem(
        phase, agent, code="WORKER_TIMEOUT", summary="Worker timed out", detail="lease was lost", affected_step=2
    )
    recovery = rt.agent_protocol.propose_recovery(
        problem, agent, action="RETRY_STEP", target_step=2, rationale="Retry on healthy worker", risk_class="LOW"
    )
    assert recovery["status"] == "AUTO_APPROVED"
    rt.agent_protocol.apply_recovery(recovery["proposal_id"], agent)

    rt.agent_protocol.update_step(phase, 2, "PASS", agent, note="retry succeeded")
    rt.agent_protocol.update_step(phase, 3, "PASS", agent, note="evidence persisted")
    assert rt.agent_protocol.verify(phase, agent, qa_result="PASS")["status"] == "PASS"
    handoff = rt.agent_protocol.write_handoff(
        phase, agent,
        {"what_was_done": "Experiment completed after recorded retry.", "next_phase": "phase_10_analysis",
         "artifact_refs": ["experiment_result"], "evidence_refs": ["runtime_evidence"]},
    )
    assert handoff
    rt.agent_protocol.complete(phase, agent)
    view = rt.agent_protocol.inspect(phase)
    assert view["attention"] == "COMPLETE"
    assert view["protocol"]["retry_count"] == 1
    assert view["problems"][0]["status"] == "RECOVERY_APPLIED"
    events = [e["event_type"] for e in view["events"]]
    assert events.index("PROBLEM_RECORDED") < events.index("RECOVERY_APPLIED")
    rt.close()


def test_human_mode_pauses_before_recovery_and_requires_human_decision(tmp_path, monkeypatch):
    rt, human, agent, _, _, project = make_runtime(tmp_path, monkeypatch)
    _, phase = add_phase(rt, project)
    skill = skill_revision(rt, agent)
    rt.agent_protocol.create_protocol(phase, skill, agent, recovery_mode="HUMAN_APPROVE", retry_budget=2)
    rt.agent_protocol.record_preflight(phase, [{"name": "ready", "pass": True}], agent)
    rt.agent_protocol.create_plan(phase, "Execute", [{"title": "Risky step"}], agent)
    rt.agent_protocol.start_execution(phase, agent)
    rt.agent_protocol.update_step(phase, 1, "FAIL", agent)
    problem = rt.agent_protocol.record_problem(
        phase, agent, code="SCHEMA_MISMATCH", summary="Schema changed", detail="requires replan", affected_step=1
    )
    proposal = rt.agent_protocol.propose_recovery(
        problem, agent, action="REPLAN", target_step=1, rationale="Normalize schema then retry",
        risk_class="MEDIUM", normative_change=False,
    )
    assert proposal["status"] == "WAITING_HUMAN"
    assert rt.agent_protocol.inspect(phase)["attention"] == "WAITING_FOR_YOU"
    with pytest.raises(InvalidTransition):
        rt.agent_protocol.apply_recovery(proposal["proposal_id"], agent)
    with pytest.raises(AuthorityDenied):
        rt.agent_protocol.decide_recovery(proposal["proposal_id"], agent, "APPROVED")

    rt.agent_protocol.decide_recovery(proposal["proposal_id"], human, "APPROVED", reason="Proceed with controlled retry")
    applied = rt.agent_protocol.apply_recovery(proposal["proposal_id"], agent)
    assert applied["status"] == "APPLIED"
    assert rt.agent_protocol.inspect(phase)["protocol"]["retry_count"] == 1
    rt.close()


def test_qa_and_handoff_are_hard_gates(tmp_path, monkeypatch):
    rt, _, agent, _, _, project = make_runtime(tmp_path, monkeypatch)
    _, phase = add_phase(rt, project)
    skill = skill_revision(rt, agent)
    rt.agent_protocol.create_protocol(phase, skill, agent)
    rt.agent_protocol.record_preflight(phase, [{"name": "ready", "pass": True}], agent)
    rt.agent_protocol.create_plan(phase, "Execute", [{"title": "A"}, {"title": "B"}], agent)
    rt.agent_protocol.start_execution(phase, agent)
    rt.agent_protocol.update_step(phase, 1, "PASS", agent)
    with pytest.raises(InvalidTransition):
        rt.agent_protocol.verify(phase, agent, qa_result="PASS")
    with pytest.raises(InvalidTransition):
        rt.agent_protocol.write_handoff(phase, agent, {"what_was_done": "too early"})
    with pytest.raises(InvalidTransition):
        rt.agent_protocol.complete(phase, agent)
    rt.close()


def test_v082_api_project_governance_and_protocol_inspection(tmp_path, monkeypatch):
    rt, human, agent, _, _, project = make_runtime(tmp_path, monkeypatch)
    _, phase = add_phase(rt, project)
    skill = skill_revision(rt, agent)
    rt.agent_protocol.create_protocol(phase, skill, agent, recovery_mode="AUTO")
    rt.agent_protocol.record_preflight(phase, [{"name": "ready", "pass": True}], agent)
    rt.agent_protocol.create_plan(phase, "API plan", [{"title": "Step one"}], agent)
    rt.agent_protocol.start_execution(phase, agent)

    client = TestClient(create_app(rt))
    auth = login(client)
    renamed = client.patch(f"/product/projects/{project}", headers=auth, json={"name": "API Renamed"})
    assert renamed.status_code == 200
    lifecycle = client.get(f"/product/projects/{project}/lifecycle", headers=auth)
    assert lifecycle.status_code == 200
    assert lifecycle.json()["name_history"][0]["new_name"] == "API Renamed"
    protocol = client.get(f"/product/phases/{phase}/agent-protocol", headers=auth)
    assert protocol.status_code == 200
    assert protocol.json()["attention"] == "AI_WORKING"
    assert protocol.json()["protocol"]["current_stage"] == "EXECUTE"
    rt.close()
