from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDITOR = ROOT / "scripts" / "g2e" / "p5a_cgw_transport_adequacy.py"
RUNNER = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_runner.py"
VERIFIER = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_verify.py"
POLICY = ROOT / "g2e" / "config" / "P5A_CGW_TRANSPORT_ADEQUACY_POLICY.json"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_upstream_transport_contract_rejects_legacy_90s_outer_assumption():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    upstream = policy["qualified_upstream"]["codex_chatgpt_web"]["source_contract"]
    future = policy["future_transport_contract"]

    assert upstream["browser_turn_absolute_deadline_default_ms"] is None
    assert upstream["bridge_stall_timeout_sec"] == 300
    assert upstream["mcp_invocation_timeout_ms"] == 90_000
    assert upstream["tunnel_command_response_deadline_ms"] == 120_000
    assert future["scientific_adjudication_absolute_turn_deadline_ms"] is None

    legacy = RUNNER.read_text(encoding="utf-8")
    assert "TURN_TIMEOUT_S = 90.0" in legacy
    assert "deadline = time.monotonic() + TURN_TIMEOUT_S" in legacy


def test_spent_attempt_is_preserved_and_never_rearmed_by_transport_study():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["origin"]["spent_attempt"] == "p5a-cgw-v4-p5-fx-001-attempt-001"
    assert policy["origin"]["rerun_forbidden"] is True
    assert policy["origin"]["replacement_attempt_authorized"] is False
    assert policy["future_transport_contract"]["reuse_spent_attempt"] is False
    assert policy["future_transport_contract"]["reuse_spent_execution_lock"] is False
    assert all(value is False for value in policy["firewall"].values())


def test_signal_decomposition_does_not_call_missing_route_authority_violation():
    m = load(AUDITOR, "transport_adequacy")
    result = m.classify_signals(
        route_valid=False,
        unexpected_server_request_count=0,
        prohibited_tool_or_network_seen=False,
        bridge_side_effects_performed=False,
        executor_is_outer_codex=None,
    )
    assert result == {
        "evidence_integrity_failure": True,
        "protocol_failure": False,
        "scope_violation": False,
        "authority_violation": False,
    }


def test_signal_decomposition_keeps_protocol_scope_and_authority_distinct():
    m = load(AUDITOR, "transport_adequacy_distinct")
    protocol = m.classify_signals(
        route_valid=True,
        unexpected_server_request_count=1,
        prohibited_tool_or_network_seen=False,
        bridge_side_effects_performed=False,
        executor_is_outer_codex=True,
    )
    assert protocol["protocol_failure"] is True
    assert protocol["authority_violation"] is False

    scope = m.classify_signals(
        route_valid=True,
        unexpected_server_request_count=0,
        prohibited_tool_or_network_seen=True,
        bridge_side_effects_performed=False,
        executor_is_outer_codex=True,
    )
    assert scope["scope_violation"] is True
    assert scope["authority_violation"] is False

    authority = m.classify_signals(
        route_valid=True,
        unexpected_server_request_count=0,
        prohibited_tool_or_network_seen=False,
        bridge_side_effects_performed=True,
        executor_is_outer_codex=True,
    )
    assert authority["authority_violation"] is True


def test_static_audit_confirms_both_v2r6_infrastructure_defects():
    m = load(AUDITOR, "transport_adequacy_audit")
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    report = m.audit_sources(
        RUNNER.read_text(encoding="utf-8"),
        VERIFIER.read_text(encoding="utf-8"),
        policy,
    )
    assert report["status"] == "PASS"
    assert report["classification"] == "INFRASTRUCTURE_CONTRACT_MISMATCH_CONFIRMED"
    assert report["legacy"]["outer_absolute_timeout_sec"] == 90
    assert report["legacy"]["authority_conflation_present"] is True
    assert report["scientific_attempt_touched"] is False


def test_legacy_verifier_conflation_is_frozen_evidence_not_future_contract():
    source = VERIFIER.read_text(encoding="utf-8")
    assert 'authority_violation = web_search_seen or bool(unexpected_server_requests) or not route_check["valid"]' in source
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["future_transport_contract"]["route_invalidity_class"] == "evidence_integrity_failure"
    assert policy["future_transport_contract"]["unexpected_server_request_class"] == "protocol_failure"
    assert policy["future_transport_contract"]["authority_violation_requires_positive_authority_evidence"] is True
