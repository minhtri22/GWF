from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import threading
import time
import uuid
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

CODEX_SHA256 = "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b"
PROFILE_ID = "g2e_product_smoke"
ISOLATION_OVERRIDES = (
    "mcp_servers={}",
    "features.apps=false",
    "features.plugins=false",
    "features.remote_plugin=false",
    "features.workspace_dependencies=false",
)
BROKER_REGISTER_RE = re.compile(r"\[chatgpt-web\] broker trace=([A-Za-z0-9_-]{6,128}) registered tokenHash=([a-f0-9]{12})")
BROKER_COMPLETE_RE = re.compile(r"\[chatgpt-web\] broker trace=([A-Za-z0-9_-]{6,128}) completed call=([^ ]+) pending=\d+")
MCP_RE = re.compile(r"\[chatgpt-web-mcp\] ([A-Za-z0-9_.$:-]+) scope=")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def safe_projection(msg: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if "id" in msg and not isinstance(msg.get("id"), (dict, list)):
        out["rpc_id"] = msg.get("id")
    method = msg.get("method")
    if isinstance(method, str):
        out["method"] = method
    params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
    item = params.get("item") if isinstance(params.get("item"), dict) else None
    if item:
        out["item"] = {
            k: item.get(k)
            for k in ("id", "type", "name", "status")
            if isinstance(item.get(k), (str, int, float, bool))
        }
    if method == "turn/completed":
        turn = params.get("turn") if isinstance(params.get("turn"), dict) else {}
        out["turn_id"] = turn.get("id")
        out["turn_status"] = turn.get("status")
        if turn.get("error") is not None:
            out["turn_error"] = turn.get("error")
    return out


class RpcClient:
    def __init__(self, proc: subprocess.Popen[str]) -> None:
        self.proc = proc
        self.q: queue.Queue[tuple[str, str]] = queue.Queue()
        self.pending: list[dict[str, Any]] = []
        self.records: list[dict[str, Any]] = []
        self.stderr_lines: list[str] = []
        self._reader(proc.stdout, "stdout")
        self._reader(proc.stderr, "stderr")

    def _reader(self, stream, tag: str) -> None:
        def run() -> None:
            try:
                for line in iter(stream.readline, ""):
                    self.q.put((tag, line.rstrip("\r\n")))
            finally:
                self.q.put((tag + "_eof", ""))
        threading.Thread(target=run, daemon=True).start()

    def send(self, obj: dict[str, Any]) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def next_json(self, timeout_s: float) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_s
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("APP_SERVER_READ_TIMEOUT")
            try:
                tag, raw = self.q.get(timeout=remaining)
            except queue.Empty as exc:
                raise TimeoutError("APP_SERVER_READ_TIMEOUT") from exc
            if tag == "stderr":
                self.stderr_lines.append(raw)
                continue
            if tag.endswith("_eof"):
                raise EOFError("APP_SERVER_EOF")
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            if isinstance(msg, dict):
                self.records.append(safe_projection(msg))
                return msg

    def wait_for_id(self, req_id: int, timeout_s: float) -> Any:
        deadline = time.monotonic() + timeout_s
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"RPC_TIMEOUT:{req_id}")
            msg = self.next_json(remaining)
            if "method" in msg and "id" not in msg:
                self.pending.append(msg)
                continue
            if msg.get("id") == req_id:
                if "error" in msg:
                    raise RuntimeError(f"RPC_ERROR:{req_id}:{msg['error']}")
                return msg.get("result")

    def wait_turn_completed(self, turn_id: str, timeout_s: float) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_s
        pending = list(self.pending)
        self.pending.clear()
        while True:
            for i, msg in enumerate(pending):
                if msg.get("method") != "turn/completed":
                    continue
                turn = ((msg.get("params") or {}).get("turn") or {})
                if turn.get("id") == turn_id:
                    pending.pop(i)
                    return msg
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("TURN_COMPLETION_TIMEOUT")
            try:
                msg = self.next_json(min(remaining, 2.0))
            except TimeoutError:
                continue
            if "method" in msg and "id" not in msg:
                pending.append(msg)


def read_log_delta(path: Path, offset: int) -> tuple[list[str], bool]:
    if not path.is_file():
        return [], False
    size = path.stat().st_size
    rotated = size < offset
    if rotated:
        offset = 0
    with path.open("rb") as f:
        f.seek(offset)
        raw = f.read()
    return raw.decode("utf-8", errors="replace").splitlines(), rotated


def route_projection(lines: list[str]) -> dict[str, Any]:
    regs: list[dict[str, str]] = []
    completes: list[dict[str, str]] = []
    mcp: list[str] = []
    for line in lines:
        if m := BROKER_REGISTER_RE.search(line):
            regs.append({"trace_id": m.group(1), "token_hash": m.group(2)})
        if m := BROKER_COMPLETE_RE.search(line):
            completes.append({"trace_id": m.group(1), "call": m.group(2)})
        if m := MCP_RE.search(line):
            mcp.append(m.group(1))
    return {
        "broker_registrations": regs,
        "broker_completions": completes,
        "mcp_tools": mcp,
    }


def diagnostic_dirs(root: Path) -> set[str]:
    if not root.is_dir():
        return set()
    return {p.name for p in root.iterdir() if p.is_dir()}


def terminate(proc: subprocess.Popen[str] | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def get_json(url: str, timeout: float = 3.0) -> dict[str, Any]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP_GET_FAILED:{url}:status={exc.code}:body={body[:500]}") from exc
    except Exception as exc:
        raise RuntimeError(f"HTTP_GET_FAILED:{url}:{type(exc).__name__}:{exc}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"HTTP_GET_BAD_JSON:{url}:{type(exc).__name__}:{exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"HTTP_GET_JSON_OBJECT_REQUIRED:{url}")
    return value


def build_config(result_path: Path) -> str:
    rp = str(result_path).replace("\\", "\\\\")
    return (
        'model = "chatgpt-web/high"\n'
        'model_provider = "openai"\n'
        'openai_base_url = "http://127.0.0.1:17841/v1"\n'
        'approval_policy = "never"\n'
        f'default_permissions = "{PROFILE_ID}"\n'
        '\n'
        f'[permissions.{PROFILE_ID}]\n'
        'description = "G2E product smoke: read workspace, write result.json only"\n'
        '\n'
        f'[permissions.{PROFILE_ID}.filesystem]\n'
        '":root" = "read"\n'
        f'"{rp}" = "write"\n'
        '\n'
        f'[permissions.{PROFILE_ID}.network]\n'
        'enabled = false\n'
    )


def run(a: argparse.Namespace) -> dict[str, Any]:
    repo = Path(a.repo).resolve()
    codex = Path(a.codex_exe).resolve()
    bridge_home = Path(a.bridge_home).resolve()
    launcher_data = Path(a.launcher_data).resolve()
    smoke_root = Path(a.output_root).resolve()

    if smoke_root.exists():
        raise RuntimeError(f"OUTPUT_ROOT_EXISTS:{smoke_root}")
    smoke_root.mkdir(parents=True)

    workspace = smoke_root / "workspace"
    codex_home = smoke_root / "codex-home"
    evidence = smoke_root / "evidence"
    workspace.mkdir()
    codex_home.mkdir()
    evidence.mkdir()

    summary: dict[str, Any] = {
        "schema": "G2E-PRODUCT-SMOKE-v1",
        "mode": "PRODUCT",
        "status": "RUNNING",
        "success": False,
        "stage": "INIT",
        "paths": {
            "root": str(smoke_root),
            "workspace": str(workspace),
            "codex_home": str(codex_home),
            "evidence": str(evidence),
        },
        "checks": {},
        "runtime": {},
        "protocol": {},
        "route": {},
        "artifact": {},
        "error": None,
    }

    proc: subprocess.Popen[str] | None = None
    client: RpcClient | None = None
    launcher_log = launcher_data / "logs" / "launcher.jsonl"
    log_offset = launcher_log.stat().st_size if launcher_log.is_file() else 0
    diagnostics_root = bridge_home / "diagnostics" / "browser-turns"
    diag_before: set[str] = diagnostic_dirs(diagnostics_root)
    try:
        summary["stage"] = "VERIFY_RUNTIME"
        if not codex.is_file():
            raise RuntimeError("CODEX_EXE_MISSING")
        codex_sha = sha256_file(codex)
        summary["checks"]["codex_sha"] = codex_sha
        if codex_sha != CODEX_SHA256:
            raise RuntimeError(f"CODEX_SHA_MISMATCH:{codex_sha}")

        health = get_json("http://127.0.0.1:17841/healthz", timeout=3.0)
        summary["runtime"]["health"] = health
        if health.get("status") != "ok" or health.get("mode") != "full":
            raise RuntimeError(f"CGW_HEALTH_NOT_READY:{health}")

        supervisor_path = bridge_home / "runtime" / "launcher-supervisor.json"
        supervisor = json.loads(supervisor_path.read_text(encoding="utf-8-sig"))
        summary["runtime"]["supervisor"] = supervisor
        if int(supervisor.get("daemonPid") or 0) != int(health.get("pid") or -1):
            raise RuntimeError("CGW_HEALTH_SUPERVISOR_PID_MISMATCH")

        run_id = uuid.uuid4().hex[:12]
        input_obj = {"run_id": run_id, "values": [17, -4, 8, 0, -1]}
        expected = {"run_id": run_id, "count": 5, "sum": 20, "status": "ok"}
        input_path = workspace / "input.json"
        result_path = workspace / "result.json"
        task_path = workspace / "TASK.md"
        input_path.write_text(json.dumps(input_obj, indent=2) + "\n", encoding="utf-8", newline="\n")
        task = (
            "G2E PRODUCT SMOKE TEST.\n"
            "Read input.json in the current workspace.\n"
            "Create result.json in the current workspace with exactly four keys:\n"
            "  run_id: copy input.run_id exactly\n"
            "  count: number of integers in input.values\n"
            "  sum: integer sum of input.values\n"
            '  status: string "ok"\n'
            "Use the available local execution/file tools to create the file.\n"
            "Do not use web/network. Do not modify input.json or TASK.md.\n"
            "After result.json exists, respond briefly.\n"
        )
        task_path.write_text(task, encoding="utf-8", newline="\n")
        summary["artifact"]["expected"] = expected
        summary["artifact"]["input_sha256"] = sha256_file(input_path)
        summary["artifact"]["task_sha256"] = sha256_file(task_path)

        (codex_home / "config.toml").write_text(build_config(result_path), encoding="utf-8", newline="\n")
        default_auth = Path.home() / ".codex" / "auth.json"
        if not default_auth.is_file():
            raise RuntimeError("DEFAULT_CODEX_AUTH_MISSING")
        shutil.copy2(default_auth, codex_home / "auth.json")

        summary["stage"] = "START_CODEX"
        cmd = [str(codex)]
        for override in ISOLATION_OVERRIDES:
            cmd.extend(["--config", override])
        cmd.append("app-server")
        env = os.environ.copy()
        env["CODEX_HOME"] = str(codex_home)
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
        client = RpcClient(proc)

        summary["stage"] = "CONTROL_PLANE"
        client.send({
            "method": "initialize",
            "id": 1,
            "params": {
                "clientInfo": {"name": "g2e_product_smoke", "title": "G2E Product Smoke", "version": "1.0.0"},
                "capabilities": {"experimentalApi": True},
            },
        })
        client.wait_for_id(1, 20)
        client.send({"method": "initialized", "params": {}})

        client.send({"method": "account/read", "id": 2, "params": {"refreshToken": False}})
        account = client.wait_for_id(2, 20)
        summary["checks"]["account_ready"] = bool(
            isinstance(account, dict)
            and (isinstance(account.get("account"), dict) or account.get("requiresOpenaiAuth") is False)
        )
        if not summary["checks"]["account_ready"]:
            raise RuntimeError("CODEX_AUTH_NOT_READY")

        client.send({
            "method": "permissionProfile/list",
            "id": 3,
            "params": {"cursor": None, "limit": 100, "cwd": str(workspace)},
        })
        profiles = client.wait_for_id(3, 20)
        profile_items: list[Any] = []
        if isinstance(profiles, dict):
            for key in ("data", "items", "profiles"):
                if isinstance(profiles.get(key), list):
                    profile_items = profiles[key]
                    break
        profile = next(
            (x for x in profile_items if isinstance(x, dict) and x.get("id") == PROFILE_ID),
            None,
        )
        summary["checks"]["permission_profile_allowed"] = bool(profile and profile.get("allowed") is True)
        if not summary["checks"]["permission_profile_allowed"]:
            raise RuntimeError(f"PERMISSION_PROFILE_NOT_ALLOWED:{profile}")

        client.send({
            "method": "thread/start",
            "id": 4,
            "params": {
                "cwd": str(workspace),
                "approvalPolicy": "never",
                "permissions": PROFILE_ID,
                "ephemeral": True,
            },
        })
        thread_result = client.wait_for_id(4, 30)
        thread = thread_result.get("thread") if isinstance(thread_result, dict) else None
        thread_id = thread.get("id") if isinstance(thread, dict) else None
        if not isinstance(thread_id, str) or not thread_id:
            raise RuntimeError("THREAD_ID_MISSING")
        summary["protocol"]["thread_id"] = thread_id

        summary["stage"] = "TURN"
        client.send({
            "method": "turn/start",
            "id": 5,
            "params": {
                "threadId": thread_id,
                "input": [{"type": "text", "text": task, "textElements": []}],
                "cwd": str(workspace),
                "approvalPolicy": "never",
            },
        })
        turn_result = client.wait_for_id(5, 30)
        turn = turn_result.get("turn") if isinstance(turn_result, dict) else None
        turn_id = turn.get("id") if isinstance(turn, dict) else None
        if not isinstance(turn_id, str) or not turn_id:
            raise RuntimeError("TURN_ID_MISSING")
        summary["protocol"]["turn_id"] = turn_id

        completed = client.wait_turn_completed(turn_id, a.timeout)
        terminal = ((completed.get("params") or {}).get("turn") or {})
        summary["protocol"]["terminal_status"] = terminal.get("status")
        summary["protocol"]["terminal_error"] = terminal.get("error")

        summary["stage"] = "VERIFY_ARTIFACT"
        if not result_path.is_file():
            raise RuntimeError("RESULT_JSON_MISSING")
        observed = json.loads(result_path.read_text(encoding="utf-8"))
        summary["artifact"]["observed"] = observed
        summary["artifact"]["result_sha256"] = sha256_file(result_path)
        summary["artifact"]["exact_match"] = observed == expected
        if observed != expected:
            raise RuntimeError(f"RESULT_JSON_MISMATCH:{canonical_json(observed)}")

        if sha256_file(input_path) != summary["artifact"]["input_sha256"]:
            raise RuntimeError("INPUT_MUTATED")
        if sha256_file(task_path) != summary["artifact"]["task_sha256"]:
            raise RuntimeError("TASK_MUTATED")

        summary["status"] = "PASS"
        summary["success"] = True
        summary["stage"] = "DONE"

    except Exception as exc:
        summary["status"] = "FAIL"
        summary["success"] = False
        summary["error"] = f"{type(exc).__name__}:{exc}"
    finally:
        terminate(proc)

        launcher_log = launcher_data / "logs" / "launcher.jsonl"
        try:
            delta, rotated = read_log_delta(launcher_log, log_offset)
            summary["route"]["launcher_log_rotated"] = rotated
            summary["route"].update(route_projection(delta))
        except Exception as exc:
            summary["route"]["log_collection_error"] = f"{type(exc).__name__}:{exc}"

        try:
            diagnostics_root = bridge_home / "diagnostics" / "browser-turns"
            after = diagnostic_dirs(diagnostics_root)
            summary["route"]["new_diagnostic_dirs"] = sorted(after - diag_before)
        except Exception as exc:
            summary["route"]["diagnostic_collection_error"] = f"{type(exc).__name__}:{exc}"

        if client is not None:
            summary["protocol"]["records"] = client.records
            summary["protocol"]["stderr_tail"] = client.stderr_lines[-30:]

        out = evidence / "summary.json"
        out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        print(f"G2E_PRODUCT_SMOKE_SUMMARY={out}")

    return summary


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--codex-exe", required=True)
    p.add_argument("--bridge-home", required=True)
    p.add_argument("--launcher-data", required=True)
    p.add_argument("--output-root")
    p.add_argument("--timeout", type=float, default=180.0)
    a = p.parse_args()

    if not a.output_root:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        a.output_root = str(Path(a.repo) / "g2e" / ".local" / "product-smokes" / f"{stamp}-{os.getpid()}")

    result = run(a)
    return 0 if result.get("success") else 2


if __name__ == "__main__":
    raise SystemExit(main())
