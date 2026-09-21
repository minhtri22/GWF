from __future__ import annotations

import importlib.util
from pathlib import Path

from g2e import AgentCapabilityManifest, validate_agent_binding_identity


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "g2e" / "docs" / "P5A_D2_P5_FX_001_PREIMPLEMENTATION_QUALIFICATION.md"
BUILDER = ROOT / "scripts" / "g2e" / "p5a_d2_p5_fx_001_preregister.py"
MANIFEST_MATERIALIZER = ROOT / "scripts" / "g2e" / "p5a_materialize_codex_d1_manifest.py"
D1_EVIDENCE = ROOT / "g2e" / "docs" / "P5A_CODEX_D1_EVIDENCE.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_d2_spec_freezes_zero_fresh_boundary():
    text = SPEC.read_text(encoding="utf-8")
    required = (
        "Model turn:** PROHIBITED",
        "Codex runtime adapter:** NOT AUTHORIZED",
        "P5-FX-001",
        "max_invalid_replacement_attempts = 0",
        "D2-F01",
        "SPEC_PASS_EXECUTION_BLOCKED",
        "No rerun-until-PASS",
    )
    for item in required:
        assert item in text


def test_preregistration_is_deterministic():
    builder = _load(BUILDER, "p5a_d2_builder")
    a = builder.build_contract()
    b = builder.build_contract()
    assert a == b
    assert len(a["fixture"]["input"]["values"]) == 32
    assert len(a["fixture"]["input_sha256"]) == 64
    assert len(a["fixture"]["task_sha256"]) == 64


def test_exact_proof_and_preflight_binding_refs_are_frozen():
    builder = _load(BUILDER, "p5a_d2_builder_refs")
    report = builder.build_contract()
    assert report["refs"]["proof_obligation"]["object_id"] == "p5a-d2-p5-fx-001-proof"
    assert report["refs"]["preflight_agent_binding"]["object_id"] == "p5a-d2-preflight-binding"
    assert report["preflight_agent_binding"]["binding_mode"] == "FROZEN"
    assert report["preflight_agent_binding"]["authority_scope"] == []


def test_workspace_prompt_and_side_effect_boundaries_are_frozen():
    builder = _load(BUILDER, "p5a_d2_builder_workspace")
    report = builder.build_contract()
    assert report["fixture"]["pre_workspace"] == ["TASK.md", "input.json"]
    assert report["fixture"]["only_permitted_post_addition"] == "result.json"
    assert report["approval_policy"]["network"] == "DENY"
    assert report["approval_policy"]["interactive_approval"] == "DENY"
    assert report["approval_policy"]["allowed_writes"] == ["result.json"]
    assert report["timeouts"] == {
        "startup_seconds": 12,
        "turn_seconds": 90,
        "verifier_seconds": 10,
    }


def test_retry_and_amendment_are_no_rescue():
    builder = _load(BUILDER, "p5a_d2_builder_no_rescue")
    report = builder.build_contract()
    assert report["retry_policy"]["max_invalid_replacement_attempts"] == 0
    assert report["amendment_policy"]["normative_pre_outcome_requires_refreeze"] is True
    assert report["amendment_policy"]["normative_post_outcome_requires_new_lineage"] is True


def test_d2_f01_is_real_under_exact_qualified_manifest():
    builder = _load(BUILDER, "p5a_d2_builder_blocker")
    materializer = _load(MANIFEST_MATERIALIZER, "p5a_manifest_materializer_for_d2")
    manifest = materializer.build_manifest(materializer.load_d1_evidence(D1_EVIDENCE))
    assert isinstance(manifest, AgentCapabilityManifest)
    assert manifest.exact_ref() == builder.MANIFEST_REF
    assert manifest.max_authority_scope == ()

    report = builder.build_contract()
    required = set(report["required_execution_authority"])
    assert required == {"READ_FROZEN_FIXTURE", "WRITE_DESIGNATED_OUTPUT"}
    assert not required.issubset(set(manifest.max_authority_scope))
    assert report["execution_admission"]["authorized"] is False
    assert report["execution_admission"]["reason"] == "D2-F01"
    assert report["execution_admission"]["final_execution_agent_binding_frozen"] is False


def test_preflight_identity_binding_remains_valid_for_structural_identity_only():
    builder = _load(BUILDER, "p5a_d2_builder_binding")
    materializer = _load(MANIFEST_MATERIALIZER, "p5a_manifest_materializer_binding")
    manifest = materializer.build_manifest(materializer.load_d1_evidence(D1_EVIDENCE))
    report = builder.build_contract()

    from g2e import AgentBinding, AgentEquivalencePolicy, ExecutionAttemptEnvelope, AttemptState, Provenance
    from g2e.canonical import ExactRef

    equivalence = AgentEquivalencePolicy.parse_authoritative(report["agent_equivalence_policy"])
    binding = AgentBinding.parse_authoritative(report["preflight_agent_binding"])

    attempt = ExecutionAttemptEnvelope.sealed(
        object_id="p5a-d2-preflight-attempt-envelope",
        revision_id="p5-fx-001-v1",
        provenance=Provenance(
            created_by="g2e-p5a-d2-preregister",
            created_at="2026-09-21T12:05:44.250506Z",
        ),
        attempt_id=binding.resolved_attempt_id,
        proof_ref=ExactRef(**report["refs"]["proof_obligation"]),
        state=AttemptState.CREATED,
        implementation_ref="p5a-d2-preregistration-only",
        config_hash="0" * 64,
        agent_app=binding.agent_app,
        provider_ref=binding.provider_ref,
        model_ref=binding.model_ref,
        harness_ref=binding.harness_ref,
        transport_ref=binding.transport_ref,
        agent_binding_ref=binding.exact_ref(),
        retry_policy_ref=ExactRef(**report["refs"]["retry_policy"]),
        authority_scope=(),
    )
    validate_agent_binding_identity(manifest, equivalence, binding, attempt)


def test_builder_has_no_codex_execution_path():
    source = BUILDER.read_text(encoding="utf-8")
    forbidden = (
        "subprocess",
        "Popen(",
        "os.system",
        "shutil.which",
        "thread/start",
        "turn/start",
        "codex app-server",
    )
    for token in forbidden:
        assert token not in source


def test_no_d2_outcome_artifact_is_tracked():
    forbidden = (
        ROOT / "P5A_D2_EXECUTION_RESULT.json",
        ROOT / "P5A_D2_ADJUDICATION.json",
        ROOT / "P5A_D2_RESULT.json",
    )
    assert not any(path.exists() for path in forbidden)
