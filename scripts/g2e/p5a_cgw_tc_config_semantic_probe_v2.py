from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

EXPECTED_HEALTH_JOIN_SHA256 = "6f4347acdcb722d52b2ea4bb166a53c28a809fdf13bb9f358e794bad12c16053"
CGW_RELEASE = "4.0.7"
CONNECTOR = "Codex Native2"
HOST = "127.0.0.1"
PORT = 17841


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_abs(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and os.path.isabs(os.path.expanduser(value))


def is_windows_pipe(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"\\\\\.\\pipe\\[A-Za-z0-9._-]+", value) is not None


def inside(path: str, root: str) -> bool:
    try:
        p = os.path.normcase(os.path.abspath(path))
        r = os.path.normcase(os.path.abspath(root))
        return os.path.commonpath([p, r]) == r
    except Exception:
        return False


def runtime_command_projection(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, list):
        return {
            "valid_list": False,
            "length": None,
            "first_basename": None,
            "executable_absolute": False,
            "executable_exists": False,
            "ephemeral_absolute_component_present": None,
        }
    strings_valid = len(raw) > 0 and all(isinstance(x, str) and x.strip() for x in raw)
    executable = raw[0] if strings_valid else None
    ephemeral_roots = {
        os.path.abspath(tempfile.gettempdir()),
        os.path.abspath("/tmp"),
        os.path.abspath("/private/tmp"),
        os.path.abspath("/var/tmp"),
        os.path.abspath("/private/var/tmp"),
    }
    ephemeral = False
    if strings_valid:
        for part in raw:
            if os.path.isabs(part) and any(inside(part, root) for root in ephemeral_roots):
                ephemeral = True
                break
    return {
        "valid_list": strings_valid,
        "length": len(raw),
        "first_basename": Path(executable).name if executable else None,
        "executable_absolute": bool(executable and os.path.isabs(executable)),
        "executable_exists": bool(executable and os.path.isfile(executable)),
        "ephemeral_absolute_component_present": ephemeral if strings_valid else None,
    }


def tunnel_projection(raw: Any) -> dict[str, Any]:
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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=str(Path.home() / ".codex-chatgpt-web" / "config.json"))
    a = p.parse_args()

    path = Path(a.config)
    raw_bytes = path.read_bytes()
    raw_hash = sha256_bytes(raw_bytes)
    raw = json.loads(raw_bytes.decode("utf-8-sig"))

    subagent = raw.get("subagentProtocol", "compatibility-v1")
    sol = raw.get("solAvailable", True)
    pro = raw.get("proAvailable", False)
    bigger = raw.get("experimentalBiggerContext", False)
    stall = raw.get("stallTimeoutSec")
    runtime = runtime_command_projection(raw.get("runtimeCommand"))
    tunnel = tunnel_projection(raw.get("tunnel"))

    config = {
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
        "runtime_command": runtime,
        "tunnel": tunnel,
    }

    checks = {
        "health_snapshot_provenance_join": raw_hash == EXPECTED_HEALTH_JOIN_SHA256,
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
        "browser_host_descriptor_absolute": config["browser_host_descriptor_absolute"],
        "chrome_executable_absolute": config["chrome_executable_absolute"],
        "storage_state_absolute": config["storage_state_absolute"],
        "broker_socket_valid": config["broker_socket_valid"],
        "headed_boolean": config["headed_is_bool"],
        "sol_available": sol is True,
        "pro_requires_sol": not (pro is True and sol is not True),
        "experimental_bigger_context_boolean": isinstance(bigger, bool),
        "stall_timeout_transport_compatible": stall is None or stall == 300,
        "auto_approve_false": raw.get("autoApproveToolCalls") is False,
        "control_token_shape_valid": config["control_token_shape_valid"],
        "runtime_command_valid_list": runtime["valid_list"],
        "runtime_executable_absolute": runtime["executable_absolute"],
        "runtime_executable_exists": runtime["executable_exists"],
        "runtime_no_ephemeral_absolute_component": runtime["ephemeral_absolute_component_present"] is False,
        "tunnel_present": tunnel["present"],
        "tunnel_required_fields_present": tunnel.get("required_fields_present") is True,
        "tunnel_id_shape_valid": tunnel.get("tunnel_id_shape_valid") is True,
        "tunnel_paths_absolute": all(
            tunnel.get(k) is True
            for k in ("binary_path_absolute", "runtime_key_path_absolute", "profile_dir_absolute")
        ),
        "tunnel_names_valid": tunnel.get("profile_name_shape_valid") is True
        and tunnel.get("alias_shape_valid") is True,
    }

    result = {
        "schema": "G2E-P5A-CGW-TC-OFFLINE-CONFIG-SEMANTIC-PROBE-v2",
        "raw_config_sha256": raw_hash,
        "prior_healthy_snapshot_raw_config_sha256": EXPECTED_HEALTH_JOIN_SHA256,
        "config": config,
        "checks": checks,
        "prior_health_snapshot": {
            "status": "ok",
            "service": "codex-chatgpt-web",
            "version": "4.0.7",
            "mode": "full",
            "port": 17841,
            "accepting_turns": True,
            "active_http_turns": 0,
            "active_browser_turns": 0,
            "evidence_origin": "TC predispatch admission captured before marker under the same raw config hash",
        },
        "firewall": {
            "network_request": False,
            "model_endpoint_requested": False,
            "browser_submission": False,
            "mcp_invocation": False,
            "attempt_marker_write": False,
            "scientific_dispatch": False,
        },
    }
    result["status"] = "PASS" if all(checks.values()) else "BLOCKED"
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
