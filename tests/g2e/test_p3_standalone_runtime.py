from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from g2e import (
    Adjudication,
    AdjudicationVerdict,
    AmendmentPolicy,
    ApplicabilityPolicy,
    AttemptState,
    BackendQualificationStatus,
    Claim,
    ClaimGraph,
    ClaimLifecycle,
    ClaimResolution,
    ClaimResolutionPolicy,
    ClaimSignature,
    DecisionExpression,
    DecisionRule,
    EvidenceAdmissionPolicy,
    EvidenceCapsule,
    EvidenceLifecycle,
    EvidenceRecord,
    ExecutionAttemptEnvelope,
    ExternalReferencePolicy,
    FreshnessState,
    GoalClosureContract,
    GoalContract,
    GoalContractLifecycle,
    GoalExpression,
    GoalRequirement,
    GoalVerdict,
    IndependencePolicy,
    LibraryCapabilityManifest,
    LibraryPublicationContract,
    LibraryQueryContract,
    MetricPredicate,
    PackageExternalReference,
    PackageManifest,
    PackageMember,
    PackageSeal,
    ProofLifecycle,
    ProofObligation,
    ProofResolution,
    ProofResult,
    ProofRetryPolicy,
    ProtectedResource,
    Provenance,
    RuntimeCapabilityManifest,
    RuntimeMode,
    canonical_hash,
)
from g2e.engine import (
    ProofOutcome,
    adjudicate_attempt,
    close_proof,
    evaluate_evidence_admission,
    evaluate_goal,
    materialize_evidence_admission,
    materialize_proof_result,
    resolve_claim,
)
from g2e.standalone import (
    CandidateEvidenceSpec,
    LocalExecutionOutcome,
    ObjectConflictError,
    PackageVerificationError,
    StandaloneRuntime,
    StandaloneRuntimeError,
    UnsupportedCapabilityError,
    export_goal_result_package,
    verify_goal_result_package,
    verify_result_package,
)

P = Provenance(created_by="p3-fixture", created_at="2026-09-21T08:30:00Z")


def sealed(cls, object_id: str, **kwargs):
    return cls.sealed(
        object_id=object_id,
        revision_id="r1",
        provenance=P,
        **kwargs,
    )


def build_program(*, proof_id: str = "proof-1"):
    pass_expr = DecisionExpression(
        op="PREDICATE",
        predicate=MetricPredicate(
            metric_id="score",
            operator="GE",
            threshold_key="pass",
        ),
    )
    fail_expr = DecisionExpression(
        op="PREDICATE",
        predicate=MetricPredicate(
            metric_id="score",
            operator="LT",
            threshold_key="fail",
        ),
    )
    decision_rule = sealed(
        DecisionRule,
        "decision-rule",
        pass_expression=pass_expr,
        fail_expression=fail_expr,
        missing_metric_behavior="INVALID",
    )
    admission = sealed(
        EvidenceAdmissionPolicy,
        "admission-policy",
        accepted_source_classes=("LOCAL", "CAPSULE"),
        require_integrity_hash=True,
        require_attempt_linkage=True,
        allowed_derivation_depth=1,
    )
    retry = sealed(
        ProofRetryPolicy,
        "retry-policy",
        max_invalid_replacement_attempts=1,
    )
    amendment = sealed(AmendmentPolicy, "amendment-policy")
    independence = sealed(IndependencePolicy, "independence-policy")
    resolution_policy = sealed(
        ClaimResolutionPolicy,
        "claim-resolution-policy",
        mode="ALL_REQUIRED",
        proof_ids=(proof_id,),
    )
    requirement = sealed(
        GoalRequirement,
        "req-1",
        statement="fixture score passes frozen threshold",
        hard_constraint=True,
    )
    goal = sealed(
        GoalContract,
        "goal-1",
        lifecycle=GoalContractLifecycle.FROZEN,
        goal_statement="prove standalone bounded fixture",
        requirements=(requirement,),
    )
    claim = sealed(
        Claim,
        "claim-1",
        proposition="fixture score satisfies threshold",
        claim_class="technical",
        resolution_policy_ref=resolution_policy.exact_ref(),
        goal_requirement_ids=(requirement.object_id,),
        lifecycle=ClaimLifecycle.READY,
        resolution=ClaimResolution.UNKNOWN,
    )
    graph = sealed(
        ClaimGraph,
        "claim-graph",
        goal_contract_ref=goal.exact_ref(),
        claims=(claim,),
        coverage_statement="fixture requirement covered",
    )
    closure = sealed(
        GoalClosureContract,
        "goal-closure",
        goal_contract_ref=goal.exact_ref(),
        claim_graph_ref=graph.exact_ref(),
        requirement_claim_map={requirement.object_id: (claim.object_id,)},
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
    proof = sealed(
        ProofObligation,
        proof_id,
        lifecycle=ProofLifecycle.FROZEN,
        target_claim_id=claim.object_id,
        proposition=claim.proposition,
        metric_ids=("score",),
        decision_thresholds={"pass": "0.80", "fail": "0.70"},
        decision_rule_ref=decision_rule.exact_ref(),
        evidence_admission_policy_ref=admission.exact_ref(),
        retry_policy_ref=retry.exact_ref(),
        amendment_policy_ref=amendment.exact_ref(),
        independence_policy_ref=independence.exact_ref(),
    )
    attempt = sealed(
        ExecutionAttemptEnvelope,
        "attempt-envelope",
        attempt_id="attempt-1",
        proof_ref=proof.exact_ref(),
        state=AttemptState.CREATED,
        implementation_ref="fixture@sha",
        config_hash="a" * 64,
        retry_policy_ref=retry.exact_ref(),
    )
    return {
        "decision_rule": decision_rule,
        "admission": admission,
        "retry": retry,
        "amendment": amendment,
        "independence": independence,
        "resolution_policy": resolution_policy,
        "requirement": requirement,
        "goal": goal,
        "claim": claim,
        "graph": graph,
        "closure": closure,
        "proof": proof,
        "attempt": attempt,
    }


def revise_attempt(attempt, state: AttemptState, revision: str):
    data = attempt.model_dump(mode="python", exclude={"content_hash"})
    data.update({"revision_id": revision, "state": state, "provenance": P})
    return ExecutionAttemptEnvelope.sealed(**data)


def execute_and_adjudicate(runtime: StandaloneRuntime, program, score="0.90"):
    report = runtime.executor.execute(
        program["attempt"],
        lambda: LocalExecutionOutcome(
            action_summary="emit deterministic fixture metric",
            evidence=(
                CandidateEvidenceSpec(
                    source_class="LOCAL",
                    payload={"metrics": {"score": score}},
                    object_id="fixture-evidence",
                ),
            ),
        ),
        provenance=P,
    )
    candidate = report.candidate_evidence[0]
    decision = evaluate_evidence_admission(candidate, program["admission"])
    admitted = materialize_evidence_admission(
        candidate,
        program["admission"],
        decision,
        revision_id="admitted-r1",
        provenance=P,
    )
    runtime.store.put(admitted)
    runtime.store.put_evidence_payload(
        admitted, report.evidence_payloads[candidate.object_id]
    )
    payload = runtime.store.load_evidence_payload(admitted)
    adjudication = adjudicate_attempt(
        program["proof"],
        program["decision_rule"],
        program["admission"],
        report.final_attempt,
        (admitted,),
        {admitted.object_id: payload},
        object_id="adjudication-1",
        revision_id="r1",
        provenance=P,
        independence_satisfied=True,
    )
    runtime.store.record_adjudication(adjudication)
    proof_result = materialize_proof_result(
        program["proof"],
        program["retry"],
        (adjudication,),
        invalid_attempt_count=0,
        object_id=f"proof-result-{program['proof'].object_id}",
        revision_id="r1",
        provenance=P,
    )
    runtime.store.put(proof_result)
    return report, admitted, adjudication, proof_result


def qualified_library_manifest(runtime: StandaloneRuntime):
    return runtime.library.capability_manifest(
        provenance=P,
        qualification_status=BackendQualificationStatus.QUALIFIED,
        evidence_refs=("fixture:p3",),
    )


def build_source_package(
    runtime: StandaloneRuntime,
    tmp_path: Path,
    *,
    resolution: ClaimResolution,
    suffix: str,
):
    program = build_program(proof_id=f"proof-{suffix}")
    score = "0.90" if resolution == ClaimResolution.PASS else "0.60"
    report, admitted, adjudication, proof_result = execute_and_adjudicate(
        runtime, program, score=score
    )
    package_dir = tmp_path / f"source-package-{suffix}"
    verification = export_goal_result_package(
        package_dir,
        goal=program["goal"],
        goal_closure=program["closure"],
        claim_graph=program["graph"],
        proofs=(program["proof"],),
        proof_results=(proof_result,),
        proof_dependencies=(
            program["decision_rule"],
            program["admission"],
            program["retry"],
            program["amendment"],
            program["independence"],
            program["resolution_policy"],
        ),
        evidence=(admitted,),
        adjudications=(adjudication,),
        reproducibility_manifest={
            "decision_rule_hash": program["decision_rule"].content_hash,
        },
        package_lineage=runtime.store.events(),
        provenance=P,
    )
    return program, package_dir, verification


def make_capsule(
    program,
    verification,
    *,
    object_id="capsule-1",
    resolution=ClaimResolution.FAIL,
    ancestors=(),
):
    signature = sealed(
        ClaimSignature,
        f"signature-{object_id}",
        proposition_family="fixture",
        subject_population="standalone",
        outcome_metric="score",
    )
    capsule = sealed(
        EvidenceCapsule,
        object_id,
        source_package_type="GOAL_RESULT",
        source_package_ref=verification.seal.object_id,
        source_package_seal_hash=verification.seal.content_hash,
        source_goal_ref=program["goal"].exact_ref(),
        source_claim_ref=program["claim"].exact_ref(),
        source_claim_resolution=resolution,
        claim_signature_ref=signature.exact_ref(),
        provenance_ancestor_refs=tuple(ancestors),
        capsule_policy_version="1",
    )
    contract = sealed(
        LibraryPublicationContract,
        f"publication-{object_id}",
        subject_ref=capsule.exact_ref(),
        source_package_type="GOAL_RESULT",
        source_package_seal_hash=capsule.source_package_seal_hash,
        publication_scope="PROJECT",
        metadata_namespace="g2e.fixture",
        metadata_schema_version="1",
    )
    return capsule, contract

def test_canonical_object_round_trip_survives_restart(tmp_path):
    runtime = StandaloneRuntime(tmp_path)
    program = build_program()
    runtime.store.put(program["proof"])

    reopened = StandaloneRuntime(tmp_path)
    loaded = reopened.store.load_ref(program["proof"].exact_ref())
    assert loaded == program["proof"]
    assert loaded.decision_rule_ref == program["decision_rule"].exact_ref()


def test_atomic_put_many_rolls_back_on_conflict(tmp_path):
    runtime = StandaloneRuntime(tmp_path)
    g1 = sealed(
        GoalContract,
        "same-goal",
        lifecycle=GoalContractLifecycle.FROZEN,
        goal_statement="one",
    )
    g2 = GoalContract.sealed(
        object_id="same-goal",
        revision_id="r1",
        provenance=P,
        lifecycle=GoalContractLifecycle.FROZEN,
        goal_statement="two",
    )
    with pytest.raises(ObjectConflictError):
        runtime.store.put_many((g1, g2))
    assert runtime.store.object_count() == 0


def test_attempt_ledger_rejects_illegal_transition_and_assignment_mutation(tmp_path):
    runtime = StandaloneRuntime(tmp_path)
    program = build_program()
    runtime.store.persist_attempt(program["attempt"])

    running = revise_attempt(program["attempt"], AttemptState.RUNNING, "r2")
    with pytest.raises(StandaloneRuntimeError, match="illegal attempt transition"):
        runtime.store.persist_attempt(running)

    mutated = ExecutionAttemptEnvelope.sealed(
        **{
            **program["attempt"].model_dump(mode="python", exclude={"content_hash"}),
            "revision_id": "r3",
            "state": AttemptState.PREFLIGHT,
            "implementation_ref": "different@sha",
        }
    )
    with pytest.raises(StandaloneRuntimeError, match="assignment changed"):
        runtime.store.persist_attempt(mutated)


def test_local_executor_success_produces_attempt_bound_candidate(tmp_path):
    runtime = StandaloneRuntime(tmp_path)
    program = build_program()
    report = runtime.executor.execute(
        program["attempt"],
        lambda: LocalExecutionOutcome(
            action_summary="fixture",
            evidence=(
                CandidateEvidenceSpec(
                    source_class="LOCAL",
                    payload={"metrics": {"score": "0.90"}},
                ),
            ),
        ),
        provenance=P,
    )
    assert report.final_attempt.state == AttemptState.COMPLETED
    assert report.execution_result.executor_state == AttemptState.COMPLETED
    assert len(report.candidate_evidence) == 1
    candidate = report.candidate_evidence[0]
    assert candidate.producer_attempt_ref == report.final_attempt.exact_ref()
    assert runtime.store.load_evidence_payload(candidate) == {
        "metrics": {"score": "0.90"}
    }


def test_local_executor_failure_is_executor_state_not_scientific_fail(tmp_path):
    runtime = StandaloneRuntime(tmp_path)
    program = build_program()

    def boom():
        raise RuntimeError("fixture infrastructure failure")

    report = runtime.executor.execute(program["attempt"], boom, provenance=P)
    assert report.final_attempt.state == AttemptState.EXECUTOR_FAILED
    assert report.execution_result.executor_state == AttemptState.EXECUTOR_FAILED
    assert report.execution_result.technical_error_class == "RuntimeError"
    assert report.candidate_evidence == ()


def test_protected_resource_recovery_fails_closed_and_preempts_attempt(tmp_path):
    runtime = StandaloneRuntime(tmp_path)
    program = build_program()
    resource = sealed(
        ProtectedResource,
        "protected-1",
        resource_type="confirmatory-cohort",
        identity_ref="cohort:42",
        freshness_state=FreshnessState.FRESH,
        reuse_allowed=False,
    )
    runtime.store.persist_protected_resource(resource)
    runtime.store.persist_attempt(program["attempt"])
    preflight = revise_attempt(program["attempt"], AttemptState.PREFLIGHT, "r2")
    locked = revise_attempt(preflight, AttemptState.LOCKED, "r3")
    running = revise_attempt(locked, AttemptState.RUNNING, "r4")
    runtime.store.persist_attempt(preflight)
    runtime.store.persist_attempt(locked)
    runtime.store.reserve_resource_for_attempt(
        resource.object_id,
        locked.attempt_id,
        provenance=P,
        revision_id="reserved-r1",
    )
    runtime.store.persist_attempt(running)

    reopened = StandaloneRuntime(tmp_path)
    report = reopened.recover(provenance=P)
    assert report.exposed_resources == ("protected-1",)
    assert report.preempted_attempts == ("attempt-1",)
    assert (
        reopened.store.current_protected_resource("protected-1").freshness_state
        == FreshnessState.EXPOSED
    )
    assert reopened.store.current_attempt("attempt-1").state == AttemptState.PREEMPTED


def test_terminal_adjudication_is_immutable_across_restart(tmp_path):
    runtime = StandaloneRuntime(tmp_path)
    program = build_program()
    report, admitted, adjudication, proof_result = execute_and_adjudicate(runtime, program)

    reopened = StandaloneRuntime(tmp_path)
    loaded = reopened.store.load_adjudication(report.final_attempt.attempt_id)
    assert loaded == adjudication

    replacement = Adjudication.sealed(
        object_id="adjudication-rewrite",
        revision_id="r1",
        provenance=P,
        proof_ref=program["proof"].exact_ref(),
        attempt_ref=report.final_attempt.exact_ref(),
        admitted_evidence_refs=(admitted.exact_ref(),),
        decision_rule_hash=program["decision_rule"].content_hash,
        adjudicator_version="malicious-rewrite",
        verdict=AdjudicationVerdict.FAIL,
        reason_codes=("REWRITE",),
    )
    with pytest.raises(StandaloneRuntimeError, match="terminal adjudication"):
        reopened.store.record_adjudication(replacement)


def test_runtime_capability_manifest_fails_closed_for_missing_governance(tmp_path):
    runtime = StandaloneRuntime(tmp_path)
    manifest = runtime.capability_manifest(
        provenance=P, qualification_refs=("fixture:p3",)
    )
    assert manifest.runtime_mode == RuntimeMode.STANDALONE
    runtime.require_capabilities(manifest, ("atomic_persistence", "result_package"))
    with pytest.raises(UnsupportedCapabilityError, match="separation_of_duty"):
        runtime.require_capabilities(manifest, ("separation_of_duty",))


def test_library_publishes_negative_results_and_queries_exactly(tmp_path):
    runtime = StandaloneRuntime(tmp_path)
    program, package_dir, verification = build_source_package(
        runtime, tmp_path, resolution=ClaimResolution.FAIL, suffix="negative"
    )
    capsule, contract = make_capsule(
        program, verification, resolution=ClaimResolution.FAIL
    )
    manifest = qualified_library_manifest(runtime)
    publication_id = runtime.library.publish_capsule(
        capsule,
        contract,
        {"domain": "fixture", "result": "negative"},
        capability_manifest=manifest,
        source_package_dir=package_dir,
    )
    assert runtime.library.resolve_subject(
        publication_id, capability_manifest=manifest
    ) == capsule
    assert runtime.library.verify_subject_integrity(
        capsule.exact_ref(), capability_manifest=manifest
    )

    query = sealed(
        LibraryQueryContract,
        "query-negative",
        query_payload={
            "subject_type": "evidence_capsule",
            "source_claim_resolution": "FAIL",
            "metadata": {"domain": "fixture"},
        },
        required_capability_ids=("query",),
        access_scope=("PROJECT",),
    )
    execution = runtime.library.query_candidates(
        query, provenance=P, capability_manifest=manifest
    )
    assert execution.status.value == "SUCCEEDED"
    assert execution.complete
    assert execution.result_publication_ids == (publication_id,)
    assert execution.result_subject_refs == (capsule.exact_ref(),)


def test_library_zero_results_is_distinct_from_query_failure(tmp_path):
    runtime = StandaloneRuntime(tmp_path)
    program, package_dir, verification = build_source_package(
        runtime, tmp_path, resolution=ClaimResolution.FAIL, suffix="zero"
    )
    capsule, contract = make_capsule(
        program, verification, resolution=ClaimResolution.FAIL
    )
    manifest = qualified_library_manifest(runtime)
    runtime.library.publish_capsule(
        capsule,
        contract,
        {"domain": "fixture"},
        capability_manifest=manifest,
        source_package_dir=package_dir,
    )

    zero_query = sealed(
        LibraryQueryContract,
        "query-zero",
        query_payload={"source_claim_resolution": "PASS"},
        required_capability_ids=("query",),
        access_scope=("PROJECT",),
    )
    zero = runtime.library.query_candidates(
        zero_query, provenance=P, capability_manifest=manifest
    )
    assert zero.status.value == "SUCCEEDED"
    assert zero.complete is True
    assert zero.result_subject_refs == ()

    bad_query = sealed(
        LibraryQueryContract,
        "query-bad",
        query_payload={"unsupported_filter": "x"},
        required_capability_ids=("query",),
        access_scope=("PROJECT",),
    )
    failed = runtime.library.query_candidates(
        bad_query, provenance=P, capability_manifest=manifest
    )
    assert failed.status.value == "FAILED"
    assert failed.complete is False
    assert failed.result_subject_refs == ()
    assert failed.reason.startswith("QUERY_FAILED:")


def test_library_snapshot_replay_survives_withdrawal(tmp_path):
    runtime = StandaloneRuntime(tmp_path)
    program, package_dir, verification = build_source_package(
        runtime, tmp_path, resolution=ClaimResolution.FAIL, suffix="replay"
    )
    capsule, contract = make_capsule(
        program, verification, resolution=ClaimResolution.FAIL
    )
    manifest = qualified_library_manifest(runtime)
    publication_id = runtime.library.publish_capsule(
        capsule,
        contract,
        {"domain": "fixture"},
        capability_manifest=manifest,
        source_package_dir=package_dir,
    )
    query = sealed(
        LibraryQueryContract,
        "query-replay",
        query_payload={"object_id": capsule.object_id},
        required_capability_ids=("query", "snapshot"),
        access_scope=("PROJECT",),
    )
    first = runtime.library.query_candidates(
        query, provenance=P, capability_manifest=manifest
    )
    assert first.result_subject_refs == (capsule.exact_ref(),)

    runtime.library.withdraw_publication(
        publication_id,
        "fixture withdrawal",
        capability_manifest=manifest,
    )
    current = runtime.library.query_candidates(
        query,
        provenance=P,
        execution_id="query-current",
        capability_manifest=manifest,
    )
    assert current.result_subject_refs == ()

    replay = runtime.library.replay_query(
        first, query, provenance=P, capability_manifest=manifest
    )
    assert replay.status.value == "SUCCEEDED"
    assert replay.complete
    assert replay.snapshot_ref == first.snapshot_ref
    assert replay.result_subject_refs == first.result_subject_refs


def test_library_provenance_and_capability_qualification(tmp_path):
    runtime = StandaloneRuntime(tmp_path)
    ancestor = sealed(
        EvidenceRecord,
        "ancestor",
        source_class="LOCAL",
        lifecycle=EvidenceLifecycle.ADMITTED,
        payload_digest="a" * 64,
    ).exact_ref()
    program, package_dir, verification = build_source_package(
        runtime, tmp_path, resolution=ClaimResolution.FAIL, suffix="provenance"
    )
    capsule, contract = make_capsule(
        program,
        verification,
        resolution=ClaimResolution.FAIL,
        ancestors=(ancestor,),
    )
    manifest = qualified_library_manifest(runtime)
    runtime.library.publish_capsule(
        capsule,
        contract,
        {},
        capability_manifest=manifest,
        source_package_dir=package_dir,
    )
    assert runtime.library.get_provenance_ancestors(
        capsule.exact_ref(), capability_manifest=manifest
    ) == (ancestor,)

    unqualified = runtime.library.capability_manifest(provenance=P)
    with pytest.raises(UnsupportedCapabilityError):
        runtime.library.require_capability(unqualified, "query")
    qualified = runtime.library.capability_manifest(
        provenance=P,
        qualification_status=BackendQualificationStatus.QUALIFIED,
        evidence_refs=("fixture:p3",),
    )
    runtime.library.require_capability(qualified, "query")
    assert qualified.silent_fallback_allowed is False


def test_result_package_seal_detects_mutation_and_unclassified_files(tmp_path):
    runtime = StandaloneRuntime(tmp_path / "runtime")
    program = build_program()
    report, admitted, adjudication, proof_result = execute_and_adjudicate(runtime, program)
    proof_closure = close_proof(
        adjudication, program["retry"], invalid_attempts_including_current=0
    )
    claim_resolution = resolve_claim(
        program["resolution_policy"], {program["proof"].object_id: proof_closure.outcome}
    )
    assert claim_resolution == ClaimResolution.PASS

    package_dir = tmp_path / "goal-result"
    verification = export_goal_result_package(
        package_dir,
        goal=program["goal"],
        goal_closure=program["closure"],
        claim_graph=program["graph"],
        proofs=(program["proof"],),
        proof_results=(proof_result,),
        proof_dependencies=(
            program["decision_rule"],
            program["admission"],
            program["retry"],
            program["amendment"],
            program["independence"],
            program["resolution_policy"],
        ),
        evidence=(admitted,),
        adjudications=(adjudication,),
        reproducibility_manifest={
            "decision_rule_ref": program["decision_rule"].exact_ref().model_dump(mode="json"),
            "proof_ref": program["proof"].exact_ref().model_dump(mode="json"),
        },
        package_lineage=runtime.store.events(),
        provenance=P,
    )
    assert verification.member_count > 5
    assert (
        json.loads((package_dir / "FINAL_VERDICT.json").read_text())["verdict"]
        == GoalVerdict.ACHIEVED.value
    )
    proof_graph = json.loads((package_dir / "PROOF_GRAPH.json").read_text())
    dependencies = {
        item["payload"]["object_id"]: item for item in proof_graph["dependencies"]
    }
    assert dependencies[program["decision_rule"].object_id]["schema_kind"] == "decision_rule"
    assert dependencies[program["decision_rule"].object_id]["payload"]["content_hash"] == program[
        "decision_rule"
    ].content_hash

    (package_dir / "GOAL.json").write_text("{}", encoding="utf-8")
    with pytest.raises(PackageVerificationError, match="(size|hash) mismatch"):
        verify_goal_result_package(package_dir)


def test_result_package_rejects_unclassified_extra_file(tmp_path):
    runtime = StandaloneRuntime(tmp_path / "runtime")
    program = build_program()
    report, admitted, adjudication, proof_result = execute_and_adjudicate(runtime, program)
    package_dir = tmp_path / "goal-result"
    export_goal_result_package(
        package_dir,
        goal=program["goal"],
        goal_closure=program["closure"],
        claim_graph=program["graph"],
        proofs=(program["proof"],),
        proof_results=(proof_result,),
        proof_dependencies=(program["decision_rule"], program["retry"], program["resolution_policy"]),
        evidence=(admitted,),
        adjudications=(adjudication,),
        reproducibility_manifest={},
        package_lineage=(),
        provenance=P,
    )
    (package_dir / "UNCLASSIFIED.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(PackageVerificationError, match="unclassified"):
        verify_goal_result_package(package_dir)


def test_external_reference_resolution_policy_is_enforced(tmp_path):
    runtime = StandaloneRuntime(tmp_path / "runtime")
    program = build_program()
    report, admitted, adjudication, proof_result = execute_and_adjudicate(runtime, program)
    external_bytes = b"immutable external artifact"
    external = PackageExternalReference(
        ref_id="artifact",
        immutable_locator="fixture://artifact",
        expected_sha256=hashlib.sha256(external_bytes).hexdigest(),
        required_online_resolution=True,
    )
    package_dir = tmp_path / "goal-result"
    export_goal_result_package(
        package_dir,
        goal=program["goal"],
        goal_closure=program["closure"],
        claim_graph=program["graph"],
        proofs=(program["proof"],),
        proof_results=(proof_result,),
        proof_dependencies=(program["decision_rule"], program["retry"], program["resolution_policy"]),
        evidence=(admitted,),
        adjudications=(adjudication,),
        reproducibility_manifest={},
        package_lineage=(),
        provenance=P,
        external_reference_policy=ExternalReferencePolicy.REQUIRE_RESOLUTION,
        external_references=(external,),
        external_resolver=lambda ref: external_bytes,
    )
    with pytest.raises(PackageVerificationError, match="resolver required"):
        verify_goal_result_package(package_dir)
    assert verify_goal_result_package(
        package_dir, external_resolver=lambda ref: external_bytes
    ).seal.runtime_id == "g2e-standalone"
    with pytest.raises(PackageVerificationError, match="hash mismatch"):
        verify_goal_result_package(
            package_dir, external_resolver=lambda ref: b"tampered"
        )


def test_complete_bounded_program_runs_without_gwf_and_preserves_decision_rule(tmp_path):
    runtime = StandaloneRuntime(tmp_path / "runtime")
    program = build_program()

    runtime.store.put_many(
        (
            program["decision_rule"],
            program["admission"],
            program["retry"],
            program["amendment"],
            program["independence"],
            program["goal"],
            program["claim"],
            program["graph"],
            program["closure"],
            program["proof"],
        )
    )
    report, admitted, adjudication, proof_result = execute_and_adjudicate(runtime, program)
    closure = close_proof(
        adjudication, program["retry"], invalid_attempts_including_current=0
    )
    assert closure.outcome == ProofOutcome.PASS
    claim_resolution = resolve_claim(
        program["resolution_policy"],
        {program["proof"].object_id: closure.outcome},
    )
    goal_verdict = evaluate_goal(
        program["closure"],
        {program["claim"].object_id: claim_resolution},
        can_progress=False,
    )
    assert goal_verdict == GoalVerdict.ACHIEVED

    reopened = StandaloneRuntime(tmp_path / "runtime")
    loaded_proof = reopened.store.load_ref(program["proof"].exact_ref())
    loaded_rule = reopened.store.load_ref(program["decision_rule"].exact_ref())
    loaded_adj = reopened.store.load_adjudication(report.final_attempt.attempt_id)
    assert loaded_proof.decision_rule_ref == loaded_rule.exact_ref()
    assert loaded_adj.decision_rule_hash == loaded_rule.content_hash

    package_dir = tmp_path / "sealed-result"
    export_goal_result_package(
        package_dir,
        goal=program["goal"],
        goal_closure=program["closure"],
        claim_graph=program["graph"],
        proofs=(loaded_proof,),
        proof_results=(proof_result,),
        proof_dependencies=(
            loaded_rule,
            program["admission"],
            program["retry"],
            program["amendment"],
            program["independence"],
            program["resolution_policy"],
        ),
        evidence=(admitted,),
        adjudications=(loaded_adj,),
        reproducibility_manifest={
            "decision_rule_hash": loaded_rule.content_hash,
            "qualified_core": "c2fc03a7470b835904252246421e1b8d9a1ec5ef",
        },
        package_lineage=reopened.store.events(),
        provenance=P,
    )
    verified = verify_goal_result_package(package_dir)
    assert verified.seal.manifest_ref == verified.manifest.exact_ref()



def test_library_publish_requires_qualified_capability_and_verified_source(tmp_path):
    runtime = StandaloneRuntime(tmp_path / "runtime")
    program, package_dir, verification = build_source_package(
        runtime, tmp_path, resolution=ClaimResolution.FAIL, suffix="verify-source"
    )
    capsule, contract = make_capsule(
        program, verification, resolution=ClaimResolution.FAIL
    )
    unqualified = runtime.library.capability_manifest(provenance=P)
    with pytest.raises(UnsupportedCapabilityError):
        runtime.library.publish_capsule(
            capsule,
            contract,
            {},
            capability_manifest=unqualified,
            source_package_dir=package_dir,
        )

    qualified = qualified_library_manifest(runtime)
    forged = EvidenceCapsule.sealed(
        **{
            **capsule.model_dump(mode="python", exclude={"content_hash"}),
            "revision_id": "forged",
            "source_package_seal_hash": "f" * 64,
        }
    )
    forged_contract = LibraryPublicationContract.sealed(
        **{
            **contract.model_dump(mode="python", exclude={"content_hash"}),
            "revision_id": "forged",
            "subject_ref": forged.exact_ref(),
            "source_package_seal_hash": forged.source_package_seal_hash,
        }
    )
    with pytest.raises(StandaloneRuntimeError, match="verified source package seal"):
        runtime.library.publish_capsule(
            forged,
            forged_contract,
            {},
            capability_manifest=qualified,
            source_package_dir=package_dir,
        )


def test_result_package_derives_fail_from_proof_result_not_caller_claim(tmp_path):
    runtime = StandaloneRuntime(tmp_path / "runtime")
    program = build_program()
    report, admitted, adjudication, proof_result = execute_and_adjudicate(
        runtime, program, score="0.60"
    )
    assert proof_result.outcome.value == "FAIL"
    package_dir = tmp_path / "derived-fail"
    export_goal_result_package(
        package_dir,
        goal=program["goal"],
        goal_closure=program["closure"],
        claim_graph=program["graph"],
        proofs=(program["proof"],),
        proof_results=(proof_result,),
        proof_dependencies=(
            program["decision_rule"],
            program["admission"],
            program["retry"],
            program["amendment"],
            program["independence"],
            program["resolution_policy"],
        ),
        evidence=(admitted,),
        adjudications=(adjudication,),
        reproducibility_manifest={},
        package_lineage=runtime.store.events(),
        provenance=P,
    )
    final = json.loads((package_dir / "FINAL_VERDICT.json").read_text())
    assert final["verdict"] == GoalVerdict.FALSIFIED.value
    claim_resolution = json.loads(
        (package_dir / "claims" / "claim-1" / "RESOLUTION.json").read_text()
    )
    assert claim_resolution["resolution"] == ClaimResolution.FAIL.value



def test_package_rejects_forged_proof_result_not_backed_by_decision_ledger(tmp_path):
    runtime = StandaloneRuntime(tmp_path / "runtime")
    program = build_program()
    report, admitted, adjudication, proof_result = execute_and_adjudicate(
        runtime, program, score="0.60"
    )
    forged = ProofResult.sealed(
        **{
            **proof_result.model_dump(mode="python", exclude={"content_hash"}),
            "revision_id": "forged-pass",
            "outcome": ProofResolution.PASS,
        }
    )
    with pytest.raises(StandaloneRuntimeError, match="deterministic P2 closure replay"):
        export_goal_result_package(
            tmp_path / "forged-package",
            goal=program["goal"],
            goal_closure=program["closure"],
            claim_graph=program["graph"],
            proofs=(program["proof"],),
            proof_results=(forged,),
            proof_dependencies=(
                program["decision_rule"],
                program["admission"],
                program["retry"],
                program["amendment"],
                program["independence"],
                program["resolution_policy"],
            ),
            evidence=(admitted,),
            adjudications=(adjudication,),
            reproducibility_manifest={},
            package_lineage=runtime.store.events(),
            provenance=P,
        )


def test_standalone_library_rejects_foreign_capability_manifest(tmp_path):
    runtime = StandaloneRuntime(tmp_path)
    qualified = qualified_library_manifest(runtime)
    foreign = LibraryCapabilityManifest.sealed(
        **{
            **qualified.model_dump(mode="python", exclude={"content_hash"}),
            "revision_id": "foreign",
            "backend_id": "foreign-library",
        }
    )
    with pytest.raises(UnsupportedCapabilityError, match="BACKEND_IDENTITY_MISMATCH"):
        runtime.library.require_capability(foreign, "query")


def test_standalone_runtime_rejects_foreign_runtime_manifest(tmp_path):
    runtime = StandaloneRuntime(tmp_path)
    manifest = runtime.capability_manifest(
        provenance=P, qualification_refs=("fixture:p3",)
    )
    foreign = RuntimeCapabilityManifest.sealed(
        **{
            **manifest.model_dump(mode="python", exclude={"content_hash"}),
            "revision_id": "foreign",
            "runtime_id": "foreign-runtime",
        }
    )
    with pytest.raises(UnsupportedCapabilityError, match="RUNTIME_IDENTITY_MISMATCH"):
        runtime.require_capabilities(foreign, ("atomic_persistence",))


def test_library_publication_rejects_capsule_resolution_mismatch_with_sealed_source(tmp_path):
    runtime = StandaloneRuntime(tmp_path / "runtime")
    program, package_dir, verification = build_source_package(
        runtime, tmp_path, resolution=ClaimResolution.FAIL, suffix="mismatch"
    )
    capsule, contract = make_capsule(
        program, verification, resolution=ClaimResolution.PASS
    )
    manifest = qualified_library_manifest(runtime)
    with pytest.raises(StandaloneRuntimeError, match="resolution does not match"):
        runtime.library.publish_capsule(
            capsule,
            contract,
            {},
            capability_manifest=manifest,
            source_package_dir=package_dir,
        )


def test_library_publication_rejects_nonterminal_source_claim_resolution(tmp_path):
    runtime = StandaloneRuntime(tmp_path / "runtime")
    program, package_dir, verification = build_source_package(
        runtime, tmp_path, resolution=ClaimResolution.FAIL, suffix="unknown"
    )
    capsule, contract = make_capsule(
        program, verification, resolution=ClaimResolution.UNKNOWN
    )
    manifest = qualified_library_manifest(runtime)
    with pytest.raises(StandaloneRuntimeError, match="must be terminal"):
        runtime.library.publish_capsule(
            capsule,
            contract,
            {},
            capability_manifest=manifest,
            source_package_dir=package_dir,
        )



def _reseal_package(package_dir: Path, *, revision_suffix: str = "tampered"):
    old_manifest = PackageManifest.parse_authoritative(
        json.loads((package_dir / "PACKAGE_MANIFEST.json").read_text())
    )
    old_seal = PackageSeal.parse_authoritative(
        json.loads((package_dir / "PACKAGE_SEAL.json").read_text())
    )
    members = tuple(
        PackageMember(
            path=member.path,
            sha256=hashlib.sha256((package_dir / member.path).read_bytes()).hexdigest(),
            size=len((package_dir / member.path).read_bytes()),
        )
        for member in old_manifest.members
    )
    manifest = PackageManifest.sealed(
        object_id=old_manifest.object_id,
        revision_id=revision_suffix + "-manifest",
        provenance=P,
        members=members,
        external_reference_policy=old_manifest.external_reference_policy,
        external_references=old_manifest.external_references,
        non_authoritative_paths=old_manifest.non_authoritative_paths,
    )
    manifest_bytes = canonical_json(manifest.model_dump(mode="json")).encode("utf-8")
    (package_dir / "PACKAGE_MANIFEST.json").write_bytes(manifest_bytes)
    seal = PackageSeal.sealed(
        object_id=old_seal.object_id,
        revision_id=revision_suffix + "-seal",
        provenance=P,
        package_type=old_seal.package_type,
        manifest_ref=manifest.exact_ref(),
        manifest_file_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        framework_version=old_seal.framework_version,
        runtime_id=old_seal.runtime_id,
        runtime_version=old_seal.runtime_version,
        attestation_identity=old_seal.attestation_identity,
    )
    (package_dir / "PACKAGE_SEAL.json").write_text(
        canonical_json(seal.model_dump(mode="json")), encoding="utf-8"
    )
    return manifest, seal


def test_semantic_verifier_rejects_resealed_false_goal_verdict(tmp_path):
    runtime = StandaloneRuntime(tmp_path / "runtime")
    program, package_dir, _ = build_source_package(
        runtime, tmp_path, resolution=ClaimResolution.FAIL, suffix="semantic-reseal"
    )
    final_path = package_dir / "FINAL_VERDICT.json"
    final_doc = json.loads(final_path.read_text())
    assert final_doc["verdict"] == GoalVerdict.FALSIFIED.value
    final_doc["verdict"] = GoalVerdict.ACHIEVED.value
    final_path.write_text(canonical_json(final_doc), encoding="utf-8")
    _reseal_package(package_dir)

    # Cryptographic/integrity verification alone now succeeds.
    assert verify_result_package(package_dir).seal.package_type == "GOAL_RESULT"
    # Formal G2E semantics must still fail.
    with pytest.raises(
        PackageVerificationError,
        match="FINAL_VERDICT does not match deterministic Goal replay",
    ):
        verify_goal_result_package(package_dir)


def test_library_publication_uses_semantic_source_verifier(tmp_path):
    runtime = StandaloneRuntime(tmp_path / "runtime")
    program, package_dir, verification = build_source_package(
        runtime, tmp_path, resolution=ClaimResolution.FAIL, suffix="semantic-publish"
    )
    capsule, contract = make_capsule(
        program, verification, resolution=ClaimResolution.FAIL
    )
    final_path = package_dir / "FINAL_VERDICT.json"
    final_doc = json.loads(final_path.read_text())
    final_doc["verdict"] = GoalVerdict.ACHIEVED.value
    final_path.write_text(canonical_json(final_doc), encoding="utf-8")
    _reseal_package(package_dir, revision_suffix="publish-tampered")

    manifest = qualified_library_manifest(runtime)
    with pytest.raises(PackageVerificationError, match="deterministic Goal replay"):
        runtime.library.publish_capsule(
            capsule,
            contract,
            {},
            capability_manifest=manifest,
            source_package_dir=package_dir,
        )
