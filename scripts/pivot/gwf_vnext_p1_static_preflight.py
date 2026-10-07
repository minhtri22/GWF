from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
P1_BASELINE = "e62032607af28603d776ea6d4a494fbc250ddd4b"
EXPECTED_MANIFEST_BLOB = "c05a94657863cc5ccb3b95273723fd0dda2ff519"
EXPECTED_PREREG_BLOB = "35059f072be1d2776d2e58cd97e07d69be04dbea"

REQUIRED_OBJECTS = {
    "GovernanceProfileRef",
    "GovernanceProfileDefinition",
    "GovernanceTransitionProposal",
    "AuthorityEnvelope",
    "AuthorityEnvelopeDelta",
    "BudgetEnvelope",
    "BudgetEnvelopeDelta",
    "ExecutionEnvironmentRef",
    "ExecutorBinding",
    "WorkAssignment",
    "HumanActionRequest",
}
FORBIDDEN_CHANGED_PREFIXES = ("domains/", "g2e/", "web/")
FORBIDDEN_PROVIDER_IMPORT_TOKENS = ("codex", "remotemcp", "chatgpt", "g2e")


def fail(code: str, message: str):
    print(json.dumps({"status": "FAIL", "code": code, "message": message}, sort_keys=True))
    raise SystemExit(1)


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def git_blob(path: Path) -> str:
    return run("git", "hash-object", str(path.relative_to(ROOT)))


def main() -> int:
    manifest_path = ROOT / "docs/pivot/GWF_VNEXT_P1_CONTRACT_MANIFEST_V1.yaml"
    prereg_path = ROOT / "docs/pivot/GWF_VNEXT_P1_GOVERNANCE_KERNEL_PREREGISTRATION_AND_CONTRACT_FREEZE.md"
    module_path = ROOT / "src/gwr/governance_vnext.py"
    migration_path = ROOT / "src/gwr/migrations.py"
    runtime_path = ROOT / "src/gwr/runtime.py"
    tests_path = ROOT / "tests/test_gwf_vnext_p1_governance_kernel.py"

    for path in (manifest_path, prereg_path, module_path, migration_path, runtime_path, tests_path):
        if not path.exists():
            fail("MISSING_REQUIRED_FILE", str(path.relative_to(ROOT)))

    if git_blob(manifest_path) != EXPECTED_MANIFEST_BLOB:
        fail("MANIFEST_BLOB_DRIFT", git_blob(manifest_path))
    if git_blob(prereg_path) != EXPECTED_PREREG_BLOB:
        fail("PREREG_BLOB_DRIFT", git_blob(prereg_path))

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    objects = set((manifest or {}).get("objects", {}).keys())
    missing = sorted(REQUIRED_OBJECTS - objects)
    if missing:
        fail("CONTRACT_OBJECT_MISSING", ",".join(missing))

    if (manifest or {}).get("implementation_lock", {}).get("allowed_in_P1") is None:
        fail("IMPLEMENTATION_LOCK_MISSING", "P1 implementation lock absent")

    migration_text = migration_path.read_text(encoding="utf-8")
    required_tables = {
        "governance_profile_definitions",
        "project_governance_profiles",
        "governance_transition_proposals",
        "authority_envelopes",
        "budget_envelopes",
        "budget_usage",
        "execution_environments",
        "work_assignments",
        "executor_bindings",
        "human_action_requests",
        "effective_governance_policies",
    }
    if "0012_vnext_p1_governance_kernel" not in migration_text:
        fail("MIGRATION_ID_MISSING", "0012_vnext_p1_governance_kernel")
    for table in sorted(required_tables):
        if f"CREATE TABLE IF NOT EXISTS {table}" not in migration_text:
            fail("MIGRATION_TABLE_MISSING", table)

    runtime_text = runtime_path.read_text(encoding="utf-8")
    if "VNextGovernanceService" not in runtime_text or "self.vnext_governance=" not in runtime_text:
        fail("RUNTIME_WIRING_MISSING", "VNextGovernanceService")

    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name.lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append((node.module or "").lower())
    for imported_name in imported:
        if any(token in imported_name for token in FORBIDDEN_PROVIDER_IMPORT_TOKENS):
            fail("PROVIDER_SPECIFIC_IMPORT", imported_name)

    tests_text = tests_path.read_text(encoding="utf-8")
    numbers = sorted(
        int(x)
        for x in re.findall(r"def test_p1_negative_(\d{2})_", tests_text)
    )
    if numbers != list(range(1, 17)):
        fail("NEGATIVE_TEST_SET_MISMATCH", repr(numbers))

    changed = run("git", "diff", "--name-only", P1_BASELINE, "HEAD").splitlines()
    forbidden = [p for p in changed if p.startswith(FORBIDDEN_CHANGED_PREFIXES)]
    if forbidden:
        fail("FORBIDDEN_SCOPE_CHANGE", ",".join(sorted(forbidden)))

    payload = {
        "status": "PASS",
        "gate": "GWF_VNEXT_P1_GOVERNANCE_KERNEL_IMPLEMENTATION_STATIC_PREFLIGHT",
        "baseline": P1_BASELINE,
        "head": run("git", "rev-parse", "HEAD"),
        "manifest_blob": EXPECTED_MANIFEST_BLOB,
        "prereg_blob": EXPECTED_PREREG_BLOB,
        "negative_tests_preregistered": 16,
        "forbidden_scope_changes": [],
        "changed_files": sorted(changed),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
