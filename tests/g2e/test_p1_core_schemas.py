from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from g2e import (
    Adjudication,
    AdjudicationVerdict,
    AmbiguityRecord,
    AttemptState,
    AuthorityPolicy,
    BackendQualificationStatus,
    Claim,
    ClaimGraph,
    ClaimLifecycle,
    ClaimResolution,
    ClaimResolutionPolicy,
    ClaimResultPackage,
    DecisionExpression,
    DecisionRule,
    EvidenceAdmissionPolicy,
    EvidenceLifecycle,
    EvidenceRecord,
    ExecutionAttemptEnvelope,
    ExecutionResult,
    GoalContract,
    GoalContractLifecycle,
    GoalExpression,
    IndependencePolicy,
    LibraryCapability,
    LibraryCapabilityManifest,
    LibraryExecutionStatus,
    LibraryQueryContract,
    LibraryQueryExecution,
    MetricPredicate,
    PackageManifest,
    PackageMember,
    PackageSeal,
    ProofLifecycle,
    ProofObligation,
    ProofRetryPolicy,
    Provenance,
    ReuseProofMetadata,
    RuntimeCapability,
    RuntimeCapabilityManifest,
    RuntimeMode,
    SCHEMA_REGISTRY,
    SelectionPolicy,
    SelectionRankField,
    AmendmentPolicy,
    canonical_hash,
    canonical_json,
    schema_catalog,
)

P = Provenance(created_by="p1-test", created_at="2026-09-21T03:00:00Z")


def sealed(cls, object_id: str, **kwargs):
    return cls.sealed(
        object_id=object_id,
        revision_id="r1",
        provenance=P,
        **kwargs,
    )


def base_decision_rule():
    predicate = DecisionExpression(
        op="PREDICATE",
        predicate=MetricPredicate(
            metric_id="accuracy",
            operator="GE",
            threshold_key="accuracy",
        ),
    )
    fail_predicate = DecisionExpression(
        op="PREDICATE",
        predicate=MetricPredicate(
            metric_id="accuracy",
            operator="LT",
            threshold_key="accuracy",
        ),
    )
    return sealed(
        DecisionRule,
        "decision-rule-1",
        pass_expression=predicate,
        fail_expression=fail_predicate,
        missing_metric_behavior="INVALID",
    )


def base_policies():
    resolution = sealed(
        ClaimResolutionPolicy,
        "claim-resolution-1",
        mode="ALL_REQUIRED",
        proof_ids=("proof-1",),
    )
    admission = sealed(
        EvidenceAdmissionPolicy,
        "admission-1",
        accepted_source_classes=("FIXTURE",),
        allowed_freshness_states=(),
    )
    retry = sealed(
        ProofRetryPolicy,
        "retry-1",
        max_invalid_replacement_attempts=1,
    )
    amendment = sealed(AmendmentPolicy, "amendment-1")
    independence = sealed(
        IndependencePolicy,
        "independence-1",
        required_dimensions=(),
    )
    return resolution, admission, retry, amendment, independence


def test_schema_registry_covers_p1_surface():
    required = {
        "goal_contract",
        "goal_closure_contract",
        "claim_graph",
        "claim_resolution_policy",
        "proof_obligation",
        "proof_retry_policy",
        "decision_rule",
        "runtime_capability_manifest",
        "execution_attempt_envelope",
        "execution_result",
        "evidence_record",
        "evidence_relation",
        "evidence_admission_policy",
        "protected_resource",
        "adjudication",
        "selection_policy",
        "selection_decision",
        "amendment_policy",
        "authority_policy",
        "independence_policy",
        "governance_disposition",
        "package_manifest",
        "package_seal",
        "claim_result_package",
        "evidence_capsule",
        "claim_signature",
        "applicability_policy",
        "applicability_assessment",
        "reuse_proof_metadata",
        "evidence_independence_cluster",
        "synthesis_universe",
        "synthesis_contract",
        "synthesis_result",
        "library_query_contract",
        "library_query_execution",
        "library_publication_contract",
        "library_snapshot",
        "library_capability_manifest",
    }
    assert required <= set(SCHEMA_REGISTRY)
    catalog = schema_catalog()
    assert set(catalog) == set(SCHEMA_REGISTRY)
    for schema in catalog.values():
        json.dumps(schema)


def test_canonical_json_is_nfc_sorted_and_stable():
    composed = {"b": "é", "a": [1, "x"]}
    decomposed = {"a": [1, "x"], "b": "e\u0301"}
    assert canonical_json(composed) == canonical_json(decomposed)
    assert canonical_hash(composed) == canonical_hash(decomposed)
    assert canonical_json(composed) == '{"a":[1,"x"],"b":"é"}'


def test_authoritative_hash_detects_tamper():
    goal = sealed(
        GoalContract,
        "goal-1",
        lifecycle=GoalContractLifecycle.FROZEN,
        goal_statement="Prove a bounded technical goal.",
    )
    GoalContract.parse_authoritative(goal.model_dump(mode="json"))
    tampered = goal.model_dump(mode="json")
    tampered["goal_statement"] = "Changed after seal."
    with pytest.raises(ValidationError, match="content_hash mismatch"):
        GoalContract.parse_authoritative(tampered)


def test_unknown_schema_major_fails_closed():
    with pytest.raises(ValidationError, match="unsupported schema major"):
        GoalContract.sealed(
            schema_version="2.0",
            object_id="goal-1",
            revision_id="r1",
            provenance=P,
            lifecycle=GoalContractLifecycle.FROZEN,
            goal_statement="x",
        )


def test_extra_fields_fail_closed():
    goal = sealed(
        GoalContract,
        "goal-1",
        lifecycle=GoalContractLifecycle.FROZEN,
        goal_statement="x",
    )
    payload = goal.model_dump(mode="json")
    payload["unexpected"] = "forbidden"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        GoalContract.model_validate(payload)


def test_goal_expression_shape_fails_closed():
    with pytest.raises(ValidationError):
        GoalExpression(
            op="CLAIM",
            claim_id="c1",
            expected_resolution=ClaimResolution.PASS,
            children=(
                GoalExpression(
                    op="ALL",
                    children=(
                        GoalExpression(
                            op="CLAIM",
                            claim_id="c2",
                            expected_resolution=ClaimResolution.PASS,
                        ),
                    ),
                ),
            ),
        )
    with pytest.raises(ValidationError):
        GoalExpression(op="ALL", children=())


def test_claim_graph_hard_dependencies_must_be_dag():
    resolution, *_ = base_policies()
    c1 = sealed(
        Claim,
        "c1",
        proposition="A",
        claim_class="technical",
        hard_prerequisite_claim_ids=("c2",),
        resolution_policy_ref=resolution.exact_ref(),
        lifecycle=ClaimLifecycle.BLOCKED,
        resolution=ClaimResolution.UNKNOWN,
    )
    c2 = sealed(
        Claim,
        "c2",
        proposition="B",
        claim_class="technical",
        hard_prerequisite_claim_ids=("c1",),
        resolution_policy_ref=resolution.exact_ref(),
        lifecycle=ClaimLifecycle.BLOCKED,
        resolution=ClaimResolution.UNKNOWN,
    )
    goal = sealed(
        GoalContract,
        "g1",
        lifecycle=GoalContractLifecycle.FROZEN,
        goal_statement="g",
    )
    with pytest.raises(ValidationError, match="dependency cycle"):
        sealed(
            ClaimGraph,
            "graph-1",
            goal_contract_ref=goal.exact_ref(),
            claims=(c1, c2),
            coverage_statement="fixture",
        )


def test_claim_graph_unknown_dependency_fails():
    resolution, *_ = base_policies()
    c1 = sealed(
        Claim,
        "c1",
        proposition="A",
        claim_class="technical",
        hard_prerequisite_claim_ids=("missing",),
        resolution_policy_ref=resolution.exact_ref(),
        lifecycle=ClaimLifecycle.BLOCKED,
        resolution=ClaimResolution.UNKNOWN,
    )
    goal = sealed(
        GoalContract,
        "g1",
        lifecycle=GoalContractLifecycle.FROZEN,
        goal_statement="g",
    )
    with pytest.raises(ValidationError, match="unknown prerequisites"):
        sealed(
            ClaimGraph,
            "graph-1",
            goal_contract_ref=goal.exact_ref(),
            claims=(c1,),
            coverage_statement="fixture",
        )


def test_proof_thresholds_are_decimal_strings():
    _, admission, retry, amendment, independence = base_policies()
    proof = sealed(
        ProofObligation,
        "proof-1",
        lifecycle=ProofLifecycle.FROZEN,
        target_claim_id="claim-1",
        proposition="p",
        decision_thresholds={"accuracy": "0.80"},
        evidence_admission_policy_ref=admission.exact_ref(),
        decision_rule_ref=base_decision_rule().exact_ref(),
        retry_policy_ref=retry.exact_ref(),
        amendment_policy_ref=amendment.exact_ref(),
        independence_policy_ref=independence.exact_ref(),
    )
    assert proof.decision_thresholds["accuracy"] == "0.80"
    with pytest.raises(ValidationError):
        sealed(
            ProofObligation,
            "proof-bad",
            lifecycle=ProofLifecycle.FROZEN,
            target_claim_id="claim-1",
            proposition="p",
            decision_thresholds={"accuracy": "not-decimal"},
            evidence_admission_policy_ref=admission.exact_ref(),
            retry_policy_ref=retry.exact_ref(),
            amendment_policy_ref=amendment.exact_ref(),
        )


def test_execution_state_is_not_adjudication_verdict():
    _, admission, retry, amendment, _ = base_policies()
    proof = sealed(
        ProofObligation,
        "proof-1",
        lifecycle=ProofLifecycle.FROZEN,
        target_claim_id="claim-1",
        proposition="p",
        evidence_admission_policy_ref=admission.exact_ref(),
        decision_rule_ref=base_decision_rule().exact_ref(),
        retry_policy_ref=retry.exact_ref(),
        amendment_policy_ref=amendment.exact_ref(),
    )
    attempt = sealed(
        ExecutionAttemptEnvelope,
        "attempt-envelope-1",
        attempt_id="attempt-1",
        proof_ref=proof.exact_ref(),
        state=AttemptState.COMPLETED,
        implementation_ref="fixture@sha",
        config_hash="a" * 64,
        retry_policy_ref=retry.exact_ref(),
    )
    evidence = sealed(
        EvidenceRecord,
        "e1",
        source_class="FIXTURE",
        lifecycle=EvidenceLifecycle.ADMITTED,
        producer_attempt_ref=attempt.exact_ref(),
    )
    adj = sealed(
        Adjudication,
        "adj-1",
        proof_ref=proof.exact_ref(),
        attempt_ref=attempt.exact_ref(),
        admitted_evidence_refs=(evidence.exact_ref(),),
        decision_rule_hash="rule-v1",
        adjudicator_version="fixture-1",
        verdict=AdjudicationVerdict.FAIL,
    )
    assert attempt.state == AttemptState.COMPLETED
    assert adj.verdict == AdjudicationVerdict.FAIL


def test_claim_result_package_rejects_unknown_resolution():
    goal = sealed(
        GoalContract,
        "g",
        lifecycle=GoalContractLifecycle.FROZEN,
        goal_statement="g",
    )
    resolution, *_ = base_policies()
    claim = sealed(
        Claim,
        "c",
        proposition="c",
        claim_class="technical",
        resolution_policy_ref=resolution.exact_ref(),
        lifecycle=ClaimLifecycle.CLOSED,
        resolution=ClaimResolution.UNKNOWN,
    )
    graph = sealed(
        ClaimGraph,
        "cg",
        goal_contract_ref=goal.exact_ref(),
        claims=(claim,),
        coverage_statement="fixture",
    )
    with pytest.raises(ValidationError, match="terminal claim resolution"):
        sealed(
            ClaimResultPackage,
            "crp",
            goal_contract_ref=goal.exact_ref(),
            claim_graph_ref=graph.exact_ref(),
            claim_ref=claim.exact_ref(),
            claim_resolution=ClaimResolution.UNKNOWN,
            proof_result_refs=(),
            evidence_refs=(),
            manifest_members=(),
            package_manifest_hash="a" * 64,
            package_seal_hash="b" * 64,
        )


def test_library_query_failure_cannot_claim_complete():
    query = sealed(
        LibraryQueryContract,
        "q1",
        query_payload={"type": "evidence_capsule"},
        required_capability_ids=("GAC_METADATA_CORE",),
        access_scope=("WORKSPACE",),
    )
    with pytest.raises(ValidationError, match="cannot claim complete"):
        sealed(
            LibraryQueryExecution,
            "qe1",
            query_ref=query.exact_ref(),
            backend_id="gwf-gac",
            backend_version="0",
            snapshot_ref="snapshot-1",
            status=LibraryExecutionStatus.BACKEND_UNAVAILABLE,
            complete=True,
        )


def test_library_manifest_forbids_silent_fallback_and_records_qualification():
    cap = LibraryCapability(
        capability_id="GAC_G2E_CONSUMER",
        status=BackendQualificationStatus.UNQUALIFIED,
        evidence_refs=("gate:pending",),
    )
    manifest = sealed(
        LibraryCapabilityManifest,
        "lib-cap",
        backend_id="gwf-gac",
        backend_type="GWF_GAC",
        adapter_version="p1-schema",
        supported_schema_versions=("1.0",),
        capabilities=(cap,),
        security_access_model="GWF authority intersection",
        exact_backend_revision="be7d606c64a97d9525d1f72d744fe5b7a336ff0c",
    )
    assert manifest.silent_fallback_allowed is False
    with pytest.raises(ValidationError):
        LibraryCapabilityManifest.sealed(
            object_id="bad",
            revision_id="r1",
            provenance=P,
            backend_id="gwf-gac",
            backend_type="GWF_GAC",
            adapter_version="x",
            supported_schema_versions=("1.0",),
            capabilities=(cap,),
            security_access_model="x",
            silent_fallback_allowed=True,
        )


def test_selection_policy_schema_can_encode_deterministic_tie_break():
    policy = sealed(
        SelectionPolicy,
        "sel-1",
        rank_fields=(
            SelectionRankField(
                field_name="hard_dependencies_unblocked",
                direction="DESC",
            ),
            SelectionRankField(
                field_name="protected_resource_cost",
                direction="ASC",
            ),
            SelectionRankField(
                field_name="resource_cost_class",
                direction="ASC",
            ),
            SelectionRankField(
                field_name="implementation_complexity",
                direction="ASC",
            ),
            SelectionRankField(field_name="proof_id", direction="ASC"),
        ),
    )
    assert policy.rank_fields[-1].field_name == "proof_id"


def test_authority_policy_cannot_enable_delegated_escalation():
    policy = sealed(AuthorityPolicy, "auth", actions=())
    assert policy.delegated_authority_may_exceed_parent is False



def test_canonical_json_rejects_nfc_key_collision():
    with pytest.raises(ValueError, match="canonical key collision"):
        canonical_json({"é": 1, "e\u0301": 2})


def test_frozen_goal_rejects_unresolved_blocking_ambiguity():
    with pytest.raises(ValidationError, match="blocking ambiguities"):
        sealed(
            GoalContract,
            "goal-blocked",
            lifecycle=GoalContractLifecycle.FROZEN,
            goal_statement="g",
            ambiguities=(
                AmbiguityRecord(
                    ambiguity_id="a1",
                    description="must resolve",
                    blocking=True,
                    owner="goal-owner",
                ),
            ),
        )


def test_authority_policy_rejects_delegated_escalation():
    with pytest.raises(ValidationError):
        sealed(
            AuthorityPolicy,
            "auth-bad",
            actions=(),
            delegated_authority_may_exceed_parent=True,
        )


def test_proof_threshold_rejects_nan_and_infinity():
    _, admission, retry, amendment, _ = base_policies()
    for bad in ("NaN", "Infinity", "-Infinity"):
        with pytest.raises(ValidationError, match="finite decimal text"):
            sealed(
                ProofObligation,
                f"proof-{bad}",
                lifecycle=ProofLifecycle.FROZEN,
                target_claim_id="claim-1",
                proposition="p",
                decision_thresholds={"metric": bad},
                evidence_admission_policy_ref=admission.exact_ref(),
                retry_policy_ref=retry.exact_ref(),
                amendment_policy_ref=amendment.exact_ref(),
            )


def test_reuse_proof_metadata_is_explicit_and_no_empirical_execution():
    goal = sealed(
        GoalContract,
        "g-reuse",
        lifecycle=GoalContractLifecycle.FROZEN,
        goal_statement="reuse",
    )
    resolution, admission, *_ = base_policies()
    claim = sealed(
        Claim,
        "c-reuse",
        proposition="reuse prior evidence",
        claim_class="reuse",
        resolution_policy_ref=resolution.exact_ref(),
        lifecycle=ClaimLifecycle.READY,
        resolution=ClaimResolution.UNKNOWN,
    )
    metadata = sealed(
        ReuseProofMetadata,
        "reuse-meta",
        target_claim_ref=claim.exact_ref(),
        capsule_refs=(goal.exact_ref(),),
        applicability_assessment_refs=(goal.exact_ref(),),
        evidence_admission_policy_ref=admission.exact_ref(),
    )
    assert metadata.no_new_empirical_execution is True
    with pytest.raises(ValidationError):
        ReuseProofMetadata.sealed(
            object_id="bad-reuse",
            revision_id="r1",
            provenance=P,
            target_claim_ref=claim.exact_ref(),
            capsule_refs=(goal.exact_ref(),),
            applicability_assessment_refs=(goal.exact_ref(),),
            evidence_admission_policy_ref=admission.exact_ref(),
            no_new_empirical_execution=False,
        )


def test_library_manifest_rejects_unknown_schema_major():
    cap = LibraryCapability(
        capability_id="LOCAL",
        status=BackendQualificationStatus.QUALIFIED,
    )
    with pytest.raises(ValidationError, match="unsupported schema major"):
        sealed(
            LibraryCapabilityManifest,
            "lib-v2",
            backend_id="standalone",
            backend_type="STANDALONE",
            adapter_version="p1",
            supported_schema_versions=("2.0",),
            capabilities=(cap,),
            security_access_model="single-user",
        )



def test_decision_rule_expression_shape_is_fail_closed():
    with pytest.raises(ValidationError):
        DecisionExpression(op="PREDICATE")
    with pytest.raises(ValidationError):
        DecisionExpression(op="ALL", children=())


def test_proof_binds_exact_decision_rule():
    _, admission, retry, amendment, _ = base_policies()
    rule = base_decision_rule()
    proof = sealed(
        ProofObligation,
        "proof-rule-bound",
        lifecycle=ProofLifecycle.FROZEN,
        target_claim_id="claim-1",
        proposition="p",
        metric_ids=("accuracy",),
        decision_thresholds={"accuracy": "0.80"},
        decision_rule_ref=rule.exact_ref(),
        evidence_admission_policy_ref=admission.exact_ref(),
        retry_policy_ref=retry.exact_ref(),
        amendment_policy_ref=amendment.exact_ref(),
    )
    assert proof.decision_rule_ref == rule.exact_ref()



def test_runtime_capability_manifest_is_canonical_and_fail_closed():
    manifest = sealed(
        RuntimeCapabilityManifest,
        "runtime-capabilities",
        runtime_id="g2e-standalone",
        runtime_version="0.1",
        runtime_mode=RuntimeMode.STANDALONE,
        authority_mode="single_user",
        persistence_backend="sqlite",
        supported_schema_versions=("1.0",),
        capabilities=(
            RuntimeCapability(
                capability_id="atomic_persistence",
                available=True,
                qualification_refs=("fixture:p3",),
            ),
        ),
        security_assumptions=("local-user-controls-filesystem",),
    )
    assert manifest.runtime_mode == RuntimeMode.STANDALONE
    with pytest.raises(ValidationError, match="capability IDs must be unique"):
        sealed(
            RuntimeCapabilityManifest,
            "runtime-capabilities-bad",
            runtime_id="g2e-standalone",
            runtime_version="0.1",
            runtime_mode=RuntimeMode.STANDALONE,
            authority_mode="single_user",
            persistence_backend="sqlite",
            supported_schema_versions=("1.0",),
            capabilities=(
                RuntimeCapability(capability_id="x", available=True),
                RuntimeCapability(capability_id="x", available=False),
            ),
        )


def test_execution_result_requires_terminal_state():
    retry = sealed(
        ProofRetryPolicy,
        "retry-exec-result",
        max_invalid_replacement_attempts=0,
    )
    _, admission, _, amendment, _ = base_policies()
    rule = base_decision_rule()
    proof = sealed(
        ProofObligation,
        "proof-exec-result",
        lifecycle=ProofLifecycle.FROZEN,
        target_claim_id="claim-1",
        proposition="p",
        metric_ids=("accuracy",),
        decision_thresholds={"accuracy": "0.8"},
        decision_rule_ref=rule.exact_ref(),
        evidence_admission_policy_ref=admission.exact_ref(),
        retry_policy_ref=retry.exact_ref(),
        amendment_policy_ref=amendment.exact_ref(),
    )
    attempt = sealed(
        ExecutionAttemptEnvelope,
        "attempt-exec-result",
        attempt_id="attempt-exec-result",
        proof_ref=proof.exact_ref(),
        state=AttemptState.COMPLETED,
        implementation_ref="fixture@sha",
        config_hash="a" * 64,
        retry_policy_ref=retry.exact_ref(),
    )
    result = sealed(
        ExecutionResult,
        "exec-result",
        attempt_ref=attempt.exact_ref(),
        executor_state=AttemptState.COMPLETED,
        started_at="2026-09-21T07:00:00Z",
        ended_at="2026-09-21T07:00:01Z",
        action_summary="fixture execution",
    )
    assert result.executor_state == AttemptState.COMPLETED
    with pytest.raises(ValidationError, match="terminal executor state"):
        sealed(
            ExecutionResult,
            "exec-result-bad",
            attempt_ref=attempt.exact_ref(),
            executor_state=AttemptState.RUNNING,
            started_at="2026-09-21T07:00:00Z",
            ended_at="2026-09-21T07:00:01Z",
            action_summary="not terminal",
        )


def test_package_manifest_and_seal_are_non_circular_and_safe():
    members = (
        PackageMember(path="A.json", sha256="a" * 64, size=1),
        PackageMember(path="nested/B.json", sha256="b" * 64, size=2),
    )
    manifest = sealed(
        PackageManifest,
        "package-manifest",
        members=members,
    )
    seal = sealed(
        PackageSeal,
        "package-seal",
        manifest_ref=manifest.exact_ref(),
        manifest_file_sha256="c" * 64,
        framework_version="g2e-p1.2",
        runtime_id="g2e-standalone",
        runtime_version="0.1",
    )
    assert seal.manifest_ref == manifest.exact_ref()

    with pytest.raises(ValidationError, match="self-appear"):
        sealed(
            PackageManifest,
            "bad-self-manifest",
            members=(
                PackageMember(
                    path="PACKAGE_MANIFEST.json",
                    sha256="a" * 64,
                    size=1,
                ),
            ),
        )
    with pytest.raises(ValidationError, match="path-sorted"):
        sealed(
            PackageManifest,
            "bad-sort-manifest",
            members=(
                PackageMember(path="Z.json", sha256="a" * 64, size=1),
                PackageMember(path="A.json", sha256="b" * 64, size=1),
            ),
        )
