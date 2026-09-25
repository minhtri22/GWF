from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_rp_l1_launcher_identity.ps1"
PLAN = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_RP_L1_LAUNCHER_IDENTITY_PLAN.md"

def test_rp_l1_is_zero_science():
    s = PROBE.read_text(encoding="utf-8")
    for token in (
        'process_launch = $false',
        'http_request = $false',
        'responses_request = $false',
        'model_execution = $false',
        'browser_submission = $false',
        'mcp_invocation = $false',
    ):
        assert token in s
    assert "Start-Process" not in s
    assert "Invoke-RestMethod" not in s
    assert "/v1/responses" not in s

def test_rp_l1_records_identity_and_signature():
    s = PROBE.read_text(encoding="utf-8")
    for token in (
        "Get-FileHash",
        "VersionInfo",
        "Get-AuthenticodeSignature",
        "authenticode_status",
        "signer_subject",
        "signer_thumbprint",
        "SAME_VERSION_DIFFERENT_BINARY_SIGNATURE_VALID",
        "SAME_VERSION_DIFFERENT_BINARY_SIGNATURE_NOT_VALID",
    ):
        assert token in s

def test_plan_does_not_auto_qualify_same_version():
    s = PLAN.read_text(encoding="utf-8")
    assert "does not automatically qualify the new binary" in s
