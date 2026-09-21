from __future__ import annotations

from pathlib import Path

import pytest

from gwr.errors import AuthorityDenied
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import parse_json

from g2e import (
    AdjudicationVerdict,
    AmendmentPolicy,
    AttemptState,
    Claim,
    ClaimGraph,
    ClaimLifecycle,
    ClaimResolution,
    ClaimResolutionPolicy,
    DecisionExpression,
    DecisionRule,
    EvidenceAdmissionPolicy,
    EvidenceLifecycle,
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
)
from g2e.canonical import ExactRef
from g2e.engine import (
    CoreInvariantError,
    ProofOutcome,
    adjudicate_attempt,
    evaluate_evidence_admission,
    evaluate_goal,
    materialize_evidence_admission,
    materialize_proof_result,
    resolve_claim,
    transition_protected_resource,
)
from g2e.gwf_adapter import (
    GWF_ADAPTER_MAPPING_VERSION,
    GWF_RUNTIME_ID,
    GWF_RUNTIME_VERSION,
    GWFCandidateEvidenceSpec,
    GWFAdapter,
    GWFExecutionOutcome,
    GWFMappingConflictError,
    GWFMappingRef,
    UnsupportedGWFMappingVersion,
)
from g2e.gwf_domain import g2e_gwf_domain
from g2e.standalone import (
    CandidateEvidenceSpec,
    LocalExecutionOutcome,
    StandaloneRuntime,
    export_goal_result_package,
    verify_goal_result_package,
)


P = Provenance(created_by="p4-fixture", created_at="2026-09-21T09:30:00Z")


def sealed(cls, object_id: str, **kwargs):
    return cls.sealed(
        object_id=object_id,
        revision_id="r1",
        provenance=P,
        **kwargs,
    )


def make_adapter(tmp_path: Path):
    runtime = GovernedWorkflowRuntime(
        g2e_gwf_domain(),
        db_path=str(tmp_path / "gwf.sqlite"),
    )
    project_id = runtime.create_project("g2e-p4")
    return runtime, project_id, GWFAdapter(runtime, project_id)


def build_program(*, protected: bool = False):
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
        accepted_source_classes=("LOCAL",),
        require_integrity_hash=True,
        require_attempt_linkage=True,
        allowed_derivation_depth=0,
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
        proof_ids=("proof-1",),
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
        goal_statement="prove GWF parity for one bounded fixture",
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

    resource = None
    protected_refs = ()
    if protected:
        resource = sealed(
            ProtectedResource,
            "protected-1",
            resource_type="frozen-fixture",
            identity_ref="fixture@sha256:abc",
            freshness_state=FreshnessState.FRESH,
            protected=True,
            reuse_allowed=False,
        )
        protected_refs = (resource.exact_ref(),)

    proof = sealed(
        ProofObligation,
        "proof-1",
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
        protected_resource_refs=protected_refs,
    )
    attempt = sealed(
        ExecutionAttemptEnvelope,
        "attempt-envelope",
        attempt_id="attempt-1",
        proof_ref=proof.exact_ref(),
        state=AttemptState.CREATED,
        implementation_ref="fixture@sha",
        config_hash="a" * 64,
        protected_resource_refs=protected_refs,
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
        "resource": resource,
        "proof": proof,
        "attempt": attempt,
    }


def persist_program(adapter: GWFAdapter, program):
    for key in (
        "decision_rule",
        "admission",
        "retry",
        "amendment",
        "independence",
        "resolution_policy",
        "requirement",
        "goal",
        "claim",
        "graph",
        "closure",
        "proof",
    ):
        adapter.persist_canonical(program[key])
    if program["resource"] is not None:
        adapter.persist_canonical(program["resource"])


def gwf_execute(adapter: GWFAdapter, program, score="0.90"):
    resources = () if program["resource"] is None else (program["resource"],)
    return adapter.execute(
        program["attempt"],
        lambda: GWFExecutionOutcome(
            action_summary="emit deterministic fixture metric",
            evidence=(
                GWFCandidateEvidenceSpec(
                    source_class="LOCAL",
                    payload={"metrics": {"score": score}},
                    object_id="fixture-evidence",
                ),
            ),
        ),
        provenance=P,
        protected_resources=resources,
    )


def adjudicate_report(adapter: GWFAdapter, program, report):
    candidate = report.candidate_evidence[0]
    payload = adapter.load_evidence_payload(candidate)
    decision = evaluate_evidence_admission(candidate, program["admission"])
    assert decision.lifecycle == EvidenceLifecycle.ADMITTED
    admitted = materialize_evidence_admission(
        candidate,
        program["admission"],
        decision,
        revision_id="admitted-r1",
        provenance=P,
    )
    adapter.persist_canonical(admitted)
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
    adapter.persist_canonical(adjudication)
    proof_result = materialize_proof_result(
        program["proof"],
        program["retry"],
        (adjudication,),
        invalid_attempt_count=0,
        object_id="proof-result-proof-1",
        revision_id="r1",
        provenance=P,
    )
    adapter.persist_canonical(proof_result)
    outcome = ProofOutcome(proof_result.outcome.value)
    claim_resolution = resolve_claim(
        program["resolution_policy"],
        {program["proof"].object_id: outcome},
    )
    goal_verdict = evaluate_goal(
        program["closure"],
        {program["claim"].object_id: claim_resolution},
        can_progress=False,
    )
    return admitted, adjudication, proof_result, claim_resolution, goal_verdict


def revise_attempt(attempt, state: AttemptState, revision_id: str):
    data = attempt.model_dump(mode="python", exclude={"content_hash"})
    data.update({"revision_id": revision_id, "state": state, "provenance": P})
    return ExecutionAttemptEnvelope.sealed(**data)


def test_static_gwf_domain_contract_is_single_attempt_and_has_no_library_surface():
    domain = g2e_gwf_domain()
    workunit = domain.workunit("g2e_execute_proof")
    assert workunit["retry_policy"]["max_attempts"] == 1
    assert workunit["execution_policy"]["runtime_success_is_scientific_pass"] is False
    serialized = repr(domain.data).lower()
    assert "catalogqueryexecution" not in serialized
    assert "gac publication" not in serialized
    assert "reference acquisition" not in serialized


def test_canonical_roundtrip_preserves_g2e_identity_and_keeps_hash_domains_separate(tmp_path):
    runtime, _, adapter = make_adapter(tmp_path)
    program = build_program()
    mapping = adapter.persist_canonical(program["goal"])
    loaded = adapter.load_mapping(mapping)

    assert loaded.exact_ref() == program["goal"].exact_ref()
    assert adapter.load_exact("goal_contract", program["goal"].exact_ref()) == program["goal"]
    # GWF hashes its wrapper representation; it is not the G2E canonical hash.
    assert mapping.gwf_revision_hash != mapping.g2e_ref.content_hash
    runtime.close()


def test_same_g2e_revision_cannot_be_remapped_with_changed_canonical_hash(tmp_path):
    runtime, _, adapter = make_adapter(tmp_path)
    program = build_program()
    adapter.persist_canonical(program["goal"])

    data = program["goal"].model_dump(mode="python", exclude={"content_hash"})
    data["goal_statement"] = "mutated semantic statement"
    changed = GoalContract.sealed(**data)
    assert changed.revision_id == program["goal"].revision_id
    assert changed.content_hash != program["goal"].content_hash

    with pytest.raises(GWFMappingConflictError, match="different canonical hash"):
        adapter.persist_canonical(changed)
    runtime.close()


def test_wrong_gwf_revision_mapping_is_rejected(tmp_path):
    runtime, _, adapter = make_adapter(tmp_path)
    program = build_program()
    mapping = adapter.persist_canonical(program["goal"])
    wrong = GWFMappingRef(
        schema_kind=mapping.schema_kind,
        g2e_ref=ExactRef(
            object_id=mapping.g2e_ref.object_id,
            revision_id=mapping.g2e_ref.revision_id,
            content_hash="0" * 64,
        ),
        gwf_artifact_id=mapping.gwf_artifact_id,
        gwf_revision_id=mapping.gwf_revision_id,
        gwf_revision_hash=mapping.gwf_revision_hash,
    )
    with pytest.raises(GWFMappingConflictError, match="wrong G2E exact ref"):
        adapter.load_mapping(wrong)
    runtime.close()


def test_unsupported_mapping_version_fails_closed(tmp_path):
    runtime, project_id, _ = make_adapter(tmp_path)
    with pytest.raises(UnsupportedGWFMappingVersion):
        GWFAdapter(runtime, project_id, mapping_version="g2e-gwf-p4-v999")
    runtime.close()


def test_gwf_succeeded_is_not_claim_pass_until_p2_adjudication(tmp_path):
    runtime, _, adapter = make_adapter(tmp_path)
    program = build_program()
    persist_program(adapter, program)
    report = gwf_execute(adapter, program, score="0.90")

    workunit = runtime.db.one(
        "SELECT * FROM workunits WHERE workunit_id=?",
        (report.gwf_workunit_id,),
    )
    assert workunit["status"] == "SUCCEEDED"
    loaded_claim = adapter.load_exact("claim", program["claim"].exact_ref())
    assert loaded_claim.resolution == ClaimResolution.UNKNOWN

    _, adjudication, _, claim_resolution, goal_verdict = adjudicate_report(
        adapter, program, report
    )
    assert adjudication.verdict == AdjudicationVerdict.PASS
    assert claim_resolution == ClaimResolution.PASS
    assert goal_verdict == GoalVerdict.ACHIEVED
    runtime.close()


def test_standalone_and_gwf_attempt_and_candidate_evidence_are_identical(tmp_path):
    program = build_program()
    standalone = StandaloneRuntime(tmp_path / "standalone")
    s_report = standalone.executor.execute(
        program["attempt"],
        lambda: LocalExecutionOutcome(
            action_summary="emit deterministic fixture metric",
            evidence=(
                CandidateEvidenceSpec(
                    source_class="LOCAL",
                    payload={"metrics": {"score": "0.90"}},
                    object_id="fixture-evidence",
                ),
            ),
        ),
        provenance=P,
    )

    runtime, _, adapter = make_adapter(tmp_path)
    persist_program(adapter, program)
    g_report = gwf_execute(adapter, program, score="0.90")

    assert g_report.final_attempt == s_report.final_attempt
    assert g_report.candidate_evidence == s_report.candidate_evidence

    # ExecutionResult has runtime timestamps/redaction metadata, but every
    # provider-neutral scientific/execution field must remain identical.
    def semantic_result_projection(result):
        return result.model_dump(
            mode="json",
            exclude={
                "content_hash",
                "started_at",
                "ended_at",
                "redaction_metadata",
            },
        )

    assert semantic_result_projection(g_report.execution_result) == (
        semantic_result_projection(s_report.execution_result)
    )
    assert adapter.load_evidence_payload(g_report.candidate_evidence[0]) == {
        "metrics": {"score": "0.90"}
    }
    runtime.close()


def test_protected_resource_parity_and_backward_transition_rejected(tmp_path):
    program = build_program(protected=True)
    standalone = StandaloneRuntime(tmp_path / "standalone")
    standalone.store.persist_protected_resource(program["resource"])
    s_report = standalone.executor.execute(
        program["attempt"],
        lambda: LocalExecutionOutcome(action_summary="protected fixture"),
        provenance=P,
        protected_resource_ids=(program["resource"].object_id,),
    )
    s_resource = standalone.store.current_protected_resource(
        program["resource"].object_id
    )

    runtime, _, adapter = make_adapter(tmp_path)
    persist_program(adapter, program)
    g_report = adapter.execute(
        program["attempt"],
        lambda: GWFExecutionOutcome(action_summary="protected fixture"),
        provenance=P,
        protected_resources=(program["resource"],),
    )
    g_resource = g_report.protected_resources[0]

    assert s_report.final_attempt == g_report.final_attempt
    assert s_resource == g_resource
    assert g_resource.freshness_state == FreshnessState.EXPOSED
    with pytest.raises(CoreInvariantError):
        transition_protected_resource(
            g_resource,
            "RESERVE",
            revision_id="illegal-backward",
            provenance=P,
        )
    runtime.close()


def test_uncertain_gwf_recovery_fails_closed_to_exposed_and_preempted(tmp_path):
    runtime, _, adapter = make_adapter(tmp_path)
    program = build_program(protected=True)
    persist_program(adapter, program)
    locked = revise_attempt(program["attempt"], AttemptState.LOCKED, "r1.locked")
    reserved = transition_protected_resource(
        program["resource"],
        "RESERVE",
        revision_id="reserved-attempt-1-1",
        provenance=P,
    )
    adapter.persist_canonical(locked)
    adapter.persist_canonical(reserved)

    recovery = adapter.recover_uncertain_execution(
        locked,
        (reserved,),
        provenance=P,
    )
    assert recovery.final_attempt.state == AttemptState.PREEMPTED
    assert recovery.protected_resources[0].freshness_state == FreshnessState.EXPOSED
    adapter.verify_checkpoint(
        recovery.checkpoint_id,
        (
            recovery.final_attempt.exact_ref(),
            recovery.protected_resources[0].exact_ref(),
        ),
    )
    runtime.close()


def test_generic_gwf_runtime_never_expands_one_g2e_attempt_into_runtime_retries(tmp_path):
    runtime, _, adapter = make_adapter(tmp_path)
    program = build_program()
    persist_program(adapter, program)

    def boom():
        raise RuntimeError("deterministic executor failure")

    report = adapter.execute(program["attempt"], boom, provenance=P)
    workunit = runtime.db.one(
        "SELECT * FROM workunits WHERE workunit_id=?",
        (report.gwf_workunit_id,),
    )
    runs = runtime.db.all(
        "SELECT * FROM runs WHERE workunit_id=?",
        (report.gwf_workunit_id,),
    )
    assert parse_json(workunit["retry_policy"], {})["max_attempts"] == 1
    assert len(runs) == 1
    assert report.final_attempt.state == AttemptState.EXECUTOR_FAILED
    assert report.execution_result.executor_state == AttemptState.EXECUTOR_FAILED
    assert report.execution_result.technical_error_class == "RuntimeError"
    runtime.close()


def test_gwf_authority_denial_blocks_execution_without_semantic_verdict(tmp_path):
    runtime, project_id, adapter = make_adapter(tmp_path)
    program = build_program()
    persist_program(adapter, program)
    unprivileged = runtime.governance.create_actor(
        "AGENT",
        "no-authority",
        [],
        [project_id],
    )
    with pytest.raises(AuthorityDenied):
        adapter.execute(
            program["attempt"],
            lambda: GWFExecutionOutcome(action_summary="must not run"),
            provenance=P,
            actor_id=unprivileged,
        )
    assert runtime.db.one("SELECT COUNT(*) n FROM runs")["n"] == 0
    runtime.close()


def test_checkpoint_handoff_rejects_wrong_g2e_exact_ref_set(tmp_path):
    runtime, _, adapter = make_adapter(tmp_path)
    program = build_program()
    persist_program(adapter, program)
    report = gwf_execute(adapter, program)
    wrong = ExactRef(
        object_id=report.final_attempt.object_id,
        revision_id=report.final_attempt.revision_id,
        content_hash="0" * 64,
    )
    with pytest.raises(GWFMappingConflictError, match="exact-ref set mismatch"):
        adapter.verify_checkpoint(report.checkpoint_id, (wrong,))
    runtime.close()


def test_policy_mismatches_are_rejected_by_g2e_not_reinterpreted_by_gwf(tmp_path):
    runtime, _, adapter = make_adapter(tmp_path)
    program = build_program()
    persist_program(adapter, program)
    report = gwf_execute(adapter, program)
    candidate = report.candidate_evidence[0]
    payload = adapter.load_evidence_payload(candidate)

    wrong_rule = sealed(
        DecisionRule,
        "wrong-decision-rule",
        pass_expression=program["decision_rule"].pass_expression,
        fail_expression=program["decision_rule"].fail_expression,
        missing_metric_behavior="INVALID",
    )
    decision = evaluate_evidence_admission(candidate, program["admission"])
    admitted = materialize_evidence_admission(
        candidate,
        program["admission"],
        decision,
        revision_id="admitted-r1",
        provenance=P,
    )
    with pytest.raises(CoreInvariantError):
        adjudicate_attempt(
            program["proof"],
            wrong_rule,
            program["admission"],
            report.final_attempt,
            (admitted,),
            {admitted.object_id: payload},
            object_id="wrong-adjudication",
            revision_id="r1",
            provenance=P,
            independence_satisfied=True,
        )

    wrong_admission = sealed(
        EvidenceAdmissionPolicy,
        "wrong-admission",
        accepted_source_classes=("OTHER",),
        require_integrity_hash=True,
        require_attempt_linkage=True,
    )
    assert evaluate_evidence_admission(
        candidate, wrong_admission
    ).lifecycle == EvidenceLifecycle.REJECTED

    _, adjudication, _, _, _ = adjudicate_report(adapter, program, report)
    wrong_retry = sealed(
        ProofRetryPolicy,
        "wrong-retry",
        max_invalid_replacement_attempts=99,
    )
    with pytest.raises(CoreInvariantError, match="retry policy"):
        materialize_proof_result(
            program["proof"],
            wrong_retry,
            (adjudication,),
            invalid_attempt_count=0,
            object_id="wrong-proof-result",
            revision_id="r1",
            provenance=P,
        )
    runtime.close()


def test_terminal_adjudication_mapping_cannot_be_rewritten(tmp_path):
    runtime, _, adapter = make_adapter(tmp_path)
    program = build_program()
    persist_program(adapter, program)
    report = gwf_execute(adapter, program)
    _, adjudication, _, _, _ = adjudicate_report(adapter, program, report)

    data = adjudication.model_dump(mode="python", exclude={"content_hash"})
    data["verdict"] = AdjudicationVerdict.FAIL
    changed = type(adjudication).sealed(**data)
    assert changed.content_hash != adjudication.content_hash
    with pytest.raises(GWFMappingConflictError, match="different canonical hash"):
        adapter.persist_canonical(changed)
    runtime.close()


def test_gwf_mapping_and_checkpoint_survive_fresh_runtime_restart(tmp_path):
    db_path = tmp_path / "restart-gwf.sqlite"
    runtime = GovernedWorkflowRuntime(g2e_gwf_domain(), db_path=str(db_path))
    project_id = runtime.create_project("g2e-p4-restart")
    adapter = GWFAdapter(runtime, project_id)
    program = build_program()
    persist_program(adapter, program)
    report = gwf_execute(adapter, program)
    final_ref = report.final_attempt.exact_ref()
    result_ref = report.execution_result.exact_ref()
    evidence_ref = report.candidate_evidence[0].exact_ref()
    checkpoint_id = report.checkpoint_id
    runtime.close()

    reopened = GovernedWorkflowRuntime(g2e_gwf_domain(), db_path=str(db_path))
    reopened_adapter = GWFAdapter(reopened, project_id)
    assert reopened_adapter.load_exact("execution_attempt_envelope", final_ref) == (
        report.final_attempt
    )
    assert reopened_adapter.load_exact("execution_result", result_ref) == (
        report.execution_result
    )
    reopened_evidence = reopened_adapter.load_exact("evidence_record", evidence_ref)
    assert reopened_evidence == report.candidate_evidence[0]
    assert reopened_adapter.load_evidence_payload(reopened_evidence) == {
        "metrics": {"score": "0.90"}
    }
    reopened_adapter.verify_checkpoint(
        checkpoint_id,
        (final_ref, result_ref, evidence_ref),
    )
    reopened.close()


def test_result_package_semantic_manifest_is_identical_across_standalone_and_gwf(tmp_path):
    program = build_program()

    standalone = StandaloneRuntime(tmp_path / "parity-standalone-runtime")
    s_report = standalone.executor.execute(
        program["attempt"],
        lambda: LocalExecutionOutcome(
            action_summary="emit deterministic fixture metric",
            evidence=(
                CandidateEvidenceSpec(
                    source_class="LOCAL",
                    payload={"metrics": {"score": "0.90"}},
                    object_id="fixture-evidence",
                ),
            ),
        ),
        provenance=P,
    )
    s_candidate = s_report.candidate_evidence[0]
    s_decision = evaluate_evidence_admission(s_candidate, program["admission"])
    s_admitted = materialize_evidence_admission(
        s_candidate,
        program["admission"],
        s_decision,
        revision_id="admitted-r1",
        provenance=P,
    )
    s_payload = s_report.evidence_payloads[s_candidate.object_id]
    s_adjudication = adjudicate_attempt(
        program["proof"],
        program["decision_rule"],
        program["admission"],
        s_report.final_attempt,
        (s_admitted,),
        {s_admitted.object_id: s_payload},
        object_id="adjudication-1",
        revision_id="r1",
        provenance=P,
        independence_satisfied=True,
    )
    s_proof_result = materialize_proof_result(
        program["proof"],
        program["retry"],
        (s_adjudication,),
        invalid_attempt_count=0,
        object_id="proof-result-proof-1",
        revision_id="r1",
        provenance=P,
    )

    runtime, _, adapter = make_adapter(tmp_path)
    persist_program(adapter, program)
    g_report = gwf_execute(adapter, program)
    g_admitted, g_adjudication, g_proof_result, _, _ = adjudicate_report(
        adapter, program, g_report
    )

    assert g_report.final_attempt == s_report.final_attempt
    assert g_report.candidate_evidence[0] == s_candidate
    assert g_admitted == s_admitted
    assert g_adjudication == s_adjudication
    assert g_proof_result == s_proof_result

    common = dict(
        goal=program["goal"],
        goal_closure=program["closure"],
        claim_graph=program["graph"],
        proofs=(program["proof"],),
        proof_dependencies=(
            program["decision_rule"],
            program["admission"],
            program["retry"],
            program["amendment"],
            program["independence"],
            program["resolution_policy"],
        ),
        reproducibility_manifest={
            "decision_rule_hash": program["decision_rule"].content_hash,
            "parity_contract": "p4",
        },
        package_lineage=(),
        provenance=P,
        framework_version="g2e-p4",
    )
    s_package = export_goal_result_package(
        tmp_path / "semantic-package-standalone",
        proof_results=(s_proof_result,),
        evidence=(s_admitted,),
        adjudications=(s_adjudication,),
        runtime_id="g2e-standalone",
        runtime_version="0.1",
        **common,
    )
    g_package = export_goal_result_package(
        tmp_path / "semantic-package-gwf",
        proof_results=(g_proof_result,),
        evidence=(g_admitted,),
        adjudications=(g_adjudication,),
        runtime_id=GWF_RUNTIME_ID,
        runtime_version=GWF_RUNTIME_VERSION,
        **common,
    )

    # The manifest is the semantic package identity. Only the outer runtime seal
    # is allowed to differ by backend.
    assert s_package.manifest == g_package.manifest
    assert s_package.seal.manifest_ref == g_package.seal.manifest_ref
    assert s_package.seal.runtime_id == "g2e-standalone"
    assert g_package.seal.runtime_id == GWF_RUNTIME_ID
    runtime.close()


def test_gwf_execution_can_feed_independently_verified_goal_result_package(tmp_path):
    runtime, project_id, adapter = make_adapter(tmp_path)
    program = build_program()
    persist_program(adapter, program)
    report = gwf_execute(adapter, program)
    admitted, adjudication, proof_result, claim_resolution, goal_verdict = (
        adjudicate_report(adapter, program, report)
    )
    assert claim_resolution == ClaimResolution.PASS
    assert goal_verdict == GoalVerdict.ACHIEVED

    package_dir = tmp_path / "gwf-goal-result"
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
            "mapping_version": GWF_ADAPTER_MAPPING_VERSION,
        },
        package_lineage=runtime.governance.query_audit(project_id),
        provenance=P,
        framework_version="g2e-p4",
        runtime_id=GWF_RUNTIME_ID,
        runtime_version=GWF_RUNTIME_VERSION,
    )
    independently_verified = verify_goal_result_package(package_dir)
    assert independently_verified.seal == verification.seal
    assert independently_verified.seal.runtime_id == GWF_RUNTIME_ID
    runtime.close()
