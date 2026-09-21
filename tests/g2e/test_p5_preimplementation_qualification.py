from __future__ import annotations

import hashlib
import json
from pathlib import Path

from g2e.schemas import ExecutionAttemptEnvelope, ExecutionResult, RuntimeCapabilityManifest, RuntimeMode


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "g2e" / "docs" / "P5_PREIMPLEMENTATION_QUALIFICATION.md"


def _spec() -> str:
    return SPEC.read_text(encoding="utf-8")


def _fx_input(seed: str = "g2e-p5-agent-profile-v1", count: int = 32) -> dict:
    values: list[int] = []
    block = seed.encode("utf-8")
    while len(values) < count:
        block = hashlib.sha256(block).digest()
        for i in range(0, len(block), 4):
            chunk = block[i : i + 4]
            if len(chunk) < 4:
                continue
            unsigned = int.from_bytes(chunk, "big", signed=False)
            values.append(unsigned - (1 << 31))
            if len(values) == count:
                break
    return {
        "generator_version": "p5-fx-001-v1",
        "seed": seed,
        "values": values,
    }


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _candidate_from_input(payload: dict) -> dict:
    values = payload["values"]
    return {
        "count": len(values),
        "sum": sum(values),
        "sorted_unique_values": sorted(set(values)),
        "input_sha256": hashlib.sha256(_canonical_bytes(payload)).hexdigest(),
    }


def _verify(payload: dict, candidate: dict) -> bool:
    expected = _candidate_from_input(payload)
    return candidate == expected


def test_p5_q0_exact_dependency_authority_is_frozen():
    text = _spec()
    required = {
        "f8d43320ed615c80f21c0f3bfdfa3f6dd951205d",
        "22c3a6becd1175d90d840d94ba0dd39d5374578b",
        "8072310b3220f94e765b992d91a1904de67348cb",
        "a0e481e13434e7b2c22df381261cd6820c9bf41a",
        "7773f998f50ac252ac92b3d92329789666d57ef9",
        "d224652753378d9a6fb6aec94f5344f63a52b0c1",
        "62b4ab6717bc6c0a00f3670c73024df5a6ad41ca",
        "fe6669dabc77c03474bbbffc76bb1e8b746c6ffc",
        "1f6d49957c0c0dffa7b83c11caebed4ab2b90e0b",
        "fbae7dcf6484556a1acf339f8187f8a2092faef0",
        "660cfbb98ab2066e3fb94adda7657087de9ab26f",
    }
    missing = sorted(item for item in required if item not in text)
    assert not missing, missing
    assert "P4L is not a P5 admission dependency" in text


def test_p5_q1_q2_codex_and_chatgpt_are_independent_qualification_subjects():
    text = _spec()
    assert "Codex actual harness" in text
    assert "ChatGPT actual harness" in text
    assert "Codex supports X" in text
    assert "ChatGPT supports X" in text
    assert "one app or one harness revision never migrates silently to another" in text


def test_p5_f01_runtime_manifest_is_not_an_agent_profile_manifest():
    fields = set(RuntimeCapabilityManifest.model_fields)
    assert set(RuntimeMode) == {RuntimeMode.STANDALONE, RuntimeMode.GWF}
    assert "runtime_id" in fields
    assert "runtime_mode" in fields
    assert "agent_app" not in fields
    assert "harness_ref" not in fields
    assert "P5-F01" in _spec()
    assert "fake runtime backend" in _spec()


def test_p5_f02_binding_identity_gap_is_explicit_and_not_hidden():
    attempt_fields = set(ExecutionAttemptEnvelope.model_fields)
    result_fields = set(ExecutionResult.model_fields)
    for field in ("agent_app", "provider_ref", "model_ref", "harness_ref", "transport_ref"):
        assert field in attempt_fields
        assert field in result_fields
    assert "agent_binding_ref" not in attempt_fields

    text = _spec()
    assert "P5-F02" in text
    assert "P1.4 — Agent Profile / Binding Identity" in text
    assert "hide binding semantics inside" in text
    assert "config_hash" in text


def test_p5_q5_authority_and_secret_boundary_is_fail_closed():
    text = _spec()
    required = (
        "no self-elevation",
        "no terminal verdict rewrite",
        "no hidden expansion of write scope",
        "no raw secret in AgentCapabilityManifest",
        "hidden chain-of-thought is not required evidence",
    )
    for phrase in required:
        assert phrase in text


def test_p5_q6_independence_is_prospective_not_post_outcome():
    text = _spec()
    assert "cross-profile agreement as independent scientific confirmation" in text
    assert "alone never proves independence" in text
    assert "post-outcome relabeling of dimensions is forbidden" in text


def test_p5_q7_fail_closed_matrix_contains_no_silent_fallback():
    text = _spec()
    required = (
        "UNSUPPORTED_CAPABILITY",
        "authority denial / no dispatch",
        "independence requirement unresolved",
        "never a silent fallback for a frozen binding",
        "no scientific PASS implication",
    )
    for phrase in required:
        assert phrase in text


def test_p5_q8_fixture_is_deterministic_and_verifier_is_outcome_blind():
    first = _fx_input()
    second = _fx_input()
    assert first == second
    assert len(first["values"]) == 32

    candidate = _candidate_from_input(first)
    assert _verify(first, candidate)

    tampered = dict(candidate)
    tampered["sum"] += 1
    assert not _verify(first, tampered)

    text = _spec()
    assert "No expected" in text and "result.json" in text
    assert "recomputes every required field" in text
    assert "No network access is required by the fixture. No secret is required." in text


def test_p5_q9_zero_implementation_scope_has_no_runtime_adapter_files():
    forbidden_patterns = (
        "src/g2e/*codex*",
        "src/g2e/*chatgpt*",
        "src/gwr/*codex*",
        "src/gwr/*chatgpt*",
    )
    hits = []
    for pattern in forbidden_patterns:
        hits.extend(str(path.relative_to(ROOT)) for path in ROOT.glob(pattern))
    assert hits == []


def test_preimplementation_adjudication_does_not_authorize_runtime():
    text = _spec()
    assert "SPEC_PASS_RUNTIME_BLOCKED" in text
    assert "P5 runtime implementation remains NOT AUTHORIZED" in text
    assert "P1.4 is a subsequent separately qualified step" in text
