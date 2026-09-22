from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = ROOT / "scripts" / "g2e" / "p5a_d2s2_isolated_volume_preflight.py"
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_d2s2_isolated_volume_oneclick.ps1"


def _load():
    spec = importlib.util.spec_from_file_location("p5a_d2s2_isolated_volume_preflight", PREFLIGHT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_d2s2_identity_and_frozen_fixture_hashes():
    module = _load()
    assert module.STUDY_ID == "p5a-d2s2-isolated-volume-root-read-successor"
    assert module.ATTEMPT_ID == "p5a-d2s2-p5-fx-001-attempt-001"
    assert module.PROFILE_ID == "g2e_p5a_d2s2"
    assert module.EXPECTED_INPUT_SHA256 == "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
    assert module.EXPECTED_TASK_SHA256 == "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"
    assert module.EXPECTED_HARNESS_SHA256 == "a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8"


def test_dynamic_profile_requires_root_read_exact_result_write_and_network_off(tmp_path: Path):
    module = _load()
    workspace = tmp_path / "R"
    workspace.mkdir()
    result_path = str(workspace / "result.json").replace("\\", "\\\\")
    config = tmp_path / "config.toml"
    config.write_text(
        f'''default_permissions = "{module.PROFILE_ID}"

[windows]
sandbox = "elevated"

[permissions.{module.PROFILE_ID}.filesystem]
":root" = "read"
"{result_path}" = "write"

[permissions.{module.PROFILE_ID}.network]
enabled = false
''',
        encoding="utf-8",
    )
    module.verify_profile(config, workspace)


def test_profile_rejects_missing_root_read(tmp_path: Path):
    module = _load()
    workspace = tmp_path / "R"
    workspace.mkdir()
    result_path = str(workspace / "result.json").replace("\\", "\\\\")
    config = tmp_path / "config.toml"
    config.write_text(
        f'''default_permissions = "{module.PROFILE_ID}"

[windows]
sandbox = "elevated"

[permissions.{module.PROFILE_ID}.filesystem]
"{result_path}" = "write"

[permissions.{module.PROFILE_ID}.network]
enabled = false
''',
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="PROFILE_ROOT_READ_MISSING"):
        module.verify_profile(config, workspace)


def test_preflight_is_strictly_no_turn():
    source = PREFLIGHT.read_text(encoding="utf-8")
    assert '"windowsSandbox/setupStart"' in source
    assert '"thread/start"' in source
    assert '"turn/start"' not in source
    assert "scientific_attempt_consumed" in source


def test_oneclick_is_fail_closed_and_report_generating():
    source = ONECLICK.read_text(encoding="utf-8")
    assert '$ErrorActionPreference = "Stop"' in source
    assert "P5A_D2S2_ONECLICK_LOCK.json" in source
    assert "git switch --detach" in source
    assert "D2S2_LOCAL_ROOT_ALREADY_EXISTS" in source
    assert "create vdisk" in source
    assert "maximum=128" in source
    assert '":root" = "read"' in source
    assert "P5A_D2S2_ONECLICK_REPORT.json" in source
    assert "P5A_D2S2_ONECLICK_REPORT.md" in source
    assert "SCIENTIFIC_DISPATCH_FIREWALL_VIOLATION" in source
    assert "scientific_attempt_consumed" in source


def test_oneclick_uses_deterministic_drive_order():
    source = ONECLICK.read_text(encoding="utf-8")
    assert '@("R","S","T","U","V","W","X","Y","Z")' in source
