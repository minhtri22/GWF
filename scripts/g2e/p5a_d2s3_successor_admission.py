from __future__ import annotations

import argparse
import hashlib
import importlib.util
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

ROOT = Path(__file__).resolve().parents[2]
OLD_PREREG = ROOT / "scripts" / "g2e" / "p5a_d2_p5_fx_001_preregister.py"
R2_BINDING_PATH = ROOT / "g2e" / "docs" / "P5A_D2S3_R2_PRETURN_EVIDENCE_BINDING.json"

STUDY_ID = "p5a-d2s3-release-coherent-instrument-successor"
ATTEMPT_ID = "p5a-d2s3-p5-fx-001-attempt-001"
REVISION_ID = "p5-fx-001-d2s3-v1"
RELEASE_TAG = "rust-v0.153.4"
SOURCE_COMMIT = "3d2ee51ca2d5db578f328aa75e20aa22c0197c9a"
HARNESS_SHA256 = "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b"
HELPER_SHA256 = "0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4"
INPUT_SHA256 = "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
TASK_SHA256 = "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"
R2_REPORT_SHA256 = "b24af8e5261ba8e5a90605e7a9b9d63c0025f37650f9a4e657cdaafd76b0545e"
R2_PREFLIGHT_EVIDENCE_SHA256 = "87f18cf15f06eb1bc3e0a9e28f76e3208b2c082c3cd458221242d65db7b8cc28"
PROFILE_ID = "g2e_p5a_d2s3"

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


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_r2_binding(path: Path = R2_BINDING_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "G2E-P5A-D2S3-R2-PRETURN-EVIDENCE-BINDING-v1":
        raise ValueError("R2 binding schema mismatch")
    exact = {
        "study_id": STUDY_ID,
        "attempt_id": ATTEMPT_ID,
        "profile_id": PROFILE_ID,
        "codex_sha256": HARNESS_SHA256,
        "helper_sha256": HELPER_SHA256,
        "input_sha256": INPUT_SHA256,
        "task_sha256": TASK_SHA256,
        "preflight_evidence_sha256": R2_PREFLIGHT_EVIDENCE_SHA256,
    }
    for key, expected in exact.items():
        if data.get(key) != expected:
            raise ValueError(f"R2 binding drift:{key}")
    if data.get("source_report", {}).get("sha256") != R2_REPORT_SHA256:
        raise ValueError("R2 report hash drift")
    for key in (
        "preturn_gate_pass",
        "turn_start_request_sent",
        "scientific_attempt_consumed",
        "result_exists",
    ):
        expected = key == "preturn_gate_pass"
        if data.get(key) is not expected:
            raise ValueError(f"R2 firewall drift:{key}")
    if data.get("workspace_payload_names") != ["input.json", "TASK.md"]:
        raise ValueError("R2 payload drift")
    if data.get("workspace_metadata_names") != ["System Volume Information"]:
        raise ValueError("R2 metadata drift")
    if data.get("workspace_unexpected_names") != []:
        raise ValueError("R2 unexpected root entries")
    cleanup = data.get("cleanup", {})
    if cleanup.get("attached_after_cleanup") is not False or cleanup.get("cleanup_error") is not None:
        raise ValueError("R2 cleanup not closed")
    derived = data.get("derived_from_exact_driver", {})
    required_derived = (
        "app_server_initialize_pass",
        "windows_sandbox_ready_pass",
        "mcp_zero_pass",
        "apps_zero_pass",
        "auth_ready_pass",
        "profile_present_and_allowed_pass",
        "thread_start_pass",
        "thread_id_present_pass",
        "instruction_sources_empty_pass",
        "unexpected_server_requests_zero_pass",
    )
    if any(derived.get(key) is not True for key in required_derived):
        raise ValueError("R2 derived platform predicate missing")
    return data


def validate_discovery(report: dict) -> dict:
    if report.get("schema") != "G2E-P5A-CODEX-DISCOVERY-v1":
        raise ValueError("discovery schema mismatch")
    if report.get("status") != "D1_MINIMUM_QUALIFIED":
        raise ValueError("official harness D1 discovery not qualified")
    if report.get("executable_sha256") != HARNESS_SHA256:
        raise ValueError("official harness hash drift")
    if report.get("functional_task_executed") is not False:
        raise ValueError("discovery executed functional task")
    if report.get("secrets_persisted") is not False:
        raise ValueError("discovery persisted secrets")
    if report.get("app_server_help_exit_code") != 0:
        raise ValueError("app-server help failed")
    if report.get("schema_generation_exit_code") != 0:
        raise ValueError("schema generation failed")
    required = report.get("required_protocol_tokens") or {}
    expected_tokens = (
        "initialize",
        "thread/start",
        "thread/resume",
        "turn/start",
        "item/started",
        "item/completed",
    )
    if any(required.get(token) is not True for token in expected_tokens):
        raise ValueError("required protocol token missing")
    handshake = report.get("initialize_handshake") or {}
    if handshake.get("success") is not True:
        raise ValueError("initialize handshake failed")
    digest = report.get("schema_inventory_digest")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("schema inventory digest missing")
    return report


def _provenance(schema_digest: str) -> Provenance:
    return Provenance(
        created_by="g2e-p5a-d2s3-successor-admission",
        created_at="2026-09-22T11:30:00Z",
        source_refs=(
            f"official-release:{RELEASE_TAG}:{SOURCE_COMMIT}",
            f"sha256:{HARNESS_SHA256}",
            f"schema-inventory-sha256:{schema_digest}",
            f"r2-report-sha256:{R2_REPORT_SHA256}",
            f"r2-preflight-evidence-sha256:{R2_PREFLIGHT_EVIDENCE_SHA256}",
        ),
        derivation=(
            "Prospective D2-S3 successor structural manifest, proof and final admission; "
            "no scientific turn"
        ),
    )


def _sealed(cls, object_id: str, provenance: Provenance, **kwargs):
    return cls.sealed(
        object_id=object_id,
        revision_id=REVISION_ID,
        provenance=provenance,
        **kwargs,
    )


def frozen_fixture() -> tuple[dict, str, bytes]:
    old = _load_module(OLD_PREREG, "p5a_d2_old_prereg_for_d2s3")
    payload = old.fixture_input()
    input_bytes = old.canonical_bytes(payload)
    task_text = old.TASK_TEXT
    if hashlib.sha256(input_bytes).hexdigest() != INPUT_SHA256:
        raise ValueError("frozen input drift")
    if hashlib.sha256(task_text.encode("utf-8")).hexdigest() != TASK_SHA256:
        raise ValueError("frozen task drift")
    return payload, task_text, input_bytes


def build_successor_admission(discovery_report: dict) -> dict:
    discovery = validate_discovery(discovery_report)
    r2 = load_r2_binding()
    payload, task_text, _ = frozen_fixture()
    schema_digest = discovery["schema_inventory_digest"]
    provenance = _provenance(schema_digest)
    qualification_refs = (
        f"official-release:{RELEASE_TAG}:{SOURCE_COMMIT}",
        f"sha256:{HARNESS_SHA256}",
        f"schema-inventory-sha256:{schema_digest}",
        f"r2-report-sha256:{R2_REPORT_SHA256}",
        f"r2-preflight-evidence-sha256:{R2_PREFLIGHT_EVIDENCE_SHA256}",
    )

    structural_available = (
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
            qualification_refs=qualification_refs,
            limitations=("D2-S3 structural/preturn qualification only",),
        )
        for capability_id in structural_available
    ]
    capabilities.extend(
        AgentCapability(
            capability_id=capability_id,
            available=False,
            qualification_refs=(),
            limitations=("D2-S3 scientific execution required",),
        )
        for capability_id in FUNCTIONAL_UNQUALIFIED
    )

    manifest = AgentCapabilityManifest.sealed(
        object_id="agent-capability-manifest-codex-d2s3-official",
        revision_id=f"{RELEASE_TAG}-d1-v1",
        provenance=provenance,
        agent_app="codex",
        profile_version="g2e-p5a-d2s3-official-d1-v1",
        harness_ref=f"sha256:{HARNESS_SHA256}",
        exact_harness_revision=HARNESS_SHA256,
        provider_ref=None,
        model_ref=None,
        transport_ref="app-server-stdio",
        availability=AgentProfileAvailability.AVAILABLE,
        capabilities=tuple(capabilities),
        execution_constraints=(
            "d2s3_structural_and_preturn_only",
            "scientific_task_not_yet_executed",
            "exact_official_release_binary_required",
        ),
        max_authority_scope=(),
        credential_ref_classes=(),
        external_session_attribution=True,
        interruption_supported=False,
        artifact_extraction_supported=False,
        structured_output_supported=False,
        status_normalization_supported=False,
        discovery_evidence_refs=qualification_refs,
        limitations=(
            "functional repository read/write remain unqualified before D2-S3 science",
            "R2 preturn PASS establishes platform/profile/thread readiness only",
        ),
    )

    retry = _sealed(
        ProofRetryPolicy,
        "p5a-d2s3-retry",
        provenance,
        max_invalid_replacement_attempts=0,
        require_same_semantic_proof_identity=True,
        allowed_technical_reason_codes=(),
    )
    amendment = _sealed(
        AmendmentPolicy,
        "p5a-d2s3-amendment",
        provenance,
        allow_editorial=False,
        normative_pre_outcome_requires_refreeze=True,
        normative_post_outcome_requires_new_lineage=True,
    )
    independence = _sealed(
        IndependencePolicy,
        "p5a-d2s3-independence",
        provenance,
        required_dimensions=(),
        forbidden_shared_ancestor_classes=(),
    )
    admission = _sealed(
        EvidenceAdmissionPolicy,
        "p5a-d2s3-evidence-admission",
        provenance,
        accepted_source_classes=("codex_p5_fx_001_d2s3",),
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
        "p5a-d2s3-decision-rule",
        provenance,
        pass_expression=DecisionExpression(op="ALL", children=pass_children),
        fail_expression=DecisionExpression(op="ANY", children=fail_children),
        missing_metric_behavior="INVALID",
        metric_conflict_behavior="INVALID",
    )
    proof = _sealed(
        ProofObligation,
        "p5a-d2s3-p5-fx-001-proof",
        provenance,
        lifecycle=ProofLifecycle.FROZEN,
        target_claim_id="p5a-d2s3-codex-functional-qualification",
        proposition=(
            "The exact D2-S3 official Codex harness completes P5-FX-001 within "
            "the frozen workspace, mutation, authority and evidence contract."
        ),
        assumptions=(
            "exact official D2-S3 harness identity remains unchanged",
            "R2 platform preturn evidence remains exact and unconsumed",
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
        stop_conditions=("first terminal attempt only", "timeout at 90 seconds"),
    )

    equivalence = _sealed(
        AgentEquivalencePolicy,
        "p5a-d2s3-agent-equivalence",
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

    authority_policy = _sealed(
        AuthorityPolicy,
        "p5a-d2s3-p5-fx-001-authority-policy",
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
        "p5a-d2s3-p5-fx-001-qualification-grant",
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
            "git:g2e/docs/P5A_D2S3_R2_SCIENTIFIC_AUTHORIZATION_MACRO_GATE.md"
        ),
    )

    binding = _sealed(
        AgentBinding,
        "p5a-d2s3-final-agent-binding",
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
            f"r2_report_sha256:{R2_REPORT_SHA256}",
            "workspace_pre:TASK.md,input.json",
            "workspace_only_post_addition:result.json",
            "network:DENY",
            "interactive_approval:DENY",
            "single_scientific_attempt",
            "turn_timeout_seconds:90",
        ),
        authority_scope=GRANTED_AUTHORITY,
        resolved_at="2026-09-22T11:30:00Z",
        resolution_ref="p5a-d2s3-successor-final-admission",
    )

    execution_config = {
        "study_id": STUDY_ID,
        "attempt_id": ATTEMPT_ID,
        "fixture_id": "P5-FX-001",
        "input_sha256": INPUT_SHA256,
        "task_sha256": TASK_SHA256,
        "task_text_sha256": TASK_SHA256,
        "harness_sha256": HARNESS_SHA256,
        "helper_sha256": HELPER_SHA256,
        "release_tag": RELEASE_TAG,
        "source_commit": SOURCE_COMMIT,
        "schema_inventory_digest": schema_digest,
        "r2_report_sha256": R2_REPORT_SHA256,
        "r2_preflight_evidence_sha256": R2_PREFLIGHT_EVIDENCE_SHA256,
        "proof_ref": proof.exact_ref().model_dump(mode="json"),
        "manifest_ref": manifest.exact_ref().model_dump(mode="json"),
        "authority_policy_ref": authority_policy.exact_ref().model_dump(mode="json"),
        "qualification_grant_ref": grant.exact_ref().model_dump(mode="json"),
        "agent_binding_ref": binding.exact_ref().model_dump(mode="json"),
        "pre_workspace": ["TASK.md", "input.json"],
        "only_permitted_post_addition": "result.json",
        "allowed_read_paths": list(READ_PATHS),
        "allowed_write_paths": list(WRITE_PATHS),
        "authority_scope": list(GRANTED_AUTHORITY),
        "network_allowed": False,
        "interactive_approval_allowed": False,
        "timeouts": {
            "startup_seconds": 12,
            "turn_seconds": 90,
            "verifier_seconds": 10,
        },
        "max_invalid_replacement_attempts": 0,
    }
    config_hash = sha256_json(execution_config)

    attempt = _sealed(
        ExecutionAttemptEnvelope,
        "p5a-d2s3-predispatch-attempt-envelope",
        provenance,
        attempt_id=ATTEMPT_ID,
        proof_ref=proof.exact_ref(),
        state=AttemptState.LOCKED,
        implementation_ref=f"external-codex-app-server-stdio:sha256:{HARNESS_SHA256}",
        config_hash=config_hash,
        artifact_refs=(),
        data_refs=(
            f"sha256:{INPUT_SHA256}",
            f"sha256:{TASK_SHA256}",
            f"sha256:{R2_REPORT_SHA256}",
            f"sha256:{R2_PREFLIGHT_EVIDENCE_SHA256}",
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

    return {
        "schema": "G2E-P5A-D2S3-SUCCESSOR-FINAL-ADMISSION-v1",
        "study_id": STUDY_ID,
        "attempt_id": ATTEMPT_ID,
        "successor_manifest": manifest.model_dump(mode="json"),
        "decision_rule": decision.model_dump(mode="json"),
        "retry_policy": retry.model_dump(mode="json"),
        "amendment_policy": amendment.model_dump(mode="json"),
        "independence_policy": independence.model_dump(mode="json"),
        "evidence_admission_policy": admission.model_dump(mode="json"),
        "proof_obligation": proof.model_dump(mode="json"),
        "agent_equivalence_policy": equivalence.model_dump(mode="json"),
        "authority_policy": authority_policy.model_dump(mode="json"),
        "qualification_authority_grant": grant.model_dump(mode="json"),
        "final_agent_binding": binding.model_dump(mode="json"),
        "predispatch_attempt": attempt.model_dump(mode="json"),
        "execution_config": execution_config,
        "execution_config_hash": config_hash,
        "fixture": {
            "input": payload,
            "input_sha256": INPUT_SHA256,
            "task_text": task_text,
            "task_sha256": TASK_SHA256,
        },
        "refs": {
            "manifest": manifest.exact_ref().model_dump(mode="json"),
            "proof": proof.exact_ref().model_dump(mode="json"),
            "equivalence_policy": equivalence.exact_ref().model_dump(mode="json"),
            "authority_policy": authority_policy.exact_ref().model_dump(mode="json"),
            "qualification_grant": grant.exact_ref().model_dump(mode="json"),
            "final_agent_binding": binding.exact_ref().model_dump(mode="json"),
            "predispatch_attempt": attempt.exact_ref().model_dump(mode="json"),
        },
        "r2_binding_sha256": sha256_file(R2_BINDING_PATH),
        "scientific_attempts_authorized_after_macro_gate": 1,
        "automatic_retry_authorized": False,
        "model_turn_executed_during_qualification": False,
        "runtime_adapter_authorized": False,
    }


def verify_successor_admission(pack: dict, discovery_report: dict) -> None:
    discovery = validate_discovery(discovery_report)
    expected = build_successor_admission(discovery)
    if pack != expected:
        raise ValueError("successor admission deterministic mismatch")
    if pack["attempt_id"] != ATTEMPT_ID:
        raise ValueError("attempt identity drift")
    if pack["execution_config"]["max_invalid_replacement_attempts"] != 0:
        raise ValueError("retry budget drift")
    if pack["execution_config"]["network_allowed"] is not False:
        raise ValueError("network policy drift")
    if pack["execution_config"]["interactive_approval_allowed"] is not False:
        raise ValueError("approval policy drift")
    if pack["scientific_attempts_authorized_after_macro_gate"] != 1:
        raise ValueError("scientific attempt authorization drift")
    if pack["automatic_retry_authorized"] is not False:
        raise ValueError("automatic retry drift")
    if pack["model_turn_executed_during_qualification"] is not False:
        raise ValueError("qualification executed model turn")


def materialize(discovery_path: Path, output_dir: Path) -> dict:
    discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
    pack = build_successor_admission(discovery)
    verify_successor_admission(pack, discovery)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "P5A_D2S3_SUCCESSOR_MANIFEST.json": pack["successor_manifest"],
        "P5A_D2S3_PROOF_OBLIGATION.json": pack["proof_obligation"],
        "P5A_D2S3_AUTHORITY_POLICY.json": pack["authority_policy"],
        "P5A_D2S3_QUALIFICATION_AUTHORITY_GRANT.json": pack["qualification_authority_grant"],
        "P5A_D2S3_FINAL_AGENT_BINDING.json": pack["final_agent_binding"],
        "P5A_D2S3_PREDISPATCH_ATTEMPT.json": pack["predispatch_attempt"],
        "P5A_D2S3_SUCCESSOR_FINAL_ADMISSION.json": pack,
    }
    for name, value in outputs.items():
        (output_dir / name).write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return pack


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--discovery", required=True)
    p.add_argument("--output-dir", required=True)
    args = p.parse_args()
    pack = materialize(Path(args.discovery), Path(args.output_dir))
    print(json.dumps({
        "manifest_ref": pack["refs"]["manifest"],
        "proof_ref": pack["refs"]["proof"],
        "final_agent_binding_ref": pack["refs"]["final_agent_binding"],
        "predispatch_attempt_ref": pack["refs"]["predispatch_attempt"],
        "execution_config_hash": pack["execution_config_hash"],
        "scientific_attempts_authorized_after_macro_gate":
            pack["scientific_attempts_authorized_after_macro_gate"],
        "model_turn_executed_during_qualification":
            pack["model_turn_executed_during_qualification"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
