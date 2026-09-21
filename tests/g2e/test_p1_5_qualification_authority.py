from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError

from g2e import (
    AgentBinding,
    AgentCapability,
    AgentCapabilityManifest,
    AgentEquivalencePolicy,
    AgentProfileAvailability,
    AttemptState,
    AuthorityAction,
    AuthorityPolicy,
    BindingMode,
    ExecutionAttemptEnvelope,
    ProofLifecycle,
    ProofObligation,
    Provenance,
    QualificationAuthorityGrant,
    SCHEMA_REGISTRY,
    validate_agent_binding_identity,
    validate_qualification_agent_binding_identity,
)
from g2e.canonical import ExactRef


P = Provenance(created_by="p1.5-test", created_at="2026-09-21T13:20:00Z")
DUMMY_DECISION = ExactRef(object_id="decision", revision_id="r1", content_hash="1" * 64)
DUMMY_ADMISSION = ExactRef(object_id="admission", revision_id="r1", content_hash="2" * 64)
DUMMY_RETRY = ExactRef(object_id="retry", revision_id="r1", content_hash="3" * 64)
DUMMY_AMENDMENT = ExactRef(object_id="amendment", revision_id="r1", content_hash="4" * 64)


def sealed(cls, object_id: str, **kwargs):
    return cls.sealed(
        object_id=object_id,
        revision_id="r1",
        provenance=P,
        **kwargs,
    )


def build_contract():
    manifest = sealed(
        AgentCapabilityManifest,
        "manifest",
        agent_app="fixture-agent",
        profile_version="1",
        harness_ref="sha256:" + "a" * 64,
        exact_harness_revision="a" * 64,
        provider_ref=None,
        model_ref=None,
        transport_ref="app-server-stdio",
        availability=AgentProfileAvailability.AVAILABLE,
        capabilities=(
            AgentCapability(
                capability_id="app_server_launch",
                available=True,
                qualification_refs=("fixture:d1",),
            ),
            AgentCapability(capability_id="repository_read", available=False),
            AgentCapability(capability_id="repository_write", available=False),
        ),
        max_authority_scope=(),
        discovery_evidence_refs=("fixture:d1",),
    )
    equivalence = sealed(
        AgentEquivalencePolicy,
        "equivalence",
        material_dimensions=("agent_app", "harness_ref", "transport_ref"),
        allowed_substitution_dimensions=(),
    )
    proof = sealed(
        ProofObligation,
        "proof",
        lifecycle=ProofLifecycle.FROZEN,
        target_claim_id="qualification-target",
        proposition="bounded qualification attempt",
        decision_rule_ref=DUMMY_DECISION,
        evidence_admission_policy_ref=DUMMY_ADMISSION,
        retry_policy_ref=DUMMY_RETRY,
        amendment_policy_ref=DUMMY_AMENDMENT,
    )
    authority_policy = sealed(
        AuthorityPolicy,
        "authority-policy",
        actions=(
            AuthorityAction(
                action="READ_FROZEN_FIXTURE",
                allowed_roles=("qualification_executor",),
            ),
            AuthorityAction(
                action="WRITE_DESIGNATED_OUTPUT",
                allowed_roles=("qualification_executor",),
            ),
        ),
    )
    grant = sealed(
        QualificationAuthorityGrant,
        "qualification-grant",
        proof_ref=proof.exact_ref(),
        capability_manifest_ref=manifest.exact_ref(),
        attempt_id="attempt-001",
        target_capability_ids=("repository_read", "repository_write"),
        authority_policy_ref=authority_policy.exact_ref(),
        granted_role="qualification_executor",
        granted_authority_scope=("READ_FROZEN_FIXTURE", "WRITE_DESIGNATED_OUTPUT"),
        allowed_read_paths=("input.json", "TASK.md"),
        allowed_write_paths=("result.json",),
        qualification_lineage_ref="fixture:p1.5",
    )
    binding = sealed(
        AgentBinding,
        "binding",
        resolved_attempt_id="attempt-001",
        agent_app=manifest.agent_app,
        capability_manifest_ref=manifest.exact_ref(),
        equivalence_policy_ref=equivalence.exact_ref(),
        binding_mode=BindingMode.FROZEN,
        harness_ref=manifest.harness_ref,
        provider_ref=manifest.provider_ref,
        model_ref=manifest.model_ref,
        transport_ref=manifest.transport_ref,
        required_capability_ids=("app_server_launch",),
        qualification_authority_ref=grant.exact_ref(),
        qualification_target_capability_ids=grant.target_capability_ids,
        authority_scope=grant.granted_authority_scope,
        resolved_at="2026-09-21T13:20:00Z",
    )
    attempt = sealed(
        ExecutionAttemptEnvelope,
        "attempt-envelope",
        attempt_id=binding.resolved_attempt_id,
        proof_ref=proof.exact_ref(),
        state=AttemptState.CREATED,
        implementation_ref="fixture@sha",
        config_hash="5" * 64,
        agent_app=binding.agent_app,
        provider_ref=binding.provider_ref,
        model_ref=binding.model_ref,
        harness_ref=binding.harness_ref,
        transport_ref=binding.transport_ref,
        agent_binding_ref=binding.exact_ref(),
        retry_policy_ref=DUMMY_RETRY,
        authority_scope=binding.authority_scope,
    )
    return manifest, equivalence, proof, authority_policy, grant, binding, attempt


def reseal(obj, **updates):
    data = obj.model_dump(mode="python", exclude={"content_hash"})
    data.update(updates)
    return type(obj).sealed(**data)


def rebind(grant, binding, attempt, **binding_updates):
    bdata = binding.model_dump(mode="python", exclude={"content_hash"})
    bdata.update(binding_updates)
    bdata["qualification_authority_ref"] = grant.exact_ref()
    rebound = AgentBinding.sealed(**bdata)
    adata = attempt.model_dump(mode="python", exclude={"content_hash"})
    adata["agent_binding_ref"] = rebound.exact_ref()
    adata["authority_scope"] = rebound.authority_scope
    return rebound, ExecutionAttemptEnvelope.sealed(**adata)


def test_p1_5_schema_registry_contains_qualification_grant():
    assert "qualification_authority_grant" in SCHEMA_REGISTRY
    assert SCHEMA_REGISTRY["qualification_authority_grant"] is QualificationAuthorityGrant


def test_p1_5_positive_qualification_binding_does_not_self_qualify_targets():
    manifest, equivalence, proof, policy, grant, binding, attempt = build_contract()
    validate_qualification_agent_binding_identity(
        manifest,
        equivalence,
        grant,
        policy,
        proof,
        binding,
        attempt,
        expected_allowed_read_paths=("input.json", "TASK.md"),
        expected_allowed_write_paths=("result.json",),
    )
    capabilities = {cap.capability_id: cap for cap in manifest.capabilities}
    assert capabilities["repository_read"].available is False
    assert capabilities["repository_write"].available is False
    assert grant.may_imply_capability_available is False
    assert grant.may_be_reused_for_operational_binding is False


def test_normal_p1_4_validator_is_not_weakened_by_p1_5():
    manifest, equivalence, _, _, _, binding, attempt = build_contract()
    with pytest.raises(ValueError, match="authority scope exceeds manifest maximum"):
        validate_agent_binding_identity(manifest, equivalence, binding, attempt)

    data = binding.model_dump(mode="python", exclude={"content_hash"})
    data["required_capability_ids"] = ("repository_write",)
    data["qualification_authority_ref"] = None
    data["qualification_target_capability_ids"] = ()
    data["authority_scope"] = ()
    normal = AgentBinding.sealed(**data)
    adata = attempt.model_dump(mode="python", exclude={"content_hash"})
    adata["agent_binding_ref"] = normal.exact_ref()
    adata["authority_scope"] = ()
    normal_attempt = ExecutionAttemptEnvelope.sealed(**adata)
    with pytest.raises(ValueError, match="required capability unavailable or unqualified"):
        validate_agent_binding_identity(manifest, equivalence, normal, normal_attempt)


def test_agent_binding_requires_grant_and_targets_together_and_disjoint():
    _, _, _, _, _, binding, _ = build_contract()
    data = binding.model_dump(mode="python", exclude={"content_hash"})
    data["qualification_authority_ref"] = None
    with pytest.raises(ValidationError, match="must appear together"):
        AgentBinding.sealed(**data)

    data = binding.model_dump(mode="python", exclude={"content_hash"})
    data["qualification_target_capability_ids"] = ()
    with pytest.raises(ValidationError, match="must appear together"):
        AgentBinding.sealed(**data)

    data = binding.model_dump(mode="python", exclude={"content_hash"})
    data["qualification_target_capability_ids"] = ("app_server_launch",)
    with pytest.raises(ValidationError, match="must not overlap"):
        AgentBinding.sealed(**data)


def test_grant_rejects_duplicate_targets_scope_and_unsafe_paths():
    _, _, _, _, grant, _, _ = build_contract()
    data = grant.model_dump(mode="python", exclude={"content_hash"})
    data["target_capability_ids"] = ("repository_read", "repository_read")
    with pytest.raises(ValidationError, match="target_capability_ids must be unique"):
        QualificationAuthorityGrant.sealed(**data)

    data = grant.model_dump(mode="python", exclude={"content_hash"})
    data["granted_authority_scope"] = ("READ_FROZEN_FIXTURE", "READ_FROZEN_FIXTURE")
    with pytest.raises(ValidationError, match="granted_authority_scope must be unique"):
        QualificationAuthorityGrant.sealed(**data)

    for unsafe in ("../secret.txt", "/tmp/result.json", "C:/tmp/result.json"):
        data = grant.model_dump(mode="python", exclude={"content_hash"})
        data["allowed_write_paths"] = (unsafe,)
        with pytest.raises(ValidationError, match="relative traversal-free"):
            QualificationAuthorityGrant.sealed(**data)


def test_grant_cannot_enable_network_or_interactive_approval():
    _, _, _, _, grant, _, _ = build_contract()
    for field in ("network_allowed", "interactive_approval_allowed"):
        data = grant.model_dump(mode="python", exclude={"content_hash"})
        data[field] = True
        with pytest.raises(ValidationError):
            QualificationAuthorityGrant.sealed(**data)


def test_qualification_validator_rejects_wrong_grant_proof_manifest_policy_and_attempt():
    manifest, equivalence, proof, policy, grant, binding, attempt = build_contract()

    wrong = reseal(grant, proof_ref=ExactRef(object_id="other-proof", revision_id="r1", content_hash="6" * 64))
    rebound, reattempt = rebind(wrong, binding, attempt)
    with pytest.raises(ValueError, match="proof reference mismatch"):
        validate_qualification_agent_binding_identity(manifest, equivalence, wrong, policy, proof, rebound, reattempt)

    wrong = reseal(grant, capability_manifest_ref=ExactRef(object_id="other-manifest", revision_id="r1", content_hash="7" * 64))
    rebound, reattempt = rebind(wrong, binding, attempt)
    with pytest.raises(ValueError, match="capability manifest reference mismatch"):
        validate_qualification_agent_binding_identity(manifest, equivalence, wrong, policy, proof, rebound, reattempt)

    wrong = reseal(grant, authority_policy_ref=ExactRef(object_id="other-policy", revision_id="r1", content_hash="8" * 64))
    rebound, reattempt = rebind(wrong, binding, attempt)
    with pytest.raises(ValueError, match="authority policy reference mismatch"):
        validate_qualification_agent_binding_identity(manifest, equivalence, wrong, policy, proof, rebound, reattempt)

    wrong = reseal(grant, attempt_id="attempt-999")
    rebound, reattempt = rebind(wrong, binding, attempt)
    with pytest.raises(ValueError, match="attempt ID mismatch"):
        validate_qualification_agent_binding_identity(manifest, equivalence, wrong, policy, proof, rebound, reattempt)


def test_qualification_validator_rejects_missing_or_already_available_target():
    manifest, equivalence, proof, policy, grant, binding, attempt = build_contract()

    gdata = grant.model_dump(mode="python", exclude={"content_hash"})
    gdata["target_capability_ids"] = ("missing_capability",)
    missing_grant = QualificationAuthorityGrant.sealed(**gdata)
    rebound, reattempt = rebind(
        missing_grant,
        binding,
        attempt,
        qualification_target_capability_ids=("missing_capability",),
    )
    with pytest.raises(ValueError, match="target capability missing"):
        validate_qualification_agent_binding_identity(manifest, equivalence, missing_grant, policy, proof, rebound, reattempt)

    mdata = manifest.model_dump(mode="python", exclude={"content_hash"})
    caps = []
    for cap in manifest.capabilities:
        if cap.capability_id == "repository_read":
            caps.append(AgentCapability(capability_id="repository_read", available=True, qualification_refs=("fixture:qualified",)))
        else:
            caps.append(cap)
    mdata["capabilities"] = tuple(caps)
    available_manifest = AgentCapabilityManifest.sealed(**mdata)
    gdata = grant.model_dump(mode="python", exclude={"content_hash"})
    gdata["capability_manifest_ref"] = available_manifest.exact_ref()
    available_grant = QualificationAuthorityGrant.sealed(**gdata)
    bdata = binding.model_dump(mode="python", exclude={"content_hash"})
    bdata["capability_manifest_ref"] = available_manifest.exact_ref()
    bdata["qualification_authority_ref"] = available_grant.exact_ref()
    available_binding = AgentBinding.sealed(**bdata)
    adata = attempt.model_dump(mode="python", exclude={"content_hash"})
    adata["agent_binding_ref"] = available_binding.exact_ref()
    available_attempt = ExecutionAttemptEnvelope.sealed(**adata)
    with pytest.raises(ValueError, match="qualification target already available: repository_read"):
        validate_qualification_agent_binding_identity(
            available_manifest, equivalence, available_grant, policy, proof, available_binding, available_attempt
        )


def test_qualification_validator_rejects_policy_role_and_authority_escalation():
    manifest, equivalence, proof, policy, grant, binding, attempt = build_contract()

    bad_policy = sealed(
        AuthorityPolicy,
        "bad-policy",
        actions=(
            AuthorityAction(action="READ_FROZEN_FIXTURE", allowed_roles=("qualification_executor",)),
        ),
    )
    gdata = grant.model_dump(mode="python", exclude={"content_hash"})
    gdata["authority_policy_ref"] = bad_policy.exact_ref()
    bad_grant = QualificationAuthorityGrant.sealed(**gdata)
    rebound, reattempt = rebind(bad_grant, binding, attempt)
    with pytest.raises(ValueError, match="action absent from policy: WRITE_DESIGNATED_OUTPUT"):
        validate_qualification_agent_binding_identity(manifest, equivalence, bad_grant, bad_policy, proof, rebound, reattempt)

    role_policy = sealed(
        AuthorityPolicy,
        "role-policy",
        actions=(
            AuthorityAction(action="READ_FROZEN_FIXTURE", allowed_roles=("other_role",)),
            AuthorityAction(action="WRITE_DESIGNATED_OUTPUT", allowed_roles=("other_role",)),
        ),
    )
    gdata = grant.model_dump(mode="python", exclude={"content_hash"})
    gdata["authority_policy_ref"] = role_policy.exact_ref()
    role_grant = QualificationAuthorityGrant.sealed(**gdata)
    rebound, reattempt = rebind(role_grant, binding, attempt)
    with pytest.raises(ValueError, match="role not permitted"):
        validate_qualification_agent_binding_identity(manifest, equivalence, role_grant, role_policy, proof, rebound, reattempt)

    bdata = binding.model_dump(mode="python", exclude={"content_hash"})
    bdata["authority_scope"] = binding.authority_scope + ("ARBITRARY_SHELL",)
    bdata["qualification_authority_ref"] = grant.exact_ref()
    escalated = AgentBinding.sealed(**bdata)
    adata = attempt.model_dump(mode="python", exclude={"content_hash"})
    adata["agent_binding_ref"] = escalated.exact_ref()
    adata["authority_scope"] = escalated.authority_scope
    escalated_attempt = ExecutionAttemptEnvelope.sealed(**adata)
    with pytest.raises(ValueError, match="exceeds manifest plus grant"):
        validate_qualification_agent_binding_identity(manifest, equivalence, grant, policy, proof, escalated, escalated_attempt)


def test_qualification_validator_rejects_attempt_authority_and_path_contract_mismatch():
    manifest, equivalence, proof, policy, grant, binding, attempt = build_contract()
    adata = attempt.model_dump(mode="python", exclude={"content_hash"})
    adata["authority_scope"] = ("READ_FROZEN_FIXTURE",)
    narrower_attempt = ExecutionAttemptEnvelope.sealed(**adata)
    with pytest.raises(ValueError, match="attempt authority scope must equal binding authority scope"):
        validate_qualification_agent_binding_identity(manifest, equivalence, grant, policy, proof, binding, narrower_attempt)

    with pytest.raises(ValueError, match="read path contract mismatch"):
        validate_qualification_agent_binding_identity(
            manifest, equivalence, grant, policy, proof, binding, attempt,
            expected_allowed_read_paths=("wrong.json",),
        )
    with pytest.raises(ValueError, match="write path contract mismatch"):
        validate_qualification_agent_binding_identity(
            manifest, equivalence, grant, policy, proof, binding, attempt,
            expected_allowed_write_paths=("wrong.json",),
        )


def test_p1_5_source_is_provider_neutral():
    from pathlib import Path
    import g2e.schemas as schemas

    source = Path(schemas.__file__).read_text(encoding="utf-8").lower()
    assert "codex" not in source
    assert "chatgpt" not in source
