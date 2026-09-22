from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import time
from pathlib import Path

STUDY_ID = "p5a-d2s4-queue-safe-scientific-successor"
ATTEMPT_ID = "p5a-d2s4-p5-fx-001-attempt-001"
PROFILE_ID = "g2e_p5a_d2s3"
PREDECESSOR_STUDY_ID = "p5a-d2s3-release-coherent-instrument-successor"
PREDECESSOR_ATTEMPT_ID = "p5a-d2s3-p5-fx-001-attempt-001"

HARNESS_SHA256 = "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b"
INPUT_SHA256 = "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
TASK_SHA256 = "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"
R2_EVIDENCE_SHA256 = "87f18cf15f06eb1bc3e0a9e28f76e3208b2c082c3cd458221242d65db7b8cc28"
PREFLIGHT_MODULE_GIT_BLOB = "6a7882dba93973aa77d8c4dd1823729d9d5d26f8"

TURN_TIMEOUT_S = 90.0
STARTUP_TIMEOUT_S = 12.0
SETUP_TIMEOUT_S = 90.0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_preflight_module(project_root: Path):
    path = project_root / "scripts" / "g2e" / "p5a_d2s4_queue_safe_client.py"
    actual_blob = run_git(
        project_root,
        "rev-parse",
        "HEAD:scripts/g2e/p5a_d2s4_queue_safe_client.py",
    )
    if actual_blob != PREFLIGHT_MODULE_GIT_BLOB:
        raise RuntimeError(f"PREFLIGHT_MODULE_BLOB_DRIFT:{actual_blob}")
    spec = importlib.util.spec_from_file_location("d2s4_queue_safe_client_frozen", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def require_under(path: Path, root: Path, label: str) -> Path:
    resolved = path.resolve()
    resolved_root = root.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(f"{label}_OUTSIDE_LOCAL_ROOT") from exc
    return resolved


def run_git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"GIT_FAILED:{' '.join(args)}")
    return proc.stdout.strip()


def optional(obj: dict, key: str, default=None):
    return obj[key] if key in obj else default


def validate_r2_evidence(path: Path) -> dict:
    if sha256_file(path) != R2_EVIDENCE_SHA256:
        raise RuntimeError("R2_EVIDENCE_HASH_DRIFT")
    evidence = json.loads(path.read_text(encoding="utf-8"))

    checks = {
        "schema": evidence.get("schema")
        == "G2E-P5A-D2S3-PLATFORM-NO-TURN-PREFLIGHT-v1",
        "study": evidence.get("study_id") == PREDECESSOR_STUDY_ID,
        "attempt": evidence.get("attempt_id") == PREDECESSOR_ATTEMPT_ID,
        "profile": evidence.get("profile_id") == PROFILE_ID,
        "harness": evidence.get("harness_sha256") == HARNESS_SHA256,
        "gate": evidence.get("preturn_gate_pass") is True,
        "readiness": evidence.get("windows_sandbox_readiness_after") == "ready",
        "mcp": evidence.get("configured_mcp_count") == 0,
        "apps": (
            evidence.get("installed_app_count") == 0
            and evidence.get("callable_or_enabled_app_count") == 0
        ),
        "auth": evidence.get("auth_ready") is True,
        "profile_present": evidence.get("profile_present") is True,
        "profile_allowed": evidence.get("profile_allowed") is True,
        "thread": bool(evidence.get("thread_id")),
        "active_profile": (
            evidence.get("active_permission_profile") is None
            or (
                isinstance(evidence.get("active_permission_profile"), dict)
                and evidence["active_permission_profile"].get("id") == PROFILE_ID
            )
        ),
        "instruction_sources": evidence.get("instruction_sources") == [],
        "driver_exception": optional(evidence, "driver_exception") in (None, ""),
        "unexpected_server_requests": optional(
            evidence, "unexpected_server_requests", []
        ) == [],
        "turn_not_sent": evidence.get("turn_start_request_sent") is False,
        "attempt_not_consumed": evidence.get("scientific_attempt_consumed") is False,
        "no_result": evidence.get("result_exists") is False,
        "input_unchanged": evidence.get("input_unchanged") is True,
        "task_unchanged": evidence.get("task_unchanged") is True,
        "payload": sorted(evidence.get("task_payload_names") or [])
        == ["TASK.md", "input.json"],
        "metadata": set(evidence.get("filesystem_support_metadata_names") or [])
        <= {"System Volume Information"},
        "unexpected_root": (evidence.get("unexpected_root_names") or []) == [],
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise RuntimeError("R2_AUTHORIZATION_PREDICATE_FAILED:" + ",".join(failed))
    return evidence


def fsync_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())


def classify_science_root(workspace: Path) -> dict:
    payload: list[str] = []
    support: list[str] = []
    result: list[str] = []
    unexpected: list[str] = []
    for entry in workspace.iterdir():
        name = entry.name
        if name in {"input.json", "TASK.md"} and entry.is_file() and not entry.is_symlink():
            payload.append(name)
        elif (
            name == "System Volume Information"
            and entry.is_dir()
            and not entry.is_symlink()
        ):
            support.append(name)
        elif name == "result.json" and entry.is_file() and not entry.is_symlink():
            result.append(name)
        else:
            unexpected.append(name)
    return {
        "payload": sorted(payload),
        "support": sorted(support),
        "result": sorted(result),
        "unexpected": sorted(unexpected),
    }


def perform_control_plane(client, workspace: Path, profile_id: str, module) -> dict:
    deadline = time.monotonic() + STARTUP_TIMEOUT_S

    client.send(
        {
            "method": "initialize",
            "id": 1,
            "params": {
                "clientInfo": {
                    "name": "g2e_p5a_d2s4_science",
                    "title": "G2E P5A D2-S3 Science",
                    "version": "1.0.0",
                },
                "capabilities": {"experimentalApi": True},
            },
        }
    )
    client.wait_for_id(1, deadline)
    client.send({"method": "initialized", "params": {}})

    client.send({"method": "windowsSandbox/readiness", "id": 20, "params": None})
    before = client.wait_for_id(20, deadline)
    before_status = before.get("status") if isinstance(before, dict) else None

    setup = {
        "requested": False,
        "started": False,
        "completed": False,
        "success": None,
        "mode": None,
        "error_code": None,
        "error_redacted": None,
        "error_sha256": None,
    }

    if before_status == "updateRequired":
        setup["requested"] = True
        client.send(
            {
                "method": "windowsSandbox/setupStart",
                "id": 21,
                "params": {"mode": "elevated", "cwd": str(workspace)},
            }
        )
        response = client.wait_for_id(
            21, time.monotonic() + STARTUP_TIMEOUT_S
        )
        setup["started"] = (
            isinstance(response, dict) and response.get("started") is True
        )
        if not setup["started"]:
            raise RuntimeError("SCIENCE_BLOCKED_SANDBOX_SETUP_NOT_STARTED")

        notification = client.wait_for_notification(
            "windowsSandbox/setupCompleted",
            time.monotonic() + SETUP_TIMEOUT_S,
        )
        params = notification.get("params") or {}
        setup["completed"] = True
        setup["mode"] = params.get("mode")
        error = params.get("error")
        if isinstance(error, str) and error:
            setup["error_sha256"] = sha256_bytes(error.encode("utf-8"))
            setup["error_redacted"] = module.redact_setup_error(error)
            prefix = error.split(":", 1)[0].strip()
            if prefix.replace("_", "").isalnum():
                setup["error_code"] = prefix
        setup["success"] = (
            params.get("mode") == "elevated" and params.get("success") is True
        )
        if setup["success"] is not True:
            raise RuntimeError("SCIENCE_BLOCKED_SANDBOX_SETUP_FAILED")
    elif before_status != "ready":
        raise RuntimeError(f"SCIENCE_BLOCKED_SANDBOX_READINESS:{before_status}")

    client.send({"method": "windowsSandbox/readiness", "id": 22, "params": None})
    after = client.wait_for_id(22, time.monotonic() + STARTUP_TIMEOUT_S)
    after_status = after.get("status") if isinstance(after, dict) else None
    if after_status != "ready":
        raise RuntimeError(f"SCIENCE_BLOCKED_SANDBOX_NOT_READY:{after_status}")

    client.send(
        {
            "method": "mcpServerStatus/list",
            "id": 2,
            "params": {"cursor": None, "limit": 100, "detail": "toolsAndAuthOnly"},
        }
    )
    mcp = client.wait_for_id(2, deadline)
    mcp_count = len(module.extract_list(mcp))
    if mcp_count != 0:
        raise RuntimeError("SCIENCE_BLOCKED_MCP")

    client.send(
        {
            "method": "app/installed",
            "id": 3,
            "params": {"forceRefresh": False},
        }
    )
    apps_result = client.wait_for_id(3, deadline)
    apps = module.extract_list(apps_result)
    callable_apps = [
        app
        for app in apps
        if isinstance(app, dict)
        and (app.get("callable") is True or app.get("enabled") is True)
    ]
    if apps or callable_apps:
        raise RuntimeError("SCIENCE_BLOCKED_APPS")

    client.send(
        {
            "method": "account/read",
            "id": 4,
            "params": {"refreshToken": False},
        }
    )
    account_result = client.wait_for_id(4, deadline)
    account = (
        account_result.get("account")
        if isinstance(account_result, dict)
        else None
    )
    requires_auth = (
        account_result.get("requiresOpenaiAuth")
        if isinstance(account_result, dict)
        else None
    )
    auth_ready = isinstance(account, dict) or requires_auth is False
    if not auth_ready:
        raise RuntimeError("SCIENCE_BLOCKED_AUTH")

    client.send(
        {
            "method": "permissionProfile/list",
            "id": 5,
            "params": {"cursor": None, "limit": 100, "cwd": str(workspace)},
        }
    )
    profiles = client.wait_for_id(5, deadline)
    profile = module.find_profile(profiles, profile_id)
    profile_present = profile is not None
    profile_allowed = (
        profile.get("allowed") is True if isinstance(profile, dict) else False
    )
    if not profile_present:
        raise RuntimeError("SCIENCE_BLOCKED_PROFILE_MISSING")
    if not profile_allowed:
        raise RuntimeError("SCIENCE_BLOCKED_PROFILE_NOT_ALLOWED")

    client.send(
        {
            "method": "thread/start",
            "id": 6,
            "params": {
                "cwd": str(workspace),
                "approvalPolicy": "never",
                "permissions": profile_id,
            },
        }
    )
    thread_result = client.wait_for_id(6, deadline)
    thread = (thread_result or {}).get("thread") or {}
    thread_id = thread.get("id")
    active_profile = (thread_result or {}).get("activePermissionProfile")
    instruction_sources = (thread_result or {}).get("instructionSources") or []

    if not thread_id:
        raise RuntimeError("SCIENCE_BLOCKED_THREAD_ID_MISSING")
    if active_profile is not None:
        if not isinstance(active_profile, dict) or active_profile.get("id") != profile_id:
            raise RuntimeError("SCIENCE_BLOCKED_ACTIVE_PROFILE_MISMATCH")
    if instruction_sources:
        raise RuntimeError("SCIENCE_BLOCKED_INSTRUCTION_SOURCES")
    if client.unexpected_server_requests:
        raise RuntimeError("SCIENCE_BLOCKED_UNEXPECTED_SERVER_REQUEST")

    return {
        "windows_sandbox_readiness_before": before_status,
        "windows_sandbox_setup": setup,
        "windows_sandbox_readiness_after": after_status,
        "configured_mcp_count": mcp_count,
        "installed_app_count": len(apps),
        "callable_or_enabled_app_count": len(callable_apps),
        "auth_ready": auth_ready,
        "profile_present": profile_present,
        "profile_allowed": profile_allowed,
        "thread_id": thread_id,
        "active_permission_profile": active_profile,
        "instruction_sources": instruction_sources,
    }


def wait_for_turn(client, turn_id: str, timeout_seconds: float) -> dict:
    deadline = time.monotonic() + timeout_seconds
    notifications: list[dict] = list(client.pending_notifications)
    client.pending_notifications.clear()

    for msg in notifications:
        if msg.get("method") == "turn/completed":
            params = msg.get("params") or {}
            turn = params.get("turn") or {}
            if not turn_id or turn.get("id") in (None, turn_id):
                return {
                    "terminal": True,
                    "timeout": False,
                    "unexpected_server_request": False,
                    "completion": msg,
                    "notifications": notifications,
                }

    while True:
        if client.unexpected_server_requests:
            return {
                "terminal": False,
                "timeout": False,
                "unexpected_server_request": True,
                "completion": None,
                "notifications": notifications,
            }

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return {
                "terminal": False,
                "timeout": True,
                "unexpected_server_request": False,
                "completion": None,
                "notifications": notifications,
            }

        try:
            msg = client.next_message(min(remaining, 1.0))
        except TimeoutError:
            continue

        if "method" in msg and "id" in msg:
            client.unexpected_server_requests.append(
                {"id": msg.get("id"), "method": msg.get("method")}
            )
            continue
        if "method" in msg and "id" not in msg:
            notifications.append(msg)
            if msg.get("method") == "turn/completed":
                params = msg.get("params") or {}
                turn = params.get("turn") or {}
                if not turn_id or turn.get("id") in (None, turn_id):
                    return {
                        "terminal": True,
                        "timeout": False,
                        "unexpected_server_request": False,
                        "completion": msg,
                        "notifications": notifications,
                    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--local-root", required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--expected-config-sha256", required=True)
    parser.add_argument("--codex-home", required=True)
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--codex", required=True)
    parser.add_argument("--execution-config-hash", required=True)
    parser.add_argument("--r2-evidence", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    local_root = Path(args.local_root).resolve()
    workspace = Path(args.workspace).resolve()
    config_path = Path(args.config).resolve()
    codex_home = require_under(
        Path(args.codex_home), local_root, "CODEX_HOME"
    )
    evidence_dir = require_under(
        Path(args.evidence_dir), local_root, "EVIDENCE_DIR"
    )
    codex = Path(args.codex).resolve()
    r2_evidence_path = Path(args.r2_evidence).resolve()

    module = load_preflight_module(project_root)
    r2_evidence = validate_r2_evidence(r2_evidence_path)

    if evidence_dir.exists():
        raise RuntimeError("SCIENCE_EVIDENCE_DIR_ALREADY_EXISTS")
    if not project_root.is_dir() or not local_root.is_dir():
        raise RuntimeError("SCIENCE_ROOT_MISSING")
    if not workspace.is_dir() or not config_path.is_file():
        raise RuntimeError("SCIENCE_WORKSPACE_OR_CONFIG_MISSING")
    if not codex.is_file() or sha256_file(codex) != HARNESS_SHA256:
        raise RuntimeError("SCIENCE_HARNESS_DRIFT")

    head = run_git(project_root, "rev-parse", "HEAD")
    if head != args.expected_head:
        raise RuntimeError("SCIENCE_SOURCE_HEAD_DRIFT")
    if run_git(project_root, "status", "--porcelain"):
        raise RuntimeError("SCIENCE_SOURCE_WORKTREE_DIRTY")

    if sha256_file(workspace / "input.json") != INPUT_SHA256:
        raise RuntimeError("SCIENCE_INPUT_HASH_DRIFT")
    if sha256_file(workspace / "TASK.md") != TASK_SHA256:
        raise RuntimeError("SCIENCE_TASK_HASH_DRIFT")
    task_text = (workspace / "TASK.md").read_text(encoding="utf-8")
    if sha256_bytes(task_text.encode("utf-8")) != TASK_SHA256:
        raise RuntimeError("SCIENCE_TASK_TEXT_HASH_DRIFT")

    expected_config_hash = args.expected_config_sha256.lower()
    if sha256_file(config_path) != expected_config_hash:
        raise RuntimeError("SCIENCE_CONFIG_HASH_DRIFT")
    module.verify_profile(config_path, workspace)

    root_before = classify_science_root(workspace)
    if root_before["payload"] != ["TASK.md", "input.json"]:
        raise RuntimeError("SCIENCE_PRESTATE_PAYLOAD_DRIFT")
    if root_before["result"] or root_before["unexpected"]:
        raise RuntimeError("SCIENCE_PRESTATE_ROOT_DRIFT")
    if set(root_before["support"]) - {"System Volume Information"}:
        raise RuntimeError("SCIENCE_PRESTATE_SUPPORT_METADATA_DRIFT")

    home_names = sorted(p.name for p in codex_home.iterdir())
    if home_names != ["auth.json", "config.toml"]:
        raise RuntimeError("SCIENCE_CODEX_HOME_PRESTATE_DRIFT")
    if sha256_file(codex_home / "config.toml") != expected_config_hash:
        raise RuntimeError("SCIENCE_CODEX_HOME_CONFIG_DRIFT")

    evidence_dir.mkdir(parents=True, exist_ok=False)
    marker_path = evidence_dir / "P5A_D2S4_TURN_START_SENT.marker"

    evidence = {
        "schema": "G2E-P5A-D2S4-SCIENTIFIC-RUNNER-v1",
        "study_id": STUDY_ID,
        "attempt_id": ATTEMPT_ID,
        "profile_id": PROFILE_ID,
        "source_head": head,
        "harness_sha256": HARNESS_SHA256,
        "input_sha256": INPUT_SHA256,
        "task_sha256": TASK_SHA256,
        "execution_config_hash": args.execution_config_hash,
        "r2_evidence_sha256": R2_EVIDENCE_SHA256,
        "r2_authorization_pass": True,
        "r2_thread_id": r2_evidence.get("thread_id"),
        "started_at_unix": time.time(),
        "turn_start_marker_created": False,
        "turn_start_request_sent": False,
        "scientific_attempt_consumed": False,
        "turn_start_accepted": False,
        "thread_id": None,
        "turn_id": None,
        "turn_timeout": False,
        "turn_terminal": False,
        "terminal_status": None,
        "unexpected_server_request": False,
        "permission_request_seen": False,
        "protocol_command_execution_seen": False,
        "protocol_mcp_tool_seen": False,
        "protocol_web_search_seen": False,
        "result_exists": False,
        "result_sha256": None,
        "result_size": None,
        "input_unchanged": False,
        "task_unchanged": False,
        "workspace_pre": root_before,
        "workspace_post": None,
        "driver_exception": None,
    }

    cmd = [str(codex)]
    for override in module.ISOLATION_OVERRIDES:
        cmd.extend(["--config", override])
    cmd.append("app-server")

    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)

    proc = None
    client = None
    return_code = 2
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(workspace),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        client = module.RpcClient(proc, evidence_dir)

        control = perform_control_plane(
            client, workspace, PROFILE_ID, module
        )
        evidence.update(control)
        evidence["thread_id"] = control["thread_id"]

        marker_text = "\n".join(
            [
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                ATTEMPT_ID,
                args.execution_config_hash,
                R2_EVIDENCE_SHA256,
                "",
            ]
        )
        fsync_text(marker_path, marker_text)
        evidence["turn_start_marker_created"] = True
        evidence["scientific_attempt_consumed"] = True

        request = {
            "method": "turn/start",
            "id": 7,
            "params": {
                "threadId": evidence["thread_id"],
                "input": [
                    {
                        "type": "text",
                        "text": task_text,
                        "textElements": [],
                    }
                ],
                "cwd": str(workspace),
                "approvalPolicy": "never",
            },
        }

        evidence["turn_start_request_sent"] = True
        client.send(request)
        turn_result = client.wait_for_id(
            7, time.monotonic() + STARTUP_TIMEOUT_S
        )
        evidence["turn_start_accepted"] = True
        turn = (turn_result or {}).get("turn") or {}
        evidence["turn_id"] = turn.get("id")

        terminal = wait_for_turn(
            client,
            evidence["turn_id"] or "",
            TURN_TIMEOUT_S,
        )
        evidence["turn_timeout"] = terminal["timeout"]
        evidence["turn_terminal"] = terminal["terminal"]
        evidence["unexpected_server_request"] = terminal[
            "unexpected_server_request"
        ]
        completion = terminal.get("completion") or {}
        completed_turn = (completion.get("params") or {}).get("turn") or {}
        evidence["terminal_status"] = completed_turn.get("status")

        notifications = terminal.get("notifications") or []
        methods = [str(msg.get("method") or "") for msg in notifications]
        serialized = "\n".join(
            json.dumps(msg, sort_keys=True, ensure_ascii=False)
            for msg in notifications
        ).lower()
        evidence["protocol_command_execution_seen"] = any(
            "command" in method.lower() and "execution" in method.lower()
            for method in methods
        )
        evidence["protocol_mcp_tool_seen"] = (
            "mcp" in serialized and "tool" in serialized
        )
        evidence["protocol_web_search_seen"] = "web_search" in serialized or "websearch" in serialized

        if client.unexpected_server_requests:
            evidence["unexpected_server_requests"] = (
                client.unexpected_server_requests
            )
            evidence["permission_request_seen"] = any(
                "approval" in str(req.get("method") or "").lower()
                or "requestapproval" in str(req.get("method") or "").lower()
                for req in client.unexpected_server_requests
            )

        return_code = 0
    except Exception as exc:
        evidence["driver_exception"] = f"{type(exc).__name__}:{exc}"
        return_code = 2
    finally:
        if client is not None and client.unexpected_server_requests:
            evidence["unexpected_server_requests"] = (
                client.unexpected_server_requests
            )
            evidence["unexpected_server_request"] = True
            evidence["permission_request_seen"] = any(
                "approval" in str(req.get("method") or "").lower()
                or "requestapproval" in str(req.get("method") or "").lower()
                for req in client.unexpected_server_requests
            )

        if proc is not None:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=5)
            except Exception:
                pass
            evidence["app_server_exit_code"] = proc.poll()

        result_path = workspace / "result.json"
        evidence["result_exists"] = result_path.is_file()
        if evidence["result_exists"]:
            evidence["result_sha256"] = sha256_file(result_path)
            evidence["result_size"] = result_path.stat().st_size

        evidence["input_unchanged"] = (
            sha256_file(workspace / "input.json") == INPUT_SHA256
        )
        evidence["task_unchanged"] = (
            sha256_file(workspace / "TASK.md") == TASK_SHA256
        )
        evidence["workspace_post"] = classify_science_root(workspace)
        evidence["finished_at_unix"] = time.time()
        evidence["protocol_file"] = str(client.protocol_path) if client else None
        evidence["stderr_hash_file"] = str(client.stderr_path) if client else None
        evidence["marker_file"] = (
            str(marker_path) if marker_path.exists() else None
        )

        out = evidence_dir / "P5A_D2S4_SCIENTIFIC_RUNNER_EVIDENCE.json"
        out.write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

        print(
            json.dumps(
                {
                    "attempt_id": ATTEMPT_ID,
                    "attempt_consumed": evidence[
                        "scientific_attempt_consumed"
                    ],
                    "turn_start_sent": evidence[
                        "turn_start_request_sent"
                    ],
                    "turn_start_accepted": evidence[
                        "turn_start_accepted"
                    ],
                    "turn_id": evidence["turn_id"],
                    "turn_terminal": evidence["turn_terminal"],
                    "turn_timeout": evidence["turn_timeout"],
                    "result_exists": evidence["result_exists"],
                    "evidence_file": str(out),
                    "evidence_sha256": sha256_file(out),
                },
                sort_keys=True,
            )
        )

    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
