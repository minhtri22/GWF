from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADMISSION = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_tc2_admission.py"
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_tc2_oneclick.ps1"
PLAN = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC2_SEMANTIC_ADMISSION_REPAIR_PLAN.md"


def load_admission():
    spec = importlib.util.spec_from_file_location("tc2_admission", ADMISSION)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def valid_config():
    exe = str(Path(sys.executable).resolve())
    root = str(Path(exe).parent)
    broker = r"\\.\pipe\codex-chatgpt-web-test" if os.name == "nt" else str(Path(root) / "broker.sock")
    runtime = [exe, str(Path(root) / "entry.js")]
    if os.name == "nt":
        # TC-002 local execution is Windows and freezes bun.exe. Unit-test the
        # remainder of the semantic guard cross-platform by bypassing only the
        # Windows-only basename condition on non-local CI executable identity.
        runtime[0] = exe
    return {
        "version": 3,
        "releaseVersion": "4.0.7",
        "mode": "full",
        "subagentProtocol": "compatibility-v1",
        "host": "127.0.0.1",
        "port": 17841,
        "contextWindow": 256000,
        "appName": "Codex Native2",
        "browserHost": "launcher",
        "browserHostDescriptorPath": str(Path(root) / "descriptor.json"),
        "chromeExecutablePath": str(Path(root) / "chrome.exe"),
        "storageStatePath": str(Path(root) / "storage.json"),
        "brokerSocketPath": broker,
        "headed": True,
        "solAvailable": True,
        "proAvailable": False,
        "experimentalBiggerContext": True,
        "autoApproveToolCalls": False,
        "controlToken": "A" * 43,
        "runtimeCommand": runtime,
        "tunnel": {
            "binaryPath": str(Path(root) / "tunnel.exe"),
            "tunnelId": "tunnel_" + "a" * 32,
            "runtimeKeyFile": str(Path(root) / "runtime.key"),
            "profileDir": str(Path(root) / "profile"),
            "profileName": "p5a",
            "alias": "p5a",
        },
    }


def test_admission_no_longer_enforces_raw_config_hash():
    s = ADMISSION.read_text(encoding="utf-8")
    assert "CGW_CONFIG_SHA256" not in s
    assert "CGW_CONFIG_HASH_DRIFT" not in s
    assert '"whole_file_hash_enforced": False' in s
    assert '"raw_sha256_provenance_only"' in s


def test_admission_freezes_observed_semantics():
    s = ADMISSION.read_text(encoding="utf-8")
    for token in (
        'subagent == "compatibility-v1"',
        'raw.get("contextWindow") == 256000',
        'sol is True',
        'pro is False',
        'bigger is True',
        'stall is None or stall == 300',
        'len(runtime) == 2',
        'Path(runtime_executable).name.lower() == "bun.exe"',
    ):
        assert token in s


def test_project_bridge_accepts_valid_semantics_except_windows_bun_identity_under_ci():
    mod = load_admission()
    cfg = valid_config()
    raw = json.dumps(cfg).encode("utf-8")
    _, errors = mod.project_bridge(cfg, raw)
    if os.name == "nt" and Path(sys.executable).name.lower() != "bun.exe":
        assert errors == ["CGW_RUNTIME_EXECUTABLE_IDENTITY_DRIFT"]
    else:
        assert errors == []


def test_project_bridge_rejects_material_semantic_drift():
    mod = load_admission()
    cfg = valid_config()
    cfg["experimentalBiggerContext"] = False
    cfg["autoApproveToolCalls"] = True
    cfg["contextWindow"] = 128000
    _, errors = mod.project_bridge(cfg, json.dumps(cfg).encode("utf-8"))
    assert "CGW_BIGGER_CONTEXT_DRIFT" in errors
    assert "CGW_AUTO_APPROVE_NOT_FALSE" in errors
    assert "CGW_CONTEXT_WINDOW_DRIFT" in errors


def test_tc2_oneclick_isolated_from_tc001_and_old_lock():
    s = ONECLICK.read_text(encoding="utf-8")
    assert "P5A-CGW-FX001-TC-002" in s
    assert "P5A-CGW-FX001-TC-001" not in s
    assert "P5A_CGW_FX001_TC2_EXECUTION_LOCK.json" in s
    assert "P5A_CGW_FX001_TC_EXECUTION_LOCK.json" not in s
    assert "p5a_cgw_fx001_tc2_admission.py" in s
    assert "p5a_cgw_fx001_tc2_oneclick.ps1" in s
    assert "DISPATCH_AUTHORIZED_EXECUTION_LOCK_TC2" in s


def test_plan_preserves_attempt_and_forbids_live_activation():
    s = PLAN.read_text(encoding="utf-8")
    assert "RESERVED_UNCONSUMED" in s
    assert "not a retry of a consumed attempt" in s
    assert "retry budget 0" in s
    assert "No live/model/browser/MCP execution is authorized by this plan alone." in s
