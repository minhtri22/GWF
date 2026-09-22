from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "g2e" / "p5a_d2s3_scientific_runner.py"
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_d2s3_scientific_oneclick.ps1"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S3_SCIENTIFIC_PREDISPATCH_REPAIR_001_SPEC.md"

EXPECTED_PREFLIGHT_BLOB = "ecd0af7cd487e14ea1691f4195af1d147efd0fe4"


def _load_runner():
    spec = importlib.util.spec_from_file_location("d2s3_science_repair_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_preflight_identity_is_verified_as_git_blob_not_file_sha256():
    source = RUNNER.read_text(encoding="utf-8")
    assert f'PREFLIGHT_MODULE_GIT_BLOB = "{EXPECTED_PREFLIGHT_BLOB}"' in source
    assert '"rev-parse",' in source
    assert '"HEAD:scripts/g2e/p5a_d2s3_platform_no_turn_preflight.py"' in source
    assert "sha256_file(path) != PREFLIGHT_MODULE" not in source

    module = _load_runner()
    loaded = module.load_preflight_module(ROOT)
    assert loaded is not None


def test_preflight_git_blob_drift_fails_closed(monkeypatch):
    module = _load_runner()
    monkeypatch.setattr(module, "run_git", lambda *args, **kwargs: "0" * 40)
    with pytest.raises(RuntimeError, match="PREFLIGHT_MODULE_BLOB_DRIFT"):
        module.load_preflight_module(ROOT)


def test_scientific_dispatch_semantics_remain_single_shot():
    source = RUNNER.read_text(encoding="utf-8")
    assert source.count('"method": "turn/start"') == 1
    marker = source.index("fsync_text(marker_path, marker_text)")
    send = source.index("client.send(request)")
    assert marker < send
    assert 'evidence["scientific_attempt_consumed"] = True' in source[marker:send]
    assert "TURN_TIMEOUT_S = 90.0" in source
    assert '"sandboxPolicy"' not in source


def test_oneclick_uses_fresh_science002_and_never_reuses_science001():
    source = ONECLICK.read_text(encoding="utf-8")
    assert "P5A-D2S3-SCIENCE-002" in source
    assert "P5A-D2S3-SCIENCE-001" not in source
    assert "SCIENTIFIC_ROOT_ALREADY_EXISTS_NO_RETRY" in source
    assert "P5A_D2S3_SCIENTIFIC_PREDISPATCH_REPAIR_001_LOCK.json" in source
    assert "Remove-Item -LiteralPath $LocalRoot" not in source


def test_native_capture_preserves_nonzero_exit_and_stderr_contract():
    source = ONECLICK.read_text(encoding="utf-8")
    assert "function Invoke-NativeCaptured" in source
    assert '$ErrorActionPreference = "Continue"' in source
    assert "G2E_NATIVE_STDERR_SENTINEL" in source
    assert "SCIENCE_NATIVE_CAPTURE_EXITCODE_SELFTEST_FAILED" in source
    assert "SCIENCE_NATIVE_CAPTURE_STDERR_SELFTEST_FAILED" in source
    assert "$RunnerNative.ExitCode" in source
    assert "$VerifierNative.ExitCode" in source


def test_cleanup_is_still_non_bypassable():
    source = ONECLICK.read_text(encoding="utf-8")
    start = source.index("# PROTECTED_SCIENTIFIC_VHDX_BODY_START")
    end = source.index("# PROTECTED_SCIENTIFIC_VHDX_BODY_END")
    protected = source[start:end]
    assert "Dismount-DiskImage -ImagePath $VhdxPath" in protected
    assert "attached_after_cleanup" in protected
    assert "exit " not in protected


def test_repair_spec_preserves_frozen_science():
    text = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "PRE-DISPATCH-REPAIR-ONLY" in text
    assert "Frozen scientific semantics MUST remain unchanged" in text
    assert "df5308888eac7fa0b876f2cd68a51d0f2dd80a1b7c6d556cb04c854067b86e81" in text
    assert "permission profile `g2e_p5a_d2s3`" in text
    assert "exactly one scientific `turn/start` code path" in text
    assert "No retry is authorized after the attempt-consumption marker exists." in text
