from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = ROOT / "scripts" / "g2e" / "p5a_d2s2_a1_ntfs_metadata_preflight.py"
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_d2s2_a1_ntfs_metadata_oneclick.ps1"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S2_A1_NTFS_METADATA_PRETURN_AMENDMENT.md"


def _load():
    spec = importlib.util.spec_from_file_location("p5a_d2s2_a1", PREFLIGHT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_a1_preserves_scientific_identity_and_frozen_hashes():
    module = _load()
    assert module.STUDY_ID == "p5a-d2s2-isolated-volume-root-read-successor"
    assert module.ATTEMPT_ID == "p5a-d2s2-p5-fx-001-attempt-001"
    assert module.PROFILE_ID == "g2e_p5a_d2s2"
    assert module.EXPECTED_INPUT_SHA256 == "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
    assert module.EXPECTED_TASK_SHA256 == "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"
    assert module.EXPECTED_HARNESS_SHA256 == "a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8"


def test_a1_accepts_only_task_payload_plus_optional_ntfs_metadata(tmp_path: Path):
    module = _load()
    (tmp_path / "TASK.md").write_text("task", encoding="utf-8")
    (tmp_path / "input.json").write_text("{}", encoding="utf-8")
    (tmp_path / "System Volume Information").mkdir()

    payload, metadata, unexpected = module.classify_workspace_root(tmp_path)
    assert payload == ["TASK.md", "input.json"]
    assert metadata == ["System Volume Information"]
    assert unexpected == []


def test_a1_accepts_payload_when_system_volume_information_absent(tmp_path: Path):
    module = _load()
    (tmp_path / "TASK.md").write_text("task", encoding="utf-8")
    (tmp_path / "input.json").write_text("{}", encoding="utf-8")

    payload, metadata, unexpected = module.classify_workspace_root(tmp_path)
    assert payload == ["TASK.md", "input.json"]
    assert metadata == []
    assert unexpected == []


def test_a1_rejects_any_other_root_entry(tmp_path: Path):
    module = _load()
    (tmp_path / "TASK.md").write_text("task", encoding="utf-8")
    (tmp_path / "input.json").write_text("{}", encoding="utf-8")
    (tmp_path / "unexpected.txt").write_text("x", encoding="utf-8")

    with pytest.raises(RuntimeError, match="WORKSPACE_UNEXPECTED_ROOT_ENTRIES"):
        module.classify_workspace_root(tmp_path)


def test_a1_rejects_system_volume_information_as_file(tmp_path: Path):
    module = _load()
    (tmp_path / "TASK.md").write_text("task", encoding="utf-8")
    (tmp_path / "input.json").write_text("{}", encoding="utf-8")
    (tmp_path / "System Volume Information").write_text("not-dir", encoding="utf-8")

    with pytest.raises(RuntimeError, match="SYSTEM_VOLUME_INFORMATION_NOT_DIRECTORY"):
        module.classify_workspace_root(tmp_path)


def test_a1_profile_still_requires_root_read_exact_result_write_network_off(tmp_path: Path):
    module = _load()
    workspace = tmp_path / "S"
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


def test_a1_oneclick_is_fresh_root_fail_closed_and_preserves_predecessor():
    source = ONECLICK.read_text(encoding="utf-8")
    assert "P5A_D2S2_A1_ONECLICK_LOCK.json" in source
    assert 'g2e\\.local\\P5A-D2S2-A1' in source
    assert "P5A_D2S2_A1_ONECLICK_REPORT.json" in source
    assert "System Volume Information" in source
    assert "ISOLATED_VOLUME_UNEXPECTED_ROOT_ENTRIES" in source
    assert "ISOLATED_VOLUME_TASK_PAYLOAD_DRIFT" in source
    assert "P5A-D2S2-A1-TASK.vhdx" in source
    assert "Invoke-Git -Root" in source
    assert 'g2e\\.local\\P5A-D2S2"' not in source


def test_a1_remains_strictly_no_turn():
    preflight = PREFLIGHT.read_text(encoding="utf-8")
    oneclick = ONECLICK.read_text(encoding="utf-8")
    assert '"thread/start"' in preflight
    assert '"turn/start"' not in preflight
    assert '"turn/start"' not in oneclick
    assert "scientific_attempt_consumed" in preflight
    assert "scientific_attempt_consumed" in oneclick


def test_a1_spec_is_pre_scientific_and_closed_set():
    normalized = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "scientific attempt remains NOT AUTHORIZED and NOT CONSUMED" in normalized
    assert "System Volume Information" in normalized
    assert "No other file or directory is admissible" in normalized
    assert "does not authorize" in normalized


def test_a1_oneclick_and_preflight_share_evidence_filename_contract():
    preflight = PREFLIGHT.read_text(encoding="utf-8")
    oneclick = ONECLICK.read_text(encoding="utf-8")
    expected = "P5A_D2S2_A1_LOCAL_PRETURN_PREFLIGHT.json"
    assert expected in preflight
    assert expected in oneclick
    assert "P5A_D2S2_LOCAL_PRETURN_PREFLIGHT.json" not in oneclick


def test_a1_does_not_consume_predecessor_report_path():
    source = ONECLICK.read_text(encoding="utf-8")
    assert "P5A_D2S2_A1_ONECLICK_REPORT.json" in source
    assert "P5A_D2S2_ONECLICK_REPORT.json" not in source
