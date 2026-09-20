from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .research_orchestrator import EvidenceOutput, PhaseExecutionResult, ResearchExecutionContext


@dataclass
class DeterministicSoftwareExecutor:
    """Synthetic executor for validating software-domain orchestration semantics."""

    scenario: str = "pass"

    def execute(self, context: ResearchExecutionContext) -> PhaseExecutionResult:
        phase = context.domain.workunit(context.phase_id)
        artifacts: dict[str, dict[str, Any]] = {}
        for out in phase.get("outputs", []):
            typ = out["artifact_type"] if isinstance(out, dict) else out
            artifacts[typ] = self._payload_for(typ, context)

        gate_assertions: list[str] = []
        for gate_type in phase.get("required_gate_types", []):
            gate = context.domain.gate(gate_type) or {}
            gate_assertions.extend(gate.get("pass_if", []) or [])
        assertions = sorted(
            set(list(phase.get("success_conditions", [])) + gate_assertions)
        )
        evidence = [
            EvidenceOutput(
                ev_type,
                {
                    "pass": True,
                    "scenario": self.scenario,
                    "phase": context.phase_id,
                    "generation": context.generation,
                    "attempt": context.attempt,
                    "assertions": assertions,
                },
            )
            for ev_type in phase.get("evidence_required", [])
        ]
        return PhaseExecutionResult(
            runtime_status="COMPLETED",
            artifacts=artifacts,
            evidence=evidence,
        )

    def _payload_for(
        self,
        artifact_type: str,
        context: ResearchExecutionContext,
    ) -> dict[str, Any]:
        cfg = context.domain.artifact(artifact_type)
        payload = {
            field: self._field_value(field, artifact_type, context)
            for field in cfg.get("required_fields", [])
        }
        payload["_synthetic"] = True
        payload["_phase"] = context.phase_id
        payload["_generation"] = context.generation

        if artifact_type == "repo_baseline":
            payload.update(
                {
                    "repository": "example/software",
                    "default_branch": "main",
                    "verified_head_sha": "a" * 40,
                }
            )
        elif artifact_type == "change_set_manifest":
            payload.update(
                {
                    "branch": "feature/v085-demo",
                    "expected_head_sha": "a" * 40,
                }
            )
        elif artifact_type == "local_test_result":
            payload.update(
                {
                    "passed": ["dedicated", "compile", "static"],
                    "failed": [],
                    "compile_status": "PASS",
                    "environment_fingerprint": "synthetic-env-v085",
                }
            )
        elif artifact_type == "qa_report":
            payload.update({"verdict": "PASS"})
        elif artifact_type == "candidate_record":
            payload.update(
                {
                    "candidate_sha": "b" * 40,
                    "base_sha": "a" * 40,
                    "qa_verdict": "PASS",
                    "merge_ready": True,
                }
            )
        elif artifact_type == "merge_record":
            payload.update(
                {
                    "candidate_sha": "b" * 40,
                    "expected_main_sha": "a" * 40,
                    "merge_sha": "c" * 40,
                    "conflict_status": "NONE",
                }
            )
        elif artifact_type == "exact_main_verification":
            payload.update(
                {
                    "main_sha": "c" * 40,
                    "all_required_pass": True,
                }
            )
        elif artifact_type == "handoff_package":
            payload.update(
                {
                    "current_status": "VERIFIED",
                    "baseline_sha": "a" * 40,
                    "candidate_sha": "b" * 40,
                    "main_sha": "c" * 40,
                    "open_issues": [],
                    "known_limits": ["synthetic executor"],
                    "next_actions": ["replace synthetic executor with real tools"],
                    "exact_resume_target": None,
                }
            )
        return payload

    @staticmethod
    def _field_value(
        field: str,
        artifact_type: str,
        context: ResearchExecutionContext,
    ) -> Any:
        listish = {
            "constraints",
            "non_goals",
            "acceptance_criteria",
            "rollback_conditions",
            "inspected_paths",
            "current_workflows",
            "current_test_surfaces",
            "known_risks",
            "in_scope",
            "out_of_scope",
            "invariants",
            "definition_of_done",
            "required_test_matrix",
            "files_expected",
            "implementation_steps",
            "test_plan",
            "risk_register",
            "file_changes",
            "expected_blob_shas",
            "proposed_content_hashes",
            "changed_files",
            "commit_shas",
            "deviations",
            "unresolved_items",
            "test_commands",
            "passed",
            "failed",
            "static_checks",
            "logs",
            "suites",
            "databases",
            "workflows",
            "compatibility_findings",
            "evidence_refs",
            "acceptance_matrix",
            "regressions",
            "security_checks",
            "sha_checks",
            "known_limits",
            "workflow_runs",
            "artifact_digests",
            "required_workflows",
            "workflow_results",
            "regression_summary",
            "evidence_manifest",
            "open_issues",
            "next_actions",
        }
        dictish = {
            "deployment_boundary",
            "rollback_boundary",
            "migration_plan",
            "compatibility_plan",
            "build_output",
        }
        boolish = {"merge_ready", "all_required_pass"}
        if field in listish:
            return [f"{artifact_type}:{field}:g{context.generation}"]
        if field in dictish:
            return {"value": f"{artifact_type}:{field}:g{context.generation}"}
        if field in boolish:
            return True
        return f"{artifact_type}:{field}:g{context.generation}"
