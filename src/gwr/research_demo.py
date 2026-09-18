from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .research_orchestrator import EvidenceOutput, PhaseExecutionResult, ResearchExecutionContext


@dataclass
class DeterministicResearchExecutor:
    """Deterministic executor used for v0.2 acceptance/QA experiments.

    This is deliberately synthetic: it validates orchestration semantics, not a
    scientific claim. Real users replace it with an executor that calls tools,
    models, scripts, experiment runners, and reviewers.
    """

    scenario: str = "pass"  # pass | fail | pivot | runtime_retry | runtime_recovery

    def execute(self, context: ResearchExecutionContext) -> PhaseExecutionResult:
        # Operational failure scenarios are injected before normal output generation.
        if self.scenario == "runtime_retry" and context.phase_id == "phase_09_main_experiment" and context.attempt == 1:
            return PhaseExecutionResult(
                runtime_status="FAILED",
                failure_class="runtime_timeout",
                failure_reason="synthetic timeout on first main-experiment attempt",
                root_artifact_type="implementation_manifest",
            )
        if self.scenario == "runtime_recovery" and context.phase_id == "phase_08_pilot" and context.generation == 0:
            return PhaseExecutionResult(
                runtime_status="FAILED",
                failure_class="protocol_mismatch",
                failure_reason="synthetic pilot exposed protocol mismatch",
                root_artifact_type="protocol",
            )

        phase = context.domain.workunit(context.phase_id)
        artifacts: dict[str, dict[str, Any]] = {}
        for out in phase.get("outputs", []):
            typ = out["artifact_type"] if isinstance(out, dict) else out
            artifacts[typ] = self._payload_for(typ, context)

        evidence = []
        gate_assertions=[]
        for gate_type in phase.get("required_gate_types", []):
            gate=context.domain.gate(gate_type) or {}
            gate_assertions.extend(gate.get("pass_if",[]) or [])
        assertions=sorted(set(list(phase.get("success_conditions", [])) + gate_assertions))
        for ev_type in phase.get("evidence_required", []):
            evidence.append(EvidenceOutput(ev_type, {
                "pass": True,
                "scenario": self.scenario,
                "phase": context.phase_id,
                "generation": context.generation,
                "attempt": context.attempt,
                "assertions": assertions,
            }))
        return PhaseExecutionResult(runtime_status="COMPLETED", artifacts=artifacts, evidence=evidence)

    def _payload_for(self, artifact_type: str, context: ResearchExecutionContext) -> dict[str, Any]:
        cfg = context.domain.artifact(artifact_type)
        payload = {field: self._field_value(field, artifact_type, context) for field in cfg.get("required_fields", [])}
        payload["_synthetic"] = True
        payload["_scenario"] = self.scenario
        payload["_phase"] = context.phase_id
        payload["_generation"] = context.generation

        if artifact_type == "decision_record":
            if self.scenario == "fail":
                outcome = "FAIL"
            elif self.scenario == "pivot" and context.generation == 0:
                outcome = "PIVOT"
            else:
                outcome = "PASS"
            payload.update({
                "outcome": outcome,
                "evidence_summary": f"synthetic evidence for {outcome}",
                "threshold_evaluation": {"precommitted_gate": outcome != "FAIL"},
                "violated_assumptions": ["synthetic_support_threshold"] if outcome == "FAIL" else [],
                "confidence_band": "synthetic-only",
                "next_action": "pivot" if outcome == "PIVOT" else "replicate_and_report",
            })
        elif artifact_type == "pivot_plan":
            payload.update({
                "reason": "synthetic pivot to exercise upstream resume",
                "preserved_findings": ["raw evidence", "negative results", "audit history"],
                "invalidated_assumptions": ["protocol assumption v1"],
                "new_or_revised_question": "same goal, revised protocol",
                "new_or_revised_hypothesis": "same hypothesis under revised protocol",
                "earliest_resume_artifact": "protocol",
                "rerun_scope": "minimal affected downstream subgraph",
            })
        elif artifact_type == "final_report":
            payload.update({
                "executive_summary": f"Synthetic v0.2 {self.scenario} orchestration report artifact",
                "research_question": "Can the runtime execute checkpointed research workflow semantics?",
                "decision_history": [h for h in context.history if h.get("phase_id") == "phase_12_decide_pass_fail_pivot" or h.get("event") == "PIVOT"],
                "limitations": ["Synthetic executor; does not validate an external scientific claim"],
                "open_questions": [],
                "claims_evidence_matrix": [{"claim": "orchestration path completed", "evidence": "audit/checkpoints/tests"}],
                "reproducibility_instructions": "pytest; python tools/run_research_demo.py",
                "negative_results": [h for h in context.history if h.get("outcome") == "FAIL"],
                "failed_runs": [h for h in context.history if h.get("status") == "FAILED"],
                "pivot_history": [h for h in context.history if h.get("event") == "PIVOT"],
                "protocol_deviations": [],
                "reproduction_commands": ["pytest", f"python tools/run_research_demo.py --scenario {self.scenario}"],
                "environment_manifest": {"executor": "DeterministicResearchExecutor", "synthetic": True},
                "exact_revision_ids": dict(context.current_revision_ids),
            })
        elif artifact_type == "handoff_package":
            payload.update({
                "current_status": "complete",
                "artifact_manifest": sorted(context.current_artifacts.keys()),
                "checkpoint_ref": context.latest_checkpoint_id,
                "unresolved_issues": [],
                "exact_resume_target": None,
                "next_actions": ["replace synthetic executor with real research adapters"],
                "commands": ["pytest", "python tools/run_research_demo.py --scenario pass"],
                "hashes": {"domain": context.domain.data.get("version")},
            })
        return payload

    @staticmethod
    def _field_value(field: str, artifact_type: str, context: ResearchExecutionContext) -> Any:
        # Type-shape is intentionally simple but stable and human-readable.
        listish = {
            "sources", "closest_prior_work", "differentiators", "unresolved_questions", "overlaps", "borrowed_ideas", "risks",
            "predictions", "falsification_criteria", "definitions", "assumptions", "variables", "equations", "invariants", "boundary_conditions",
            "controls", "independent_variables", "dependent_variables", "metrics", "thresholds", "leakage_controls", "confound_controls", "stopping_rules",
            "data_sources", "splits", "sampling", "inclusion_exclusion", "contamination_checks", "benchmark_cases", "seeds", "runs", "baselines", "ablations",
            "adversarial_cases", "resources", "expected_artifacts", "exact_commands", "dependencies", "commands", "config_hashes", "checks", "failures", "warnings",
            "raw_metrics", "anomalies", "run_ids", "aggregate_metrics", "logs", "artifacts", "provenance", "statistical_results", "effect_sizes", "uncertainty",
            "robustness", "baseline_comparison", "assumption_checks", "falsification_attempts", "alternative_explanations", "confounds", "boundary_failures",
            "independent_seed_or_environment", "reproduced_metrics", "divergence", "hypothesis_lineage", "prior_art", "formalization", "protocol", "implementation",
            "experiments", "results", "falsification", "replication", "artifact_manifest", "unresolved_issues", "next_actions", "hashes",
        }
        dictish = {"experimental_design", "statistical_plan", "pass_fail_pivot_rules", "gold_or_oracle_definition", "environment", "environment_fingerprint", "power_or_signal_check"}
        boolish = {"feasibility"}
        if field in listish:
            return [f"{artifact_type}:{field}:g{context.generation}"]
        if field in dictish:
            return {"value": f"{artifact_type}:{field}:g{context.generation}"}
        if field in boolish:
            return True
        return f"{artifact_type}:{field}:g{context.generation}"
