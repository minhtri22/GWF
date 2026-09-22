from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "scripts" / "g2e" / "p5a_d2s2_diagnostic_return_oneclick.ps1"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S2_DIAGNOSTIC_RETURN_WRAPPER_SPEC.md"


def test_wrapper_is_zero_science_and_delegates_only_to_qualified_diagnostic():
    source = WRAPPER.read_text(encoding="utf-8")
    lower = source.lower()

    assert '"turn/start"' not in source
    assert "windowssandbox/setupstart" not in lower
    assert "thread/start" not in lower
    assert "diskpart" not in lower
    assert "create vdisk" not in lower
    assert "attach vdisk" not in lower
    assert "& $codexexe" not in lower
    assert "start-process -filepath $codexexe" not in lower

    assert "p5a_d2s2_elevation_bootstrap_diagnostic.ps1" in source
    assert "& $DiagnosticScript -ProjectRoot $ProjectRoot" in source


def test_wrapper_fetches_and_detaches_exact_remote_branch():
    source = WRAPPER.read_text(encoding="utf-8")
    assert '@("fetch", "--prune", "origin", "feature/g2e-framework")' in source
    assert '@("switch", "--detach", "origin/feature/g2e-framework")' in source
    assert '@("rev-parse", "HEAD")' in source


def test_wrapper_archives_prior_report_and_uses_unique_return_name():
    source = WRAPPER.read_text(encoding="utf-8")
    assert "P5A_D2S2_ELEVATION_BOOTSTRAP_REPORT_STALE_$stamp.json" in source
    assert "P5A_D2S2_ELEVATION_BOOTSTRAP_REPORT_${head12}_${returnStamp}.json" in source
    assert "g2e\\.local\\P5A-D2S2-BOOTSTRAP" in source
    assert '$ReturnDir = Join-Path $BootstrapRoot "return"' in source


def test_wrapper_rejects_stale_or_wrong_head_report():
    source = WRAPPER.read_text(encoding="utf-8")
    assert "RETURN_REPORT_SOURCE_HEAD_MISSING" in source
    assert "RETURN_REPORT_HEAD_MISMATCH" in source
    assert "RETURN_REPORT_STALE" in source
    assert "$ReportStarted -lt $InvocationStart.AddSeconds(-2)" in source


def test_wrapper_enforces_scientific_firewalls():
    source = WRAPPER.read_text(encoding="utf-8")
    assert "SCIENTIFIC_ATTEMPT_CONSUMPTION_FIREWALL_VIOLATION" in source
    assert "MODEL_TURN_FIREWALL_VIOLATION" in source
    assert "scientific_attempt_consumed = $false" in source
    assert "model_turn_executed = $false" in source


def test_spec_keeps_return_wrapper_non_scientific():
    normalized = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "NOT AUTHORIZED and NOT CONSUMED" in normalized
    assert "report provenance/return-path problem" in normalized
    assert "does not authorize the D2-S2 isolated-volume preflight" in normalized
