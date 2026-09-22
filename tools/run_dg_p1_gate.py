from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from gwr.document_validation import ValeAdapter


ROOT = Path(__file__).resolve().parents[1]
VALE_DIR = ROOT / "tools" / "document_validation" / "vale"
TOOLCHAIN = VALE_DIR / "toolchain.json"
CONFIG = VALE_DIR / ".vale.ini"
STYLES = VALE_DIR / "styles"
VALID = ROOT / "tests" / "fixtures" / "document_validation" / "vale_valid.md"
INVALID = ROOT / "tests" / "fixtures" / "document_validation" / "vale_invalid.md"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--executable", default="vale")
    ap.add_argument("--out", default=str(ROOT / "evidence" / "dg-p1" / "DG_P1_GATE.json"))
    args = ap.parse_args()

    toolchain = json.loads(TOOLCHAIN.read_text(encoding="utf-8"))
    resolved_executable = shutil.which(args.executable) or args.executable
    executable_path = Path(resolved_executable)
    adapter = ValeAdapter(
        executable=str(executable_path),
        expected_version=toolchain["version"],
        config_path=CONFIG,
        styles_path=STYLES,
    )

    valid_before = VALID.read_bytes()
    invalid_before = INVALID.read_bytes()
    valid = adapter.validate(VALID)
    invalid = adapter.validate(INVALID)
    repeat = adapter.validate(VALID)

    expected_config_hash = toolchain["config_bundle_hash"].removeprefix("sha256:")
    expected_ini_hash = toolchain["config_files"][".vale.ini"].removeprefix("sha256:")
    expected_terms_hash = toolchain["config_files"]["styles/GWF/Terminology.yml"].removeprefix("sha256:")

    checks = {
        "toolchain_version_pinned": toolchain["version"] == "3.22.0",
        "real_version_observed": valid.validator_version == toolchain["version"],
        "vale_ini_hash_matches": sha256_file(CONFIG) == expected_ini_hash,
        "terminology_rule_hash_matches": sha256_file(STYLES / "GWF" / "Terminology.yml") == expected_terms_hash,
        "config_bundle_hash_recorded": valid.config_hash == expected_config_hash,
        "valid_subject_hash_recorded": valid.subject_hash == hashlib.sha256(valid_before).hexdigest(),
        "invalid_subject_hash_recorded": invalid.subject_hash == hashlib.sha256(invalid_before).hexdigest(),
        "valid_fixture_pass": valid.execution_status == "SUCCEEDED" and valid.content_status == "PASS" and not valid.findings,
        "terminology_drift_detected": (
            invalid.execution_status == "SUCCEEDED"
            and invalid.content_status == "FINDINGS"
            and any(f.rule_id == "GWF.Terminology" and f.severity == "ERROR" and f.line == 3 for f in invalid.findings)
        ),
        "matched_source_redacted": all("ARC fallback layer" not in finding.message for finding in invalid.findings),
        "repeat_normalizes_identically": valid.to_dict() == repeat.to_dict(),
        "source_not_mutated": VALID.read_bytes() == valid_before and INVALID.read_bytes() == invalid_before,
    }

    status = "PASS" if all(checks.values()) else "FAIL"
    result = {
        "schema": "DG-P1-GATE-v1",
        "status": status,
        "toolchain": toolchain,
        "vale_binary_sha256": sha256_file(executable_path) if executable_path.is_file() else None,
        "checks": checks,
        "valid_execution": valid.to_dict(),
        "invalid_execution": invalid.to_dict(),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    main()
