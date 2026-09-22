from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import queue
import re
import subprocess
import threading
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_HARNESS_SHA256 = "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b"
EXPECTED_INPUT_SHA256 = "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
EXPECTED_TASK_SHA256 = "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"

STUDY_ID = "p5a-d2s5-observability-qualified-functional-successor"
ATTEMPT_ID = "p5a-d2s5-p5-fx-001-attempt-001"
PROFILE_ID = "g2e_p5a_d2s3"

STARTUP_TIMEOUT_S = 12.0
WINDOWS_SANDBOX_SETUP_TIMEOUT_S = 180.0

OBSERVABILITY_GIT_BLOB = "b6d3c6fcb671dd166893edd46388c8d69dca9105"


def git_blob_sha1(path: Path) -> str:
    project_root = Path(__file__).resolve().parents[2]
    relative = path.resolve().relative_to(project_root).as_posix()
    return subprocess.check_output(
        ["git", "-C", str(project_root), "rev-parse", f"HEAD:{relative}"],
        text=True,
        encoding="utf-8",
        stderr=subprocess.STDOUT,
    ).strip()


def load_observability_module():
    path = Path(__file__).resolve().with_name("p5a_codex_observability.py")
    if not path.is_file():
        raise RuntimeError("OBSERVABILITY_MODULE_MISSING")
    actual_blob = git_blob_sha1(path)
    if actual_blob != OBSERVABILITY_GIT_BLOB:
        raise RuntimeError(
            f"OBSERVABILITY_BLOB_DRIFT:{actual_blob}:{OBSERVABILITY_GIT_BLOB}"
        )
    spec = importlib.util.spec_from_file_location("p5a_codex_observability_locked", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("OBSERVABILITY_MODULE_LOAD_SPEC_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OBSERVABILITY = load_observability_module()

ISOLATION_OVERRIDES = (
    "mcp_servers={}",
    "features.apps=false",
    "features.plugins=false",
    "features.remote_plugin=false",
    "features.workspace_dependencies=false",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def redact_setup_error(value: str) -> str:
    redacted = value
    candidates = [
        ("<userprofile>", os.environ.get("USERPROFILE")),
        ("<userprofile>", str(Path.home()) if str(Path.home()) else None),
        ("<user>", os.environ.get("USERNAME")),
    ]
    seen = set()
    for replacement, candidate in sorted(
        candidates,
        key=lambda item: len(item[1] or ""),
        reverse=True,
    ):
        if not candidate:
            continue
        key = candidate.casefold()
        if key in seen:
            continue
        seen.add(key)
        redacted = re.sub(
            re.escape(candidate),
            replacement,
            redacted,
            flags=re.IGNORECASE,
        )
    return redacted[:4096]


def require_under(path: Path, root: Path, label: str) -> Path:
    path = path.resolve()
    root = root.resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"{label}_OUTSIDE_LOCAL_ROOT:{path}") from exc
    return path


def run_git(project_root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(project_root), *args],
        text=True,
        encoding="utf-8",
        stderr=subprocess.STDOUT,
    ).strip()


def extract_list(result):
    if not isinstance(result, dict):
        return []
    for key in ("data", "servers", "items", "apps"):
        value = result.get(key)
        if isinstance(value, list):
            return value
    return []


def find_profile(result, profile_id: str):
    for item in extract_list(result):
        if isinstance(item, dict) and item.get("id") == profile_id:
            return item
    return None


def verify_profile(config_path: Path, workspace: Path) -> None:
    parsed = tomllib.loads(config_path.read_text(encoding="utf-8"))
    if parsed.get("default_permissions") != PROFILE_ID:
        raise RuntimeError("DEFAULT_PERMISSION_PROFILE_DRIFT")
    if parsed.get("windows", {}).get("sandbox") != "elevated":
        raise RuntimeError("WINDOWS_SANDBOX_MODE_DRIFT")
    profile = parsed.get("permissions", {}).get(PROFILE_ID)
    if not isinstance(profile, dict):
        raise RuntimeError("PROFILE_MISSING")
    filesystem = profile.get("filesystem")
    if not isinstance(filesystem, dict):
        raise RuntimeError("PROFILE_FILESYSTEM_MISSING")
    if filesystem.get(":root") != "read":
        raise RuntimeError("PROFILE_ROOT_READ_MISSING")

    result_path = str(workspace / "result.json")
    result_access = filesystem.get(result_path)
    if result_access != "write":
        raise RuntimeError("PROFILE_RESULT_WRITE_DRIFT")

    network = profile.get("network")
    if not isinstance(network, dict) or network.get("enabled") is not False:
        raise RuntimeError("PROFILE_NETWORK_DRIFT")



def classify_workspace_root(workspace: Path) -> tuple[list[str], list[str], list[str]]:
    workspace_entries = {p.name: p for p in workspace.iterdir()}
    workspace_names = sorted(workspace_entries)
    allowed_names = {"TASK.md", "input.json", "System Volume Information"}
    unexpected_root_names = sorted(set(workspace_names) - allowed_names)
    if unexpected_root_names:
        raise RuntimeError(
            f"WORKSPACE_UNEXPECTED_ROOT_ENTRIES:{unexpected_root_names}"
        )

    support_metadata_names: list[str] = []
    svi = workspace_entries.get("System Volume Information")
    if svi is not None:
        if not svi.is_dir():
            raise RuntimeError("SYSTEM_VOLUME_INFORMATION_NOT_DIRECTORY")
        support_metadata_names.append("System Volume Information")

    payload_names = sorted(
        name for name, path in workspace_entries.items() if path.is_file()
    )
    if payload_names != ["TASK.md", "input.json"]:
        raise RuntimeError(f"WORKSPACE_TASK_PAYLOAD_DRIFT:{payload_names}")

    return payload_names, support_metadata_names, unexpected_root_names


class RpcClient:
    def __init__(self, proc: subprocess.Popen[str], evidence_dir: Path):
        self.proc = proc
        self.q: queue.Queue[tuple[str, str, float]] = queue.Queue()
        self.protocol_path = evidence_dir / "P5A_D2S5_PROTOCOL_OBSERVABILITY.jsonl"
        self.stderr_path = evidence_dir / "P5A_D2S5_STDERR_HASHES.jsonl"
        self.unexpected_server_requests: list[dict] = []
        self.pending_notifications: list[dict] = []
        self._reader(proc.stdout, "stdout")
        self._reader(proc.stderr, "stderr")

    def _reader(self, stream, tag):
        def run():
            try:
                for line in iter(stream.readline, ""):
                    self.q.put((tag, line.rstrip("\r\n"), time.time()))
            finally:
                self.q.put((tag + "_eof", "", time.time()))
        threading.Thread(target=run, daemon=True).start()

    @staticmethod
    def _append_jsonl(path: Path, obj):
        with path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n")

    def send(self, obj):
        self.proc.stdin.write(
            json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n"
        )
        self.proc.stdin.flush()

    def _record_stderr(self, raw: str, ts: float):
        self._append_jsonl(self.stderr_path, {
            "ts_unix": ts,
            "length": len(raw),
            "raw_sha256": sha256_bytes(raw.encode("utf-8")),
        })

    def _record_stdout(self, raw: str, ts: float):
        rec = OBSERVABILITY.project_protocol_message(raw, ts)
        self._append_jsonl(self.protocol_path, rec)
        try:
            msg = json.loads(raw)
        except Exception:
            return None
        return msg if isinstance(msg, dict) else None

    def next_message(self, timeout: float):
        end = time.monotonic() + timeout
        while True:
            remaining = end - time.monotonic()
            if remaining <= 0:
                raise TimeoutError()
            try:
                tag, raw, ts = self.q.get(timeout=remaining)
            except queue.Empty as exc:
                raise TimeoutError() from exc
            if tag == "stderr":
                self._record_stderr(raw, ts)
                continue
            if tag == "stdout":
                msg = self._record_stdout(raw, ts)
                if msg is not None:
                    return msg
                continue
            if tag == "stdout_eof":
                raise EOFError("app-server stdout closed")

    def wait_for_id(self, req_id: int, deadline: float):
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"timeout waiting for id={req_id}")
            msg = self.next_message(remaining)
            if "method" in msg and "id" in msg:
                self.unexpected_server_requests.append({
                    "id": msg.get("id"),
                    "method": msg.get("method"),
                })
                continue
            if "method" in msg and "id" not in msg:
                self.pending_notifications.append(msg)
                continue
            if msg.get("id") == req_id:
                if "error" in msg:
                    raise RuntimeError(f"RPC_ERROR id={req_id}:{msg['error']}")
                return msg.get("result")

    def wait_for_notification(self, method: str, deadline: float):
        for idx, msg in enumerate(self.pending_notifications):
            if msg.get("method") == method:
                return self.pending_notifications.pop(idx)

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"timeout waiting for notification={method}")
            msg = self.next_message(remaining)
            if "method" in msg and "id" in msg:
                self.unexpected_server_requests.append({
                    "id": msg.get("id"),
                    "method": msg.get("method"),
                })
                continue
            if msg.get("method") == method and "id" not in msg:
                return msg
            if "method" in msg and "id" not in msg:
                self.pending_notifications.append(msg)


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
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    local_root = Path(args.local_root).resolve()
    codex_home = require_under(Path(args.codex_home), local_root, "CODEX_HOME")
    evidence_dir = require_under(Path(args.evidence_dir), local_root, "EVIDENCE_DIR")
    codex = Path(args.codex).resolve()
    workspace = Path(args.workspace).resolve()
    config_path = Path(args.config).resolve()

    if evidence_dir.exists():
        raise RuntimeError(f"EVIDENCE_DIR_ALREADY_EXISTS:{evidence_dir}")
    if not project_root.is_dir():
        raise RuntimeError("PROJECT_ROOT_MISSING")
    if not local_root.is_dir():
        raise RuntimeError("LOCAL_ROOT_MISSING")
    if not codex.is_file():
        raise RuntimeError("CODEX_EXECUTABLE_MISSING")
    if not workspace.is_dir():
        raise RuntimeError("WORKSPACE_MISSING")
    if not config_path.is_file():
        raise RuntimeError("CONFIG_MISSING")

    head = run_git(project_root, "rev-parse", "HEAD")
    if head != args.expected_head:
        raise RuntimeError(f"SOURCE_HEAD_DRIFT:{head}")
    if run_git(project_root, "status", "--porcelain"):
        raise RuntimeError("SOURCE_WORKTREE_DIRTY")

    if sha256_file(codex) != EXPECTED_HARNESS_SHA256:
        raise RuntimeError("HARNESS_HASH_DRIFT")

    payload_names, support_metadata_names, unexpected_root_names = (
        classify_workspace_root(workspace)
    )

    if sha256_file(workspace / "input.json") != EXPECTED_INPUT_SHA256:
        raise RuntimeError("INPUT_HASH_DRIFT")
    if sha256_file(workspace / "TASK.md") != EXPECTED_TASK_SHA256:
        raise RuntimeError("TASK_HASH_DRIFT")

    expected_config_hash = args.expected_config_sha256.lower()
    if sha256_file(config_path) != expected_config_hash:
        raise RuntimeError("CONFIG_TOML_HASH_DRIFT")
    verify_profile(config_path, workspace)

    home_names = sorted(p.name for p in codex_home.iterdir())
    if home_names != ["auth.json", "config.toml"]:
        raise RuntimeError(f"CODEX_HOME_PRESTATE_DRIFT:{home_names}")
    if sha256_file(codex_home / "config.toml") != expected_config_hash:
        raise RuntimeError("CODEX_HOME_CONFIG_HASH_DRIFT")
    if not (codex_home / "auth.json").is_file():
        raise RuntimeError("AUTH_JSON_MISSING")

    evidence_dir.mkdir(parents=True, exist_ok=False)
    evidence = {
        "schema": "G2E-P5A-D2S5-PLATFORM-NO-TURN-PREFLIGHT-v1",
        "study_id": STUDY_ID,
        "attempt_id": ATTEMPT_ID,
        "profile_id": PROFILE_ID,
        "started_at": utc_now(),
        "source_head": head,
        "workspace": str(workspace),
        "workspace_drive": workspace.drive,
        "task_payload_names": payload_names,
        "filesystem_support_metadata_names": support_metadata_names,
        "unexpected_root_names": unexpected_root_names,
        "harness_sha256": EXPECTED_HARNESS_SHA256,
        "config_toml_sha256": expected_config_hash,
        "windows_sandbox_readiness_before": None,
        "windows_sandbox_setup_requested": False,
        "windows_sandbox_setup_started": False,
        "windows_sandbox_setup_completed": False,
        "windows_sandbox_setup_success": None,
        "windows_sandbox_setup_mode": None,
        "windows_sandbox_setup_error_code": None,
        "windows_sandbox_setup_error_redacted": None,
        "windows_sandbox_setup_error_sha256": None,
        "windows_sandbox_readiness_after": None,
        "configured_mcp_count": None,
        "installed_app_count": None,
        "callable_or_enabled_app_count": None,
        "auth_ready": None,
        "profile_present": None,
        "profile_allowed": None,
        "thread_id": None,
        "active_permission_profile": None,
        "instruction_sources": None,
        "turn_start_request_sent": False,
        "scientific_attempt_consumed": False,
        "observability_git_blob": OBSERVABILITY_GIT_BLOB,
        "result_exists": False,
    }

    cmd = [str(codex)]
    for override in ISOLATION_OVERRIDES:
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
        client = RpcClient(proc, evidence_dir)
        deadline = time.monotonic() + STARTUP_TIMEOUT_S

        client.send({
            "method": "initialize",
            "id": 1,
            "params": {
                "clientInfo": {
                    "name": "g2e_p5a_d2s5_platform_preflight",
                    "title": "G2E P5A D2-S5 Platform Preflight",
                    "version": "1.0.0",
                },
                "capabilities": {"experimentalApi": True},
            },
        })
        client.wait_for_id(1, deadline)
        client.send({"method": "initialized", "params": {}})

        client.send({
            "method": "windowsSandbox/readiness",
            "id": 20,
            "params": None,
        })
        readiness_before = client.wait_for_id(20, deadline)
        readiness_before_status = (
            readiness_before.get("status")
            if isinstance(readiness_before, dict)
            else None
        )
        evidence["windows_sandbox_readiness_before"] = readiness_before_status

        if readiness_before_status == "updateRequired":
            evidence["windows_sandbox_setup_requested"] = True
            client.send({
                "method": "windowsSandbox/setupStart",
                "id": 21,
                "params": {
                    "mode": "elevated",
                    "cwd": str(workspace),
                },
            })
            setup_response = client.wait_for_id(
                21,
                time.monotonic() + STARTUP_TIMEOUT_S,
            )
            evidence["windows_sandbox_setup_started"] = (
                isinstance(setup_response, dict)
                and setup_response.get("started") is True
            )
            if evidence["windows_sandbox_setup_started"] is not True:
                raise RuntimeError(
                    "PRETURN_BLOCKED_WINDOWS_SANDBOX_SETUP_NOT_STARTED"
                )

            setup_notification = client.wait_for_notification(
                "windowsSandbox/setupCompleted",
                time.monotonic() + WINDOWS_SANDBOX_SETUP_TIMEOUT_S,
            )
            setup_params = setup_notification.get("params") or {}
            evidence["windows_sandbox_setup_completed"] = True
            evidence["windows_sandbox_setup_mode"] = setup_params.get("mode")
            setup_error = setup_params.get("error")
            if isinstance(setup_error, str) and setup_error:
                evidence["windows_sandbox_setup_error_sha256"] = sha256_bytes(
                    setup_error.encode("utf-8")
                )
                evidence["windows_sandbox_setup_error_redacted"] = (
                    redact_setup_error(setup_error)
                )
                prefix = setup_error.split(":", 1)[0].strip()
                if re.fullmatch(r"[a-z0-9_]+", prefix):
                    evidence["windows_sandbox_setup_error_code"] = prefix
            evidence["windows_sandbox_setup_success"] = (
                setup_params.get("mode") == "elevated"
                and setup_params.get("success") is True
            )
            if evidence["windows_sandbox_setup_success"] is not True:
                raise RuntimeError(
                    "PRETURN_BLOCKED_WINDOWS_SANDBOX_SETUP_FAILED"
                )
        elif readiness_before_status != "ready":
            raise RuntimeError(
                f"PRETURN_BLOCKED_WINDOWS_SANDBOX_READINESS:{readiness_before_status}"
            )

        client.send({
            "method": "windowsSandbox/readiness",
            "id": 22,
            "params": None,
        })
        readiness_after = client.wait_for_id(
            22,
            time.monotonic() + STARTUP_TIMEOUT_S,
        )
        readiness_after_status = (
            readiness_after.get("status")
            if isinstance(readiness_after, dict)
            else None
        )
        evidence["windows_sandbox_readiness_after"] = readiness_after_status
        if readiness_after_status != "ready":
            raise RuntimeError(
                f"PRETURN_BLOCKED_WINDOWS_SANDBOX_NOT_READY:{readiness_after_status}"
            )

        client.send({
            "method": "mcpServerStatus/list",
            "id": 2,
            "params": {"cursor": None, "limit": 100, "detail": "toolsAndAuthOnly"},
        })
        mcp = client.wait_for_id(2, deadline)
        evidence["configured_mcp_count"] = len(extract_list(mcp))
        if evidence["configured_mcp_count"] != 0:
            raise RuntimeError("PRETURN_BLOCKED_MCP")

        client.send({
            "method": "app/installed",
            "id": 3,
            "params": {"forceRefresh": False},
        })
        apps_result = client.wait_for_id(3, deadline)
        apps = extract_list(apps_result)
        evidence["installed_app_count"] = len(apps)
        callable_apps = [
            a for a in apps
            if isinstance(a, dict)
            and (a.get("callable") is True or a.get("enabled") is True)
        ]
        evidence["callable_or_enabled_app_count"] = len(callable_apps)
        if apps or callable_apps:
            raise RuntimeError("PRETURN_BLOCKED_APPS")

        client.send({
            "method": "account/read",
            "id": 4,
            "params": {"refreshToken": False},
        })
        account_result = client.wait_for_id(4, deadline)
        account = account_result.get("account") if isinstance(account_result, dict) else None
        requires_auth = (
            account_result.get("requiresOpenaiAuth")
            if isinstance(account_result, dict)
            else None
        )
        evidence["auth_ready"] = isinstance(account, dict) or requires_auth is False
        if evidence["auth_ready"] is not True:
            raise RuntimeError("PRETURN_BLOCKED_AUTH")

        client.send({
            "method": "permissionProfile/list",
            "id": 5,
            "params": {"cursor": None, "limit": 100, "cwd": str(workspace)},
        })
        profiles_result = client.wait_for_id(5, deadline)
        profile = find_profile(profiles_result, PROFILE_ID)
        evidence["profile_present"] = profile is not None
        evidence["profile_allowed"] = (
            profile.get("allowed") is True if isinstance(profile, dict) else False
        )
        if not evidence["profile_present"]:
            raise RuntimeError("PRETURN_BLOCKED_PROFILE_MISSING")
        if not evidence["profile_allowed"]:
            raise RuntimeError("PRETURN_BLOCKED_PROFILE_NOT_ALLOWED")

        client.send({
            "method": "thread/start",
            "id": 6,
            "params": {
                "cwd": str(workspace),
                "approvalPolicy": "never",
                "permissions": PROFILE_ID,
            },
        })
        thread_result = client.wait_for_id(6, deadline)
        thread = (thread_result or {}).get("thread") or {}
        evidence["thread_id"] = thread.get("id")
        evidence["active_permission_profile"] = (
            (thread_result or {}).get("activePermissionProfile")
        )
        evidence["instruction_sources"] = (
            (thread_result or {}).get("instructionSources") or []
        )

        if not evidence["thread_id"]:
            raise RuntimeError("PRETURN_BLOCKED_THREAD_ID_MISSING")
        active = evidence["active_permission_profile"]
        if active is not None:
            if not isinstance(active, dict) or active.get("id") != PROFILE_ID:
                raise RuntimeError("PRETURN_BLOCKED_ACTIVE_PROFILE_MISMATCH")
        if evidence["instruction_sources"]:
            raise RuntimeError("PRETURN_BLOCKED_INSTRUCTION_SOURCES")
        if client.unexpected_server_requests:
            raise RuntimeError("PRETURN_BLOCKED_UNEXPECTED_SERVER_REQUEST")

        evidence["preturn_gate_pass"] = True
        return_code = 0

    except Exception as exc:
        evidence["driver_exception"] = f"{type(exc).__name__}:{exc}"
        evidence["preturn_gate_pass"] = False
        return_code = 2
    finally:
        if client is not None and client.unexpected_server_requests:
            evidence["unexpected_server_requests"] = client.unexpected_server_requests
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

        evidence["finished_at"] = utc_now()
        evidence["result_exists"] = (workspace / "result.json").exists()
        evidence["workspace_names"] = sorted(p.name for p in workspace.iterdir())
        evidence["input_unchanged"] = (
            sha256_file(workspace / "input.json") == EXPECTED_INPUT_SHA256
        )
        evidence["task_unchanged"] = (
            sha256_file(workspace / "TASK.md") == EXPECTED_TASK_SHA256
        )
        evidence["codex_home_post_entries"] = sorted(
            p.name for p in codex_home.iterdir()
        )

        out = evidence_dir / "P5A_D2S5_PLATFORM_NO_TURN_PREFLIGHT.json"
        out.write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

        print(json.dumps({
            "study_id": STUDY_ID,
            "attempt_id": ATTEMPT_ID,
            "preturn_gate_pass": evidence.get("preturn_gate_pass", False),
            "workspace": evidence["workspace"],
            "workspace_drive": evidence["workspace_drive"],
            "windows_sandbox_readiness_before": evidence["windows_sandbox_readiness_before"],
            "windows_sandbox_setup_requested": evidence["windows_sandbox_setup_requested"],
            "windows_sandbox_setup_started": evidence["windows_sandbox_setup_started"],
            "windows_sandbox_setup_completed": evidence["windows_sandbox_setup_completed"],
            "windows_sandbox_setup_success": evidence["windows_sandbox_setup_success"],
            "windows_sandbox_setup_mode": evidence["windows_sandbox_setup_mode"],
            "windows_sandbox_setup_error_code": evidence["windows_sandbox_setup_error_code"],
            "windows_sandbox_setup_error_redacted": evidence["windows_sandbox_setup_error_redacted"],
            "windows_sandbox_setup_error_sha256": evidence["windows_sandbox_setup_error_sha256"],
            "windows_sandbox_readiness_after": evidence["windows_sandbox_readiness_after"],
            "configured_mcp_count": evidence["configured_mcp_count"],
            "installed_app_count": evidence["installed_app_count"],
            "callable_or_enabled_app_count": evidence["callable_or_enabled_app_count"],
            "auth_ready": evidence["auth_ready"],
            "profile_present": evidence["profile_present"],
            "profile_allowed": evidence["profile_allowed"],
            "thread_id_present": bool(evidence["thread_id"]),
            "active_permission_profile": evidence["active_permission_profile"],
            "instruction_sources": evidence["instruction_sources"],
            "turn_start_request_sent": False,
            "scientific_attempt_consumed": False,
            "result_exists": evidence["result_exists"],
            "input_unchanged": evidence["input_unchanged"],
            "task_unchanged": evidence["task_unchanged"],
            "driver_exception": evidence.get("driver_exception"),
            "evidence_file": str(out),
            "evidence_sha256": sha256_file(out),
        }, indent=2, sort_keys=True))

    return return_code


if __name__ == "__main__":
    raise SystemExit(main())