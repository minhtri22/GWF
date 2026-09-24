from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_tc_oneclick.ps1"
OLD_ONECLICK = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_oneclick.ps1"


def source() -> str:
    return ONECLICK.read_text(encoding="utf-8")


def test_tc_oneclick_uses_new_study_attempt_config_and_root():
    s = source()
    assert 'p5a-cgw-v4-p5-fx-001-transport-corrected-qualification' in s
    assert 'p5a-cgw-v4-p5-fx-001-tc-attempt-001' in s
    assert '6b88011e0bc6ba0164a0e6f4230bb1fb8be6037d7513f348c15d39ea726816f7' in s
    assert '$LocalRoot = Join-Path $ProjectRoot "g2e\.local\P5A-CGW-FX001-TC-001"' in s
    assert 'P5A-CGW-FX001-TC-001-HANDOFF' in s
    assert 'P5A_CGW_FX001_TC_EXECUTION_REPORT.json' in s


def test_tc_oneclick_preserves_spent_predecessor_without_using_its_marker_as_new_state():
    s = source()
    assert '$SpentPredecessorRoot = Join-Path $ProjectRoot "g2e\.local\P5A-CGW-FX001-V4-002"' in s
    assert '$SpentPredecessorMarker = Join-Path $SpentPredecessorRoot "evidence\attempt_consumed.marker"' in s
    assert 'ATTEMPT_ALREADY_CONSUMED_IN_PREDECESSOR_ROOT' not in s
    assert '$LocalRoot = Join-Path $ProjectRoot "g2e\.local\P5A-CGW-FX001-V4-002"' not in s


def test_preflight_only_is_allowed_under_prereg_but_live_path_requires_future_lock():
    s = source()
    assert 'P5A_CGW_FX001_TC_PREREGISTRATION_LOCK.json' in s
    assert 'PREREGISTERED_DISPATCH_WITHHELD' in s
    assert 'P5A_CGW_FX001_TC_EXECUTION_LOCK.json' in s
    assert 'TC_LIVE_DISPATCH_LOCK_MISSING' in s

    gate = s.index('if (-not $PreflightOnly) {')
    live_lock = s.index('TC_LIVE_DISPATCH_LOCK_MISSING')
    preflight_return = s.index('if ($PreflightOnly) {', gate)
    uac = s.index('if (-not (Test-IsAdministrator))')
    assert gate < live_lock < preflight_return < uac


def test_live_lock_must_bind_exact_tc_component_blobs_before_uac():
    s = source()
    uac = s.index('if (-not (Test-IsAdministrator))')
    for token in (
        'DISPATCH_AUTHORIZED_EXECUTION_LOCK_TC1',
        'TC_ADMISSION_BLOB_DRIFT',
        'TC_RUNNER_BLOB_DRIFT',
        'TC_VERIFIER_BLOB_DRIFT',
        'TC_ONECLICK_BLOB_DRIFT',
        'TC_EXECUTION_CONFIG_BLOB_DRIFT',
        'TC_DISPATCH_CGW_IDENTITY_DRIFT',
    ):
        assert s.index(token) < uac, token


def test_tc_oneclick_invokes_only_tc_science_components():
    s = source()
    assert 'p5a_cgw_fx001_tc_admission.py' in s
    assert 'p5a_cgw_fx001_tc_runner.py' in s
    assert 'p5a_cgw_fx001_tc_verify.py' in s

    assert '$AdmissionScript = Join-Path $ProjectRoot "scripts\g2e\p5a_cgw_fx001_admission.py"' not in s
    assert '$RunnerScript = Join-Path $ProjectRoot "scripts\g2e\p5a_cgw_fx001_runner.py"' not in s
    assert '$VerifierScript = Join-Path $ProjectRoot "scripts\g2e\p5a_cgw_fx001_verify.py"' not in s


def test_preflight_returns_before_uac_vhdx_and_marker_creation():
    s = source()
    preflight_return = s.index('if ($PreflightOnly) {')
    uac = s.index('if (-not (Test-IsAdministrator))')
    local_create = s.index('New-Item -ItemType Directory -Path $VolumeDir,$CodexHome,$ReportDir,$VerificationDir')
    runner_call = s.index('& $PythonExe @RunnerArgs')
    assert preflight_return < uac < local_create < runner_call
    assert 'dispatch remains withheld; no UAC, no VHDX, no LocalRoot, no marker, no model turn.' in s


def test_tc_oneclick_keeps_exact_local_codex_and_cgw_identity_checks():
    s = source()
    assert '444A3F0008050605CAE73CD9B7A2DCAC61294062DFAAB56DD20430FD6498518B' in s
    assert '0C3EEB7CEE8D2BC4C8644DEF3C818E8B06760979572DCEDC919C38D0F38F64C4' in s
    assert 'AC152AD499B1F41B2CAFE94A3D05F5D4E4D3CD7DDBB417B9C60B118B08BC3CBB' in s
    assert 'LOCAL_CODEX_PATH_BINDING_DRIFT' in s
    assert 'CGW_LAUNCHER_HASH_DRIFT' in s


def test_tc_oneclick_remains_ascii_for_windows_powershell_51():
    s = source()
    assert all(ord(ch) < 128 for ch in s)


def test_spent_oneclick_is_unchanged_and_not_reused():
    old = OLD_ONECLICK.read_text(encoding="utf-8")
    new = source()
    assert 'P5A_CGW_FX001_EXECUTION_LOCK_V2R6.json' in old
    assert 'P5A_CGW_FX001_EXECUTION_LOCK_V2R6.json' not in new
    assert 'p5a-cgw-v4-p5-fx-001-attempt-001' in old
    assert 'p5a-cgw-v4-p5-fx-001-attempt-001' not in new
