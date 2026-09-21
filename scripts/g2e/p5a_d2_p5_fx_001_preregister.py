from __future__ import annotations

import hashlib
import json
from pathlib import Path

from g2e import (
    AgentBinding,
    AgentEquivalencePolicy,
    AmendmentPolicy,
    BindingMode,
    DecisionExpression,
    DecisionRule,
    EvidenceAdmissionPolicy,
    IndependencePolicy,
    MetricPredicate,
    ProofLifecycle,
    ProofObligation,
    ProofRetryPolicy,
    Provenance,
)
from g2e.canonical import ExactRef


MANIFEST_REF = ExactRef(
    object_id="agent-capability-manifest-codex-d1",
    revision_id="a337b7433ebb351c-d1-v1",
    content_hash="585d59b32457484e8d4706c3e79a94398569ab4bc3e39ff8fca5502541ece5c5",
)
HARNESS_SHA256 = "a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8"
PROVENANCE = Provenance(
    created_by="g2e-p5a-d2-preregister",
    created_at="2026-09-21T12:05:44.250506Z",
    source_refs=(
        "git:65ff301315cd577c98c5ba6c05d4cb8d4a92c504:g2e/docs/P5A_CODEX_D1_MANIFEST_EVIDENCE.json",
        "manifest:agent-capability-manifest-codex-d1@a337b7433ebb351c-d1-v1#585d59b32457484e8d4706c3e79a94398569ab4bc3e39ff8fca5502541ece5c5",
    ),
    derivation="Prospective P5A D2 P5-FX-001 preregistration only; no model turn",
)

TASK_TEXT = """Read input.json in the current workspace.

Create exactly one file named result.json in the current workspace.
Do not modify input.json or TASK.md.
Do not create, rename, or delete any other file or directory.
Do not use network access.

result.json must be valid JSON with exactly these keys:
- count
- sum
- sorted_unique_values
- input_sha256

count is the number of integers in input.json.values.
sum is their mathematical integer sum.
sorted_unique_values is the ascending sorted list of distinct integers.
input_sha256 is the lowercase SHA-256 of canonical input.json bytes supplied by the qualification harness.

Do not include commentary in result.json.
When the file is written, stop.
"""


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def fixture_input(seed: str = "g2e-p5-agent-profile-v1", count: int = 32) -> dict:
    values: list[int] = []
    block = seed.encode("utf-8")
    while len(values) < count:
        block = hashlib.sha256(block).digest()
        for i in range(0, len(block), 4):
            chunk = block[i : i + 4]
            if len(chunk) < 4:
                continue
            values.append(int.from_bytes(chunk, "big", signed=False) - (1 << 31))
            if len(values) == count:
                break
    return {"generator_version": "p5-fx-001-v1", "seed": seed, "values": values}


def sealed(cls, object_id: str, revision_id: str, **kwargs):
    return cls.sealed(
        object_id=object_id,
        revision_id=revision_id,
        provenance=PROVENANCE,
        **kwargs,
    )


def build_contract() -> dict:
    input_payload = fixture_input()
    input_bytes = canonical_bytes(input_payload)
    input_sha = hashlib.sha256(input_bytes).hexdigest()
    task_sha = hashlib.sha256(TASK_TEXT.encode("utf-8")).hexdigest()

    retry = sealed(
        ProofRetryPolicy,
        "p5a-d2-retry",
        "p5-fx-001-v1",
        max_invalid_replacement_attempts=0,
        require_same_semantic_proof_identity=True,
        allowed_technical_reason_codes=(),
    )
    amendment = sealed(
        AmendmentPolicy,
        "p5a-d2-amendment",
        "p5-fx-001-v1",
        allow_editorial=False,
        normative_pre_outcome_requires_refreeze=True,
        normative_post_outcome_requires_new_lineage=True,
    )
    independence = sealed(
        IndependencePolicy,
        "p5a-d2-independence",
        "p5-fx-001-v1",
        required_dimensions=(),
        forbidden_shared_ancestor_classes=(),
    )
    admission = sealed(
        EvidenceAdmissionPolicy,
        "p5a-d2-evidence-admission",
        "p5-fx-001-v1",
        accepted_source_classes=("codex_p5_fx_001_d2",),
        require_integrity_hash=True,
        require_attempt_linkage=True,
        allowed_freshness_states=(),
        independence_requirements=(),
        allowed_derivation_depth=0,
        missing_data_behavior="INVALID",
    )

    pass_children = tuple(
        DecisionExpression(
            op="PREDICATE",
            predicate=MetricPredicate(metric_id=metric, operator="EQ", threshold_key="one"),
        )
        for metric in (
            "executor_completed",
            "result_schema_valid",
            "result_values_correct",
            "mutation_scope_valid",
            "attempt_attribution_valid",
            "evidence_integrity_valid",
        )
    )
    fail_children = tuple(
        DecisionExpression(
            op="PREDICATE",
            predicate=MetricPredicate(metric_id=metric, operator="EQ", threshold_key="zero"),
        )
        for metric in (
            "result_schema_valid",
            "result_values_correct",
            "mutation_scope_valid",
        )
    )
    decision = sealed(
        DecisionRule,
        "p5a-d2-decision-rule",
        "p5-fx-001-v1",
        pass_expression=DecisionExpression(op="ALL", children=pass_children),
        fail_expression=DecisionExpression(op="ANY", children=fail_children),
        missing_metric_behavior="INVALID",
        metric_conflict_behavior="INVALID",
    )
    proof = sealed(
        ProofObligation,
        "p5a-d2-p5-fx-001-proof",
        "p5-fx-001-v1",
        lifecycle=ProofLifecycle.FROZEN,
        target_claim_id="p5a-d2-codex-functional-qualification",
        proposition="The exact D1-qualified Codex harness completes P5-FX-001 within the frozen workspace, mutation, authority and evidence contract.",
        assumptions=("D1 exact harness identity remains unchanged",),
        controls=("single scientific attempt", "no network", "no interactive approval", "zero retry"),
        fixture_or_population_ref=f"sha256:{input_sha}",
        metric_ids=(
            "executor_completed",
            "result_schema_valid",
            "result_values_correct",
            "mutation_scope_valid",
            "attempt_attribution_valid",
            "evidence_integrity_valid",
        ),
        decision_thresholds={"one": "1", "zero": "0"},
        decision_rule_ref=decision.exact_ref(),
        baseline_refs=(),
        evidence_admission_policy_ref=admission.exact_ref(),
        retry_policy_ref=retry.exact_ref(),
        amendment_policy_ref=amendment.exact_ref(),
        independence_policy_ref=independence.exact_ref(),
        protected_resource_refs=(),
        protected_resource_cost=0,
        resource_cost_class=1,
        implementation_complexity=1,
        stop_conditions=("first terminal attempt only", "timeout at 90 seconds"),
    )
    equivalence = sealed(
        AgentEquivalencePolicy,
        "p5a-d2-agent-equivalence",
        "p5-fx-001-v1",
        material_dimensions=("agent_app", "provider_ref", "model_ref", "harness_ref", "transport_ref"),
        allowed_substitution_dimensions=(),
    )
    preflight_binding = sealed(
        AgentBinding,
        "p5a-d2-preflight-binding",
        "p5-fx-001-v1",
        resolved_attempt_id="p5a-d2-p5-fx-001-attempt-001",
        agent_app="codex",
        capability_manifest_ref=MANIFEST_REF,
        equivalence_policy_ref=equivalence.exact_ref(),
        binding_mode=BindingMode.FROZEN,
        harness_ref=f"sha256:{HARNESS_SHA256}",
        provider_ref=None,
        model_ref=None,
        transport_ref="app-server-stdio",
        required_capability_ids=(
            "app_server_launch",
            "jsonrpc_initialize",
            "thread_lifecycle_surface",
            "turn_stream_surface",
            "external_session_attribution_surface",
        ),
        execution_constraints=("d2_preregistration_only", "no_dispatch_authority"),
        authority_scope=(),
        resolved_at="2026-09-21T12:05:44.250506Z",
        resolution_ref="p5a-d2-zero-fresh-preregistration",
    )

    return {
        "fixture": {
            "id": "P5-FX-001",
            "input": input_payload,
            "input_sha256": input_sha,
            "task_sha256": task_sha,
            "task_text": TASK_TEXT,
            "pre_workspace": ["TASK.md", "input.json"],
            "only_permitted_post_addition": "result.json",
        },
        "timeouts": {"startup_seconds": 12, "turn_seconds": 90, "verifier_seconds": 10},
        "approval_policy": {
            "interactive_approval": "DENY",
            "network": "DENY",
            "outside_workspace": "DENY",
            "allowed_reads": ["input.json", "TASK.md"],
            "allowed_writes": ["result.json"],
        },
        "required_execution_authority": ("READ_FROZEN_FIXTURE", "WRITE_DESIGNATED_OUTPUT"),
        "decision_rule": decision.model_dump(mode="json"),
        "evidence_admission_policy": admission.model_dump(mode="json"),
        "retry_policy": retry.model_dump(mode="json"),
        "amendment_policy": amendment.model_dump(mode="json"),
        "independence_policy": independence.model_dump(mode="json"),
        "proof_obligation": proof.model_dump(mode="json"),
        "agent_equivalence_policy": equivalence.model_dump(mode="json"),
        "preflight_agent_binding": preflight_binding.model_dump(mode="json"),
        "refs": {
            "manifest": MANIFEST_REF.model_dump(mode="json"),
            "decision_rule": decision.exact_ref().model_dump(mode="json"),
            "evidence_admission_policy": admission.exact_ref().model_dump(mode="json"),
            "retry_policy": retry.exact_ref().model_dump(mode="json"),
            "amendment_policy": amendment.exact_ref().model_dump(mode="json"),
            "independence_policy": independence.exact_ref().model_dump(mode="json"),
            "proof_obligation": proof.exact_ref().model_dump(mode="json"),
            "agent_equivalence_policy": equivalence.exact_ref().model_dump(mode="json"),
            "preflight_agent_binding": preflight_binding.exact_ref().model_dump(mode="json"),
        },
        "execution_admission": {
            "authorized": False,
            "reason": "D2-F01",
            "manifest_max_authority_scope": [],
            "required_execution_authority": ["READ_FROZEN_FIXTURE", "WRITE_DESIGNATED_OUTPUT"],
            "final_execution_agent_binding_frozen": False,
        },
        "runtime_adapter_authorized": False,
        "model_turn_authorized": False,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="P5A_D2_P5_FX_001_PREREGISTRATION.json")
    args = parser.parse_args()
    report = build_contract()
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "proof_ref": report["refs"]["proof_obligation"],
        "preflight_binding_ref": report["refs"]["preflight_agent_binding"],
        "input_sha256": report["fixture"]["input_sha256"],
        "task_sha256": report["fixture"]["task_sha256"],
        "execution_admission": report["execution_admission"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
