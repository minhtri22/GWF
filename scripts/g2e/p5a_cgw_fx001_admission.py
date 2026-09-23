from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any

STUDY_ID = "p5a-cgw-v4-p5-fx-001-functional-qualification"
ATTEMPT_ID = "p5a-cgw-v4-p5-fx-001-attempt-001"
ROUTE_ID = "p5a-cgw"

V1_LOCK_BLOB = "22cefe57c214cf58c759fd76ad25fff9dba834cb"
EXECUTION_CONFIG_BLOB = "5551262c62389eaecf928e8d60fbde22e39d3b1e"
CGW_RELEASE = "4.0.7"
CGW_SOURCE_COMMIT = "b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494"
CGW_BINARY_SHA256 = "ac152ad499b1f41b2cafe94a3d05f5d4e4d3cd7ddbb417b9c60b118b08bc3cbb"
CGW_CONFIG_SHA256 = "f8ba628c60faf5c95409ee3a37ad359f74dd0eb41bb961312b67758f9ba53858"
CODEX_BINARY_SHA256 = "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b"
INPUT_SHA256 = "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
TASK_SHA256 = "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"
MODEL = "chatgpt-web/high"
BASE_URL = "http://127.0.0.1:17841/v1"
PROFILE_ID = "g2e_p5a_cgw_fx001"


class AdmissionError(ValueError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require(condition: bool, code: str, errors: list[str]) -> None:
    if not condition:
        errors.append(code)


def classify_workspace(workspace: Path) -> dict[str, Any]:
    entries = {p.name: p for p in workspace.iterdir()}
    payload = sorted(name for name in ("TASK.md", "input.json") if name in entries and entries[name].is_file())
    support = sorted(name for name in ("System Volume Information",) if name in entries and entries[name].is_dir())
    result = sorted(name for name in ("result.json",) if name in entries and entries[name].is_file())
    allowed = set(payload + support + result)
    unexpected = sorted(name for name in entries if name not in allowed)
    return {"payload": payload, "support": support, "result": result, "unexpected": unexpected}


def project_bridge(raw: dict[str, Any], raw_bytes: bytes) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    require(raw.get("version") == 3, "CGW_CONFIG_VERSION", errors)
    require(raw.get("releaseVersion") == CGW_RELEASE, "CGW_RELEASE_VERSION", errors)
    require(raw.get("mode") == "full", "CGW_MODE_NOT_FULL", errors)
    require(raw.get("host") == "127.0.0.1", "CGW_HOST_NOT_LOOPBACK", errors)
    require(raw.get("port") == 17841, "CGW_PORT_DRIFT", errors)
    require(raw.get("appName") == "Codex Native2", "CGW_CONNECTOR_DRIFT", errors)
    require(raw.get("autoApproveToolCalls") is False, "CGW_AUTO_APPROVE_NOT_FALSE", errors)
    require(isinstance(raw.get("runtimeCommand"), list) and len(raw["runtimeCommand"]) >= 1, "CGW_RUNTIME_COMMAND", errors)
    require(bool(raw.get("tunnel") or raw.get("automaticTunnel") or raw.get("manualTunnel")), "CGW_TUNNEL_MISSING", errors)
    require(sha256_bytes(raw_bytes) == CGW_CONFIG_SHA256, "CGW_CONFIG_HASH_DRIFT", errors)
    return {
        "release_version": raw.get("releaseVersion"),
        "mode": raw.get("mode"),
        "host": raw.get("host"),
        "port": raw.get("port"),
        "connector": raw.get("appName"),
        "browser_host": raw.get("browserHost"),
        "auto_approve_tool_calls": raw.get("autoApproveToolCalls"),
        "tunnel_present": bool(raw.get("tunnel") or raw.get("automaticTunnel") or raw.get("manualTunnel")),
        "raw_sha256": sha256_bytes(raw_bytes),
    }, errors


def project_health(raw: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    require(raw.get("status") == "ok", "CGW_HEALTH_STATUS", errors)
    require(raw.get("service") == "codex-chatgpt-web", "CGW_HEALTH_SERVICE", errors)
    require(raw.get("version") == CGW_RELEASE, "CGW_HEALTH_VERSION", errors)
    require(raw.get("mode") == "full", "CGW_HEALTH_MODE", errors)
    require(raw.get("port") == 17841, "CGW_HEALTH_PORT", errors)
    require(raw.get("accepting_turns") is True, "CGW_NOT_ACCEPTING_TURNS", errors)
    require(raw.get("active_http_turns") == 0, "CGW_HTTP_NOT_IDLE", errors)
    require(raw.get("active_browser_turns") == 0, "CGW_BROWSER_NOT_IDLE", errors)
    return {
        "status": raw.get("status"),
        "service": raw.get("service"),
        "version": raw.get("version"),
        "mode": raw.get("mode"),
        "port": raw.get("port"),
        "accepting_turns": raw.get("accepting_turns"),
        "active_http_turns": raw.get("active_http_turns"),
        "active_browser_turns": raw.get("active_browser_turns"),
    }, errors


def project_codex_config(text: str, workspace: Path) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        return {}, [f"CODEX_CONFIG_TOML:{exc}"]

    require(raw.get("model") == MODEL, "CODEX_MODEL_DRIFT", errors)
    require(raw.get("model_provider") in (None, "openai"), "CODEX_PROVIDER_DRIFT", errors)
    require(raw.get("openai_base_url") == BASE_URL, "CODEX_BASE_URL_DRIFT", errors)
    require(raw.get("default_permissions") == PROFILE_ID, "CODEX_PERMISSION_PROFILE_DRIFT", errors)
    require((raw.get("windows") or {}).get("sandbox") == "elevated", "CODEX_WINDOWS_SANDBOX_DRIFT", errors)

    profile = ((raw.get("permissions") or {}).get(PROFILE_ID) or {})
    fs = profile.get("filesystem") or {}
    network = profile.get("network") or {}
    result_path = str(workspace / "result.json")
    require(fs.get(":root") == "read", "CODEX_ROOT_READ_MISSING", errors)
    require(fs.get(result_path) == "write", "CODEX_RESULT_WRITE_MISSING", errors)
    require(network.get("enabled") is False, "CODEX_TASK_NETWORK_NOT_DISABLED", errors)

    return {
        "model": raw.get("model"),
        "model_provider": raw.get("model_provider"),
        "openai_base_url": raw.get("openai_base_url"),
        "default_permissions": raw.get("default_permissions"),
        "windows_sandbox": (raw.get("windows") or {}).get("sandbox"),
        "result_write_exact": fs.get(result_path) == "write",
        "root_read": fs.get(":root"),
        "task_network_enabled": network.get("enabled"),
        "raw_sha256": sha256_bytes(text.encode("utf-8")),
    }, errors


def build_admission(
    *,
    bridge_config_path: Path,
    health_path: Path,
    codex_config_path: Path,
    cgw_binary_path: Path,
    codex_binary_path: Path,
    workspace: Path,
    diagnostics_root: Path,
    launcher_log: Path,
    marker_path: Path,
) -> dict[str, Any]:
    errors: list[str] = []

    bridge_bytes = bridge_config_path.read_bytes()
    bridge_raw = json.loads(bridge_bytes.decode("utf-8-sig"))
    bridge, e = project_bridge(bridge_raw, bridge_bytes)
    errors += e

    health_raw = json.loads(health_path.read_text(encoding="utf-8-sig"))
    health, e = project_health(health_raw)
    errors += e

    codex_text = codex_config_path.read_text(encoding="utf-8-sig")
    codex_cfg, e = project_codex_config(codex_text, workspace)
    errors += e

    require(cgw_binary_path.is_file(), "CGW_BINARY_MISSING", errors)
    if cgw_binary_path.is_file():
        require(sha256_file(cgw_binary_path) == CGW_BINARY_SHA256, "CGW_BINARY_HASH_DRIFT", errors)
    require(codex_binary_path.is_file(), "CODEX_BINARY_MISSING", errors)
    if codex_binary_path.is_file():
        require(sha256_file(codex_binary_path) == CODEX_BINARY_SHA256, "CODEX_BINARY_HASH_DRIFT", errors)

    pre = classify_workspace(workspace)
    require(pre["payload"] == ["TASK.md", "input.json"], "WORKSPACE_PAYLOAD_DRIFT", errors)
    require(pre["result"] == [], "WORKSPACE_RESULT_PREEXISTS", errors)
    require(pre["unexpected"] == [], "WORKSPACE_UNEXPECTED_PRESTATE", errors)
    require((workspace / "input.json").is_file() and sha256_file(workspace / "input.json") == INPUT_SHA256, "INPUT_HASH_DRIFT", errors)
    require((workspace / "TASK.md").is_file() and sha256_file(workspace / "TASK.md") == TASK_SHA256, "TASK_HASH_DRIFT", errors)
    require(not marker_path.exists(), "ATTEMPT_MARKER_ALREADY_EXISTS", errors)

    diagnostics_before = sorted(
        p.name for p in diagnostics_root.iterdir() if p.is_dir()
    ) if diagnostics_root.is_dir() else []
    launcher_log_size = launcher_log.stat().st_size if launcher_log.is_file() else 0

    status = "PREDISPATCH_ADMISSION_PASS" if not errors else "PREDISPATCH_ADMISSION_BLOCKED"
    return {
        "schema": "G2E-P5A-CGW-FX001-PREDISPATCH-ADMISSION-v1",
        "status": status,
        "study_id": STUDY_ID,
        "attempt_id": ATTEMPT_ID,
        "route_id": ROUTE_ID,
        "errors": errors,
        "runtime": {
            "cgw_source_commit": CGW_SOURCE_COMMIT,
            "cgw_binary_sha256": sha256_file(cgw_binary_path) if cgw_binary_path.is_file() else None,
            "codex_binary_sha256": sha256_file(codex_binary_path) if codex_binary_path.is_file() else None,
        },
        "bridge_config": bridge,
        "health": health,
        "codex_config": codex_cfg,
        "workspace_pre": pre,
        "diagnostics_baseline": {
            "directory_names": diagnostics_before,
            "launcher_log_size": launcher_log_size,
        },
        "attempt_consumed": False,
        "model_turn_sent": False,
        "automatic_config_mutation": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--bridge-config", required=True)
    p.add_argument("--health-json", required=True)
    p.add_argument("--codex-config", required=True)
    p.add_argument("--cgw-binary", required=True)
    p.add_argument("--codex-binary", required=True)
    p.add_argument("--workspace", required=True)
    p.add_argument("--diagnostics-root", required=True)
    p.add_argument("--launcher-log", required=True)
    p.add_argument("--marker", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()

    report = build_admission(
        bridge_config_path=Path(a.bridge_config),
        health_path=Path(a.health_json),
        codex_config_path=Path(a.codex_config),
        cgw_binary_path=Path(a.cgw_binary),
        codex_binary_path=Path(a.codex_binary),
        workspace=Path(a.workspace),
        diagnostics_root=Path(a.diagnostics_root),
        launcher_log=Path(a.launcher_log),
        marker_path=Path(a.marker),
    )
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": report["status"], "errors": report["errors"]}, sort_keys=True))
    return 0 if report["status"] == "PREDISPATCH_ADMISSION_PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
