from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.errors import AuthorityDenied
from gwr.product import ProjectDashboardService
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import canonical_json, uid


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
PASSWORD = "recovery-browser-password"
VIEWER_PASSWORD = "recovery-viewer-password"


def _runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "research.workflow.yaml"),
        str(tmp_path / "bps-recovery.db"),
        auth_secret="r" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
    )
    human = rt.governance.create_actor(
        "HUMAN", "recovery-human", ["human_approver"], []
    )
    viewer = rt.governance.create_actor(
        "HUMAN", "recovery-viewer", [], []
    )
    agent = rt.governance.create_actor(
        "AGENT", "recovery-agent", ["research_lead"], []
    )
    rt.auth.register_human(human, "recovery-human", PASSWORD)
    rt.auth.register_human(viewer, "recovery-viewer", VIEWER_PASSWORD)

    tenant = rt.tenancy.create_tenant(
        "Recovery Tenant", human, tenant_id="tenant_recovery"
    )
    workspace = rt.tenancy.create_workspace(
        tenant, "Recovery Workspace", human, workspace_id="workspace_recovery"
    )
    project = rt.create_scoped_project(
        "Recovery Project",
        tenant,
        workspace,
        human,
        project_id="project_recovery",
    )
    rt.tenancy.add_project_member(project, human, "APPROVER", human)
    rt.tenancy.add_project_member(project, viewer, "VIEWER", human)
    rt.tenancy.add_project_member(project, agent, "RESEARCHER", human)

    second_project = rt.create_scoped_project(
        "Recovery Project B",
        tenant,
        workspace,
        human,
        project_id="project_recovery_b",
    )
    rt.tenancy.add_project_member(second_project, human, "APPROVER", human)
    return rt, human, viewer, agent, project, second_project


def _app(rt):
    return create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "test-version",
            "build_sha": "recovery-build-sha",
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "canonical",
        },
        web_root=WEB,
    )


def _browser_login(client, username="recovery-human", password=PASSWORD):
    response = client.post(
        "/browser/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200


def _bearer_login(client):
    response = client.post(
        "/auth/login",
        json={"username": "recovery-human", "password": PASSWORD},
    )
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def _phase(rt, project, *, suffix="main"):
    orchestration_id = f"orch_recovery_{suffix}_{uid('x')}"
    phase_id = f"phase_recovery_{suffix}_{uid('x')}"
    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            orchestration_id,
            project,
            rt.domain.domain_id,
            "RUNNING",
            "phase_09_main_experiment",
            0,
            None,
            0,
            "2026-09-26T10:00:00+00:00",
            "2026-09-26T10:00:00+00:00",
            None,
            "{}",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            phase_id,
            orchestration_id,
            "phase_09_main_experiment",
            9,
            0,
            None,
            None,
            "RUNNING",
            None,
            None,
            None,
            "2026-09-26T10:00:01+00:00",
            None,
            "{}",
        ),
    )
    rt.db.conn.commit()
    return phase_id


def _skill(rt, agent):
    package = rt.agent_protocol.create_skill_package(
        "bps-recovery-skill-" + uid("s"),
        "BPS Recovery Skill",
        agent,
    )
    return rt.agent_protocol.add_skill_revision(
        package,
        "1.0.0",
        "# BPS Recovery\nExecute, verify, recover, handoff.",
        agent,
        tool_requirements=["python"],
        qa_contract={"requires_evidence": True},
    )


def _waiting_proposal(rt, human, agent, project, *, suffix="main"):
    phase = _phase(rt, project, suffix=suffix)
    skill = _skill(rt, agent)
    rt.agent_protocol.create_protocol(
        phase,
        skill,
        agent,
        recovery_mode="HUMAN_APPROVE",
        retry_budget=2,
    )
    rt.agent_protocol.record_preflight(
        phase, [{"name": "ready", "pass": True}], agent
    )
    rt.agent_protocol.create_plan(
        phase,
        "Execute governed recovery test",
        [{"title": "Risky step"}],
        agent,
    )
    rt.agent_protocol.start_execution(phase, agent)
    rt.agent_protocol.update_step(phase, 1, "FAIL", agent)
    problem_id = rt.agent_protocol.record_problem(
        phase,
        agent,
        code="BPS_RECOVERY_TEST",
        summary="Human decision required",
        detail="Persisted test problem",
        affected_step=1,
        severity="HIGH",
    )
    proposal = rt.agent_protocol.propose_recovery(
        problem_id,
        agent,
        action="REPLAN",
        target_step=1,
        rationale="Use a controlled revised plan",
        risk_class="MEDIUM",
        normative_change=False,
    )
    assert proposal["status"] == "WAITING_HUMAN"
    return phase, problem_id, proposal["proposal_id"]


def _decision_path(project, phase, proposal):
    return (
        f"/browser/projects/{project}/execution/phases/{phase}"
        f"/recovery-proposals/{proposal}/decision"
    )


@pytest.mark.parametrize(
    ("decision", "expected_proposal", "expected_protocol"),
    [
        ("APPROVED", "HUMAN_APPROVED", "RUNNING"),
        ("REJECTED", "REJECTED", "BLOCKED"),
    ],
)
def test_browser_recovery_decision_mutates_only_qualified_human_transition(
    tmp_path, monkeypatch, decision, expected_proposal, expected_protocol
):
    rt, human, _, agent, project, _ = _runtime(tmp_path, monkeypatch)
    phase, _, proposal = _waiting_proposal(rt, human, agent, project)
    client = TestClient(_app(rt))
    _browser_login(client)

    detail = client.get(
        f"/browser/projects/{project}/execution/phases/{phase}"
    )
    assert detail.status_code == 200
    recovery = detail.json()["agent_protocol"]["problems"][0]["recoveries"][0]
    assert recovery["status"] == "WAITING_HUMAN"
    assert recovery["decision_capability"] == {
        "authority": "HUMAN+APPROVE",
        "can_decide": True,
        "allowed_decisions": ["APPROVED", "REJECTED"],
    }

    reason = "Browser operator exact decision"
    response = client.post(
        _decision_path(project, phase, proposal),
        json={"decision": decision, "reason": reason},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project
    assert body["phase_execution_id"] == phase
    assert body["proposal_id"] == proposal
    assert body["decision"] == decision
    assert body["proposal_status"] == expected_proposal
    assert body["protocol_status"] == expected_protocol

    row = rt.db.one(
        "SELECT * FROM phase_recovery_decisions WHERE proposal_id=?",
        (proposal,),
    )
    assert row["decision_id"] == body["decision_id"]
    assert row["actor_id"] == human
    assert row["decision"] == decision
    assert row["reason"] == reason

    refreshed = client.get(
        f"/browser/projects/{project}/execution/phases/{phase}"
    ).json()
    decided = refreshed["agent_protocol"]["problems"][0]["recoveries"][0]
    assert decided["status"] == expected_proposal
    assert decided["decision_capability"]["can_decide"] is False
    assert decided["decision_capability"]["allowed_decisions"] == []
    assert len(decided["decisions"]) == 1
    rt.close()


def test_browser_recovery_decision_denies_viewer_and_capability_is_false(
    tmp_path, monkeypatch
):
    rt, human, viewer, agent, project, _ = _runtime(tmp_path, monkeypatch)
    phase, _, proposal = _waiting_proposal(rt, human, agent, project)
    client = TestClient(_app(rt))
    _browser_login(client, "recovery-viewer", VIEWER_PASSWORD)

    detail = client.get(
        f"/browser/projects/{project}/execution/phases/{phase}"
    )
    assert detail.status_code == 200
    capability = (
        detail.json()["agent_protocol"]["problems"][0]["recoveries"][0]
        ["decision_capability"]
    )
    assert capability["authority"] == "HUMAN+APPROVE"
    assert capability["can_decide"] is False
    assert capability["allowed_decisions"] == []

    response = client.post(
        _decision_path(project, phase, proposal),
        json={"decision": "APPROVED", "reason": ""},
    )
    assert response.status_code == 403
    assert rt.db.one(
        "SELECT COUNT(*) n FROM phase_recovery_decisions WHERE proposal_id=?",
        (proposal,),
    )["n"] == 0
    assert rt.db.one(
        "SELECT status FROM phase_recovery_proposals WHERE proposal_id=?",
        (proposal,),
    )["status"] == "WAITING_HUMAN"
    rt.close()


def test_nonhuman_actor_cannot_decide_and_projection_does_not_offer_action(
    tmp_path, monkeypatch
):
    rt, human, _, agent, project, _ = _runtime(tmp_path, monkeypatch)
    phase, _, proposal = _waiting_proposal(rt, human, agent, project)

    detail = ProjectDashboardService(rt).project_phase_execution(
        agent,
        project,
        phase,
        build_sha="recovery-build-sha",
    )
    capability = (
        detail["agent_protocol"]["problems"][0]["recoveries"][0]
        ["decision_capability"]
    )
    assert capability["can_decide"] is False
    assert capability["allowed_decisions"] == []
    with pytest.raises(AuthorityDenied):
        rt.agent_protocol.decide_recovery(
            proposal, agent, "APPROVED", reason="not human"
        )
    rt.close()


def test_browser_recovery_decision_rejects_cross_phase_and_cross_project_binding(
    tmp_path, monkeypatch
):
    rt, human, _, agent, project, second_project = _runtime(tmp_path, monkeypatch)
    phase, _, proposal = _waiting_proposal(rt, human, agent, project)
    other_phase = _phase(rt, project, suffix="other-phase")
    second_phase = _phase(rt, second_project, suffix="other-project")

    client = TestClient(_app(rt))
    _browser_login(client)

    cross_phase = client.post(
        _decision_path(project, other_phase, proposal),
        json={"decision": "APPROVED", "reason": ""},
    )
    assert cross_phase.status_code == 404

    cross_project = client.post(
        _decision_path(second_project, second_phase, proposal),
        json={"decision": "APPROVED", "reason": ""},
    )
    assert cross_project.status_code == 404

    assert rt.db.one(
        "SELECT COUNT(*) n FROM phase_recovery_decisions WHERE proposal_id=?",
        (proposal,),
    )["n"] == 0
    assert rt.db.one(
        "SELECT status FROM phase_recovery_proposals WHERE proposal_id=?",
        (proposal,),
    )["status"] == "WAITING_HUMAN"
    rt.close()


def test_browser_recovery_decision_replay_and_invalid_value_do_not_duplicate(
    tmp_path, monkeypatch
):
    rt, human, _, agent, project, _ = _runtime(tmp_path, monkeypatch)
    phase, _, proposal = _waiting_proposal(rt, human, agent, project)
    client = TestClient(_app(rt))
    _browser_login(client)

    invalid = client.post(
        _decision_path(project, phase, proposal),
        json={"decision": "MAYBE", "reason": "invalid"},
    )
    assert invalid.status_code == 422
    assert rt.db.one(
        "SELECT status FROM phase_recovery_proposals WHERE proposal_id=?",
        (proposal,),
    )["status"] == "WAITING_HUMAN"

    first = client.post(
        _decision_path(project, phase, proposal),
        json={"decision": "APPROVED", "reason": ""},
    )
    assert first.status_code == 200

    replay = client.post(
        _decision_path(project, phase, proposal),
        json={"decision": "REJECTED", "reason": "too late"},
    )
    assert replay.status_code == 400
    assert rt.db.one(
        "SELECT COUNT(*) n FROM phase_recovery_decisions WHERE proposal_id=?",
        (proposal,),
    )["n"] == 1
    assert rt.db.one(
        "SELECT status FROM phase_recovery_proposals WHERE proposal_id=?",
        (proposal,),
    )["status"] == "HUMAN_APPROVED"
    rt.close()


def test_existing_bearer_recovery_decision_route_remains_compatible(
    tmp_path, monkeypatch
):
    rt, human, _, agent, project, _ = _runtime(tmp_path, monkeypatch)
    _, _, proposal = _waiting_proposal(rt, human, agent, project)
    client = TestClient(_app(rt))
    headers = _bearer_login(client)

    response = client.post(
        f"/product/recovery-proposals/{proposal}/decision",
        headers=headers,
        json={"decision": "APPROVED", "reason": "Bearer compatibility"},
    )
    assert response.status_code == 200
    assert response.json()["proposal_id"] == proposal
    assert response.json()["decision"] == "APPROVED"
    assert rt.db.one(
        "SELECT status FROM phase_recovery_proposals WHERE proposal_id=?",
        (proposal,),
    )["status"] == "HUMAN_APPROVED"
    rt.close()
