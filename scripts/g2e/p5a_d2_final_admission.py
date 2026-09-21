from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from g2e import (
    AgentBinding,
    AgentCapabilityManifest,
    AgentEquivalencePolicy,
    AttemptState,
    AuthorityAction,
    AuthorityPolicy,
    BindingMode,
    ExecutionAttemptEnvelope,
    ProofObligation,
    Provenance,
    QualificationAuthorityGrant,
    validate_qualification_agent_binding_identity,
)


ROOT = Path(__file__).resolve().parents[2]
PREREG_PATH = ROOT / "scripts" / "g2e" / "p5a_d2_p5_fx_001_preregister.py"
MANIFEST_MATERIALIZER_PATH = ROOT / "scripts" / "g2e" / "p5a_materialize_codex_d1_manifest.py"
D1_EVIDENCE_PATH = ROOT / "g2e" / "docs" / "P5A_CODEX_D1_EVIDENCE.json"

ATTEMPT_ID = "p5a-d2-p5-fx-001-attempt-001"
REVISION_ID = "p5-fx-001-v1"
HARNESS_SHA256 = "a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8"
INPUT_SHA256 = "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
TASK_SHA256 = "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"
PROOF_HASH = "8e275db790fe4c83061385f9988f4165f54d514611a44a4a555c5d01f6d3dbcd"
MANIFEST_HASH = "585d59b32457484e8d4706c3e79a94398569ab4bc3e39ff8fca5502541ece5c5"
QUALIFICATION_TARGETS = ("repository_read", "repository_write")
REQUIRED_PREREQUISITES = (
    "app_server_launch",
    "jsonrpc_initialize",
    "thread_lifecycle_surface",
    "turn_stream_surface",
    "external_session_attribution_surface",
)
GRANTED_AUTHORITY = ("READ_FROZEN_FIXTURE", "WRITE_DESIGNATED_OUTPUT")
READ_PATHS = ("input.json", "TASK.md")
WRITE_PATHS = ("result.json",)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _provenance() -> Provenance:
    return Provenance(
        created_by="g2e-p5a-d2-final-admission",
        created_at="2026-09-21T13:45:00Z",
        source_refs=(
            "git:1811fb1e7b2d703a4cfae776b12832efd8c4e503:g2e/docs/P1_5_QUALIFICATION_ATTEMPT_AUTHORITY_EVIDENCE.json",
            "git:aae2de936f5bc4dee20be4ce614e8f4938994bc1:g2e/docs/P5A_D2_P5_FX_001_PREIMPLEMENTATION_EVIDENCE.json",
        ),
        derivation="Prospective final D2 admission materialization; no model turn",
    )


def _sealed(cls, object_id: str, **kwargs):
    return cls.sealed(
        object_id=object_id,
        revision_id=REVISION_ID,
        provenance=_provenance(),
        **kwargs,
    )


def inherited_contract():
    prereg = _load_module(PREREG_PATH, "p5a_d2_prereg_for_final_admission")
    materializer = _load_module(MANIFEST_MATERIALIZER_PATH, "p5a_d1_manifest_for_final_admission")
    report = prereg.build_contract()
    manifest = materializer.build_manifest(materializer.load_d1_evidence(D1_EVIDENCE_PATH))
    proof = ProofObligation.parse_authoritative(report["proof_obligation"])
    equivalence = AgentEquivalencePolicy.parse_authoritative(report["agent_equivalence_policy"])
    if manifest.content_hash != MANIFEST_HASH:
        raise ValueError("D1 manifest exact ref drift")
    if proof.content_hash != PROOF_HASH:
        raise ValueError("P5-FX-001 proof exact ref drift")
    if report["fixture"]["input_sha256"] != INPUT_SHA256:
        raise ValueError("P5-FX-001 input hash drift")
    if report["fixture"]["task_sha256"] != TASK_SHA256:
        raise ValueError("P5-FX-001 task hash drift")
    return report, manifest, proof, equivalence


def build_final_admission() -> dict:
    report, manifest, proof, equivalence = inherited_contract()

    authority_policy = _sealed(
        AuthorityPolicy,
        "p5a-d2-p5-fx-001-authority-policy",
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
        "p5a-d2-p5-fx-001-qualification-grant",
        proof_ref=proof.exact_ref(),
        capability_manifest_ref=manifest.exact_ref(),
        attempt_id=ATTEMPT_ID,
        target_capability_ids=QUALIFICATION_TARGETS,
        authority_policy_ref=authority_policy.exact_ref(),
        granted_role="qualification_executor",
        granted_authority_scope=GRANTED_AUTHORITY,
        allowed_read_paths=READ_PATHS,
        allowed_write_paths=WRITE_PATHS,
        qualification_lineage_ref="git:926d6a46344e8ac4822907fdc6b597f8d6ba6feb:g2e/LINEAGE.md#G2E-P1.5",
    )

    binding = _sealed(
        AgentBinding,
        "p5a-d2-final-agent-binding",
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
            "workspace_pre:TASK.md,input.json",
            "workspace_only_post_addition:result.json",
            "network:DENY",
            "interactive_approval:DENY",
            "single_scientific_attempt",
            "turn_timeout_seconds:90",
        ),
        authority_scope=GRANTED_AUTHORITY,
        resolved_at="2026-09-21T13:45:00Z",
        resolution_ref="p5a-d2-final-zero-fresh-admission",
    )

    execution_config = {
        "fixture_id": "P5-FX-001",
        "input_sha256": INPUT_SHA256,
        "task_sha256": TASK_SHA256,
        "harness_sha256": HARNESS_SHA256,
        "proof_ref": proof.exact_ref().model_dump(mode="json"),
        "manifest_ref": manifest.exact_ref().model_dump(mode="json"),
        "authority_policy_ref": authority_policy.exact_ref().model_dump(mode="json"),
        "qualification_grant_ref": grant.exact_ref().model_dump(mode="json"),
        "agent_binding_ref": binding.exact_ref().model_dump(mode="json"),
        "pre_workspace": report["fixture"]["pre_workspace"],
        "only_permitted_post_addition": report["fixture"]["only_permitted_post_addition"],
        "allowed_read_paths": list(READ_PATHS),
        "allowed_write_paths": list(WRITE_PATHS),
        "authority_scope": list(GRANTED_AUTHORITY),
        "network_allowed": False,
        "interactive_approval_allowed": False,
        "timeouts": report["timeouts"],
        "max_invalid_replacement_attempts": report["retry_policy"]["max_invalid_replacement_attempts"],
    }
    config_hash = _sha256_json(execution_config)

    attempt = _sealed(
        ExecutionAttemptEnvelope,
        "p5a-d2-predispatch-attempt-envelope",
        attempt_id=ATTEMPT_ID,
        proof_ref=proof.exact_ref(),
        state=AttemptState.LOCKED,
        implementation_ref=f"external-codex-app-server-stdio:sha256:{HARNESS_SHA256}",
        config_hash=config_hash,
        artifact_refs=(),
        data_refs=(f"sha256:{INPUT_SHA256}", f"sha256:{TASK_SHA256}"),
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

    capabilities = {cap.capability_id: cap.available for cap in manifest.capabilities}
    if capabilities["repository_read"] or capabilities["repository_write"]:
        raise ValueError("D1 target capability availability mutated before D2")

    return {
        "schema": "G2E-P5A-D2-FINAL-ADMISSION-v1",
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
        "workspace": {
            "pre": report["fixture"]["pre_workspace"],
            "only_permitted_post_addition": report["fixture"]["only_permitted_post_addition"],
            "allowed_read_paths": list(READ_PATHS),
            "allowed_write_paths": list(WRITE_PATHS),
        },
        "fresh_outcome_consumed": False,
        "model_turn_executed": False,
        "runtime_adapter_authorized": False,
        "d2_scientific_attempts_authorized_after_gate": 1,
    }


def materialize(output_dir: Path) -> dict:
    pack = build_final_admission()
    output_dir.mkdir(parents=True, exist_ok=True)
    objects = {
        "P5A_D2_AUTHORITY_POLICY.json": pack["authority_policy"],
        "P5A_D2_QUALIFICATION_AUTHORITY_GRANT.json": pack["qualification_authority_grant"],
        "P5A_D2_FINAL_AGENT_BINDING.json": pack["final_agent_binding"],
        "P5A_D2_PREDISPATCH_ATTEMPT.json": pack["predispatch_attempt"],
        "P5A_D2_FINAL_ADMISSION.json": pack,
    }
    for name, value in objects.items():
        (output_dir / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return pack


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize P5A D2 final zero-fresh admission graph")
    parser.add_argument("--output-dir", default="p5a_d2_final_admission")
    args = parser.parse_args()
    pack = materialize(Path(args.output_dir))
    print(json.dumps({
        "authority_policy_ref": pack["refs"]["authority_policy"],
        "qualification_grant_ref": pack["refs"]["qualification_authority_grant"],
        "final_agent_binding_ref": pack["refs"]["final_agent_binding"],
        "predispatch_attempt_ref": pack["refs"]["predispatch_attempt"],
        "execution_config_hash": pack["execution_config_hash"],
        "model_turn_executed": pack["model_turn_executed"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
