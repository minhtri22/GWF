from __future__ import annotations

from pathlib import Path

from g2e.schemas import ExecutionAttemptEnvelope, ExecutionResult, RuntimeCapabilityManifest, RuntimeMode, SCHEMA_REGISTRY


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "g2e" / "docs" / "P1_4_AGENT_PROFILE_BINDING_PREIMPLEMENTATION.md"


def _spec() -> str:
    return SPEC.read_text(encoding="utf-8")


def test_p1_4_origin_binds_exact_p5_blocker_evidence():
    text = _spec()
    required = (
        "a799a6039498dfd4196b9874f230da48fdbb42c1",
        "35587111264",
        "106292892218",
        "10632522432",
        "6283bf4c033828b2915bf3029ed9b3e0ea9d0870",
        "P5-F01",
        "P5-F02",
        "P1.4_AGENT_PROFILE_BINDING_IDENTITY",
    )
    for item in required:
        assert item in text


def test_p1_4_reuses_runtime_and_execution_identity_without_reinterpretation():
    text = _spec()
    runtime_fields = set(RuntimeCapabilityManifest.model_fields)
    assert set(RuntimeMode) == {RuntimeMode.STANDALONE, RuntimeMode.GWF}
    assert "runtime_id" in runtime_fields
    assert "agent_app" not in runtime_fields
    assert "RuntimeCapabilityManifest" in text
    assert "MUST NOT reinterpret" in text


def test_p1_4_schema_gap_is_real_before_implementation():
    assert "agent_capability_manifest" not in SCHEMA_REGISTRY
    assert "agent_equivalence_policy" not in SCHEMA_REGISTRY
    assert "agent_binding" not in SCHEMA_REGISTRY
    assert "agent_binding_ref" not in ExecutionAttemptEnvelope.model_fields
    assert "agent_binding_ref" not in ExecutionResult.model_fields


def test_p1_4_minimal_schema_surface_is_frozen():
    text = _spec()
    required = (
        "AgentProfileAvailability",
        "BindingMode",
        "AgentCapability",
        "AgentCapabilityManifest",
        "AgentEquivalencePolicy",
        "AgentBinding",
        "agent_binding_ref",
        "validate_agent_binding_identity",
    )
    for item in required:
        assert item in text


def test_p1_4_backward_compatibility_is_frozen():
    text = _spec()
    assert "non-agent attempts may omit it" in text
    assert "non-agent results may omit it" in text
    assert "if any of" in text and "agent_app/provider_ref/model_ref/harness_ref/transport_ref" in text
    assert "P3/P4 result construction must preserve the binding ref when present" in text


def test_p1_4_fail_closed_matrix_is_frozen():
    text = _spec()
    required = (
        "AVAILABLE without discovery evidence",
        "available capability without qualification ref",
        "duplicate capability IDs",
        "agent attempt without binding ref",
        "binding manifest-ref mismatch",
        "resolved attempt ID mismatch",
        "required unavailable/missing capability",
        "authority escalation beyond manifest ceiling",
        "result binding/attempt/identity mismatch",
    )
    for item in required:
        assert item in text


def test_p1_4_provider_neutral_scope_is_explicit():
    text = _spec()
    forbidden_runtime = (
        "Codex classes/drivers/commands",
        "ChatGPT classes/drivers/commands",
        "provider API calls",
        "MCP server/client",
        "ARC transport",
        "harness session creation",
        "profile discovery implementation",
    )
    for item in forbidden_runtime:
        assert item in text
    assert "agent_app=\"codex\"" in text
    assert "agent_app=\"chatgpt\"" in text
    assert "no P1.4 code may branch on either value" in text


def test_p1_4_zero_implementation_scope_has_no_provider_runtime_files():
    patterns = (
        "src/g2e/*codex*",
        "src/g2e/*chatgpt*",
        "src/gwr/*codex*",
        "src/gwr/*chatgpt*",
    )
    hits: list[str] = []
    for pattern in patterns:
        hits.extend(str(path.relative_to(ROOT)) for path in ROOT.glob(pattern))
    assert hits == []
