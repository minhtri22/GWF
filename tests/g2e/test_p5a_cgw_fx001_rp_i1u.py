from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_rp_i1u_runtime_availability.ps1"
PLAN = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_RP_I1U_RUNTIME_AVAILABILITY_PLAN.md"

def test_rp_i1u_is_zero_science_and_offline():
    s = PROBE.read_text(encoding="utf-8")
    assert 'http_request = $false' in s
    assert 'responses_request = $false' in s
    assert 'model_execution = $false' in s
    assert 'browser_submission = $false' in s
    assert 'mcp_invocation = $false' in s
    assert 'Invoke-RestMethod' not in s
    assert '/healthz' not in s
    assert '/v1/responses' not in s

def test_rp_i1u_classifies_runtime_generations():
    s = PROBE.read_text(encoding="utf-8")
    for token in (
        "PRIOR_RUNTIME_GENERATION_TERMINATED",
        "LAUNCHER_ALIVE_DAEMON_NOT_LISTENING",
        "PRIOR_RUNTIME_GENERATION_STILL_LISTENING",
        "NEW_LISTENER_GENERATION_PRESENT",
        "PRIOR_DAEMON_ALIVE_NOT_LISTENING",
    ):
        assert token in s

def test_plan_is_read_only():
    s = PLAN.read_text(encoding="utf-8")
    assert "ZERO-SCIENCE READ-ONLY DIAGNOSTIC" in s
    assert "No HTTP request" in s
