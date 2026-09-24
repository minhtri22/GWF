from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC_EXECUTION_LOCK_CANDIDATE.json"
FINAL_LOCK = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC_EXECUTION_LOCK.json"
PREFLIGHT = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC_LOCAL_PREFLIGHT_RESULT.json"
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_tc_oneclick.ps1"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_candidate_is_exact_future_live_lock_payload_but_not_active_path():
    c = load(CANDIDATE)
    assert c["schema"] == "G2E-P5A-CGW-FX001-TC-EXECUTION-LOCK-v1"
    assert c["status"] == "DISPATCH_AUTHORIZED_EXECUTION_LOCK_TC1"
    assert c["qualified"] is True
    assert c["study_id"] == "p5a-cgw-v4-p5-fx-001-transport-corrected-qualification"
    assert c["attempt_id"] == "p5a-cgw-v4-p5-fx-001-tc-attempt-001"
    assert c["attempt_state"] == "RESERVED_UNCONSUMED"
    assert not FINAL_LOCK.exists()


def test_candidate_binds_formal_preflight_pass_and_unconsumed_state():
    c = load(CANDIDATE)
    p = load(PREFLIGHT)
    assert p["status"] == "PASS"
    assert p["adjudication"] == "LOCAL_PREFLIGHT_PASS_UNCONSUMED"
    assert p["observed"]["exit_code"] == 0
    assert p["observed"]["attempt_consumed"] is False
    assert p["observed"]["model_turn_sent"] is False
    assert p["observed"]["tc_local_root_exists_after"] is False
    assert p["observed"]["tc_marker_exists_after"] is False
    assert c["local_preflight"]["status"] == "PASS"
    assert c["local_preflight"]["attempt_consumed"] is False
    assert c["local_preflight"]["model_turn_sent"] is False
    assert c["local_preflight"]["tc_local_root_exists_after"] is False
    assert c["local_preflight"]["tc_marker_exists_after"] is False


def test_candidate_binds_qualified_component_and_transport_identities():
    c = load(CANDIDATE)
    assert c["execution_config"]["git_blob"] == "b8196f331e39e37f2f5fc4b6fc2031f50ac1c192"
    assert c["execution_config"]["canonical_sha256"] == "6b88011e0bc6ba0164a0e6f4230bb1fb8be6037d7513f348c15d39ea726816f7"
    assert c["components"] == {
        "admission_blob": "9042940d696f41990c3eb1808035a49f0ddc938e",
        "runner_blob": "d999931d67a6e5958ed1059f894a359aeef82e22",
        "verifier_blob": "5ff0190f4024625f3c5330813878a1b17b663b8c",
        "oneclick_blob": "5cb4285819819a5e6e034be7043628b978332b16",
    }
    assert c["local_codex"]["codex_sha256"] == "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b"
    assert c["local_codex"]["helper_sha256"] == "0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4"
    assert c["launcher_identity"]["expected_sha256"] == "ac152ad499b1f41b2cafe94a3d05f5d4e4d3cd7ddbb417b9c60b118b08bc3cbb"
    assert c["transport_contract"]["scientific_absolute_turn_deadline_ms"] is None
    assert c["transport_contract"]["qualified_upstream_bridge_stall_timeout_sec"] == 300
    assert c["transport_contract"]["qualified_upstream_mcp_invocation_timeout_ms"] == 90000
    assert c["transport_contract"]["qualified_upstream_tunnel_command_response_deadline_ms"] == 120000


def test_candidate_keeps_spent_predecessor_closed_and_tc_cardinality_one():
    c = load(CANDIDATE)
    assert c["evidence_roots"]["spent_predecessor_disposition"] == "PRESERVE_IMMUTABLE_DO_NOT_DELETE"
    assert c["evidence_roots"]["successor_root"] == "g2e/.local/P5A-CGW-FX001-TC-001"
    assert c["frozen_consumption"]["max_dispatches"] == 1
    assert c["frozen_consumption"]["retry_budget"] == 0
    assert c["frozen_consumption"]["same_attempt_rearm"] is False
    assert c["authorization"]["dispatch_authorized"] is True
    assert c["authorization"]["max_dispatches"] == 1
    assert c["authorization"]["retry_budget"] == 0
    assert c["authorization"]["automatic_execution"] is False


def test_oneclick_live_path_reads_only_exact_final_lock_path_and_fail_closes():
    s = ONECLICK.read_text(encoding="utf-8")
    assert "P5A_CGW_FX001_TC_EXECUTION_LOCK.json" in s
    assert "P5A_CGW_FX001_TC_EXECUTION_LOCK_CANDIDATE.json" not in s
    assert "TC_LIVE_DISPATCH_LOCK_MISSING" in s
    assert "DISPATCH_AUTHORIZED_EXECUTION_LOCK_TC1" in s
    assert "TC_DISPATCH_NOT_AUTHORIZED" in s
    assert "TC_DISPATCH_CARDINALITY_DRIFT" in s
    assert "TC_RETRY_BUDGET_DRIFT" in s
