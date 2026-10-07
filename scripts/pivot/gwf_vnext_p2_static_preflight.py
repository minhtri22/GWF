from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P2_CONTRACT_HEAD = "1f64ff9df32ddbfe1460025ac8ec2716cb884669"
P2_DEFINITIONS_BLOB = "fe83c0c638baee9912aa6b15f82bee1c19c2267a"
P2_PREREG_BLOB = "4009b9fe8cb9bb0d48b6dea15b7df528010c7bde"

P1_LOCKED_BLOBS = {
    "src/gwr/governance_vnext.py": "3ed843327b1219d48e9348d76ab449caef19b6ed",
    "src/gwr/migrations.py": "edac944c7d3e4ce0121811ab72cb758436f96bee",
    "src/gwr/runtime.py": "b01cceafe38ddf8feb9acafac53fefa2038ebabe",
    "src/gwr/__init__.py": "f7ff73b34f59e0f2dd1ec9080069029966a11587",
    "tests/test_gwf_vnext_p1_governance_kernel.py": "452aa277f36ecb784e04077006b2a8934afe3ae3",
    "scripts/pivot/gwf_vnext_p1_static_preflight.py": "310d3e5883c06f840ebb311f6e772e81bf49e1d6",
    ".github/workflows/gwf-vnext-p1-governance-kernel.yml": "cfc4b6d8f152e0ea0592a939cfe5deb7170bd8ad",
}

PACKAGE_FILES = {
    "research.full-cycle": ROOT / "domains/research.governance_profiles.v1.json",
    "software.delivery": ROOT / "domains/software.governance_profiles.v1.json",
}
DEFINITIONS = ROOT / "docs/pivot/GWF_VNEXT_P2_DOMAIN_GOVERNANCE_PROFILE_DEFINITIONS_V1.json"
PREREG = ROOT / "docs/pivot/GWF_VNEXT_P2_DOMAIN_GOVERNANCE_PROFILES_PREREGISTRATION_AND_CONTRACT_FREEZE.md"
SERVICE = ROOT / "src/gwr/domain_governance_vnext.py"
TESTS = ROOT / "tests/test_gwf_vnext_p2_domain_governance_profiles.py"

ALLOWED_POLICY_SECTIONS = {
    "authority_overlay",
    "budget_overlay",
    "autonomy_policy",
    "mutation_policy",
    "protected_resource_policy",
    "lineage_policy",
    "approval_policy",
    "retry_recovery_policy",
    "claim_permission_policy",
}


def fail(code: str, message: str) -> None:
    print(json.dumps({"status": "FAIL", "code": code, "message": message}, sort_keys=True))
    raise SystemExit(1)


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def git_blob(path: Path) -> str:
    return run("git", "hash-object", str(path.relative_to(ROOT)))


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_hash(value) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def main() -> int:
    required = [DEFINITIONS, PREREG, SERVICE, TESTS, *PACKAGE_FILES.values()]
    for path in required:
        if not path.exists():
            fail("MISSING_REQUIRED_FILE", str(path.relative_to(ROOT)))

    if git_blob(DEFINITIONS) != P2_DEFINITIONS_BLOB:
        fail("P2_DEFINITIONS_BLOB_DRIFT", git_blob(DEFINITIONS))
    if git_blob(PREREG) != P2_PREREG_BLOB:
        fail("P2_PREREG_BLOB_DRIFT", git_blob(PREREG))

    for rel, expected in P1_LOCKED_BLOBS.items():
        actual = git_blob(ROOT / rel)
        if actual != expected:
            fail("P1_EXECUTION_LOCK_INVALIDATED", f"{rel}:{actual}!={expected}")

    frozen = json.loads(DEFINITIONS.read_text(encoding="utf-8"))
    frozen_domains = frozen.get("domains") or {}
    if set(frozen_domains) != set(PACKAGE_FILES):
        fail("DOMAIN_SET_MISMATCH", repr(sorted(frozen_domains)))

    all_profiles: dict[str, tuple[str, dict]] = {}
    for domain_id, package_path in PACKAGE_FILES.items():
        package = json.loads(package_path.read_text(encoding="utf-8"))
        if package.get("schema_id") != "GWF-DOMAIN-GOVERNANCE-PROFILES-v1":
            fail("PACKAGE_SCHEMA_MISMATCH", domain_id)
        if package.get("domain_id") != domain_id:
            fail("PACKAGE_DOMAIN_MISMATCH", domain_id)
        if package.get("transition_topology") != "ACYCLIC_FORWARD_ONLY":
            fail("PACKAGE_TOPOLOGY_MISMATCH", domain_id)
        if package.get("frozen_source", {}).get("p2_definitions_blob") != P2_DEFINITIONS_BLOB:
            fail("PACKAGE_FROZEN_SOURCE_MISMATCH", domain_id)

        expected_domain = frozen_domains[domain_id]
        if package.get("profiles") != expected_domain.get("profiles"):
            fail("PACKAGE_PROFILE_PAYLOAD_DRIFT", domain_id)
        if package.get("profile_order") != expected_domain.get("profile_order"):
            fail("PACKAGE_PROFILE_ORDER_DRIFT", domain_id)

        for key, entry in package["profiles"].items():
            definition = entry["definition"]
            actual_hash = content_hash(definition)
            if actual_hash != entry["expected_profile_hash"]:
                fail("PROFILE_HASH_MISMATCH", f"{key}:{actual_hash}")
            unknown = sorted(set(definition.get("policy", {})) - ALLOWED_POLICY_SECTIONS)
            if unknown:
                fail("UNKNOWN_POLICY_SECTION", f"{key}:{unknown}")
            all_profiles[key] = (domain_id, entry)

    # Exact target resolution + strict forward DAG.
    for domain_id, package_path in PACKAGE_FILES.items():
        package = json.loads(package_path.read_text(encoding="utf-8"))
        order = package["profile_order"]
        index = {key: i for i, key in enumerate(order)}
        for key, entry in package["profiles"].items():
            for edge in entry["definition"].get("transition_edges") or []:
                ref = edge["target_profile_ref"]
                target = None
                for candidate_key, candidate in package["profiles"].items():
                    d = candidate["definition"]
                    if (
                        d["domain_id"] == ref["domain_id"]
                        and d["profile_id"] == ref["profile_id"]
                        and d["version"] == ref["profile_version"]
                        and candidate["expected_profile_hash"] == ref["profile_hash"]
                    ):
                        target = candidate_key
                        break
                if not target:
                    fail("UNRESOLVED_TRANSITION_TARGET", key)
                if index[target] <= index[key]:
                    fail("NON_FORWARD_TRANSITION", f"{key}->{target}")

    service_text = SERVICE.read_text(encoding="utf-8")
    tree = ast.parse(service_text, filename=str(SERVICE))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name.lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append((node.module or "").lower())
    for imported_name in imported:
        if any(token in imported_name for token in ("remotemcp", "codex", "chatgpt", "g2e")):
            fail("PROVIDER_OR_G2E_SPECIFIC_IMPORT", imported_name)

    lower_service = service_text.lower()
    for token in ("remotemcp", "codex", "chatgpt", "astra"):
        if token in lower_service:
            fail("PROVIDER_SPECIFIC_SEMANTIC", token)
    if re.search(r"(^|[^a-z0-9])sol([^a-z0-9]|$)", lower_service):
        fail("PROVIDER_SPECIFIC_SEMANTIC", "sol")

    test_text = TESTS.read_text(encoding="utf-8")
    numbers = sorted(int(x) for x in re.findall(r"def test_p2_negative_(\d{2})_", test_text))
    if numbers != list(range(1, 31)):
        fail("NEGATIVE_TEST_SET_MISMATCH", repr(numbers))

    changed = run("git", "diff", "--name-only", P2_CONTRACT_HEAD, "HEAD").splitlines()
    forbidden_exact = {
        "domains/research.workflow.yaml",
        "domains/software.workflow.yaml",
        "src/gwr/governance_vnext.py",
        "src/gwr/runtime.py",
        "src/gwr/migrations.py",
        "src/gwr/__init__.py",
    }
    forbidden_prefixes = ("g2e/", "web/")
    forbidden = [
        path for path in changed
        if path in forbidden_exact or path.startswith(forbidden_prefixes)
    ]
    if forbidden:
        fail("FORBIDDEN_SCOPE_CHANGE", ",".join(sorted(forbidden)))

    payload = {
        "status": "PASS",
        "gate": "GWF_VNEXT_P2_DOMAIN_GOVERNANCE_PROFILES_IMPLEMENTATION_STATIC_PREFLIGHT",
        "contract_head": P2_CONTRACT_HEAD,
        "head": run("git", "rev-parse", "HEAD"),
        "definitions_blob": P2_DEFINITIONS_BLOB,
        "prereg_blob": P2_PREREG_BLOB,
        "profile_count": len(all_profiles),
        "negative_tests_preregistered": 30,
        "p1_execution_lock_preserved": True,
        "forbidden_scope_changes": [],
        "changed_files": sorted(changed),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
