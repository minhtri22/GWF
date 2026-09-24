from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC2_EXECUTION_LOCK_CANDIDATE.json"
FINAL_LOCK = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC2_EXECUTION_LOCK.json"
PREFLIGHT = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC2_LOCAL_PREFLIGHT_RESULT.json"
QUAL = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC2_IMPLEMENTATION_QUALIFICATION_RESULT.json"
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_tc2_oneclick.ps1"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_candidate_is_not_yet_active_lock():
    c = load(CANDIDATE)
    assert c["schema"] == "G2E-P5A-CGW-FX001-TC2-EXECUTION-LOCK-v1"
    assert c["status"] == "DISPATCH_AUTHORIZED_EXECUTION_LOCK_TC2"
    assert c["qualified"] is True
    assert c["attempt_state"] == "RESERVED_UNCONSUMED"
    assert not FINAL_LOCK.exists()


def test_candidate_binds_tc2_preflight_and_qualified_blobs():
    c = load(CANDIDATE)
    p = load(PREFLIGHT)
    q = load(QUAL)
    assert p["status"] == "PASS"
    assert p["adjudication"] == "TC2_LOCAL_PREFLIGHT_PASS_UNCONSUMED"
    assert p["observed"]["attempt_consumed"] is False
    assert p["observed"]["model_turn_sent"] is False
    assert p["observed"]["tc002_local_root_exists_after"] is False
    assert p["observed"]["tc002_marker_exists_after"] is False
    assert q["status"] == "PASS"
    assert c["components"]["admission_blob"] == q["successor_tc002"]["admission_blob"]
    assert c["components"]["oneclick_blob"] == q["successor_tc002"]["oneclick_blob"]
    assert c["components"]["runner_blob"] == q["successor_tc002"]["runner_blob"]
    assert c["components"]["verifier_blob"] == q["successor_tc002"]["verifier_blob"]


def test_candidate_preserves_tc001_and_uses_fresh_tc002_root():
    c = load(CANDIDATE)
    assert c["evidence_roots"]["tc001_preconsumption_root"] == "g2e/.local/P5A-CGW-FX001-TC-001"
    assert c["evidence_roots"]["tc001_disposition"] == "PRESERVE_IMMUTABLE_DO_NOT_REUSE"
    assert c["evidence_roots"]["successor_root"] == "g2e/.local/P5A-CGW-FX001-TC-002"
    assert c["evidence_roots"]["successor_marker"].endswith("TC-002/evidence/attempt_consumed.marker")


def test_candidate_freezes_semantic_repair_and_transport_contract():
    c = load(CANDIDATE)
    s = c["semantic_config_contract"]
    assert s["whole_file_hash_enforced"] is False
    assert s["raw_hash_provenance_only"] is True
    assert s["release_version"] == "4.0.7"
    assert s["mode"] == "full"
    assert s["subagent_protocol"] == "compatibility-v1"
    assert s["context_window"] == 256000
    assert s["connector"] == "Codex Native2"
    assert s["sol_available"] is True
    assert s["pro_available"] is False
    assert s["experimental_bigger_context"] is True
    assert s["windows_runtime_executable_basename"] == "bun.exe"
    assert c["transport_contract"]["scientific_absolute_turn_deadline_ms"] is None
    assert c["transport_contract"]["qualified_upstream_bridge_stall_timeout_sec"] == 300
    assert c["transport_contract"]["qualified_upstream_mcp_invocation_timeout_ms"] == 90000
    assert c["transport_contract"]["qualified_upstream_tunnel_command_response_deadline_ms"] == 120000


def test_dispatch_cardinality_and_authority_remain_frozen():
    c = load(CANDIDATE)
    assert c["frozen_consumption"]["max_dispatches"] == 1
    assert c["frozen_consumption"]["retry_budget"] == 0
    assert c["frozen_consumption"]["same_attempt_rearm"] is False
    assert c["authorization"]["dispatch_authorized"] is True
    assert c["authorization"]["max_dispatches"] == 1
    assert c["authorization"]["retry_budget"] == 0
    assert c["authorization"]["automatic_execution"] is False
    assert c["authority_invariant"] == "delegated_authority <= active_outer_codex_turn_authority <= G2E_attempt_authority"


def test_tc2_oneclick_reads_only_exact_final_tc2_lock_and_fails_closed():
    s = ONECLICK.read_text(encoding="utf-8")
    assert "P5A_CGW_FX001_TC2_EXECUTION_LOCK.json" in s
    assert "P5A_CGW_FX001_TC2_EXECUTION_LOCK_CANDIDATE.json" not in s
    assert "P5A_CGW_FX001_TC_EXECUTION_LOCK.json" not in s
    assert "TC_LIVE_DISPATCH_LOCK_MISSING" in s
    assert "DISPATCH_AUTHORIZED_EXECUTION_LOCK_TC2" in s
    assert "TC_DISPATCH_NOT_AUTHORIZED" in s
    assert "TC_DISPATCH_CARDINALITY_DRIFT" in s
    assert "TC_RETRY_BUDGET_DRIFT" in s
