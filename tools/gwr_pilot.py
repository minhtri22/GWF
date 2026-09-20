from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "pilot_id",
    "version",
    "domain_path",
    "target_repository",
    "default_branch",
    "mode",
    "baseline_policy",
    "governance",
    "github",
    "success_criteria",
}


def load_profile(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("pilot profile root must be an object")
    return data


def validate_profile(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    data = load_profile(p)
    errors: list[str] = []
    missing = sorted(REQUIRED - set(data))
    if missing:
        errors.append(f"missing fields: {missing}")

    domain_path = data.get("domain_path")
    resolved_domain = None
    if domain_path:
        resolved_domain = ROOT / str(domain_path)
        if not resolved_domain.exists():
            errors.append(f"domain_path does not exist: {domain_path}")

    repo = str(data.get("target_repository") or "")
    if repo.count("/") != 1 or any(not x for x in repo.split("/")):
        errors.append("target_repository must be owner/name")

    if data.get("baseline_policy") != "RESOLVE_AT_START":
        errors.append("baseline_policy must be RESOLVE_AT_START for live pilots")

    governance = data.get("governance") or {}
    if governance.get("recovery_mode") not in {"AUTO", "HUMAN_APPROVE"}:
        errors.append("governance.recovery_mode must be AUTO or HUMAN_APPROVE")

    github = data.get("github") or {}
    if github.get("write_policy") != "FEATURE_BRANCH_ONLY":
        errors.append("live pilot write_policy must be FEATURE_BRANCH_ONLY")
    if github.get("direct_main_write") is not False:
        errors.append("live pilot direct_main_write must be false")
    if github.get("expected_head_sha_policy") != "EXACT":
        errors.append("github.expected_head_sha_policy must be EXACT")
    if github.get("post_commit_verification") is not True:
        errors.append("github.post_commit_verification must be true")

    success = data.get("success_criteria")
    if not isinstance(success, list) or not success:
        errors.append("success_criteria must be a non-empty list")

    return {
        "ok": not errors,
        "path": str(p),
        "pilot_id": data.get("pilot_id"),
        "target_repository": data.get("target_repository"),
        "domain_path": data.get("domain_path"),
        "domain_resolved": str(resolved_domain) if resolved_domain else None,
        "mode": data.get("mode"),
        "errors": errors,
    }


def plan_profile(path: str | Path) -> dict[str, Any]:
    data = load_profile(path)
    check = validate_profile(path)
    if not check["ok"]:
        raise ValueError("; ".join(check["errors"]))
    return {
        "pilot_id": data["pilot_id"],
        "target_repository": data["target_repository"],
        "default_branch": data["default_branch"],
        "domain_path": data["domain_path"],
        "mode": data["mode"],
        "baseline": "Fetch remote default-branch HEAD at execution start and freeze exact SHA.",
        "recovery_mode": data["governance"]["recovery_mode"],
        "write_policy": data["github"]["write_policy"],
        "branch_prefix": data["github"].get("branch_prefix"),
        "direct_main_write": data["github"]["direct_main_write"],
        "success_criteria": data["success_criteria"],
        "note": "Profile validation does not perform repository mutations; execution remains governed by GWF runtime/plugin authority.",
    }


def main():
    ap = argparse.ArgumentParser(prog="gwr-pilot")
    sub = ap.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate")
    v.add_argument("path")

    p = sub.add_parser("plan")
    p.add_argument("path")

    args = ap.parse_args()
    if args.command == "validate":
        result = validate_profile(args.path)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["ok"] else 1)
    print(json.dumps(plan_profile(args.path), indent=2))


if __name__ == "__main__":
    main()
