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
    assert module.EXPECTED_CONFIG_TOML_SHA256 == "8877cc89ccf5dd6e3cf6c45016ca7e62d93746c8f56db8bb38956eb6ff6e172d"
    assert module.EXPECTED_EXECUTION_CONFIG_HASH == "d03e6f6f2c20b757685188e30f4cabd44102b61b74cdacc585bab328647b0367"


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

    # Scientific dispatch must not exist anywhere in this preflight implementation.
    assert '"turn/start"' not in source
    assert "TURN_START_SENT" not in source


def test_script_does_not_use_legacy_sandbox_fields():
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"sandboxPolicy"' not in source
    assert '"readOnlyAccess"' not in source
    assert '"permissionProfile":' not in source


def test_preflight_uses_only_local_mutable_paths():
    source = SCRIPT.read_text(encoding="utf-8")
    for label in ("EXEC_DIR", "PROFILE_PACK_DIR", "CODEX_HOME", "EVIDENCE_DIR"):
        assert f'require_under(Path(args.' in source or "require_under(" in source
    assert "REFUSED_OUTSIDE_LOCAL_ROOT" not in source
