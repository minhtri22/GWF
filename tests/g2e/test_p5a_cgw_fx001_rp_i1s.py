from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_rp_i1s_ownership_snapshot.ps1"
PLAN = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_RP_I1S_OWNERSHIP_SNAPSHOT_PLAN.md"


def test_rp_i1s_is_zero_science():
    s = PROBE.read_text(encoding="utf-8")
    assert 'zero_science = $true' in s
    assert 'model_execution = $false' in s
    assert 'responses_request = $false' in s
    assert 'browser_submission = $false' in s
    assert 'mcp_invocation = $false' in s
    assert '/healthz' in s
    assert '/v1/responses' not in s


def test_rp_i1s_projects_descriptor_without_secret_fields():
    s = PROBE.read_text(encoding="utf-8")
    assert 'control = ' not in s
    assert 'helper = ' not in s
    assert 'surfaceId = ' not in s
    assert 'endpoint = [string]$descriptor.endpoint' in s


def test_rp_i1s_reads_ownership_relationships():
    s = PROBE.read_text(encoding="utf-8")
    for token in (
        "supervisor_daemon_equals_listener",
        "supervisor_owner_equals_listener_parent",
        "descriptor_equals_supervisor_owner",
        "OWNERSHIP_STATE_REFERENCES_NONLIVE_PROCESS",
        "SUPERVISOR_DESCRIPTOR_GENERATION_SPLIT",
        "OWNERSHIP_STATE_BINDS_DIFFERENT_LIVE_INSTANCE",
    ):
        assert token in s


def test_plan_is_diagnostic_only():
    s = PLAN.read_text(encoding="utf-8")
    assert "ZERO-SCIENCE READ-ONLY DIAGNOSTIC" in s
    assert "No /v1/responses request" in s
