from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path


TAG = "rust-v0.153.4"
SOURCE_COMMIT = "3d2ee51ca2d5db578f328aa75e20aa22c0197c9a"

ASSETS = {
    "codex": {
        "url": "https://github.com/openai/codex/releases/download/rust-v0.153.4/codex-x86_64-pc-windows-msvc.exe.zip",
        "archive_name": "codex-x86_64-pc-windows-msvc.exe.zip",
        "archive_size": 104174469,
        "archive_sha256": "c016b0e6968b78586919c720d2685a03712f6d5f11bcd9d6f92c91eb8c41ba16",
        "binary_name": "codex-x86_64-pc-windows-msvc.exe",
        "binary_size": 295408944,
        "binary_sha256": "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b",
    },
    "helper": {
        "url": "https://github.com/openai/codex/releases/download/rust-v0.153.4/codex-windows-sandbox-setup-x86_64-pc-windows-msvc.exe.zip",
        "archive_name": "codex-windows-sandbox-setup-x86_64-pc-windows-msvc.exe.zip",
        "archive_size": 5562782,
        "archive_sha256": "256c4deb16946a01a52156e8fd619baec38743ff482741767ab5fdb4079e97cb",
        "binary_name": "codex-windows-sandbox-setup-x86_64-pc-windows-msvc.exe",
        "binary_size": 15413040,
        "binary_sha256": "0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4",
    },
}

MARKERS = (
    "interactive-provision",
    "full",
    "provision-only",
    "read-acls-only",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "G2E-D2S3-S3-I0/1.0"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        with destination.open("wb") as out:
            shutil.copyfileobj(response, out, length=1024 * 1024)


def marker_matrix(path: Path) -> dict[str, bool]:
    result = {marker: False for marker in MARKERS}
    with path.open("rb") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            for marker in MARKERS:
                result[marker] = mm.find(marker.encode("ascii")) >= 0
    return result


def locate_exact(root: Path, name: str) -> Path:
    matches = [p for p in root.rglob(name) if p.is_file()]
    if len(matches) != 1:
        raise RuntimeError(f"EXPECTED_EXACTLY_ONE_BINARY:{name}:{len(matches)}")
    return matches[0]


def audit_asset(role: str, spec: dict[str, object], root: Path) -> dict[str, object]:
    archive = root / str(spec["archive_name"])
    extract_dir = root / f"extract-{role}"
    extract_dir.mkdir(parents=True, exist_ok=True)

    download(str(spec["url"]), archive)

    archive_size = archive.stat().st_size
    archive_hash = sha256_file(archive)
    if archive_size != int(spec["archive_size"]):
        raise RuntimeError(
            f"{role.upper()}_ARCHIVE_SIZE_MISMATCH:{archive_size}:{spec['archive_size']}"
        )
    if archive_hash != str(spec["archive_sha256"]):
        raise RuntimeError(
            f"{role.upper()}_ARCHIVE_HASH_MISMATCH:{archive_hash}:{spec['archive_sha256']}"
        )

    with zipfile.ZipFile(archive, "r") as zf:
        zf.extractall(extract_dir)

    binary = locate_exact(extract_dir, str(spec["binary_name"]))
    binary_size = binary.stat().st_size
    binary_hash = sha256_file(binary)
    if binary_size != int(spec["binary_size"]):
        raise RuntimeError(
            f"{role.upper()}_BINARY_SIZE_MISMATCH:{binary_size}:{spec['binary_size']}"
        )
    if binary_hash != str(spec["binary_sha256"]):
        raise RuntimeError(
            f"{role.upper()}_BINARY_HASH_MISMATCH:{binary_hash}:{spec['binary_sha256']}"
        )

    return {
        "role": role,
        "archive": {
            "name": str(spec["archive_name"]),
            "size_bytes": archive_size,
            "sha256": archive_hash,
        },
        "binary": {
            "name": str(spec["binary_name"]),
            "size_bytes": binary_size,
            "sha256": binary_hash,
            "markers": marker_matrix(binary),
        },
    }


def adjudicate(codex: dict[str, object], helper: dict[str, object]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    codex_markers = codex["binary"]["markers"]
    helper_markers = helper["binary"]["markers"]

    if codex_markers["interactive-provision"]:
        reasons.append("CODEX_CONTAINS_INTERACTIVE_PROVISION")
    if helper_markers["interactive-provision"]:
        reasons.append("HELPER_CONTAINS_INTERACTIVE_PROVISION")

    for role, markers in (("CODEX", codex_markers), ("HELPER", helper_markers)):
        if not markers["full"]:
            reasons.append(f"{role}_MISSING_FULL")
        if not markers["provision-only"]:
            reasons.append(f"{role}_MISSING_PROVISION_ONLY")

    if not helper_markers["read-acls-only"]:
        reasons.append("HELPER_MISSING_READ_ACLS_ONLY")

    return (not reasons), reasons


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="g2e-d2s3-s3i0-") as td:
        root = Path(td)
        codex = audit_asset("codex", ASSETS["codex"], root)
        helper = audit_asset("helper", ASSETS["helper"], root)
        passed, reasons = adjudicate(codex, helper)

    report = {
        "schema": "G2E-P5A-D2S3-S3-I0-OFFICIAL-RELEASE-ASSET-AUDIT-v1",
        "release_tag": TAG,
        "source_commit": SOURCE_COMMIT,
        "codex": codex,
        "helper": helper,
        "source_tag_interactive_provision_occurrences": 0,
        "executables_invoked": False,
        "model_turn_executed": False,
        "scientific_attempt_authorized": False,
        "scientific_attempt_consumed": False,
        "pass": passed,
        "reasons": reasons,
        "adjudication": (
            "OFFICIAL_RELEASE_COHERENT_LOCAL_STAGING_REQUIRED"
            if passed
            else "OFFICIAL_RELEASE_PROVENANCE_INCOHERENT"
        ),
    }

    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 20


if __name__ == "__main__":
    raise SystemExit(main())
