from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Any

CGW_RELEASE = "4.0.7"
CONNECTOR = "Codex Native2"
HOST = "127.0.0.1"
PORT = 17841
HEALTH_URL = "http://127.0.0.1:17841/healthz"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_abs(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and os.path.isabs(os.path.expanduser(value))


def is_windows_pipe(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"\\\\\.\\pipe\\[A-Za-z0-9._-]+", value) is not None


def safe_runtime_command(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, list):
        return {"valid": False, "length": None, "first_basename": None}
    valid = len(raw) > 0 and all(isinstance(x, str) and x.strip() for x in raw)
    first = Path(raw[0]).name if valid else None
    return {"valid": valid, "length": len(raw), "first_basename": first}


def safe_tunnel(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"present": False}
    required = ["binaryPath", "tunnelId", "runtimeKeyFile", "profileDir", "profileName", "alias"]
    return {
        "present": True,
        "required_fields_present": all(isinstance(raw.get(k), str) and raw.get(k, "").strip() for k in required),
        "tunnel_id_shape_valid": isinstance(raw.get("tunnelId"), str)
        and re.fullmatch(r"tunnel_[a-f0-9]{32}", raw["tunnelId"]) is not None,
        "binary_path_absolute": is_abs(raw.get("binaryPath")),
        "runtime_key_path_absolute": is_abs(raw.get("runtimeKeyFile")),
        "profile_dir_absolute": is_abs(raw.get("profileDir")),
        "profile_name_shape_valid": isinstance(raw.get("profileName"), str)
        and re.fullmatch(r"[A-Za-z0-9._-]+", raw["profileName"]) is not None,
        "alias_shape_valid": isinstance(raw.get("alias"), str)
        and re.fullmatch(r"[A-Za-z0-9._-]+", raw["alias"]) is not None,
    }


def load_health() -> dict[str, Any]:
    with urllib.request.urlopen(HEALTH_URL, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=str(Path.home() / ".codex-chatgpt-web" / "config.json"))
    a = p.parse_args()

    path = Path(a.config)
    raw_bytes = path.read_bytes()
    raw = json.loads(raw_bytes.decode("utf-8-sig"))
    health = load_health()

    subagent = raw.get("subagentProtocol", "compatibility-v1")
    sol = raw.get("solAvailable", True)
    pro = raw.get("proAvailable", False)
    bigger = raw.get("experimentalBiggerContext", False)
    stall = raw.get("stallTimeoutSec")

    projection = {
        "schema": "G2E-P5A-CGW-TC-CONFIG-SEMANTIC-PROBE-v1",
        "raw_config_sha256": sha256_bytes(raw_bytes),
        "config": {
            "version": raw.get("version"),
            "purpose_present": "purpose" in raw,
            "release_version": raw.get("releaseVersion"),
            "mode": raw.get("mode"),
            "subagent_protocol": subagent,
            "host": raw.get("host"),
            "port": raw.get("port"),
            "context_window": raw.get("contextWindow"),
            "connector": raw.get("appName"),
            "browser_host": raw.get("browserHost"),
            "browser_host_descriptor_absolute": is_abs(raw.get("browserHostDescriptorPath")),
            "chrome_executable_absolute": is_abs(raw.get("chromeExecutablePath")),
            "storage_state_absolute": is_abs(raw.get("storageStatePath")),
            "broker_socket_valid": is_windows_pipe(raw.get("brokerSocketPath")) or is_abs(raw.get("brokerSocketPath")),
            "headed_is_bool": isinstance(raw.get("headed"), bool),
            "sol_available": sol,
            "pro_available": pro,
            "experimental_bigger_context": bigger,
            "stall_timeout_sec": stall,
            "auto_approve_tool_calls": raw.get("autoApproveToolCalls"),
            "control_token_shape_valid": isinstance(raw.get("controlToken"), str)
            and re.fullmatch(r"[A-Za-z0-9_-]{40,}", raw["controlToken"]) is not None,
            "runtime_command": safe_runtime_command(raw.get("runtimeCommand")),
            "tunnel": safe_tunnel(raw.get("tunnel")),
        },
        "health": {
            "status": health.get("status"),
            "service": health.get("service"),
            "version": health.get("version"),
            "mode": health.get("mode"),
            "port": health.get("port"),
            "accepting_turns": health.get("accepting_turns"),
            "active_http_turns": health.get("active_http_turns"),
            "active_browser_turns": health.get("active_browser_turns"),
        },
        "firewall": {
            "model_endpoint_requested": False,
            "browser_submission": False,
            "mcp_invocation": False,
            "attempt_marker_write": False,
            "scientific_dispatch": False,
        },
    }

    checks = {
        "config_version_3": raw.get("version") == 3,
        "production_not_dev_harness": "purpose" not in raw,
        "release_4_0_7": raw.get("releaseVersion") == CGW_RELEASE,
        "mode_full": raw.get("mode") == "full",
        "subagent_protocol_upstream_valid": subagent in ("compatibility-v1", "native"),
        "loopback_host": raw.get("host") == HOST,
        "port_17841": raw.get("port") == PORT,
        "context_window_positive": isinstance(raw.get("contextWindow"), int) and raw["contextWindow"] > 0,
        "connector_native2": raw.get("appName") == CONNECTOR,
        "browser_host_launcher": raw.get("browserHost") == "launcher",
        "browser_host_descriptor_absolute": projection["config"]["browser_host_descriptor_absolute"],
        "chrome_executable_absolute": projection["config"]["chrome_executable_absolute"],
        "storage_state_absolute": projection["config"]["storage_state_absolute"],
        "broker_socket_valid": projection["config"]["broker_socket_valid"],
        "headed_boolean": projection["config"]["headed_is_bool"],
        "sol_available": sol is True,
        "pro_requires_sol": not (pro is True and sol is not True),
        "experimental_bigger_context_boolean": isinstance(bigger, bool),
        "stall_timeout_transport_compatible": stall is None or stall == 300,
        "auto_approve_false": raw.get("autoApproveToolCalls") is False,
        "control_token_shape_valid": projection["config"]["control_token_shape_valid"],
        "runtime_command_valid": projection["config"]["runtime_command"]["valid"],
        "tunnel_present": projection["config"]["tunnel"]["present"],
        "tunnel_required_fields_present": projection["config"]["tunnel"].get("required_fields_present") is True,
        "tunnel_id_shape_valid": projection["config"]["tunnel"].get("tunnel_id_shape_valid") is True,
        "tunnel_paths_absolute": all(
            projection["config"]["tunnel"].get(k) is True
            for k in ("binary_path_absolute", "runtime_key_path_absolute", "profile_dir_absolute")
        ),
        "tunnel_names_valid": projection["config"]["tunnel"].get("profile_name_shape_valid") is True
        and projection["config"]["tunnel"].get("alias_shape_valid") is True,
        "health_ok": health.get("status") == "ok",
        "health_service": health.get("service") == "codex-chatgpt-web",
        "health_release": health.get("version") == CGW_RELEASE,
        "health_full": health.get("mode") == "full",
        "health_port": health.get("port") == PORT,
        "health_accepting": health.get("accepting_turns") is True,
        "health_idle": health.get("active_http_turns") == 0 and health.get("active_browser_turns") == 0,
    }
    projection["checks"] = checks
    projection["status"] = "PASS" if all(checks.values()) else "BLOCKED"
    print(json.dumps(projection, indent=2, sort_keys=True))
    return 0 if projection["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
