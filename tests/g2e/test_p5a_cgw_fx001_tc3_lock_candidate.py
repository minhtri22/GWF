from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC3_EXECUTION_LOCK_CANDIDATE.json"
FINAL_LOCK = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC3_EXECUTION_LOCK.json"
PREFLIGHT = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC3_LOCAL_PREFLIGHT_RESULT.json"
QUAL = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC3_RUNTIME_READINESS_QUALIFICATION.json"
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_tc3_oneclick.ps1"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_candidate_is_not_yet_active_lock():
    c = load(CANDIDATE)
    assert c["schema"] == "G2E-P5A-CGW-FX001-TC3-EXECUTION-LOCK-v1"
    assert c["status"] == "DISPATCH_AUTHORIZED_EXECUTION_LOCK_TC3"
    assert c["qualified"] is True
    assert c["attempt_state"] == "RESERVED_UNCONSUMED"
    assert not FINAL_LOCK.exists()


def test_candidate_binds_tc3_preflight_and_qualified_blobs():
    c = load(CANDIDATE)
    p = load(PREFLIGHT)
    q = load(QUAL)
    assert p["status"] == "PASS"
    assert p["adjudication"] == "TC3_RUNTIME_READINESS_PREFLIGHT_PASS_UNCONSUMED"
    assert p["observed"]["runtime_health_ready"] is True
    assert p["observed"]["attempt_consumed"] is False
    assert p["observed"]["model_turn_sent"] is False
    assert p["observed"]["tc003_local_root_exists_after"] is False
    assert p["observed"]["tc003_marker_exists_after"] is False
    assert q["status"] == "PASS"
    assert c["components"]["admission_blob"] == q["successor_tc003"]["admission_blob"]
    assert c["components"]["oneclick_blob"] == q["successor_tc003"]["oneclick_blob"]
    assert c["components"]["runner_blob"] == q["successor_tc003"]["runner_blob"]
    assert c["components"]["verifier_blob"] == q["successor_tc003"]["verifier_blob"]


def test_candidate_preserves_predecessor_roots_and_uses_fresh_tc003():
    c = load(CANDIDATE)
    roots = c["evidence_roots"]
    assert roots["tc001_preconsumption_root"] == "g2e/.local/P5A-CGW-FX001-TC-001"
    assert roots["tc002_preconsumption_root"] == "g2e/.local/P5A-CGW-FX001-TC-002"
    assert roots["predecessor_disposition"] == "PRESERVE_IMMUTABLE_DO_NOT_REUSE"
    assert roots["successor_root"] == "g2e/.local/P5A-CGW-FX001-TC-003"
    assert roots["successor_marker"].endswith("TC-003/evidence/attempt_consumed.marker")


def test_readiness_contract_is_frozen_before_science():
    c = load(CANDIDATE)
    r = c["readiness_contract"]
    assert r["gate_position"] == "PRE_UAC_PRE_VHDX_PRE_LOCALROOT_PRE_ADMISSION_PRE_RUNNER"
    assert r["endpoint"] == "http://127.0.0.1:17841/healthz"
    assert r["status"] == "ok"
    assert r["service"] == "codex-chatgpt-web"
    assert r["version"] == "4.0.7"
    assert r["mode"] == "full"
    assert r["port"] == 17841
    assert r["accepting_turns"] is True
    assert r["active_http_turns"] == 0
    assert r["active_browser_turns"] == 0


def test_dispatch_cardinality_transport_and_authority_remain_frozen():
    c = load(CANDIDATE)
    assert c["transport_contract"]["scientific_absolute_turn_deadline_ms"] is None
    assert c["transport_contract"]["qualified_upstream_bridge_stall_timeout_sec"] == 300
    assert c["transport_contract"]["qualified_upstream_mcp_invocation_timeout_ms"] == 90000
    assert c["transport_contract"]["qualified_upstream_tunnel_command_response_deadline_ms"] == 120000
    assert c["frozen_consumption"]["max_dispatches"] == 1
    assert c["frozen_consumption"]["retry_budget"] == 0
    assert c["frozen_consumption"]["same_attempt_rearm"] is False
    assert c["authorization"]["dispatch_authorized"] is True
    assert c["authorization"]["max_dispatches"] == 1
    assert c["authorization"]["retry_budget"] == 0
    assert c["authorization"]["automatic_execution"] is False
    assert c["authority_invariant"] == "delegated_authority <= active_outer_codex_turn_authority <= G2E_attempt_authority"


def test_tc3_oneclick_reads_only_final_tc3_lock_and_fails_closed():
    s = ONECLICK.read_text(encoding="utf-8")
    assert "P5A_CGW_FX001_TC3_EXECUTION_LOCK.json" in s
    assert "P5A_CGW_FX001_TC3_EXECUTION_LOCK_CANDIDATE.json" not in s
    assert "P5A_CGW_FX001_TC2_EXECUTION_LOCK.json" not in s
    assert "TC_LIVE_DISPATCH_LOCK_MISSING" in s
    assert "DISPATCH_AUTHORIZED_EXECUTION_LOCK_TC3" in s
    assert "TC_DISPATCH_NOT_AUTHORIZED" in s
    assert "TC_DISPATCH_CARDINALITY_DRIFT" in s
    assert "TC_RETRY_BUDGET_DRIFT" in s


def test_readiness_gate_precedes_uac_and_root_creation():
    s = ONECLICK.read_text(encoding="utf-8")
    health = s.index('Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:17841/healthz"')
    uac = s.index("if (-not (Test-IsAdministrator))")
    root_create = s.index("New-Item -ItemType Directory -Path $VolumeDir,$CodexHome,$ReportDir,$VerificationDir")
    assert 0 <= health < uac < root_create
