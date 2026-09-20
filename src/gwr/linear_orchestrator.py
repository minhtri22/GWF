from __future__ import annotations

from typing import Any

from .errors import ValidationError
from .research_orchestrator import ResearchOrchestrator


class LinearDomainOrchestrator(ResearchOrchestrator):
    """Governed sequential orchestrator for non-research domain packages.

    It deliberately reuses the same authoritative execution path as the research
    orchestrator (skill pinning, protocol stages, evidence, gates, recovery,
    checkpoints and handoffs) while leaving domain-specific decision semantics to
    the domain itself. No research PASS/FAIL/PIVOT shortcuts are inherited.
    """

    state_key = "linear_domain_orchestrator_state"
    checkpoint_kind = "LINEAR_DOMAIN_ORCHESTRATOR"
    orchestration_audit_type = "LinearDomainOrchestration"
    orchestration_started_event = "domain_orchestration_started"
    orchestration_resumed_event = "domain_orchestration_resumed"
    orchestration_paused_event = "domain_orchestration_paused"

    def __init__(
        self,
        runtime,
        actor_by_role: dict[str, str],
        *,
        human_approver_id: str | None = None,
        approval_provider=None,
    ):
        self.runtime = runtime
        self.db = runtime.db
        self.domain = runtime.domain
        mode = str(self.domain.data.get("orchestration_mode") or "").strip().lower()
        if mode != "linear":
            raise ValidationError(
                "LinearDomainOrchestrator requires orchestration_mode: linear",
                details={"domain_id": self.domain.domain_id, "orchestration_mode": mode or None},
            )
        self.actor_by_role = dict(actor_by_role)
        self.human_approver_id = human_approver_id
        self.approval_provider = approval_provider
        self.phases = [
            w for w in self.domain.workunits()
            if str(w.get("id", "")).startswith("phase_")
        ]
        if not self.phases:
            raise ValidationError("Linear domain must define at least one phase")
        self.phase_index_by_id = {p["id"]: i for i, p in enumerate(self.phases)}
        if len(self.phase_index_by_id) != len(self.phases):
            raise ValidationError("Linear domain phase ids must be unique")
        self.producer_phase_by_artifact: dict[str, int] = {}
        for i, phase in enumerate(self.phases):
            for out in phase.get("outputs", []):
                typ = out["artifact_type"] if isinstance(out, dict) else out
                self.producer_phase_by_artifact[typ] = i

    def _drive(self, state: dict[str, Any], executor, *, max_steps: int) -> dict[str, Any]:
        steps = 0
        while state["next_phase_index"] < len(self.phases):
            if steps >= max_steps:
                return self._pause(state, "MAX_STEPS_EXCEEDED")
            steps += 1
            idx = int(state["next_phase_index"])
            phase = self.phases[idx]
            phase_id = phase["id"]
            self.runtime.observe(
                "domain_phase_started",
                project_id=state["project_id"],
                orchestration_id=state["orchestration_id"],
                phase_id=phase_id,
                generation=state["generation"],
                domain_id=self.domain.domain_id,
            )
            self._update_orchestration(
                state,
                status="RUNNING",
                current_phase_id=phase_id,
            )

            if not self._should_execute(phase, state):
                self._record_phase_skip(state, idx, phase_id)
                state["next_phase_index"] = idx + 1
                self._persist_state(state)
                continue

            result = self._execute_phase(state, idx, phase, executor)
            if result["action"] == "PAUSE":
                return self._pause(state, result["reason"], result.get("checkpoint_id"))
            if result["action"] == "RESUME_AT":
                state["next_phase_index"] = int(result["phase_index"])
                state["generation"] += 1
                state["outcome"] = None
                self._persist_state(state)
                continue

            state["history"].append(
                {
                    "phase_id": phase_id,
                    "generation": state["generation"],
                    "status": "PASS",
                    "checkpoint_id": result.get("checkpoint_id"),
                }
            )
            self.runtime.observe(
                "domain_phase_passed",
                project_id=state["project_id"],
                orchestration_id=state["orchestration_id"],
                phase_id=phase_id,
                generation=state["generation"],
                checkpoint_id=result.get("checkpoint_id"),
                domain_id=self.domain.domain_id,
            )

            if (
                state.get("recovery_failure_id")
                and state.get("recovery_root_phase_index") == idx
            ):
                self.runtime.decision.resolve_failure(state["recovery_failure_id"])
                state["history"].append(
                    {
                        "event": "RECOVERY_RESOLVED",
                        "failure_id": state["recovery_failure_id"],
                        "phase_id": phase_id,
                    }
                )
                state["recovery_failure_id"] = None
                state["recovery_root_phase_index"] = None

            state["next_phase_index"] = idx + 1
            self._persist_state(state)

        terminal_phase = self.phases[-1]["id"]
        terminal_cp = self._checkpoint(
            state,
            terminal_phase,
            "TERMINAL",
            next_phase_index=len(self.phases),
        )
        self._update_orchestration(
            state,
            status="COMPLETED",
            current_phase_id=None,
            terminal_checkpoint_id=terminal_cp,
        )
        self.runtime.observe(
            "domain_orchestration_completed",
            project_id=state["project_id"],
            orchestration_id=state["orchestration_id"],
            domain_id=self.domain.domain_id,
            generation=state.get("generation"),
        )
        return {
            "status": "COMPLETED",
            "orchestration_id": state["orchestration_id"],
            "project_id": state["project_id"],
            "domain_id": self.domain.domain_id,
            "generation": state["generation"],
            "terminal_checkpoint_id": terminal_cp,
        }

    def _should_execute(self, phase: dict[str, Any], state: dict[str, Any]) -> bool:
        cond = phase.get("execution_condition")
        if cond in (None, "", "ALWAYS"):
            return True
        raise ValidationError(
            "Linear domain uses explicit phases; unsupported execution_condition",
            details={"phase_id": phase["id"], "execution_condition": cond},
        )
