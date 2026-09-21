from __future__ import annotations

from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from .canonical import CanonicalModel, ExactRef, StrictModel, assert_supported_schema_version


DecimalString = str
HashString = str


class GoalContractLifecycle(StrEnum):
    DRAFT = "DRAFT"
    REVIEWED = "REVIEWED"
    FROZEN = "FROZEN"
    SUPERSEDED = "SUPERSEDED"


class GoalVerdict(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    ACHIEVED = "ACHIEVED"
    FALSIFIED = "FALSIFIED"
    UNRESOLVED = "UNRESOLVED"
    STOPPED = "STOPPED"


class ClaimLifecycle(StrEnum):
    DRAFT = "DRAFT"
    BLOCKED = "BLOCKED"
    READY = "READY"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    SUPERSEDED = "SUPERSEDED"


class ClaimResolution(StrEnum):
    UNKNOWN = "UNKNOWN"
    PASS = "PASS"
    FAIL = "FAIL"
    UNRESOLVED = "UNRESOLVED"


class ProofLifecycle(StrEnum):
    DRAFT = "DRAFT"
    REVIEWED = "REVIEWED"
    FROZEN = "FROZEN"
    AUTHORIZED = "AUTHORIZED"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    SUPERSEDED = "SUPERSEDED"


class AttemptState(StrEnum):
    CREATED = "CREATED"
    PREFLIGHT = "PREFLIGHT"
    LOCKED = "LOCKED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    EXECUTOR_FAILED = "EXECUTOR_FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"
    PREEMPTED = "PREEMPTED"


class AdjudicationVerdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    INVALID = "INVALID"
    UNRESOLVED = "UNRESOLVED"


class ProofResolution(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNRESOLVED = "UNRESOLVED"


class EvidenceLifecycle(StrEnum):
    CANDIDATE = "CANDIDATE"
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"
    INVALIDATED = "INVALIDATED"


class FreshnessState(StrEnum):
    FRESH = "FRESH"
    RESERVED = "RESERVED"
    EXPOSED = "EXPOSED"


class ReuseDisposition(StrEnum):
    QUALIFIED_REUSE = "QUALIFIED_REUSE"
    REPLICATION_REQUIRED = "REPLICATION_REQUIRED"
    SYNTHESIS_INPUT = "SYNTHESIS_INPUT"
    METHOD_REFERENCE = "METHOD_REFERENCE"
    CONTEXT_ONLY = "CONTEXT_ONLY"
    INCOMPATIBLE = "INCOMPATIBLE"


class ConvergenceClassification(StrEnum):
    CORROBORATED = "CORROBORATED"
    CONTRADICTED = "CONTRADICTED"
    BOUNDARY_IDENTIFIED = "BOUNDARY_IDENTIFIED"
    HETEROGENEOUS = "HETEROGENEOUS"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNRESOLVED = "UNRESOLVED"


class GovernanceDispositionValue(StrEnum):
    ACCEPT_FOR_USE = "ACCEPT_FOR_USE"
    REJECT_FOR_USE = "REJECT_FOR_USE"
    REQUEST_NEW_PROOF = "REQUEST_NEW_PROOF"
    STOP = "STOP"


class RuntimeMode(StrEnum):
    STANDALONE = "STANDALONE"
    GWF = "GWF"


class AgentProfileAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNQUALIFIED = "UNQUALIFIED"


class BindingMode(StrEnum):
    DYNAMIC = "DYNAMIC"
    FROZEN = "FROZEN"


class ExternalReferencePolicy(StrEnum):
    OFFLINE_ONLY = "OFFLINE_ONLY"
    VERIFY_WHEN_AVAILABLE = "VERIFY_WHEN_AVAILABLE"
    REQUIRE_RESOLUTION = "REQUIRE_RESOLUTION"


class LibraryExecutionStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    BACKEND_UNAVAILABLE = "BACKEND_UNAVAILABLE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class BackendQualificationStatus(StrEnum):
    QUALIFIED = "QUALIFIED"
    UNQUALIFIED = "UNQUALIFIED"
    UNAVAILABLE = "UNAVAILABLE"


class AmendmentClass(StrEnum):
    EDITORIAL = "EDITORIAL"
    NORMATIVE = "NORMATIVE"


class GoalRequirement(CanonicalModel):
    schema_kind = "goal_requirement"
    statement: str = Field(min_length=1)
    hard_constraint: bool = False
    falsification_relevant: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class AmbiguityRecord(StrictModel):
    ambiguity_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    blocking: bool
    owner: str = Field(min_length=1)
    disposition: str | None = None


class GoalContract(CanonicalModel):
    schema_kind = "goal_contract"
    lifecycle: GoalContractLifecycle
    goal_statement: str = Field(min_length=1)
    requirements: tuple[GoalRequirement, ...] = ()
    desired_outputs: tuple[str, ...] = ()
    hard_constraints: tuple[str, ...] = ()
    preferences: tuple[str, ...] = ()
    non_goals: tuple[str, ...] = ()
    target_environments: tuple[str, ...] = ()
    ambiguities: tuple[AmbiguityRecord, ...] = ()
    amendment_policy_ref: ExactRef | None = None
    authority_policy_ref: ExactRef | None = None

    @model_validator(mode="after")
    def _frozen_has_no_blocking_ambiguity(self):
        if self.lifecycle == GoalContractLifecycle.FROZEN:
            unresolved = [
                a.ambiguity_id
                for a in self.ambiguities
                if a.blocking and not a.disposition
            ]
            if unresolved:
                raise ValueError(
                    f"FROZEN goal has unresolved blocking ambiguities: {unresolved}"
                )
        return self


class GoalExpression(StrictModel):
    op: Literal["CLAIM", "ALL", "ANY"]
    claim_id: str | None = None
    expected_resolution: ClaimResolution | None = None
    children: tuple["GoalExpression", ...] = ()

    @model_validator(mode="after")
    def _shape(self):
        if self.op == "CLAIM":
            if not self.claim_id or self.expected_resolution is None or self.children:
                raise ValueError("CLAIM expression requires claim_id/resolution and no children")
        else:
            if self.claim_id is not None or self.expected_resolution is not None or not self.children:
                raise ValueError("ALL/ANY expression requires children only")
        return self


class GoalClosureContract(CanonicalModel):
    schema_kind = "goal_closure_contract"
    goal_contract_ref: ExactRef
    claim_graph_ref: ExactRef
    requirement_claim_map: dict[str, tuple[str, ...]]
    success_expression: GoalExpression
    falsification_expression: GoalExpression
    terminal_claim_ids: tuple[str, ...]
    authorized_stop_policy_ref: ExactRef | None = None


class ClaimResolutionPolicy(CanonicalModel):
    schema_kind = "claim_resolution_policy"
    mode: Literal["ALL_REQUIRED", "ANY_SUFFICIENT"]
    proof_ids: tuple[str, ...]

    @field_validator("proof_ids")
    @classmethod
    def _proofs_nonempty_unique(cls, value):
        if not value:
            raise ValueError("proof_ids must not be empty")
        if len(value) != len(set(value)):
            raise ValueError("proof_ids must be unique")
        return value


class Claim(CanonicalModel):
    schema_kind = "claim"
    proposition: str = Field(min_length=1)
    claim_class: str = Field(min_length=1)
    scope: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    hard_prerequisite_claim_ids: tuple[str, ...] = ()
    resolution_policy_ref: ExactRef
    goal_requirement_ids: tuple[str, ...] = ()
    lifecycle: ClaimLifecycle
    resolution: ClaimResolution


class ClaimGraph(CanonicalModel):
    schema_kind = "claim_graph"
    goal_contract_ref: ExactRef
    claims: tuple[Claim, ...]
    coverage_statement: str = Field(min_length=1)
    unresolved_coverage: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _hard_dag(self):
        ids = [c.object_id for c in self.claims]
        if len(ids) != len(set(ids)):
            raise ValueError("claim IDs must be unique")
        known = set(ids)
        graph = {c.object_id: tuple(c.hard_prerequisite_claim_ids) for c in self.claims}
        for cid, deps in graph.items():
            unknown = set(deps) - known
            if unknown:
                raise ValueError(f"claim {cid} has unknown prerequisites: {sorted(unknown)}")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str):
            if node in visiting:
                raise ValueError("HARD claim dependency cycle")
            if node in visited:
                return
            visiting.add(node)
            for dep in graph[node]:
                visit(dep)
            visiting.remove(node)
            visited.add(node)

        for cid in graph:
            visit(cid)
        return self


class ProofRetryPolicy(CanonicalModel):
    schema_kind = "proof_retry_policy"
    max_invalid_replacement_attempts: int = Field(ge=0)
    require_same_semantic_proof_identity: bool = True
    allowed_technical_reason_codes: tuple[str, ...] = ()


class MetricPredicate(StrictModel):
    metric_id: str = Field(min_length=1)
    operator: Literal["GE", "GT", "LE", "LT", "EQ", "NE"]
    threshold_key: str = Field(min_length=1)


class DecisionExpression(StrictModel):
    op: Literal["PREDICATE", "ALL", "ANY"]
    predicate: MetricPredicate | None = None
    children: tuple["DecisionExpression", ...] = ()

    @model_validator(mode="after")
    def _shape(self):
        if self.op == "PREDICATE":
            if self.predicate is None or self.children:
                raise ValueError("PREDICATE requires predicate and no children")
        else:
            if self.predicate is not None or not self.children:
                raise ValueError("ALL/ANY decision expression requires children only")
        return self


class DecisionRule(CanonicalModel):
    schema_kind = "decision_rule"
    pass_expression: DecisionExpression
    fail_expression: DecisionExpression
    missing_metric_behavior: Literal["INVALID", "UNRESOLVED"] = "INVALID"
    metric_conflict_behavior: Literal["INVALID"] = "INVALID"


class EvidenceAdmissionPolicy(CanonicalModel):
    schema_kind = "evidence_admission_policy"
    accepted_source_classes: tuple[str, ...]
    require_integrity_hash: bool = True
    require_attempt_linkage: bool = False
    allowed_freshness_states: tuple[FreshnessState, ...] = ()
    independence_requirements: tuple[str, ...] = ()
    allowed_derivation_depth: int = Field(default=0, ge=0)
    missing_data_behavior: Literal["REJECT", "INVALID", "ALLOW_WITH_REASON"] = "REJECT"


class IndependencePolicy(CanonicalModel):
    schema_kind = "independence_policy"
    required_dimensions: tuple[str, ...] = ()
    forbidden_shared_ancestor_classes: tuple[str, ...] = ()


class AmendmentPolicy(CanonicalModel):
    schema_kind = "amendment_policy"
    allow_editorial: bool = True
    normative_pre_outcome_requires_refreeze: bool = True
    normative_post_outcome_requires_new_lineage: bool = True


class AuthorityAction(StrictModel):
    action: str = Field(min_length=1)
    allowed_roles: tuple[str, ...]


class AuthorityPolicy(CanonicalModel):
    schema_kind = "authority_policy"
    actions: tuple[AuthorityAction, ...]
    delegated_authority_may_exceed_parent: Literal[False] = False


class ProtectedResource(CanonicalModel):
    schema_kind = "protected_resource"
    resource_type: str = Field(min_length=1)
    identity_ref: str = Field(min_length=1)
    freshness_state: FreshnessState
    protected: bool = True
    reuse_allowed: bool = False
    reuse_policy_ref: ExactRef | None = None


class ProofObligation(CanonicalModel):
    schema_kind = "proof_obligation"
    lifecycle: ProofLifecycle
    target_claim_id: str = Field(min_length=1)
    proposition: str = Field(min_length=1)
    prerequisites: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    intervention: str | None = None
    controls: tuple[str, ...] = ()
    fixture_or_population_ref: str | None = None
    metric_ids: tuple[str, ...] = ()
    decision_thresholds: dict[str, DecimalString] = Field(default_factory=dict)
    decision_rule_ref: ExactRef
    baseline_refs: tuple[str, ...] = ()
    evidence_admission_policy_ref: ExactRef
    retry_policy_ref: ExactRef
    amendment_policy_ref: ExactRef
    independence_policy_ref: ExactRef | None = None
    protected_resource_refs: tuple[ExactRef, ...] = ()
    protected_resource_cost: int = Field(default=0, ge=0)
    resource_cost_class: int = Field(default=0, ge=0)
    implementation_complexity: int = Field(default=0, ge=0)
    stop_conditions: tuple[str, ...] = ()

    @field_validator("decision_thresholds")
    @classmethod
    def _decimal_strings(cls, value):
        for key, item in value.items():
            if not isinstance(item, str) or not item:
                raise ValueError(f"threshold {key} must be a non-empty decimal string")
            try:
                decimal = Decimal(item)
            except InvalidOperation:
                raise ValueError(
                    f"threshold {key} must be finite decimal text"
                ) from None
            if not decimal.is_finite():
                raise ValueError(f"threshold {key} must be finite decimal text")
        return value


class RuntimeCapability(StrictModel):
    capability_id: str = Field(min_length=1)
    available: bool
    qualification_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


class RuntimeCapabilityManifest(CanonicalModel):
    schema_kind = "runtime_capability_manifest"
    runtime_id: str = Field(min_length=1)
    runtime_version: str = Field(min_length=1)
    runtime_mode: RuntimeMode
    authority_mode: str = Field(min_length=1)
    persistence_backend: str = Field(min_length=1)
    supported_schema_versions: tuple[str, ...]
    capabilities: tuple[RuntimeCapability, ...]
    security_assumptions: tuple[str, ...] = ()
    exact_runtime_revision: str | None = None

    @field_validator("supported_schema_versions")
    @classmethod
    def _runtime_supported_versions(cls, value):
        if not value:
            raise ValueError("supported_schema_versions must not be empty")
        for version in value:
            assert_supported_schema_version(version)
        return value

    @model_validator(mode="after")
    def _capability_ids_unique(self):
        ids = [c.capability_id for c in self.capabilities]
        if len(ids) != len(set(ids)):
            raise ValueError("runtime capability IDs must be unique")
        return self


class AgentCapability(StrictModel):
    capability_id: str = Field(min_length=1)
    available: bool
    qualification_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _qualified_when_available(self):
        if self.available and not self.qualification_refs:
            raise ValueError("available agent capability requires qualification_refs")
        return self


class AgentCapabilityManifest(CanonicalModel):
    schema_kind = "agent_capability_manifest"
    agent_app: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    harness_ref: str = Field(min_length=1)
    exact_harness_revision: str | None = None
    provider_ref: str | None = None
    model_ref: str | None = None
    transport_ref: str | None = None
    availability: AgentProfileAvailability
    capabilities: tuple[AgentCapability, ...] = ()
    execution_constraints: tuple[str, ...] = ()
    max_authority_scope: tuple[str, ...] = ()
    credential_ref_classes: tuple[str, ...] = ()
    external_session_attribution: bool = False
    interruption_supported: bool = False
    artifact_extraction_supported: bool = False
    structured_output_supported: bool = False
    status_normalization_supported: bool = False
    discovery_evidence_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _manifest_invariants(self):
        ids = [c.capability_id for c in self.capabilities]
        if len(ids) != len(set(ids)):
            raise ValueError("agent capability IDs must be unique")
        if self.availability == AgentProfileAvailability.AVAILABLE and not self.discovery_evidence_refs:
            raise ValueError("AVAILABLE agent profile requires discovery_evidence_refs")
        if len(self.max_authority_scope) != len(set(self.max_authority_scope)):
            raise ValueError("max_authority_scope entries must be unique")
        return self


class QualificationAuthorityGrant(CanonicalModel):
    schema_kind = "qualification_authority_grant"
    mode: Literal["QUALIFICATION_ONLY"] = "QUALIFICATION_ONLY"
    proof_ref: ExactRef
    capability_manifest_ref: ExactRef
    attempt_id: str = Field(min_length=1)
    target_capability_ids: tuple[str, ...]
    authority_policy_ref: ExactRef
    granted_role: str = Field(min_length=1)
    granted_authority_scope: tuple[str, ...]
    allowed_read_paths: tuple[str, ...] = ()
    allowed_write_paths: tuple[str, ...] = ()
    network_allowed: Literal[False] = False
    interactive_approval_allowed: Literal[False] = False
    single_attempt: Literal[True] = True
    may_imply_capability_available: Literal[False] = False
    may_be_reused_for_operational_binding: Literal[False] = False
    qualification_lineage_ref: str = Field(min_length=1)

    @model_validator(mode="after")
    def _qualification_grant_invariants(self):
        if not self.target_capability_ids:
            raise ValueError("target_capability_ids must not be empty")
        if len(self.target_capability_ids) != len(set(self.target_capability_ids)):
            raise ValueError("target_capability_ids must be unique")
        if not self.granted_authority_scope:
            raise ValueError("granted_authority_scope must not be empty")
        if len(self.granted_authority_scope) != len(set(self.granted_authority_scope)):
            raise ValueError("granted_authority_scope must be unique")
        for field_name, paths in (
            ("allowed_read_paths", self.allowed_read_paths),
            ("allowed_write_paths", self.allowed_write_paths),
        ):
            if len(paths) != len(set(paths)):
                raise ValueError(f"{field_name} must be unique")
            for path in paths:
                parts = path.replace("\\", "/").split("/")
                if not path or path.startswith(("/", "\\")) or ":" in parts[0] or ".." in parts:
                    raise ValueError(f"{field_name} entries must be relative traversal-free paths")
        return self


class AgentEquivalencePolicy(CanonicalModel):
    schema_kind = "agent_equivalence_policy"
    material_dimensions: tuple[str, ...]
    allowed_substitution_dimensions: tuple[str, ...] = ()
    substitution_requires_new_attempt: Literal[True] = True
    prospective: Literal[True] = True

    @model_validator(mode="after")
    def _equivalence_invariants(self):
        if not self.material_dimensions:
            raise ValueError("material_dimensions must not be empty")
        if len(self.material_dimensions) != len(set(self.material_dimensions)):
            raise ValueError("material_dimensions must be unique")
        if len(self.allowed_substitution_dimensions) != len(set(self.allowed_substitution_dimensions)):
            raise ValueError("allowed_substitution_dimensions must be unique")
        undeclared = set(self.allowed_substitution_dimensions) - set(self.material_dimensions)
        if undeclared:
            raise ValueError("allowed substitution dimensions must be declared material dimensions")
        return self


class AgentBinding(CanonicalModel):
    schema_kind = "agent_binding"
    resolved_attempt_id: str = Field(min_length=1)
    agent_app: str = Field(min_length=1)
    capability_manifest_ref: ExactRef
    equivalence_policy_ref: ExactRef
    binding_mode: BindingMode
    harness_ref: str = Field(min_length=1)
    provider_ref: str | None = None
    model_ref: str | None = None
    transport_ref: str | None = None
    required_capability_ids: tuple[str, ...] = ()
    qualification_authority_ref: ExactRef | None = None
    qualification_target_capability_ids: tuple[str, ...] = ()
    execution_constraints: tuple[str, ...] = ()
    authority_scope: tuple[str, ...] = ()
    resolved_at: str
    resolution_ref: str | None = None

    @model_validator(mode="after")
    def _binding_invariants(self):
        if len(self.required_capability_ids) != len(set(self.required_capability_ids)):
            raise ValueError("required_capability_ids must be unique")
        if len(self.qualification_target_capability_ids) != len(set(self.qualification_target_capability_ids)):
            raise ValueError("qualification_target_capability_ids must be unique")
        if set(self.required_capability_ids) & set(self.qualification_target_capability_ids):
            raise ValueError("qualification targets must not overlap required capabilities")
        has_grant = self.qualification_authority_ref is not None
        has_targets = bool(self.qualification_target_capability_ids)
        if has_grant != has_targets:
            raise ValueError("qualification authority ref and target capabilities must appear together")
        if len(self.authority_scope) != len(set(self.authority_scope)):
            raise ValueError("authority_scope entries must be unique")
        if not self.resolved_at.endswith("Z"):
            raise ValueError("resolved_at must be RFC3339 UTC ending in Z")
        return self


class ExecutionAttemptEnvelope(CanonicalModel):
    schema_kind = "execution_attempt_envelope"
    attempt_id: str = Field(min_length=1)
    proof_ref: ExactRef
    state: AttemptState
    implementation_ref: str = Field(min_length=1)
    config_hash: HashString
    artifact_refs: tuple[str, ...] = ()
    data_refs: tuple[str, ...] = ()
    agent_app: str | None = None
    provider_ref: str | None = None
    model_ref: str | None = None
    harness_ref: str | None = None
    transport_ref: str | None = None
    agent_binding_ref: ExactRef | None = None
    resource_identity: str | None = None
    protected_resource_refs: tuple[ExactRef, ...] = ()
    retry_policy_ref: ExactRef
    authority_scope: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _agent_binding_identity_required(self):
        identities = (
            self.agent_app,
            self.provider_ref,
            self.model_ref,
            self.harness_ref,
            self.transport_ref,
        )
        if any(item is not None for item in identities) and self.agent_binding_ref is None:
            raise ValueError("agent identity requires agent_binding_ref")
        if self.agent_binding_ref is not None and (self.agent_app is None or self.harness_ref is None):
            raise ValueError("agent_binding_ref requires agent_app and harness_ref")
        return self


class ExecutionResult(CanonicalModel):
    schema_kind = "execution_result"
    attempt_ref: ExactRef
    executor_state: AttemptState
    started_at: str
    ended_at: str
    action_summary: str = Field(min_length=1)
    artifact_refs: tuple[str, ...] = ()
    candidate_evidence_refs: tuple[ExactRef, ...] = ()
    resource_identity: str | None = None
    agent_app: str | None = None
    provider_ref: str | None = None
    model_ref: str | None = None
    harness_ref: str | None = None
    transport_ref: str | None = None
    agent_binding_ref: ExactRef | None = None
    technical_error_class: str | None = None
    technical_error_reason: str | None = None
    redaction_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _agent_binding_identity_required(self):
        identities = (
            self.agent_app,
            self.provider_ref,
            self.model_ref,
            self.harness_ref,
            self.transport_ref,
        )
        if any(item is not None for item in identities) and self.agent_binding_ref is None:
            raise ValueError("agent identity requires agent_binding_ref")
        if self.agent_binding_ref is not None and (self.agent_app is None or self.harness_ref is None):
            raise ValueError("agent_binding_ref requires agent_app and harness_ref")
        return self

    @model_validator(mode="after")
    def _terminal_executor_state(self):
        allowed = {
            AttemptState.COMPLETED,
            AttemptState.EXECUTOR_FAILED,
            AttemptState.CANCELLED,
            AttemptState.TIMED_OUT,
            AttemptState.PREEMPTED,
        }
        if self.executor_state not in allowed:
            raise ValueError("ExecutionResult requires terminal executor state")
        if not self.started_at.endswith("Z") or not self.ended_at.endswith("Z"):
            raise ValueError("ExecutionResult timestamps must be RFC3339 UTC ending in Z")
        return self


def validate_agent_binding_identity(
    manifest: AgentCapabilityManifest,
    equivalence_policy: AgentEquivalencePolicy,
    binding: AgentBinding,
    attempt: ExecutionAttemptEnvelope,
    result: ExecutionResult | None = None,
) -> None:
    if manifest.availability != AgentProfileAvailability.AVAILABLE:
        raise ValueError("agent capability manifest is not AVAILABLE")
    if binding.capability_manifest_ref != manifest.exact_ref():
        raise ValueError("binding capability manifest reference mismatch")
    if binding.equivalence_policy_ref != equivalence_policy.exact_ref():
        raise ValueError("binding equivalence policy reference mismatch")
    if binding.resolved_attempt_id != attempt.attempt_id:
        raise ValueError("binding resolved attempt ID mismatch")
    if attempt.agent_binding_ref != binding.exact_ref():
        raise ValueError("attempt agent binding reference mismatch")

    identity_fields = ("agent_app", "provider_ref", "model_ref", "harness_ref", "transport_ref")
    for field in identity_fields:
        manifest_value = getattr(manifest, field)
        binding_value = getattr(binding, field)
        attempt_value = getattr(attempt, field)
        if binding_value != manifest_value:
            raise ValueError(f"binding {field} does not match manifest")
        if attempt_value != binding_value:
            raise ValueError(f"attempt {field} does not match binding")

    capabilities = {cap.capability_id: cap for cap in manifest.capabilities}
    for capability_id in binding.required_capability_ids:
        capability = capabilities.get(capability_id)
        if capability is None or not capability.available or not capability.qualification_refs:
            raise ValueError(f"required capability unavailable or unqualified: {capability_id}")

    if not set(binding.authority_scope).issubset(set(manifest.max_authority_scope)):
        raise ValueError("binding authority scope exceeds manifest maximum")

    if result is None:
        return

    if result.attempt_ref != attempt.exact_ref():
        raise ValueError("result attempt reference mismatch")
    if result.agent_binding_ref != binding.exact_ref():
        raise ValueError("result agent binding reference mismatch")
    for field in identity_fields:
        if getattr(result, field) != getattr(binding, field):
            raise ValueError(f"result {field} does not match binding")


def validate_qualification_agent_binding_identity(
    manifest: AgentCapabilityManifest,
    equivalence_policy: AgentEquivalencePolicy,
    grant: QualificationAuthorityGrant,
    authority_policy: AuthorityPolicy,
    proof: ProofObligation,
    binding: AgentBinding,
    attempt: ExecutionAttemptEnvelope,
    result: ExecutionResult | None = None,
    *,
    expected_allowed_read_paths: tuple[str, ...] | None = None,
    expected_allowed_write_paths: tuple[str, ...] | None = None,
) -> None:
    if manifest.availability != AgentProfileAvailability.AVAILABLE:
        raise ValueError("agent capability manifest is not AVAILABLE")
    if proof.lifecycle not in {ProofLifecycle.FROZEN, ProofLifecycle.AUTHORIZED}:
        raise ValueError("qualification proof must be FROZEN or AUTHORIZED")
    if grant.proof_ref != proof.exact_ref():
        raise ValueError("qualification grant proof reference mismatch")
    if grant.capability_manifest_ref != manifest.exact_ref():
        raise ValueError("qualification grant capability manifest reference mismatch")
    if grant.authority_policy_ref != authority_policy.exact_ref():
        raise ValueError("qualification grant authority policy reference mismatch")
    if grant.attempt_id != attempt.attempt_id:
        raise ValueError("qualification grant attempt ID mismatch")
    if binding.qualification_authority_ref != grant.exact_ref():
        raise ValueError("binding qualification authority reference mismatch")
    if tuple(binding.qualification_target_capability_ids) != tuple(grant.target_capability_ids):
        raise ValueError("binding qualification target capabilities mismatch")
    if binding.capability_manifest_ref != manifest.exact_ref():
        raise ValueError("binding capability manifest reference mismatch")
    if binding.equivalence_policy_ref != equivalence_policy.exact_ref():
        raise ValueError("binding equivalence policy reference mismatch")
    if binding.resolved_attempt_id != attempt.attempt_id:
        raise ValueError("binding resolved attempt ID mismatch")
    if attempt.proof_ref != proof.exact_ref():
        raise ValueError("attempt proof reference mismatch")
    if attempt.agent_binding_ref != binding.exact_ref():
        raise ValueError("attempt agent binding reference mismatch")
    if tuple(attempt.authority_scope) != tuple(binding.authority_scope):
        raise ValueError("attempt authority scope must equal binding authority scope")

    identity_fields = ("agent_app", "provider_ref", "model_ref", "harness_ref", "transport_ref")
    for field in identity_fields:
        manifest_value = getattr(manifest, field)
        binding_value = getattr(binding, field)
        attempt_value = getattr(attempt, field)
        if binding_value != manifest_value:
            raise ValueError(f"binding {field} does not match manifest")
        if attempt_value != binding_value:
            raise ValueError(f"attempt {field} does not match binding")

    capabilities = {cap.capability_id: cap for cap in manifest.capabilities}
    for capability_id in binding.required_capability_ids:
        capability = capabilities.get(capability_id)
        if capability is None or not capability.available or not capability.qualification_refs:
            raise ValueError(f"required capability unavailable or unqualified: {capability_id}")

    for capability_id in binding.qualification_target_capability_ids:
        capability = capabilities.get(capability_id)
        if capability is None:
            raise ValueError(f"qualification target capability missing: {capability_id}")
        if capability.available:
            raise ValueError(f"qualification target already available: {capability_id}")

    if set(binding.required_capability_ids) & set(binding.qualification_target_capability_ids):
        raise ValueError("qualification targets overlap required capabilities")

    policy_actions: dict[str, set[str]] = {}
    for action in authority_policy.actions:
        policy_actions.setdefault(action.action, set()).update(action.allowed_roles)
    for action_name in grant.granted_authority_scope:
        allowed_roles = policy_actions.get(action_name)
        if allowed_roles is None:
            raise ValueError(f"qualification authority action absent from policy: {action_name}")
        if grant.granted_role not in allowed_roles:
            raise ValueError(f"qualification role not permitted for action: {action_name}")

    effective_authority = set(manifest.max_authority_scope) | set(grant.granted_authority_scope)
    if not set(binding.authority_scope).issubset(effective_authority):
        raise ValueError("qualification binding authority exceeds manifest plus grant")
    outside_manifest = set(binding.authority_scope) - set(manifest.max_authority_scope)
    if not outside_manifest.issubset(set(grant.granted_authority_scope)):
        raise ValueError("qualification binding authority outside manifest is not granted")

    if expected_allowed_read_paths is not None and tuple(grant.allowed_read_paths) != tuple(expected_allowed_read_paths):
        raise ValueError("qualification grant read path contract mismatch")
    if expected_allowed_write_paths is not None and tuple(grant.allowed_write_paths) != tuple(expected_allowed_write_paths):
        raise ValueError("qualification grant write path contract mismatch")

    if result is None:
        return

    if result.attempt_ref != attempt.exact_ref():
        raise ValueError("result attempt reference mismatch")
    if result.agent_binding_ref != binding.exact_ref():
        raise ValueError("result agent binding reference mismatch")
    for field in identity_fields:
        if getattr(result, field) != getattr(binding, field):
            raise ValueError(f"result {field} does not match binding")


class EvidenceRecord(CanonicalModel):
    schema_kind = "evidence_record"
    source_class: str = Field(min_length=1)
    lifecycle: EvidenceLifecycle
    producer_attempt_ref: ExactRef | None = None
    subject_refs: tuple[ExactRef, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    resource_refs: tuple[str, ...] = ()
    payload_digest: str | None = None
    immutable_external_ref: str | None = None
    freshness_state: FreshnessState | None = None
    admission_policy_ref: ExactRef | None = None
    admission_reason: str | None = None


class EvidenceRelation(CanonicalModel):
    schema_kind = "evidence_relation"
    relation: Literal[
        "PRODUCED_BY",
        "SUPPORTS",
        "FALSIFIES",
        "VALIDATES",
        "DERIVED_FROM",
        "REPRODUCES",
        "CONFLICTS_WITH",
        "SUPERSEDES",
        "IMPORTS_CAPSULE",
    ]
    subject_ref: ExactRef
    object_ref: ExactRef


class Adjudication(CanonicalModel):
    schema_kind = "adjudication"
    proof_ref: ExactRef
    attempt_ref: ExactRef
    admitted_evidence_refs: tuple[ExactRef, ...]
    decision_rule_hash: str = Field(min_length=1)
    adjudicator_version: str = Field(min_length=1)
    verdict: AdjudicationVerdict
    reason_codes: tuple[str, ...] = ()


class ProofResult(CanonicalModel):
    schema_kind = "proof_result"
    proof_ref: ExactRef
    adjudication_refs: tuple[ExactRef, ...]
    outcome: ProofResolution
    retry_policy_ref: ExactRef
    invalid_attempt_count: int = Field(default=0, ge=0)
    reason_codes: tuple[str, ...] = ()

    @field_validator("adjudication_refs")
    @classmethod
    def _adjudications_nonempty(cls, value):
        if not value:
            raise ValueError("ProofResult requires adjudication history")
        return value


class SelectionRankField(StrictModel):
    field_name: str = Field(min_length=1)
    direction: Literal["ASC", "DESC"]


class SelectionPolicy(CanonicalModel):
    schema_kind = "selection_policy"
    rank_fields: tuple[SelectionRankField, ...]
    allow_authorized_non_default_choice: bool = True


class SelectionDecision(CanonicalModel):
    schema_kind = "selection_decision"
    policy_ref: ExactRef
    admissible_proof_ids: tuple[str, ...]
    ranked_proof_ids: tuple[str, ...]
    selected_proof_id: str
    authorized_override: bool = False
    override_reason: str | None = None


class GovernanceDisposition(CanonicalModel):
    schema_kind = "governance_disposition"
    adjudication_ref: ExactRef
    disposition: GovernanceDispositionValue
    approved_by: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class PackageMember(StrictModel):
    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    size: int = Field(ge=0)


class PackageExternalReference(StrictModel):
    ref_id: str = Field(min_length=1)
    immutable_locator: str = Field(min_length=1)
    expected_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    required_online_resolution: bool = False


class PackageManifest(CanonicalModel):
    schema_kind = "package_manifest"
    members: tuple[PackageMember, ...]
    external_reference_policy: ExternalReferencePolicy = ExternalReferencePolicy.OFFLINE_ONLY
    external_references: tuple[PackageExternalReference, ...] = ()
    non_authoritative_paths: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _manifest_paths_valid(self):
        paths = [m.path for m in self.members]
        if paths != sorted(paths):
            raise ValueError("package manifest members must be path-sorted")
        if len(paths) != len(set(paths)):
            raise ValueError("package manifest member paths must be unique")
        forbidden = {"PACKAGE_MANIFEST.json", "PACKAGE_SEAL.json"}
        for path in paths:
            if path in forbidden:
                raise ValueError("manifest/seal must not self-appear in package members")
            if path.startswith("/") or ".." in path.split("/"):
                raise ValueError("package manifest paths must be safe relative paths")
        ref_ids = [ref.ref_id for ref in self.external_references]
        if len(ref_ids) != len(set(ref_ids)):
            raise ValueError("package external reference IDs must be unique")
        return self


class PackageSeal(CanonicalModel):
    schema_kind = "package_seal"
    package_type: Literal["GOAL_RESULT", "CLAIM_RESULT", "SYNTHESIS_RESULT"]
    manifest_ref: ExactRef
    manifest_file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    framework_version: str = Field(min_length=1)
    runtime_id: str = Field(min_length=1)
    runtime_version: str = Field(min_length=1)
    attestation_identity: str | None = None


class ClaimResultPackage(CanonicalModel):
    schema_kind = "claim_result_package"
    goal_contract_ref: ExactRef
    claim_graph_ref: ExactRef
    claim_ref: ExactRef
    claim_resolution: ClaimResolution
    proof_result_refs: tuple[ExactRef, ...]
    evidence_refs: tuple[ExactRef, ...]
    limitations: tuple[str, ...] = ()
    manifest_members: tuple[PackageMember, ...]
    package_manifest_hash: str = Field(min_length=64, max_length=64)
    package_seal_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def _terminal_claim(self):
        if self.claim_resolution == ClaimResolution.UNKNOWN:
            raise ValueError("ClaimResultPackage requires terminal claim resolution")
        return self


class ClaimSignature(CanonicalModel):
    schema_kind = "claim_signature"
    proposition_family: str = Field(min_length=1)
    subject_population: str = Field(min_length=1)
    intervention: str | None = None
    comparator: str | None = None
    outcome_metric: str = Field(min_length=1)
    measurement_procedure: str | None = None
    environment_runtime: str | None = None
    data_cohort_regime: str | None = None
    artifact_model_identity: str | None = None
    temporal_version_regime: str | None = None
    assumptions: tuple[str, ...] = ()
    boundaries: tuple[str, ...] = ()
    domain_extensions: dict[str, Any] = Field(default_factory=dict)


class EvidenceCapsule(CanonicalModel):
    schema_kind = "evidence_capsule"
    source_package_type: Literal["CLAIM_RESULT", "GOAL_RESULT", "SYNTHESIS_RESULT"]
    source_package_ref: str = Field(min_length=1)
    source_package_seal_hash: str = Field(min_length=64, max_length=64)
    source_goal_ref: ExactRef
    source_claim_ref: ExactRef
    source_proof_refs: tuple[ExactRef, ...] = ()
    source_evidence_refs: tuple[ExactRef, ...] = ()
    source_claim_resolution: ClaimResolution
    claim_signature_ref: ExactRef
    environment_regime: str | None = None
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    provenance_ancestor_refs: tuple[ExactRef, ...] = ()
    independence_cluster_hints: tuple[str, ...] = ()
    source_exposure: Literal["EXPOSED"] = "EXPOSED"
    capsule_policy_version: str = Field(min_length=1)


class ApplicabilityDimension(StrictModel):
    dimension: str = Field(min_length=1)
    source_value: str | None = None
    target_value: str | None = None
    match: Literal["EXACT", "COMPATIBLE", "PARTIAL", "INCOMPATIBLE", "UNKNOWN"]
    reason: str | None = None


class ApplicabilityPolicy(CanonicalModel):
    schema_kind = "applicability_policy"
    required_exact_dimensions: tuple[str, ...] = ()
    allowed_partial_dimensions: tuple[str, ...] = ()
    provenance_overlap_policy: str = Field(min_length=1)
    fail_closed_on_unknown_required_dimension: bool = True


class ApplicabilityAssessment(CanonicalModel):
    schema_kind = "applicability_assessment"
    source_capsule_ref: ExactRef
    target_goal_ref: ExactRef
    target_claim_ref: ExactRef
    target_proof_ref: ExactRef | None = None
    policy_ref: ExactRef
    dimensions: tuple[ApplicabilityDimension, ...]
    provenance_overlap_refs: tuple[ExactRef, ...] = ()
    source_integrity_valid: bool
    disposition: ReuseDisposition
    reason_codes: tuple[str, ...] = ()


class ReuseProofMetadata(CanonicalModel):
    schema_kind = "reuse_proof_metadata"
    target_claim_ref: ExactRef
    capsule_refs: tuple[ExactRef, ...]
    applicability_assessment_refs: tuple[ExactRef, ...]
    evidence_admission_policy_ref: ExactRef
    required_disposition: Literal["QUALIFIED_REUSE"] = "QUALIFIED_REUSE"
    no_new_empirical_execution: Literal[True] = True


class EvidenceIndependenceCluster(CanonicalModel):
    schema_kind = "evidence_independence_cluster"
    member_capsule_refs: tuple[ExactRef, ...]
    shared_ancestor_refs: tuple[ExactRef, ...] = ()
    independence_policy_ref: ExactRef
    independent_confirmation_units: int = Field(ge=1)


class CoverageStatement(StrictModel):
    target_universe: str = Field(min_length=1)
    searched_scopes: tuple[str, ...]
    missing_or_inaccessible_sources: tuple[str, ...] = ()
    publication_selection_bias_risks: tuple[str, ...] = ()
    temporal_cutoff: str | None = None
    limitations: tuple[str, ...] = ()


class SynthesisObservation(StrictModel):
    discovery_channel: Literal[
        "G2E_LIBRARY_ADAPTER",
        "REFERENCE_ACQUISITION_GWF_CATALOG",
        "REFERENCE_ACQUISITION_EXTERNAL",
        "MANUAL",
    ]
    observation_ref: str = Field(min_length=1)
    exact_subject_ref: ExactRef


class SynthesisUniverse(CanonicalModel):
    schema_kind = "synthesis_universe"
    catalog_snapshot_refs: tuple[str, ...] = ()
    retrieval_session_refs: tuple[str, ...] = ()
    observations: tuple[SynthesisObservation, ...]
    temporal_cutoff: str | None = None
    coverage: CoverageStatement


class SynthesisContract(CanonicalModel):
    schema_kind = "synthesis_contract"
    target_goal_ref: ExactRef
    target_claim_ref: ExactRef
    question: str = Field(min_length=1)
    universe_ref: ExactRef
    inclusion_rules: tuple[str, ...]
    exclusion_rules: tuple[str, ...]
    outcome_blind_by_default: bool = True
    applicability_policy_ref: ExactRef
    required_reuse_disposition: Literal["SYNTHESIS_INPUT"] = "SYNTHESIS_INPUT"
    quality_gate: tuple[str, ...] = ()
    independence_policy_ref: ExactRef
    provenance_clustering_rules: tuple[str, ...] = ()
    compatibility_grouping_rules: tuple[str, ...] = ()
    aggregation_method: str = Field(min_length=1)
    conflict_policy: str = Field(min_length=1)
    boundary_policy: str = Field(min_length=1)
    missing_data_policy: str = Field(min_length=1)
    stopping_rule: str = Field(min_length=1)


class SynthesisCandidate(StrictModel):
    subject_ref: ExactRef
    observation_refs: tuple[str, ...]
    included: bool
    reason_codes: tuple[str, ...]


class SynthesisResult(CanonicalModel):
    schema_kind = "synthesis_result"
    contract_ref: ExactRef
    universe_ref: ExactRef
    candidates: tuple[SynthesisCandidate, ...]
    applicability_refs: tuple[ExactRef, ...]
    independence_cluster_refs: tuple[ExactRef, ...]
    compatibility_groups: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    aggregation_outputs: dict[str, Any] = Field(default_factory=dict)
    conflicts: tuple[str, ...] = ()
    boundaries: tuple[str, ...] = ()
    classification: ConvergenceClassification
    limitations: tuple[str, ...] = ()
    source_provenance_closure: tuple[ExactRef, ...] = ()


class LibraryQueryContract(CanonicalModel):
    schema_kind = "library_query_contract"
    query_payload: dict[str, Any]
    required_capability_ids: tuple[str, ...]
    access_scope: tuple[str, ...]
    require_complete_results: bool = True


class LibraryQueryExecution(CanonicalModel):
    schema_kind = "library_query_execution"
    query_ref: ExactRef
    backend_id: str = Field(min_length=1)
    backend_version: str = Field(min_length=1)
    snapshot_ref: str = Field(min_length=1)
    status: LibraryExecutionStatus
    complete: bool
    result_publication_ids: tuple[str, ...] = ()
    result_subject_refs: tuple[ExactRef, ...] = ()
    ranking_backend_version: str | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def _status_completeness(self):
        if self.status != LibraryExecutionStatus.SUCCEEDED and self.complete:
            raise ValueError("non-success library execution cannot claim complete=true")
        if len(self.result_publication_ids) != len(self.result_subject_refs):
            raise ValueError("publication IDs must align with result subject refs")
        return self


class LibraryPublicationContract(CanonicalModel):
    schema_kind = "library_publication_contract"
    subject_ref: ExactRef
    source_package_type: Literal["CLAIM_RESULT", "GOAL_RESULT", "SYNTHESIS_RESULT"]
    source_package_seal_hash: str = Field(min_length=64, max_length=64)
    publication_scope: Literal["PROJECT", "WORKSPACE", "TENANT"]
    metadata_namespace: str = Field(pattern=r"^[a-z][a-z0-9_.-]*$")
    metadata_schema_version: str = Field(min_length=1)


class LibrarySnapshot(CanonicalModel):
    schema_kind = "library_snapshot"
    backend_id: str = Field(min_length=1)
    backend_version: str = Field(min_length=1)
    snapshot_ref: str = Field(min_length=1)
    publication_ids: tuple[str, ...]
    subject_refs: tuple[ExactRef, ...]

    @model_validator(mode="after")
    def _snapshot_alignment(self):
        if len(self.publication_ids) != len(self.subject_refs):
            raise ValueError("snapshot publication IDs must align with subject refs")
        return self


class LibraryCapability(StrictModel):
    capability_id: str = Field(min_length=1)
    status: BackendQualificationStatus
    evidence_refs: tuple[str, ...] = ()
    supported_subject_kinds: tuple[str, ...] = ()
    supported_query_modes: tuple[str, ...] = ()


class LibraryCapabilityManifest(CanonicalModel):
    schema_kind = "library_capability_manifest"
    backend_id: str = Field(min_length=1)
    backend_type: Literal["GWF_GAC", "STANDALONE"]
    adapter_version: str = Field(min_length=1)
    runtime_version: str | None = None
    supported_schema_versions: tuple[str, ...]
    capabilities: tuple[LibraryCapability, ...]
    security_access_model: str = Field(min_length=1)
    exact_backend_revision: str | None = None
    silent_fallback_allowed: Literal[False] = False

    @field_validator("supported_schema_versions")
    @classmethod
    def _supported_versions_fail_closed(cls, value):
        if not value:
            raise ValueError("supported_schema_versions must not be empty")
        for version in value:
            assert_supported_schema_version(version)
        return value


SCHEMA_MODELS = (
    GoalRequirement,
    GoalContract,
    GoalClosureContract,
    ClaimResolutionPolicy,
    Claim,
    ClaimGraph,
    ProofRetryPolicy,
    DecisionRule,
    RuntimeCapabilityManifest,
    AgentCapabilityManifest,
    QualificationAuthorityGrant,
    AgentEquivalencePolicy,
    AgentBinding,
    ExecutionResult,
    EvidenceAdmissionPolicy,
    IndependencePolicy,
    AmendmentPolicy,
    AuthorityPolicy,
    ProtectedResource,
    ProofObligation,
    ExecutionAttemptEnvelope,
    EvidenceRecord,
    EvidenceRelation,
    Adjudication,
    ProofResult,
    SelectionPolicy,
    SelectionDecision,
    GovernanceDisposition,
    PackageManifest,
    PackageSeal,
    ClaimResultPackage,
    ClaimSignature,
    EvidenceCapsule,
    ApplicabilityPolicy,
    ApplicabilityAssessment,
    ReuseProofMetadata,
    EvidenceIndependenceCluster,
    SynthesisUniverse,
    SynthesisContract,
    SynthesisResult,
    LibraryQueryContract,
    LibraryQueryExecution,
    LibraryPublicationContract,
    LibrarySnapshot,
    LibraryCapabilityManifest,
)


SCHEMA_REGISTRY = {model.schema_kind: model for model in SCHEMA_MODELS}
