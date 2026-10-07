from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

P3_CONTRACT_HEAD = "03999e8a76da532c9e8cb65344858b149ad59a8b"
P3_MANIFEST_BLOB = "57917853b838bc1b62da46e7336baa0bcd11bf11"
P3_PREREG_BLOB = "20be52b0239b81966dc09935220515c5ae1ae1a7"
P3_QA_BLOB = "07d90ee156137703c6f236a610c8d9272fe69160"

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

P1_LOCK_ARTIFACT = ("docs/pivot/GWF_VNEXT_P1_EXECUTION_LOCK.json", "ecfc8435f0f381d0a2edfac8575cbbc09a87abe3")
P2_LOCK_ARTIFACT = ("docs/pivot/GWF_VNEXT_P2_EXECUTION_LOCK.json", "25660c52526923d557224ac9fbc9abeae23adcc4")

MANIFEST = ROOT / "docs/pivot/GWF_VNEXT_P3_G2E_RECONCILIATION_MANIFEST_V1.json"
PREREG = ROOT / "docs/pivot/GWF_VNEXT_P3_G2E_SEMANTIC_RUNTIME_RECONCILIATION_PREREGISTRATION_AND_CONTRACT_FREEZE.md"
QA = ROOT / "docs/pivot/GWF_VNEXT_P3_QA_AND_FORMAL_DECISION.md"
BRIDGE = ROOT / "src/gwr/g2e_bridge_vnext.py"
TESTS = ROOT / "tests/test_gwf_vnext_p3_g2e_reconciliation.py"

ALLOWED_IMPLEMENTATION_FILES = {
    "src/gwr/g2e_bridge_vnext.py",
    "tests/test_gwf_vnext_p3_g2e_reconciliation.py",
    "scripts/pivot/gwf_vnext_p3_static_preflight.py",
    ".github/workflows/gwf-vnext-p3-g2e-reconciliation.yml",
    "docs/pivot/GWF_VNEXT_P3_EXECUTION_LOCK.json",
    "docs/pivot/P3_G2E_RECONCILIATION_IMPLEMENTATION_LOCK_CLOSURE.md",
    "docs/pivot/GWF_AUTONOMOUS_RESEARCH_STACK_VNEXT_PLAN.md",
}


def fail(code: str, message: str) -> None:
    print(json.dumps({"status": "FAIL", "code": code, "message": message}, sort_keys=True))
    raise SystemExit(1)


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def git_blob(path: Path) -> str:
    return run("git", "hash-object", str(path.relative_to(ROOT)))


def require_blob(path: Path, expected: str, code: str) -> None:
    if not path.exists():
        fail(code, f"missing:{path.relative_to(ROOT)}")
    actual = git_blob(path)
    if actual != expected:
        fail(code, f"{path.relative_to(ROOT)}:{actual}!={expected}")


def main() -> int:
    require_blob(MANIFEST, P3_MANIFEST_BLOB, "P3_MANIFEST_DRIFT")
    require_blob(PREREG, P3_PREREG_BLOB, "P3_PREREG_DRIFT")
    require_blob(QA, P3_QA_BLOB, "P3_QA_DRIFT")

    for rel, expected in P1_LOCKED_BLOBS.items():
        require_blob(ROOT / rel, expected, "P1_EXECUTION_LOCK_INVALIDATED")
    for rel, expected in P2_LOCKED_BLOBS.items():
        require_blob(ROOT / rel, expected, "P2_EXECUTION_LOCK_INVALIDATED")
    require_blob(ROOT / P1_LOCK_ARTIFACT[0], P1_LOCK_ARTIFACT[1], "P1_LOCK_ARTIFACT_DRIFT")
    require_blob(ROOT / P2_LOCK_ARTIFACT[0], P2_LOCK_ARTIFACT[1], "P2_LOCK_ARTIFACT_DRIFT")

    if not BRIDGE.exists() or not TESTS.exists():
        fail("P3_IMPLEMENTATION_MISSING", "bridge or qualification tests missing")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("schema_id") != "GWF-VNEXT-P3-G2E-SEMANTIC-RUNTIME-RECONCILIATION-v1":
        fail("P3_SCHEMA_ID_MISMATCH", str(manifest.get("schema_id")))
    if manifest.get("g2e_baseline", {}).get("canonical_provider_neutral_qualified_commit") != "6e9c518671c3f9ba140daa798458b37bee83647c":
        fail("P3_G2E_BASELINE_MISMATCH", "canonical provider-neutral baseline changed")
    if manifest.get("classification", {}).get("total_files") != 585:
        fail("P3_CLASSIFICATION_COUNT_MISMATCH", str(manifest.get("classification", {}).get("total_files")))
    if manifest.get("classification", {}).get("unclassified_count") != 0:
        fail("P3_UNCLASSIFIED_FILES", str(manifest.get("classification", {}).get("unclassified_count")))
    if len(manifest.get("p3_implementation_preregistered_negative_tests") or []) != 40:
        fail("P3_FROZEN_NEGATIVE_TEST_COUNT_MISMATCH", "manifest must freeze exactly 40 negative tests")

    test_text = TESTS.read_text(encoding="utf-8")
    numbers = sorted(int(x) for x in re.findall(r"def test_p3_negative_(\d{2})_", test_text))
    if numbers != list(range(1, 41)):
        fail("P3_IMPLEMENTED_NEGATIVE_TEST_SET_MISMATCH", repr(numbers))

    bridge_text = BRIDGE.read_text(encoding="utf-8")
    tree = ast.parse(bridge_text, filename=str(BRIDGE))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name.lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append((node.module or "").lower())
    if any(name == "g2e" or name.startswith("g2e.") for name in imported):
        fail("P3_G2E_RUNTIME_IMPORT_FORBIDDEN", repr(imported))

    lowered = bridge_text.lower()
    banned = ("codex", "chatgpt", "remotemcp", "claude", "gemini", "astra")
    for token in banned:
        if token in lowered:
            fail("P3_PROVIDER_SPECIFIC_SEMANTIC", token)
    if re.search(r"(^|[^a-z0-9_])sol([^a-z0-9_]|$)", lowered):
        fail("P3_PROVIDER_SPECIFIC_SEMANTIC", "sol")

    required_symbols = {
        "P3_G2E_MAPPING_VERSION",
        "G2EExactRef",
        "g2e_bridge_ref",
        "G2EGWFBridgeVNext",
        "validate_work_assignment_bridge",
        "validate_agent_executor_binding",
        "protected_resource_transition",
        "validate_candidate_evidence",
        "validate_adjudication_inputs",
        "validate_independence",
        "validate_checkpoint",
        "assert_source_import_allowed",
    }
    missing = [symbol for symbol in sorted(required_symbols) if symbol not in bridge_text]
    if missing:
        fail("P3_BRIDGE_SURFACE_INCOMPLETE", ",".join(missing))

    changed = [x for x in run("git", "diff", "--name-only", P3_CONTRACT_HEAD, "HEAD").splitlines() if x]
    forbidden = []
    for path in changed:
        if path.startswith(("src/g2e/", "g2e/", "web/")):
            forbidden.append(path)
            continue
        if path not in ALLOWED_IMPLEMENTATION_FILES:
            forbidden.append(path)
    if forbidden:
        fail("P3_FORBIDDEN_SCOPE_CHANGE", ",".join(sorted(forbidden)))

    payload = {
        "status": "PASS",
        "gate": "GWF_VNEXT_P3_G2E_SEMANTIC_RUNTIME_RECONCILIATION_IMPLEMENTATION_STATIC_PREFLIGHT",
        "contract_head": P3_CONTRACT_HEAD,
        "head": run("git", "rev-parse", "HEAD"),
        "manifest_blob": P3_MANIFEST_BLOB,
        "prereg_blob": P3_PREREG_BLOB,
        "qa_blob": P3_QA_BLOB,
        "negative_tests_preregistered": 40,
        "negative_tests_implemented": 40,
        "p1_execution_lock_preserved": True,
        "p2_execution_lock_preserved": True,
        "g2e_runtime_imported": False,
        "provider_specific_semantics": False,
        "forbidden_scope_changes": [],
        "changed_files": sorted(changed),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
