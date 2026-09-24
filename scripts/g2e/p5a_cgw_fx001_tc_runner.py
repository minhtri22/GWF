from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

STUDY_ID = "p5a-cgw-v4-p5-fx-001-transport-corrected-qualification"
ATTEMPT_ID = "p5a-cgw-v4-p5-fx-001-tc-attempt-001"
ROUTE_ID = "p5a-cgw"
PROFILE_ID = "g2e_p5a_cgw_fx001"

CODEX_BINARY_SHA256 = "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b"
INPUT_SHA256 = "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
TASK_SHA256 = "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"
EXECUTION_CONFIG_CANONICAL_SHA256 = "6b88011e0bc6ba0164a0e6f4230bb1fb8be6037d7513f348c15d39ea726816f7"
STARTUP_TIMEOUT_S = 15.0
SANDBOX_SETUP_TIMEOUT_S = 180.0

ISOLATION_OVERRIDES = (
    "mcp_servers={}",
    "features.apps=false",
    "features.plugins=false",
    "features.remote_plugin=false",
    "features.workspace_dependencies=false",
)

_REGISTER_RE = re.compile(r"\[chatgpt-web\] broker trace=([A-Za-z0-9_-]{6,128}) registered tokenHash=([a-f0-9]{12})")
_COMPLETE_RE = re.compile(r"\[chatgpt-web\] broker trace=([A-Za-z0-9_-]{6,128}) completed call=([^ ]+) pending=\d+")
_MCP_RE = re.compile(r"\[chatgpt-web-mcp\] ([A-Za-z0-9_.$:-]+) scope=")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n")


def safe_item_projection(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    item_id = item.get("id") or item.get("callId") or item.get("toolCallId")
    item_type = item.get("type")
    name = item.get("name") or item.get("toolName")
    status = item.get("status")
    out: dict[str, Any] = {}
    if isinstance(item_id, str):
        out["id"] = item_id
    if isinstance(item_type, str):
        out["type"] = item_type
    if isinstance(name, str):
        out["name"] = name
    if isinstance(status, str):
        out["status"] = status
    return out or None


def project_protocol(raw: str, ts: float) -> tuple[dict[str, Any], dict[str, Any] | None]:
    rec: dict[str, Any] = {
        "ts_unix": ts,
        "length": len(raw),
        "rawSha256": sha256_bytes(raw.encode("utf-8")),
    }
    try:
        msg = json.loads(raw)
    except Exception:
        rec["json"] = False
        return rec, None
    if not isinstance(msg, dict):
        rec["json"] = False
        return rec, None
    rec["json"] = True
    if "id" in msg and not isinstance(msg.get("id"), (dict, list)):
        rec["rpcId"] = msg.get("id")
    method = msg.get("method")
    if isinstance(method, str):
        rec["method"] = method
        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        if method in {"item/started", "item/completed"}:
            item = safe_item_projection(params.get("item"))
            if item:
                rec["item"] = item
        if method == "turn/completed":
            turn = params.get("turn") if isinstance(params.get("turn"), dict) else {}
            rec["threadId"] = params.get("threadId")
            rec["turnId"] = turn.get("id")
            rec["status"] = turn.get("status")
            error = turn.get("error")
            if error is not None:
                encoded = json.dumps(error, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                rec["terminalErrorSha256"] = sha256_bytes(encoded)
        if method == "error":
            rec["threadId"] = params.get("threadId")
            rec["turnId"] = params.get("turnId")
            rec["willRetry"] = params.get("willRetry")
            if params.get("error") is not None:
                encoded = json.dumps(params.get("error"), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                rec["terminalErrorSha256"] = sha256_bytes(encoded)
    return rec, msg


class RpcClient:
    def __init__(self, proc: subprocess.Popen[str], evidence_dir: Path):
        self.proc = proc
        self.q: queue.Queue[tuple[str, str, float]] = queue.Queue()
        self.protocol_path = evidence_dir / "codex_protocol.jsonl"
        self.stderr_path = evidence_dir / "codex_stderr_hashes.jsonl"
        self.pending_notifications: list[dict[str, Any]] = []
        self.unexpected_server_requests: list[dict[str, Any]] = []
        self.protocol_records: list[dict[str, Any]] = []
        self._reader(proc.stdout, "stdout")
        self._reader(proc.stderr, "stderr")

    def _reader(self, stream, tag: str) -> None:
        def run() -> None:
            try:
                for line in iter(stream.readline, ""):
                    self.q.put((tag, line.rstrip("\r\n"), time.time()))
            finally:
                self.q.put((tag + "_eof", "", time.time()))
        threading.Thread(target=run, daemon=True).start()

    def send(self, obj: dict[str, Any]) -> None:
        self.proc.stdin.write(json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def next_message(self, timeout: float) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError()
            try:
                tag, raw, ts = self.q.get(timeout=remaining)
            except queue.Empty as exc:
                raise TimeoutError() from exc
            if tag == "stderr":
                append_jsonl(self.stderr_path, {
                    "ts_unix": ts,
                    "length": len(raw),
                    "rawSha256": sha256_bytes(raw.encode("utf-8")),
                })
                continue
            if tag == "stdout":
                rec, msg = project_protocol(raw, ts)
                append_jsonl(self.protocol_path, rec)
                self.protocol_records.append(rec)
                if msg is not None:
                    return msg
                continue
            if tag == "stdout_eof":
                raise EOFError("app-server stdout closed")

    def wait_for_id(self, req_id: int, deadline: float) -> Any:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"timeout waiting for id={req_id}")
            msg = self.next_message(remaining)
            if "method" in msg and "id" in msg:
                self.unexpected_server_requests.append({"id": msg.get("id"), "method": msg.get("method")})
                continue
            if "method" in msg and "id" not in msg:
                self.pending_notifications.append(msg)
                continue
            if msg.get("id") == req_id:
                if "error" in msg:
                    raise RuntimeError(f"RPC_ERROR:{req_id}:{msg['error']}")
                return msg.get("result")

    def wait_for_notification(self, method: str, deadline: float) -> dict[str, Any]:
        for i, msg in enumerate(self.pending_notifications):
            if msg.get("method") == method:
                return self.pending_notifications.pop(i)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"timeout waiting for {method}")
            msg = self.next_message(remaining)
            if "method" in msg and "id" in msg:
                self.unexpected_server_requests.append({"id": msg.get("id"), "method": msg.get("method")})
                continue
            if msg.get("method") == method and "id" not in msg:
                return msg
            if "method" in msg and "id" not in msg:
                self.pending_notifications.append(msg)


def extract_list(result: Any) -> list[Any]:
    if not isinstance(result, dict):
        return []
    for key in ("data", "servers", "items", "apps"):
        if isinstance(result.get(key), list):
            return result[key]
    return []


def find_profile(result: Any) -> dict[str, Any] | None:
    for item in extract_list(result):
        if isinstance(item, dict) and item.get("id") == PROFILE_ID:
            return item
    return None


def perform_control_plane(client: RpcClient, workspace: Path) -> dict[str, Any]:
    deadline = time.monotonic() + STARTUP_TIMEOUT_S
    client.send({"method": "initialize", "id": 1, "params": {
        "clientInfo": {"name": "g2e_p5a_cgw_fx001", "title": "G2E P5A-CGW FX001", "version": "1.0.0"},
        "capabilities": {"experimentalApi": True},
    }})
    client.wait_for_id(1, deadline)
    client.send({"method": "initialized", "params": {}})

    client.send({"method": "windowsSandbox/readiness", "id": 2, "params": None})
    before = client.wait_for_id(2, deadline)
    before_status = before.get("status") if isinstance(before, dict) else None
    setup = {"requested": False, "success": None}
    if before_status == "updateRequired":
        setup["requested"] = True
        client.send({"method": "windowsSandbox/setupStart", "id": 3, "params": {"mode": "elevated", "cwd": str(workspace)}})
        started = client.wait_for_id(3, time.monotonic() + STARTUP_TIMEOUT_S)
        if not isinstance(started, dict) or started.get("started") is not True:
            raise RuntimeError("PREDISPATCH_SANDBOX_SETUP_NOT_STARTED")
        completed = client.wait_for_notification("windowsSandbox/setupCompleted", time.monotonic() + SANDBOX_SETUP_TIMEOUT_S)
        params = completed.get("params") or {}
        setup["success"] = params.get("mode") == "elevated" and params.get("success") is True
        if setup["success"] is not True:
            raise RuntimeError("PREDISPATCH_SANDBOX_SETUP_FAILED")
    elif before_status != "ready":
        raise RuntimeError(f"PREDISPATCH_SANDBOX_NOT_READY:{before_status}")

    client.send({"method": "windowsSandbox/readiness", "id": 4, "params": None})
    after = client.wait_for_id(4, time.monotonic() + STARTUP_TIMEOUT_S)
    after_status = after.get("status") if isinstance(after, dict) else None
    if after_status != "ready":
        raise RuntimeError(f"PREDISPATCH_SANDBOX_NOT_READY_AFTER:{after_status}")

    client.send({"method": "mcpServerStatus/list", "id": 5, "params": {"cursor": None, "limit": 100, "detail": "toolsAndAuthOnly"}})
    mcp_count = len(extract_list(client.wait_for_id(5, deadline)))
    if mcp_count != 0:
        raise RuntimeError("PREDISPATCH_ARBITRARY_MCP_PRESENT")

    client.send({"method": "app/installed", "id": 6, "params": {"forceRefresh": False}})
    apps = extract_list(client.wait_for_id(6, deadline))
    if apps:
        raise RuntimeError("PREDISPATCH_APPS_PRESENT")

    client.send({"method": "account/read", "id": 7, "params": {"refreshToken": False}})
    account = client.wait_for_id(7, deadline)
    auth_ready = isinstance(account, dict) and (isinstance(account.get("account"), dict) or account.get("requiresOpenaiAuth") is False)
    if not auth_ready:
        raise RuntimeError("PREDISPATCH_CODEX_AUTH_NOT_READY")

    client.send({"method": "permissionProfile/list", "id": 8, "params": {"cursor": None, "limit": 100, "cwd": str(workspace)}})
    profile = find_profile(client.wait_for_id(8, deadline))
    if not profile or profile.get("allowed") is not True:
        raise RuntimeError("PREDISPATCH_PERMISSION_PROFILE_NOT_ALLOWED")

    client.send({"method": "thread/start", "id": 9, "params": {
        "cwd": str(workspace),
        "approvalPolicy": "never",
        "permissions": PROFILE_ID,
    }})
    result = client.wait_for_id(9, deadline)
    thread = (result or {}).get("thread") or {}
    thread_id = thread.get("id")
    if not thread_id:
        raise RuntimeError("PREDISPATCH_THREAD_ID_MISSING")
    active = (result or {}).get("activePermissionProfile")
    if active is not None and (not isinstance(active, dict) or active.get("id") != PROFILE_ID):
        raise RuntimeError("PREDISPATCH_ACTIVE_PROFILE_MISMATCH")
    instruction_sources = (result or {}).get("instructionSources") or []
    if instruction_sources:
        raise RuntimeError("PREDISPATCH_INSTRUCTION_SOURCES_PRESENT")
    if client.unexpected_server_requests:
        raise RuntimeError("PREDISPATCH_UNEXPECTED_SERVER_REQUEST")
    return {
        "sandbox_before": before_status,
        "sandbox_setup": setup,
        "sandbox_after": after_status,
        "configured_mcp_count": mcp_count,
        "installed_app_count": len(apps),
        "auth_ready": auth_ready,
        "thread_id": thread_id,
        "instruction_sources": instruction_sources,
    }


def wait_for_turn(client: RpcClient, turn_id: str) -> dict[str, Any]:
    """Wait for exact app-server terminal notification with no scientific absolute turn deadline.

    Qualified CGW/Codex transport owns liveness. A local operator/process abort is handled outside
    this function and can only make the run infrastructure-invalid; it cannot assign scientific
    PASS or substantive FAIL.
    """
    notifications = list(client.pending_notifications)
    client.pending_notifications.clear()
    while True:
        for msg in list(notifications):
            if msg.get("method") == "turn/completed":
                turn = ((msg.get("params") or {}).get("turn") or {})
                if turn.get("id") == turn_id:
                    return {
                        "terminal": True,
                        "timeout": False,
                        "completion": msg,
                        "notifications": notifications,
                    }
        try:
            msg = client.next_message(1.0)
        except TimeoutError:
            continue
        if "method" in msg and "id" in msg:
            client.unexpected_server_requests.append({"id": msg.get("id"), "method": msg.get("method")})
            continue
        if "method" in msg and "id" not in msg:
            notifications.append(msg)

def read_launcher_delta(path: Path, offset: int) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    if path.stat().st_size < offset:
        raise RuntimeError("LAUNCHER_LOG_ROTATED_DURING_ATTEMPT")
    with path.open("rb") as f:
        f.seek(offset)
        raw = f.read()
    records: list[dict[str, Any]] = []
    for line in raw.decode("utf-8", errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if isinstance(obj, dict):
            records.append(obj)
    return records


def runtime_lines(records: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for record in records:
        if record.get("event") not in {"runtime.daemon_stdout", "runtime.daemon_stderr"}:
            continue
        detail = record.get("detail")
        if isinstance(detail, dict) and isinstance(detail.get("line"), str):
            out.append(detail["line"])
    return out


def collect_diagnostics(root: Path, baseline: set[str]) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.is_dir():
        return [], []
    new_dirs = sorted(p for p in root.iterdir() if p.is_dir() and p.name not in baseline)
    projected: list[dict[str, Any]] = []
    for directory in new_dirs:
        for path in sorted(directory.glob("*.json")):
            try:
                raw = json.loads(path.read_text(encoding="utf-8-sig"))
            except Exception:
                continue
            if not isinstance(raw, dict):
                continue
            state = raw.get("state") if isinstance(raw.get("state"), dict) else {}
            turns = state.get("turns") if isinstance(state.get("turns"), dict) else {}
            assistant = turns.get("assistant") if isinstance(turns.get("assistant"), list) else []
            projected.append({
                "directory": directory.name,
                "file": path.name,
                "traceId": raw.get("traceId"),
                "checkpoint": raw.get("checkpoint"),
                "capturedAt": raw.get("capturedAt"),
                "surfaceId": state.get("surfaceId"),
                "assistantTurnCount": len(assistant),
                "rawSha256": sha256_file(path),
            })
    return projected, [p.name for p in new_dirs]


def derive_route_evidence(
    *,
    admission: dict[str, Any],
    protocol_records: list[dict[str, Any]],
    launcher_records: list[dict[str, Any]],
    diagnostics: list[dict[str, Any]],
    diagnostics_dirs: list[str],
    outer_thread_id: str | None,
    outer_turn_id: str | None,
    terminal_status: str | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    lines = runtime_lines(launcher_records)
    registrations = [m.groups() for line in lines if (m := _REGISTER_RE.search(line))]
    completions = [m.groups() for line in lines if (m := _COMPLETE_RE.search(line))]
    mcp_names = [m.group(1) for line in lines if (m := _MCP_RE.search(line))]

    if len(registrations) != 1:
        errors.append("ROUTE_BROKER_REGISTRATION_CARDINALITY")
        trace_id = None
        token_hash = None
    else:
        trace_id, token_hash = registrations[0]

    if len(diagnostics_dirs) != 1:
        errors.append("ROUTE_BROWSER_DIAGNOSTIC_DIRECTORY_CARDINALITY")
    trace_values = {d.get("traceId") for d in diagnostics if isinstance(d.get("traceId"), str)}
    if trace_id and trace_values != {trace_id}:
        errors.append("ROUTE_TRACE_DIAGNOSTIC_MISMATCH")

    checkpoints = {d.get("checkpoint") for d in diagnostics}
    for required in ("send-accepted", "response-visible", "turn-completed"):
        if required not in checkpoints:
            errors.append(f"ROUTE_CHECKPOINT_MISSING:{required}")
    surfaces = {d.get("surfaceId") for d in diagnostics if isinstance(d.get("surfaceId"), str)}
    if len(surfaces) != 1:
        errors.append("ROUTE_BROWSER_SURFACE_AMBIGUOUS")
    surface = next(iter(surfaces)) if len(surfaces) == 1 else None
    response_rows = [d for d in diagnostics if d.get("checkpoint") == "response-visible" and int(d.get("assistantTurnCount") or 0) > 0]
    if not response_rows:
        errors.append("ROUTE_RESPONSE_BINDING_MISSING")
        response_binding = None
    else:
        response_binding = response_rows[-1]["rawSha256"]

    completed_item_records = [
        r for r in protocol_records
        if r.get("method") == "item/completed" and isinstance(r.get("item"), dict) and isinstance(r["item"].get("id"), str)
    ]
    matching: tuple[tuple[str, str], dict[str, Any]] | None = None
    if trace_id:
        for completion in completions:
            c_trace, prefix = completion
            if c_trace != trace_id:
                continue
            for rec in completed_item_records:
                full_id = rec["item"]["id"]
                if full_id.startswith(prefix) or prefix.startswith(full_id):
                    matching = (completion, rec)
                    break
            if matching:
                break
    if matching is None:
        errors.append("ROUTE_MCP_CALL_NOT_CORRELATED_TO_CODEX_ITEM")
        invocation_id = None
        result_digest = None
    else:
        invocation_id = matching[1]["item"]["id"]
        result_digest = matching[1]["rawSha256"]

    if not mcp_names:
        errors.append("ROUTE_MCP_TOOL_NAME_MISSING")
        tool_name = None
    else:
        tool_name = mcp_names[0]

    if token_hash is None:
        errors.append("ROUTE_CAPABILITY_DIGEST_MISSING")

    base = {
        "request_id": trace_id,
        "outer_thread_id": outer_thread_id,
        "outer_turn_id": outer_turn_id,
        "bridge_mode": "full",
        "model": "chatgpt-web/high",
        "bridge_side_effects_performed": False,
    }
    events = [
        {"event": "codex_request", **base},
        {
            "event": "browser_submit",
            **base,
            "browser_lease_id": surface,
            "qualified_response_binding": response_binding,
        },
        {
            "event": "mcp_roundtrip",
            **base,
            "browser_lease_id": surface,
            "connector": "Codex Native2",
            "capability_token_digest": f"sha256-prefix12:{token_hash}" if token_hash else None,
            "tool_name": tool_name,
            "invocation_id": invocation_id,
            "executor": "codex",
            "tool_result_digest": result_digest,
        },
        {
            "event": "terminal",
            **base,
            "browser_lease_id": surface,
            "qualified_response_binding": response_binding,
            "status": terminal_status,
        },
    ]
    return events, errors


def fsync_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workspace", required=True)
    p.add_argument("--codex-home", required=True)
    p.add_argument("--codex", required=True)
    p.add_argument("--admission", required=True)
    p.add_argument("--diagnostics-root", required=True)
    p.add_argument("--launcher-log", required=True)
    p.add_argument("--evidence-dir", required=True)
    p.add_argument("--execution-config-hash", required=True)
    a = p.parse_args()

    workspace = Path(a.workspace).resolve()
    codex_home = Path(a.codex_home).resolve()
    codex = Path(a.codex).resolve()
    admission_path = Path(a.admission).resolve()
    diagnostics_root = Path(a.diagnostics_root).resolve()
    launcher_log = Path(a.launcher_log).resolve()
    evidence_dir = Path(a.evidence_dir).resolve()

    if evidence_dir.exists():
        raise RuntimeError("EVIDENCE_DIR_ALREADY_EXISTS")
    evidence_dir.mkdir(parents=True, exist_ok=False)
    marker = evidence_dir / "attempt_consumed.marker"
    route_path = evidence_dir / "cgw_route_evidence.jsonl"
    out_path = evidence_dir / "runner_evidence.json"

    admission = json.loads(admission_path.read_text(encoding="utf-8"))
    if admission.get("status") != "PREDISPATCH_ADMISSION_PASS":
        raise RuntimeError("PREDISPATCH_ADMISSION_NOT_PASS")
    if admission.get("attempt_id") != ATTEMPT_ID:
        raise RuntimeError("PREDISPATCH_ATTEMPT_ID_DRIFT")
    if admission.get("attempt_consumed") is not False or admission.get("model_turn_sent") is not False:
        raise RuntimeError("PREDISPATCH_FIREWALL_DRIFT")
    if a.execution_config_hash != EXECUTION_CONFIG_CANONICAL_SHA256:
        raise RuntimeError("EXECUTION_CONFIG_HASH_DRIFT")
    if not codex.is_file() or sha256_file(codex) != CODEX_BINARY_SHA256:
        raise RuntimeError("CODEX_BINARY_HASH_DRIFT")
    if sha256_file(workspace / "input.json") != INPUT_SHA256 or sha256_file(workspace / "TASK.md") != TASK_SHA256:
        raise RuntimeError("WORKSPACE_FIXTURE_HASH_DRIFT")

    baseline = admission.get("diagnostics_baseline") or {}
    baseline_dirs = set(baseline.get("directory_names") or [])
    launcher_offset = int(baseline.get("launcher_log_size") or 0)
    admission_sha = sha256_file(admission_path)
    task_text = (workspace / "TASK.md").read_text(encoding="utf-8")

    evidence: dict[str, Any] = {
        "schema": "G2E-P5A-CGW-FX001-TC-RUNNER-v1",
        "study_id": STUDY_ID,
        "attempt_id": ATTEMPT_ID,
        "route_id": ROUTE_ID,
        "execution_config_hash": a.execution_config_hash,
        "predispatch_admission_sha256": admission_sha,
        "codex_binary_sha256": CODEX_BINARY_SHA256,
        "started_at_unix": time.time(),
        "turn_start_marker_created": False,
        "attempt_consumed": False,
        "turn_start_request_sent": False,
        "turn_start_accepted": False,
        "thread_id": None,
        "turn_id": None,
        "turn_terminal": False,
        "turn_timeout": False,
        "scientific_absolute_turn_deadline_ms": None,
        "terminal_status": None,
        "driver_exception": None,
        "route_evidence_errors": [],
        "unexpected_server_requests": [],
        "result_exists": False,
        "result_sha256": None,
    }

    cmd = [str(codex)]
    for override in ISOLATION_OVERRIDES:
        cmd.extend(["--config", override])
    cmd.append("app-server")
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)

    proc = None
    client = None
    rc = 2
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
        control = perform_control_plane(client, workspace)
        evidence.update(control)
        evidence["thread_id"] = control["thread_id"]

        marker_text = "\n".join([
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            ATTEMPT_ID,
            a.execution_config_hash,
            admission_sha,
            "",
        ])
        fsync_text(marker, marker_text)
        evidence["turn_start_marker_created"] = True
        evidence["attempt_consumed"] = True

        request = {
            "method": "turn/start",
            "id": 10,
            "params": {
                "threadId": evidence["thread_id"],
                "input": [{"type": "text", "text": task_text, "textElements": []}],
                "cwd": str(workspace),
                "approvalPolicy": "never",
            },
        }
        evidence["turn_start_request_sent"] = True
        client.send(request)
        result = client.wait_for_id(10, time.monotonic() + STARTUP_TIMEOUT_S)
        evidence["turn_start_accepted"] = True
        turn = (result or {}).get("turn") or {}
        evidence["turn_id"] = turn.get("id")

        terminal = wait_for_turn(client, evidence["turn_id"] or "")
        evidence["turn_terminal"] = terminal["terminal"]
        evidence["turn_timeout"] = terminal["timeout"]
        completion = terminal.get("completion") or {}
        completed_turn = ((completion.get("params") or {}).get("turn") or {})
        evidence["terminal_status"] = completed_turn.get("status")
        rc = 0
    except Exception as exc:
        evidence["driver_exception"] = f"{type(exc).__name__}:{exc}"
        rc = 2
    finally:
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

        protocol_records = client.protocol_records if client is not None else []
        if client is not None:
            evidence["unexpected_server_requests"] = list(client.unexpected_server_requests)
        try:
            launcher_records = read_launcher_delta(launcher_log, launcher_offset)
            diagnostics, new_dirs = collect_diagnostics(diagnostics_root, baseline_dirs)
            route_events, route_errors = derive_route_evidence(
                admission=admission,
                protocol_records=protocol_records,
                launcher_records=launcher_records,
                diagnostics=diagnostics,
                diagnostics_dirs=new_dirs,
                outer_thread_id=evidence.get("thread_id"),
                outer_turn_id=evidence.get("turn_id"),
                terminal_status=evidence.get("terminal_status"),
            )
            for event in route_events:
                append_jsonl(route_path, event)
            evidence["route_evidence_errors"] = route_errors
            evidence["route_evidence_record_count"] = len(route_events)
            evidence["browser_diagnostics_new_dirs"] = new_dirs
            evidence["browser_diagnostics_projection_sha256"] = sha256_bytes(
                json.dumps(diagnostics, sort_keys=True, separators=(",", ":")).encode("utf-8")
            )
            evidence["launcher_delta_record_count"] = len(launcher_records)
        except Exception as exc:
            evidence["route_evidence_errors"] = [f"ROUTE_EVIDENCE_COLLECTION_EXCEPTION:{type(exc).__name__}:{exc}"]

        result_path = workspace / "result.json"
        evidence["result_exists"] = result_path.is_file()
        if result_path.is_file():
            evidence["result_sha256"] = sha256_file(result_path)
            evidence["result_size"] = result_path.stat().st_size
        evidence["input_unchanged"] = (workspace / "input.json").is_file() and sha256_file(workspace / "input.json") == INPUT_SHA256
        evidence["task_unchanged"] = (workspace / "TASK.md").is_file() and sha256_file(workspace / "TASK.md") == TASK_SHA256
        evidence["workspace_post"] = sorted(p.name for p in workspace.iterdir())
        evidence["finished_at_unix"] = time.time()
        evidence["protocol_sha256"] = sha256_file(client.protocol_path) if client and client.protocol_path.is_file() else None
        evidence["route_evidence_sha256"] = sha256_file(route_path) if route_path.is_file() else None
        evidence["marker_sha256"] = sha256_file(marker) if marker.is_file() else None
        out_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({
            "attempt_id": ATTEMPT_ID,
            "attempt_consumed": evidence["attempt_consumed"],
            "turn_start_sent": evidence["turn_start_request_sent"],
            "turn_terminal": evidence["turn_terminal"],
            "terminal_status": evidence["terminal_status"],
            "route_errors": evidence["route_evidence_errors"],
            "runner_evidence": str(out_path),
        }, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
