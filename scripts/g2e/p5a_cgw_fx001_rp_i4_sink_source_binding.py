from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

UPSTREAM_TAG_COMMIT = "b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494"
CRITICAL = {
    "src/server.ts": "af4cd5c3886f119f35efa4fc0e28bd2ecfc48530",
    "src/config.ts": "1444c64ab66282e72411585392e3d242773a971a",
    "src/adapters/chatgpt-web/index.ts": "c7e7f291ae6ea6d23818aba8803ad83e39171dbd",
    "src/adapters/chatgpt-web/browser-worker.ts": "4e82981a28158e65705f31213bfbd123a6be5e2e",
    "src/adapters/chatgpt-web/turn-broker.ts": "6017bbaafd87c58078a72dbac42e843d5bcf3209",
    "src/adapters/chatgpt-web/mcp-server.ts": "51d9c787f93c391fba70f68ce759c673d789275d",
    "launcher/electron/runtime-supervisor.cjs": "19b19e24b4ab02ae02f762006f750ca9054d7bc6",
    "launcher/electron/main.cjs": "c3f83aacac26baaa28119ff1b147fbb355c4cac9",
    "launcher/electron/profile.cjs": "b1a20dc7fcfffc0ab45bfe916d173a59d4b93e5a",
    "launcher/electron/logging.cjs": "c4149c3c8a27a9b8105d23f58655d9bdc5df9d70",
}
RUNTIME_FILES = ("app/cli.js", "app/browser-helper.cjs", "app/package.json", "app/bun.lock")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return p.stdout.strip()


def load_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return raw


def run(a: argparse.Namespace) -> dict[str, Any]:
    source = Path(a.source_repo).resolve()
    portable = Path(a.portable_root).resolve()
    core_home = Path(a.bridge_home).resolve()
    launcher_data = Path(a.launcher_data).resolve()

    packaged_runtime = portable / "resources" / "runtime"
    live_runtime = core_home / "versions" / "4.0.7-win32-x64"
    packaged_manifest_path = packaged_runtime / "manifest.json"
    live_manifest_path = live_runtime / "manifest.json"

    if not packaged_manifest_path.is_file():
        raise RuntimeError(f"PACKAGED_RUNTIME_MANIFEST_MISSING:{packaged_manifest_path}")
    if not live_manifest_path.is_file():
        raise RuntimeError(f"LIVE_RUNTIME_MANIFEST_MISSING:{live_manifest_path}")

    packaged_manifest = load_json(packaged_manifest_path)
    live_manifest = load_json(live_manifest_path)

    runtime_files: dict[str, Any] = {}
    runtime_files_equal = True
    for rel in RUNTIME_FILES:
        pp = packaged_runtime / Path(rel)
        lp = live_runtime / Path(rel)
        psha = sha256_file(pp) if pp.is_file() else None
        lsha = sha256_file(lp) if lp.is_file() else None
        equal = psha is not None and psha == lsha
        runtime_files[rel] = {
            "packaged_exists": pp.is_file(),
            "live_exists": lp.is_file(),
            "packaged_sha256": psha,
            "live_sha256": lsha,
            "equal": equal,
        }
        runtime_files_equal = runtime_files_equal and equal

    tag_commit = git(source, "rev-list", "-n", "1", "v4.0.7")
    source_head = git(source, "rev-parse", "HEAD")
    dirty_entries = [x for x in git(source, "status", "--porcelain=v1").splitlines() if x.strip()]

    critical: dict[str, Any] = {}
    critical_equal = True
    drifted: list[str] = []
    for rel, expected_blob in CRITICAL.items():
        p = source / Path(rel)
        if p.is_file():
            actual_blob = git(source, "hash-object", str(p))
        else:
            actual_blob = None
        equal = actual_blob == expected_blob
        critical[rel] = {
            "exists": p.is_file(),
            "expected_blob": expected_blob,
            "actual_blob": actual_blob,
            "equal": equal,
        }
        critical_equal = critical_equal and equal
        if not equal:
            drifted.append(rel)

    config_path = core_home / "config.json"
    supervisor_path = core_home / "runtime" / "launcher-supervisor.json"
    descriptor_path = core_home / "runtime" / "launcher-browser.json"
    diagnostics_root = core_home / "diagnostics" / "browser-turns"
    launcher_log = launcher_data / "logs" / "launcher.jsonl"

    config = load_json(config_path) if config_path.is_file() else {}
    supervisor = load_json(supervisor_path) if supervisor_path.is_file() else {}
    daemon_pid = supervisor.get("daemonPid")

    log_bound = False
    if launcher_log.is_file() and isinstance(daemon_pid, int):
        needle = f'"daemonPid":{daemon_pid}'
        needle_spaced = f'"daemonPid": {daemon_pid}'
        with launcher_log.open("r", encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                if needle in line or needle_spaced in line:
                    log_bound = True
                    break

    manifest_identity_equal = (
        packaged_manifest.get("bundleId") == live_manifest.get("bundleId")
        and packaged_manifest.get("appVersion") == live_manifest.get("appVersion") == "4.0.7"
        and packaged_manifest.get("platform") == live_manifest.get("platform") == "win32"
        and packaged_manifest.get("arch") == live_manifest.get("arch") == "x64"
    )

    sink_binding = {
        "config_exists": config_path.is_file(),
        "config_mode_full": config.get("mode") == "full",
        "supervisor_exists": supervisor_path.is_file(),
        "supervisor_ready": supervisor.get("status") == "ready",
        "browser_descriptor_exists": descriptor_path.is_file(),
        "launcher_log_exists": launcher_log.is_file(),
        "launcher_log_bound_to_daemon_pid": log_bound,
        "diagnostics_root": str(diagnostics_root),
        "diagnostics_root_derived_from_same_core_home": diagnostics_root.parent.parent == core_home,
        "descriptor_under_same_core_home": descriptor_path.parent.parent == core_home,
    }
    sink_pass = all(v is True for k, v in sink_binding.items() if k not in {"diagnostics_root"})

    verdict = "BLOCKED"
    if not critical_equal:
        verdict = "BLOCKED_CUSTOM_CRITICAL_SOURCE_DRIFT"
    elif (
        tag_commit == UPSTREAM_TAG_COMMIT
        and manifest_identity_equal
        and runtime_files_equal
        and sink_pass
    ):
        verdict = "PASS_SINK_CONTRACT_BOUND"

    return {
        "schema": "G2E-P5A-CGW-FX001-RP-I4-v1",
        "zero_science": True,
        "source": {
            "repo": str(source),
            "head": source_head,
            "dirty": bool(dirty_entries),
            "dirty_entry_count": len(dirty_entries),
            "v4_0_7_tag_commit": tag_commit,
            "tag_matches_reviewed_commit": tag_commit == UPSTREAM_TAG_COMMIT,
        },
        "package_to_live_runtime": {
            "packaged_runtime": str(packaged_runtime),
            "live_runtime": str(live_runtime),
            "packaged_bundle_id": packaged_manifest.get("bundleId"),
            "live_bundle_id": live_manifest.get("bundleId"),
            "manifest_identity_equal": manifest_identity_equal,
            "runtime_files": runtime_files,
            "runtime_files_equal": runtime_files_equal,
        },
        "critical_source": {
            "all_equal_reviewed_blobs": critical_equal,
            "drifted_paths": drifted,
            "files": critical,
        },
        "live_sink_binding": sink_binding,
        "inherited_reviewed_semantics": {
            "mode_full_implies_local_tools_enabled": critical_equal,
            "broker_register_precedes_browser_send": critical_equal,
            "browser_page_acquired_precedes_browser_send": critical_equal,
            "launcher_daemon_stdio_feeds_launcher_log": critical_equal and log_bound,
            "diagnostics_root_derives_from_core_home": sink_binding["diagnostics_root_derived_from_same_core_home"],
        },
        "science_firewall": {
            "responses_post": False,
            "model_execution": False,
            "browser_submission": False,
            "mcp_invocation": False,
            "scientific_attempt_created": False,
            "replacement_attempt_authorized": False,
        },
        "verdict": verdict,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source-repo", required=True)
    p.add_argument("--portable-root", required=True)
    p.add_argument("--bridge-home", required=True)
    p.add_argument("--launcher-data", required=True)
    p.add_argument("--output")
    a = p.parse_args()
    result = run(a)
    text = json.dumps(result, indent=2, sort_keys=False)
    print(text)
    if a.output:
        Path(a.output).write_text(text + "\n", encoding="utf-8", newline="\n")
    return 0 if result["verdict"] == "PASS_SINK_CONTRACT_BOUND" else 2


if __name__ == "__main__":
    raise SystemExit(main())
