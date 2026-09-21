from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import queue
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_TOKENS = (
    "initialize",
    "thread/start",
    "thread/resume",
    "turn/start",
    "item/started",
    "item/completed",
)

OPTIONAL_TOKENS = (
    "thread/fork",
    "turn/steer",
    "sessionId",
    "requestApproval",
    "mcpServer",
    "skill",
    "command/exec",
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve_command(command: str) -> Path | None:
    candidate = shutil.which(command)
    if candidate:
        return Path(candidate).resolve()
    path = Path(command)
    if path.exists():
        return path.resolve()
    return None


def _prefix(executable: Path) -> list[str]:
    suffix = executable.suffix.lower()
    if os.name == "nt" and suffix in {".cmd", ".bat"}:
        return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", str(executable)]
    return [str(executable)]


def _run(executable: Path, args: list[str], timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*_prefix(executable), *args],
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def _schema_inventory(schema_dir: Path) -> tuple[list[dict[str, Any]], str, str]:
    files: list[dict[str, Any]] = []
    combined_text_parts: list[str] = []
    for path in sorted(schema_dir.rglob("*.json")):
        rel = path.relative_to(schema_dir).as_posix()
        raw = path.read_bytes()
        files.append({"path": rel, "sha256": _sha256_bytes(raw), "size": len(raw)})
        try:
            combined_text_parts.append(raw.decode("utf-8"))
        except UnicodeDecodeError:
            combined_text_parts.append("")
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return files, _sha256_bytes(canonical), "\n".join(combined_text_parts)


def _sanitize_initialize_response(message: dict[str, Any]) -> dict[str, Any]:
    result = message.get("result")
    if not isinstance(result, dict):
        return {"response_id": message.get("id"), "result_present": False}
    allowed = {}
    for key in ("userAgent", "platformFamily", "platformOs"):
        value = result.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            allowed[key] = value
    return {
        "response_id": message.get("id"),
        "result_present": True,
        "metadata": allowed,
    }


def _initialize_handshake(executable: Path, timeout: float) -> tuple[bool, dict[str, Any], str | None]:
    proc = subprocess.Popen(
        [*_prefix(executable), "app-server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    q: queue.Queue[str] = queue.Queue()

    def reader() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            q.put(line)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    try:
        assert proc.stdin is not None
        initialize = {
            "method": "initialize",
            "id": 1,
            "params": {
                "clientInfo": {
                    "name": "g2e_p5a_discovery",
                    "title": "G2E P5A Discovery",
                    "version": "1",
                }
            },
        }
        proc.stdin.write(json.dumps(initialize, separators=(",", ":")) + "\n")
        proc.stdin.flush()

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                line = q.get(timeout=max(0.05, deadline - time.monotonic()))
            except queue.Empty:
                break
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if message.get("id") == 1:
                if "error" in message:
                    return False, {"response_id": 1}, str(message.get("error"))
                proc.stdin.write(json.dumps({"method": "initialized", "params": {}}, separators=(",", ":")) + "\n")
                proc.stdin.flush()
                return True, _sanitize_initialize_response(message), None
        return False, {}, "initialize handshake timeout"
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def discover(codex_command: str, output: Path, work_dir: Path, timeout: float) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": "G2E-P5A-CODEX-DISCOVERY-v1",
        "status": "UNRESOLVED",
        "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "codex_command": codex_command,
        "secrets_persisted": False,
        "functional_task_executed": False,
        "errors": [],
        "limitations": [
            "D1 structural discovery only",
            "no thread/start or model turn executed",
            "task execution capabilities remain unqualified until D2",
        ],
    }

    executable = _resolve_command(codex_command)
    if executable is None:
        report["status"] = "HARNESS_NOT_FOUND"
        report["errors"].append("codex executable not found")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    report["executable_path"] = str(executable)
    try:
        report["executable_sha256"] = _sha256_file(executable)
    except OSError as exc:
        report["executable_sha256"] = None
        report["executable_sha256_unavailable_reason"] = type(exc).__name__

    version = _run(executable, ["--version"], timeout=timeout)
    report["codex_version_stdout"] = version.stdout.strip()
    report["codex_version_stderr_sha256"] = _sha256_bytes(version.stderr.encode("utf-8"))
    if version.returncode != 0 or not version.stdout.strip():
        report["status"] = "VERSION_UNRESOLVED"
        report["errors"].append(f"codex --version exit={version.returncode}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    help_result = _run(executable, ["app-server", "--help"], timeout=timeout)
    report["app_server_help_exit_code"] = help_result.returncode
    report["app_server_help_sha256"] = _sha256_bytes(help_result.stdout.encode("utf-8"))
    if help_result.returncode != 0:
        report["errors"].append("codex app-server --help failed")

    schema_dir = work_dir / "schemas"
    if schema_dir.exists():
        shutil.rmtree(schema_dir)
    schema_dir.mkdir(parents=True, exist_ok=True)
    generated = _run(
        executable,
        ["app-server", "generate-json-schema", "--out", str(schema_dir)],
        timeout=max(timeout, 60.0),
    )
    report["schema_generation_exit_code"] = generated.returncode
    if generated.returncode != 0:
        report["status"] = "SCHEMA_DISCOVERY_FAILED"
        report["errors"].append("generate-json-schema failed")
        report["schema_generation_stderr_sha256"] = _sha256_bytes(generated.stderr.encode("utf-8"))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    files, bundle_digest, schema_text = _schema_inventory(schema_dir)
    report["generated_schema_files"] = files
    report["schema_inventory_digest"] = bundle_digest
    report["required_protocol_tokens"] = {token: token in schema_text for token in REQUIRED_TOKENS}
    report["optional_protocol_tokens"] = {token: token in schema_text for token in OPTIONAL_TOKENS}

    handshake_ok, handshake_meta, handshake_error = _initialize_handshake(executable, timeout)
    report["initialize_handshake"] = {
        "success": handshake_ok,
        "sanitized_response": handshake_meta,
        "error": handshake_error,
    }

    missing = [token for token, present in report["required_protocol_tokens"].items() if not present]
    if missing:
        report["errors"].append("missing required protocol tokens: " + ",".join(missing))
    if not handshake_ok:
        report["errors"].append("initialize handshake failed")

    report["status"] = "D1_MINIMUM_QUALIFIED" if not missing and handshake_ok and help_result.returncode == 0 else "D1_MINIMUM_NOT_QUALIFIED"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only G2E P5A Codex actual-harness discovery probe")
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--output", default="P5A_CODEX_DISCOVERY.json")
    parser.add_argument("--work-dir", default=".p5a-codex-discovery")
    parser.add_argument("--timeout", type=float, default=12.0)
    args = parser.parse_args()

    report = discover(
        args.codex_command,
        Path(args.output).resolve(),
        Path(args.work_dir).resolve(),
        args.timeout,
    )
    print(json.dumps({
        "status": report["status"],
        "output": str(Path(args.output).resolve()),
        "functional_task_executed": report["functional_task_executed"],
        "secrets_persisted": report["secrets_persisted"],
    }, sort_keys=True))
    return 0 if report["status"] == "D1_MINIMUM_QUALIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
