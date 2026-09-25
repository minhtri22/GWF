from __future__ import annotations

import argparse
import hashlib
import http.server
import json
import os
import queue
import socketserver
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

CODEX_SHA256 = "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b"
EXPECTED_MODEL = "chatgpt-web/high"
STARTUP_TIMEOUT_S = 20.0
WITNESS_TIMEOUT_S = 30.0
ISOLATION_OVERRIDES = (
    "mcp_servers={}",
    "features.apps=false",
    "features.plugins=false",
    "features.remote_plugin=false",
    "features.workspace_dependencies=false",
)
MUTATION_TOOL_NAMES = {
    "apply_patch",
    "shell",
    "shell_command",
    "exec_command",
    "write_stdin",
    "request_permissions",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tool_projection(body: dict[str, Any]) -> list[dict[str, str | None]]:
    tools = body.get("tools")
    if not isinstance(tools, list):
        return []
    out: list[dict[str, str | None]] = []
    for item in tools[:128]:
        if not isinstance(item, dict):
            continue
        typ = item.get("type")
        name = item.get("name")
        fn = item.get("function")
        if not isinstance(name, str) and isinstance(fn, dict) and isinstance(fn.get("name"), str):
            name = fn.get("name")
        out.append({
            "type": typ if isinstance(typ, str) else None,
            "name": name if isinstance(name, str) else None,
        })
    return out


def metadata_projection(body: dict[str, Any]) -> dict[str, Any]:
    metadata = body.get("metadata")
    keys = sorted(str(k) for k in metadata.keys()) if isinstance(metadata, dict) else []
    lower = [k.lower() for k in keys]
    return {
        "metadata_present": isinstance(metadata, dict),
        "metadata_keys": keys[:64],
        "thread_metadata_present": any("thread" in k for k in lower),
        "turn_metadata_present": any("turn" in k for k in lower),
    }


def bounded_projection(method: str, path: str, headers: http.client.HTTPMessage, raw: bytes) -> dict[str, Any]:
    projection: dict[str, Any] = {
        "method": method,
        "path": path,
        "content_length": len(raw),
        "request_body_sha256": sha256_bytes(raw),
        "authorization_header_present": bool(headers.get("Authorization")),
        "json": False,
        "model": None,
        "tool_count": None,
        "tools": [],
        "metadata_present": False,
        "metadata_keys": [],
        "thread_metadata_present": False,
        "turn_metadata_present": False,
    }
    try:
        body = json.loads(raw.decode("utf-8"))
    except Exception:
        return projection
    if not isinstance(body, dict):
        return projection
    projection["json"] = True
    model = body.get("model")
    projection["model"] = model if isinstance(model, str) else None
    tools_raw = body.get("tools")
    projection["tool_count"] = len(tools_raw) if isinstance(tools_raw, list) else None
    projection["tools"] = tool_projection(body)
    projection.update(metadata_projection(body))
    return projection


class WitnessState:
    def __init__(self) -> None:
        self.q: queue.Queue[dict[str, Any]] = queue.Queue()
        self.total_post_count = 0
        self.responses_post_count = 0
        self.forwarded_requests = 0


class WitnessHandler(http.server.BaseHTTPRequestHandler):
    state: WitnessState

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _respond_json(self, status: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/v1/models":
            self._respond_json(200, {"object": "list", "data": [{"id": EXPECTED_MODEL, "object": "model"}]})
            return
        self._respond_json(404, {"error": {"type": "g2e_witness_not_found"}})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length)
        self.state.total_post_count += 1
        if self.path == "/v1/responses":
            self.state.responses_post_count += 1
            if self.state.q.empty():
                self.state.q.put(bounded_projection("POST", self.path, self.headers, raw))
        self._respond_json(409, {
            "error": {
                "type": "g2e_rp_i3_witness_stop",
                "message": "Local zero-science witness rejects before upstream/model forwarding."
            }
        })


class ThreadingLoopbackServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


class RpcClient:
    def __init__(self, proc: subprocess.Popen[str]) -> None:
        self.proc = proc
        self.q: queue.Queue[tuple[str, str]] = queue.Queue()
        self.pending: list[dict[str, Any]] = []
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
        self.proc.stdin.write(json.dumps(obj, separators=(",", ":")) + "\n")
        self.proc.stdin.flush()

    def wait_for_id(self, req_id: int, timeout_s: float) -> Any:
        deadline = time.monotonic() + timeout_s
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"RPC_TIMEOUT:{req_id}")
            tag, raw = self.q.get(timeout=remaining)
            if tag == "stderr":
                continue
            if tag.endswith("_eof"):
                raise EOFError("APP_SERVER_EOF")
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            if isinstance(msg, dict) and msg.get("id") == req_id and "method" not in msg:
                if "error" in msg:
                    raise RuntimeError(f"RPC_ERROR:{req_id}")
                return msg.get("result")
            if isinstance(msg, dict) and "method" in msg and "id" not in msg:
                self.pending.append(msg)


def write_config(codex_home: Path, witness_port: int) -> None:
    config = (
        f'model = "{EXPECTED_MODEL}"\n'
        'model_provider = "openai"\n'
        f'openai_base_url = "http://127.0.0.1:{witness_port}/v1"\n'
        'approval_policy = "never"\n'
        'sandbox_mode = "read-only"\n'
        'cli_auth_credentials_store = "file"\n'
        '\n[features]\n'
        'enable_request_compression = false\n'
    )
    codex_home.mkdir(parents=True, exist_ok=True)
    (codex_home / "config.toml").write_text(config, encoding="utf-8", newline="\n")


def terminate(proc: subprocess.Popen[str] | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def run(args: argparse.Namespace) -> dict[str, Any]:
    codex = Path(args.codex_exe).resolve()
    if not codex.is_file():
        raise RuntimeError("CODEX_EXE_MISSING")
    codex_sha = sha256_file(codex)
    if codex_sha != CODEX_SHA256:
        raise RuntimeError(f"CODEX_SHA_MISMATCH:{codex_sha}")

    state = WitnessState()
    handler = type("BoundWitnessHandler", (WitnessHandler,), {"state": state})
    server = ThreadingLoopbackServer(("127.0.0.1", 0), handler)
    port = int(server.server_address[1])
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    proc: subprocess.Popen[str] | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="g2e-rp-i3-") as td:
            root = Path(td)
            codex_home = root / "codex-home"
            workspace = root / "workspace"
            workspace.mkdir(parents=True)
            write_config(codex_home, port)

            cmd = [str(codex)]
            for override in ISOLATION_OVERRIDES:
                cmd.extend(["--config", override])
            cmd.append("app-server")

            env = os.environ.copy()
            env["CODEX_HOME"] = str(codex_home)
            env["OPENAI_API_KEY"] = "sk-g2e-rp-i3-loopback-witness-only"
            env.pop("OPENAI_BASE_URL", None)

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
            client.send({
                "method": "initialize",
                "id": 1,
                "params": {
                    "clientInfo": {"name": "g2e_rp_i3", "title": "G2E RP-I3 Witness", "version": "1.0.0"},
                    "capabilities": {"experimentalApi": True},
                },
            })
            client.wait_for_id(1, STARTUP_TIMEOUT_S)
            client.send({"method": "initialized", "params": {}})

            client.send({
                "method": "thread/start",
                "id": 2,
                "params": {
                    "cwd": str(workspace),
                    "approvalPolicy": "never",
                    "sandbox": "read-only",
                    "ephemeral": True,
                },
            })
            thread_result = None
            thread_error = None
            try:
                thread_result = client.wait_for_id(2, STARTUP_TIMEOUT_S)
            except Exception as exc:
                thread_error = type(exc).__name__
                if state.q.empty():
                    raise

            thread = thread_result.get("thread") if isinstance(thread_result, dict) else None
            thread_id = thread.get("id") if isinstance(thread, dict) else None

            if state.q.empty():
                if not isinstance(thread_id, str) or not thread_id:
                    raise RuntimeError("THREAD_ID_MISSING")
                client.send({
                    "method": "turn/start",
                    "id": 3,
                    "params": {
                        "threadId": thread_id,
                        "input": [{
                            "type": "text",
                            "text": "G2E RP-I3 outbound contract witness.",
                            "textElements": [],
                        }],
                        "cwd": str(workspace),
                        "approvalPolicy": "never",
                    },
                })

            try:
                captured = state.q.get(timeout=WITNESS_TIMEOUT_S)
            except queue.Empty as exc:
                raise RuntimeError("RESPONSES_POST_NOT_WITNESSED") from exc
            finally:
                terminate(proc)

            tools = captured.get("tools") if isinstance(captured.get("tools"), list) else []
            tool_names = sorted({
                str(item["name"]) for item in tools
                if isinstance(item, dict) and isinstance(item.get("name"), str)
            })
            mutation_hits = sorted(set(tool_names).intersection(MUTATION_TOOL_NAMES))

            result = {
                "schema": "G2E-P5A-CGW-FX001-RP-I3-v1",
                "zero_science": True,
                "codex": {
                    "path": str(codex),
                    "sha256": codex_sha,
                    "version_expected": "codex-cli 0.153.4",
                },
                "isolation": {
                    "temporary_codex_home": True,
                    "real_auth_copied": False,
                    "dummy_api_key_only": True,
                    "mcp_servers_empty": True,
                    "apps_disabled": True,
                    "plugins_disabled": True,
                    "remote_plugin_disabled": True,
                    "workspace_dependencies_disabled": True,
                    "witness_host": "127.0.0.1",
                    "witness_port": port,
                    "forwarded_requests": state.forwarded_requests,
                },
                "captured": captured,
                "derived": {
                    "total_post_count_observed": state.total_post_count,
                    "responses_post_count_observed": state.responses_post_count,
                    "thread_start_error_after_local_reject": thread_error,
                    "tool_names": tool_names,
                    "mutation_capable_known_tool_names": mutation_hits,
                    "mutation_capable_known_surface_present": bool(mutation_hits),
                },
                "science_firewall": {
                    "cgw_request": False,
                    "browser_submission": False,
                    "mcp_invocation": False,
                    "upstream_model_forwarding": False,
                    "scientific_attempt_created": False,
                    "replacement_attempt_authorized": False,
                },
                "verdict": "BLOCKED",
            }
            if (
                captured.get("method") == "POST"
                and captured.get("path") == "/v1/responses"
                and captured.get("json") is True
                and captured.get("model") == EXPECTED_MODEL
                and isinstance(captured.get("tool_count"), int)
                and isinstance(captured.get("request_body_sha256"), str)
                and len(captured["request_body_sha256"]) == 64
                and state.responses_post_count == 1
                and state.forwarded_requests == 0
            ):
                result["verdict"] = "PASS_CODEX_OUTBOUND_CONTRACT_WITNESSED"
            return result
    finally:
        terminate(proc)
        server.shutdown()
        server.server_close()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--codex-exe", required=True)
    p.add_argument("--output")
    args = p.parse_args()
    result = run(args)
    text = json.dumps(result, indent=2, sort_keys=False)
    print(text)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8", newline="\n")
    return 0 if result.get("verdict") == "PASS_CODEX_OUTBOUND_CONTRACT_WITNESSED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
