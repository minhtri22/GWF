from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAG = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_route_instance_diagnostic.ps1"
PLAN = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_RP_I1D_DIAGNOSTIC_PLAN.md"


def test_rp_i1d_is_zero_science_and_diagnostic_only():
    s = DIAG.read_text(encoding="utf-8")
    assert 'zero_science = $true' in s
    assert 'model_execution = $false' in s
    assert 'responses_post = $false' in s
    assert 'browser_submission = $false' in s
    assert 'mcp_invocation = $false' in s
    assert '/healthz' in s
    assert '/v1/responses' not in s
    assert 'PostAsync(' not in s
    assert 'Invoke-RestMethod -Method Post' not in s
    assert 'turn/start' not in s


def test_rp_i1d_collects_identity_without_raw_commandline():
    s = DIAG.read_text(encoding="utf-8")
    for token in (
        'Get-NetTCPConnection',
        'launcher-supervisor.json',
        'launcher-browser.json',
        'Codex Web GPT.exe',
        'runtime.daemon_started',
        'runtime.external_owner_detected',
        'command_sha256',
    ):
        assert token in s
    assert 'command_line =' not in s


def test_plan_cannot_pass_rp_i1():
    s = PLAN.read_text(encoding="utf-8")
    assert "cannot PASS RP-I1 or RP-I2 by itself" in s
    assert "no model execution" in s
