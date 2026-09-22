from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = ROOT / "scripts" / "g2e" / "p5a_d2s2_a2_config_serialization_preflight.py"
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_d2s2_a2_config_serialization_oneclick.ps1"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S2_A2_CONFIG_SERIALIZATION_PRETURN_AMENDMENT.md"


def _load():
    spec = importlib.util.spec_from_file_location("p5a_d2s2_a2", PREFLIGHT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_a2_preserves_scientific_identity_and_hashes():
    module = _load()
    assert module.STUDY_ID == "p5a-d2s2-isolated-volume-root-read-successor"
    assert module.ATTEMPT_ID == "p5a-d2s2-p5-fx-001-attempt-001"
    assert module.PROFILE_ID == "g2e_p5a_d2s2"
    assert module.EXPECTED_INPUT_SHA256 == "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
    assert module.EXPECTED_TASK_SHA256 == "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"
    assert module.EXPECTED_HARNESS_SHA256 == "a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8"


def test_a2_preserves_a1_ntfs_closed_set_policy(tmp_path: Path):
    module = _load()
    (tmp_path / "TASK.md").write_text("task", encoding="utf-8")
    (tmp_path / "input.json").write_text("{}", encoding="utf-8")
    (tmp_path / "System Volume Information").mkdir()

    payload, metadata, unexpected = module.classify_workspace_root(tmp_path)
    assert payload == ["TASK.md", "input.json"]
    assert metadata == ["System Volume Information"]
    assert unexpected == []

    (tmp_path / "rogue.txt").write_text("x", encoding="utf-8")
    with pytest.raises(RuntimeError, match="WORKSPACE_UNEXPECTED_ROOT_ENTRIES"):
        module.classify_workspace_root(tmp_path)


def test_a2_oneclick_uses_fresh_root_and_distinct_artifacts():
    source = ONECLICK.read_text(encoding="utf-8")
    assert "P5A_D2S2_A2_ONECLICK_LOCK.json" in source
    assert 'g2e\\.local\\P5A-D2S2-A2' in source
    assert "P5A_D2S2_A2_ONECLICK_REPORT.json" in source
    assert "P5A-D2S2-A2-TASK.vhdx" in source
    assert "P5A_D2S2_A2_LOCAL_PRETURN_PREFLIGHT.json" in source
    assert "P5A_D2S2_A1_ONECLICK_REPORT.json" not in source
    assert 'g2e\\.local\\P5A-D2S2-A1"' not in source


def test_a2_removes_overload_sensitive_replace_and_has_selftest():
    source = ONECLICK.read_text(encoding="utf-8")
    assert '$config.Replace([Environment]::NewLine, [char]10)' not in source
    assert "function Convert-ToLfText" in source
    assert '-replace "\\r\\n", "`n"' in source
    assert "[switch]$ConfigSerializationSelfTest" in source
    assert "CONFIG_SERIALIZATION_SELFTEST_PASS" in source
    assert '$configLf = Convert-ToLfText $config' in source
    assert '$configLf + "`n"' in source


def test_a2_preflight_and_oneclick_share_evidence_contract():
    preflight = PREFLIGHT.read_text(encoding="utf-8")
    oneclick = ONECLICK.read_text(encoding="utf-8")
    expected = "P5A_D2S2_A2_LOCAL_PRETURN_PREFLIGHT.json"
    assert expected in preflight
    assert expected in oneclick


def test_a2_is_strictly_no_turn():
    preflight = PREFLIGHT.read_text(encoding="utf-8")
    oneclick = ONECLICK.read_text(encoding="utf-8")
    assert '"thread/start"' in preflight
    assert '"turn/start"' not in preflight
    assert '"turn/start"' not in oneclick
    assert "scientific_attempt_consumed" in preflight
    assert "scientific_attempt_consumed" in oneclick


def test_a2_spec_requires_windows_powershell_runtime_qualification():
    normalized = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "Windows PowerShell 5.1 qualification requirement" in normalized
    assert "scientific attempt remains NOT AUTHORIZED and NOT CONSUMED" in normalized
    assert "A1 and predecessor local roots are historical evidence" in normalized
