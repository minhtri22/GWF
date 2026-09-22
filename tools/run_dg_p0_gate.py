from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from gwr.document_validation import MarkdownlintCli2Adapter


ROOT = Path(__file__).resolve().parents[1]
TOOLCHAIN = ROOT / "tools" / "document_validation" / "toolchain.json"
CONFIG = ROOT / "tools" / "document_validation" / ".markdownlint-cli2.jsonc"
VALID = ROOT / "tests" / "fixtures" / "document_validation" / "valid.md"
INVALID = ROOT / "tests" / "fixtures" / "document_validation" / "invalid.md"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--executable", default="markdownlint-cli2")
    ap.add_argument(
        "--out",
        default=str(ROOT / "evidence" / "dg-p0" / "DG_P0_GATE.json"),
    )
    args = ap.parse_args()

    toolchain = json.loads(TOOLCHAIN.read_text(encoding="utf-8"))
    expected_version = toolchain["version"]
    adapter = MarkdownlintCli2Adapter(
        executable=args.executable,
        expected_version=expected_version,
        config_path=CONFIG,
    )

    valid_before = VALID.read_bytes()
    invalid_before = INVALID.read_bytes()
    valid = adapter.validate(VALID)
    invalid = adapter.validate(INVALID)
    repeat = adapter.validate(VALID)

    checks = {
        "toolchain_version_pinned": expected_version == "0.23.3",
        "real_version_observed": valid.validator_version == expected_version,
        "config_hash_recorded": valid.config_hash == sha256_file(CONFIG),
        "valid_subject_hash_recorded": (
            valid.subject_hash == hashlib.sha256(valid_before).hexdigest()
        ),
        "invalid_subject_hash_recorded": (
            invalid.subject_hash == hashlib.sha256(invalid_before).hexdigest()
        ),
        "valid_fixture_pass": (
            valid.execution_status == "SUCCEEDED"
            and valid.content_status == "PASS"
            and not valid.findings
        ),
        "invalid_fixture_findings": (
            invalid.execution_status == "SUCCEEDED"
            and invalid.content_status == "FINDINGS"
            and any(f.rule_id.startswith("MD009") for f in invalid.findings)
        ),
        "repeat_normalizes_identically": valid.to_dict() == repeat.to_dict(),
        "source_not_mutated": (
            VALID.read_bytes() == valid_before
            and INVALID.read_bytes() == invalid_before
        ),
        "no_raw_context_persisted": all(
            "Context:" not in finding.message for finding in invalid.findings
        ),
    }

    status = "PASS" if all(checks.values()) else "FAIL"
    result = {
        "schema": "DG-P0-GATE-v1",
        "status": status,
        "toolchain": toolchain,
        "config_hash": sha256_file(CONFIG),
        "checks": checks,
        "valid_execution": valid.to_dict(),
        "invalid_execution": invalid.to_dict(),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    main()
