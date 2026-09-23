from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_preregister.py"


def load():
    spec = importlib.util.spec_from_file_location("p5a_cgw_fx001_preregister", MODULE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_exact_runtime_route_model_mode_are_frozen():
    m = load()
    r = m.build_preregistration()
    assert r["runtime_identity"]["cgw_release"] == "4.0.7"
    assert r["runtime_identity"]["cgw_source_commit"] == "b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494"
    assert r["runtime_identity"]["cgw_installed_binary_sha256"] == "ac152ad499b1f41b2cafe94a3d05f5d4e4d3cd7ddbb417b9c60b118b08bc3cbb"
    assert r["runtime_identity"]["codex_binary_sha256"] == "a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8"
    assert r["route"]["bridge_mode"] == "full"
    assert r["route"]["connector"] == "Codex Native2"
    assert r["route"]["model_slug"] == "chatgpt-web/high"
    assert r["route"]["backend_model"] == "gpt-5.6-sol"
    assert r["route"]["codex_openai_base_url"] == "http://127.0.0.1:17841/v1"


def test_p5_fx_001_task_and_expected_result_are_exact():
    m = load()
    r = m.build_preregistration()
    assert r["fixture"]["input_sha256"] == "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
    assert r["fixture"]["task_sha256"] == "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"
    assert r["result_contract"]["expected_canonical_sha256"] == "6dd3ebce33677409bec596309e061cc421bfa38b3160c5b577ffe5f7fbc9980d"
    assert r["result_contract"]["expected_value"]["count"] == 32
    assert r["result_contract"]["expected_value"]["sum"] == -6372402978
    assert r["result_contract"]["additional_keys_allowed"] is False


def test_codex_remains_sole_local_execution_authority():
    m = load()
    r = m.build_preregistration()
    a = r["authority"]
    assert a["codex"] == "sole_local_execution_authority"
    assert a["cgw"] == "transport_and_inference_mediation_only"
    assert a["bridge_local_side_effects"] == "DENY"
    assert a["task_tool_network"] == "DENY"
    assert a["route_transport_network"] == "ALLOW_ONLY_FROZEN_CGW_BROWSER_PATH"
    assert a["approval_policy"] == "never"


def test_attempt_consumption_and_retry_are_frozen():
    m = load()
    r = m.build_preregistration()
    c = r["attempt_consumption"]
    assert c["boundary"] == "durable marker fsync immediately before sole Codex turn/start transport write"
    assert c["pre_marker_failure_consumes_attempt"] is False
    assert c["post_marker_attempt_consumed"] is True
    assert c["max_turn_start_transport_writes"] == 1
    assert c["retry_budget"] == 0
    assert c["automatic_retry"] is False
    assert c["turn_timeout_seconds"] == 90


def test_live_mcp_roundtrip_is_mandatory_evidence():
    m = load()
    r = m.build_preregistration()
    assert "at_least_one_live_roundtrip" in r["evidence_requirements"]["required_mcp_roundtrip_fields"]
    assert "missing_live_mcp_roundtrip" in r["decision"]["invalid"]


def test_preregistration_does_not_authorize_model_execution():
    m = load()
    r = m.build_preregistration()
    assert r["authorization"]["model_turn"] is False
    assert r["authorization"]["functional_attempt"] is False
    assert r["authorization"]["scientific_attempt"] is False
    assert r["authorization"]["comparative_ab"] is False


def test_no_silent_substitution():
    m = load()
    r = m.build_preregistration()
    route = r["route"]
    for key in (
        "silent_model_fallback",
        "silent_transport_fallback",
        "official_p5a_fallback",
        "model_substitution",
        "mode_substitution",
        "connector_substitution",
    ):
        assert route[key] is False


def test_contract_hash_is_deterministic():
    m = load()
    a = m.build_preregistration()
    b = m.build_preregistration()
    assert a["contract_sha256"] == b["contract_sha256"]
    unsigned = dict(a)
    digest = unsigned.pop("contract_sha256")
    assert m.canonical_sha256(unsigned) == digest
