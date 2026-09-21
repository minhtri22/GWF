from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from g2e import (
    AgentBinding,
    AgentCapability,
    AgentCapabilityManifest,
    AgentEquivalencePolicy,
    AgentProfileAvailability,
    AttemptState,
    BindingMode,
    ExecutionAttemptEnvelope,
    ExecutionResult,
    Provenance,
    SCHEMA_REGISTRY,
    validate_agent_binding_identity,
)
from g2e.canonical import ExactRef
from g2e.standalone import LocalExecutionOutcome, StandaloneRuntime


P = Provenance(created_by="p1.4-test", created_at="2026-09-21T10:45:00Z")
DUMMY_PROOF = ExactRef(object_id="proof-agent", revision_id="r1", content_hash="a" * 64)
DUMMY_RETRY = ExactRef(object_id="retry-agent", revision_id="r1", content_hash="b" * 64)


def sealed(cls, object_id: str, **kwargs):
    return cls.sealed(
        object_id=object_id,
        revision_id="r1",
        provenance=P,
        **kwargs,
    )


def agent_contract(*, capability_available: bool = True, max_authority=("READ", "WRITE")):
    capability = AgentCapability(
        capability_id="repository_read",
        available=capability_available,
        qualification_refs=("fixture:repo-read",) if capability_available else (),
    )
    manifest = sealed(
        AgentCapabilityManifest,
        "agent-manifest",
        agent_app="fixture-agent",
        profile_version="1",
        harness_ref="fixture-harness@1",
        exact_harness_revision="fixture-harness-sha",
        provider_ref="fixture-provider",
        model_ref="fixture-model",
        transport_ref="native",
        availability=AgentProfileAvailability.AVAILABLE,
        capabilities=(capability,),
        execution_constraints=("workspace:repo",),
        max_authority_scope=max_authority,
        credential_ref_classes=(),
        external_session_attribution=True,
        interruption_supported=True,
        artifact_extraction_supported=True,
        structured_output_supported=True,
        status_normalization_supported=True,
        discovery_evidence_refs=("fixture:discovery",),
    )
    equivalence = sealed(
        AgentEquivalencePolicy,
        "agent-equivalence",
        material_dimensions=(
            "agent_app",
            "provider_ref",
            "model_ref",
            "harness_ref",
            "transport_ref",
        ),
        allowed_substitution_dimensions=("model_ref",),
    )
    binding = sealed(
        AgentBinding,
        "agent-binding",
        resolved_attempt_id="attempt-agent",
        agent_app=manifest.agent_app,
        capability_manifest_ref=manifest.exact_ref(),
        equivalence_policy_ref=equivalence.exact_ref(),
        binding_mode=BindingMode.FROZEN,
        harness_ref=manifest.harness_ref,
        provider_ref=manifest.provider_ref,
        model_ref=manifest.model_ref,
        transport_ref=manifest.transport_ref,
        required_capability_ids=("repository_read",),
        execution_constraints=("workspace:repo",),
        authority_scope=("READ",),
        resolved_at="2026-09-21T10:45:00Z",
        resolution_ref="fixture:resolution",
    )
    return manifest, equivalence, binding


def agent_attempt(binding: AgentBinding):
    return sealed(
        ExecutionAttemptEnvelope,
        "attempt-envelope-agent",
        attempt_id=binding.resolved_attempt_id,
        proof_ref=DUMMY_PROOF,
        state=AttemptState.CREATED,
        implementation_ref="fixture@sha",
        config_hash="c" * 64,
        agent_app=binding.agent_app,
        provider_ref=binding.provider_ref,
        model_ref=binding.model_ref,
        harness_ref=binding.harness_ref,
        transport_ref=binding.transport_ref,
        agent_binding_ref=binding.exact_ref(),
        retry_policy_ref=DUMMY_RETRY,
        authority_scope=binding.authority_scope,
    )


def test_p1_4_schema_registry_contains_agent_identity_surface():
    assert {
        "agent_capability_manifest",
        "agent_equivalence_policy",
        "agent_binding",
    } <= set(SCHEMA_REGISTRY)


def test_available_profile_requires_discovery_evidence():
    with pytest.raises(ValidationError, match="discovery_evidence_refs"):
        sealed(
            AgentCapabilityManifest,
            "bad-manifest",
            agent_app="fixture-agent",
            profile_version="1",
            harness_ref="fixture-harness@1",
            availability=AgentProfileAvailability.AVAILABLE,
            capabilities=(),
            discovery_evidence_refs=(),
        )


def test_available_capability_requires_qualification_ref():
    with pytest.raises(ValidationError, match="qualification_refs"):
        AgentCapability(capability_id="repository_read", available=True)


def test_duplicate_capability_ids_rejected():
    cap = AgentCapability(capability_id="repository_read", available=False)
    with pytest.raises(ValidationError, match="capability IDs must be unique"):
        sealed(
            AgentCapabilityManifest,
            "duplicate-manifest",
            agent_app="fixture-agent",
            profile_version="1",
            harness_ref="fixture-harness@1",
            availability=AgentProfileAvailability.UNQUALIFIED,
            capabilities=(cap, cap),
        )


def test_equivalence_policy_is_prospective_and_fail_closed():
    policy = sealed(
        AgentEquivalencePolicy,
        "eq-ok",
        material_dimensions=("agent_app", "model_ref"),
        allowed_substitution_dimensions=("model_ref",),
    )
    assert policy.prospective is True
    assert policy.substitution_requires_new_attempt is True

    with pytest.raises(ValidationError, match="must be unique"):
        sealed(
            AgentEquivalencePolicy,
            "eq-dup",
            material_dimensions=("agent_app", "agent_app"),
        )

    with pytest.raises(ValidationError, match="declared material dimensions"):
        sealed(
            AgentEquivalencePolicy,
            "eq-undeclared",
            material_dimensions=("agent_app",),
            allowed_substitution_dimensions=("model_ref",),
        )


def test_agent_identity_requires_binding_ref_and_binding_ref_requires_app_harness():
    with pytest.raises(ValidationError, match="agent identity requires agent_binding_ref"):
        sealed(
            ExecutionAttemptEnvelope,
            "bad-attempt-agent",
            attempt_id="attempt-agent",
            proof_ref=DUMMY_PROOF,
            state=AttemptState.CREATED,
            implementation_ref="fixture@sha",
            config_hash="d" * 64,
            agent_app="fixture-agent",
            harness_ref="fixture-harness@1",
            retry_policy_ref=DUMMY_RETRY,
        )

    manifest, equivalence, binding = agent_contract()
    with pytest.raises(ValidationError, match="requires agent_app and harness_ref"):
        sealed(
            ExecutionResult,
            "bad-result-binding",
            attempt_ref=ExactRef(object_id="attempt", revision_id="r1", content_hash="e" * 64),
            executor_state=AttemptState.COMPLETED,
            started_at="2026-09-21T10:45:00Z",
            ended_at="2026-09-21T10:45:01Z",
            action_summary="fixture",
            agent_binding_ref=binding.exact_ref(),
        )


def test_validate_agent_binding_identity_accepts_exact_consistent_graph():
    manifest, equivalence, binding = agent_contract()
    attempt = agent_attempt(binding)
    result = sealed(
        ExecutionResult,
        "result-agent",
        attempt_ref=attempt.exact_ref(),
        executor_state=AttemptState.COMPLETED,
        started_at="2026-09-21T10:45:00Z",
        ended_at="2026-09-21T10:45:01Z",
        action_summary="fixture",
        agent_app=binding.agent_app,
        provider_ref=binding.provider_ref,
        model_ref=binding.model_ref,
        harness_ref=binding.harness_ref,
        transport_ref=binding.transport_ref,
        agent_binding_ref=binding.exact_ref(),
    )
    validate_agent_binding_identity(manifest, equivalence, binding, attempt, result)


def test_validate_agent_binding_identity_rejects_manifest_identity_drift():
    manifest, equivalence, binding = agent_contract()
    attempt = agent_attempt(binding)
    data = binding.model_dump(mode="python", exclude={"content_hash"})
    data["provider_ref"] = "other-provider"
    drifted = AgentBinding.sealed(**data)
    drifted_attempt = agent_attempt(drifted)
    with pytest.raises(ValueError, match="provider_ref does not match manifest"):
        validate_agent_binding_identity(manifest, equivalence, drifted, drifted_attempt)


def test_validate_agent_binding_identity_rejects_wrong_refs_and_attempt_id():
    manifest, equivalence, binding = agent_contract()
    attempt = agent_attempt(binding)

    data = binding.model_dump(mode="python", exclude={"content_hash"})
    data["resolved_attempt_id"] = "different-attempt"
    wrong_attempt = AgentBinding.sealed(**data)
    with pytest.raises(ValueError, match="resolved attempt ID mismatch"):
        validate_agent_binding_identity(manifest, equivalence, wrong_attempt, attempt)

    data = binding.model_dump(mode="python", exclude={"content_hash"})
    data["capability_manifest_ref"] = ExactRef(object_id="other", revision_id="r1", content_hash="f" * 64)
    wrong_manifest_ref = AgentBinding.sealed(**data)
    with pytest.raises(ValueError, match="capability manifest reference mismatch"):
        validate_agent_binding_identity(manifest, equivalence, wrong_manifest_ref, attempt)


def test_validate_agent_binding_identity_rejects_unavailable_capability_and_authority_escalation():
    manifest, equivalence, binding = agent_contract(capability_available=False)
    attempt = agent_attempt(binding)
    with pytest.raises(ValueError, match="required capability unavailable or unqualified"):
        validate_agent_binding_identity(manifest, equivalence, binding, attempt)

    manifest, equivalence, binding = agent_contract(max_authority=("READ",))
    data = binding.model_dump(mode="python", exclude={"content_hash"})
    data["authority_scope"] = ("READ", "WRITE")
    escalated = AgentBinding.sealed(**data)
    attempt = agent_attempt(escalated)
    with pytest.raises(ValueError, match="authority scope exceeds manifest maximum"):
        validate_agent_binding_identity(manifest, equivalence, escalated, attempt)


def test_non_available_manifest_cannot_bind_even_if_capability_records_exist():
    manifest, equivalence, binding = agent_contract()
    data = manifest.model_dump(mode="python", exclude={"content_hash"})
    data["availability"] = AgentProfileAvailability.UNQUALIFIED
    unqualified = AgentCapabilityManifest.sealed(**data)
    bdata = binding.model_dump(mode="python", exclude={"content_hash"})
    bdata["capability_manifest_ref"] = unqualified.exact_ref()
    rebound = AgentBinding.sealed(**bdata)
    attempt = agent_attempt(rebound)
    with pytest.raises(ValueError, match="manifest is not AVAILABLE"):
        validate_agent_binding_identity(unqualified, equivalence, rebound, attempt)


def test_standalone_propagates_binding_identity_without_interpreting_verdict(tmp_path: Path):
    manifest, equivalence, binding = agent_contract()
    attempt = agent_attempt(binding)
    runtime = StandaloneRuntime(tmp_path / "standalone-agent")
    report = runtime.executor.execute(
        attempt,
        lambda: LocalExecutionOutcome(action_summary="agent fixture"),
        provenance=P,
    )
    result = report.execution_result
    assert result.agent_binding_ref == binding.exact_ref()
    assert result.agent_app == binding.agent_app
    assert result.provider_ref == binding.provider_ref
    assert result.model_ref == binding.model_ref
    assert result.harness_ref == binding.harness_ref
    assert result.transport_ref == binding.transport_ref
    assert result.executor_state == AttemptState.COMPLETED
    validate_agent_binding_identity(manifest, equivalence, binding, report.final_attempt, result)


def test_p1_4_schema_code_is_provider_neutral():
    source = (Path(__file__).resolve().parents[2] / "src" / "g2e" / "schemas.py").read_text(encoding="utf-8").lower()
    assert "codex" not in source
    assert "chatgpt" not in source
