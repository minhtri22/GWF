from __future__ import annotations

import importlib.util
from pathlib import Path

from g2e import AgentBinding, AgentCapabilityManifest
from g2e.schemas import validate_agent_binding_identity


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "g2e" / "docs" / "P5A_D2_QUALIFICATION_AUTHORITY_ADMISSION_PREIMPLEMENTATION.md"
D2_BUILDER = ROOT / "scripts" / "g2e" / "p5a_d2_p5_fx_001_preregister.py"
MANIFEST_MATERIALIZER = ROOT / "scripts" / "g2e" / "p5a_materialize_codex_d1_manifest.py"
D1_EVIDENCE = ROOT / "g2e" / "docs" / "P5A_CODEX_D1_EVIDENCE.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _text() -> str:
    return SPEC.read_text(encoding="utf-8")


def test_qa_q0_binds_exact_d2_f01_lineage():
    text = _text()
    required = (
        "15eeae4776a969cb0d64b9d55f33146e303161ec",
        "35603125876",
        "106343728888",
        "D2-F01",
        "8e275db790fe4c83061385f9988f4165f54d514611a44a4a555c5d01f6d3dbcd",
        "a5a9287d464d3d3450e9cf82d7866d45e9e2fc2921b0c28d938fd7257a3940f8",
        "eaeff7a8141697b2ecb824709277ba51db5e60643a722f2d06b3d5d3f6d4d4b4",
    )
    for item in required:
        assert item in text


def test_capability_and_qualification_authority_are_explicitly_distinct():
    text = _text()
    assert "authority_to_attempt(C)" in text
    assert "capability_available(C)" in text
    assert "A qualification grant is permission to create evidence. It is not evidence itself." in text
    assert "AgentCapability.available=true" in text


def test_qualification_authority_grant_contract_is_frozen():
    text = _text()
    required = (
        "QualificationAuthorityGrant",
        "qualification_authority_grant",
        "QUALIFICATION_ONLY",
        "proof_ref",
        "capability_manifest_ref",
        "attempt_id",
        "target_capability_ids",
        "authority_policy_ref",
        "granted_role",
        "granted_authority_scope",
        "allowed_read_paths",
        "allowed_write_paths",
        "network_allowed: false",
        "interactive_approval_allowed: false",
        "single_attempt: true",
        "may_imply_capability_available: false",
        "may_be_reused_for_operational_binding: false",
    )
    for item in required:
        assert item in text


def test_prd14_parent_authority_rule_is_preserved():
    text = _text()
    assert "delegated authority ≤ parent authority" in text
    assert "qualification_executor" in text
    assert "READ_FROZEN_FIXTURE" in text
    assert "WRITE_DESIGNATED_OUTPUT" in text
    assert "No generic:" in text
    for forbidden_scope in ("repository write", "arbitrary shell", "network", "approval bypass"):
        assert forbidden_scope in text


def test_agent_binding_extension_preserves_normal_semantics():
    text = _text()
    assert "qualification_authority_ref: ExactRef | None = None" in text
    assert "qualification_target_capability_ids: tuple[str, ...] = ()" in text
    assert "Normal binding:" in text
    assert "retains current P1.4 validation unchanged" in text
    assert "required_capability_ids" in text
    assert "qualification_target_capability_ids" in text


def test_qualification_target_semantics_do_not_self_qualify_capability():
    text = _text()
    assert "capability exists" in text
    assert "available == false" in text
    assert "capability is named by exact QualificationAuthorityGrant" in text
    assert "grant itself does not mutate the manifest" in text
    assert "separate manifest revision proposal" in text


def test_p5_fx_001_grant_scope_is_exact_and_bounded():
    text = _text()
    exact = (
        "p5a-d2-p5-fx-001-attempt-001",
        "repository_read",
        "repository_write",
        "qualification_executor",
        "READ_FROZEN_FIXTURE",
        "WRITE_DESIGNATED_OUTPUT",
        "input.json",
        "TASK.md",
        "result.json",
    )
    for item in exact:
        assert item in text


def test_existing_d2_f01_blocker_is_reproducible_from_qualified_state():
    d2 = _load(D2_BUILDER, "d2_builder_qa_authority")
    materializer = _load(MANIFEST_MATERIALIZER, "d1_manifest_qa_authority")
    manifest = materializer.build_manifest(materializer.load_d1_evidence(D1_EVIDENCE))
    assert isinstance(manifest, AgentCapabilityManifest)

    report = d2.build_contract()
    assert manifest.max_authority_scope == ()
    assert set(report["required_execution_authority"]) == {
        "READ_FROZEN_FIXTURE",
        "WRITE_DESIGNATED_OUTPUT",
    }
    assert report["execution_admission"]["authorized"] is False
    assert report["execution_admission"]["reason"] == "D2-F01"


def test_current_p1_4_schema_has_no_hidden_qualification_backdoor():
    assert "qualification_authority_ref" not in AgentBinding.model_fields
    assert "qualification_target_capability_ids" not in AgentBinding.model_fields
    source = Path(validate_agent_binding_identity.__code__.co_filename).read_text(encoding="utf-8")
    assert "qualification_authority" not in source


def test_future_validator_must_be_explicit_not_normal_path_weakening():
    text = _text()
    assert "MUST NOT silently weaken" in text
    assert "validate_agent_binding_identity()" in text
    assert "validate_qualification_agent_binding_identity" in text


def test_forbidden_designs_are_frozen():
    text = _text()
    forbidden_requirements = (
        "set `repository_read/write=true` to authorize their own test",
        "widen the D1 manifest `max_authority_scope` before evidence",
        "treat a QualificationAuthorityGrant as capability evidence",
        "hide qualification authority in prompt/config/environment/GWF metadata",
        "reuse a qualification grant for production",
        "let executor success mutate manifest availability",
    )
    for item in forbidden_requirements:
        assert item in text


def test_zero_fresh_scope_has_no_model_turn_runtime_adapter_or_core_patch():
    text = _text()
    assert "D2 model turn:** PROHIBITED" in text
    assert "Codex runtime adapter:** NOT AUTHORIZED" in text
    assert "Core/runtime implementation:** NOT AUTHORIZED BY THIS SPEC PHASE" in text

    forbidden_patterns = (
        "src/g2e/*codex*",
        "src/g2e/*chatgpt*",
        "src/gwr/*codex*",
        "src/gwr/*chatgpt*",
    )
    hits: list[str] = []
    for pattern in forbidden_patterns:
        hits.extend(str(path.relative_to(ROOT)) for path in ROOT.glob(pattern))
    assert hits == []


def test_expected_verdict_is_spec_pass_implementation_required():
    text = _text()
    assert "SPEC_PASS_IMPLEMENTATION_REQUIRED" in text
    assert "P1.5 — Qualification Attempt Authority" in text
    assert "ONLY THEN" in text
    assert "one D2 model turn" in text
