from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE_PATH = ROOT / "scripts" / "g2e" / "p5a_codex_discovery.py"
SPEC_PATH = ROOT / "g2e" / "docs" / "P5A_CODEX_DISCOVERY_PREPARATION.md"


def _load_probe():
    spec = importlib.util.spec_from_file_location("p5a_codex_discovery", PROBE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _fake_codex(path: Path, *, omit_token: str | None = None) -> Path:
    tokens = [
        "initialize",
        "thread/start",
        "thread/resume",
        "turn/start",
        "item/started",
        "item/completed",
        "thread/fork",
        "turn/steer",
        "sessionId",
        "requestApproval",
        "mcpServer",
        "skill",
        "command/exec",
    ]
    if omit_token:
        tokens.remove(omit_token)
    script = f'''#!/usr/bin/env python3
import json
import pathlib
import sys

args = sys.argv[1:]
if args == ["--version"]:
    print("codex-cli 9.9.9-fixture")
    raise SystemExit(0)

if args == ["app-server", "--help"]:
    print("fixture app-server help")
    raise SystemExit(0)

if len(args) == 4 and args[:3] == ["app-server", "generate-json-schema", "--out"]:
    out = pathlib.Path(args[3])
    out.mkdir(parents=True, exist_ok=True)
    payload = {{"methods": {tokens!r}}}
    (out / "protocol.json").write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    raise SystemExit(0)

if args == ["app-server"]:
    line = sys.stdin.readline()
    msg = json.loads(line)
    if msg.get("method") != "initialize":
        print(json.dumps({{"id": msg.get("id"), "error": {{"message": "not initialized"}}}}), flush=True)
        raise SystemExit(1)
    print(json.dumps({{
        "id": msg["id"],
        "result": {{
            "userAgent": "fixture-agent",
            "platformFamily": "fixture",
            "platformOs": "fixture-os",
            "accountEmail": "must-not-persist@example.com",
            "token": "must-not-persist"
        }}
    }}), flush=True)
    sys.stdin.readline()
    raise SystemExit(0)

raise SystemExit(3)
'''
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)
    return path


def test_p5a_spec_separates_documented_structural_and_functional_evidence():
    text = SPEC_PATH.read_text(encoding="utf-8")
    assert "D0 — documented" in text
    assert "D1 — structural actual-harness discovery" in text
    assert "D2 — bounded functional harness qualification" in text
    assert "D0 never sets" in text and "AgentCapability.available=true" in text
    assert "No `latest` alias becomes canonical evidence." in text


def test_p5a_probe_qualifies_minimum_structural_fake_harness(tmp_path: Path):
    probe = _load_probe()
    fake = _fake_codex(tmp_path / "codex")
    output = tmp_path / "P5A_CODEX_DISCOVERY.json"
    report = probe.discover(str(fake), output, tmp_path / "work", 3.0)

    assert report["status"] == "D1_MINIMUM_QUALIFIED"
    assert report["codex_version_stdout"] == "codex-cli 9.9.9-fixture"
    assert all(report["required_protocol_tokens"].values())
    assert report["initialize_handshake"]["success"] is True
    assert report["functional_task_executed"] is False
    assert report["secrets_persisted"] is False
    assert report["generated_schema_files"]
    assert len(report["schema_inventory_digest"]) == 64

    persisted = output.read_text(encoding="utf-8")
    assert "must-not-persist@example.com" not in persisted
    assert "must-not-persist" not in persisted
    assert report["initialize_handshake"]["sanitized_response"]["metadata"] == {
        "platformFamily": "fixture",
        "platformOs": "fixture-os",
        "userAgent": "fixture-agent",
    }


def test_p5a_probe_fails_closed_when_required_protocol_token_missing(tmp_path: Path):
    probe = _load_probe()
    fake = _fake_codex(tmp_path / "codex", omit_token="turn/start")
    report = probe.discover(
        str(fake),
        tmp_path / "discovery.json",
        tmp_path / "work",
        3.0,
    )
    assert report["status"] == "D1_MINIMUM_NOT_QUALIFIED"
    assert report["required_protocol_tokens"]["turn/start"] is False
    assert any("missing required protocol tokens" in item for item in report["errors"])


def test_p5a_probe_fails_closed_when_harness_missing(tmp_path: Path):
    probe = _load_probe()
    report = probe.discover(
        str(tmp_path / "not-a-codex"),
        tmp_path / "discovery.json",
        tmp_path / "work",
        1.0,
    )
    assert report["status"] == "HARNESS_NOT_FOUND"
    assert report["functional_task_executed"] is False
    assert report["secrets_persisted"] is False


def test_p5a_probe_never_dispatches_model_turn_or_proof():
    source = PROBE_PATH.read_text(encoding="utf-8")
    forbidden = (
        "ProofObligation",
        "ExecutionAttemptEnvelope",
        "AgentBinding",
        '["exec"]',
    )
    for token in forbidden:
        assert token not in source
    assert '"method": "thread/start"' not in source
    assert "'method': 'thread/start'" not in source


def test_p5a_windows_entrypoint_is_read_only_wrapper():
    text = (ROOT / "scripts" / "g2e" / "p5a_codex_discovery.ps1").read_text(encoding="utf-8")
    assert "p5a_codex_discovery.py" in text
    assert "P5A_CODEX_DISCOVERY.json" in text
    assert "thread/start" not in text
    assert '["exec"]' not in text
