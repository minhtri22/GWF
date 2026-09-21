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
    resource_identity: str | None = None
    protected_resource_refs: tuple[ExactRef, ...] = ()
    retry_policy_ref: ExactRef
    authority_scope: tuple[str, ...] = ()


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
    result_subject_refs: tuple[ExactRef, ...] = ()
    ranking_backend_version: str | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def _status_completeness(self):
        if self.status != LibraryExecutionStatus.SUCCEEDED and self.complete:
            raise ValueError("non-success library execution cannot claim complete=true")
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
    subject_refs: tuple[ExactRef, ...]


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
    SelectionPolicy,
    SelectionDecision,
    GovernanceDisposition,
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
