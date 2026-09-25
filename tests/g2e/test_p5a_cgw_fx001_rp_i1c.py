from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_rp_i1c_derived_core_home.ps1"
PLAN = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_RP_I1C_DERIVED_CORE_HOME_PLAN.md"


def test_rp_i1c_is_zero_science():
    s = PROBE.read_text(encoding="utf-8")
    assert 'zero_science = $true' in s
    assert 'model_execution = $false' in s
    assert 'responses_request = $false' in s
    assert 'browser_submission = $false' in s
    assert 'mcp_invocation = $false' in s
    assert '/healthz' in s
    assert '/v1/responses' not in s


def test_rp_i1c_derives_core_home_from_versions_contract():
    s = PROBE.read_text(encoding="utf-8")
    assert 'Split-Path -Leaf $versionsDir' in s
    assert '"versions"' in s
    assert 'core_home = $coreHome' in s


def test_rp_i1c_checks_direct_ownership_binding():
    s = PROBE.read_text(encoding="utf-8")
    for token in (
        "supervisor_daemon_equals_listener",
        "supervisor_owner_equals_listener_parent",
        "descriptor_equals_supervisor_owner",
        "launcher_sha_matches_qualified",
        "PASS_DERIVED_CORE_HOME_BINDS_PRODUCTION_LAUNCHER",
        "PASS_DERIVED_CORE_HOME_BINDS_DEVELOPMENT_LAUNCHER",
    ):
        assert token in s


def test_plan_is_read_only():
    s = PLAN.read_text(encoding="utf-8")
    assert "ZERO-SCIENCE READ-ONLY DIAGNOSTIC" in s
    assert "No /v1/responses request" in s


def test_rp_i1c_uses_robust_timestamp_normalization():
    s = PROBE.read_text(encoding="utf-8")
    assert "function Convert-ToUtcIso([object]$Value)" in s
    assert 'creation_time_utc = Convert-ToUtcIso $p.CreationDate' in s
    assert '[Management.ManagementDateTimeConverter]::ToDateTime([string]$p.CreationDate)' not in s
