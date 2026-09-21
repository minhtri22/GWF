from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from gwr.document_validation import MARKDOWNLINT_CLI2_VERSION, MarkdownlintCli2Adapter


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "markdownlint.p0.yaml"
SECRET_SENTINEL = "TOP-SECRET-P0-CONTEXT"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name: str, passed: bool, **details):
    return {"name": name, "pass": bool(passed), **details}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "evidence" / "dg-p0" / "DG_P0_GATE.json"))
    args = ap.parse_args()

    runtime_root = ROOT / ".gwr" / "dg-p0"
    runtime_root.mkdir(parents=True, exist_ok=True)
    adapter = MarkdownlintCli2Adapter(CONFIG)

    with tempfile.TemporaryDirectory(prefix="gate-", dir=runtime_root) as td:
        td_path = Path(td)
        valid_path = td_path / "valid.md"
        invalid_path = td_path / "invalid.md"
        valid_path.write_text("# Valid\n\nBody.\n", encoding="utf-8")
        invalid_path.write_text(SECRET_SENTINEL, encoding="utf-8")

        valid_before = sha256_file(valid_path)
        invalid_before = sha256_file(invalid_path)
        valid = adapter.validate(valid_path)
        invalid = adapter.validate(invalid_path)
        invalid_repeat = adapter.validate(invalid_path)
        valid_after = sha256_file(valid_path)
        invalid_after = sha256_file(invalid_path)

        unavailable = MarkdownlintCli2Adapter(
            CONFIG,
            command_prefix=("gwr-dg-p0-validator-that-does-not-exist",),
        ).validate(valid_path)

        invalid_payload = invalid.to_dict()
        checks = [
            check(
                "real_markdownlint_version",
                valid.observed_validator_version == MARKDOWNLINT_CLI2_VERSION
                and invalid.observed_validator_version == MARKDOWNLINT_CLI2_VERSION,
                expected=MARKDOWNLINT_CLI2_VERSION,
                observed=valid.observed_validator_version,
            ),
            check(
                "config_hash_recorded",
                valid.config_sha256 == sha256_file(CONFIG)
                and invalid.config_sha256 == sha256_file(CONFIG),
                config_sha256=sha256_file(CONFIG),
            ),
            check(
                "valid_fixture_pass",
                valid.execution_status == "SUCCEEDED"
                and valid.content_status == "PASS"
                and valid.finding_count == 0,
            ),
            check(
                "invalid_fixture_findings",
                invalid.execution_status == "SUCCEEDED"
                and invalid.content_status == "FINDINGS"
                and {x.rule_id for x in invalid.findings}.issuperset({"MD041", "MD047"}),
                rules=sorted({x.rule_id for x in invalid.findings}),
            ),
            check(
                "deterministic_normalization",
                invalid.to_dict() == invalid_repeat.to_dict(),
            ),
            check(
                "source_not_mutated",
                valid_before == valid_after and invalid_before == invalid_after,
            ),
            check(
                "unavailable_not_document_failure",
                unavailable.execution_status == "UNAVAILABLE"
                and unavailable.content_status == "NOT_EVALUATED"
                and unavailable.error_code == "EXECUTABLE_NOT_FOUND",
            ),
            check(
                "secret_context_not_persisted",
                SECRET_SENTINEL not in json.dumps(invalid_payload, sort_keys=True),
            ),
        ]

        errors = [x for x in checks if not x["pass"]]
        result = {
            "schema": "DG-P0-GATE-v1",
            "status": "PASS" if not errors else "FAIL",
            "validator": {
                "id": adapter.validator_id,
                "expected_version": MARKDOWNLINT_CLI2_VERSION,
                "observed_version": valid.observed_validator_version,
                "config_path": str(CONFIG.relative_to(ROOT)),
                "config_sha256": sha256_file(CONFIG),
            },
            "checks": checks,
            "valid_execution": valid.to_dict(),
            "invalid_execution": invalid_payload,
            "unavailable_execution": unavailable.to_dict(),
            "errors": errors,
        }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
