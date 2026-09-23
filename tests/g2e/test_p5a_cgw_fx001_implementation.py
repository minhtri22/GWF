from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADMISSION = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_admission.py"
RUNNER = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_runner.py"
VERIFIER = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_verify.py"
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_oneclick.ps1"
PREREG = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_preregister.py"
V1_LOCK = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_EXECUTION_LOCK.json"
EXEC_CONFIG = ROOT / "g2e" / "config" / "P5A_CGW_FX001_EXECUTION_CONFIG.json"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def write_fixture(workspace: Path):
    prereg = load(PREREG, "fx_prereg_fixture")
    payload = prereg.fixture_input()
    input_bytes = prereg.canonical_bytes(payload)
    task_bytes = prereg.TASK_TEXT.encode("utf-8")
    assert hashlib.sha256(input_bytes).hexdigest() == prereg.INPUT_SHA256
    assert hashlib.sha256(task_bytes).hexdigest() == prereg.TASK_SHA256
    (workspace / "input.json").write_bytes(input_bytes)
    (workspace / "TASK.md").write_bytes(task_bytes)
    return prereg, payload


def fake_bridge_config():
    return {
        "version": 3,
        "releaseVersion": "4.0.7",
        "mode": "full",
        "host": "127.0.0.1",
        "port": 17841,
        "appName": "Codex Native2",
        "browserHost": "launcher",
        "autoApproveToolCalls": False,
        "runtimeCommand": ["C:/Program Files/Codex Web GPT/Codex Web GPT.exe"],
        "automaticTunnel": {"runtimeKeyFile": "C:/redacted/runtime.key"},
    }


def fake_codex_config(workspace: Path):
    result = str(workspace / "result.json").replace("\\", "\\\\")
    return f'''model = "chatgpt-web/high"
model_provider = "openai"
openai_base_url = "http://127.0.0.1:17841/v1"
default_permissions = "g2e_p5a_cgw_fx001"

[windows]
sandbox = "elevated"

[permissions.g2e_p5a_cgw_fx001]
description = "synthetic"

[permissions.g2e_p5a_cgw_fx001.filesystem]
":root" = "read"
"{result}" = "write"

[permissions.g2e_p5a_cgw_fx001.network]
enabled = false
'''


def fake_health():
    return {
        "status": "ok",
        "service": "codex-chatgpt-web",
        "version": "4.0.7",
        "mode": "full",
        "port": 17841,
        "accepting_turns": True,
        "active_http_turns": 0,
        "active_browser_turns": 0,
    }


def test_v1_lock_is_exact_predecessor_and_dispatch_withheld():
    lock = json.loads(V1_LOCK.read_text(encoding="utf-8"))
    assert lock["status"] == "EXECUTION_ENVELOPE_LOCKED_DISPATCH_WITHHELD"
    assert lock["authorization"]["dispatch_authorized"] is False
    assert lock["attempt_id"] == "p5a-cgw-v4-p5-fx-001-attempt-001"
    assert lock["frozen_consumption"]["retry_budget"] == 0
    assert lock["frozen_route"]["model"] == "chatgpt-web/high"


def test_admission_accepts_exact_synthetic_snapshot_and_never_consumes(tmp_path, monkeypatch):
    m = load(ADMISSION, "fx_admission")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    write_fixture(workspace)

    bridge = fake_bridge_config()
    bridge_bytes = json.dumps(bridge, separators=(",", ":"), sort_keys=True).encode("utf-8")
    bridge_path = tmp_path / "config.json"
    bridge_path.write_bytes(bridge_bytes)
    monkeypatch.setattr(m, "CGW_CONFIG_SHA256", hashlib.sha256(bridge_bytes).hexdigest())

    health_path = tmp_path / "health.json"
    health_path.write_text(json.dumps(fake_health()), encoding="utf-8")
    codex_path = tmp_path / "config.toml"
    codex_path.write_text(fake_codex_config(workspace), encoding="utf-8")

    cgw = tmp_path / "cgw.exe"
    codex = tmp_path / "codex.exe"
    cgw.write_bytes(b"cgw")
    codex.write_bytes(b"codex")
    monkeypatch.setattr(m, "CGW_BINARY_SHA256", hashlib.sha256(b"cgw").hexdigest())
    monkeypatch.setattr(m, "CODEX_BINARY_SHA256", hashlib.sha256(b"codex").hexdigest())

    diagnostics = tmp_path / "diagnostics"
    diagnostics.mkdir()
    (diagnostics / "old-trace").mkdir()
    launcher = tmp_path / "launcher.jsonl"
    launcher.write_text('{"old":true}\n', encoding="utf-8")
    marker = tmp_path / "attempt_consumed.marker"

    report = m.build_admission(
        bridge_config_path=bridge_path,
        health_path=health_path,
        codex_config_path=codex_path,
        cgw_binary_path=cgw,
        codex_binary_path=codex,
        workspace=workspace,
        diagnostics_root=diagnostics,
        launcher_log=launcher,
        marker_path=marker,
    )
    assert report["status"] == "PREDISPATCH_ADMISSION_PASS"
    assert report["attempt_consumed"] is False
    assert report["model_turn_sent"] is False
    assert report["codex_config"]["model"] == "chatgpt-web/high"
    assert report["diagnostics_baseline"]["directory_names"] == ["old-trace"]


def test_admission_blocks_model_mismatch_before_consumption(tmp_path, monkeypatch):
    m = load(ADMISSION, "fx_admission_block")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    write_fixture(workspace)

    bridge = fake_bridge_config()
    bridge_bytes = json.dumps(bridge, separators=(",", ":"), sort_keys=True).encode()
    bridge_path = tmp_path / "config.json"
    bridge_path.write_bytes(bridge_bytes)
    monkeypatch.setattr(m, "CGW_CONFIG_SHA256", hashlib.sha256(bridge_bytes).hexdigest())

    health_path = tmp_path / "health.json"
    health_path.write_text(json.dumps(fake_health()), encoding="utf-8")
    text = fake_codex_config(workspace).replace('model = "chatgpt-web/high"', 'model = "chatgpt-web/medium"')
    codex_cfg = tmp_path / "config.toml"
    codex_cfg.write_text(text, encoding="utf-8")
    cgw = tmp_path / "cgw.exe"; cgw.write_bytes(b"cgw")
    codex = tmp_path / "codex.exe"; codex.write_bytes(b"codex")
    monkeypatch.setattr(m, "CGW_BINARY_SHA256", hashlib.sha256(b"cgw").hexdigest())
    monkeypatch.setattr(m, "CODEX_BINARY_SHA256", hashlib.sha256(b"codex").hexdigest())

    report = m.build_admission(
        bridge_config_path=bridge_path,
        health_path=health_path,
        codex_config_path=codex_cfg,
        cgw_binary_path=cgw,
        codex_binary_path=codex,
        workspace=workspace,
        diagnostics_root=tmp_path / "diag",
        launcher_log=tmp_path / "log",
        marker_path=tmp_path / "marker",
    )
    assert report["status"] == "PREDISPATCH_ADMISSION_BLOCKED"
    assert "CODEX_MODEL_DRIFT" in report["errors"]
    assert report["attempt_consumed"] is False


def synthetic_route_inputs():
    trace = "abc123def456"
    prefix = "call_123456789012"
    full = prefix + "ABCDEFG"
    launcher = [
        {"event": "runtime.daemon_stdout", "detail": {"line": f"[chatgpt-web] broker trace={trace} registered tokenHash=abcdef123456"}},
        {"event": "runtime.daemon_stderr", "detail": {"line": "[chatgpt-web-mcp] codex_apply_patch scope=turn"}},
        {"event": "runtime.daemon_stdout", "detail": {"line": f"[chatgpt-web] broker trace={trace} completed call={prefix} pending=0"}},
    ]
    protocol = [
        {
            "method": "item/completed",
            "rawSha256": "a" * 64,
            "item": {"id": full, "type": "fileChange", "name": "apply_patch", "status": "completed"},
        }
    ]
    surface = "S" * 32
    diagnostics = [
        {"traceId": trace, "checkpoint": "send-accepted", "surfaceId": surface, "assistantTurnCount": 0, "rawSha256": "b" * 64},
        {"traceId": trace, "checkpoint": "response-visible", "surfaceId": surface, "assistantTurnCount": 1, "rawSha256": "c" * 64},
        {"traceId": trace, "checkpoint": "turn-completed", "surfaceId": surface, "assistantTurnCount": 1, "rawSha256": "d" * 64},
    ]
    return trace, full, launcher, protocol, diagnostics


def test_route_evidence_binds_token_trace_surface_and_full_codex_item():
    m = load(RUNNER, "fx_runner_route")
    trace, full, launcher, protocol, diagnostics = synthetic_route_inputs()
    events, errors = m.derive_route_evidence(
        admission={},
        protocol_records=protocol,
        launcher_records=launcher,
        diagnostics=diagnostics,
        diagnostics_dirs=[trace + "-12345678"],
        outer_thread_id="thread-1",
        outer_turn_id="turn-1",
        terminal_status="completed",
    )
    assert errors == []
    tool = [x for x in events if x["event"] == "mcp_roundtrip"][0]
    assert tool["request_id"] == trace
    assert tool["capability_token_digest"] == "sha256-prefix12:abcdef123456"
    assert tool["invocation_id"] == full
    assert tool["tool_name"] == "codex_apply_patch"
    assert tool["executor"] == "codex"
    rendered = json.dumps(events)
    assert "runtime.key" not in rendered
    assert '"capability_token":' not in rendered


def test_route_evidence_rejects_uncorrelated_broker_completion():
    m = load(RUNNER, "fx_runner_route_bad")
    trace, _full, launcher, _protocol, diagnostics = synthetic_route_inputs()
    events, errors = m.derive_route_evidence(
        admission={},
        protocol_records=[],
        launcher_records=launcher,
        diagnostics=diagnostics,
        diagnostics_dirs=[trace + "-12345678"],
        outer_thread_id="thread-1",
        outer_turn_id="turn-1",
        terminal_status="completed",
    )
    assert "ROUTE_MCP_CALL_NOT_CORRELATED_TO_CODEX_ITEM" in errors
    tool = [x for x in events if x["event"] == "mcp_roundtrip"][0]
    assert tool["invocation_id"] is None


def materialize_verifier_fixture(tmp_path: Path, include_tool: bool = True):
    runner_mod = load(RUNNER, "fx_runner_materialize")
    verify_mod = load(VERIFIER, "fx_verify_materialize")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    prereg, payload = write_fixture(workspace)
    expected = prereg.expected_result(payload)
    (workspace / "result.json").write_text(json.dumps(expected), encoding="utf-8")

    admission = {
        "status": "PREDISPATCH_ADMISSION_PASS",
        "attempt_id": verify_mod.ATTEMPT_ID,
        "attempt_consumed": False,
        "model_turn_sent": False,
    }
    admission_path = tmp_path / "predispatch_admission.json"
    admission_path.write_text(json.dumps(admission), encoding="utf-8")

    marker_path = tmp_path / "attempt_consumed.marker"
    marker_path.write_text(
        "2026-09-23T00:00:00Z\n"
        + verify_mod.ATTEMPT_ID + "\n"
        + verify_mod.EXECUTION_CONFIG_CANONICAL_SHA256 + "\n"
        + verify_mod.sha256_file(admission_path) + "\n",
        encoding="utf-8",
    )

    trace, full, launcher, protocol_records, diagnostics = synthetic_route_inputs()
    route_events, route_errors = runner_mod.derive_route_evidence(
        admission={},
        protocol_records=protocol_records if include_tool else [],
        launcher_records=launcher,
        diagnostics=diagnostics,
        diagnostics_dirs=[trace + "-12345678"],
        outer_thread_id="thread-1",
        outer_turn_id="turn-1",
        terminal_status="completed",
    )

    protocol_path = tmp_path / "codex_protocol.jsonl"
    with protocol_path.open("w", encoding="utf-8", newline="\n") as f:
        for rec in protocol_records:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
    route_path = tmp_path / "cgw_route_evidence.jsonl"
    with route_path.open("w", encoding="utf-8", newline="\n") as f:
        for rec in route_events:
            f.write(json.dumps(rec, sort_keys=True) + "\n")

    runner = {
        "schema": "G2E-P5A-CGW-FX001-RUNNER-v1",
        "study_id": verify_mod.STUDY_ID,
        "attempt_id": verify_mod.ATTEMPT_ID,
        "route_id": verify_mod.ROUTE_ID,
        "execution_config_hash": verify_mod.EXECUTION_CONFIG_CANONICAL_SHA256,
        "predispatch_admission_sha256": verify_mod.sha256_file(admission_path),
        "codex_binary_sha256": verify_mod.CODEX_BINARY_SHA256,
        "turn_start_marker_created": True,
        "attempt_consumed": True,
        "turn_start_request_sent": True,
        "turn_start_accepted": True,
        "thread_id": "thread-1",
        "turn_id": "turn-1",
        "turn_terminal": True,
        "turn_timeout": False,
        "terminal_status": "completed",
        "driver_exception": None,
        "route_evidence_errors": route_errors,
        "protocol_sha256": verify_mod.sha256_file(protocol_path),
        "route_evidence_sha256": verify_mod.sha256_file(route_path),
        "input_unchanged": True,
        "task_unchanged": True,
    }
    runner_path = tmp_path / "runner_evidence.json"
    runner_path.write_text(json.dumps(runner), encoding="utf-8")
    return verify_mod, runner_path, protocol_path, route_path, marker_path, admission_path, workspace


def test_verifier_accepts_complete_synthetic_evidence(tmp_path):
    m, runner, protocol, route, marker, admission, workspace = materialize_verifier_fixture(tmp_path, True)
    report = m.verify(
        runner_path=runner,
        protocol_path=protocol,
        route_path=route,
        marker_path=marker,
        admission_path=admission,
        workspace=workspace,
        execution_config_hash=m.EXECUTION_CONFIG_CANONICAL_SHA256,
    )
    assert report["metrics"] == {
        "executor_completed": 1,
        "result_schema_valid": 1,
        "result_values_correct": 1,
        "mutation_scope_valid": 1,
        "attempt_attribution_valid": 1,
        "evidence_integrity_valid": 1,
    }
    assert report["adjudication_inputs"]["live_mcp_roundtrip_admitted"] is True
    assert report["verifier_assigns_scientific_verdict"] is False


def test_verifier_makes_missing_live_mcp_roundtrip_evidence_invalid(tmp_path):
    m, runner, protocol, route, marker, admission, workspace = materialize_verifier_fixture(tmp_path, False)
    report = m.verify(
        runner_path=runner,
        protocol_path=protocol,
        route_path=route,
        marker_path=marker,
        admission_path=admission,
        workspace=workspace,
        execution_config_hash=m.EXECUTION_CONFIG_CANONICAL_SHA256,
    )
    assert report["metrics"]["evidence_integrity_valid"] == 0
    assert report["adjudication_inputs"]["live_mcp_roundtrip_admitted"] is False
    assert report["adjudication_inputs"]["infrastructure_or_protocol_failure"] is True


def test_runner_has_one_consumption_boundary_and_one_turn_start():
    source = RUNNER.read_text(encoding="utf-8")
    assert source.count('"method": "turn/start"') == 1
    assert "TURN_TIMEOUT_S = 90.0" in source
    marker_index = source.index("fsync_text(marker, marker_text)")
    consumed_index = source.index('evidence["attempt_consumed"] = True')
    send_index = source.index("client.send(request)")
    assert marker_index < consumed_index < send_index
    assert 'evidence["turn_start_request_sent"] = True' in source[consumed_index:send_index]


def test_oneclick_requires_v2_dispatch_lock_and_zero_retry_shape():
    source = ONECLICK.read_text(encoding="utf-8")
    assert "P5A_CGW_FX001_EXECUTION_LOCK_V2R1.json" in source
    assert "DISPATCH_AUTHORIZED_EXECUTION_LOCK_V2R1" in source
    assert "dispatch_authorized" in source
    assert "max_dispatches" in source
    assert "PREDISPATCH_ADMISSION_BLOCKED" in source
    assert "attempt_consumed.marker" in source
    assert "Dismount-DiskImage" in source
    assert "Test-IsAdministrator" in source
    assert "Start-Process" in source
    assert "-PythonExe" in source
    assert "while (" not in source


def test_oneclick_ignores_noncritical_untracked_outputs_but_fails_closed_on_source():
    source = ONECLICK.read_text(encoding="utf-8")
    assert "Assert-ExecutionSourceClean" in source
    assert "git -C $Repo diff --quiet --no-ext-diff --" in source
    assert "git -C $Repo diff --cached --quiet --no-ext-diff --" in source
    assert "git -C $Repo ls-files --others --exclude-standard" in source
    assert '"scripts/g2e/"' in source
    assert '"g2e/docs/"' in source
    assert '"g2e/config/"' in source
    assert '"src/"' in source
    assert '"tests/g2e/"' in source
    assert '".github/workflows/"' in source
    assert "status --porcelain" not in source

    critical = (
        "scripts/g2e/",
        "g2e/docs/",
        "g2e/config/",
        "src/",
        "tests/g2e/",
        ".github/workflows/",
    )
    for benign in (".local/cache.bin", "dist/pkg.whl", "evidence/dg-p9/report.json"):
        assert not any(benign.lower().startswith(p.lower()) for p in critical)
    for dangerous in (
        "scripts/g2e/shadow.py",
        "g2e/docs/shadow.json",
        "g2e/config/shadow.json",
        "src/shadow.py",
        "tests/g2e/shadow.py",
        ".github/workflows/shadow.yml",
    ):
        assert any(dangerous.lower().startswith(p.lower()) for p in critical)


def test_implementation_does_not_change_normative_execution_config():
    config = json.loads(EXEC_CONFIG.read_text(encoding="utf-8"))
    assert config["route"]["model_slug"] == "chatgpt-web/high"
    assert config["route"]["bridge_mode"] == "full"
    assert config["consumption"]["retry_budget"] == 0
    assert config["evidence"]["live_mcp_roundtrip_required"] is True
