from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_rp_i1t_temporal_binding.ps1"
PLAN = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_RP_I1T_TEMPORAL_BINDING_PLAN.md"


def test_rp_i1t_is_zero_science():
    s = PROBE.read_text(encoding="utf-8")
    assert 'model_execution = $false' in s
    assert 'responses_request = $false' in s
    assert 'browser_submission = $false' in s
    assert 'mcp_invocation = $false' in s
    assert '/healthz' in s
    assert '/v1/responses' not in s
    assert 'Invoke-RestMethod -Method Post' not in s


def test_rp_i1t_freezes_tc3_git_window():
    s = PROBE.read_text(encoding="utf-8")
    assert '2026-09-25T02:59:15Z' in s
    assert '2026-09-25T03:40:47Z' in s
    assert 'PASS_TC3_DEV_INSTANCE_TEMPORAL_BINDING' in s


def test_rp_i1t_uses_dev_profile_roots():
    s = PROBE.read_text(encoding="utf-8")
    assert '.codex-chatgpt-web-dev' in s
    assert 'launcher\\logs\\launcher.jsonl' in s
    assert 'launcher-supervisor.json' in s
    assert 'launcher-browser.json' in s
    assert 'runtime.daemon_started' in s


def test_plan_requires_temporal_join_before_historical_root_cause():
    s = PLAN.read_text(encoding="utf-8")
    assert "H-R1 may be promoted" in s
    assert "No /v1/responses request" in s
