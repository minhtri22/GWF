from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_rp_i1r_active_profile_probe.ps1"
PLAN = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_RP_I1R_ACTIVE_PROFILE_REPAIR_PLAN.md"


def test_rp_i1r_is_zero_science():
    s = PROBE.read_text(encoding="utf-8")
    assert 'zero_science = $true' in s
    assert 'model_execution = $false' in s
    assert 'responses_post = $false' in s
    assert 'browser_submission = $false' in s
    assert 'mcp_invocation = $false' in s
    assert '.GetAsync("http://127.0.0.1:$ExpectedPort/v1/responses")' in s
    assert 'PostAsync(' not in s
    assert 'Invoke-RestMethod -Method Post' not in s


def test_rp_i1r_binds_profile_before_selecting_sinks():
    s = PROBE.read_text(encoding="utf-8")
    for token in (
        'exactly_one_profile_bound',
        'owner_matches',
        'daemon_matches',
        'descriptor_matches',
        'active_config_valid',
        'active_launcher_log_exists',
        'PASS_ACTIVE_PROFILE_INSTANCE_BOUND_ZERO_SCIENCE',
    ):
        assert token in s


def test_rp_i1r_supports_both_qualified_profiles():
    s = PROBE.read_text(encoding="utf-8")
    assert '.codex-chatgpt-web' in s
    assert '.codex-chatgpt-web-dev' in s
    assert 'expected_purpose = "dev-harness"' in s
    assert 'expected_purpose = $null' in s


def test_rp_i1r_uses_shared_dictionary_contract():
    s = PROBE.read_text(encoding="utf-8")
    assert '[System.Collections.IDictionary]$Checks' in s
    assert '[hashtable]$Checks' not in s
    assert 'Get-ProcessInfo([int]$ProcessId)' in s
    assert 'Get-ProcessInfo([int]$Pid)' not in s


def test_plan_forbids_hardcoded_sink_selection_before_binding():
    s = PLAN.read_text(encoding="utf-8")
    assert "must never choose an evidence root before binding the active listener instance" in s
    assert "does not authorize a replacement scientific attempt" in s


def test_rp_i1r_loads_system_net_http_before_httpclient_use():
    s = PROBE.read_text(encoding="utf-8")
    load = 'Add-Type -AssemblyName System.Net.Http'
    use = '[Net.Http.HttpClient]::new()'
    assert load in s
    assert use in s
    assert s.index(load) < s.index(use)
