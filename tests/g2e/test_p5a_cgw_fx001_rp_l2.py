from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_rp_l2_launcher_provenance.ps1"
PLAN = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_RP_L2_LAUNCHER_PROVENANCE_PLAN.md"

def test_rp_l2_is_read_only_zero_science():
    s = PROBE.read_text(encoding="utf-8")
    for token in (
        'process_launch = $false',
        'http_request = $false',
        'download = $false',
        'install_or_extract = $false',
        'responses_request = $false',
        'model_execution = $false',
        'browser_submission = $false',
        'mcp_invocation = $false',
    ):
        assert token in s
    for forbidden in ("Start-Process", "Invoke-RestMethod", "Invoke-WebRequest", "curl ", "Expand-Archive"):
        assert forbidden not in s

def test_rp_l2_binds_official_release_and_source_commit():
    s = PROBE.read_text(encoding="utf-8")
    assert "b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494" in s
    assert "90f47feaa5c6c17612ac9bee6a49b11b65e0241b046b7380e2c5219792a55354" in s
    assert "ac152ad499b1f41b2cafe94a3d05f5d4e4d3cd7ddbb417b9c60b118b08bc3cbb" in s

def test_rp_l2_reads_git_registry_and_candidates():
    s = PROBE.read_text(encoding="utf-8")
    for token in (
        "git -C $CgwRepo rev-parse HEAD",
        "git -C $CgwRepo status --porcelain=v1",
        "git -C $CgwRepo rev-list -n 1 v4.0.7",
        "d1a6026a-6210-588e-9a2b-da3936f94e02",
        "registered_matches_prior_qualified",
        "local_installer_matches_official_release",
    ):
        assert token in s

def test_plan_does_not_authorize_execution():
    s = PLAN.read_text(encoding="utf-8")
    assert "does not itself authorize any launcher execution" in s
