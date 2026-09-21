from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any, Iterable, Mapping, Sequence

from .canonical import ExactRef, Provenance, canonical_hash, canonical_json
from .schemas import (
    Adjudication,
    AdjudicationVerdict,
    ApplicabilityAssessment,
    ApplicabilityDimension,
    ApplicabilityPolicy,
    AttemptState,
    Claim,
    ClaimGraph,
    ClaimLifecycle,
    ClaimResolution,
    ClaimResolutionPolicy,
    ClaimSignature,
    ConvergenceClassification,
    DecisionExpression,
    DecisionRule,
    EvidenceAdmissionPolicy,
    EvidenceCapsule,
    EvidenceIndependenceCluster,
    EvidenceLifecycle,
    EvidenceRecord,
    EvidenceRelation,
    ExecutionAttemptEnvelope,
    FreshnessState,
    GoalClosureContract,
    GoalContract,
    GoalExpression,
    GoalVerdict,
    IndependencePolicy,
    ProofLifecycle,
    ProofObligation,
    ProofRetryPolicy,
    ProtectedResource,
    ReuseDisposition,
    ReuseProofMetadata,
    SelectionDecision,
    SelectionPolicy,
    SynthesisCandidate,
    SynthesisContract,
    SynthesisResult,
    SynthesisUniverse,
)


class CoreInvariantError(ValueError):
    """A frozen semantic/core invariant was violated."""


class ProofOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNRESOLVED = "UNRESOLVED"
    RETRY_ALLOWED = "RETRY_ALLOWED"
    OPEN = "OPEN"


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdmissionDecision:
    lifecycle: EvidenceLifecycle
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdmissibilityResult:
    admissible: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProofClosure:
    outcome: ProofOutcome
    terminal: bool
    replacement_attempt_allowed: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class AmendmentDecision:
    unchanged: bool
    refreeze_required: bool
    new_lineage_required: bool


def ref_key(ref: ExactRef) -> tuple[str, str, str]:
    return (ref.object_id, ref.revision_id, ref.content_hash)


def ref_token(ref: ExactRef) -> str:
    return "|".join(ref_key(ref))


def _exact_ref_matches(obj: Any, ref: ExactRef) -> bool:
    return hasattr(obj, "exact_ref") and obj.exact_ref() == ref


def _collect_goal_claim_ids(expr: GoalExpression) -> set[str]:
    if expr.op == "CLAIM":
        return {expr.claim_id} if expr.claim_id else set()
    out: set[str] = set()
    for child in expr.children:
        out.update(_collect_goal_claim_ids(child))
    return out


def validate_claim_graph_and_goal_closure(
    goal: GoalContract,
    graph: ClaimGraph,
    closure: GoalClosureContract,
    resolution_policies: Mapping[str, ClaimResolutionPolicy],
) -> ValidationReport:
    reasons: list[str] = []

    if graph.goal_contract_ref != goal.exact_ref():
        reasons.append("CLAIM_GRAPH_GOAL_REF_MISMATCH")
    if closure.goal_contract_ref != goal.exact_ref():
        reasons.append("GOAL_CLOSURE_GOAL_REF_MISMATCH")
    if closure.claim_graph_ref != graph.exact_ref():
        reasons.append("GOAL_CLOSURE_GRAPH_REF_MISMATCH")

    claims = {c.object_id: c for c in graph.claims}
    requirement_ids = {r.object_id for r in goal.requirements}
    unresolved = set(graph.unresolved_coverage)

    derived: dict[str, set[str]] = {rid: set() for rid in requirement_ids}
    for claim in graph.claims:
        for rid in claim.goal_requirement_ids:
            if rid not in requirement_ids:
                reasons.append(f"CLAIM_UNKNOWN_GOAL_REQUIREMENT:{claim.object_id}:{rid}")
            else:
                derived[rid].add(claim.object_id)

        if claim.lifecycle in {
            ClaimLifecycle.READY,
            ClaimLifecycle.ACTIVE,
            ClaimLifecycle.CLOSED,
        }:
            policy = resolution_policies.get(claim.resolution_policy_ref.object_id)
            if policy is None or policy.exact_ref() != claim.resolution_policy_ref:
                reasons.append(f"CLAIM_RESOLUTION_POLICY_UNRESOLVED:{claim.object_id}")

    unknown_unresolved = unresolved - requirement_ids
    for rid in sorted(unknown_unresolved):
        reasons.append(f"UNKNOWN_UNRESOLVED_COVERAGE:{rid}")

    for rid in sorted(requirement_ids):
        mapped = derived[rid]
        closure_mapped = set(closure.requirement_claim_map.get(rid, ()))
        if mapped != closure_mapped:
            reasons.append(f"REQUIREMENT_MAPPING_MISMATCH:{rid}")
        if not mapped and rid not in unresolved:
            reasons.append(f"REQUIREMENT_UNCOVERED:{rid}")

    extra_map = set(closure.requirement_claim_map) - requirement_ids
    for rid in sorted(extra_map):
        reasons.append(f"GOAL_CLOSURE_UNKNOWN_REQUIREMENT:{rid}")

    known_claim_ids = set(claims)
    for rid, mapped in sorted(closure.requirement_claim_map.items()):
        for cid in mapped:
            if cid not in known_claim_ids:
                reasons.append(f"GOAL_CLOSURE_UNKNOWN_CLAIM:{rid}:{cid}")

    for cid in closure.terminal_claim_ids:
        if cid not in known_claim_ids:
            reasons.append(f"UNKNOWN_TERMINAL_CLAIM:{cid}")

    expression_ids = (
        _collect_goal_claim_ids(closure.success_expression)
        | _collect_goal_claim_ids(closure.falsification_expression)
    )
    for cid in sorted(expression_ids - known_claim_ids):
        reasons.append(f"GOAL_EXPRESSION_UNKNOWN_CLAIM:{cid}")

    return ValidationReport(not reasons, tuple(reasons))


def _resource_map(resources: Iterable[ProtectedResource]) -> dict[tuple[str, str, str], ProtectedResource]:
    return {ref_key(r.exact_ref()): r for r in resources}


def check_proof_admissibility(
    proof: ProofObligation,
    claims_by_id: Mapping[str, Claim],
    proof_outcomes: Mapping[str, ProofOutcome],
    retry_policy: ProofRetryPolicy,
    protected_resources: Sequence[ProtectedResource] = (),
    *,
    invalid_attempts_so_far: int = 0,
    authority_satisfied: bool = True,
    independence_satisfied: bool = True,
    amendment_valid: bool = True,
) -> AdmissibilityResult:
    reasons: list[str] = []
    if retry_policy.exact_ref() != proof.retry_policy_ref:
        reasons.append("RETRY_POLICY_REF_MISMATCH")
    claim = claims_by_id.get(proof.target_claim_id)
    if claim is None:
        reasons.append("TARGET_CLAIM_MISSING")
    else:
        if claim.lifecycle not in {ClaimLifecycle.READY, ClaimLifecycle.ACTIVE}:
            reasons.append("TARGET_CLAIM_NOT_READY_OR_ACTIVE")
        for dep_id in claim.hard_prerequisite_claim_ids:
            dep = claims_by_id.get(dep_id)
            if dep is None or dep.resolution != ClaimResolution.PASS:
                reasons.append(f"HARD_CLAIM_DEPENDENCY_UNSATISFIED:{dep_id}")

    if proof.lifecycle not in {ProofLifecycle.FROZEN, ProofLifecycle.AUTHORIZED}:
        reasons.append("PROOF_NOT_FROZEN_OR_AUTHORIZED")

    existing = proof_outcomes.get(proof.object_id, ProofOutcome.OPEN)
    if existing in {ProofOutcome.PASS, ProofOutcome.FAIL, ProofOutcome.UNRESOLVED}:
        reasons.append("TERMINAL_PROOF_REPLAY_FORBIDDEN")

    for dep_id in proof.prerequisites:
        if proof_outcomes.get(dep_id) != ProofOutcome.PASS:
            reasons.append(f"PROOF_PREREQUISITE_UNSATISFIED:{dep_id}")

    if invalid_attempts_so_far > retry_policy.max_invalid_replacement_attempts:
        reasons.append("INVALID_RETRY_BUDGET_EXHAUSTED")

    rmap = _resource_map(protected_resources)
    for rref in proof.protected_resource_refs:
        resource = rmap.get(ref_key(rref))
        if resource is None:
            reasons.append(f"PROTECTED_RESOURCE_MISSING:{rref.object_id}")
            continue
        if resource.freshness_state == FreshnessState.RESERVED:
            reasons.append(f"PROTECTED_RESOURCE_ALREADY_RESERVED:{resource.object_id}")
        elif resource.freshness_state == FreshnessState.EXPOSED and not resource.reuse_allowed:
            reasons.append(f"PROTECTED_RESOURCE_EXPOSED_NO_REUSE:{resource.object_id}")

    if not authority_satisfied:
        reasons.append("AUTHORITY_UNSATISFIED")
    if proof.independence_policy_ref is not None and not independence_satisfied:
        reasons.append("INDEPENDENCE_UNSATISFIED")
    if not amendment_valid:
        reasons.append("AMENDMENT_OR_LINEAGE_INVALID")

    return AdmissibilityResult(not reasons, tuple(reasons))


def transition_protected_resource(
    resource: ProtectedResource,
    event: str,
    *,
    revision_id: str,
    provenance: Provenance,
) -> ProtectedResource:
    current = resource.freshness_state
    if event == "RESERVE":
        if current != FreshnessState.FRESH:
            raise CoreInvariantError("only FRESH resource can be RESERVED")
        target = FreshnessState.RESERVED
    elif event == "EXPOSE":
        if current != FreshnessState.RESERVED:
            raise CoreInvariantError("resource must be RESERVED before EXPOSED")
        target = FreshnessState.EXPOSED
    elif event == "RECOVERY_UNCERTAIN_ACCESS":
        target = FreshnessState.EXPOSED
    elif event == "RECOVERY_CONFIRMED_NO_ACCESS":
        target = current
    else:
        raise CoreInvariantError(f"unknown protected-resource event: {event}")

    if current == FreshnessState.EXPOSED and target != FreshnessState.EXPOSED:
        raise CoreInvariantError("EXPOSED resource cannot transition backwards")

    return ProtectedResource.sealed(
        schema_version=resource.schema_version,
        object_id=resource.object_id,
        revision_id=revision_id,
        provenance=provenance,
        resource_type=resource.resource_type,
        identity_ref=resource.identity_ref,
        freshness_state=target,
        protected=resource.protected,
        reuse_allowed=resource.reuse_allowed,
        reuse_policy_ref=resource.reuse_policy_ref,
    )


def evaluate_evidence_admission(
    evidence: EvidenceRecord,
    policy: EvidenceAdmissionPolicy,
    *,
    derivation_depth: int = 0,
    independence_satisfied: Iterable[str] = (),
    payload_available: bool = True,
) -> AdmissionDecision:
    reasons: list[str] = []
    satisfied = set(independence_satisfied)

    if evidence.lifecycle == EvidenceLifecycle.INVALIDATED:
        reasons.append("EVIDENCE_INVALIDATED")
    if evidence.source_class not in policy.accepted_source_classes:
        reasons.append("SOURCE_CLASS_NOT_ACCEPTED")
    if policy.require_integrity_hash and not evidence.payload_digest:
        reasons.append("INTEGRITY_HASH_REQUIRED")
    if policy.require_attempt_linkage and evidence.producer_attempt_ref is None:
        reasons.append("ATTEMPT_LINKAGE_REQUIRED")
    if policy.allowed_freshness_states:
        if evidence.freshness_state not in set(policy.allowed_freshness_states):
            reasons.append("FRESHNESS_NOT_ALLOWED")
    for requirement in policy.independence_requirements:
        if requirement not in satisfied:
            reasons.append(f"INDEPENDENCE_REQUIREMENT_UNSATISFIED:{requirement}")
    if derivation_depth > policy.allowed_derivation_depth:
        reasons.append("DERIVATION_DEPTH_EXCEEDED")

    if not payload_available:
        if policy.missing_data_behavior == "REJECT":
            reasons.append("MISSING_DATA_REJECTED")
        elif policy.missing_data_behavior == "INVALID":
            reasons.append("MISSING_DATA_INVALID")
        else:
            return AdmissionDecision(
                EvidenceLifecycle.ADMITTED,
                ("MISSING_DATA_ALLOWED_WITH_REASON",),
            )

    if reasons:
        return AdmissionDecision(EvidenceLifecycle.REJECTED, tuple(reasons))
    return AdmissionDecision(EvidenceLifecycle.ADMITTED, ())


def materialize_evidence_admission(
    evidence: EvidenceRecord,
    policy: EvidenceAdmissionPolicy,
    decision: AdmissionDecision,
    *,
    revision_id: str,
    provenance: Provenance,
) -> EvidenceRecord:
    reason = "ADMITTED" if not decision.reasons else ";".join(decision.reasons)
    return EvidenceRecord.sealed(
        schema_version=evidence.schema_version,
        object_id=evidence.object_id,
        revision_id=revision_id,
        provenance=provenance,
        source_class=evidence.source_class,
        lifecycle=decision.lifecycle,
        producer_attempt_ref=evidence.producer_attempt_ref,
        subject_refs=evidence.subject_refs,
        artifact_refs=evidence.artifact_refs,
        resource_refs=evidence.resource_refs,
        payload_digest=evidence.payload_digest,
        immutable_external_ref=evidence.immutable_external_ref,
        freshness_state=evidence.freshness_state,
        admission_policy_ref=policy.exact_ref(),
        admission_reason=reason,
    )


def validate_evidence_relation(
    relation: EvidenceRelation,
    objects: Mapping[tuple[str, str, str], Any],
) -> ValidationReport:
    reasons: list[str] = []
    subject = objects.get(ref_key(relation.subject_ref))
    obj = objects.get(ref_key(relation.object_ref))
    if not isinstance(subject, EvidenceRecord):
        reasons.append("RELATION_SUBJECT_NOT_EVIDENCE")
    if obj is None:
        reasons.append("RELATION_OBJECT_MISSING")
        return ValidationReport(False, tuple(reasons))

    if relation.relation == "PRODUCED_BY":
        if not isinstance(obj, ExecutionAttemptEnvelope):
            reasons.append("PRODUCED_BY_OBJECT_NOT_ATTEMPT")
    elif relation.relation in {"SUPPORTS", "FALSIFIES"}:
        if not isinstance(obj, (Claim, ProofObligation)):
            reasons.append("SUPPORTS_FALSIFIES_OBJECT_NOT_CLAIM_OR_PROOF")
    elif relation.relation in {
        "DERIVED_FROM",
        "REPRODUCES",
        "CONFLICTS_WITH",
        "SUPERSEDES",
    }:
        if not isinstance(obj, EvidenceRecord):
            reasons.append("EVIDENCE_RELATION_OBJECT_NOT_EVIDENCE")
    elif relation.relation == "IMPORTS_CAPSULE":
        if not isinstance(obj, EvidenceCapsule):
            reasons.append("IMPORTS_CAPSULE_OBJECT_NOT_CAPSULE")
    elif relation.relation == "VALIDATES":
        if not hasattr(obj, "exact_ref"):
            reasons.append("VALIDATES_OBJECT_NOT_EXACT_REVISION")
    else:
        reasons.append("UNKNOWN_EVIDENCE_RELATION")

    return ValidationReport(not reasons, tuple(reasons))


def _decision_predicates(expr: DecisionExpression) -> list[Any]:
    if expr.op == "PREDICATE":
        return [expr.predicate]
    out: list[Any] = []
    for child in expr.children:
        out.extend(_decision_predicates(child))
    return out


def _eval_predicate(
    metric_value: Decimal,
    threshold: Decimal,
    operator: str,
) -> bool:
    if operator == "GE":
        return metric_value >= threshold
    if operator == "GT":
        return metric_value > threshold
    if operator == "LE":
        return metric_value <= threshold
    if operator == "LT":
        return metric_value < threshold
    if operator == "EQ":
        return metric_value == threshold
    if operator == "NE":
        return metric_value != threshold
    raise CoreInvariantError(f"unsupported decision operator: {operator}")


def _eval_decision_expression(
    expr: DecisionExpression,
    metrics: Mapping[str, Decimal],
    thresholds: Mapping[str, Decimal],
) -> bool:
    if expr.op == "PREDICATE":
        assert expr.predicate is not None
        predicate = expr.predicate
        return _eval_predicate(
            metrics[predicate.metric_id],
            thresholds[predicate.threshold_key],
            predicate.operator,
        )
    values = [
        _eval_decision_expression(child, metrics, thresholds)
        for child in expr.children
    ]
    if expr.op == "ALL":
        return all(values)
    if expr.op == "ANY":
        return any(values)
    raise CoreInvariantError(f"unsupported decision expression op: {expr.op}")


def _metric_values_from_evidence(
    evidence: Sequence[EvidenceRecord],
    payloads: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Decimal], tuple[str, ...]]:
    metrics: dict[str, Decimal] = {}
    reasons: list[str] = []
    for record in evidence:
        if record.lifecycle != EvidenceLifecycle.ADMITTED:
            reasons.append(f"EVIDENCE_NOT_ADMITTED:{record.object_id}")
            continue
        payload = payloads.get(record.object_id)
        if payload is None:
            reasons.append(f"EVIDENCE_PAYLOAD_MISSING:{record.object_id}")
            continue
        if record.payload_digest is None:
            reasons.append(f"EVIDENCE_DIGEST_MISSING:{record.object_id}")
            continue
        if canonical_hash(payload) != record.payload_digest:
            reasons.append(f"EVIDENCE_PAYLOAD_DIGEST_MISMATCH:{record.object_id}")
            continue
        raw_metrics = payload.get("metrics")
        if not isinstance(raw_metrics, Mapping):
            reasons.append(f"EVIDENCE_METRICS_MISSING:{record.object_id}")
            continue
        for metric_id, raw in raw_metrics.items():
            if not isinstance(raw, str):
                reasons.append(f"METRIC_NOT_DECIMAL_STRING:{metric_id}")
                continue
            try:
                value = Decimal(raw)
            except InvalidOperation:
                reasons.append(f"METRIC_INVALID_DECIMAL:{metric_id}")
                continue
            if not value.is_finite():
                reasons.append(f"METRIC_NONFINITE:{metric_id}")
                continue
            if metric_id in metrics and metrics[metric_id] != value:
                reasons.append(f"METRIC_CONFLICT:{metric_id}")
                continue
            metrics[metric_id] = value
    return metrics, tuple(reasons)


def adjudicate_attempt(
    proof: ProofObligation,
    rule: DecisionRule,
    admission_policy: EvidenceAdmissionPolicy,
    attempt: ExecutionAttemptEnvelope,
    evidence: Sequence[EvidenceRecord],
    payloads: Mapping[str, Mapping[str, Any]],
    *,
    object_id: str,
    revision_id: str,
    provenance: Provenance,
    existing_adjudications: Sequence[Adjudication] = (),
    independence_satisfied: bool | None = None,
    adjudicator_version: str = "g2e-p2-v1",
) -> Adjudication:
    if proof.decision_rule_ref != rule.exact_ref():
        raise CoreInvariantError("decision rule does not match frozen proof identity")
    if proof.evidence_admission_policy_ref != admission_policy.exact_ref():
        raise CoreInvariantError(
            "evidence admission policy does not match frozen proof identity"
        )
    if attempt.proof_ref != proof.exact_ref():
        raise CoreInvariantError("attempt does not bind exact frozen proof")
    if any(a.attempt_ref == attempt.exact_ref() for a in existing_adjudications):
        raise CoreInvariantError("execution attempt already adjudicated")

    verified_evidence: list[EvidenceRecord] = []
    reasons: list[str] = []

    for record in evidence:
        if record.lifecycle != EvidenceLifecycle.ADMITTED:
            reasons.append(f"EVIDENCE_NOT_ADMITTED:{record.object_id}")
            continue
        if record.admission_policy_ref != proof.evidence_admission_policy_ref:
            reasons.append(f"EVIDENCE_ADMISSION_POLICY_MISMATCH:{record.object_id}")
            continue
        if (
            admission_policy.require_attempt_linkage
            and record.producer_attempt_ref != attempt.exact_ref()
        ):
            reasons.append(f"EVIDENCE_ATTEMPT_LINK_MISMATCH:{record.object_id}")
            continue
        verified_evidence.append(record)

    admitted_refs = tuple(record.exact_ref() for record in verified_evidence)
    verdict = AdjudicationVerdict.UNRESOLVED

    if attempt.state != AttemptState.COMPLETED:
        verdict = AdjudicationVerdict.INVALID
        reasons.append(f"ATTEMPT_NOT_COMPLETED:{attempt.state}")
    elif proof.independence_policy_ref is not None and independence_satisfied is not True:
        verdict = AdjudicationVerdict.INVALID
        reasons.append("INDEPENDENCE_NOT_VERIFIED")
    elif reasons:
        verdict = AdjudicationVerdict.INVALID
    else:
        metrics, metric_reasons = _metric_values_from_evidence(
            verified_evidence, payloads
        )
        reasons.extend(metric_reasons)

        predicates = (
            _decision_predicates(rule.pass_expression)
            + _decision_predicates(rule.fail_expression)
        )
        required_metric_ids: set[str] = set()
        thresholds: dict[str, Decimal] = {}

        for predicate in predicates:
            if predicate.metric_id not in proof.metric_ids:
                raise CoreInvariantError(
                    f"decision rule metric not frozen in proof: {predicate.metric_id}"
                )
            if predicate.threshold_key not in proof.decision_thresholds:
                raise CoreInvariantError(
                    f"decision rule threshold not frozen in proof: {predicate.threshold_key}"
                )
            required_metric_ids.add(predicate.metric_id)
            thresholds[predicate.threshold_key] = Decimal(
                proof.decision_thresholds[predicate.threshold_key]
            )

        missing = sorted(required_metric_ids - set(metrics))
        if metric_reasons:
            verdict = AdjudicationVerdict.INVALID
        elif missing:
            reasons.append("MISSING_METRICS:" + ",".join(missing))
            verdict = (
                AdjudicationVerdict.INVALID
                if rule.missing_metric_behavior == "INVALID"
                else AdjudicationVerdict.UNRESOLVED
            )
        else:
            pass_value = _eval_decision_expression(
                rule.pass_expression, metrics, thresholds
            )
            fail_value = _eval_decision_expression(
                rule.fail_expression, metrics, thresholds
            )
            if pass_value and fail_value:
                verdict = AdjudicationVerdict.INVALID
                reasons.append("DECISION_RULE_OVERLAP")
            elif pass_value:
                verdict = AdjudicationVerdict.PASS
            elif fail_value:
                verdict = AdjudicationVerdict.FAIL
            else:
                verdict = AdjudicationVerdict.UNRESOLVED
                reasons.append("DECISION_RULE_INDETERMINATE")

    return Adjudication.sealed(
        object_id=object_id,
        revision_id=revision_id,
        provenance=provenance,
        proof_ref=proof.exact_ref(),
        attempt_ref=attempt.exact_ref(),
        admitted_evidence_refs=admitted_refs,
        decision_rule_hash=rule.content_hash,
        adjudicator_version=adjudicator_version,
        verdict=verdict,
        reason_codes=tuple(reasons),
    )


def close_proof(
    adjudication: Adjudication,
    retry_policy: ProofRetryPolicy,
    *,
    invalid_attempts_including_current: int = 0,
) -> ProofClosure:
    verdict = adjudication.verdict
    if verdict == AdjudicationVerdict.PASS:
        return ProofClosure(ProofOutcome.PASS, True, False)
    if verdict == AdjudicationVerdict.FAIL:
        return ProofClosure(ProofOutcome.FAIL, True, False)
    if verdict == AdjudicationVerdict.UNRESOLVED:
        return ProofClosure(ProofOutcome.UNRESOLVED, True, False)
    if invalid_attempts_including_current <= retry_policy.max_invalid_replacement_attempts:
        return ProofClosure(
            ProofOutcome.RETRY_ALLOWED,
            False,
            True,
            ("INVALID_REPLACEMENT_ALLOWED",),
        )
    return ProofClosure(
        ProofOutcome.UNRESOLVED,
        True,
        False,
        ("INVALID_RETRY_BUDGET_EXHAUSTED",),
    )


def resolve_claim(
    policy: ClaimResolutionPolicy,
    proof_outcomes: Mapping[str, ProofOutcome],
) -> ClaimResolution:
    values = [proof_outcomes.get(pid, ProofOutcome.OPEN) for pid in policy.proof_ids]
    if policy.mode == "ALL_REQUIRED":
        if any(v == ProofOutcome.FAIL for v in values):
            return ClaimResolution.FAIL
        if all(v == ProofOutcome.PASS for v in values):
            return ClaimResolution.PASS
        if all(v in {ProofOutcome.PASS, ProofOutcome.UNRESOLVED} for v in values):
            if any(v == ProofOutcome.UNRESOLVED for v in values):
                return ClaimResolution.UNRESOLVED
        return ClaimResolution.UNKNOWN

    if any(v == ProofOutcome.PASS for v in values):
        return ClaimResolution.PASS
    if all(v == ProofOutcome.FAIL for v in values):
        return ClaimResolution.FAIL
    if all(v in {ProofOutcome.FAIL, ProofOutcome.UNRESOLVED} for v in values):
        if any(v == ProofOutcome.UNRESOLVED for v in values):
            return ClaimResolution.UNRESOLVED
    return ClaimResolution.UNKNOWN


def _eval_goal_expression(
    expr: GoalExpression,
    resolutions: Mapping[str, ClaimResolution],
) -> bool | None:
    if expr.op == "CLAIM":
        value = resolutions.get(expr.claim_id or "", ClaimResolution.UNKNOWN)
        if value == ClaimResolution.UNKNOWN:
            return None
        return value == expr.expected_resolution

    values = [_eval_goal_expression(c, resolutions) for c in expr.children]
    if expr.op == "ALL":
        if any(v is False for v in values):
            return False
        if all(v is True for v in values):
            return True
        return None
    if expr.op == "ANY":
        if any(v is True for v in values):
            return True
        if all(v is False for v in values):
            return False
        return None
    raise CoreInvariantError(f"unsupported goal expression op: {expr.op}")


def evaluate_goal(
    closure: GoalClosureContract,
    claim_resolutions: Mapping[str, ClaimResolution],
    *,
    can_progress: bool,
    authorized_stop: bool = False,
) -> GoalVerdict:
    success = _eval_goal_expression(closure.success_expression, claim_resolutions)
    falsification = _eval_goal_expression(
        closure.falsification_expression, claim_resolutions
    )
    if success is True:
        return GoalVerdict.ACHIEVED
    if falsification is True:
        return GoalVerdict.FALSIFIED
    if authorized_stop:
        return GoalVerdict.STOPPED
    if not can_progress:
        return GoalVerdict.UNRESOLVED
    return GoalVerdict.IN_PROGRESS


def _rank_value(proof: ProofObligation, field_name: str) -> Any:
    if field_name == "hard_dependencies_unblocked":
        return len(proof.prerequisites)
    if field_name == "protected_resource_cost":
        return proof.protected_resource_cost
    if field_name == "resource_cost_class":
        return proof.resource_cost_class
    if field_name == "implementation_complexity":
        return proof.implementation_complexity
    if field_name == "proof_id":
        return proof.object_id
    raise CoreInvariantError(f"unsupported SelectionPolicy field: {field_name}")


def select_next_proof(
    proofs: Sequence[ProofObligation],
    policy: SelectionPolicy,
    claims_by_id: Mapping[str, Claim],
    proof_outcomes: Mapping[str, ProofOutcome],
    retry_policies: Mapping[str, ProofRetryPolicy],
    *,
    protected_resources: Sequence[ProtectedResource] = (),
    invalid_attempt_counts: Mapping[str, int] | None = None,
    authority_satisfied: Mapping[str, bool] | None = None,
    independence_satisfied: Mapping[str, bool] | None = None,
    amendment_valid: Mapping[str, bool] | None = None,
    selected_override: str | None = None,
    override_reason: str | None = None,
    object_id: str,
    revision_id: str,
    provenance: Provenance,
) -> SelectionDecision:
    invalid_attempt_counts = invalid_attempt_counts or {}
    authority_satisfied = authority_satisfied or {}
    independence_satisfied = independence_satisfied or {}
    amendment_valid = amendment_valid or {}

    admissible: list[ProofObligation] = []
    for proof in proofs:
        retry = retry_policies.get(proof.retry_policy_ref.object_id)
        if retry is None or retry.exact_ref() != proof.retry_policy_ref:
            continue
        result = check_proof_admissibility(
            proof,
            claims_by_id,
            proof_outcomes,
            retry,
            protected_resources,
            invalid_attempts_so_far=invalid_attempt_counts.get(proof.object_id, 0),
            authority_satisfied=authority_satisfied.get(proof.object_id, True),
            independence_satisfied=independence_satisfied.get(proof.object_id, True),
            amendment_valid=amendment_valid.get(proof.object_id, True),
        )
        if result.admissible:
            admissible.append(proof)

    if not admissible:
        raise CoreInvariantError("no admissible proof candidates")

    def rank_key(proof: ProofObligation):
        values: list[Any] = []
        for field in policy.rank_fields:
            value = _rank_value(proof, field.field_name)
            if field.direction == "DESC":
                if not isinstance(value, (int, float)):
                    raise CoreInvariantError(
                        f"DESC ranking only supported for numeric field: {field.field_name}"
                    )
                value = -value
            values.append(value)
        return tuple(values)

    ranked = sorted(admissible, key=rank_key)
    ranked_ids = tuple(p.object_id for p in ranked)

    selected = ranked_ids[0]
    authorized_override = False
    if selected_override is not None:
        if selected_override not in ranked_ids:
            raise CoreInvariantError("override cannot select inadmissible proof")
        if not policy.allow_authorized_non_default_choice:
            raise CoreInvariantError("SelectionPolicy forbids non-default override")
        selected = selected_override
        authorized_override = selected != ranked_ids[0]

    return SelectionDecision.sealed(
        object_id=object_id,
        revision_id=revision_id,
        provenance=provenance,
        policy_ref=policy.exact_ref(),
        admissible_proof_ids=tuple(sorted(ranked_ids)),
        ranked_proof_ids=ranked_ids,
        selected_proof_id=selected,
        authorized_override=authorized_override,
        override_reason=override_reason if authorized_override else None,
    )


def enforce_amendment_boundary(
    original: Any,
    candidate: Any,
    *,
    outcome_exposed: bool,
) -> AmendmentDecision:
    if not hasattr(original, "content_hash") or not hasattr(candidate, "content_hash"):
        raise CoreInvariantError("amendment comparison requires canonical objects")
    if original.content_hash == candidate.content_hash:
        return AmendmentDecision(True, False, False)
    if outcome_exposed:
        raise CoreInvariantError(
            "post-outcome normative semantic mutation requires new lineage"
        )
    return AmendmentDecision(False, True, False)


_SIGNATURE_FIELDS = (
    "proposition_family",
    "subject_population",
    "intervention",
    "comparator",
    "outcome_metric",
    "measurement_procedure",
    "environment_runtime",
    "data_cohort_regime",
    "artifact_model_identity",
    "temporal_version_regime",
    "assumptions",
    "boundaries",
)


def _signature_value(signature: ClaimSignature, dimension: str) -> str | None:
    if dimension not in _SIGNATURE_FIELDS:
        raise CoreInvariantError(f"unknown ClaimSignature dimension: {dimension}")
    value = getattr(signature, dimension)
    if value is None:
        return None
    if isinstance(value, tuple):
        return canonical_json(list(value))
    return str(value)


def assess_applicability(
    capsule: EvidenceCapsule,
    source_signature: ClaimSignature,
    target_signature: ClaimSignature,
    policy: ApplicabilityPolicy,
    *,
    target_goal_ref: ExactRef,
    target_claim_ref: ExactRef,
    target_proof_ref: ExactRef | None,
    purpose: str,
    source_integrity_valid: bool,
    provenance_overlap_refs: Sequence[ExactRef] = (),
    object_id: str,
    revision_id: str,
    provenance: Provenance,
) -> ApplicabilityAssessment:
    if capsule.claim_signature_ref != source_signature.exact_ref():
        raise CoreInvariantError("capsule does not bind supplied source ClaimSignature")
    if purpose not in {"REUSE", "SYNTHESIS"}:
        raise CoreInvariantError("applicability purpose must be REUSE or SYNTHESIS")

    dimensions = set(policy.required_exact_dimensions) | set(
        policy.allowed_partial_dimensions
    )
    if not dimensions:
        dimensions = set(_SIGNATURE_FIELDS)

    results: list[ApplicabilityDimension] = []
    by_name: dict[str, str] = {}
    for dimension in sorted(dimensions):
        source = _signature_value(source_signature, dimension)
        target = _signature_value(target_signature, dimension)
        if source == target:
            match = "EXACT"
        elif source is None or target is None:
            match = "UNKNOWN"
        elif dimension in set(policy.allowed_partial_dimensions):
            match = "PARTIAL"
        else:
            match = "INCOMPATIBLE"
        by_name[dimension] = match
        results.append(
            ApplicabilityDimension(
                dimension=dimension,
                source_value=source,
                target_value=target,
                match=match,
            )
        )

    reason_codes: list[str] = []
    if not source_integrity_valid:
        disposition = ReuseDisposition.INCOMPATIBLE
        reason_codes.append("SOURCE_INTEGRITY_INVALID")
    else:
        disposition = (
            ReuseDisposition.SYNTHESIS_INPUT
            if purpose == "SYNTHESIS"
            else ReuseDisposition.QUALIFIED_REUSE
        )
        for dimension in policy.required_exact_dimensions:
            match = by_name[dimension]
            if match == "INCOMPATIBLE":
                disposition = ReuseDisposition.INCOMPATIBLE
                reason_codes.append(f"REQUIRED_DIMENSION_INCOMPATIBLE:{dimension}")
                break
            if match != "EXACT":
                disposition = ReuseDisposition.REPLICATION_REQUIRED
                reason_codes.append(f"REQUIRED_DIMENSION_NOT_EXACT:{dimension}")
                break
        if disposition in {
            ReuseDisposition.QUALIFIED_REUSE,
            ReuseDisposition.SYNTHESIS_INPUT,
        }:
            incompatible = [
                d for d, match in by_name.items() if match == "INCOMPATIBLE"
            ]
            if incompatible:
                disposition = ReuseDisposition.REPLICATION_REQUIRED
                reason_codes.append(
                    "NONREQUIRED_DIMENSION_INCOMPATIBLE:" + ",".join(incompatible)
                )

    return ApplicabilityAssessment.sealed(
        object_id=object_id,
        revision_id=revision_id,
        provenance=provenance,
        source_capsule_ref=capsule.exact_ref(),
        target_goal_ref=target_goal_ref,
        target_claim_ref=target_claim_ref,
        target_proof_ref=target_proof_ref,
        policy_ref=policy.exact_ref(),
        dimensions=tuple(results),
        provenance_overlap_refs=tuple(provenance_overlap_refs),
        source_integrity_valid=source_integrity_valid,
        disposition=disposition,
        reason_codes=tuple(reason_codes),
    )


def validate_reuse_proof(
    metadata: ReuseProofMetadata,
    capsules: Sequence[EvidenceCapsule],
    assessments: Sequence[ApplicabilityAssessment],
) -> ValidationReport:
    reasons: list[str] = []
    capsule_refs = {ref_key(c.exact_ref()) for c in capsules}
    assessment_refs = {ref_key(a.exact_ref()) for a in assessments}

    if {ref_key(r) for r in metadata.capsule_refs} != capsule_refs:
        reasons.append("REUSE_CAPSULE_SET_MISMATCH")
    if {ref_key(r) for r in metadata.applicability_assessment_refs} != assessment_refs:
        reasons.append("REUSE_ASSESSMENT_SET_MISMATCH")
    for assessment in assessments:
        if assessment.disposition != ReuseDisposition.QUALIFIED_REUSE:
            reasons.append(
                f"REUSE_ASSESSMENT_NOT_QUALIFIED:{assessment.object_id}"
            )
        if ref_key(assessment.source_capsule_ref) not in capsule_refs:
            reasons.append(
                f"REUSE_ASSESSMENT_UNKNOWN_CAPSULE:{assessment.object_id}"
            )

    return ValidationReport(not reasons, tuple(reasons))


def build_independence_clusters(
    capsules: Sequence[EvidenceCapsule],
    policy: IndependencePolicy,
    *,
    provenance: Provenance,
    revision_id: str = "r1",
) -> tuple[EvidenceIndependenceCluster, ...]:
    ordered = sorted(capsules, key=lambda c: ref_token(c.exact_ref()))
    tokens: dict[str, set[str]] = {}
    ancestor_refs: dict[str, set[tuple[str, str, str]]] = {}
    by_token: dict[str, EvidenceCapsule] = {}

    for capsule in ordered:
        token = ref_token(capsule.exact_ref())
        by_token[token] = capsule
        exact_ancestors = {
            ref_key(r)
            for r in (
                tuple(capsule.provenance_ancestor_refs)
                + tuple(capsule.source_evidence_refs)
            )
        }
        ancestor_refs[token] = exact_ancestors
        token_set = {"ref:" + "|".join(k) for k in exact_ancestors}
        token_set.update("hint:" + h for h in capsule.independence_cluster_hints)
        token_set.add("source-package:" + capsule.source_package_ref)
        tokens[token] = token_set

    adjacency: dict[str, set[str]] = {t: set() for t in tokens}
    all_tokens = sorted(tokens)
    for i, left in enumerate(all_tokens):
        for right in all_tokens[i + 1 :]:
            if tokens[left] & tokens[right]:
                adjacency[left].add(right)
                adjacency[right].add(left)

    seen: set[str] = set()
    clusters: list[EvidenceIndependenceCluster] = []
    for start in all_tokens:
        if start in seen:
            continue
        stack = [start]
        members: list[str] = []
        seen.add(start)
        while stack:
            node = stack.pop()
            members.append(node)
            for nxt in sorted(adjacency[node], reverse=True):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        members.sort()

        common: set[tuple[str, str, str]] = set()
        if members:
            common = set(ancestor_refs[members[0]])
            for member in members[1:]:
                common &= ancestor_refs[member]

        member_refs = tuple(by_token[m].exact_ref() for m in members)
        shared_refs = tuple(
            ExactRef(object_id=k[0], revision_id=k[1], content_hash=k[2])
            for k in sorted(common)
        )
        cluster_hash = canonical_hash([list(ref_key(r)) for r in member_refs])[:16]
        clusters.append(
            EvidenceIndependenceCluster.sealed(
                object_id=f"independence-cluster-{cluster_hash}",
                revision_id=revision_id,
                provenance=provenance,
                member_capsule_refs=member_refs,
                shared_ancestor_refs=shared_refs,
                independence_policy_ref=policy.exact_ref(),
                independent_confirmation_units=1,
            )
        )
    return tuple(clusters)


def deduplicate_synthesis_observations(
    universe: SynthesisUniverse,
) -> dict[tuple[str, str, str], tuple[str, ...]]:
    grouped: dict[tuple[str, str, str], set[str]] = {}
    for observation in universe.observations:
        grouped.setdefault(ref_key(observation.exact_subject_ref), set()).add(
            observation.observation_ref
        )
    return {
        key: tuple(sorted(values))
        for key, values in sorted(grouped.items())
    }


def build_synthesis_candidates(
    contract: SynthesisContract,
    universe: SynthesisUniverse,
    assessments_by_subject: Mapping[
        tuple[str, str, str], ApplicabilityAssessment
    ],
    *,
    rule_results_by_subject: Mapping[str, Mapping[str, bool]] | None = None,
) -> tuple[SynthesisCandidate, ...]:
    if contract.universe_ref != universe.exact_ref():
        raise CoreInvariantError("SynthesisContract does not bind supplied universe")
    if not contract.outcome_blind_by_default:
        raise CoreInvariantError(
            "outcome-direction-sensitive inclusion is not qualified in P2"
        )

    rule_results_by_subject = rule_results_by_subject or {}
    grouped = deduplicate_synthesis_observations(universe)
    candidates: list[SynthesisCandidate] = []

    for key, observation_refs in grouped.items():
        subject_ref = ExactRef(
            object_id=key[0], revision_id=key[1], content_hash=key[2]
        )
        reasons: list[str] = []
        assessment = assessments_by_subject.get(key)
        if assessment is None:
            reasons.append("APPLICABILITY_ASSESSMENT_MISSING")
        elif assessment.source_capsule_ref != subject_ref:
            reasons.append("APPLICABILITY_SUBJECT_MISMATCH")
        elif assessment.disposition.value != contract.required_reuse_disposition:
            reasons.append(
                f"DISPOSITION_NOT_{contract.required_reuse_disposition}"
            )

        results = rule_results_by_subject.get(subject_ref.object_id, {})
        for rule in contract.inclusion_rules:
            if results.get(rule) is not True:
                reasons.append(f"INCLUSION_RULE_FAILED:{rule}")
        for rule in contract.exclusion_rules:
            if results.get(rule) is True:
                reasons.append(f"EXCLUSION_RULE_TRIGGERED:{rule}")
        for rule in contract.quality_gate:
            if results.get(rule) is not True:
                reasons.append(f"QUALITY_GATE_FAILED:{rule}")

        candidates.append(
            SynthesisCandidate(
                subject_ref=subject_ref,
                observation_refs=observation_refs,
                included=not reasons,
                reason_codes=tuple(reasons),
            )
        )

    return tuple(candidates)


def classify_synthesis(
    candidates: Sequence[SynthesisCandidate],
    capsules_by_subject: Mapping[tuple[str, str, str], EvidenceCapsule],
    universe: SynthesisUniverse,
    *,
    boundary_groups: Mapping[str, Sequence[ClaimResolution]] | None = None,
) -> ConvergenceClassification:
    if (
        universe.coverage.missing_or_inaccessible_sources
        or universe.coverage.publication_selection_bias_risks
    ):
        return ConvergenceClassification.INSUFFICIENT_EVIDENCE

    included = [c for c in candidates if c.included]
    if not included:
        return ConvergenceClassification.INSUFFICIENT_EVIDENCE

    if boundary_groups and len(boundary_groups) >= 2:
        uniform: set[ClaimResolution] = set()
        valid_boundary = True
        for resolutions in boundary_groups.values():
            values = set(resolutions)
            if len(values) != 1:
                valid_boundary = False
                break
            value = next(iter(values))
            if value not in {ClaimResolution.PASS, ClaimResolution.FAIL}:
                valid_boundary = False
                break
            uniform.add(value)
        if valid_boundary and len(uniform) >= 2:
            return ConvergenceClassification.BOUNDARY_IDENTIFIED

    resolutions: list[ClaimResolution] = []
    for candidate in included:
        capsule = capsules_by_subject.get(ref_key(candidate.subject_ref))
        if capsule is None:
            raise CoreInvariantError(
                f"included synthesis subject missing capsule: {candidate.subject_ref.object_id}"
            )
        resolutions.append(capsule.source_claim_resolution)

    if all(r == ClaimResolution.PASS for r in resolutions):
        return ConvergenceClassification.CORROBORATED
    if all(r == ClaimResolution.FAIL for r in resolutions):
        return ConvergenceClassification.CONTRADICTED
    if all(r == ClaimResolution.UNRESOLVED for r in resolutions):
        return ConvergenceClassification.UNRESOLVED
    return ConvergenceClassification.HETEROGENEOUS


def required_synthesis_provenance_closure(
    candidates: Sequence[SynthesisCandidate],
    capsules_by_subject: Mapping[tuple[str, str, str], EvidenceCapsule],
) -> set[tuple[str, str, str]]:
    required: set[tuple[str, str, str]] = set()
    for candidate in candidates:
        if not candidate.included:
            continue
        capsule = capsules_by_subject.get(ref_key(candidate.subject_ref))
        if capsule is None:
            raise CoreInvariantError(
                f"included synthesis subject missing capsule: {candidate.subject_ref.object_id}"
            )
        required.add(ref_key(capsule.exact_ref()))
        required.update(ref_key(r) for r in capsule.provenance_ancestor_refs)
    return required


def validate_synthesis_result_ancestry(
    result: SynthesisResult,
    candidates: Sequence[SynthesisCandidate],
    capsules_by_subject: Mapping[tuple[str, str, str], EvidenceCapsule],
) -> ValidationReport:
    required = required_synthesis_provenance_closure(
        candidates, capsules_by_subject
    )
    actual = {ref_key(r) for r in result.source_provenance_closure}
    missing = sorted(required - actual)
    if missing:
        return ValidationReport(
            False,
            tuple(
                "SYNTHESIS_PROVENANCE_MISSING:" + "|".join(item)
                for item in missing
            ),
        )
    return ValidationReport(True, ())
