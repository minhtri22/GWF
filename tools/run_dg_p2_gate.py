from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import socket
import tempfile
from threading import Thread

from gwr.document_validation import LycheeAdapter


ROOT = Path(__file__).resolve().parents[1]
LYCHEE_DIR = ROOT / "tools" / "document_validation" / "lychee"
TOOLCHAIN = LYCHEE_DIR / "toolchain.json"
CONFIG = LYCHEE_DIR / "lychee.toml"
FIXTURES = ROOT / "tests" / "fixtures" / "document_validation"
INTERNAL_VALID = FIXTURES / "lychee_internal_valid.md"
INTERNAL_BROKEN = FIXTURES / "lychee_internal_broken.md"
TARGET = FIXTURES / "lychee_target.md"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class _Handler(BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:
        self._respond()

    def do_GET(self) -> None:
        self._respond()

    def _respond(self) -> None:
        code = 200 if self.path == "/ok" else 404
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(b"ok" if code == 200 else b"missing")

    def log_message(self, format: str, *args: object) -> None:
        return


@contextmanager
def local_http_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def closed_loopback_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--executable", default="lychee")
    ap.add_argument("--out", default=str(ROOT / "evidence" / "dg-p2" / "DG_P2_GATE.json"))
    args = ap.parse_args()

    toolchain = json.loads(TOOLCHAIN.read_text(encoding="utf-8"))
    resolved_executable = shutil.which(args.executable) or args.executable
    executable_path = Path(resolved_executable)
    adapter = LycheeAdapter(
        executable=str(executable_path),
        expected_version=toolchain["version"],
        config_path=CONFIG,
    )

    static_before = {
        str(path): path.read_bytes()
        for path in (INTERNAL_VALID, INTERNAL_BROKEN, TARGET)
    }

    internal_valid = adapter.validate(INTERNAL_VALID)
    internal_broken = adapter.validate(INTERNAL_BROKEN)
    repeat = adapter.validate(INTERNAL_VALID)

    with tempfile.TemporaryDirectory(prefix="gwf-dg-p2-") as tmp:
        tmp_path = Path(tmp)
        with local_http_server() as port:
            external_valid_path = tmp_path / "external_valid.md"
            external_broken_path = tmp_path / "external_broken.md"
            external_valid_path.write_text(
                f"# External valid\n\n[ok](http://127.0.0.1:{port}/ok)\n",
                encoding="utf-8",
            )
            external_broken_path.write_text(
                f"# External broken\n\n[missing](http://127.0.0.1:{port}/missing)\n",
                encoding="utf-8",
            )
            external_valid_before = external_valid_path.read_bytes()
            external_broken_before = external_broken_path.read_bytes()
            external_valid = adapter.validate(external_valid_path)
            external_broken = adapter.validate(external_broken_path)
            external_unchanged = (
                external_valid_path.read_bytes() == external_valid_before
                and external_broken_path.read_bytes() == external_broken_before
            )

        network_path = tmp_path / "network_failure.md"
        closed_port = closed_loopback_port()
        network_path.write_text(
            f"# Network failure\n\n[down](http://127.0.0.1:{closed_port}/down)\n",
            encoding="utf-8",
        )
        network_before = network_path.read_bytes()
        network_failure = adapter.validate(network_path)
        network_unchanged = network_path.read_bytes() == network_before

    expected_config_hash = toolchain["config_sha256"].removeprefix("sha256:")
    checks = {
        "toolchain_version_pinned": toolchain["version"] == "0.24.2",
        "upstream_commit_pinned": toolchain["upstream_commit"] == "2bba271688c1abb1503097a064e6c3bc1d1b6a9b",
        "config_hash_matches": sha256_file(CONFIG) == expected_config_hash,
        "real_version_observed": internal_valid.validator_version == toolchain["version"],
        "internal_valid_pass": (
            internal_valid.execution_status == "SUCCEEDED"
            and internal_valid.content_status == "PASS"
            and not internal_valid.findings
        ),
        "internal_broken_detected": (
            internal_broken.execution_status == "SUCCEEDED"
            and internal_broken.content_status == "FINDINGS"
            and any(f.rule_id == "LYCHEE.INTERNAL_BROKEN" for f in internal_broken.findings)
        ),
        "external_valid_pass": (
            external_valid.execution_status == "SUCCEEDED"
            and external_valid.content_status == "PASS"
            and not external_valid.findings
        ),
        "external_broken_detected": (
            external_broken.execution_status == "SUCCEEDED"
            and external_broken.content_status == "FINDINGS"
            and any(
                f.rule_id == "LYCHEE.EXTERNAL_BROKEN"
                and f.message == "Broken external link (HTTP 404)"
                for f in external_broken.findings
            )
        ),
        "internal_external_distinguishable": (
            {f.rule_id for f in internal_broken.findings} == {"LYCHEE.INTERNAL_BROKEN"}
            and {f.rule_id for f in external_broken.findings} == {"LYCHEE.EXTERNAL_BROKEN"}
        ),
        "network_failure_not_content_failure": (
            network_failure.execution_status == "TOOL_ERROR"
            and network_failure.content_status == "NOT_EVALUATED"
            and network_failure.error_code == "NETWORK_FAILURE"
            and not network_failure.findings
        ),
        "raw_urls_not_persisted": all(
            "http://" not in f.message
            and "https://" not in f.message
            and "file://" not in f.message
            for f in (*internal_broken.findings, *external_broken.findings)
        ),
        "repeat_normalizes_identically": internal_valid.to_dict() == repeat.to_dict(),
        "source_not_mutated": (
            all(path.read_bytes() == before for path, before in ((Path(p), b) for p, b in static_before.items()))
            and external_unchanged
            and network_unchanged
        ),
    }

    status = "PASS" if all(checks.values()) else "FAIL"
    result = {
        "schema": "DG-P2-GATE-v1",
        "status": status,
        "toolchain": toolchain,
        "lychee_binary_sha256": sha256_file(executable_path) if executable_path.is_file() else None,
        "checks": checks,
        "internal_valid_execution": internal_valid.to_dict(),
        "internal_broken_execution": internal_broken.to_dict(),
        "external_valid_execution": external_valid.to_dict(),
        "external_broken_execution": external_broken.to_dict(),
        "network_failure_execution": network_failure.to_dict(),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    main()
