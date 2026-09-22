from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "g2e" / "p5a_d2s2_cleanup_mounted_vhdx.ps1"
CONTRACT = ROOT / "g2e" / "docs" / "P5A_D2S2_EPHEMERAL_VHDX_CLEANUP_CONTRACT.md"


def test_cleanup_targets_only_exact_historical_vhdx_paths():
    source = SCRIPT.read_text(encoding="utf-8")
    expected = [
        r"g2e\.local\P5A-D2S2\volume\P5A-D2S2-TASK.vhdx",
        r"g2e\.local\P5A-D2S2-A1\volume\P5A-D2S2-A1-TASK.vhdx",
        r"g2e\.local\P5A-D2S2-A2\volume\P5A-D2S2-A2-TASK.vhdx",
    ]
    for path in expected:
        assert path in source


def test_cleanup_is_detach_only_and_preserves_evidence():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "Dismount-DiskImage -ImagePath $path" in source
    assert "Get-DiskImage -ImagePath $path" in source
    assert "vhdx_deleted = $false" in source
    assert "evidence_preserved = $true" in source

    forbidden = [
        "Remove-Item",
        "DeleteFile",
        "Format-Volume",
        "New-VHD",
        "Mount-DiskImage",
        "diskpart.exe",
        "codex.exe",
        "app-server",
        "windowsSandbox/",
        "thread/start",
        "turn/start",
    ]
    for token in forbidden:
        assert token not in source


def test_cleanup_uses_safe_uac_argument_vector():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "$ElevatedArgs = @(" in source
    assert "-ArgumentList $ElevatedArgs" in source
    assert "$args = @(" not in source


def test_cleanup_has_plan_only_mode_for_ci():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "[switch]$PlanOnly" in source
    assert "PLAN_ONLY_PASS" in source


def test_cleanup_reports_before_after_and_firewalls():
    source = SCRIPT.read_text(encoding="utf-8")
    for field in [
        "attached_before",
        "attached_after",
        "cleanup_error",
        "CLEANUP_PASS",
        "CLEANUP_BLOCKED",
        "turn_start_request_sent = $false",
        "scientific_attempt_consumed = $false",
    ]:
        assert field in source


def test_successor_contract_requires_finally_detach_and_verify():
    normalized = " ".join(CONTRACT.read_text(encoding="utf-8").split())
    assert "execute cleanup from a `finally` path" in normalized
    assert "dismount the exact image path before script termination" in normalized
    assert "verify `Attached == false`" in normalized
    assert "return nonzero if cleanup verification fails" in normalized
    assert "MUST NOT be edited retroactively" in normalized
