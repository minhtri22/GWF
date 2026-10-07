from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git_blob(path: str, commit: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"{commit}:{path}"], cwd=ROOT, text=True).strip()

def no_forbidden_runtime() -> tuple[bool, list[str]]:
    roots = [ROOT / "src", ROOT / "migrations"]
    needles = (
        "class DocumentRecord", "class DocumentRevision", "class DocumentFinding",
        "class DocumentQARecord", "CREATE TABLE document_records",
        "CREATE TABLE document_revisions", "CREATE TABLE document_findings",
        "CREATE TABLE document_qa_records", "class CatalogEntry",
        "CREATE TABLE catalog_entries",
    )
    hits = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".sql"}:
                continue
            body = path.read_text(encoding="utf-8", errors="replace")
            for needle in needles:
                if needle in body:
                    hits.append(f"{path.relative_to(ROOT)}::{needle}")
    return not hits, hits

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    p0 = read_json(ROOT / "evidence/dg-w1/p0.json")
    p1 = read_json(ROOT / "evidence/dg-w1/p1.json")
    p2 = read_json(ROOT / "evidence/dg-w1/p2.json")
    p3 = read_json(ROOT / "evidence/dg-w1/p3.json")

    p0_config = ROOT / "tools/document_validation/.markdownlint-cli2.jsonc"
    p1_ini = ROOT / "tools/document_validation/vale/.vale.ini"
    p1_terms = ROOT / "tools/document_validation/vale/styles/GWF/Terminology.yml"
    p2_config = ROOT / "tools/document_validation/lychee/lychee.toml"
    p1_tc = read_json(ROOT / "tools/document_validation/vale/toolchain.json")
    p2_tc = read_json(ROOT / "tools/document_validation/lychee/toolchain.json")
    runtime_clean, forbidden_hits = no_forbidden_runtime()

    fingerprints = {
        "p0": {
            "tool": "markdownlint-cli2", "version": p0["toolchain"]["version"],
            "toolchain_git_blob": git_blob("tools/document_validation/toolchain.json", args.commit),
            "config_git_blob": git_blob("tools/document_validation/.markdownlint-cli2.jsonc", args.commit),
            "config_sha256": sha256_file(p0_config),
        },
        "p1": {
            "tool": "vale", "version": p1["toolchain"]["version"],
            "toolchain_git_blob": git_blob("tools/document_validation/vale/toolchain.json", args.commit),
            "vale_ini_git_blob": git_blob("tools/document_validation/vale/.vale.ini", args.commit),
            "terminology_git_blob": git_blob("tools/document_validation/vale/styles/GWF/Terminology.yml", args.commit),
            "vale_ini_sha256": sha256_file(p1_ini),
            "terminology_sha256": sha256_file(p1_terms),
            "config_bundle_hash": p1_tc["config_bundle_hash"],
            "binary_sha256": p1.get("vale_binary_sha256"),
        },
        "p2": {
            "tool": "lychee", "version": p2["toolchain"]["version"],
            "upstream_commit": p2_tc["upstream_commit"],
            "release_asset_sha256": p2_tc["linux_asset_sha256"],
            "toolchain_git_blob": git_blob("tools/document_validation/lychee/toolchain.json", args.commit),
            "config_git_blob": git_blob("tools/document_validation/lychee/lychee.toml", args.commit),
            "config_sha256": sha256_file(p2_config),
            "binary_sha256": p2.get("lychee_binary_sha256"),
        },
        "p3": {
            "provider": "github", "repository_id": p3["repository_id"],
            "commit": p3["commit"], "path": p3["path"],
            "blob_sha": p3["blob_sha"], "content_sha256": p3["content_sha256"],
        },
    }

    checks = {
        "p0_real_gate_pass": p0.get("status") == "PASS",
        "p1_real_gate_pass": p1.get("status") == "PASS",
        "p2_real_gate_pass": p2.get("status") == "PASS",
        "p3_real_gate_pass": p3.get("status") == "PASS",
        "p0_version_exact": p0["toolchain"]["version"] == "0.23.3",
        "p1_version_exact": p1["toolchain"]["version"] == "3.22.0",
        "p2_version_exact": p2["toolchain"]["version"] == "0.24.2",
        "p1_config_identity_exact": (
            "sha256:" + sha256_file(p1_ini) == p1_tc["config_files"][".vale.ini"]
            and "sha256:" + sha256_file(p1_terms) == p1_tc["config_files"]["styles/GWF/Terminology.yml"]
        ),
        "p2_config_identity_exact": "sha256:" + sha256_file(p2_config) == p2_tc["config_sha256"],
        "p3_exact_head_bound": p3["commit"] == args.commit,
        "p3_repository_identity_bound": str(p3["repository_id"]) == "1374857546",
        "shared_validator_contract_present": all(
            token in (ROOT / "src/gwr/document_validation.py").read_text(encoding="utf-8")
            for token in ("class ValidatorFinding", "class ValidatorExecution", "class ValidatorAdapter")
        ),
        "no_authoritative_document_or_gac_runtime": runtime_clean,
        "finding_ledger_open_zero": "**OPEN = 0**" in (ROOT / "docs/Finding_checklist.md").read_text(encoding="utf-8"),
    }

    result = {
        "schema": "DG-W1-QA-v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "commit": args.commit,
        "component_status": {"DG-P0": p0.get("status"), "DG-P1": p1.get("status"), "DG-P2": p2.get("status"), "DG-P3": p3.get("status")},
        "fingerprints": fingerprints,
        "checks": checks,
        "forbidden_runtime_hits": forbidden_hits,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)

if __name__ == "__main__":
    main()
