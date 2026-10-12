from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_BASE_HEAD = "4cd2e8b10bfbbad04ff820ce7818f7ef4bc83775"

P4_CONTRACT_BLOBS = {
    "docs/pivot/GWF_VNEXT_P4_PM_WORKASSIGNMENT_PROTOCOL_MANIFEST_V1.json": "2439db2b21d75075eb52ff366a36d88eb77fa5ea",
    "docs/pivot/GWF_VNEXT_P4_PM_WORKASSIGNMENT_PROTOCOL_PREREGISTRATION_AND_CONTRACT_FREEZE.md": "e9a8e67b02b40dabce1e5cfebd02b9f843cd86b5",
    "docs/pivot/GWF_VNEXT_P4_QA_AND_FORMAL_DECISION.md": "5c43b60fea73bad7f5c06c37071c5372a20c4fda",
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
LOCK_ARTIFACT_BLOBS = {
    "docs/pivot/GWF_VNEXT_P1_EXECUTION_LOCK.json": "ecfc8435f0f381d0a2edfac8575cbbc09a87abe3",
    "docs/pivot/GWF_VNEXT_P2_EXECUTION_LOCK.json": "25660c52526923d557224ac9fbc9abeae23adcc4",
    "docs/pivot/GWF_VNEXT_P3_EXECUTION_LOCK.json": "60aa70e8f03a2c4f11e5693bf58cf82b5806b24e",
}

MODULE = ROOT / "src/gwr/pm_workassignment_vnext.py"
TESTS = ROOT / "tests/test_gwf_vnext_p4_pm_workassignment_protocol.py"
MANIFEST = ROOT / "docs/pivot/GWF_VNEXT_P4_PM_WORKASSIGNMENT_PROTOCOL_MANIFEST_V1.json"

ALLOWED_IMPLEMENTATION_FILES = {
    "src/gwr/pm_workassignment_vnext.py",
    "tests/test_gwf_vnext_p4_pm_workassignment_protocol.py",
    "scripts/pivot/gwf_vnext_p4_static_preflight.py",
    ".github/workflows/gwf-vnext-p4-pm-workassignment-protocol.yml",
}

FORBIDDEN_PROVIDER_TOKENS = {
    "remotemcp",
    "codex",
    "chatgpt",
    "openai",
    "anthropic",
    "gemini",
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
    raw = run("git", "diff", "--name-only", f"{CONTRACT_BASE_HEAD}..HEAD")
    return {line for line in raw.splitlines() if line}


def check_test_matrix() -> None:
    tree = ast.parse(TESTS.read_text(encoding="utf-8"))
    negative = sorted(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and re.fullmatch(r"test_p4_negative_\d{2}_.+", node.name)
    )
    if len(negative) != 36:
        raise SystemExit(f"Expected exactly 36 P4 negative tests, found {len(negative)}")
    ordinals = [int(re.search(r"negative_(\d{2})_", name).group(1)) for name in negative]
    if ordinals != list(range(1, 37)):
        raise SystemExit(f"P4 negative-test ordinals are not exactly 01..36: {ordinals}")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("schema_id") != "GWF-VNEXT-P4-PM-WORKASSIGNMENT-PROTOCOL-v1":
        raise SystemExit("Unexpected P4 manifest schema")
    if manifest.get("status") != "FROZEN":
        raise SystemExit("P4 manifest must remain FROZEN")
    if len(manifest.get("negative_tests") or []) != 36:
        raise SystemExit("P4 manifest must freeze exactly 36 negative tests")
    if manifest.get("next_gate") != "GWF_VNEXT_P4_PM_WORKASSIGNMENT_PROTOCOL_IMPLEMENTATION_STATIC_PREFLIGHT_AND_EXECUTION_LOCK":
        raise SystemExit("P4 next-gate identity drift")


def check_provider_neutrality() -> None:
    source = MODULE.read_text(encoding="utf-8")
    lowered = source.lower()
    hit = sorted(token for token in FORBIDDEN_PROVIDER_TOKENS if token in lowered)
    if hit:
        raise SystemExit(f"Provider-specific token(s) in P4 core implementation: {hit}")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "WorkAssignment":
            raise SystemExit("P4 may not redefine P1 WorkAssignment")


def check_scope() -> None:
    changed = changed_files()
    if changed != ALLOWED_IMPLEMENTATION_FILES:
        raise SystemExit(
            "P4 implementation diff scope mismatch.\n"
            f"Expected: {sorted(ALLOWED_IMPLEMENTATION_FILES)}\n"
            f"Actual:   {sorted(changed)}"
        )


def main() -> None:
    assert_blob_map("P4 contract", P4_CONTRACT_BLOBS)
    assert_blob_map("P1 lock", P1_LOCKED_BLOBS)
    assert_blob_map("P2 lock", P2_LOCKED_BLOBS)
    assert_blob_map("P3 lock", P3_LOCKED_BLOBS)
    assert_blob_map("execution-lock artifact", LOCK_ARTIFACT_BLOBS)
    check_scope()
    check_test_matrix()
    check_provider_neutrality()
    run("git", "diff", "--check", f"{CONTRACT_BASE_HEAD}..HEAD")
    print("PASS: P4 static contract/hash/scope/test-matrix/provider-neutrality preflight")


if __name__ == "__main__":
    main()
