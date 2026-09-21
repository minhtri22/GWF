from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCHEMA = "G2E-P5A-CODEX-D1-ADJUDICATION-v1"
DISCOVERY_SCHEMA = "G2E-P5A-CODEX-DISCOVERY-v1"
PASS_STATUS = "D1_MINIMUM_QUALIFIED"
FAIL_STATUSES = {
    "HARNESS_NOT_FOUND",
    "VERSION_UNRESOLVED",
    "SCHEMA_DISCOVERY_FAILED",
    "D1_MINIMUM_NOT_QUALIFIED",
}
REQUIRED_TOKENS = (
    "initialize",
    "thread/start",
    "thread/resume",
    "turn/start",
    "item/started",
    "item/completed",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SENSITIVE_KEYS = {
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "authorization",
    "password",
    "secret",
    "credential",
    "accountemail",
    "email",
}
ALLOWED_INITIALIZE_KEYS = {"success", "sanitized_response", "error"}
ALLOWED_SANITIZED_KEYS = {"response_id", "result_present", "metadata"}
ALLOWED_METADATA_KEYS = {"userAgent", "platformFamily", "platformOs"}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_inventory_digest(files: list[dict[str, Any]]) -> str:
    canonical = json.dumps(
        files,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return _sha256_bytes(canonical)


def _find_sensitive_keys(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if key_text.lower() in SENSITIVE_KEYS:
                hits.append(f"{path}.{key_text}")
            hits.extend(_find_sensitive_keys(item, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            hits.extend(_find_sensitive_keys(item, f"{path}[{index}]"))
    return hits


def _validate_inventory(value: Any) -> tuple[bool, list[str], str | None]:
    reasons: list[str] = []
    if not isinstance(value, list) or not value:
        return False, ["INVENTORY_MISSING_OR_EMPTY"], None

    paths: list[str] = []
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            reasons.append("INVENTORY_ITEM_NOT_OBJECT")
            continue
        if set(item) != {"path", "sha256", "size"}:
            reasons.append("INVENTORY_ITEM_FIELDS_INVALID")
            continue
        path = item.get("path")
        sha = item.get("sha256")
        size = item.get("size")
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in Path(path).parts:
            reasons.append("INVENTORY_PATH_INVALID")
        if not isinstance(sha, str) or not SHA256_RE.fullmatch(sha):
            reasons.append("INVENTORY_SHA256_INVALID")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            reasons.append("INVENTORY_SIZE_INVALID")
        if isinstance(path, str):
            paths.append(path)
        normalized.append(item)

    if paths != sorted(paths):
        reasons.append("INVENTORY_PATHS_NOT_SORTED")
    if len(paths) != len(set(paths)):
        reasons.append("INVENTORY_PATHS_DUPLICATE")

    digest = _canonical_inventory_digest(normalized) if not reasons else None
    return not reasons, reasons, digest


def adjudicate_data(data: Any, input_sha256: str, source_sha256: str) -> dict[str, Any]:
    verdict = "INVALID"
    reasons: list[str] = []

    base = {
        "schema": SCHEMA,
        "adjudicator_source_sha256": source_sha256,
        "discovery_input_sha256": input_sha256,
        "verdict": verdict,
        "reason_codes": reasons,
        "codex_profile_available_for_d1_surface": False,
        "d2_authorized": False,
        "runtime_adapter_authorized": False,
    }

    if not isinstance(data, dict):
        reasons.append("INPUT_NOT_OBJECT")
        return base

    base["observed_codex_version"] = data.get("codex_version_stdout")
    base["observed_executable_path"] = data.get("executable_path")
    base["observed_executable_sha256"] = data.get("executable_sha256")
    base["schema_inventory_digest"] = data.get("schema_inventory_digest")
    base["required_protocol_tokens"] = data.get("required_protocol_tokens")
    handshake = data.get("initialize_handshake")
    base["initialize_handshake_success"] = handshake.get("success") if isinstance(handshake, dict) else None

    if data.get("schema") != DISCOVERY_SCHEMA:
        reasons.append("DISCOVERY_SCHEMA_MISMATCH")

    if data.get("secrets_persisted") is not False:
        reasons.append("SECRETS_PERSISTED_NOT_FALSE")
    if data.get("functional_task_executed") is not False:
        reasons.append("FUNCTIONAL_TASK_EXECUTED_NOT_FALSE")

    sensitive_hits = _find_sensitive_keys(data)
    if sensitive_hits:
        reasons.append("FORBIDDEN_SENSITIVE_FIELD")
        base["sensitive_field_paths"] = sensitive_hits

    if isinstance(handshake, dict):
        if not set(handshake).issubset(ALLOWED_INITIALIZE_KEYS):
            reasons.append("INITIALIZE_FIELDS_UNSANITIZED")
        sanitized = handshake.get("sanitized_response")
        if sanitized is not None:
            if not isinstance(sanitized, dict):
                reasons.append("SANITIZED_RESPONSE_INVALID")
            else:
                if not set(sanitized).issubset(ALLOWED_SANITIZED_KEYS):
                    reasons.append("SANITIZED_RESPONSE_FIELDS_INVALID")
                metadata = sanitized.get("metadata")
                if metadata is not None:
                    if not isinstance(metadata, dict) or not set(metadata).issubset(ALLOWED_METADATA_KEYS):
                        reasons.append("SANITIZED_METADATA_FIELDS_INVALID")
    elif data.get("status") == PASS_STATUS:
        reasons.append("INITIALIZE_HANDSHAKE_MISSING")

    inventory_present = "generated_schema_files" in data
    if inventory_present:
        inventory_ok, inventory_reasons, recomputed = _validate_inventory(data.get("generated_schema_files"))
        reasons.extend(inventory_reasons)
        if inventory_ok:
            base["recomputed_schema_inventory_digest"] = recomputed
            if data.get("schema_inventory_digest") != recomputed:
                reasons.append("SCHEMA_INVENTORY_DIGEST_MISMATCH")

    status = data.get("status")
    if status not in FAIL_STATUSES | {PASS_STATUS}:
        reasons.append("DISCOVERY_STATUS_UNRECOGNIZED")

    if status == PASS_STATUS:
        pass_requirements: list[tuple[bool, str]] = [
            (isinstance(data.get("codex_version_stdout"), str) and bool(data.get("codex_version_stdout").strip()), "VERSION_MISSING"),
            (isinstance(data.get("executable_path"), str) and bool(data.get("executable_path").strip()), "EXECUTABLE_PATH_MISSING"),
            (data.get("app_server_help_exit_code") == 0, "APP_SERVER_HELP_FAILED"),
            (isinstance(data.get("app_server_help_sha256"), str) and bool(SHA256_RE.fullmatch(data.get("app_server_help_sha256", ""))), "APP_SERVER_HELP_HASH_INVALID"),
            (data.get("schema_generation_exit_code") == 0, "SCHEMA_GENERATION_FAILED"),
            (inventory_present, "INVENTORY_MISSING"),
            (isinstance(data.get("required_protocol_tokens"), dict), "REQUIRED_TOKEN_MAP_MISSING"),
            (isinstance(handshake, dict) and handshake.get("success") is True, "INITIALIZE_HANDSHAKE_FAILED"),
            (data.get("errors") == [], "DISCOVERY_ERRORS_NONEMPTY"),
        ]
        executable_sha = data.get("executable_sha256")
        executable_reason = data.get("executable_sha256_unavailable_reason")
        pass_requirements.append(
            (
                (isinstance(executable_sha, str) and bool(SHA256_RE.fullmatch(executable_sha)))
                or (isinstance(executable_reason, str) and bool(executable_reason.strip())),
                "EXECUTABLE_IDENTITY_UNRESOLVED",
            )
        )
        token_map = data.get("required_protocol_tokens")
        if isinstance(token_map, dict):
            for token in REQUIRED_TOKENS:
                pass_requirements.append((token_map.get(token) is True, f"REQUIRED_TOKEN_FALSE:{token}"))
            if set(token_map) != set(REQUIRED_TOKENS):
                pass_requirements.append((False, "REQUIRED_TOKEN_SET_MISMATCH"))
        for ok, reason in pass_requirements:
            if not ok:
                reasons.append(reason)

        if reasons:
            base["verdict"] = "INVALID"
            return base

        base["verdict"] = "PASS"
        base["codex_profile_available_for_d1_surface"] = True
        return base

    if reasons:
        structural_invalid = any(
            reason.startswith((
                "DISCOVERY_SCHEMA_",
                "SECRETS_",
                "FUNCTIONAL_",
                "FORBIDDEN_",
                "INITIALIZE_FIELDS_",
                "SANITIZED_",
                "INVENTORY_",
                "SCHEMA_INVENTORY_",
                "DISCOVERY_STATUS_UNRECOGNIZED",
            ))
            for reason in reasons
        )
        if structural_invalid:
            base["verdict"] = "INVALID"
            return base

    if status in FAIL_STATUSES:
        base["verdict"] = "FAIL"
        if not reasons:
            reasons.append(f"DISCOVERY_STATUS:{status}")
        return base

    base["verdict"] = "INVALID"
    return base


def adjudicate_file(input_path: Path, output_path: Path) -> dict[str, Any]:
    raw = input_path.read_bytes()
    input_sha = _sha256_bytes(raw)
    source_sha = _sha256_bytes(Path(__file__).read_bytes())
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        result = {
            "schema": SCHEMA,
            "adjudicator_source_sha256": source_sha,
            "discovery_input_sha256": input_sha,
            "verdict": "INVALID",
            "reason_codes": ["MALFORMED_JSON"],
            "codex_profile_available_for_d1_surface": False,
            "d2_authorized": False,
            "runtime_adapter_authorized": False,
        }
    else:
        result = adjudicate_data(data, input_sha, source_sha)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Frozen one-shot G2E P5A Codex D1 adjudicator")
    parser.add_argument("input", nargs="?", default="P5A_CODEX_DISCOVERY.json")
    parser.add_argument("--output", default="P5A_CODEX_D1_ADJUDICATION.json")
    args = parser.parse_args()

    result = adjudicate_file(Path(args.input), Path(args.output))
    print(json.dumps({
        "verdict": result["verdict"],
        "reason_codes": result["reason_codes"],
        "discovery_input_sha256": result["discovery_input_sha256"],
        "output": str(Path(args.output).resolve()),
    }, sort_keys=True))
    return 0 if result["verdict"] == "PASS" else (2 if result["verdict"] == "FAIL" else 3)


if __name__ == "__main__":
    raise SystemExit(main())
