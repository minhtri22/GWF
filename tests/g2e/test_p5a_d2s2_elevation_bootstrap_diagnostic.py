from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "g2e" / "p5a_d2s2_elevation_bootstrap_diagnostic.ps1"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S2_ELEVATION_BOOTSTRAP_DIAGNOSTIC_SPEC.md"


def test_diagnostic_scope_is_zero_science():
    source = SCRIPT.read_text(encoding="utf-8")
    lower = source.lower()

    assert '"turn/start"' not in source
    assert "windowssandbox/setupstart" not in lower
    assert "thread/start" not in lower
    assert "diskpart" not in lower
    assert "create vdisk" not in lower
    assert "attach vdisk" not in lower
    assert "result.json" not in lower
    assert "& $codexexe" not in lower
    assert "start-process -filepath $codexexe" not in lower

    assert "scientific_attempt_consumed = $false" in source
    assert "model_turn_executed = $false" in source


def test_parent_report_is_created_before_uac_handoff():
    source = SCRIPT.read_text(encoding="utf-8")

    report_marker = 'status = "LAUNCHER_READY"'
    save_marker = "Save-Report $report $ReportJson $ReportMd"
    uac_marker = 'Start-Process -FilePath "powershell.exe" -Verb RunAs'

    assert report_marker in source
    assert save_marker in source
    assert uac_marker in source

    report_index = source.index(report_marker)
    save_index = source.index(save_marker, report_index)
    uac_index = source.index(uac_marker)

    assert report_index < save_index < uac_index


def test_elevated_child_reports_before_running_gates():
    source = SCRIPT.read_text(encoding="utf-8")

    entry = 'status = "ELEVATED_ENTERED"'
    save = "Save-Report $report $ReportJson $ReportMd"
    first_gate = 'Set-Gate $report "elevation"'

    entry_index = source.index(entry)
    save_index = source.index(save, entry_index)
    gate_index = source.index(first_gate, entry_index)

    assert entry_index < save_index < gate_index


def test_diagnostic_uses_separate_local_artifact_root():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "g2e\\.local\\P5A-D2S2-BOOTSTRAP\\report" in source
    assert "P5A_D2S2_ELEVATION_BOOTSTRAP_REPORT.json" in source
    assert "P5A_D2S2_ELEVATION_BOOTSTRAP_REPORT.md" in source


def test_diagnostic_checks_both_qualification_locks_and_blob_identity():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "P5A_D2S2_ELEVATION_BOOTSTRAP_DIAGNOSTIC_LOCK.json" in source
    assert "P5A_D2S2_ONECLICK_LOCK.json" in source
    assert "diagnostic_blob_identity" in source
    assert "qualified_oneclick_blob_identity" in source
    assert "qualified_preflight_blob_identity" in source


def test_diagnostic_covers_observed_pre_report_failure_surface():
    source = SCRIPT.read_text(encoding="utf-8")
    required = (
        "elevation",
        "project_root_exists",
        "git_head",
        "git_worktree_clean_excluding_local",
        "python_executable",
        "codex_executable_exists",
        "codex_executable_hash",
        "prior_d2s2_local_root_absent",
    )
    for marker in required:
        assert marker in source


def test_spec_freezes_baseline_and_non_scientific_status():
    spec = SPEC.read_text(encoding="utf-8")
    assert "4f61aff2aff5da6a75d696cf758968bcbd697c74" in spec
    assert "NOT AUTHORIZED and NOT CONSUMED" in spec
    assert "technical observability failure only" in spec
    assert "No scientific model turn is authorized" in spec
