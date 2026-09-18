from pathlib import Path

from gwr.runtime import GovernedWorkflowRuntime
from gwr.research_orchestrator import ResearchOrchestrator
from gwr.research_demo import DeterministicResearchExecutor


ROLES = [
    "research_lead",
    "literature_reviewer",
    "protocol_designer",
    "experimenter",
    "analyst",
    "adversarial_reviewer",
    "reproducibility_reviewer",
]


def make_runtime(tmp_path, scenario):
    domain = Path(__file__).parents[1] / "domains" / "research.workflow.yaml"
    rt = GovernedWorkflowRuntime(str(domain), str(tmp_path / f"{scenario}.db"))
    project = rt.create_project(f"research-{scenario}")
    actors = {}
    for role in ROLES:
        actors[role] = rt.governance.create_actor("AGENT", f"{role}-1", [role], [project])
    human = rt.governance.create_actor("HUMAN", "human-approver-1", ["human_approver"], [project])
    orch = ResearchOrchestrator(rt, actors, human_approver_id=human)
    return rt, project, orch


def current_revision(rt, project, artifact_type):
    a = rt.db.one("SELECT current_revision_id FROM artifacts WHERE project_id=? AND artifact_type=?", (project, artifact_type))
    return rt.knowledge.get_revision(a["current_revision_id"])


def test_pass_branch_runs_to_terminal_report(tmp_path):
    rt, project, orch = make_runtime(tmp_path, "pass")
    result = orch.start(project, DeterministicResearchExecutor("pass"))
    assert result["status"] == "COMPLETED"
    assert result["outcome"] == "PASS"
    status = orch.get_status(result["orchestration_id"])
    phase_status = [(p["phase_id"], p["status"]) for p in status["phases"]]
    assert ("phase_13_pivot_if_required", "SKIPPED") in phase_status
    assert any(p[0] == "phase_14_replication_or_replay" and p[1] == "SUCCEEDED" for p in phase_status)
    assert current_revision(rt, project, "final_report")["validity_state"] == "VALID"
    assert current_revision(rt, project, "handoff_package")["validity_state"] == "VALID"
    assert len(rt.db.all("SELECT * FROM checkpoints WHERE project_id=?", (project,))) >= 17
    assert "Research outcome: **PASS**" in orch.render_report(result["orchestration_id"])
    rt.close()


def test_scientific_fail_is_not_runtime_failure(tmp_path):
    rt, project, orch = make_runtime(tmp_path, "fail")
    result = orch.start(project, DeterministicResearchExecutor("fail"))
    assert result["status"] == "COMPLETED"
    assert result["outcome"] == "FAIL"
    assert not rt.db.all("SELECT * FROM failures WHERE project_id=?", (project,))
    assert current_revision(rt, project, "replication_result")["validity_state"] == "VALID"
    assert current_revision(rt, project, "final_report")["validity_state"] == "VALID"
    rt.close()


def test_pivot_creates_new_generation_invalidates_and_resumes(tmp_path):
    rt, project, orch = make_runtime(tmp_path, "pivot")
    result = orch.start(project, DeterministicResearchExecutor("pivot"))
    assert result["status"] == "COMPLETED"
    assert result["outcome"] == "PASS"
    assert result["pivot_count"] == 1
    assert result["generation"] >= 1
    protocol_art = rt.db.one("SELECT artifact_id,current_revision_id FROM artifacts WHERE project_id=? AND artifact_type='protocol'", (project,))
    revisions = rt.db.all("SELECT * FROM revisions WHERE artifact_id=? ORDER BY revision_number", (protocol_art["artifact_id"],))
    assert len(revisions) >= 2
    assert revisions[0]["validity_state"] == "SUPERSEDED"
    decisions = rt.db.all("SELECT decision_type,target_ref FROM decisions WHERE project_id=?", (project,))
    assert any(d["decision_type"] == "REPLAN" and d["target_ref"] == "protocol" for d in decisions)
    phases = orch.get_status(result["orchestration_id"])["phases"]
    assert sum(1 for p in phases if p["phase_id"] == "phase_12_decide_pass_fail_pivot" and p["status"] == "SUCCEEDED") == 2
    assert any(p["phase_id"] == "phase_13_pivot_if_required" and p["status"] == "SUCCEEDED" for p in phases)
    rt.close()


def test_retry_failure_checkpoints_then_succeeds(tmp_path):
    rt, project, orch = make_runtime(tmp_path, "runtime_retry")
    result = orch.start(project, DeterministicResearchExecutor("runtime_retry"))
    assert result["status"] == "COMPLETED"
    assert result["outcome"] == "PASS"
    failures = rt.db.all("SELECT * FROM failures WHERE project_id=? AND failure_class='runtime_timeout'", (project,))
    assert len(failures) == 1
    assert failures[0]["status"] == "RESOLVED"
    main_runs = rt.db.all("SELECT r.* FROM runs r JOIN workunits w ON w.workunit_id=r.workunit_id WHERE w.project_id=? AND w.workunit_type='phase_09_main_experiment' ORDER BY attempt_number", (project,))
    assert [r["attempt_number"] for r in main_runs] == [1, 2]
    cps = rt.db.all("SELECT runtime_metadata FROM checkpoints WHERE project_id=?", (project,))
    assert any("ON_FAILURE" in c["runtime_metadata"] for c in cps)
    rt.close()


def test_upstream_recovery_resumes_from_protocol_and_completes(tmp_path):
    rt, project, orch = make_runtime(tmp_path, "runtime_recovery")
    result = orch.start(project, DeterministicResearchExecutor("runtime_recovery"))
    assert result["status"] == "COMPLETED"
    assert result["outcome"] == "PASS"
    failures = rt.db.all("SELECT * FROM failures WHERE project_id=? AND failure_class='protocol_mismatch'", (project,))
    assert len(failures) == 1
    assert failures[0]["root_status"] == "CONFIRMED"
    assert failures[0]["status"] == "RESOLVED"
    protocol_art = rt.db.one("SELECT artifact_id FROM artifacts WHERE project_id=? AND artifact_type='protocol'", (project,))
    revisions = rt.db.all("SELECT * FROM revisions WHERE artifact_id=?", (protocol_art["artifact_id"],))
    assert len(revisions) >= 2
    decisions = rt.db.all("SELECT decision_type,target_ref FROM decisions WHERE project_id=?", (project,))
    assert any(d["decision_type"] == "REVISE_UPSTREAM" and d["target_ref"] == "protocol" for d in decisions)
    rt.close()


def test_resume_from_checkpoint_after_forced_pause(tmp_path):
    rt, project, orch = make_runtime(tmp_path, "pass")
    # Force a deterministic pause by capping max_steps, then resume from persisted checkpoint.
    first = orch.start(project, DeterministicResearchExecutor("pass"), max_steps=3)
    assert first["status"] == "PAUSED"
    resumed = orch.resume(first["checkpoint_id"], DeterministicResearchExecutor("pass"), max_steps=100)
    assert resumed["status"] == "COMPLETED"
    assert resumed["outcome"] == "PASS"
    audit = rt.governance.query_audit(project)
    assert any(e["action"] == "ORCHESTRATION_RESUMED" for e in audit)
    rt.close()


def test_missing_human_approval_pauses_and_can_resume_after_external_approval(tmp_path):
    domain = Path(__file__).parents[1] / "domains" / "research.workflow.yaml"
    rt = GovernedWorkflowRuntime(str(domain), str(tmp_path / "approval.db"))
    project = rt.create_project("research-approval")
    actors = {role: rt.governance.create_actor("AGENT", f"{role}-approval", [role], [project]) for role in ROLES}
    human = rt.governance.create_actor("HUMAN", "human-approval", ["human_approver"], [project])
    orch_no_human = ResearchOrchestrator(rt, actors, human_approver_id=None)
    first = orch_no_human.start(project, DeterministicResearchExecutor("pass"), max_steps=20)
    assert first["status"] == "PAUSED"
    assert first["reason"] == "WAITING_APPROVAL"
    pending = rt.governance.get_pending_approvals(project)
    assert len(pending) == 1
    rt.governance.approve_proposal(pending[0]["proposal_id"], human, pending[0]["payload_hash"])
    orch = ResearchOrchestrator(rt, actors, human_approver_id=human)
    resumed = orch.resume(first["checkpoint_id"], DeterministicResearchExecutor("pass"), max_steps=100)
    assert resumed["status"] == "COMPLETED"
    assert resumed["outcome"] == "PASS"
    assert rt.db.one("SELECT COUNT(*) c FROM failures WHERE project_id=? AND status!='RESOLVED'", (project,))["c"] == 0
    rt.close()


def test_gate_predicates_require_structured_assertions(tmp_path):
    rt, project, orch = make_runtime(tmp_path, "pass")
    # Seed a valid goal input and then evaluate a research gate with evidence that
    # has the right evidence type but omits all declared pass_if assertions.
    lead = orch.actor_by_role["research_lead"]
    human = orch.human_approver_id
    aid = rt.knowledge.create_artifact(project, "research_goal", "research:research_goal", lead)
    payload = {k: "x" for k in rt.domain.artifact("research_goal")["required_fields"]}
    prop = rt.governance.prepare_proposal(project, lead, "CREATE_REVISION", [aid], {"artifact_id": aid, "payload": payload}, "normative_research_change")
    prow = rt.db.one("SELECT payload_hash FROM proposals WHERE proposal_id=?", (prop,))
    rt.governance.approve_proposal(prop, human, prow["payload_hash"])
    rid = rt.knowledge.create_revision(aid, payload, lead, 0, proposal_id=prop)["revision_id"]
    rt.knowledge.set_validity_system(rid, "VALID")
    ev = rt.execution.add_evidence(project, "source_citation_evidence", lead, [rid], {"pass": True, "assertions": []}, "SUPPORTED")
    ev2 = rt.execution.add_evidence(project, "novelty_review_evidence", lead, [rid], {"pass": True, "assertions": []}, "SUPPORTED")
    gate = rt.decision.evaluate_gate(project, "prior_art_ready", {"test": True}, [rid], [ev, ev2])
    assert gate["result"] == "BLOCKED"
    assert any(v.startswith("UNASSERTED_PREDICATE:") for v in gate["violations"])
    rt.close()
