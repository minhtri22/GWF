from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol
import re

from .domain import DomainPackage
from .errors import InvalidTransition, NotFound, ValidationError
from .utils import canonical_json, content_hash, parse_json, uid, utcnow


@dataclass
class EvidenceOutput:
    evidence_type: str
    payload: dict[str, Any]
    trust_class: str | None = None
    subject_refs: list[str] = field(default_factory=list)


@dataclass
class PhaseExecutionResult:
    runtime_status: str = "COMPLETED"  # COMPLETED | FAILED
    artifacts: dict[str, dict[str, Any]] = field(default_factory=dict)
    evidence: list[EvidenceOutput] = field(default_factory=list)
    failure_class: str | None = None
    failure_reason: str | None = None
    root_artifact_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchExecutionContext:
    orchestration_id: str
    project_id: str
    phase_id: str
    phase_index: int
    generation: int
    attempt: int
    actor_id: str
    input_revisions: dict[str, dict[str, Any]]
    current_artifacts: dict[str, dict[str, Any]]
    current_revision_ids: dict[str, str]
    outcome: str | None
    history: list[dict[str, Any]]
    latest_checkpoint_id: str | None
    domain: DomainPackage


class ResearchPhaseExecutor(Protocol):
    def execute(self, context: ResearchExecutionContext) -> PhaseExecutionResult: ...


# Callback may bridge to a trusted UI. Returning None leaves the orchestration paused.
ApprovalProvider = Callable[[str, str, str | None], str | None]


class ResearchOrchestrator:
    """Runs the research Domain Package as an executable, checkpointed state machine.

    Domain `required_gate_types` are interpreted as *completion/postcondition* gates.
    Readiness is derived from current input validity + executor authority. This resolves
    the ambiguity in the v0.1 generic WorkUnit API where the same field was used as a
    readiness gate.
    """

    def __init__(
        self,
        runtime,
        actor_by_role: dict[str, str],
        *,
        human_approver_id: str | None = None,
        approval_provider: ApprovalProvider | None = None,
    ):
        self.runtime = runtime
        self.db = runtime.db
        self.domain = runtime.domain
        if not self.domain.domain_id.startswith("research"):
            raise ValidationError("ResearchOrchestrator requires a research domain package")
        self.actor_by_role = dict(actor_by_role)
        self.human_approver_id = human_approver_id
        self.approval_provider = approval_provider
        self.phases = [w for w in self.domain.workunits() if w.get("id", "").startswith("phase_")]
        if len(self.phases) != 17:
            raise ValidationError("Research domain must define exactly 17 phases", details={"count": len(self.phases)})
        self.phase_index_by_id = {p["id"]: i for i, p in enumerate(self.phases)}
        self.producer_phase_by_artifact: dict[str, int] = {}
        for i, phase in enumerate(self.phases):
            for out in phase.get("outputs", []):
                typ = out["artifact_type"] if isinstance(out, dict) else out
                self.producer_phase_by_artifact[typ] = i

    # ------------------------------------------------------------------ public
    def start(self, project_id: str, executor: ResearchPhaseExecutor, *, max_steps: int = 250) -> dict[str, Any]:
        if not self.db.one("SELECT 1 FROM projects WHERE id=?", (project_id,)):
            raise NotFound("Project not found")
        self.runtime.project_governance.require_mutable(project_id)
        oid = uid("orch")
        state = {
            "orchestration_id": oid,
            "project_id": project_id,
            "next_phase_index": 0,
            "generation": 0,
            "outcome": None,
            "pivot_count": 0,
            "history": [],
            "recovery_failure_id": None,
            "recovery_root_phase_index": None,
            "pending_approval": None,
            "pending_human_action": None,
            "pending_protocol_recovery": None,
            "phase_retry_counts": {},
            "resumed_from_checkpoint": None,
        }
        now = utcnow()
        self.db.conn.execute(
            "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (oid, project_id, self.domain.domain_id, "RUNNING", self.phases[0]["id"], 0, None, 0, now, now, None, canonical_json(state)),
        )
        self.runtime.governance.append_audit(project_id, "SYSTEM", "ORCHESTRATION_STARTED", "ResearchOrchestration", oid)
        self.runtime.observe("orchestration_started", project_id=project_id, orchestration_id=oid)
        self.db.conn.commit()
        return self._drive(state, executor, max_steps=max_steps)

    def resume(self, checkpoint_id: str, executor: ResearchPhaseExecutor, *, max_steps: int = 250) -> dict[str, Any]:
        reconciled = self.runtime.execution.reconcile_checkpoint(checkpoint_id)
        metadata = reconciled.get("runtime_metadata", {})
        state = metadata.get("research_orchestrator_state")
        if not state:
            raise ValidationError("Checkpoint does not contain ResearchOrchestrator state")
        state = dict(state)
        state["resumed_from_checkpoint"] = checkpoint_id
        pending_protocol=state.get("pending_protocol_recovery")
        if pending_protocol:
            recovery=self.db.one("SELECT status FROM phase_recovery_proposals WHERE proposal_id=?", (pending_protocol.get("proposal_id"),))
            if not recovery or recovery["status"] == "WAITING_HUMAN":
                return {"status":"PAUSED","reason":"WAITING_PROTOCOL_RECOVERY","orchestration_id":state["orchestration_id"],"project_id":state["project_id"],"checkpoint_id":checkpoint_id,"outcome":state.get("outcome"),"generation":state.get("generation"),"pivot_count":state.get("pivot_count")}
            if recovery["status"] == "REJECTED":
                return {"status":"PAUSED","reason":"PROTOCOL_RECOVERY_REJECTED","orchestration_id":state["orchestration_id"],"project_id":state["project_id"],"checkpoint_id":checkpoint_id,"outcome":state.get("outcome"),"generation":state.get("generation"),"pivot_count":state.get("pivot_count")}
            if recovery["status"] in {"AUTO_APPROVED","HUMAN_APPROVED"}:
                self.runtime.agent_protocol.apply_recovery(pending_protocol["proposal_id"], pending_protocol["actor_id"])
            elif recovery["status"] != "APPLIED":
                raise InvalidTransition(f"Unexpected protocol recovery status {recovery['status']}")
            if pending_protocol.get("phase_execution_id"):
                self.runtime.agent_protocol.mark_attempt_failed(
                    pending_protocol["phase_execution_id"], pending_protocol["actor_id"], reason="Recovery approved; retry will use a new phase execution"
                )
            retry_key=pending_protocol.get("retry_key")
            if retry_key:
                counters=state.setdefault("phase_retry_counts", {})
                counters[retry_key]=int(counters.get(retry_key, 0))+1
            state["pending_protocol_recovery"]=None
        pending_approval=state.get("pending_approval")
        if pending_approval:
            proposal=self.db.one("SELECT status FROM proposals WHERE proposal_id=?", (pending_approval.get("proposal_id"),))
            if not proposal or proposal["status"] != "APPROVED":
                return {"status":"PAUSED","reason":"WAITING_APPROVAL","orchestration_id":state["orchestration_id"],"project_id":state["project_id"],"checkpoint_id":checkpoint_id,"outcome":state.get("outcome"),"generation":state.get("generation"),"pivot_count":state.get("pivot_count")}
            if pending_approval.get("failure_id"):
                self.runtime.decision.resolve_failure(pending_approval["failure_id"])
            if pending_approval.get("phase_execution_id"):
                self.runtime.agent_protocol.mark_attempt_failed(
                    pending_approval["phase_execution_id"],
                    pending_approval.get("actor_id") or "SYSTEM",
                    reason="Required approval granted; phase will restart from checkpoint",
                )
            state["pending_approval"]=None
        pending_action=state.get("pending_human_action")
        if pending_action:
            proposal=self.db.one("SELECT status FROM proposals WHERE proposal_id=?", (pending_action.get("proposal_id"),))
            if not proposal or proposal["status"] != "APPROVED":
                return {"status":"PAUSED","reason":"WAITING_HUMAN_CONFIRMATION","orchestration_id":state["orchestration_id"],"project_id":state["project_id"],"checkpoint_id":checkpoint_id,"outcome":state.get("outcome"),"generation":state.get("generation"),"pivot_count":state.get("pivot_count")}
            appr=self.db.one("SELECT approver_actor_id FROM approvals WHERE proposal_id=? AND decision='APPROVED' ORDER BY created_at DESC LIMIT 1", (pending_action["proposal_id"],))
            if not appr:
                return {"status":"PAUSED","reason":"WAITING_HUMAN_CONFIRMATION","orchestration_id":state["orchestration_id"],"project_id":state["project_id"],"checkpoint_id":checkpoint_id,"outcome":state.get("outcome"),"generation":state.get("generation"),"pivot_count":state.get("pivot_count")}
            approver=appr["approver_actor_id"]
            failure_id=pending_action["failure_id"]
            root_revision_id=pending_action["root_revision_id"]
            root_type=pending_action["root_type"]
            resume_idx=int(pending_action["resume_phase_index"])
            self.runtime.decision.confirm_root(failure_id, root_revision_id, root_type, approver)
            self.runtime.knowledge.set_validity_system(root_revision_id, "DIRTY")
            impact=self.runtime.knowledge.compute_impact(state["project_id"], "OPERATIONAL_FAILURE", failure_id, root_revision_id, apply=True)
            recovery_id=self.runtime.decision.create_recovery_plan(failure_id, impact["impact_id"], approver)
            recovery_cp=self.runtime.execution.apply_recovery_plan(recovery_id)
            self.runtime.decision.create_decision(state["project_id"], {"workunit_id":pending_action["workunit_id"]}, pending_action.get("route") if pending_action.get("route") in {"REVISE_CURRENT","REVISE_UPSTREAM","REPLAN"} else "REVISE_UPSTREAM", ["AUTHENTICATED_ROOT_CONFIRMATION","RECOVERY_PLAN_CREATED"], source_failure_id=failure_id, target_ref=root_type)
            state["recovery_failure_id"]=failure_id
            state["recovery_root_phase_index"]=resume_idx
            state["history"].append({"event":"RECOVERY","failure_id":failure_id,"root_artifact_type":root_type,"resume_phase":self.phases[resume_idx]["id"],"checkpoint_id":recovery_cp,"authenticated_approver":approver})
            state["next_phase_index"]=resume_idx
            state["generation"]+=1
            state["outcome"]=None
            state["pending_human_action"]=None
        oid = state["orchestration_id"]
        row = self.db.one("SELECT * FROM orchestrations WHERE orchestration_id=?", (oid,))
        if not row:
            raise NotFound("Orchestration referenced by checkpoint not found")
        self.db.conn.execute("UPDATE orchestrations SET status='RUNNING',updated_at=?,metadata=? WHERE orchestration_id=?", (utcnow(), canonical_json(state), oid))
        self.runtime.governance.append_audit(state["project_id"], "SYSTEM", "ORCHESTRATION_RESUMED", "ResearchOrchestration", oid, reason_code=checkpoint_id)
        self.runtime.observe("orchestration_resumed", project_id=state["project_id"], orchestration_id=oid, checkpoint_id=checkpoint_id)
        self.db.conn.commit()
        return self._drive(state, executor, max_steps=max_steps)

    def get_status(self, orchestration_id: str) -> dict[str, Any]:
        row = self.db.one("SELECT * FROM orchestrations WHERE orchestration_id=?", (orchestration_id,))
        if not row:
            raise NotFound("Orchestration not found")
        d = dict(row)
        d["metadata"] = parse_json(d["metadata"], {})
        d["phases"] = [dict(r) for r in self.db.all("SELECT * FROM phase_executions WHERE orchestration_id=? ORDER BY started_at", (orchestration_id,))]
        return d

    def render_report(self, orchestration_id: str) -> str:
        o = self.get_status(orchestration_id)
        project_id = o["project_id"]
        phases = o["phases"]
        failures = [dict(r) for r in self.db.all("SELECT * FROM failures WHERE project_id=? ORDER BY created_at", (project_id,))]
        checkpoints = [dict(r) for r in self.db.all("SELECT * FROM checkpoints WHERE project_id=? ORDER BY created_at", (project_id,))]
        artifacts = [dict(r) for r in self.db.all("SELECT * FROM artifacts WHERE project_id=? ORDER BY artifact_type", (project_id,))]
        decisions = [dict(r) for r in self.db.all("SELECT * FROM decisions WHERE project_id=? ORDER BY created_at", (project_id,))]
        gates = [dict(r) for r in self.db.all("SELECT * FROM gates WHERE project_id=? ORDER BY evaluated_at", (project_id,))]
        open_failures = [f for f in failures if f["status"] != "RESOLVED"]
        lines = [
            "# Research Orchestration Report",
            "",
            f"- Orchestration: `{orchestration_id}`",
            f"- Project: `{project_id}`",
            f"- Status: **{o['status']}**",
            f"- Research outcome: **{o['research_outcome'] or 'N/A'}**",
            f"- Lineage generation: **{o['generation']}**",
            f"- Pivots: **{o['pivot_count']}**",
            f"- Phase executions: **{len(phases)}**",
            f"- Checkpoints: **{len(checkpoints)}**",
            f"- Gates evaluated: **{len(gates)}**",
            f"- Failures: **{len(failures)}** (open: {len(open_failures)})",
            "",
            "## Phase history",
            "",
            "| Generation | Phase | Status | Outcome | Failure | Checkpoint |",
            "|---:|---|---|---|---|---|",
        ]
        for p in phases:
            lines.append(
                f"| {p['generation']} | `{p['phase_id']}` | {p['status']} | {p['decision_outcome'] or ''} | {p['failure_id'] or ''} | {p['checkpoint_id'] or ''} |"
            )
        lines += ["", "## Current artifacts", "", "| Type | Revision | Validity |", "|---|---|---|"]
        for a in artifacts:
            rid = a["current_revision_id"]
            rev = self.db.one("SELECT revision_number,validity_state FROM revisions WHERE revision_id=?", (rid,)) if rid else None
            lines.append(f"| `{a['artifact_type']}` | {rev['revision_number'] if rev else '-'} | {rev['validity_state'] if rev else '-'} |")
        lines += ["", "## Operational failures", ""]
        if not failures:
            lines.append("No operational failures recorded.")
        else:
            for f in failures:
                lines.append(f"- `{f['failure_class']}` — detected `{f['detected_stage']}`, root `{f['root_ref'] or 'unconfirmed'}`, status **{f['status']}**, resume `{f['resume_candidate'] or '-'} `.")
        lines += ["", "## Decision events", ""]
        if not decisions:
            lines.append("No runtime decisions recorded.")
        else:
            for d in decisions:
                lines.append(f"- **{d['decision_type']}** → `{d['target_ref'] or '-'}` ({', '.join(parse_json(d['reason_codes'], []))})")
        lines += ["", "## Open issues", ""]
        if open_failures:
            for f in open_failures:
                lines.append(f"- Open failure `{f['failure_id']}`: {f['failure_class']}")
        else:
            lines.append("- None recorded by the runtime.")
        lines += ["", "## Reproducibility", "", "The authoritative execution trail is the SQLite state + append-only audit log + checkpoint snapshots. The Markdown report is a derived view, not the source of truth.", ""]
        return "\n".join(lines)

    def write_report(self, orchestration_id: str, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.render_report(orchestration_id), encoding="utf-8")
        return p

    # -------------------------------------------------------------- drive logic
    def _drive(self, state: dict[str, Any], executor: ResearchPhaseExecutor, *, max_steps: int) -> dict[str, Any]:
        steps = 0
        while state["next_phase_index"] < len(self.phases):
            if steps >= max_steps:
                return self._pause(state, "MAX_STEPS_EXCEEDED")
            steps += 1
            idx = int(state["next_phase_index"])
            phase = self.phases[idx]
            phase_id = phase["id"]
            self.runtime.observe("research_phase_started", project_id=state["project_id"], orchestration_id=state["orchestration_id"], phase_id=phase_id, generation=state["generation"])
            self._update_orchestration(state, status="RUNNING", current_phase_id=phase_id)

            if not self._should_execute(phase, state):
                self._record_phase_skip(state, idx, phase_id)
                state["next_phase_index"] = idx + 1
                self._persist_state(state)
                continue

            result = self._execute_phase(state, idx, phase, executor)
            if result["action"] == "PAUSE":
                return self._pause(state, result["reason"], result.get("checkpoint_id"))
            if result["action"] == "RESUME_AT":
                state["next_phase_index"] = result["phase_index"]
                state["generation"] += 1
                state["outcome"] = None
                self._persist_state(state)
                continue

            # successful phase
            output_revisions = result["output_revisions"]
            state["history"].append({"phase_id": phase_id, "generation": state["generation"], "status": "PASS", "checkpoint_id": result.get("checkpoint_id")})
            self.runtime.observe("research_phase_passed", project_id=state["project_id"], orchestration_id=state["orchestration_id"], phase_id=phase_id, generation=state["generation"], checkpoint_id=result.get("checkpoint_id"))

            # if this phase is the repaired root, the operational failure is now resolved
            if state.get("recovery_failure_id") and state.get("recovery_root_phase_index") == idx:
                self.runtime.decision.resolve_failure(state["recovery_failure_id"])
                state["history"].append({"event": "RECOVERY_RESOLVED", "failure_id": state["recovery_failure_id"], "phase_id": phase_id})
                state["recovery_failure_id"] = None
                state["recovery_root_phase_index"] = None

            if phase_id == "phase_12_decide_pass_fail_pivot":
                decision_rev = output_revisions.get("decision_record")
                decision_payload = self.runtime.knowledge.get_revision(decision_rev)["structured_payload"]
                outcome = decision_payload.get("outcome")
                if outcome not in {"PASS", "FAIL", "PIVOT"}:
                    return self._pause(state, "INVALID_RESEARCH_OUTCOME")
                state["outcome"] = outcome
                self._checkpoint(state, phase_id, "PASS_FAIL_PIVOT_DECISION")

            if phase_id == "phase_13_pivot_if_required":
                pivot_rev = output_revisions.get("pivot_plan")
                pivot = self.runtime.knowledge.get_revision(pivot_rev)["structured_payload"]
                target_type = pivot.get("earliest_resume_artifact")
                allowed = set(self.domain.data.get("pivot_resume_policy", {}).get("after_phase_13", {}).get("allowed_resume_targets", []))
                if target_type not in allowed or target_type not in self.producer_phase_by_artifact:
                    return self._pause(state, "INVALID_PIVOT_RESUME_TARGET")
                state["pivot_count"] += 1
                limit = int(self.domain.data.get("loop_policy", {}).get("decision_cycle_limit", 2))
                if state["pivot_count"] > limit:
                    return self._pause(state, "PIVOT_LOOP_GUARD")
                root = self._current_revision_by_type(state["project_id"], target_type)
                if root:
                    self.runtime.knowledge.set_validity_system(root["revision_id"], "DIRTY")
                    self.runtime.knowledge.compute_impact(state["project_id"], "PIVOT", pivot_rev, root["revision_id"], apply=True)
                resume_idx = self.producer_phase_by_artifact[target_type]
                self.runtime.decision.create_decision(state["project_id"], {"orchestration_id": state["orchestration_id"]}, "REPLAN", ["RESEARCH_PIVOT"], target_ref=target_type)
                cp = self._checkpoint(state, phase_id, "PIVOT_BEFORE_RESUME", next_phase_index=resume_idx)
                state["history"].append({"event": "PIVOT", "target": target_type, "checkpoint_id": cp, "generation": state["generation"]})
                state["next_phase_index"] = resume_idx
                state["generation"] += 1
                state["outcome"] = None
                self._persist_state(state)
                continue

            if phase_id == "phase_16_handoff_and_archive":
                state["next_phase_index"] = len(self.phases)
                terminal_cp = self._checkpoint(state, phase_id, "TERMINAL", next_phase_index=len(self.phases))
                self._update_orchestration(state, status="COMPLETED", current_phase_id=None, terminal_checkpoint_id=terminal_cp)
                self.runtime.observe("orchestration_completed", project_id=state["project_id"], orchestration_id=state["orchestration_id"], outcome=state.get("outcome"), generation=state.get("generation"), pivot_count=state.get("pivot_count"))
                return {"status": "COMPLETED", "orchestration_id": state["orchestration_id"], "project_id": state["project_id"], "outcome": state["outcome"], "generation": state["generation"], "pivot_count": state["pivot_count"], "terminal_checkpoint_id": terminal_cp}

            state["next_phase_index"] = idx + 1
            self._persist_state(state)

        self._update_orchestration(state, status="COMPLETED", current_phase_id=None)
        return {"status": "COMPLETED", "orchestration_id": state["orchestration_id"], "project_id": state["project_id"], "outcome": state["outcome"], "generation": state["generation"], "pivot_count": state["pivot_count"]}

    def _execute_phase(self, state: dict[str, Any], idx: int, phase: dict[str, Any], executor: ResearchPhaseExecutor) -> dict[str, Any]:
        project_id = state["project_id"]
        phase_id = phase["id"]
        role = phase.get("executor_role")
        actor_id = self.actor_by_role.get(role)
        if not actor_id:
            cp = self._checkpoint(state, phase_id, f"MISSING_ACTOR:{role}", next_phase_index=idx)
            return {"action": "PAUSE", "reason": f"MISSING_ACTOR:{role}", "checkpoint_id": cp}

        inputs = self._resolve_inputs(project_id, phase)
        input_ids = [v["revision_id"] for v in inputs.values()]
        checkpoint_cfg = phase.get("checkpoint_policy", {})
        if checkpoint_cfg.get("before"):
            self._checkpoint(state, phase_id, "BEFORE_PHASE", next_phase_index=idx)

        workunit_id = self.runtime.execution.create_workunit(project_id, phase_id, input_ids, actor_id)
        readiness = self.runtime.execution.prepare_for_execution(workunit_id)
        if readiness["status"] != "READY":
            failure_class = "stale_input" if any(x.startswith("INPUT_") for x in readiness["blockers"]) else "approval_missing"
            fid = self.runtime.decision.record_failure(project_id, workunit_id, failure_class, "READINESS", workunit_id, violations=readiness["blockers"])
            cp = self._checkpoint(state, phase_id, "READINESS_FAILURE", next_phase_index=idx)
            self._record_phase_execution(state, idx, phase_id, workunit_id, None, "FAILED", failure_id=fid, checkpoint_id=cp)
            return {"action": "PAUSE", "reason": "READINESS_BLOCKED", "checkpoint_id": cp}

        max_attempts = int(phase.get("retry_policy", {}).get("max_attempts", 1))
        for attempt in range(1, max_attempts + 1):
            if attempt > 1:
                self.db.conn.execute("UPDATE workunits SET status='READY',version=version+1 WHERE workunit_id=?", (workunit_id,))
                self.db.conn.commit()

            # A phase execution record exists before any agent execution so LOAD/PREFLIGHT/PLAN
            # are authoritative persisted stages, rather than an API-only side channel.
            pexec_id = self._record_phase_execution(state, idx, phase_id, workunit_id, None, "RUNNING")
            previous_phase_execution_id = self._previous_successful_phase_execution(state["orchestration_id"], idx)
            try:
                skill = self.runtime.agent_protocol.resolve_skill_revision(phase_id)
                self.runtime.agent_protocol.create_protocol(
                    pexec_id,
                    skill["skill_revision_id"],
                    actor_id,
                    recovery_mode=None,
                    retry_budget=None,
                    enforce_domain_binding=True,
                )
                handoff_ok = True
                handoff_detail = "first executable phase"
                try:
                    link = self.runtime.agent_protocol.bind_previous_handoff(pexec_id, previous_phase_execution_id, actor_id)
                    if previous_phase_execution_id:
                        handoff_detail = f"verified {link.get('previous_handoff_id')}"
                except (InvalidTransition, NotFound, ValidationError) as exc:
                    handoff_ok = False
                    handoff_detail = str(exc)

                preflight = self.runtime.agent_protocol.record_preflight(
                    pexec_id,
                    [
                        {"name": "skill_revision_pinned", "pass": True, "detail": f"{skill['skill_revision_id']}:{skill['skill_hash']}"},
                        {"name": "inputs_ready", "pass": readiness["status"] == "READY", "detail": ",".join(readiness.get("blockers", [])) or "READY"},
                        {"name": "previous_handoff_verified", "pass": handoff_ok, "detail": handoff_detail},
                        {"name": "tool_contract_declared", "pass": True, "detail": ",".join(skill.get("required_tools", [])) or "none"},
                    ],
                    actor_id,
                )
                if preflight["status"] != "PASS":
                    cp = self._checkpoint(state, phase_id, "AGENT_PREFLIGHT_BLOCKED", next_phase_index=idx)
                    self._finish_phase_execution(pexec_id, "FAILED", checkpoint_id=cp)
                    return {"action": "PAUSE", "reason": "AGENT_PREFLIGHT_BLOCKED", "checkpoint_id": cp}

                self.runtime.agent_protocol.create_plan(
                    pexec_id,
                    f"Execute {phase_id} under pinned skill revision {skill['version']}",
                    [
                        {"title": "Resolve validated inputs", "expected_output": "validated input set"},
                        {"title": "Execute phase contract", "expected_output": "phase executor result"},
                        {"title": "Persist artifacts and evidence", "expected_output": "authoritative revisions and evidence"},
                        {"title": "Verify completion gates", "expected_output": "gate PASS"},
                    ],
                    actor_id,
                )
                self.runtime.agent_protocol.start_execution(pexec_id, actor_id)
                self.runtime.agent_protocol.update_step(pexec_id, 1, "PASS", actor_id, note="runtime readiness and inputs locked")
            except (InvalidTransition, NotFound, ValidationError) as exc:
                cp = self._checkpoint(state, phase_id, "AGENT_PROTOCOL_SETUP_FAILURE", next_phase_index=idx, extra={"error": str(exc)})
                self._finish_phase_execution(pexec_id, "FAILED", checkpoint_id=cp)
                return {"action": "PAUSE", "reason": "AGENT_PROTOCOL_SETUP_FAILURE", "checkpoint_id": cp}

            retry_key = f"{state['generation']}:{phase_id}"
            retry_count = int(state.setdefault("phase_retry_counts", {}).get(retry_key, 0))
            logical_attempt = retry_count + 1
            if logical_attempt > max_attempts:
                cp = self._checkpoint(state, phase_id, "RETRY_EXHAUSTED", next_phase_index=idx)
                self._finish_phase_execution(pexec_id, "FAILED", checkpoint_id=cp)
                return {"action": "PAUSE", "reason": "RETRY_EXHAUSTED", "checkpoint_id": cp}
            version = self.db.one("SELECT version FROM workunits WHERE workunit_id=?", (workunit_id,))["version"]
            run = self.runtime.execution.start_run(
                workunit_id,
                actor_id,
                version,
                f"{state['orchestration_id']}:{state['generation']}:{phase_id}:{workunit_id}:{logical_attempt}",
                state["orchestration_id"],
            )
            run_id = run["run_id"]
            self._attach_phase_run(pexec_id, run_id)
            context = ResearchExecutionContext(
                orchestration_id=state["orchestration_id"], project_id=project_id, phase_id=phase_id,
                phase_index=idx, generation=state["generation"], attempt=logical_attempt, actor_id=actor_id,
                input_revisions=inputs, current_artifacts=self._current_artifact_payloads(project_id), current_revision_ids=self._current_revision_ids(project_id),
                outcome=state.get("outcome"), history=list(state.get("history", [])), latest_checkpoint_id=self._latest_checkpoint_id(project_id), domain=self.domain,
            )
            try:
                phase_result = executor.execute(context)
            except Exception as exc:
                phase_result = PhaseExecutionResult(
                    runtime_status="FAILED",
                    failure_class=self._fallback_failure_class(phase),
                    failure_reason=f"executor_exception:{type(exc).__name__}:{exc}",
                )

            if phase_result.runtime_status != "COMPLETED":
                self.runtime.agent_protocol.update_step(pexec_id, 2, "FAIL", actor_id, note=phase_result.failure_reason or "runtime failure")
                problem_id = self.runtime.agent_protocol.record_problem(
                    pexec_id,
                    actor_id,
                    code=phase_result.failure_class or self._fallback_failure_class(phase),
                    summary="Phase runtime execution failed",
                    detail=phase_result.failure_reason or "PHASE_RUNTIME_FAILURE",
                    affected_step=2,
                    severity="MEDIUM",
                )
                fc = phase_result.failure_class or self._fallback_failure_class(phase)
                self.runtime.execution.finish_run(run_id, "FAILED", {"failure_class": fc, "reason": phase_result.failure_reason or "PHASE_RUNTIME_FAILURE"})
                failure = self.db.one("SELECT * FROM failures WHERE scope_id=? AND status!='RESOLVED' ORDER BY created_at DESC LIMIT 1", (workunit_id,))
                fid = failure["failure_id"] if failure else None
                cp = self._checkpoint(state, phase_id, "ON_FAILURE", next_phase_index=idx, extra={"failure_id": fid, "attempt": logical_attempt, "problem_id": problem_id})
                self._finish_phase_execution(pexec_id, "FAILED", failure_id=fid, checkpoint_id=cp)
                action = self._route_operational_failure(state, idx, phase, workunit_id, fid, phase_result)
                if action["action"] == "RETRY":
                    if retry_count >= max_attempts - 1:
                        self.runtime.agent_protocol.mark_attempt_failed(pexec_id, actor_id, reason="Runtime retry budget exhausted")
                        exhausted_cp = self._checkpoint(state, phase_id, "RETRY_EXHAUSTED", next_phase_index=idx)
                        return {"action": "PAUSE", "reason": "RETRY_EXHAUSTED", "checkpoint_id": exhausted_cp}
                    recovery = self.runtime.agent_protocol.propose_recovery(
                        problem_id,
                        actor_id,
                        action="RETRY_PHASE",
                        target_step=2,
                        rationale=phase_result.failure_reason or fc,
                        risk_class="LOW",
                        normative_change=False,
                    )
                    if recovery["status"] == "AUTO_APPROVED":
                        self.runtime.agent_protocol.apply_recovery(recovery["proposal_id"], actor_id)
                        self.runtime.agent_protocol.mark_attempt_failed(pexec_id, actor_id, reason="Recovered attempt superseded by retry")
                        state.setdefault("phase_retry_counts", {})[retry_key] = retry_count + 1
                        self._persist_state(state)
                        continue
                    self.runtime.agent_protocol.mark_waiting_for_human(
                        pexec_id, actor_id, reason="Retry requires human approval",
                        metadata={"proposal_id": recovery["proposal_id"], "problem_id": problem_id},
                    )
                    state["pending_protocol_recovery"] = {
                        "proposal_id": recovery["proposal_id"],
                        "actor_id": actor_id,
                        "phase_index": idx,
                        "phase_execution_id": pexec_id,
                        "retry_key": retry_key,
                    }
                    waiting_cp = self._checkpoint(
                        state,
                        phase_id,
                        "WAITING_PROTOCOL_RECOVERY",
                        next_phase_index=idx,
                        extra={"proposal_id": recovery["proposal_id"], "problem_id": problem_id},
                    )
                    return {"action": "PAUSE", "reason": "WAITING_PROTOCOL_RECOVERY", "checkpoint_id": waiting_cp}
                self.runtime.agent_protocol.mark_attempt_failed(pexec_id, actor_id, reason=f"Failure routed as {action['action']}")
                return action

            self.runtime.agent_protocol.update_step(pexec_id, 2, "PASS", actor_id, note="executor completed")
            try:
                output_revisions = self._commit_phase_outputs(state, phase, actor_id, run_id, phase_result.artifacts)
            except InvalidTransition as exc:
                if "Approval required for proposal" not in str(exc):
                    raise
                self.runtime.agent_protocol.update_step(pexec_id, 3, "FAIL", actor_id, note=str(exc))
                problem_id = self.runtime.agent_protocol.record_problem(
                    pexec_id, actor_id, code="APPROVAL_REQUIRED", summary="Normative output requires approval",
                    detail=str(exc), affected_step=3, severity="MEDIUM",
                )
                self.runtime.execution.finish_run(run_id, "FAILED", {"failure_class": "approval_missing", "reason": str(exc)})
                for oldf in self.db.all("SELECT failure_id,failure_class FROM failures WHERE scope_id=? AND status!='RESOLVED'", (workunit_id,)):
                    if oldf["failure_class"] != "approval_missing":
                        self.runtime.decision.resolve_failure(oldf["failure_id"])
                failure = self.db.one("SELECT * FROM failures WHERE scope_id=? AND status!='RESOLVED' ORDER BY created_at DESC LIMIT 1", (workunit_id,))
                fid = failure["failure_id"] if failure else None
                pending=self.db.one("SELECT proposal_id FROM proposals WHERE project_id=? AND status='PENDING_APPROVAL' ORDER BY created_at DESC LIMIT 1", (project_id,))
                self.runtime.agent_protocol.mark_waiting_for_human(
                    pexec_id, actor_id, reason="Normative output is waiting for trusted human approval",
                    metadata={"proposal_id": pending["proposal_id"] if pending else None, "problem_id": problem_id},
                )
                state["pending_approval"]={
                    "proposal_id": pending["proposal_id"] if pending else None,
                    "failure_id": fid,
                    "phase_index": idx,
                    "phase_execution_id": pexec_id,
                    "actor_id": actor_id,
                }
                cp = self._checkpoint(state, phase_id, "WAITING_APPROVAL", next_phase_index=idx, extra={"failure_id": fid, "proposal_id": pending["proposal_id"] if pending else None, "problem_id": problem_id})
                self._finish_phase_execution(pexec_id, "FAILED", failure_id=fid, checkpoint_id=cp)
                return {"action": "PAUSE", "reason": "WAITING_APPROVAL", "checkpoint_id": cp}

            evidence_ids = self._record_phase_evidence(project_id, phase, actor_id, run_id, input_ids, output_revisions, phase_result.evidence)
            self.runtime.agent_protocol.update_step(pexec_id, 3, "PASS", actor_id, note=f"{len(output_revisions)} revisions, {len(evidence_ids)} evidence records")
            self.runtime.execution.finish_run(run_id, "COMPLETED", {"exit_code": 0}, await_gate=True)
            if checkpoint_cfg.get("after_each_run"):
                self._checkpoint(state, phase_id, "AFTER_EXECUTION_RUN", next_phase_index=idx)
            gate_result = self._evaluate_completion_gates(project_id, phase, workunit_id, input_ids, evidence_ids)
            if gate_result["result"] != "PASS":
                self.runtime.agent_protocol.update_step(pexec_id, 4, "FAIL", actor_id, note=";".join(gate_result.get("violations", [])))
                problem_id = self.runtime.agent_protocol.record_problem(
                    pexec_id, actor_id, code="COMPLETION_GATE_FAILED", summary="Completion gate did not pass",
                    detail=";".join(gate_result.get("violations", [])) or gate_result["result"], affected_step=4, severity="MEDIUM",
                )
                self.runtime.execution.finalize_workunit(workunit_id, gate_result["result"], gate_result.get("gate_id"))
                fc = phase_result.failure_class or self._fallback_failure_class(phase)
                fid = self.runtime.decision.record_failure(project_id, workunit_id, fc, "GATE", gate_result.get("gate_id") or workunit_id, failed_gate_id=gate_result.get("gate_id"), evidence_ids=evidence_ids, violations=gate_result.get("violations", []))
                cp = self._checkpoint(state, phase_id, "GATE_FAILURE", next_phase_index=idx, extra={"failure_id": fid, "problem_id": problem_id})
                self._finish_phase_execution(pexec_id, "FAILED", failure_id=fid, checkpoint_id=cp)
                action = self._route_operational_failure(state, idx, phase, workunit_id, fid, phase_result)
                if action["action"] == "RETRY":
                    if retry_count >= max_attempts - 1:
                        self.runtime.agent_protocol.mark_attempt_failed(pexec_id, actor_id, reason="Gate retry budget exhausted")
                        exhausted_cp = self._checkpoint(state, phase_id, "RETRY_EXHAUSTED", next_phase_index=idx)
                        return {"action": "PAUSE", "reason": "RETRY_EXHAUSTED", "checkpoint_id": exhausted_cp}
                    recovery = self.runtime.agent_protocol.propose_recovery(
                        problem_id, actor_id, action="RETRY_PHASE", target_step=4,
                        rationale="Completion gate retry", risk_class="LOW", normative_change=False,
                    )
                    if recovery["status"] == "AUTO_APPROVED":
                        self.runtime.agent_protocol.apply_recovery(recovery["proposal_id"], actor_id)
                        self.runtime.agent_protocol.mark_attempt_failed(pexec_id, actor_id, reason="Recovered gate attempt superseded by retry")
                        state.setdefault("phase_retry_counts", {})[retry_key] = retry_count + 1
                        self._persist_state(state)
                        continue
                    self.runtime.agent_protocol.mark_waiting_for_human(
                        pexec_id, actor_id, reason="Gate retry requires human approval",
                        metadata={"proposal_id": recovery["proposal_id"], "problem_id": problem_id},
                    )
                    state["pending_protocol_recovery"] = {
                        "proposal_id": recovery["proposal_id"],
                        "actor_id": actor_id,
                        "phase_index": idx,
                        "phase_execution_id": pexec_id,
                        "retry_key": retry_key,
                    }
                    waiting_cp = self._checkpoint(
                        state, phase_id, "WAITING_PROTOCOL_RECOVERY", next_phase_index=idx,
                        extra={"proposal_id": recovery["proposal_id"], "problem_id": problem_id},
                    )
                    return {"action": "PAUSE", "reason": "WAITING_PROTOCOL_RECOVERY", "checkpoint_id": waiting_cp}
                self.runtime.agent_protocol.mark_attempt_failed(pexec_id, actor_id, reason=f"Gate failure routed as {action['action']}")
                return action

            self.runtime.agent_protocol.update_step(pexec_id, 4, "PASS", actor_id, note="all completion gates passed")
            self.runtime.agent_protocol.verify(pexec_id, actor_id, qa_result="PASS", detail="Runtime outputs, evidence and completion gates verified")
            self.runtime.execution.finalize_workunit(workunit_id, "PASS", gate_result.get("gate_id"))
            for rid in output_revisions.values():
                self.runtime.knowledge.set_validity_system(rid, "VALID")
            for failure_row in self.db.all("SELECT failure_id FROM failures WHERE scope_id=? AND status!='RESOLVED'", (workunit_id,)):
                self.runtime.decision.resolve_failure(failure_row["failure_id"])

            cp = None
            if checkpoint_cfg.get("after_success"):
                cp = self._checkpoint(state, phase_id, "AFTER_PHASE_PASS", next_phase_index=idx + 1)
            decision_outcome = None
            if "decision_record" in output_revisions:
                decision_outcome = self.runtime.knowledge.get_revision(output_revisions["decision_record"])["structured_payload"].get("outcome")
            next_phase = self.phases[idx + 1]["id"] if idx + 1 < len(self.phases) else None
            self.runtime.agent_protocol.write_handoff(
                pexec_id,
                actor_id,
                {
                    "what_was_done": f"{phase_id} completed under pinned skill {skill['skill_revision_id']}.",
                    "what_was_not_done": "",
                    "known_limitations": [],
                    "open_questions": [],
                    "risks": [],
                    "next_phase": next_phase,
                    "next_phase_prerequisites": [],
                    "artifact_refs": list(output_revisions.values()),
                    "evidence_refs": evidence_ids,
                    "checkpoint_id": cp,
                    "markdown": f"# {phase_id} handoff\n\nProtocol, runtime outputs, evidence and completion gates passed.",
                },
            )
            self.runtime.agent_protocol.complete(pexec_id, actor_id)
            self._finish_phase_execution(pexec_id, "SUCCEEDED", checkpoint_id=cp, decision_outcome=decision_outcome)
            return {"action": "SUCCESS", "output_revisions": output_revisions, "evidence_ids": evidence_ids, "checkpoint_id": cp}

        cp = self._checkpoint(state, phase_id, "RETRY_EXHAUSTED", next_phase_index=idx)
        return {"action": "PAUSE", "reason": "RETRY_EXHAUSTED", "checkpoint_id": cp}

    # --------------------------------------------------------------- operations
    def _resolve_inputs(self, project_id: str, phase: dict[str, Any]) -> dict[str, dict[str, Any]]:
        inputs: dict[str, dict[str, Any]] = {}
        for spec in phase.get("inputs", []):
            typ = spec["artifact_type"] if isinstance(spec, dict) else spec
            rev = self._current_revision_by_type(project_id, typ)
            if not rev:
                raise ValidationError(f"Phase {phase['id']} missing input artifact {typ}")
            inputs[typ] = rev
        return inputs

    def _commit_phase_outputs(self, state: dict[str, Any], phase: dict[str, Any], actor_id: str, run_id: str, payloads: dict[str, dict[str, Any]]) -> dict[str, str]:
        result: dict[str, str] = {}
        project_id = state["project_id"]
        expected_types = [x["artifact_type"] if isinstance(x, dict) else x for x in phase.get("outputs", [])]
        missing = [t for t in expected_types if t not in payloads]
        if missing:
            raise ValidationError(f"Phase {phase['id']} did not produce required artifacts", details={"missing": missing})
        for typ in expected_types:
            payload = payloads[typ]
            self.domain.validate_artifact_payload(typ, payload)
            art = self.db.one("SELECT * FROM artifacts WHERE project_id=? AND artifact_type=? ORDER BY created_at LIMIT 1", (project_id, typ))
            if not art:
                aid = self.runtime.knowledge.create_artifact(project_id, typ, f"research:{typ}", actor_id)
                art = self.db.one("SELECT * FROM artifacts WHERE artifact_id=?", (aid,))
            proposal_id = None
            cfg = self.domain.artifact(typ)
            if typ == self.domain.data.get("reporting", {}).get("final_report_artifact"):
                self._validate_reporting_payload(payload)
            if cfg.get("normative"):
                self._checkpoint(state, phase["id"], "BEFORE_NORMATIVE_REVISION", next_phase_index=self.phase_index_by_id[phase["id"]])
                frozen = {"artifact_id": art["artifact_id"], "payload": payload}
                idem = f"research:{state['orchestration_id']}:{state['generation']}:{phase['id']}:{typ}:{content_hash(payload)}"
                proposal_id = self.runtime.governance.prepare_proposal(project_id, actor_id, "CREATE_REVISION", [art["artifact_id"]], frozen, cfg.get("approval_policy"), idem)
                prop = self.db.one("SELECT * FROM proposals WHERE proposal_id=?", (proposal_id,))
                if prop["status"] != "APPROVED":
                    approver = None
                    if self.approval_provider:
                        approver = self.approval_provider(proposal_id, prop["payload_hash"], cfg.get("approval_policy"))
                    elif self.human_approver_id:
                        approver = self.human_approver_id
                    if approver:
                        self.runtime.governance.approve_proposal(proposal_id, approver, prop["payload_hash"])
                    else:
                        raise InvalidTransition(f"Approval required for proposal {proposal_id}")
            created = self.runtime.knowledge.create_revision(art["artifact_id"], payload, actor_id, int(art["version"]), proposal_id=proposal_id, producer_run_id=run_id)
            rid = created["revision_id"]
            result[typ] = rid
            if cfg.get("normative"):
                self._checkpoint(state, phase["id"], "AFTER_NORMATIVE_REVISION", next_phase_index=self.phase_index_by_id[phase["id"]])
            # every output is traceable to all semantic input revisions
            for inp in self._resolve_inputs(project_id, phase).values():
                self.runtime.knowledge.create_trace_link(project_id, rid, "REVISION", inp["revision_id"], "derived_from", "HARD", True, "MARK_STALE", actor_id)
        return result

    def _record_phase_evidence(self, project_id: str, phase: dict[str, Any], actor_id: str, run_id: str, input_ids: list[str], output_revisions: dict[str, str], evidence: list[EvidenceOutput]) -> list[str]:
        by_type = {e.evidence_type: e for e in evidence}
        ids: list[str] = []
        for typ in phase.get("evidence_required", []):
            item = by_type.get(typ)
            if item is None:
                raise ValidationError(f"Phase {phase['id']} missing required evidence {typ}")
            cfg = self.domain.evidence(typ) or {}
            trust = item.trust_class or cfg.get("trust_class", "SUPPORTED")
            subjects = item.subject_refs or list(output_revisions.values()) + input_ids
            ids.append(self.runtime.execution.add_evidence(project_id, typ, actor_id, subjects, item.payload, trust, run_id))
        # preserve optional evidence too
        required = set(phase.get("evidence_required", []))
        for item in evidence:
            if item.evidence_type in required:
                continue
            cfg = self.domain.evidence(item.evidence_type) or {}
            trust = item.trust_class or cfg.get("trust_class", "SUPPORTED")
            ids.append(self.runtime.execution.add_evidence(project_id, item.evidence_type, actor_id, item.subject_refs or list(output_revisions.values()) + input_ids, item.payload, trust, run_id))
        return ids

    def _evaluate_completion_gates(self, project_id: str, phase: dict[str, Any], workunit_id: str, input_ids: list[str], evidence_ids: list[str]) -> dict[str, Any]:
        last = {"result": "PASS", "gate_id": None, "violations": []}
        for gate_type in phase.get("required_gate_types", []):
            r = self.runtime.decision.evaluate_gate(project_id, gate_type, {"workunit_id": workunit_id, "phase_id": phase["id"], "semantics": "POSTCONDITION"}, input_ids, evidence_ids)
            last = r
            if r["result"] != "PASS":
                return r
        return last

    def _route_operational_failure(self, state: dict[str, Any], idx: int, phase: dict[str, Any], workunit_id: str, failure_id: str | None, phase_result: PhaseExecutionResult) -> dict[str, Any]:
        if not failure_id:
            cp = self._checkpoint(state, phase["id"], "FAILURE_RECORD_MISSING", next_phase_index=idx)
            return {"action": "PAUSE", "reason": "FAILURE_RECORD_MISSING", "checkpoint_id": cp}
        route = self.runtime.decision.route_failure(failure_id)
        if route == "RETRY":
            loop = self.runtime.decision.evaluate_loop_guard(failure_id)
            if loop and loop.get("status") == "ESCALATE":
                cp = self._checkpoint(state, phase["id"], "LOOP_GUARD_ESCALATE", next_phase_index=idx)
                self.runtime.decision.create_decision(state["project_id"], {"workunit_id": workunit_id}, "ESCALATE", ["LOOP_GUARD"], source_failure_id=failure_id)
                return {"action": "PAUSE", "reason": "LOOP_GUARD_ESCALATE", "checkpoint_id": cp}
            self.runtime.decision.create_decision(state["project_id"], {"workunit_id": workunit_id}, "RETRY", [self.db.one("SELECT failure_class FROM failures WHERE failure_id=?", (failure_id,))["failure_class"]], source_failure_id=failure_id, target_ref=phase["id"])
            return {"action": "RETRY"}
        if route in {"WAIT", "ESCALATE", "ABORT"}:
            self.runtime.decision.create_decision(state["project_id"], {"workunit_id": workunit_id}, route, ["OPERATIONAL_FAILURE"], source_failure_id=failure_id)
            cp = self._checkpoint(state, phase["id"], f"{route}_REQUIRED", next_phase_index=idx)
            return {"action": "PAUSE", "reason": route, "checkpoint_id": cp}

        # semantic recovery: locate and confirm root, invalidate only affected descendants, resume at producer phase
        root_type = phase_result.root_artifact_type or self._select_root_artifact_type(state["project_id"], failure_id)
        if not root_type or root_type not in self.producer_phase_by_artifact:
            cp = self._checkpoint(state, phase["id"], "ROOT_CAUSE_UNRESOLVED", next_phase_index=idx)
            return {"action": "PAUSE", "reason": "ROOT_CAUSE_UNRESOLVED", "checkpoint_id": cp}
        root = self._current_revision_by_type(state["project_id"], root_type)
        if not root:
            cp = self._checkpoint(state, phase["id"], "ROOT_ARTIFACT_MISSING", next_phase_index=idx)
            return {"action": "PAUSE", "reason": "ROOT_ARTIFACT_MISSING", "checkpoint_id": cp}
        resume_idx = self.producer_phase_by_artifact[root_type]
        if not self.human_approver_id:
            frozen={"failure_id":failure_id,"root_revision_id":root["revision_id"],"root_type":root_type,"resume_phase_id":self.phases[resume_idx]["id"]}
            proposal_id=self.runtime.governance.prepare_system_proposal(state["project_id"],"CONFIRM_ROOT",[failure_id,root["revision_id"]],frozen,"high_impact_research_change")
            state["pending_human_action"]={"type":"CONFIRM_ROOT","proposal_id":proposal_id,"failure_id":failure_id,"root_revision_id":root["revision_id"],"root_type":root_type,"resume_phase_index":resume_idx,"workunit_id":workunit_id,"route":route}
            cp=self._checkpoint(state,phase["id"],"WAITING_AUTHENTICATED_ROOT_CONFIRMATION",next_phase_index=idx,extra={"proposal_id":proposal_id,"failure_id":failure_id})
            return {"action":"PAUSE","reason":"WAITING_HUMAN_CONFIRMATION","checkpoint_id":cp}
        self.runtime.decision.confirm_root(failure_id, root["revision_id"], root_type, self.human_approver_id)
        self.runtime.knowledge.set_validity_system(root["revision_id"], "DIRTY")
        impact = self.runtime.knowledge.compute_impact(state["project_id"], "OPERATIONAL_FAILURE", failure_id, root["revision_id"], apply=True)
        recovery_id = self.runtime.decision.create_recovery_plan(failure_id, impact["impact_id"], self.human_approver_id)
        recovery_cp = self.runtime.execution.apply_recovery_plan(recovery_id)
        self.runtime.decision.create_decision(state["project_id"], {"workunit_id": workunit_id}, route if route in {"REVISE_CURRENT", "REVISE_UPSTREAM", "REPLAN"} else "REVISE_UPSTREAM", ["RECOVERY_PLAN_CREATED"], source_failure_id=failure_id, target_ref=root_type)
        state["recovery_failure_id"] = failure_id
        state["recovery_root_phase_index"] = resume_idx
        state["history"].append({"event": "RECOVERY", "failure_id": failure_id, "root_artifact_type": root_type, "resume_phase": self.phases[resume_idx]["id"], "checkpoint_id": recovery_cp})
        cp = self._checkpoint(state, phase["id"], "RECOVERY_RESUME", next_phase_index=resume_idx, extra={"recovery_id": recovery_id, "recovery_checkpoint": recovery_cp})
        return {"action": "RESUME_AT", "phase_index": resume_idx, "checkpoint_id": cp}

    # --------------------------------------------------------------- persistence
    def _record_phase_execution(self, state, idx, phase_id, workunit_id, run_id, status, *, failure_id=None, checkpoint_id=None, decision_outcome=None):
        peid = uid("pexec")
        self.db.conn.execute(
            "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (peid, state["orchestration_id"], phase_id, idx, state["generation"], workunit_id, run_id, status, decision_outcome, failure_id, checkpoint_id, utcnow(), None, canonical_json({}),),
        )
        self.db.conn.commit()
        return peid

    def _finish_phase_execution(self, peid, status, *, failure_id=None, checkpoint_id=None, decision_outcome=None):
        self.db.conn.execute("UPDATE phase_executions SET status=?,failure_id=COALESCE(?,failure_id),checkpoint_id=COALESCE(?,checkpoint_id),decision_outcome=COALESCE(?,decision_outcome),finished_at=? WHERE phase_execution_id=?", (status, failure_id, checkpoint_id, decision_outcome, utcnow(), peid))
        self.db.conn.commit()

    def _attach_phase_run(self, phase_execution_id: str, run_id: str):
        self.db.conn.execute("UPDATE phase_executions SET run_id=? WHERE phase_execution_id=?", (run_id, phase_execution_id))
        self.db.conn.commit()

    def _previous_successful_phase_execution(self, orchestration_id: str, phase_index: int) -> str | None:
        row = self.db.one(
            "SELECT phase_execution_id FROM phase_executions "
            "WHERE orchestration_id=? AND phase_index<? AND status='SUCCEEDED' "
            "ORDER BY generation DESC,phase_index DESC,finished_at DESC,phase_execution_id DESC LIMIT 1",
            (orchestration_id, int(phase_index)),
        )
        return row["phase_execution_id"] if row else None

    def _record_phase_skip(self, state, idx, phase_id):
        peid = uid("pexec")
        now = utcnow()
        self.db.conn.execute("INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (peid, state["orchestration_id"], phase_id, idx, state["generation"], None, None, "SKIPPED", state.get("outcome"), None, None, now, now, canonical_json({"condition": "false"})))
        self.db.conn.commit()
        state["history"].append({"phase_id": phase_id, "generation": state["generation"], "status": "SKIPPED", "outcome": state.get("outcome")})

    def _checkpoint(self, state: dict[str, Any], phase_id: str, reason: str, *, next_phase_index: int | None = None, extra: dict[str, Any] | None = None) -> str:
        snapshot_state = dict(state)
        snapshot_state["next_phase_index"] = state["next_phase_index"] if next_phase_index is None else next_phase_index
        artifact_hashes={}
        for row in self.db.all("SELECT a.artifact_type,r.revision_id,r.content_hash FROM artifacts a JOIN revisions r ON r.revision_id=a.current_revision_id WHERE a.project_id=?", (state["project_id"],)):
            artifact_hashes[row["artifact_type"]] = {"revision_id": row["revision_id"], "content_hash": row["content_hash"]}
        env_fingerprint=None
        preflight=self._current_revision_by_type(state["project_id"], "preflight_result")
        if preflight:
            env_fingerprint=preflight["structured_payload"].get("environment_fingerprint")
        metadata = {"kind": "RESEARCH_ORCHESTRATOR", "phase_id": phase_id, "reason": reason, "artifact_hashes": artifact_hashes, "environment_fingerprint": env_fingerprint, "research_orchestrator_state": snapshot_state}
        if extra:
            metadata.update(extra)
        return self.runtime.execution.create_checkpoint(state["project_id"], state["orchestration_id"], metadata)

    def _persist_state(self, state: dict[str, Any]):
        current = self.phases[state["next_phase_index"]]["id"] if state["next_phase_index"] < len(self.phases) else None
        self._update_orchestration(state, status="RUNNING", current_phase_id=current)

    def _update_orchestration(self, state, *, status=None, current_phase_id=None, terminal_checkpoint_id=None):
        oid = state["orchestration_id"]
        row = self.db.one("SELECT * FROM orchestrations WHERE orchestration_id=?", (oid,))
        if not row:
            raise NotFound("Orchestration not found")
        self.db.conn.execute(
            "UPDATE orchestrations SET status=?,current_phase_id=?,generation=?,research_outcome=?,pivot_count=?,updated_at=?,terminal_checkpoint_id=COALESCE(?,terminal_checkpoint_id),metadata=? WHERE orchestration_id=?",
            (status or row["status"], current_phase_id, int(state.get("generation", 0)), state.get("outcome"), int(state.get("pivot_count", 0)), utcnow(), terminal_checkpoint_id, canonical_json(state), oid),
        )
        self.db.conn.commit()

    def _pause(self, state, reason, checkpoint_id=None):
        cp = checkpoint_id or self._checkpoint(state, self.phases[min(state["next_phase_index"], len(self.phases)-1)]["id"], reason, next_phase_index=state["next_phase_index"])
        self._update_orchestration(state, status="PAUSED", current_phase_id=self.phases[state["next_phase_index"]]["id"] if state["next_phase_index"] < len(self.phases) else None, terminal_checkpoint_id=cp)
        self.runtime.observe("orchestration_paused", project_id=state["project_id"], orchestration_id=state["orchestration_id"], reason=reason, checkpoint_id=cp, generation=state.get("generation"))
        return {"status": "PAUSED", "reason": reason, "orchestration_id": state["orchestration_id"], "project_id": state["project_id"], "checkpoint_id": cp, "outcome": state.get("outcome"), "generation": state.get("generation"), "pivot_count": state.get("pivot_count")}

    def _validate_reporting_payload(self, payload: dict[str, Any]):
        cfg=self.domain.data.get("reporting", {})
        required=[]
        mapping={
            "require_negative_results":"negative_results",
            "require_failed_runs":"failed_runs",
            "require_pivot_history":"pivot_history",
            "require_protocol_deviations":"protocol_deviations",
            "require_open_questions":"open_questions",
            "require_claims_evidence_matrix":"claims_evidence_matrix",
            "require_reproduction_commands":"reproduction_commands",
            "require_environment_manifest":"environment_manifest",
            "require_exact_revision_ids":"exact_revision_ids",
        }
        for flag,field in mapping.items():
            if cfg.get(flag): required.append(field)
        missing=[x for x in required if x not in payload]
        if missing:
            raise ValidationError("Final report violates reporting contract", details={"missing":missing})

    def _latest_checkpoint_id(self, project_id: str) -> str | None:
        r=self.db.one("SELECT checkpoint_id FROM checkpoints WHERE project_id=? ORDER BY created_at DESC LIMIT 1", (project_id,))
        return r["checkpoint_id"] if r else None

    # ---------------------------------------------------------------- utilities
    def _current_revision_by_type(self, project_id: str, artifact_type: str) -> dict[str, Any] | None:
        row = self.db.one("SELECT current_revision_id FROM artifacts WHERE project_id=? AND artifact_type=? ORDER BY created_at LIMIT 1", (project_id, artifact_type))
        if not row or not row["current_revision_id"]:
            return None
        return self.runtime.knowledge.get_revision(row["current_revision_id"])

    def _current_revision_ids(self, project_id: str) -> dict[str, str]:
        return {a["artifact_type"]: a["current_revision_id"] for a in self.db.all("SELECT artifact_type,current_revision_id FROM artifacts WHERE project_id=? AND current_revision_id IS NOT NULL", (project_id,))}

    def _current_artifact_payloads(self, project_id: str) -> dict[str, dict[str, Any]]:
        out = {}
        for a in self.db.all("SELECT artifact_type,current_revision_id FROM artifacts WHERE project_id=?", (project_id,)):
            if a["current_revision_id"]:
                out[a["artifact_type"]] = self.runtime.knowledge.get_revision(a["current_revision_id"])["structured_payload"]
        return out

    def _should_execute(self, phase: dict[str, Any], state: dict[str, Any]) -> bool:
        cond = phase.get("execution_condition")
        if not cond:
            return True
        outcome = state.get("outcome")
        if re.fullmatch(r"decision_record\.outcome\s*==\s*PIVOT", str(cond)):
            return outcome == "PIVOT"
        if re.fullmatch(r"decision_record\.outcome\s+in\s+\[PASS,\s*FAIL\]", str(cond)):
            return outcome in {"PASS", "FAIL"}
        raise ValidationError(f"Unsupported research execution_condition: {cond}")

    def _select_root_artifact_type(self, project_id: str, failure_id: str) -> str | None:
        f = self.db.one("SELECT failure_class FROM failures WHERE failure_id=?", (failure_id,))
        if not f:
            return None
        cfg = self.domain.failure(f["failure_class"]) or {}
        for typ in cfg.get("root_candidates", []):
            if self._current_revision_by_type(project_id, typ):
                return typ
        return None

    @staticmethod
    def _fallback_failure_class(phase: dict[str, Any]) -> str:
        known = phase.get("known_failure_modes", [])
        return known[0] if known else "approval_missing"
