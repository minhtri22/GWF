from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_FREEZE_HEAD = "c5fe6efed005bad069f155c5f84cb56dcc0b2039"

P5_CONTRACT_BLOBS = {
    "docs/pivot/GWF_VNEXT_P5_CHATGPT_WEB_REMOTEMCP_EXECUTION_ENVIRONMENT_MANIFEST_V1.json": "2e4587cb501d3f98e29bb79be35e48f8f8bd1a36",
    "docs/pivot/GWF_VNEXT_P5_CHATGPT_WEB_REMOTEMCP_EXECUTION_ENVIRONMENT_PREREGISTRATION_AND_CONTRACT_FREEZE.md": "10d8126d56d9ccd9cd68acc310e00619d62a27b2",
    "docs/pivot/GWF_VNEXT_P5_QA_AND_FORMAL_DECISION.md": "24d755a080b4b11b968d7a2e5d90c9762453081d",
}
EXECUTION_LOCK_BLOBS = {
    "docs/pivot/GWF_VNEXT_P1_EXECUTION_LOCK.json": "ecfc8435f0f381d0a2edfac8575cbbc09a87abe3",
    "docs/pivot/GWF_VNEXT_P2_EXECUTION_LOCK.json": "25660c52526923d557224ac9fbc9abeae23adcc4",
    "docs/pivot/GWF_VNEXT_P3_EXECUTION_LOCK.json": "60aa70e8f03a2c4f11e5693bf58cf82b5806b24e",
    "docs/pivot/GWF_VNEXT_P4_EXECUTION_LOCK.json": "da96b599137835592d0ceb390ffe0162d6bcee33",
}
P1_LOCKED_BLOBS = {
    "src/gwr/governance_vnext.py": "3ed843327b1219d48e9348d76ab449caef19b6ed",
    "src/gwr/migrations.py": "edac944c7d3e4ce0121811ab72cb758436f96bee",
    "src/gwr/runtime.py": "b01cceafe38ddf8feb9acafac53fefa2038ebabe",
    "src/gwr/__init__.py": "f7ff73b34f59e0f2dd1ec9080069029966a11587",
    "tests/test_gwf_vnext_p1_governance_kernel.py": "452aa277f36ecb784e04077006b2a8934afe3ae3",
    "scripts/pivot/gwf_vnext_p1_static_preflight.py": "310d3e5883c06f840ebb311f6e772e81bf49e1d6",
    ".github/workflows/gwf-vnext-p1-governance-kernel.yml": "cfc4b6d8f152e0ea0592a939cfe5deb7170bd8ad",
}
P2_LOCKED_BLOBS = {
    "domains/research.governance_profiles.v1.json": "7ca53b894c8be051e7375e036d43c6c7b6499326",
    "domains/software.governance_profiles.v1.json": "9b8a18eed9d45343a32a733efd9b400f022285f8",
    "src/gwr/domain_governance_vnext.py": "d83ec96de7c572401f44d23f8a7e9dd3a05b4f60",
    "tests/test_gwf_vnext_p2_domain_governance_profiles.py": "0f0f31d6c0d59067f31997333c00dea8de9f8578",
    "scripts/pivot/gwf_vnext_p2_static_preflight.py": "bcafb2e0589290b012268623b595c85f183435ff",
    ".github/workflows/gwf-vnext-p2-domain-governance-profiles.yml": "c9a1df7b9b4a6ecf808d00497a6f9abf3f81cffe",
}
P3_LOCKED_BLOBS = {
    "src/gwr/g2e_bridge_vnext.py": "a6943efa64002bbcac1332f9ef87cf47275842d4",
    "tests/test_gwf_vnext_p3_g2e_reconciliation.py": "1831241912cfd943be577ab38c416f71b724111e",
    "scripts/pivot/gwf_vnext_p3_static_preflight.py": "78dfaad8762904ec30063a375fe4d82fa1a9e08e",
    ".github/workflows/gwf-vnext-p3-g2e-reconciliation.yml": "69618c1e25e8cd1d96bac228e53acda54ab58afb",
}
P4_LOCKED_BLOBS = {
    "src/gwr/pm_workassignment_vnext.py": "502e6c6b9d4b17a80b75dcff9bd6755349152021",
    "tests/test_gwf_vnext_p4_pm_workassignment_protocol.py": "ce63a3858700ebc472bb71982177d04122344f70",
    "scripts/pivot/gwf_vnext_p4_static_preflight.py": "a43c49ac42f72d6d86dc7cf8887b51222bc2c19e",
    ".github/workflows/gwf-vnext-p4-pm-workassignment-protocol.yml": "47a5a9ae8ff4527441fd311047eb664fcb2dbfc3",
}

MODULE = ROOT / "src/gwr/remotemcp_execution_vnext.py"
TESTS = ROOT / "tests/test_gwf_vnext_p5_remotemcp_execution_environment.py"
MANIFEST = ROOT / "docs/pivot/GWF_VNEXT_P5_CHATGPT_WEB_REMOTEMCP_EXECUTION_ENVIRONMENT_MANIFEST_V1.json"

ALLOWED_IMPLEMENTATION_FILES = {
    "src/gwr/remotemcp_execution_vnext.py",
    "tests/test_gwf_vnext_p5_remotemcp_execution_environment.py",
    "scripts/pivot/gwf_vnext_p5_static_preflight.py",
    ".github/workflows/gwf-vnext-p5-remotemcp-execution-environment.yml",
}
FORBIDDEN_RUNTIME_IMPORT_ROOTS = {
    "subprocess",
    "socket",
    "requests",
    "httpx",
    "urllib",
    "aiohttp",
}


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def blob_sha(path: str) -> str:
    return run("git", "hash-object", path)


def assert_blob_map(name: str, mapping: dict[str, str]) -> None:
    for path, expected in mapping.items():
        actual = blob_sha(path)
        if actual != expected:
            raise SystemExit(f"{name} blob drift: {path}: expected {expected}, got {actual}")


def changed_files() -> set[str]:
    raw = run("git", "diff", "--name-only", f"{CONTRACT_FREEZE_HEAD}..HEAD")
    return {line for line in raw.splitlines() if line}


def expected_test_name(symbol: str) -> str:
    match = re.fullmatch(r"N(\d{2})_(.+)", symbol)
    if not match:
        raise SystemExit(f"Malformed P5 negative-test symbol: {symbol}")
    return f"test_p5_negative_{match.group(1)}_{match.group(2).lower()}"


def check_test_matrix() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    symbols = manifest.get("negative_tests") or []
    if len(symbols) != 56:
        raise SystemExit(f"Expected exactly 56 manifest negative tests, found {len(symbols)}")
    tree = ast.parse(TESTS.read_text(encoding="utf-8"))
    actual = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and re.fullmatch(r"test_p5_negative_\d{2}_.+", node.name)
    }
    expected = {expected_test_name(symbol) for symbol in symbols}
    if actual != expected:
        raise SystemExit(
            "P5 negative-test function set differs from frozen manifest.\n"
            f"Missing: {sorted(expected - actual)}\n"
            f"Extra:   {sorted(actual - expected)}"
        )
    if manifest.get("schema_id") != "GWF-VNEXT-P5-CHATGPT-WEB-REMOTEMCP-EXECUTION-ENVIRONMENT-v1":
        raise SystemExit("Unexpected P5 manifest schema")
    if manifest.get("status") != "FROZEN":
        raise SystemExit("P5 manifest must remain FROZEN")
    if manifest.get("next_gate") != (
        "GWF_VNEXT_P5_CHATGPT_WEB_REMOTEMCP_EXECUTION_ENVIRONMENT_"
        "IMPLEMENTATION_STATIC_PREFLIGHT_AND_EXECUTION_LOCK"
    ):
        raise SystemExit("P5 next-gate identity drift")


def check_no_live_execution_path() -> None:
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in FORBIDDEN_RUNTIME_IMPORT_ROOTS:
                    raise SystemExit(f"P5 implementation imports live execution/network module: {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] in FORBIDDEN_RUNTIME_IMPORT_ROOTS:
                raise SystemExit(f"P5 implementation imports live execution/network module: {node.module}")
    forbidden_call_tokens = (
        "mcp__RemoteDesktop__",
        "device_pair_begin(",
        "device_restart(",
        "task_job_submit(",
        "project_register_on_device(",
        "project_bind_device(",
    )
    for token in forbidden_call_tokens:
        if token in source:
            raise SystemExit(f"P5 qualification core contains live RemoteMCP call token: {token}")


def check_scope() -> None:
    actual = changed_files()
    if actual != ALLOWED_IMPLEMENTATION_FILES:
        raise SystemExit(
            "P5 implementation diff scope mismatch.\n"
            f"Expected: {sorted(ALLOWED_IMPLEMENTATION_FILES)}\n"
            f"Actual:   {sorted(actual)}"
        )


def main() -> None:
    assert_blob_map("P5 contract", P5_CONTRACT_BLOBS)
    assert_blob_map("execution lock", EXECUTION_LOCK_BLOBS)
    assert_blob_map("P1", P1_LOCKED_BLOBS)
    assert_blob_map("P2", P2_LOCKED_BLOBS)
    assert_blob_map("P3", P3_LOCKED_BLOBS)
    assert_blob_map("P4", P4_LOCKED_BLOBS)
    check_scope()
    check_test_matrix()
    check_no_live_execution_path()
    run("git", "diff", "--check", f"{CONTRACT_FREEZE_HEAD}..HEAD")
    print("PASS: P5 static contract/hash/scope/56-test/zero-science preflight")


if __name__ == "__main__":
    main()
