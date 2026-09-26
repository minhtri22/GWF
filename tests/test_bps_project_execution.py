from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.product import ProjectDashboardService
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import canonical_json


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
PASSWORD = "execution-test-password"


def _fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(tmp_path / "project-execution.db"),
        auth_secret="e" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
    )
    owner = rt.governance.create_actor("HUMAN", "execution-owner", [], [])
    outsider = rt.governance.create_actor("HUMAN", "execution-outsider", [], [])
    executor = rt.governance.create_actor("AGENT", "execution-agent", ["operator"], ["project_execution"])
    rt.auth.register_human(owner, "execution-owner", PASSWORD)
    rt.auth.register_human(outsider, "execution-outsider", PASSWORD)

    tenant = rt.tenancy.create_tenant("Execution Tenant", owner, tenant_id="tenant_execution")
    workspace = rt.tenancy.create_workspace(
        tenant, "Execution Workspace", owner, workspace_id="workspace_execution"
    )
    project = rt.create_scoped_project(
        "Execution Project", tenant, workspace, owner, project_id="project_execution"
    )

    hidden_tenant = rt.tenancy.create_tenant(
        "Hidden Execution Tenant", outsider, tenant_id="tenant_execution_hidden"
    )
    hidden_workspace = rt.tenancy.create_workspace(
        hidden_tenant, "Hidden Execution Workspace", outsider,
        workspace_id="workspace_execution_hidden",
    )
    hidden_project = rt.create_scoped_project(
        "Hidden Execution Project", hidden_tenant, hidden_workspace, outsider,
        project_id="project_execution_hidden",
    )
    return rt, owner, outsider, executor, project, hidden_project


def _app(rt):
    return create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "test-version",
            "build_sha": "execution-build-sha",
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "canonical",
        },
        web_root=WEB,
    )


def _login(client, username="execution-owner"):
    response = client.post(
        "/browser/auth/login",
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 200


def _seed_phase(rt, owner, executor, project):
    rt.db.conn.execute(
        "INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "wu_execution", project, "phase_exact",
            canonical_json(["rev_input"]),
            canonical_json([{"artifact_type": "REPORT"}]),
            canonical_json([{"kind": "VALID_INPUT"}]),
            canonical_json(["QUALITY_GATE"]),
            canonical_json(["EXECUTE"]),
            canonical_json({"role": "operator"}),
            canonical_json({"resources": {"cpu": 1}, "required_capabilities": ["python"]}),
            canonical_json({"max_attempts": 2}),
            canonical_json({"mode": "HUMAN_APPROVE"}),
            canonical_json(["dataset:execution"]),
            "RUNNING", 3,
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "run_execution", "wu_execution", 2, executor,
            canonical_json(["rev_input"]),
            "2026-09-26T02:00:00+00:00", None, "RUNNING",
            canonical_json({"worker_exit": "pending"}),
            canonical_json(["rev_pivot_trigger"]),
            canonical_json(["evidence_execution"]),
            "checkpoint_execution", "corr-execution",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "orch_execution", project, rt.domain.domain_id, "RUNNING",
            "phase_exact", 4, "PIVOT", 2,
            "2026-09-26T01:58:00+00:00",
            "2026-09-26T02:05:00+00:00",
            None, canonical_json({
                "persisted": True,
                "history": [
                    {
                        "event": "PIVOT",
                        "target": "REPORT",
                        "checkpoint_id": "checkpoint_pivot_history",
                        "generation": 3,
                    },
                    {
                        "event": "RECOVERY",
                        "failure_id": "failure_execution",
                        "resume_phase": "phase_exact",
                        "checkpoint_id": "checkpoint_execution",
                    },
                ],
            }),
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "phase_execution_previous", "orch_execution", "phase_previous", 6, 3,
            None, None, "SUCCEEDED", "CONTINUE",
            None, None,
            "2026-09-26T01:57:00+00:00",
            "2026-09-26T01:58:00+00:00",
            canonical_json({"attempt": "previous"}),
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "phase_execution_exact", "orch_execution", "phase_exact", 7, 4,
            "wu_execution", "run_execution", "RUNNING", "REPLAN",
            "failure_execution", "checkpoint_execution",
            "2026-09-26T01:59:00+00:00", None,
            canonical_json({"attempt": "exact"}),
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO gates VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            "gate_execution", project, "QUALITY_GATE",
            canonical_json({"workunit_id": "wu_execution"}),
            canonical_json(["rev_input"]),
            canonical_json(["evidence_execution"]),
            "gate-policy-v3", "BLOCKED",
            canonical_json(["QUALITY_THRESHOLD"]),
            canonical_json(["run_execution"]),
            "2026-09-26T02:01:00+00:00",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO decisions VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            "decision_execution", project,
            canonical_json({"workunit_id": "wu_execution"}),
            canonical_json(["gate_execution"]),
            "failure_execution", "REPLAN", "REPORT",
            canonical_json(["RECOVERY_PLAN_CREATED"]),
            "2026-09-26T02:02:00+00:00", owner,
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO failures VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "failure_execution", project, "wu_execution",
            "execution_failure", "VERIFY", "run_execution",
            "rev_input", "gate_execution",
            canonical_json(["evidence_execution"]),
            "rev_input", "rev_input", "CONFIRMED",
            "phase_exact", "HIGH", "signature_execution",
            "RECOVERY_PLANNED", "2026-09-26T02:02:30+00:00", None,
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO recoveries VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "recovery_execution", project, "failure_execution",
            "rev_input", "phase_exact",
            canonical_json(["rev_keep"]),
            canonical_json(["rev_invalidate"]),
            canonical_json(["rev_stale"]),
            canonical_json([{"revision_id": "rev_input", "action": "REVISE"}]),
            canonical_json(["wu_repair"]),
            canonical_json(["gate_retest"]),
            canonical_json(["approval_required"]),
            "AFTER_INVALIDATION", "PLANNED",
            "2026-09-26T02:03:00+00:00",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO loopguards VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            "loop_execution", project, "wu_execution", "signature_execution",
            2, 1, 1, "runtime",
            canonical_json({"same_signature_limit": 2}), "ESCALATE",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO checkpoints VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "checkpoint_execution", project, "failure_execution",
            "2026-09-26T02:03:30+00:00", "phaseevt_execution_1",
            canonical_json(["wu_execution"]),
            canonical_json(["wu_done"]),
            canonical_json(["VERIFY"]),
            canonical_json(["rev_keep"]),
            canonical_json(["rev_input"]),
            canonical_json(["rev_stale"]),
            canonical_json(["failure_execution"]),
            canonical_json(["decision_execution"]),
            canonical_json(["approval_required"]),
            canonical_json(["phase_exact"]),
            canonical_json({"recovery_id": "recovery_execution"}),
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO impacts VALUES(?,?,?,?,?,?,?,?,?)",
        (
            "impact_execution_failure", project, "OPERATIONAL_FAILURE",
            "failure_execution", "rev_input",
            canonical_json([{"revision_id": "rev_stale", "action": "MARK_STALE"}]),
            canonical_json(["OPERATIONAL_FAILURE"]),
            "2026-09-26T02:03:10+00:00", "core-0.1",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO impacts VALUES(?,?,?,?,?,?,?,?,?)",
        (
            "impact_execution_pivot", project, "PIVOT",
            "rev_pivot_trigger", "rev_input",
            canonical_json([{"revision_id": "rev_input", "action": "MARK_DIRTY"}]),
            canonical_json(["PIVOT"]),
            "2026-09-26T02:03:20+00:00", "core-0.1",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO impacts VALUES(?,?,?,?,?,?,?,?,?)",
        (
            "impact_unrelated", project, "PIVOT",
            "some_other_revision", "rev_other",
            canonical_json([]), canonical_json(["PIVOT"]),
            "2026-09-26T02:03:25+00:00", "core-0.1",
        ),
    )

    rt.db.conn.execute(
        "INSERT INTO phase_execution_protocols VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "protocol_execution", "phase_execution_exact", project,
            "skillrev_execution", "skillhash_execution",
            "HUMAN_APPROVE", "EXECUTE", "WAITING_HUMAN",
            3, 1, "2026-09-26T01:59:10+00:00",
            "2026-09-26T02:04:00+00:00",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO project_agent_protocol_settings VALUES(?,?,?,?,?)",
        (
            project, "HUMAN_APPROVE", 4, owner,
            "2026-09-26T01:50:00+00:00",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_preflights VALUES(?,?,?,?,?,?,?)",
        (
            "preflight_execution", "phase_execution_exact", "PASS",
            canonical_json([{"name": "inputs", "pass": True, "detail": "exact"}]),
            "preflight-hash", executor, "2026-09-26T01:59:20+00:00",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_plans VALUES(?,?,?,?,?,?,?,?,?)",
        (
            "plan_execution", "phase_execution_exact", 1,
            "Execute exact phase",
            canonical_json([{"step_index": 1, "title": "Do work"}]),
            "plan-hash", "INITIAL_PLAN", executor,
            "2026-09-26T01:59:30+00:00",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_checklist_items VALUES(?,?,?,?,?,?,?,?)",
        (
            "check_execution", "plan_execution", "phase_execution_exact",
            1, "Do work", "PASS", "done",
            "2026-09-26T02:00:30+00:00",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_problem_records VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            "problem_execution", "phase_execution_exact", 1,
            "EXECUTION_PROBLEM", "Need operator decision", "persisted detail",
            "HIGH", "OPEN", executor, "2026-09-26T02:01:30+00:00",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_recovery_proposals VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            "protocol_recovery_execution", "problem_execution",
            "phase_execution_exact", "RETRY", 1,
            canonical_json([{"op": "replace", "step": 1}]),
            "persisted rationale", "HIGH", 0,
            "WAITING_HUMAN", "2026-09-26T02:01:40+00:00",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_recovery_decisions VALUES(?,?,?,?,?,?)",
        (
            "protocol_decision_execution", "protocol_recovery_execution",
            owner, "APPROVED", "operator decision",
            "2026-09-26T02:01:50+00:00",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_handoffs VALUES(?,?,?,?,?,?,?)",
        (
            "handoff_previous", "phase_execution_previous",
            canonical_json({"summary": "previous persisted handoff"}),
            "handoff-previous-hash", executor,
            "2026-09-26T01:58:00+00:00",
            "Previous persisted handoff markdown.",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_handoffs VALUES(?,?,?,?,?,?,?)",
        (
            "handoff_execution", "phase_execution_exact",
            canonical_json({"summary": "persisted handoff"}),
            "handoff-execution-hash", executor,
            "2026-09-26T02:04:30+00:00",
            "Persisted handoff markdown.",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_handoff_links VALUES(?,?,?,?,?)",
        (
            "phase_execution_exact", "phase_execution_previous",
            "handoff_previous", "handoff-previous-hash",
            "2026-09-26T01:59:15+00:00",
        ),
    )
    for event_id, stage, event_type, created_at in (
        ("phaseevt_execution_1", "LOAD", "SKILL_LOADED", "2026-09-26T01:59:11+00:00"),
        ("phaseevt_execution_2", "EXECUTE", "STEP_PROGRESS", "2026-09-26T02:00:40+00:00"),
        ("phaseevt_execution_3", "VERIFY", "QA_BLOCKED", "2026-09-26T02:01:20+00:00"),
    ):
        rt.db.conn.execute(
            "INSERT INTO phase_stage_events VALUES(?,?,?,?,?,?,?,?)",
            (
                event_id, "phase_execution_exact", stage, event_type,
                executor, event_type, canonical_json({"source": "test"}), created_at,
            ),
        )
    rt.db.conn.commit()
    return "phase_execution_exact"


def test_project_execution_index_and_phase_detail_are_exact(tmp_path, monkeypatch):
    rt, owner, _, executor, project, hidden_project = _fixture(tmp_path, monkeypatch)
    phase_id = _seed_phase(rt, owner, executor, project)
    client = TestClient(_app(rt))

    assert client.get(f"/browser/projects/{project}/execution").status_code == 401
    _login(client)

    index = client.get(f"/browser/projects/{project}/execution")
    assert index.status_code == 200
    body = index.json()
    assert body["build_sha"] == "execution-build-sha"
    assert body["query_status"] == "COMPLETE"
    assert body["project"]["project_id"] == project
    assert body["execution_activity"] == "EXECUTING"
    assert len(body["orchestrations"]) == 1
    orch = body["orchestrations"][0]
    assert orch["orchestration_id"] == "orch_execution"
    assert orch["status"] == "RUNNING"
    assert orch["generation"] == 4
    assert orch["research_outcome"] == "PIVOT"
    assert orch["pivot_count"] == 2
    assert orch["current_phase_execution_id"] == phase_id
    assert [p["phase_execution_id"] for p in orch["phases"]] == [
        "phase_execution_previous", phase_id
    ]
    assert orch["history"] == [
        {
            "event": "PIVOT",
            "target": "REPORT",
            "checkpoint_id": "checkpoint_pivot_history",
            "generation": 3,
        },
        {
            "event": "RECOVERY",
            "failure_id": "failure_execution",
            "resume_phase": "phase_exact",
            "checkpoint_id": "checkpoint_execution",
        },
    ]
    assert "metadata" not in orch

    detail = client.get(
        f"/browser/projects/{project}/execution/phases/{phase_id}"
    )
    assert detail.status_code == 200
    d = detail.json()
    assert d["phase"]["phase_execution_id"] == phase_id
    assert d["phase"]["generation"] == 4
    assert d["workunit"]["workunit_id"] == "wu_execution"
    assert d["workunit"]["version"] == 3
    assert d["workunit"]["required_gates"] == ["QUALITY_GATE"]
    assert d["workunit"]["resource_conflict_keys"] == ["dataset:execution"]
    assert d["run"]["run_id"] == "run_execution"
    assert d["run"]["attempt_number"] == 2
    assert d["run"]["executor_actor_id"] == executor
    assert d["run"]["runtime_status"] == "RUNNING"
    assert d["run"]["produced_revision_ids"] == ["rev_pivot_trigger"]
    assert d["run"]["evidence_ids"] == ["evidence_execution"]

    assert d["gates"][0]["gate_id"] == "gate_execution"
    assert d["gates"][0]["result"] == "BLOCKED"
    assert d["gates"][0]["violation_codes"] == ["QUALITY_THRESHOLD"]
    assert d["decisions"][0]["decision_id"] == "decision_execution"
    assert d["decisions"][0]["decision_type"] == "REPLAN"
    assert d["failure"]["failure_id"] == "failure_execution"
    assert d["failure"]["root_status"] == "CONFIRMED"
    assert d["recoveries"][0]["recovery_id"] == "recovery_execution"
    assert d["recoveries"][0]["mark_stale_refs"] == ["rev_stale"]
    assert d["loopguard"]["loopguard_id"] == "loop_execution"
    assert d["loopguard"]["status"] == "ESCALATE"
    assert d["loopguard"]["budget"]["same_signature_limit"] == 2
    assert d["checkpoint"]["checkpoint_id"] == "checkpoint_execution"
    assert d["checkpoint"]["blocking_failure_ids"] == ["failure_execution"]
    assert d["checkpoint"]["runtime_metadata"]["recovery_id"] == "recovery_execution"

    assert {item["impact_id"] for item in d["impacts"]} == {
        "impact_execution_failure", "impact_execution_pivot"
    }
    assert "impact_unrelated" not in {item["impact_id"] for item in d["impacts"]}

    protocol = d["agent_protocol"]
    assert protocol["protocol"]["protocol_id"] == "protocol_execution"
    assert protocol["protocol"]["skill_hash"] == "skillhash_execution"
    assert protocol["protocol"]["recovery_mode"] == "HUMAN_APPROVE"
    assert protocol["protocol"]["current_stage"] == "EXECUTE"
    assert protocol["previous_handoff"]["previous_phase_execution_id"] == "phase_execution_previous"
    assert protocol["previous_handoff"]["previous_handoff_id"] == "handoff_previous"
    assert protocol["previous_handoff"]["handoff_hash"] == "handoff-previous-hash"
    assert protocol["previous_handoff"]["handoff"]["payload_hash"] == "handoff-previous-hash"
    assert protocol["previous_handoff"]["handoff"]["structured_payload"] == {
        "summary": "previous persisted handoff"
    }
    assert protocol["preflights"][0]["checks"][0]["pass"] is True
    assert protocol["plans"][0]["plan_hash"] == "plan-hash"
    assert protocol["plans"][0]["checklist"][0]["status"] == "PASS"
    assert protocol["problems"][0]["problem_id"] == "problem_execution"
    assert protocol["problems"][0]["recoveries"][0]["status"] == "WAITING_HUMAN"
    assert protocol["handoffs"][0]["payload_hash"] == "handoff-execution-hash"
    assert protocol["handoffs"][0]["structured_payload"] == {"summary": "persisted handoff"}
    assert protocol["handoffs"][0]["markdown"] == "Persisted handoff markdown."
    assert [event["event_id"] for event in protocol["events"]] == [
        "phaseevt_execution_1", "phaseevt_execution_2", "phaseevt_execution_3"
    ]

    assert "inputs" not in d
    assert "outputs" not in d
    assert "evidence" not in d
    assert "lease_token" not in str(d)
    assert client.get(
        f"/browser/projects/{hidden_project}/execution"
    ).status_code == 404
    assert client.get(
        f"/browser/projects/{hidden_project}/execution/phases/{phase_id}"
    ).status_code == 404
    rt.close()


def test_project_execution_empty_and_cross_project_phase_are_truthful(tmp_path, monkeypatch):
    rt, owner, outsider, executor, project, hidden_project = _fixture(tmp_path, monkeypatch)
    hidden_phase = _seed_phase(rt, outsider, executor, hidden_project)
    client = TestClient(_app(rt))
    _login(client)

    body = client.get(f"/browser/projects/{project}/execution").json()
    assert body["query_status"] == "COMPLETE"
    assert body["orchestrations"] == []

    assert client.get(
        f"/browser/projects/{project}/execution/phases/{hidden_phase}"
    ).status_code == 404
    assert client.get(
        f"/browser/projects/{project}/execution/phases/missing_phase"
    ).status_code == 404
    rt.close()


def test_phase_without_protocol_and_dangling_identity_semantics(tmp_path, monkeypatch):
    rt, _, _, _, project, _ = _fixture(tmp_path, monkeypatch)
    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "orch_plain", project, rt.domain.domain_id, "COMPLETED",
            "phase_plain", 0, "PASS", 0,
            "2026-09-26T03:00:00+00:00",
            "2026-09-26T03:02:00+00:00", None, "{}",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "phase_plain_exact", "orch_plain", "phase_plain", 0, 0,
            None, None, "SUCCEEDED", "CONTINUE", None, None,
            "2026-09-26T03:00:10+00:00",
            "2026-09-26T03:01:00+00:00", "{}",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "phase_dangling_exact", "orch_plain", "phase_dangling", 1, 0,
            "missing_workunit", None, "FAILED", "WAIT", None, None,
            "2026-09-26T03:01:10+00:00",
            "2026-09-26T03:01:20+00:00", "{}",
        ),
    )
    rt.db.conn.commit()

    client = TestClient(_app(rt))
    _login(client)

    plain = client.get(
        f"/browser/projects/{project}/execution/phases/phase_plain_exact"
    )
    assert plain.status_code == 200
    assert plain.json()["query_status"] == "COMPLETE"
    assert plain.json()["agent_protocol"] is None
    assert plain.json()["workunit"] is None
    assert plain.json()["run"] is None

    dangling = client.get(
        f"/browser/projects/{project}/execution/phases/phase_dangling_exact"
    )
    assert dangling.status_code == 200
    assert dangling.json()["query_status"] == "PARTIAL"
    assert dangling.json()["phase"]["workunit_id"] == "missing_workunit"
    assert dangling.json()["workunit"] is None
    rt.close()


def test_project_execution_outage_is_not_fake_zero(tmp_path, monkeypatch):
    rt, _, _, _, project, _ = _fixture(tmp_path, monkeypatch)

    def unavailable(*_args, **_kwargs):
        raise RuntimeError("forced project execution outage")

    monkeypatch.setattr(ProjectDashboardService, "project_execution", unavailable)
    client = TestClient(_app(rt), raise_server_exceptions=False)
    _login(client)
    response = client.get(f"/browser/projects/{project}/execution")
    assert response.status_code == 500
    assert response.text
    rt.close()


def test_browser_phase_events_and_sse_resume_use_session_authority(tmp_path, monkeypatch):
    rt, owner, _, executor, project, hidden_project = _fixture(tmp_path, monkeypatch)
    phase_id = _seed_phase(rt, owner, executor, project)
    client = TestClient(_app(rt))
    _login(client)

    events = client.get(
        f"/browser/projects/{project}/execution/phases/{phase_id}/events"
    )
    assert events.status_code == 200
    assert [e["event_id"] for e in events.json()["events"]] == [
        "phaseevt_execution_1", "phaseevt_execution_2", "phaseevt_execution_3"
    ]

    stream = client.get(
        f"/browser/projects/{project}/execution/phases/{phase_id}/events/stream?follow=false",
        headers={"Last-Event-ID": "phaseevt_execution_1"},
    )
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    assert "id: phaseevt_execution_1\n" not in stream.text
    assert "id: phaseevt_execution_2\n" in stream.text
    assert "id: phaseevt_execution_3\n" in stream.text

    assert client.get(
        f"/browser/projects/{hidden_project}/execution/phases/{phase_id}/events"
    ).status_code == 404
    assert client.get(
        f"/browser/projects/{hidden_project}/execution/phases/{phase_id}/events/stream?follow=false"
    ).status_code == 404
    rt.close()


def test_project_execution_final_report_is_exact_project_derived_view(tmp_path, monkeypatch):
    rt, owner, _, executor, project, hidden_project = _fixture(tmp_path, monkeypatch)
    _seed_phase(rt, owner, executor, project)
    client = TestClient(_app(rt))
    _login(client)

    response = client.get(
        f"/browser/projects/{project}/execution/orchestrations/orch_execution/report"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["authority"] == "DERIVED_VIEW"
    assert body["project_id"] == project
    assert body["orchestration_id"] == "orch_execution"
    assert rt.domain.domain_id == "example.workflow"
    assert body["domain_id"] == "example.workflow"
    assert "# Orchestration Report" in body["markdown"]
    assert "# Research Orchestration Report" not in body["markdown"]
    assert "Authority: **DERIVED_VIEW**" in body["markdown"]
    assert "Domain: `example.workflow`" in body["markdown"]
    assert "phase_previous" in body["markdown"]
    assert "phase_exact" in body["markdown"]
    assert "PIVOT" in body["markdown"]
    assert "RECOVERY" in body["markdown"]
    assert "source of truth" in body["markdown"]
    assert "orch_execution" in body["markdown"]
    assert project in body["markdown"]

    assert client.get(
        f"/browser/projects/{hidden_project}/execution/orchestrations/orch_execution/report"
    ).status_code == 404
    assert client.get(
        f"/browser/projects/{project}/execution/orchestrations/missing_orch/report"
    ).status_code == 404
    rt.close()


def test_existing_bearer_process_phase_and_event_reads_remain_valid(tmp_path, monkeypatch):
    rt, owner, _, executor, project, _ = _fixture(tmp_path, monkeypatch)
    phase_id = _seed_phase(rt, owner, executor, project)
    client = TestClient(_app(rt))

    token = client.post(
        "/auth/login",
        json={"username": "execution-owner", "password": PASSWORD},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    process = client.get(f"/product/projects/{project}/process", headers=headers)
    assert process.status_code == 200
    phase = client.get(f"/product/phases/{phase_id}", headers=headers)
    assert phase.status_code == 200
    events = client.get(f"/product/phases/{phase_id}/events", headers=headers)
    assert events.status_code == 200
    stream = client.get(
        f"/product/phases/{phase_id}/events/stream?follow=false",
        headers={**headers, "Last-Event-ID": "phaseevt_execution_1"},
    )
    assert stream.status_code == 200
    assert "id: phaseevt_execution_2\n" in stream.text
    rt.close()

def test_project_execution_browser_surface_is_live_read_only_and_fallback_capable():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")

    assert 'data-project-section="execution"><span>Execution</span><small>Live</small>' in html
    assert 'id="projectExecutionLiveView"' in html
    assert 'id="projectExecutionPhaseInspector"' in html
    assert 'id="projectExecutionLiveStatus"' in html
    assert 'id="projectExecutionReportButton"' in html
    assert 'id="projectExecutionReport"' in html
    assert '"/execution/phases/"' in js
    assert 'new EventSource(url)' in js
    assert "Reconnecting · Last-Event-ID" in js
    assert "source.readyState === EventSource.OPEN" in js
    assert "Live stream unavailable · persisted events" in js
    assert "active.section !== \"execution\"" in js
    assert "state.me.actor_id !== requestActorId" in js
    assert "Hidden model chain-of-thought is not stored or displayed." in js
    assert '"/execution/orchestrations/"' in js
    assert 'result.markdown || "Derived report is empty."' in js
    assert 'const extra = match[3] || "";' in js
    assert 'section: extra ? "__invalid__"' in js
    assert "function renderProjectWorkspaceLoading(route, message)" in js
    assert '$("#projectOverviewLiveView").hidden = true;' in js
    assert '$("#projectExecutionLiveView").hidden = true;' in js

    for forbidden in (
        "Apply recovery",
        "Start protocol",
        "Complete protocol",
        "Retry phase",
        "Verify phase",
        "Write handoff",
    ):
        assert forbidden not in html

