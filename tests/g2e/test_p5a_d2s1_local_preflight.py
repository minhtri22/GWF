from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "g2e" / "p5a_d2s1_local_preflight.py"


def _load():
    spec = importlib.util.spec_from_file_location("p5a_d2s1_local_preflight", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_preflight_constants_are_frozen():
    module = _load()
    assert module.ATTEMPT_ID == "p5a-d2s1-p5-fx-001-attempt-001"
    assert module.PROFILE_ID == "g2e_p5a_d2s1"
    assert module.EXPECTED_HARNESS_SHA256 == "a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8"
    assert module.EXPECTED_CONFIG_TOML_SHA256 == "a21289d995d75416ade0f4483bb93f0c54cf1808f0c2ae289c29fe89a9050cd4"
    assert module.EXPECTED_EXECUTION_CONFIG_HASH == "72874872ea241efecbdd537e0a7fbf0718fd036cf4abd564b27b0bcd03dd81ce"


def test_setup_error_redaction_hides_user_identity(monkeypatch):
    module = _load()
    monkeypatch.setenv("USERPROFILE", r"C:\\Users\\Alice")
    monkeypatch.setenv("USERNAME", "Alice")
    raw = (
        r"orchestrator_helper_launch_failed: failed C:\\Users\\Alice\\tool.exe "
        r"for Alice"
    )
    redacted = module.redact_setup_error(raw)
    assert "Alice" not in redacted
    assert "<userprofile>" in redacted or "<user>" in redacted


def test_profile_lookup_is_exact_and_requires_allowed():
    module = _load()
    result = {
        "data": [
            {"id": ":workspace", "allowed": True},
            {"id": module.PROFILE_ID, "allowed": True},
        ]
    }
    assert module.find_profile(result, module.PROFILE_ID) == {
        "id": module.PROFILE_ID,
        "allowed": True,
    }
    assert module.find_profile(result, "missing") is None


def test_require_under_fails_closed(tmp_path: Path):
    module = _load()
    root = tmp_path / "local"
    root.mkdir()
    inside = root / "evidence"
    outside = tmp_path / "outside"

    assert module.require_under(inside, root, "EVIDENCE_DIR") == inside.resolve()
    with pytest.raises(RuntimeError, match="EVIDENCE_DIR_OUTSIDE_LOCAL_ROOT"):
        module.require_under(outside, root, "EVIDENCE_DIR")


def test_script_is_strictly_no_turn():
    source = SCRIPT.read_text(encoding="utf-8")

    assert '"experimentalApi": True' in source
    assert '"permissionProfile/list"' in source
    assert '"permissions": PROFILE_ID' in source
    assert '"thread/start"' in source
    assert '"windowsSandbox/readiness"' in source
    assert '"windowsSandbox/setupStart"' in source
    assert '"mode": "elevated"' in source
    assert '"windowsSandbox/setupCompleted"' in source
    assert "WINDOWS_SANDBOX_SETUP_TIMEOUT_S = 180.0" in source

    # Scientific dispatch must not exist anywhere in this preflight implementation.
    assert '"turn/start"' not in source
    assert "TURN_START_SENT" not in source


def test_script_does_not_use_legacy_sandbox_fields():
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"sandboxPolicy"' not in source
    assert '"readOnlyAccess"' not in source
    assert '"permissionProfile":' not in source


def test_windows_setup_gate_fails_closed_and_requires_ready():
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'readiness_before_status == "updateRequired"' in source
    assert 'setup_params.get("mode") == "elevated"' in source
    assert 'setup_params.get("success") is True' in source
    assert 'readiness_after_status != "ready"' in source
    assert "CONFIG_TOML_MUTATED_BY_WINDOWS_SANDBOX_SETUP" in source
    assert "windows_sandbox_setup_error_code" in source
    assert "windows_sandbox_setup_error_redacted" in source
    assert "windows_sandbox_setup_error_sha256" in source
    assert "redact_setup_error(setup_error)" in source


def test_preflight_uses_only_local_mutable_paths():
    source = SCRIPT.read_text(encoding="utf-8")
    for label in ("EXEC_DIR", "PROFILE_PACK_DIR", "CODEX_HOME", "EVIDENCE_DIR"):
        assert f'require_under(Path(args.' in source or "require_under(" in source
    assert "REFUSED_OUTSIDE_LOCAL_ROOT" not in source
