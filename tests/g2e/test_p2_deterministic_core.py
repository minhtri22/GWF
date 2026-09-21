from __future__ import annotations

import pytest

from g2e import (
    AdjudicationVerdict,
    AmendmentPolicy,
    ApplicabilityPolicy,
    AttemptState,
    Claim,
    ClaimGraph,
    ClaimLifecycle,
    ClaimResolution,
    ClaimResolutionPolicy,
    ClaimSignature,
    CoverageStatement,
    DecisionExpression,
    DecisionRule,
    EvidenceAdmissionPolicy,
    EvidenceCapsule,
    EvidenceLifecycle,
    EvidenceRecord,
    EvidenceRelation,
    ExecutionAttemptEnvelope,
    FreshnessState,
    GoalClosureContract,
    GoalContract,
    GoalContractLifecycle,
    GoalExpression,
    GoalRequirement,
    GoalVerdict,
    IndependencePolicy,
    MetricPredicate,
    ProofLifecycle,
    ProofObligation,
    ProofRetryPolicy,
    ProtectedResource,
    Provenance,
    ReuseDisposition,
    ReuseProofMetadata,
    SelectionPolicy,
    SelectionRankField,
    SynthesisCandidate,
    SynthesisContract,
    SynthesisObservation,
    SynthesisResult,
    SynthesisUniverse,
    canonical_hash,
)
from g2e.engine import (
    CoreInvariantError,
    ProofOutcome,
    adjudicate_attempt,
    assess_applicability,
    build_independence_clusters,
    build_synthesis_candidates,
    check_proof_admissibility,
    classify_synthesis,
    close_proof,
    deduplicate_synthesis_observations,
    enforce_amendment_boundary,
    evaluate_evidence_admission,
    materialize_evidence_admission,
    evaluate_goal,
    ref_key,
    resolve_claim,
    select_next_proof,
    transition_protected_resource,
    validate_claim_graph_and_goal_closure,
    validate_evidence_relation,
    validate_reuse_proof,
    validate_synthesis_result_ancestry,
)

P = Provenance(created_by="p2-fixture", created_at="2026-09-21T07:30:00Z")


def sealed(cls, object_id: str, **kwargs):
    return cls.sealed(
        object_id=object_id,
        revision_id="r1",
        provenance=P,
        **kwargs,
    )


def rule(
    *,
    pass_op: str = "GE",
    pass_threshold: str = "0.80",
    fail_op: str = "LT",
    fail_threshold: str = "0.70",
    missing: str = "INVALID",
):
    pass_expr = DecisionExpression(
        op="PREDICATE",
        predicate=MetricPredicate(
            metric_id="score",
            operator=pass_op,
            threshold_key="pass",
        ),
    )
    fail_expr = DecisionExpression(
        op="PREDICATE",
        predicate=MetricPredicate(
            metric_id="score",
            operator=fail_op,
            threshold_key="fail",
        ),
    )
    dr = sealed(
        DecisionRule,
        f"rule-{pass_op}-{fail_op}-{pass_threshold}-{fail_threshold}-{missing}",
        pass_expression=pass_expr,
        fail_expression=fail_expr,
        missing_metric_behavior=missing,
    )
    return dr, {"pass": pass_threshold, "fail": fail_threshold}


def policies(*, resolution_mode="ALL_REQUIRED", proof_ids=("proof-1",)):
    resolution = sealed(
        ClaimResolutionPolicy,
        "resolution-" + "-".join(proof_ids),
        mode=resolution_mode,
        proof_ids=proof_ids,
    )
    admission = sealed(
        EvidenceAdmissionPolicy,
        "admission",
        accepted_source_classes=("FIXTURE", "CAPSULE"),
        require_integrity_hash=True,
        require_attempt_linkage=True,
        allowed_freshness_states=(FreshnessState.FRESH, FreshnessState.EXPOSED),
        allowed_derivation_depth=1,
    )
    retry = sealed(
        ProofRetryPolicy,
        "retry",
        max_invalid_replacement_attempts=1,
    )
    amendment = sealed(AmendmentPolicy, "amendment")
    independence = sealed(IndependencePolicy, "independence")
    return resolution, admission, retry, amendment, independence


def goal_claim_fixture(*, resolution_mode="ALL_REQUIRED", proof_ids=("proof-1",)):
    resolution, admission, retry, amendment, independence = policies(
        resolution_mode=resolution_mode,
        proof_ids=proof_ids,
    )
    req = sealed(
        GoalRequirement,
        "req-1",
        statement="bounded requirement",
        hard_constraint=True,
    )
    goal = sealed(
        GoalContract,
        "goal-1",
        lifecycle=GoalContractLifecycle.FROZEN,
        goal_statement="prove bounded requirement",
        requirements=(req,),
    )
    claim = sealed(
        Claim,
        "claim-1",
        proposition="bounded claim",
        claim_class="technical",
        resolution_policy_ref=resolution.exact_ref(),
        goal_requirement_ids=(req.object_id,),
        lifecycle=ClaimLifecycle.READY,
        resolution=ClaimResolution.UNKNOWN,
    )
    graph = sealed(
        ClaimGraph,
        "graph-1",
        goal_contract_ref=goal.exact_ref(),
        claims=(claim,),
        coverage_statement="all requirements mapped",
    )
    closure = sealed(
        GoalClosureContract,
        "closure-1",
        goal_contract_ref=goal.exact_ref(),
        claim_graph_ref=graph.exact_ref(),
        requirement_claim_map={req.object_id: (claim.object_id,)},
        success_expression=GoalExpression(
            op="CLAIM",
            claim_id=claim.object_id,
            expected_resolution=ClaimResolution.PASS,
        ),
        falsification_expression=GoalExpression(
            op="CLAIM",
            claim_id=claim.object_id,
            expected_resolution=ClaimResolution.FAIL,
        ),
        terminal_claim_ids=(claim.object_id,),
    )
    return (
        goal,
        req,
        claim,
        graph,
        closure,
        resolution,
        admission,
        retry,
        amendment,
        independence,
    )


def proof_fixture(
    claim: Claim,
    admission: EvidenceAdmissionPolicy,
    retry: ProofRetryPolicy,
    amendment: AmendmentPolicy,
    independence: IndependencePolicy,
    *,
    proof_id="proof-1",
    decision_rule=None,
    thresholds=None,
    prerequisites=(),
    protected_refs=(),
    resource_cost=0,
    complexity=0,
):
    dr, default_thresholds = rule()
    dr = decision_rule or dr
    thresholds = thresholds or default_thresholds
    return (
        sealed(
            ProofObligation,
            proof_id,
            lifecycle=ProofLifecycle.FROZEN,
            target_claim_id=claim.object_id,
            proposition=claim.proposition,
            prerequisites=prerequisites,
            metric_ids=("score",),
            decision_thresholds=thresholds,
            decision_rule_ref=dr.exact_ref(),
            evidence_admission_policy_ref=admission.exact_ref(),
            retry_policy_ref=retry.exact_ref(),
            amendment_policy_ref=amendment.exact_ref(),
            independence_policy_ref=independence.exact_ref(),
            protected_resource_refs=protected_refs,
            protected_resource_cost=resource_cost,
            resource_cost_class=resource_cost,
            implementation_complexity=complexity,
        ),
        dr,
    )


def attempt_for(proof, retry, *, state=AttemptState.COMPLETED, suffix="1"):
    return sealed(
        ExecutionAttemptEnvelope,
        f"attempt-envelope-{suffix}",
        attempt_id=f"attempt-{suffix}",
        proof_ref=proof.exact_ref(),
        state=state,
        implementation_ref="fixture@sha",
        config_hash="a" * 64,
        retry_policy_ref=retry.exact_ref(),
    )


def evidence_for(attempt, score: str, admission, *, object_id="e1"):
    payload = {"metrics": {"score": score}}
    candidate = sealed(
        EvidenceRecord,
        object_id,
        source_class="FIXTURE",
        lifecycle=EvidenceLifecycle.CANDIDATE,
        producer_attempt_ref=attempt.exact_ref(),
        payload_digest=canonical_hash(payload),
        freshness_state=FreshnessState.FRESH,
    )
    decision = evaluate_evidence_admission(candidate, admission)
    record = materialize_evidence_admission(
        candidate,
        admission,
        decision,
        revision_id="r2",
        provenance=P,
    )
    return record, payload


def capsule_fixture(
    *,
    object_id: str,
    resolution: ClaimResolution,
    signature: ClaimSignature,
    ancestor_refs=(),
    source_package="package-1",
    hints=(),
):
    goal = sealed(
        GoalContract,
        f"source-goal-{object_id}",
        lifecycle=GoalContractLifecycle.FROZEN,
        goal_statement="source",
    )
    resolution_policy = sealed(
        ClaimResolutionPolicy,
        f"source-policy-{object_id}",
        mode="ALL_REQUIRED",
        proof_ids=(f"source-proof-{object_id}",),
    )
    claim = sealed(
        Claim,
        f"source-claim-{object_id}",
        proposition="source",
        claim_class="technical",
        resolution_policy_ref=resolution_policy.exact_ref(),
        lifecycle=ClaimLifecycle.CLOSED,
        resolution=resolution,
    )
    return sealed(
        EvidenceCapsule,
        object_id,
        source_package_type="CLAIM_RESULT",
        source_package_ref=source_package,
        source_package_seal_hash="b" * 64,
        source_goal_ref=goal.exact_ref(),
        source_claim_ref=claim.exact_ref(),
        source_claim_resolution=resolution,
        claim_signature_ref=signature.exact_ref(),
        provenance_ancestor_refs=ancestor_refs,
        independence_cluster_hints=hints,
        capsule_policy_version="1",
    )


def test_claim_graph_and_goal_closure_validate():
    goal, _, _, graph, closure, resolution, *_ = goal_claim_fixture()
    report = validate_claim_graph_and_goal_closure(
        goal, graph, closure, {resolution.object_id: resolution}
    )
    assert report.valid
    assert report.reasons == ()


def test_goal_requirement_must_be_covered_or_declared_unresolved():
    goal, req, claim, graph, closure, resolution, *_ = goal_claim_fixture()
    broken_claim = claim.model_copy(update={"goal_requirement_ids": ()})
    broken_graph = ClaimGraph.sealed(
        object_id="graph-broken",
        revision_id="r1",
        provenance=P,
        goal_contract_ref=goal.exact_ref(),
        claims=(broken_claim,),
        coverage_statement="claims no longer cover requirement",
    )
    broken_closure = GoalClosureContract.sealed(
        object_id="closure-broken",
        revision_id="r1",
        provenance=P,
        goal_contract_ref=goal.exact_ref(),
        claim_graph_ref=broken_graph.exact_ref(),
        requirement_claim_map={req.object_id: ()},
        success_expression=closure.success_expression,
        falsification_expression=closure.falsification_expression,
        terminal_claim_ids=(claim.object_id,),
    )
    report = validate_claim_graph_and_goal_closure(
        goal, broken_graph, broken_closure, {resolution.object_id: resolution}
    )
    assert not report.valid
    assert "REQUIREMENT_UNCOVERED:req-1" in report.reasons


def test_goal_closure_exact_graph_binding_is_required():
    goal, _, _, graph, closure, resolution, *_ = goal_claim_fixture()
    wrong = closure.model_copy(
        update={
            "claim_graph_ref": graph.exact_ref().model_copy(
                update={"content_hash": "f" * 64}
            )
        }
    )
    report = validate_claim_graph_and_goal_closure(
        goal, graph, wrong, {resolution.object_id: resolution}
    )
    assert not report.valid
    assert "GOAL_CLOSURE_GRAPH_REF_MISMATCH" in report.reasons


def test_proof_admissibility_blocks_unsatisfied_hard_claim_dependency():
    (
        _,
        req,
        claim,
        _,
        _,
        resolution,
        admission,
        retry,
        amendment,
        independence,
    ) = goal_claim_fixture()
    dep = sealed(
        Claim,
        "dep",
        proposition="dependency",
        claim_class="technical",
        resolution_policy_ref=resolution.exact_ref(),
        goal_requirement_ids=(req.object_id,),
        lifecycle=ClaimLifecycle.CLOSED,
        resolution=ClaimResolution.FAIL,
    )
    target = claim.model_copy(update={"hard_prerequisite_claim_ids": ("dep",)})
    proof, _ = proof_fixture(target, admission, retry, amendment, independence)
    result = check_proof_admissibility(
        proof,
        {"dep": dep, target.object_id: target},
        {},
        retry,
    )
    assert not result.admissible
    assert "HARD_CLAIM_DEPENDENCY_UNSATISFIED:dep" in result.reasons


def test_proof_admissibility_blocks_terminal_replay():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    proof, _ = proof_fixture(claim, admission, retry, amendment, independence)
    result = check_proof_admissibility(
        proof,
        {claim.object_id: claim},
        {proof.object_id: ProofOutcome.FAIL},
        retry,
    )
    assert not result.admissible
    assert "TERMINAL_PROOF_REPLAY_FORBIDDEN" in result.reasons


def test_protected_resource_state_is_monotonic():
    resource = sealed(
        ProtectedResource,
        "resource-1",
        resource_type="confirmatory-seed",
        identity_ref="seed:42",
        freshness_state=FreshnessState.FRESH,
        reuse_allowed=False,
    )
    reserved = transition_protected_resource(
        resource, "RESERVE", revision_id="r2", provenance=P
    )
    exposed = transition_protected_resource(
        reserved, "EXPOSE", revision_id="r3", provenance=P
    )
    assert reserved.freshness_state == FreshnessState.RESERVED
    assert exposed.freshness_state == FreshnessState.EXPOSED
    with pytest.raises(CoreInvariantError):
        transition_protected_resource(
            exposed, "RESERVE", revision_id="r4", provenance=P
        )


def test_uncertain_recovery_fails_closed_to_exposed():
    resource = sealed(
        ProtectedResource,
        "resource-1",
        resource_type="confirmatory-seed",
        identity_ref="seed:42",
        freshness_state=FreshnessState.FRESH,
        reuse_allowed=False,
    )
    recovered = transition_protected_resource(
        resource,
        "RECOVERY_UNCERTAIN_ACCESS",
        revision_id="r2",
        provenance=P,
    )
    assert recovered.freshness_state == FreshnessState.EXPOSED


def test_evidence_admission_accepts_only_policy_compliant_evidence():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    proof, _ = proof_fixture(claim, admission, retry, amendment, independence)
    attempt = attempt_for(proof, retry)
    record, _ = evidence_for(attempt, "0.90", admission)
    decision = evaluate_evidence_admission(
        record,
        admission,
        independence_satisfied=(),
        payload_available=True,
    )
    assert decision.lifecycle == EvidenceLifecycle.ADMITTED


def test_evidence_admission_rejects_wrong_source_and_missing_integrity():
    policy = sealed(
        EvidenceAdmissionPolicy,
        "strict-admission",
        accepted_source_classes=("FIXTURE",),
        require_integrity_hash=True,
    )
    record = sealed(
        EvidenceRecord,
        "bad-evidence",
        source_class="REFERENCE",
        lifecycle=EvidenceLifecycle.CANDIDATE,
    )
    decision = evaluate_evidence_admission(record, policy)
    assert decision.lifecycle == EvidenceLifecycle.REJECTED
    assert "SOURCE_CLASS_NOT_ACCEPTED" in decision.reasons
    assert "INTEGRITY_HASH_REQUIRED" in decision.reasons


def test_evidence_relation_direction_is_deterministic():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    proof, _ = proof_fixture(claim, admission, retry, amendment, independence)
    attempt = attempt_for(proof, retry)
    record, _ = evidence_for(attempt, "0.90", admission)
    relation = sealed(
        EvidenceRelation,
        "rel-1",
        relation="PRODUCED_BY",
        subject_ref=record.exact_ref(),
        object_ref=attempt.exact_ref(),
    )
    objects = {
        ref_key(record.exact_ref()): record,
        ref_key(attempt.exact_ref()): attempt,
    }
    assert validate_evidence_relation(relation, objects).valid
    bad = relation.model_copy(update={"object_ref": proof.exact_ref()})
    objects[ref_key(proof.exact_ref())] = proof
    assert not validate_evidence_relation(bad, objects).valid


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        ("0.90", AdjudicationVerdict.PASS),
        ("0.60", AdjudicationVerdict.FAIL),
        ("0.75", AdjudicationVerdict.UNRESOLVED),
    ],
)
def test_adjudicator_known_pass_fail_unresolved(score, expected):
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    proof, dr = proof_fixture(claim, admission, retry, amendment, independence)
    attempt = attempt_for(proof, retry)
    record, payload = evidence_for(attempt, score, admission)
    adj = adjudicate_attempt(
        proof,
        dr,
        admission,
        attempt,
        (record,),
        {record.object_id: payload},
        object_id=f"adj-{score}",
        revision_id="r1",
        provenance=P,
        independence_satisfied=True,
    )
    assert adj.verdict == expected
    assert adj.decision_rule_hash == dr.content_hash


def test_adjudicator_invalid_execution_is_not_substantive_fail():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    proof, dr = proof_fixture(claim, admission, retry, amendment, independence)
    attempt = attempt_for(proof, retry, state=AttemptState.EXECUTOR_FAILED)
    adj = adjudicate_attempt(
        proof,
        dr,
        admission,
        attempt,
        (),
        {},
        object_id="adj-invalid",
        revision_id="r1",
        provenance=P,
        independence_satisfied=True,
    )
    assert adj.verdict == AdjudicationVerdict.INVALID


def test_adjudicator_rejects_tampered_evidence_payload():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    proof, dr = proof_fixture(claim, admission, retry, amendment, independence)
    attempt = attempt_for(proof, retry)
    record, _ = evidence_for(attempt, "0.90", admission)
    adj = adjudicate_attempt(
        proof,
        dr,
        admission,
        attempt,
        (record,),
        {record.object_id: {"metrics": {"score": "0.10"}}},
        object_id="adj-tampered",
        revision_id="r1",
        provenance=P,
        independence_satisfied=True,
    )
    assert adj.verdict == AdjudicationVerdict.INVALID
    assert any("DIGEST_MISMATCH" in reason for reason in adj.reason_codes)


def test_adjudication_is_one_shot_per_attempt():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    proof, dr = proof_fixture(claim, admission, retry, amendment, independence)
    attempt = attempt_for(proof, retry)
    record, payload = evidence_for(attempt, "0.90", admission)
    first = adjudicate_attempt(
        proof,
        dr,
        admission,
        attempt,
        (record,),
        {record.object_id: payload},
        object_id="adj-1",
        revision_id="r1",
        provenance=P,
        independence_satisfied=True,
    )
    with pytest.raises(CoreInvariantError, match="already adjudicated"):
        adjudicate_attempt(
            proof,
            dr,
            admission,
            attempt,
            (record,),
            {record.object_id: payload},
            object_id="adj-2",
            revision_id="r1",
            provenance=P,
            existing_adjudications=(first,),
        )


def test_adjudicator_rejects_rule_not_bound_by_proof():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    proof, _ = proof_fixture(claim, admission, retry, amendment, independence)
    other_rule, _ = rule(pass_op="GT")
    attempt = attempt_for(proof, retry)
    with pytest.raises(CoreInvariantError, match="decision rule"):
        adjudicate_attempt(
            proof,
            other_rule,
            admission,
            attempt,
            (),
            {},
            object_id="adj",
            revision_id="r1",
            provenance=P,
        )


def test_invalid_attempt_retry_budget_is_bounded():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    proof, dr = proof_fixture(claim, admission, retry, amendment, independence)
    attempt = attempt_for(proof, retry, state=AttemptState.EXECUTOR_FAILED)
    adj = adjudicate_attempt(
        proof,
        dr,
        admission,
        attempt,
        (),
        {},
        object_id="adj-invalid",
        revision_id="r1",
        provenance=P,
        independence_satisfied=True,
    )
    first = close_proof(adj, retry, invalid_attempts_including_current=1)
    exhausted = close_proof(adj, retry, invalid_attempts_including_current=2)
    assert first.outcome == ProofOutcome.RETRY_ALLOWED
    assert first.replacement_attempt_allowed
    assert exhausted.outcome == ProofOutcome.UNRESOLVED
    assert exhausted.terminal


def test_claim_resolution_all_required_multiple_proofs():
    policy = sealed(
        ClaimResolutionPolicy,
        "all-two",
        mode="ALL_REQUIRED",
        proof_ids=("p1", "p2"),
    )
    assert resolve_claim(
        policy, {"p1": ProofOutcome.PASS, "p2": ProofOutcome.PASS}
    ) == ClaimResolution.PASS
    assert resolve_claim(
        policy, {"p1": ProofOutcome.PASS, "p2": ProofOutcome.FAIL}
    ) == ClaimResolution.FAIL
    assert resolve_claim(
        policy, {"p1": ProofOutcome.PASS, "p2": ProofOutcome.UNRESOLVED}
    ) == ClaimResolution.UNRESOLVED


def test_claim_resolution_any_sufficient_preserves_alternate_path():
    policy = sealed(
        ClaimResolutionPolicy,
        "any-two",
        mode="ANY_SUFFICIENT",
        proof_ids=("p1", "p2"),
    )
    assert resolve_claim(
        policy, {"p1": ProofOutcome.FAIL, "p2": ProofOutcome.PASS}
    ) == ClaimResolution.PASS
    assert resolve_claim(
        policy, {"p1": ProofOutcome.FAIL, "p2": ProofOutcome.OPEN}
    ) == ClaimResolution.UNKNOWN


def test_prior_pass_cannot_directly_flip_claim():
    policy = sealed(
        ClaimResolutionPolicy,
        "reuse-claim-policy",
        mode="ALL_REQUIRED",
        proof_ids=("reuse-proof",),
    )
    outcomes = {"prior-capsule-pass": ProofOutcome.PASS}
    assert resolve_claim(policy, outcomes) == ClaimResolution.UNKNOWN


def test_goal_alternate_path_can_achieve_despite_one_failed_claim():
    req = sealed(GoalRequirement, "r", statement="goal")
    goal = sealed(
        GoalContract,
        "g",
        lifecycle=GoalContractLifecycle.FROZEN,
        goal_statement="alternate",
        requirements=(req,),
    )
    resolution = sealed(
        ClaimResolutionPolicy,
        "p",
        mode="ALL_REQUIRED",
        proof_ids=("proof",),
    )
    c1 = sealed(
        Claim,
        "c1",
        proposition="path one",
        claim_class="technical",
        resolution_policy_ref=resolution.exact_ref(),
        lifecycle=ClaimLifecycle.CLOSED,
        resolution=ClaimResolution.FAIL,
    )
    c2 = sealed(
        Claim,
        "c2",
        proposition="path two",
        claim_class="technical",
        resolution_policy_ref=resolution.exact_ref(),
        lifecycle=ClaimLifecycle.CLOSED,
        resolution=ClaimResolution.PASS,
    )
    graph = sealed(
        ClaimGraph,
        "cg",
        goal_contract_ref=goal.exact_ref(),
        claims=(c1, c2),
        coverage_statement="alternate paths",
        unresolved_coverage=(req.object_id,),
    )
    closure = sealed(
        GoalClosureContract,
        "gc",
        goal_contract_ref=goal.exact_ref(),
        claim_graph_ref=graph.exact_ref(),
        requirement_claim_map={req.object_id: ()},
        success_expression=GoalExpression(
            op="ANY",
            children=(
                GoalExpression(
                    op="CLAIM",
                    claim_id="c1",
                    expected_resolution=ClaimResolution.PASS,
                ),
                GoalExpression(
                    op="CLAIM",
                    claim_id="c2",
                    expected_resolution=ClaimResolution.PASS,
                ),
            ),
        ),
        falsification_expression=GoalExpression(
            op="ALL",
            children=(
                GoalExpression(
                    op="CLAIM",
                    claim_id="c1",
                    expected_resolution=ClaimResolution.FAIL,
                ),
                GoalExpression(
                    op="CLAIM",
                    claim_id="c2",
                    expected_resolution=ClaimResolution.FAIL,
                ),
            ),
        ),
        terminal_claim_ids=("c1", "c2"),
    )
    verdict = evaluate_goal(
        closure,
        {"c1": ClaimResolution.FAIL, "c2": ClaimResolution.PASS},
        can_progress=False,
    )
    assert verdict == GoalVerdict.ACHIEVED


def test_goal_becomes_unresolved_only_when_progress_is_exhausted():
    _, _, claim, _, closure, *_ = goal_claim_fixture()
    assert evaluate_goal(
        closure,
        {claim.object_id: ClaimResolution.UNKNOWN},
        can_progress=True,
    ) == GoalVerdict.IN_PROGRESS
    assert evaluate_goal(
        closure,
        {claim.object_id: ClaimResolution.UNKNOWN},
        can_progress=False,
    ) == GoalVerdict.UNRESOLVED


def test_selector_is_deterministic_and_uses_lexical_tie_break():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture(
        proof_ids=("proof-a", "proof-b")
    )
    p_b, _ = proof_fixture(
        claim,
        admission,
        retry,
        amendment,
        independence,
        proof_id="proof-b",
        resource_cost=1,
        complexity=1,
    )
    p_a, _ = proof_fixture(
        claim,
        admission,
        retry,
        amendment,
        independence,
        proof_id="proof-a",
        resource_cost=1,
        complexity=1,
    )
    policy = sealed(
        SelectionPolicy,
        "selection",
        rank_fields=(
            SelectionRankField(
                field_name="hard_dependencies_unblocked", direction="DESC"
            ),
            SelectionRankField(
                field_name="protected_resource_cost", direction="ASC"
            ),
            SelectionRankField(
                field_name="resource_cost_class", direction="ASC"
            ),
            SelectionRankField(
                field_name="implementation_complexity", direction="ASC"
            ),
            SelectionRankField(field_name="proof_id", direction="ASC"),
        ),
    )
    decision = select_next_proof(
        (p_b, p_a),
        policy,
        {claim.object_id: claim},
        {},
        {retry.object_id: retry},
        object_id="selection-decision",
        revision_id="r1",
        provenance=P,
    )
    assert decision.ranked_proof_ids == ("proof-a", "proof-b")
    assert decision.selected_proof_id == "proof-a"


def test_selector_cannot_override_to_inadmissible_proof():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    p1, _ = proof_fixture(
        claim, admission, retry, amendment, independence, proof_id="proof-1"
    )
    p2, _ = proof_fixture(
        claim,
        admission,
        retry,
        amendment,
        independence,
        proof_id="proof-2",
        prerequisites=("missing-prereq",),
    )
    policy = sealed(
        SelectionPolicy,
        "selection",
        rank_fields=(SelectionRankField(field_name="proof_id", direction="ASC"),),
    )
    with pytest.raises(CoreInvariantError, match="inadmissible"):
        select_next_proof(
            (p1, p2),
            policy,
            {claim.object_id: claim},
            {},
            {retry.object_id: retry},
            selected_override="proof-2",
            object_id="decision",
            revision_id="r1",
            provenance=P,
        )


def test_post_outcome_semantic_mutation_is_rejected():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    original, _ = proof_fixture(claim, admission, retry, amendment, independence)
    changed = ProofObligation.sealed(
        **{
            **original.model_dump(mode="python", exclude={"content_hash"}),
            "revision_id": "r2",
            "proposition": "mutated after exposure",
        }
    )
    with pytest.raises(CoreInvariantError, match="new lineage"):
        enforce_amendment_boundary(original, changed, outcome_exposed=True)


def test_pre_outcome_semantic_mutation_requires_refreeze():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    original, _ = proof_fixture(claim, admission, retry, amendment, independence)
    changed = ProofObligation.sealed(
        **{
            **original.model_dump(mode="python", exclude={"content_hash"}),
            "revision_id": "r2",
            "proposition": "changed pre-outcome",
        }
    )
    decision = enforce_amendment_boundary(
        original, changed, outcome_exposed=False
    )
    assert decision.refreeze_required
    assert not decision.unchanged


def signatures():
    source = sealed(
        ClaimSignature,
        "sig-source",
        proposition_family="reasoning_gain",
        subject_population="model-family-x",
        intervention="sft",
        comparator="base",
        outcome_metric="accuracy",
        environment_runtime="hf",
    )
    target = sealed(
        ClaimSignature,
        "sig-target",
        proposition_family="reasoning_gain",
        subject_population="model-family-x",
        intervention="sft",
        comparator="base",
        outcome_metric="accuracy",
        environment_runtime="hf",
    )
    return source, target


def test_applicability_exact_match_qualifies_reuse():
    source, target = signatures()
    capsule = capsule_fixture(
        object_id="cap-1",
        resolution=ClaimResolution.PASS,
        signature=source,
    )
    policy = sealed(
        ApplicabilityPolicy,
        "app-policy",
        required_exact_dimensions=(
            "proposition_family",
            "subject_population",
            "outcome_metric",
        ),
        provenance_overlap_policy="allow-none",
    )
    goal, _, claim, *_ = goal_claim_fixture()
    assessment = assess_applicability(
        capsule,
        source,
        target,
        policy,
        target_goal_ref=goal.exact_ref(),
        target_claim_ref=claim.exact_ref(),
        target_proof_ref=None,
        purpose="REUSE",
        source_integrity_valid=True,
        object_id="assessment",
        revision_id="r1",
        provenance=P,
    )
    assert assessment.disposition == ReuseDisposition.QUALIFIED_REUSE


def test_applicability_required_dimension_mismatch_does_not_qualify():
    source, target = signatures()
    target = ClaimSignature.sealed(
        **{
            **target.model_dump(mode="python", exclude={"content_hash"}),
            "revision_id": "r2",
            "subject_population": "different-model-family",
        }
    )
    capsule = capsule_fixture(
        object_id="cap-1",
        resolution=ClaimResolution.PASS,
        signature=source,
    )
    policy = sealed(
        ApplicabilityPolicy,
        "app-policy",
        required_exact_dimensions=("subject_population",),
        provenance_overlap_policy="allow-none",
    )
    goal, _, claim, *_ = goal_claim_fixture()
    assessment = assess_applicability(
        capsule,
        source,
        target,
        policy,
        target_goal_ref=goal.exact_ref(),
        target_claim_ref=claim.exact_ref(),
        target_proof_ref=None,
        purpose="REUSE",
        source_integrity_valid=True,
        object_id="assessment",
        revision_id="r1",
        provenance=P,
    )
    assert assessment.disposition == ReuseDisposition.INCOMPATIBLE


def test_reuse_proof_requires_qualified_assessments():
    source, target = signatures()
    capsule = capsule_fixture(
        object_id="cap-1",
        resolution=ClaimResolution.PASS,
        signature=source,
    )
    policy = sealed(
        ApplicabilityPolicy,
        "app-policy",
        required_exact_dimensions=("subject_population",),
        provenance_overlap_policy="allow-none",
    )
    goal, _, claim, _, _, _, admission, *_ = goal_claim_fixture()
    assessment = assess_applicability(
        capsule,
        source,
        target,
        policy,
        target_goal_ref=goal.exact_ref(),
        target_claim_ref=claim.exact_ref(),
        target_proof_ref=None,
        purpose="REUSE",
        source_integrity_valid=True,
        object_id="assessment",
        revision_id="r1",
        provenance=P,
    )
    metadata = sealed(
        ReuseProofMetadata,
        "reuse-meta",
        target_claim_ref=claim.exact_ref(),
        capsule_refs=(capsule.exact_ref(),),
        applicability_assessment_refs=(assessment.exact_ref(),),
        evidence_admission_policy_ref=admission.exact_ref(),
    )
    assert validate_reuse_proof(metadata, (capsule,), (assessment,)).valid
    bad_assessment = assessment.model_copy(
        update={"disposition": ReuseDisposition.REPLICATION_REQUIRED}
    )
    report = validate_reuse_proof(
        metadata, (capsule,), (bad_assessment,)
    )
    assert not report.valid


def test_shared_ancestry_clusters_dependent_capsules():
    source, _ = signatures()
    ancestor = sealed(
        EvidenceRecord,
        "ancestor",
        source_class="FIXTURE",
        lifecycle=EvidenceLifecycle.ADMITTED,
        payload_digest="a" * 64,
    ).exact_ref()
    c1 = capsule_fixture(
        object_id="cap-1",
        resolution=ClaimResolution.PASS,
        signature=source,
        ancestor_refs=(ancestor,),
        source_package="package-a",
    )
    c2 = capsule_fixture(
        object_id="cap-2",
        resolution=ClaimResolution.PASS,
        signature=source,
        ancestor_refs=(ancestor,),
        source_package="package-b",
    )
    policy = sealed(IndependencePolicy, "independence-cluster")
    clusters = build_independence_clusters((c1, c2), policy, provenance=P)
    assert len(clusters) == 1
    assert len(clusters[0].member_capsule_refs) == 2
    assert clusters[0].independent_confirmation_units == 1


def synthesis_fixture(*, bias=False):
    source, target = signatures()
    c1 = capsule_fixture(
        object_id="cap-1",
        resolution=ClaimResolution.PASS,
        signature=source,
        source_package="package-a",
    )
    c2 = capsule_fixture(
        object_id="cap-2",
        resolution=ClaimResolution.PASS,
        signature=source,
        source_package="package-b",
    )
    universe = sealed(
        SynthesisUniverse,
        "universe",
        observations=(
            SynthesisObservation(
                discovery_channel="G2E_LIBRARY_ADAPTER",
                observation_ref="obs-1",
                exact_subject_ref=c1.exact_ref(),
            ),
            SynthesisObservation(
                discovery_channel="REFERENCE_ACQUISITION_GWF_CATALOG",
                observation_ref="obs-2",
                exact_subject_ref=c1.exact_ref(),
            ),
            SynthesisObservation(
                discovery_channel="G2E_LIBRARY_ADAPTER",
                observation_ref="obs-3",
                exact_subject_ref=c2.exact_ref(),
            ),
        ),
        coverage=CoverageStatement(
            target_universe="all fixture capsules",
            searched_scopes=("fixture",),
            publication_selection_bias_risks=("known-bias",) if bias else (),
        ),
    )
    app_policy = sealed(
        ApplicabilityPolicy,
        "synth-app-policy",
        required_exact_dimensions=("subject_population", "outcome_metric"),
        provenance_overlap_policy="cluster",
    )
    ind_policy = sealed(IndependencePolicy, "synth-independence")
    goal, _, claim, *_ = goal_claim_fixture()
    a1 = assess_applicability(
        c1,
        source,
        target,
        app_policy,
        target_goal_ref=goal.exact_ref(),
        target_claim_ref=claim.exact_ref(),
        target_proof_ref=None,
        purpose="SYNTHESIS",
        source_integrity_valid=True,
        object_id="a1",
        revision_id="r1",
        provenance=P,
    )
    a2 = assess_applicability(
        c2,
        source,
        target,
        app_policy,
        target_goal_ref=goal.exact_ref(),
        target_claim_ref=claim.exact_ref(),
        target_proof_ref=None,
        purpose="SYNTHESIS",
        source_integrity_valid=True,
        object_id="a2",
        revision_id="r1",
        provenance=P,
    )
    contract = sealed(
        SynthesisContract,
        "synth-contract",
        target_goal_ref=goal.exact_ref(),
        target_claim_ref=claim.exact_ref(),
        question="do fixture results converge",
        universe_ref=universe.exact_ref(),
        inclusion_rules=("eligible",),
        exclusion_rules=(),
        outcome_blind_by_default=True,
        applicability_policy_ref=app_policy.exact_ref(),
        independence_policy_ref=ind_policy.exact_ref(),
        aggregation_method="qualitative-structured",
        conflict_policy="retain",
        boundary_policy="stratify",
        missing_data_policy="fail-closed",
        stopping_rule="frozen-universe",
    )
    assessments = {
        ref_key(c1.exact_ref()): a1,
        ref_key(c2.exact_ref()): a2,
    }
    rules = {
        c1.object_id: {"eligible": True},
        c2.object_id: {"eligible": True},
    }
    return c1, c2, universe, contract, assessments, rules, ind_policy


def test_synthesis_deduplicates_same_subject_across_discovery_channels():
    c1, c2, universe, contract, assessments, rules, _ = synthesis_fixture()
    grouped = deduplicate_synthesis_observations(universe)
    assert len(grouped) == 2
    assert len(grouped[ref_key(c1.exact_ref())]) == 2
    candidates = build_synthesis_candidates(
        contract, universe, assessments, rule_results_by_subject=rules
    )
    assert len(candidates) == 2
    assert all(c.included for c in candidates)


def test_synthesis_rejects_outcome_sensitive_inclusion_contract():
    _, _, universe, contract, assessments, rules, _ = synthesis_fixture()
    unsafe = SynthesisContract.sealed(
        **{
            **contract.model_dump(mode="python", exclude={"content_hash"}),
            "revision_id": "r2",
            "outcome_blind_by_default": False,
        }
    )
    with pytest.raises(CoreInvariantError, match="outcome-direction-sensitive"):
        build_synthesis_candidates(
            unsafe, universe, assessments, rule_results_by_subject=rules
        )


def test_synthesis_coverage_bias_constrains_classification():
    c1, c2, universe, contract, assessments, rules, _ = synthesis_fixture(bias=True)
    candidates = build_synthesis_candidates(
        contract, universe, assessments, rule_results_by_subject=rules
    )
    classification = classify_synthesis(
        candidates,
        {
            ref_key(c1.exact_ref()): c1,
            ref_key(c2.exact_ref()): c2,
        },
        universe,
    )
    assert classification.value == "INSUFFICIENT_EVIDENCE"


def test_synthesis_boundary_regimes_are_not_forced_into_contradiction():
    c1, c2, universe, contract, assessments, rules, _ = synthesis_fixture()
    candidates = build_synthesis_candidates(
        contract, universe, assessments, rule_results_by_subject=rules
    )
    classification = classify_synthesis(
        candidates,
        {
            ref_key(c1.exact_ref()): c1,
            ref_key(c2.exact_ref()): c2,
        },
        universe,
        boundary_groups={
            "regime-a": (ClaimResolution.PASS, ClaimResolution.PASS),
            "regime-b": (ClaimResolution.FAIL, ClaimResolution.FAIL),
        },
    )
    assert classification.value == "BOUNDARY_IDENTIFIED"


def test_synthesis_result_requires_transitive_capsule_ancestry():
    source, _ = signatures()
    ancestor_record = sealed(
        EvidenceRecord,
        "ancestor",
        source_class="FIXTURE",
        lifecycle=EvidenceLifecycle.ADMITTED,
        payload_digest="a" * 64,
    )
    c1 = capsule_fixture(
        object_id="cap-1",
        resolution=ClaimResolution.PASS,
        signature=source,
        ancestor_refs=(ancestor_record.exact_ref(),),
    )
    c2, _, universe, contract, assessments, rules, ind_policy = synthesis_fixture()
    candidates = (
        SynthesisCandidate(
            subject_ref=c1.exact_ref(),
            observation_refs=("obs-x",),
            included=True,
            reason_codes=(),
        ),
    )
    result = sealed(
        SynthesisResult,
        "synth-result",
        contract_ref=contract.exact_ref(),
        universe_ref=universe.exact_ref(),
        candidates=candidates,
        applicability_refs=(),
        independence_cluster_refs=(),
        classification="CORROBORATED",
        source_provenance_closure=(c1.exact_ref(),),
    )
    report = validate_synthesis_result_ancestry(
        result, candidates, {ref_key(c1.exact_ref()): c1}
    )
    assert not report.valid
    fixed = SynthesisResult.sealed(
        **{
            **result.model_dump(mode="python", exclude={"content_hash"}),
            "revision_id": "r2",
            "source_provenance_closure": (
                c1.exact_ref(),
                ancestor_record.exact_ref(),
            ),
        }
    )
    assert validate_synthesis_result_ancestry(
        fixed, candidates, {ref_key(c1.exact_ref()): c1}
    ).valid


def test_synthesis_contract_post_outcome_mutation_is_no_rescue():
    _, _, _, contract, _, _, _ = synthesis_fixture()
    changed = SynthesisContract.sealed(
        **{
            **contract.model_dump(mode="python", exclude={"content_hash"}),
            "revision_id": "r2",
            "aggregation_method": "changed-after-outcome",
        }
    )
    with pytest.raises(CoreInvariantError, match="new lineage"):
        enforce_amendment_boundary(contract, changed, outcome_exposed=True)



def test_admission_materialization_binds_exact_policy():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    proof, _ = proof_fixture(claim, admission, retry, amendment, independence)
    attempt = attempt_for(proof, retry)
    record, _ = evidence_for(attempt, "0.90", admission)
    assert record.lifecycle == EvidenceLifecycle.ADMITTED
    assert record.admission_policy_ref == admission.exact_ref()
    assert record.admission_reason == "ADMITTED"


def test_adjudicator_rejects_unbound_admitted_evidence():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    proof, dr = proof_fixture(claim, admission, retry, amendment, independence)
    attempt = attempt_for(proof, retry)
    payload = {"metrics": {"score": "0.90"}}
    forged = sealed(
        EvidenceRecord,
        "forged",
        source_class="FIXTURE",
        lifecycle=EvidenceLifecycle.ADMITTED,
        producer_attempt_ref=attempt.exact_ref(),
        payload_digest=canonical_hash(payload),
        freshness_state=FreshnessState.FRESH,
    )
    adj = adjudicate_attempt(
        proof,
        dr,
        admission,
        attempt,
        (forged,),
        {forged.object_id: payload},
        object_id="adj-forged",
        revision_id="r1",
        provenance=P,
        independence_satisfied=True,
    )
    assert adj.verdict == AdjudicationVerdict.INVALID
    assert adj.admitted_evidence_refs == ()
    assert any("ADMISSION_POLICY_MISMATCH" in r for r in adj.reason_codes)


def test_adjudicator_requires_independence_verification_when_bound():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    proof, dr = proof_fixture(claim, admission, retry, amendment, independence)
    attempt = attempt_for(proof, retry)
    record, payload = evidence_for(attempt, "0.90", admission)
    adj = adjudicate_attempt(
        proof,
        dr,
        admission,
        attempt,
        (record,),
        {record.object_id: payload},
        object_id="adj-independence",
        revision_id="r1",
        provenance=P,
    )
    assert adj.verdict == AdjudicationVerdict.INVALID
    assert "INDEPENDENCE_NOT_VERIFIED" in adj.reason_codes


def test_direct_admissibility_rejects_wrong_retry_policy_ref():
    _, _, claim, _, _, _, admission, retry, amendment, independence = goal_claim_fixture()
    proof, _ = proof_fixture(claim, admission, retry, amendment, independence)
    wrong = sealed(
        ProofRetryPolicy,
        "wrong-retry",
        max_invalid_replacement_attempts=retry.max_invalid_replacement_attempts,
    )
    result = check_proof_admissibility(
        proof,
        {claim.object_id: claim},
        {},
        wrong,
    )
    assert not result.admissible
    assert "RETRY_POLICY_REF_MISMATCH" in result.reasons
