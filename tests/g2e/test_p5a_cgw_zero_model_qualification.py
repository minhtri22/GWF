from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "scripts" / "g2e" / "p5a_cgw_bridge_qualification.py"
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_cgw_local_zero_model_oneclick.ps1"


def _load():
    spec = importlib.util.spec_from_file_location("p5a_cgw_bridge", MODULE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_synthetic_q0_q7_core_pass_and_no_science():
    m = _load()
    report = m.run_synthetic_qualification()
    assert report["status"] == "SYNTHETIC_ZERO_MODEL_CORE_PASS"
    assert report["model_turn_executed"] is False
    assert report["scientific_attempt_created"] is False
    assert report["scientific_attempt_consumed"] is False
    assert report["functional_claim"] is False
    for gate in (
        "Q1_route_no_fallback",
        "Q2_request_response_correlation",
        "Q3_browser_binding_observability",
        "Q4_authority_preservation",
        "Q5_full_mode_mcp_binding",
        "Q6_observability_privacy",
        "Q7_failure_injection",
    ):
        assert report["gates"][gate]["pass"] is True
    assert report["gates"]["Q8_g2e_regression"]["pass"] is None


def test_bridge_config_is_loopback_full_mode_exact_connector_and_no_autoapproval():
    m = _load()
    config, _, _ = m.synthetic_fixture("full")
    result = m.project_bridge_config(config, m.canonical_bytes(config))
    assert result["valid"] is True
    p = result["projection"]
    assert p["host"] == "127.0.0.1"
    assert p["mode"] == "full"
    assert p["active_connector"] == "Codex Native2"
    assert p["auto_approve_tool_calls"] is False
    assert p["tunnel_config_present"] is True
    rendered = json.dumps(p)
    assert "SECRET_CONTROL_TOKEN" not in rendered
    assert "runtime.key" not in rendered
    assert "tunnel_" not in rendered


@pytest.mark.parametrize(
    "mutation,code",
    [
        (lambda c: c.update(host="0.0.0.0"), "CGW_HOST_NOT_LOOPBACK"),
        (lambda c: c.update(releaseVersion="9.9.9"), "CGW_RELEASE_VERSION"),
        (lambda c: c.update(autoApproveToolCalls=True), "CGW_AUTO_APPROVE_MUST_BE_FALSE"),
        (lambda c: c.update(appName="Codex Native"), "CGW_ACTIVE_CONNECTOR_AUTOMATIC"),
        (lambda c: c.pop("automaticTunnel"), "CGW_FULL_TUNNEL_CONFIG_MISSING"),
    ],
)
def test_bridge_config_fail_closed(mutation, code):
    m = _load()
    config, _, _ = m.synthetic_fixture("full")
    mutation(config)
    result = m.project_bridge_config(config)
    assert result["valid"] is False
    assert code in result["errors"]


def test_health_requires_idle_exact_service_version_mode_port():
    m = _load()
    config, health, _ = m.synthetic_fixture("full")
    cfg = m.project_bridge_config(config)["projection"]
    assert m.project_health(health, cfg)["valid"] is True
    health["active_browser_turns"] = 1
    bad = m.project_health(health, cfg)
    assert bad["valid"] is False
    assert "CGW_ACTIVE_BROWSER_TURNS" in bad["errors"]


def test_codex_route_must_point_openai_base_url_at_exact_loopback_bridge():
    m = _load()
    _, _, toml = m.synthetic_fixture()
    good = m.project_codex_route(toml, 17841)
    assert good["valid"] is True
    assert good["projection"]["openai_base_url"] == "http://127.0.0.1:17841/v1"
    bad = m.project_codex_route(
        'model_provider="openai"\nopenai_base_url="https://example.invalid/v1"\n',
        17841,
    )
    assert bad["valid"] is False
    assert "CODEX_OPENAI_BASE_URL_NOT_CGW" in bad["errors"]


def _trace():
    return [
        {
            "event": "codex_request",
            "request_id": "r1",
            "outer_thread_id": "th1",
            "outer_turn_id": "tu1",
            "bridge_mode": "full",
            "model": "chatgpt-web/high",
            "bridge_side_effects_performed": False,
        },
        {
            "event": "browser_submit",
            "request_id": "r1",
            "outer_thread_id": "th1",
            "outer_turn_id": "tu1",
            "browser_lease_id": "lease1",
            "chatgpt_turn_id": "chat1",
            "bridge_mode": "full",
            "model": "chatgpt-web/high",
            "bridge_side_effects_performed": False,
        },
        {
            "event": "terminal",
            "request_id": "r1",
            "outer_thread_id": "th1",
            "outer_turn_id": "tu1",
            "browser_lease_id": "lease1",
            "chatgpt_turn_id": "chat1",
            "bridge_mode": "full",
            "model": "chatgpt-web/high",
            "bridge_side_effects_performed": False,
        },
    ]


def test_route_trace_exact_cross_hop_binding():
    m = _load()
    result = m.validate_route_trace(_trace())
    assert result["valid"] is True
    assert result["outer_turn_id"] == "tu1"
    assert result["browser_lease_id"] == "lease1"
    assert len(result["trace_sha256"]) == 64


@pytest.mark.parametrize(
    "edit,reason",
    [
        (lambda x: x[1].update(outer_turn_id="other"), "TRACE_IDENTITY_MISMATCH:outer_turn_id"),
        (lambda x: x[2].update(browser_lease_id="other"), "TRACE_BROWSER_LEASE_MISMATCH"),
        (lambda x: x[2].update(chatgpt_turn_id="other"), "TRACE_CHATGPT_TURN_MISMATCH"),
        (lambda x: x[2].update(model="gpt-5.6-sol"), "TRACE_MODEL_SUBSTITUTION"),
        (lambda x: x[1].update(bridge_side_effects_performed=True), "BRIDGE_EXECUTED_LOCAL_SIDE_EFFECT"),
    ],
)
def test_route_trace_fail_closed(edit, reason):
    m = _load()
    trace = _trace()
    edit(trace)
    with pytest.raises(m.QualificationError, match=reason):
        m.validate_route_trace(trace)


def test_full_mode_tool_roundtrip_codex_is_executor():
    m = _load()
    digest = m.sha256_bytes(b"cap")
    event = {
        "outer_thread_id": "th",
        "outer_turn_id": "tu",
        "connector": m.CGW_AUTOMATIC_CONNECTOR,
        "capability_token_digest": digest,
        "tool_name": "read_file",
        "executor": "codex",
        "bridge_side_effects_performed": False,
        "invocation_id": "i1",
        "result_sha256": "a" * 64,
    }
    result = m.validate_tool_roundtrip(
        event,
        expected_thread="th",
        expected_turn="tu",
        expected_connector=m.CGW_AUTOMATIC_CONNECTOR,
        allowed_tools={"read_file"},
        expected_capability_digest=digest,
    )
    assert result["executor"] == "codex"


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("outer_turn_id", "wrong", "TOOL_TURN_MISMATCH"),
        ("connector", "Codex Native", "TOOL_CONNECTOR_MISMATCH"),
        ("tool_name", "shell_anything", "TOOL_NOT_IN_OUTER_CODEX_REGISTRY"),
        ("executor", "bridge", "TOOL_EXECUTOR_NOT_CODEX"),
        ("bridge_side_effects_performed", True, "BRIDGE_SIDE_EFFECT_FLAG_INVALID"),
    ],
)
def test_tool_roundtrip_fail_closed(field, value, reason):
    m = _load()
    digest = m.sha256_bytes(b"cap")
    event = {
        "outer_thread_id": "th",
        "outer_turn_id": "tu",
        "connector": m.CGW_AUTOMATIC_CONNECTOR,
        "capability_token_digest": digest,
        "tool_name": "read_file",
        "executor": "codex",
        "bridge_side_effects_performed": False,
    }
    event[field] = value
    with pytest.raises(m.QualificationError, match=reason):
        m.validate_tool_roundtrip(
            event,
            expected_thread="th",
            expected_turn="tu",
            expected_connector=m.CGW_AUTOMATIC_CONNECTOR,
            allowed_tools={"read_file"},
            expected_capability_digest=digest,
        )


def test_raw_capability_token_must_never_persist():
    m = _load()
    digest = m.sha256_bytes(b"cap")
    event = {
        "outer_thread_id": "th",
        "outer_turn_id": "tu",
        "connector": m.CGW_AUTOMATIC_CONNECTOR,
        "capability_token_digest": digest,
        "capability_token": "SECRET",
        "tool_name": "read_file",
        "executor": "codex",
        "bridge_side_effects_performed": False,
    }
    with pytest.raises(m.QualificationError, match="RAW_CAPABILITY_TOKEN_PERSISTED"):
        m.validate_tool_roundtrip(
            event,
            expected_thread="th",
            expected_turn="tu",
            expected_connector=m.CGW_AUTOMATIC_CONNECTOR,
            allowed_tools={"read_file"},
            expected_capability_digest=digest,
        )


def test_privacy_redaction_is_recursive():
    m = _load()
    raw = {
        "Authorization": "Bearer 123456789SECRET",
        "nested": {"api_key": "sk-abcdef123456789", "text": "Bearer ABCDEFGHIJKLMNO"},
        "safe": "ok",
    }
    projected = m.redact_evidence(raw)
    rendered = json.dumps(projected, sort_keys=True)
    assert "SECRET" not in rendered
    assert "abcdef" not in rendered
    assert "ABCDEFGHIJ" not in rendered
    assert projected["safe"] == "ok"


def test_failure_matrix_exactly_covers_preregistered_18_cases():
    m = _load()
    assert len(m.FAILURE_MATRIX) == 18
    assert set(m.FAILURE_MATRIX.values()) == {"PRE_ATTEMPT_BLOCK", "FUTURE_ATTEMPT_INVALID"}


def test_local_admission_from_synthetic_files_never_creates_attempt(tmp_path):
    m = _load()
    config, health, codex = m.synthetic_fixture("full")
    config_path = tmp_path / "config.json"
    health_path = tmp_path / "health.json"
    codex_path = tmp_path / "config.toml"
    cgw = tmp_path / "Codex Web GPT.exe"
    codex_cmd = tmp_path / "codex.cmd"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    health_path.write_text(json.dumps(health), encoding="utf-8")
    codex_path.write_text(codex, encoding="utf-8")
    cgw.write_bytes(b"synthetic-cgw")
    codex_cmd.write_bytes(b"synthetic-codex")

    report = m.build_local_admission(
        config_path=config_path,
        codex_config_path=codex_path,
        health_path=health_path,
        cgw_binary_path=cgw,
        codex_command_path=codex_cmd,
    )
    assert report["status"] == "LOCAL_ZERO_MODEL_ADMISSION_PASS"
    assert report["model_turn_executed"] is False
    assert report["responses_endpoint_called"] is False
    assert report["models_endpoint_called"] is False
    assert report["scientific_attempt_created"] is False
    assert report["scientific_attempt_consumed"] is False
    assert len(report["binary_identities"]["cgw_launcher_or_runtime"]["sha256"]) == 64


def test_oneclick_has_hard_zero_model_firewall():
    source = ONECLICK.read_text(encoding="utf-8")
    assert "/healthz" in source
    assert "no /v1/responses" in source
    assert "no /v1/models" in source
    assert "scientific_attempt_created" in source
    assert "P5A_CGW_ZERO_MODEL_ROOT_ALREADY_EXISTS" in source
    assert "Invoke-RestMethod -Method Get" in source
    assert source.count("turn/start") == 1
