from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "scripts" / "g2e" / "p5a_d2s3_official_release_asset_audit.py"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S3_RELEASE_COHERENT_INSTRUMENT_PREIMPLEMENTATION.md"


def _load():
    spec = importlib.util.spec_from_file_location("d2s3_audit", AUDIT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _record(markers: dict[str, bool]):
    return {"binary": {"markers": markers}}


def test_audit_freezes_exact_release_and_asset_digests():
    module = _load()
    assert module.TAG == "rust-v0.153.4"
    assert module.SOURCE_COMMIT == "3d2ee51ca2d5db578f328aa75e20aa22c0197c9a"
    codex = module.ASSETS["codex"]
    helper = module.ASSETS["helper"]
    assert codex["archive_sha256"] == "c016b0e6968b78586919c720d2685a03712f6d5f11bcd9d6f92c91eb8c41ba16"
    assert codex["binary_sha256"] == "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b"
    assert helper["archive_sha256"] == "256c4deb16946a01a52156e8fd619baec38743ff482741767ab5fdb4079e97cb"
    assert helper["binary_sha256"] == "0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4"


def test_adjudication_passes_only_source_compatible_marker_matrix():
    module = _load()
    codex = _record({
        "interactive-provision": False,
        "full": True,
        "provision-only": True,
        "read-acls-only": False,
    })
    helper = _record({
        "interactive-provision": False,
        "full": True,
        "provision-only": True,
        "read-acls-only": True,
    })
    passed, reasons = module.adjudicate(codex, helper)
    assert passed is True
    assert reasons == []


def test_adjudication_fails_closed_on_interactive_provision():
    module = _load()
    codex = _record({
        "interactive-provision": True,
        "full": True,
        "provision-only": True,
        "read-acls-only": False,
    })
    helper = _record({
        "interactive-provision": False,
        "full": True,
        "provision-only": True,
        "read-acls-only": True,
    })
    passed, reasons = module.adjudicate(codex, helper)
    assert passed is False
    assert "CODEX_CONTAINS_INTERACTIVE_PROVISION" in reasons


def test_audit_never_executes_downloaded_binaries():
    source = AUDIT.read_text(encoding="utf-8")
    forbidden = [
        "subprocess",
        "os.system",
        "Popen(",
        "Start-Process",
        "app-server",
        "turn/start",
        "thread/start",
        "windowsSandbox/",
    ]
    for token in forbidden:
        assert token not in source
    assert '"executables_invoked": False' in source
    assert '"model_turn_executed": False' in source
    assert '"scientific_attempt_consumed": False' in source


def test_spec_stops_before_local_staging_on_incoherence():
    normalized = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "S3-I0 — official-release asset coherence audit" in normalized
    assert "OFFICIAL_RELEASE_PROVENANCE_INCOHERENT" in normalized
    assert "D2-S3 MUST STOP before local staging" in normalized
    assert "global `%LOCALAPPDATA%\\Programs\\OpenAI\\Codex` installation must not be modified" in normalized
