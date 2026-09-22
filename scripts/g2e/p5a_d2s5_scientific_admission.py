from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from g2e import (
    AgentBinding,
    AgentCapability,
    AgentCapabilityManifest,
    AgentEquivalencePolicy,
    AgentProfileAvailability,
    AmendmentPolicy,
    AttemptState,
    AuthorityAction,
    AuthorityPolicy,
    BindingMode,
    DecisionExpression,
    DecisionRule,
    EvidenceAdmissionPolicy,
    ExecutionAttemptEnvelope,
    IndependencePolicy,
    MetricPredicate,
    ProofLifecycle,
    ProofObligation,
    ProofRetryPolicy,
    Provenance,
    QualificationAuthorityGrant,
    validate_qualification_agent_binding_identity,
)

RELEASE_TAG = "rust-v0.153.4"
SOURCE_COMMIT = "3d2ee51ca2d5db578f328aa75e20aa22c0197c9a"
HARNESS_SHA256 = "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b"
HELPER_SHA256 = "0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4"
INPUT_SHA256 = "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
TASK_SHA256 = "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"
R2_REPORT_SHA256 = "b24af8e5261ba8e5a90605e7a9b9d63c0025f37650f9a4e657cdaafd76b0545e"
R2_EVIDENCE_SHA256 = "87f18cf15f06eb1bc3e0a9e28f76e3208b2c082c3cd458221242d65db7b8cc28"
PREDECESSOR_POSTCLOSURE_BUNDLE_SHA256 = "ad7aef6c621554791213635c802578c5cc0f94f8e2e12381b5e629fd2836be39"
OBSERVABLE_CLIENT_GIT_BLOB = "57f5b3e0a1ac13f7722d7bfe244a100bfeb08504"
OBSERVABILITY_GIT_BLOB = "b6d3c6fcb671dd166893edd46388c8d69dca9105"

STUDY_ID = "p5a-d2s5-observability-qualified-functional-successor"
ATTEMPT_ID = "p5a-d2s5-p5-fx-001-attempt-001"
PROFILE_ID = "g2e_p5a_d2s3"
REVISION_ID = "p5-fx-001-d2s5-v1"

REQUIRED_PREREQUISITES = (
    "app_server_launch",
    "jsonrpc_initialize",
    "thread_lifecycle_surface",
    "turn_stream_surface",
    "external_session_attribution_surface",
)
QUALIFICATION_TARGETS = ("repository_read", "repository_write")
GRANTED_AUTHORITY = ("READ_FROZEN_FIXTURE", "WRITE_DESIGNATED_OUTPUT")
READ_PATHS = ("input.json", "TASK.md")
WRITE_PATHS = ("result.json",)
FUNCTIONAL_UNQUALIFIED = (
    "repository_read",
    "repository_write",
    "shell_execution",
    "test_execution",
    "network_access",
    "side_effect_approval_execution",
    "active_task_cancellation_interruption",
    "completed_task_artifact_extraction",
    "model_task_correctness",
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
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


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
    return {
        "generator_version": "p5-fx-001-v1",
        "seed": seed,
        "values": values,
    }


def _stable_discovery_payload(discovery: dict) -> dict:
    required = discovery.get("required_protocol_tokens") or {}
    optional = discovery.get("optional_protocol_tokens") or {}
    handshake = discovery.get("initialize_handshake") or {}

    if discovery.get("schema") != "G2E-P5A-CODEX-DISCOVERY-v1":
        raise ValueError("unexpected discovery schema")
    if discovery.get("status") != "D1_MINIMUM_QUALIFIED":
        raise ValueError("official harness D1 discovery is not qualified")
    if discovery.get("executable_sha256") != HARNESS_SHA256:
        raise ValueError("official harness SHA256 mismatch")
    if discovery.get("app_server_help_exit_code") != 0:
        raise ValueError("app-server help did not pass")
    if discovery.get("schema_generation_exit_code") != 0:
        raise ValueError("schema generation did not pass")
    if discovery.get("functional_task_executed") is not False:
        raise ValueError("functional task executed during D1")
    if discovery.get("secrets_persisted") is not False:
        raise ValueError("D1 secret-persistence boundary violated")
    if handshake.get("success") is not True:
        raise ValueError("initialize handshake did not pass")

    required_tokens = (
        "initialize",
        "thread/start",
        "thread/resume",
        "turn/start",
        "item/started",
        "item/completed",
    )
    missing = [name for name in required_tokens if required.get(name) is not True]
    if missing:
        raise ValueError("required protocol token missing: " + ",".join(missing))

    if optional.get("sessionId") is not True:
        raise ValueError("sessionId attribution surface missing")

    files = discovery.get("generated_schema_files")
    if not isinstance(files, list) or not files:
        raise ValueError("generated schema inventory missing")

    digest = discovery.get("schema_inventory_digest")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("schema inventory digest missing")

    return {
        "release_tag": RELEASE_TAG,
        "source_commit": SOURCE_COMMIT,
        "executable_sha256": HARNESS_SHA256,
        "app_server_help_exit_code": 0,
        "schema_generation_exit_code": 0,
        "schema_inventory_digest": digest,
        "required_protocol_tokens": {
            name: True for name in required_tokens
        },
        "session_id_surface": True,
        "initialize_handshake_success": True,
        "functional_task_executed": False,
        "secrets_persisted": False,
    }


def structural_discovery_digest(discovery: dict) -> str:
    return sha256_json(_stable_discovery_payload(discovery))


def _provenance(discovery_digest: str) -> Provenance:
    return Provenance(
        created_by="g2e-p5a-d2s5-scientific-admission",
        created_at="2026-09-22T10:00:00Z",
        source_refs=(
            f"d2s5-structural-discovery:{discovery_digest}",
            f"release-tag:{RELEASE_TAG}",
            f"source-commit:{SOURCE_COMMIT}",
            f"predecessor-r2-report-sha256:{R2_REPORT_SHA256}",
            f"predecessor-r2-evidence-sha256:{R2_EVIDENCE_SHA256}",
            f"predecessor-postclosure-bundle-sha256:{PREDECESSOR_POSTCLOSURE_BUNDLE_SHA256}",
            f"observable-client-git-blob:{OBSERVABLE_CLIENT_GIT_BLOB}",
        ),
        derivation=(
            "Prospective D2-S5 structural manifest, proof and P1.5 admission; "
            "no scientific model turn"
        ),
    )


def _sealed(cls, object_id: str, provenance: Provenance, **kwargs):
    return cls.sealed(
        object_id=object_id,
        revision_id=REVISION_ID,
        provenance=provenance,
        **kwargs,
    )


def build_manifest(discovery: dict) -> AgentCapabilityManifest:
    stable = _stable_discovery_payload(discovery)
    discovery_digest = sha256_json(stable)
    provenance = _provenance(discovery_digest)
    refs = (
        f"d2s5-structural-discovery:{discovery_digest}",
        f"schema-inventory-sha256:{stable['schema_inventory_digest']}",
        f"release-tag:{RELEASE_TAG}",
        f"source-commit:{SOURCE_COMMIT}",
    )

    available = (
        "app_server_launch",
        "version_matched_schema_generation",
        "jsonrpc_initialize",
        "thread_lifecycle_surface",
        "turn_stream_surface",
        "external_session_attribution_surface",
    )
    capabilities = [
        AgentCapability(
            capability_id=capability_id,
            available=True,
            qualification_refs=refs,
            limitations=(
                "D2-S5 structural surface only; functional execution not demonstrated",
            ),
        )
        for capability_id in available
    ]
    capabilities.extend(
        AgentCapability(
            capability_id=capability_id,
            available=False,
            qualification_refs=(),
            limitations=("D2-S5 bounded functional qualification required",),
        )
        for capability_id in FUNCTIONAL_UNQUALIFIED
    )

    return AgentCapabilityManifest.sealed(
        object_id="agent-capability-manifest-codex-d2s5-d1",
        revision_id="444a3f0008050605-d1-v1",
        provenance=provenance,
        agent_app="codex",
        profile_version="g2e-p5a-d2s5-d1-v1",
        harness_ref=f"sha256:{HARNESS_SHA256}",
        exact_harness_revision=HARNESS_SHA256,
        provider_ref=None,
        model_ref=None,
        transport_ref="app-server-stdio",
        availability=AgentProfileAvailability.AVAILABLE,
        capabilities=tuple(capabilities),
        execution_constraints=(
            "d2s5_structural_only",
            "no_functional_task_executed",
            "exact_release_coherent_executable_required",
        ),
        max_authority_scope=(),
        credential_ref_classes=(),
        external_session_attribution=True,
        interruption_supported=False,
        artifact_extraction_supported=False,
        structured_output_supported=False,
        status_normalization_supported=False,
        discovery_evidence_refs=refs,
        limitations=(
            "availability applies only to D2-S5 structural App Server surface",
            "repository read/write remain unqualified before scientific attempt",
        ),
    )


def build_proof_bundle(manifest: AgentCapabilityManifest, discovery_digest: str) -> dict:
    provenance = _provenance(discovery_digest)

    retry = _sealed(
        ProofRetryPolicy,
        "p5a-d2s5-retry",
        provenance,
        max_invalid_replacement_attempts=0,
        require_same_semantic_proof_identity=True,
        allowed_technical_reason_codes=(),
    )
    amendment = _sealed(
        AmendmentPolicy,
        "p5a-d2s5-amendment",
        provenance,
        allow_editorial=False,
        normative_pre_outcome_requires_refreeze=True,
        normative_post_outcome_requires_new_lineage=True,
    )
    independence = _sealed(
        IndependencePolicy,
        "p5a-d2s5-independence",
        provenance,
        required_dimensions=(),
        forbidden_shared_ancestor_classes=(),
    )
    admission = _sealed(
        EvidenceAdmissionPolicy,
        "p5a-d2s5-evidence-admission",
        provenance,
        accepted_source_classes=("codex_p5_fx_001_d2s5",),
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
            predicate=MetricPredicate(
                metric_id=metric,
                operator="EQ",
                threshold_key="one",
            ),
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
            predicate=MetricPredicate(
                metric_id=metric,
                operator="EQ",
                threshold_key="zero",
            ),
        )
        for metric in (
            "result_schema_valid",
            "result_values_correct",
            "mutation_scope_valid",
        )
    )
    decision = _sealed(
        DecisionRule,
        "p5a-d2s5-decision-rule",
        provenance,
        pass_expression=DecisionExpression(op="ALL", children=pass_children),
        fail_expression=DecisionExpression(op="ANY", children=fail_children),
        missing_metric_behavior="INVALID",
        metric_conflict_behavior="INVALID",
    )
    proof = _sealed(
        ProofObligation,
        "p5a-d2s5-p5-fx-001-proof",
        provenance,
        lifecycle=ProofLifecycle.FROZEN,
        target_claim_id="p5a-d2s5-codex-functional-qualification",
        proposition=(
            "The exact release-coherent D2-S5 Codex harness completes P5-FX-001 "
            "within the frozen workspace, mutation, authority and evidence contract."
        ),
        assumptions=(
            f"exact D2-S5 harness sha256 {HARNESS_SHA256} remains unchanged",
            f"exact setup helper sha256 {HELPER_SHA256} remains unchanged",
        ),
        controls=(
            "single scientific attempt",
            "no network",
            "no interactive approval",
            "zero retry",
        ),
        fixture_or_population_ref=f"sha256:{INPUT_SHA256}",
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
        stop_conditions=(
            "first attempt-consumption marker only",
            "timeout at 90 seconds",
        ),
    )
    equivalence = _sealed(
        AgentEquivalencePolicy,
        "p5a-d2s5-agent-equivalence",
        provenance,
        material_dimensions=(
            "agent_app",
            "provider_ref",
            "model_ref",
            "harness_ref",
            "transport_ref",
        ),
        allowed_substitution_dimensions=(),
    )

    return {
        "retry": retry,
        "amendment": amendment,
        "independence": independence,
        "evidence_admission": admission,
        "decision": decision,
        "proof": proof,
        "equivalence": equivalence,
    }


def build_final_admission(discovery: dict) -> dict:
    stable = _stable_discovery_payload(discovery)
    discovery_digest = sha256_json(stable)
    provenance = _provenance(discovery_digest)

    manifest = build_manifest(discovery)
    proof_bundle = build_proof_bundle(manifest, discovery_digest)
    proof = proof_bundle["proof"]
    equivalence = proof_bundle["equivalence"]

    authority_policy = _sealed(
        AuthorityPolicy,
        "p5a-d2s5-p5-fx-001-authority-policy",
        provenance,
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

    grant = _sealed(
        QualificationAuthorityGrant,
        "p5a-d2s5-p5-fx-001-qualification-grant",
        provenance,
        proof_ref=proof.exact_ref(),
        capability_manifest_ref=manifest.exact_ref(),
        attempt_id=ATTEMPT_ID,
        target_capability_ids=QUALIFICATION_TARGETS,
        authority_policy_ref=authority_policy.exact_ref(),
        granted_role="qualification_executor",
        granted_authority_scope=GRANTED_AUTHORITY,
        allowed_read_paths=READ_PATHS,
        allowed_write_paths=WRITE_PATHS,
        qualification_lineage_ref=(
            "g2e/docs/P5A_D2S5_OBSERVABILITY_QUALIFIED_SUCCESSOR_PREIMPLEMENTATION.md"
        ),
    )

    binding = _sealed(
        AgentBinding,
        "p5a-d2s5-final-agent-binding",
        provenance,
        resolved_attempt_id=ATTEMPT_ID,
        agent_app=manifest.agent_app,
        capability_manifest_ref=manifest.exact_ref(),
        equivalence_policy_ref=equivalence.exact_ref(),
        binding_mode=BindingMode.FROZEN,
        harness_ref=manifest.harness_ref,
        provider_ref=manifest.provider_ref,
        model_ref=manifest.model_ref,
        transport_ref=manifest.transport_ref,
        required_capability_ids=REQUIRED_PREREQUISITES,
        qualification_authority_ref=grant.exact_ref(),
        qualification_target_capability_ids=QUALIFICATION_TARGETS,
        execution_constraints=(
            f"fixture_sha256:{INPUT_SHA256}",
            f"task_sha256:{TASK_SHA256}",
            f"predecessor_r2_evidence_sha256:{R2_EVIDENCE_SHA256}",
            f"observable_client_git_blob:{OBSERVABLE_CLIENT_GIT_BLOB}",
            f"observability_git_blob:{OBSERVABILITY_GIT_BLOB}",
            "workspace_pre:TASK.md,input.json",
            "workspace_optional_support_metadata:System Volume Information",
            "workspace_only_task_output:result.json",
            "network:DENY",
            "interactive_approval:DENY",
            "single_scientific_attempt",
            "turn_timeout_seconds:90",
        ),
        authority_scope=GRANTED_AUTHORITY,
        resolved_at="2026-09-22T10:00:00Z",
        resolution_ref="p5a-d2s5-scientific-macro-admission",
    )

    execution_config = {
        "study_id": STUDY_ID,
        "attempt_id": ATTEMPT_ID,
        "fixture_id": "P5-FX-001",
        "input_sha256": INPUT_SHA256,
        "task_sha256": TASK_SHA256,
        "harness_sha256": HARNESS_SHA256,
        "helper_sha256": HELPER_SHA256,
        "release_tag": RELEASE_TAG,
        "source_commit": SOURCE_COMMIT,
        "profile_id": PROFILE_ID,
        "proof_ref": proof.exact_ref().model_dump(mode="json"),
        "manifest_ref": manifest.exact_ref().model_dump(mode="json"),
        "authority_policy_ref": authority_policy.exact_ref().model_dump(mode="json"),
        "qualification_grant_ref": grant.exact_ref().model_dump(mode="json"),
        "agent_binding_ref": binding.exact_ref().model_dump(mode="json"),
        "pre_workspace_payload": ["TASK.md", "input.json"],
        "optional_filesystem_support_metadata": ["System Volume Information"],
        "only_permitted_task_output": "result.json",
        "allowed_read_paths": list(READ_PATHS),
        "allowed_write_paths": list(WRITE_PATHS),
        "authority_scope": list(GRANTED_AUTHORITY),
        "network_allowed": False,
        "interactive_approval_allowed": False,
        "startup_timeout_seconds": 12,
        "sandbox_setup_timeout_seconds": 90,
        "turn_timeout_seconds": 90,
        "verifier_timeout_seconds": 10,
        "max_invalid_replacement_attempts": 0,
        "r2_report_sha256": R2_REPORT_SHA256,
        "r2_evidence_sha256": R2_EVIDENCE_SHA256,
        "predecessor_postclosure_bundle_sha256": PREDECESSOR_POSTCLOSURE_BUNDLE_SHA256,
        "observable_client_git_blob": OBSERVABLE_CLIENT_GIT_BLOB,
        "observability_git_blob": OBSERVABILITY_GIT_BLOB,
        "attempt_consumption_rule": (
            "durable marker creation immediately before sole turn/start send"
        ),
    }
    config_hash = sha256_json(execution_config)

    attempt = _sealed(
        ExecutionAttemptEnvelope,
        "p5a-d2s5-predispatch-attempt-envelope",
        provenance,
        attempt_id=ATTEMPT_ID,
        proof_ref=proof.exact_ref(),
        state=AttemptState.LOCKED,
        implementation_ref=(
            f"external-codex-app-server-stdio:sha256:{HARNESS_SHA256}"
        ),
        config_hash=config_hash,
        artifact_refs=(),
        data_refs=(
            f"sha256:{INPUT_SHA256}",
            f"sha256:{TASK_SHA256}",
            f"preflight-sha256:{R2_EVIDENCE_SHA256}",
        ),
        agent_app=binding.agent_app,
        provider_ref=binding.provider_ref,
        model_ref=binding.model_ref,
        harness_ref=binding.harness_ref,
        transport_ref=binding.transport_ref,
        agent_binding_ref=binding.exact_ref(),
        protected_resource_refs=(),
        retry_policy_ref=proof.retry_policy_ref,
        authority_scope=binding.authority_scope,
    )

    validate_qualification_agent_binding_identity(
        manifest,
        equivalence,
        grant,
        authority_policy,
        proof,
        binding,
        attempt,
        expected_allowed_read_paths=READ_PATHS,
        expected_allowed_write_paths=WRITE_PATHS,
    )

    capabilities = {
        cap.capability_id: cap.available for cap in manifest.capabilities
    }
    if capabilities.get("repository_read") is not False:
        raise ValueError("repository_read became available before D2-S5 result")
    if capabilities.get("repository_write") is not False:
        raise ValueError("repository_write became available before D2-S5 result")

    return {
        "schema": "G2E-P5A-D2S5-SCIENTIFIC-ADMISSION-v1",
        "study_id": STUDY_ID,
        "attempt_id": ATTEMPT_ID,
        "structural_discovery_digest": discovery_digest,
        "manifest": manifest.model_dump(mode="json"),
        "proof_objects": {
            key: value.model_dump(mode="json")
            for key, value in proof_bundle.items()
        },
        "authority_policy": authority_policy.model_dump(mode="json"),
        "qualification_authority_grant": grant.model_dump(mode="json"),
        "final_agent_binding": binding.model_dump(mode="json"),
        "predispatch_attempt": attempt.model_dump(mode="json"),
        "execution_config": execution_config,
        "execution_config_hash": config_hash,
        "refs": {
            "manifest": manifest.exact_ref().model_dump(mode="json"),
            "proof": proof.exact_ref().model_dump(mode="json"),
            "equivalence_policy": equivalence.exact_ref().model_dump(mode="json"),
            "authority_policy": authority_policy.exact_ref().model_dump(mode="json"),
            "qualification_authority_grant": grant.exact_ref().model_dump(mode="json"),
            "final_agent_binding": binding.exact_ref().model_dump(mode="json"),
            "predispatch_attempt": attempt.exact_ref().model_dump(mode="json"),
        },
        "authorization": {
            "mode": (
                "CONDITIONAL_ON_EXACT_PREDECESSOR_EVIDENCE_AND_FRESH_RUNTIME_PREFLIGHT"
            ),
            "r2_report_sha256": R2_REPORT_SHA256,
            "r2_evidence_sha256": R2_EVIDENCE_SHA256,
            "exact_scientific_attempts_authorized_after_lock": 1,
            "retry_authorized": False,
            "automatic_retry_authorized": False,
            "runtime_adapter_authorized": False,
            "model_turn_executed_during_qualification": False,
        },
    }


def verify_final_admission(pack: dict, discovery: dict) -> None:
    expected = build_final_admission(discovery)
    if pack != expected:
        raise ValueError("materialized D2-S5 admission is not deterministic")

    manifest = AgentCapabilityManifest.parse_authoritative(pack["manifest"])
    proof = ProofObligation.parse_authoritative(
        pack["proof_objects"]["proof"]
    )
    equivalence = AgentEquivalencePolicy.parse_authoritative(
        pack["proof_objects"]["equivalence"]
    )
    authority_policy = AuthorityPolicy.parse_authoritative(
        pack["authority_policy"]
    )
    grant = QualificationAuthorityGrant.parse_authoritative(
        pack["qualification_authority_grant"]
    )
    binding = AgentBinding.parse_authoritative(pack["final_agent_binding"])
    attempt = ExecutionAttemptEnvelope.parse_authoritative(
        pack["predispatch_attempt"]
    )

    if attempt.state != AttemptState.LOCKED:
        raise ValueError("attempt is not LOCKED")
    if attempt.attempt_id != ATTEMPT_ID:
        raise ValueError("attempt id drift")
    if binding.resolved_attempt_id != ATTEMPT_ID:
        raise ValueError("binding attempt id drift")
    if grant.attempt_id != ATTEMPT_ID:
        raise ValueError("grant attempt id drift")
    if binding.harness_ref != f"sha256:{HARNESS_SHA256}":
        raise ValueError("binding harness drift")
    if attempt.harness_ref != f"sha256:{HARNESS_SHA256}":
        raise ValueError("attempt harness drift")
    if tuple(binding.required_capability_ids) != REQUIRED_PREREQUISITES:
        raise ValueError("required prerequisite drift")
    if tuple(binding.qualification_target_capability_ids) != QUALIFICATION_TARGETS:
        raise ValueError("qualification target drift")
    if tuple(binding.authority_scope) != GRANTED_AUTHORITY:
        raise ValueError("authority scope drift")
    if tuple(grant.allowed_read_paths) != READ_PATHS:
        raise ValueError("read path drift")
    if tuple(grant.allowed_write_paths) != WRITE_PATHS:
        raise ValueError("write path drift")
    if grant.network_allowed is not False:
        raise ValueError("network authority drift")
    if grant.interactive_approval_allowed is not False:
        raise ValueError("approval authority drift")

    config = pack["execution_config"]
    if config["input_sha256"] != INPUT_SHA256:
        raise ValueError("input hash drift")
    if config["task_sha256"] != TASK_SHA256:
        raise ValueError("task hash drift")
    if config["r2_evidence_sha256"] != R2_EVIDENCE_SHA256:
        raise ValueError("R2 evidence drift")
    if config["observable_client_git_blob"] != OBSERVABLE_CLIENT_GIT_BLOB:
        raise ValueError("observable client blob drift")
    if config["observability_git_blob"] != OBSERVABILITY_GIT_BLOB:
        raise ValueError("observability blob drift")
    if config["max_invalid_replacement_attempts"] != 0:
        raise ValueError("retry budget drift")
    if pack["execution_config_hash"] != sha256_json(config):
        raise ValueError("execution config hash mismatch")
    if attempt.config_hash != pack["execution_config_hash"]:
        raise ValueError("attempt config hash mismatch")

    validate_qualification_agent_binding_identity(
        manifest,
        equivalence,
        grant,
        authority_policy,
        proof,
        binding,
        attempt,
        expected_allowed_read_paths=READ_PATHS,
        expected_allowed_write_paths=WRITE_PATHS,
    )


def materialize(discovery_path: Path, output_dir: Path) -> dict:
    discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
    pack = build_final_admission(discovery)
    verify_final_admission(pack, discovery)

    output_dir.mkdir(parents=True, exist_ok=True)
    objects = {
        "P5A_D2S5_AGENT_CAPABILITY_MANIFEST.json": pack["manifest"],
        "P5A_D2S5_PROOF_OBLIGATION.json": pack["proof_objects"]["proof"],
        "P5A_D2S5_AUTHORITY_POLICY.json": pack["authority_policy"],
        "P5A_D2S5_QUALIFICATION_AUTHORITY_GRANT.json": (
            pack["qualification_authority_grant"]
        ),
        "P5A_D2S5_FINAL_AGENT_BINDING.json": pack["final_agent_binding"],
        "P5A_D2S5_PREDISPATCH_ATTEMPT.json": pack["predispatch_attempt"],
        "P5A_D2S5_SCIENTIFIC_ADMISSION.json": pack,
    }
    for name, value in objects.items():
        (output_dir / name).write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return pack


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--discovery", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    pack = materialize(Path(args.discovery), Path(args.output_dir))
    print(
        json.dumps(
            {
                "schema": pack["schema"],
                "structural_discovery_digest": pack[
                    "structural_discovery_digest"
                ],
                "manifest_ref": pack["refs"]["manifest"],
                "proof_ref": pack["refs"]["proof"],
                "final_agent_binding_ref": pack["refs"][
                    "final_agent_binding"
                ],
                "predispatch_attempt_ref": pack["refs"][
                    "predispatch_attempt"
                ],
                "execution_config_hash": pack["execution_config_hash"],
                "scientific_attempts_authorized": pack["authorization"][
                    "exact_scientific_attempts_authorized_after_lock"
                ],
                "model_turn_executed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
