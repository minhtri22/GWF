from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "uiux" / "bps_current_surface_u16_recovery.ps1"
REPAIR_HEAD = "277dd6c32f10563ebaafca9618b3c479fcea8d41"


def test_u16_recovery_is_bounded_and_preserves_failed_evidence():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'Set-StrictMode -Version Latest' in text
    assert '$ErrorActionPreference = "Stop"' in text
    assert REPAIR_HEAD in text
    assert "CURRENT_SURFACE_UAT_REPORT.json" in text
    assert "CURRENT_SURFACE_U16_RECOVERY_REPORT.json" in text
    assert "prior_only_u16_failed" in text
    assert "prior_other_18_pass" in text
    assert "repair_is_styles_only" in text
    assert '$repairDiff[0] -eq "web/styles.css"' in text
    assert "no_product_drift_after_repair" in text
    assert "COMPOSITE_FINAL_VERDICT=$Verdict" in text
    assert "U16 TARGETED RECOVERY" in text
    assert "U01-U15 and U17-U19 PASS" in text
    assert "Stop-Process -Id $Proc.Id" in text
    assert "Stop-Process -Id $serverMeta.pid" not in text


def test_u16_recovery_script_is_windows_powershell_51_text_safe():
    text = SCRIPT.read_text(encoding="utf-8")
    assert sorted({ch for ch in text if ord(ch) > 127}) == []
