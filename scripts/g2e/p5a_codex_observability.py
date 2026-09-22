from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

SOURCE_COMMIT = "3d2ee51ca2d5db578f328aa75e20aa22c0197c9a"
THREAD_DATA_GIT_BLOB = "649a94be493dadac887a9eb67cecae1365ff3c1e"
NOTIFICATION_GIT_BLOB = "ca0e7753f3cb3c007e544b3507881b6cffeecacd"
ERROR_NOTIFICATION_SCHEMA_GIT_BLOB = "69187dd539dfa5f676397444b3e36a426884b81d"
TURN_COMPLETED_SCHEMA_GIT_BLOB = "7db8c18c82325feee77876ed7172dae8125a4cd5"

SECRET_KEY_RE = re.compile(
    r"(authorization|api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret|credential|cookie)",
    re.IGNORECASE,
)
SECRET_PATTERNS = [
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(
        r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|token|password|secret)\b"
        r"\s*[:=]\s*[^\s,;]+"
    ),
]
WINDOWS_HOME_RE = re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+")
UNIX_HOME_RE = re.compile(r"(?<![A-Za-z0-9_])/(?:home|Users)/[^/\s]+")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _known_home_candidates() -> list[str]:
    candidates = [
        os.environ.get("USERPROFILE"),
        os.environ.get("HOME"),
        str(Path.home()) if str(Path.home()) else None,
    ]
    unique: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate:
            continue
        key = candidate.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return sorted(unique, key=len, reverse=True)


def redact_text(value: str) -> tuple[str, bool]:
    redacted = value
    changed = False

    for candidate in _known_home_candidates():
        replaced = re.sub(re.escape(candidate), "<USER_HOME>", redacted, flags=re.IGNORECASE)
        if replaced != redacted:
            redacted = replaced
            changed = True

    for pattern, replacement in (
        (WINDOWS_HOME_RE, "<USER_HOME>"),
        (UNIX_HOME_RE, "<USER_HOME>"),
    ):
        replaced = pattern.sub(replacement, redacted)
        if replaced != redacted:
            redacted = replaced
            changed = True

    for pattern in SECRET_PATTERNS:
        replaced = pattern.sub("<REDACTED_SECRET>", redacted)
        if replaced != redacted:
            redacted = replaced
            changed = True

    return redacted, changed


def project_text(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    raw = str(value)
    redacted, changed = redact_text(raw)
    return {
        "text": redacted,
        "rawSha256": sha256_bytes(raw.encode("utf-8")),
        "rawLength": len(raw),
        "redactionApplied": changed,
    }


def sanitize_structured(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            if SECRET_KEY_RE.search(str(key)):
                result[str(key)] = "<REDACTED_SECRET>"
            else:
                result[str(key)] = sanitize_structured(child)
        return result
    if isinstance(value, list):
        return [sanitize_structured(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)[0]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return redact_text(str(value))[0]


def project_misalignment(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    result: dict[str, Any] = {}
    if "errorType" in value:
        result["errorType"] = sanitize_structured(value.get("errorType"))
    if "detailedExplanation" in value:
        result["detailedExplanation"] = project_text(value.get("detailedExplanation"))
    if "steer" in value:
        steer = value.get("steer")
        # Preserve observability that a continuation steer exists without persisting
        # the continuation instruction itself.
        result["steerPresent"] = steer is not None
    return result


def project_turn_error(error: Any) -> dict[str, Any] | None:
    if not isinstance(error, dict):
        return None
    return {
        "message": project_text(error.get("message")),
        "codexErrorInfo": sanitize_structured(error.get("codexErrorInfo")),
        "additionalDetails": project_text(error.get("additionalDetails")),
        "misalignment": project_misalignment(error.get("misalignment")),
    }


def project_protocol_message(raw: str, ts_unix: float | None = None) -> dict[str, Any]:
    raw_bytes = raw.encode("utf-8")
    record: dict[str, Any] = {
        "length": len(raw),
        "rawSha256": sha256_bytes(raw_bytes),
    }
    if ts_unix is not None:
        record["tsUnix"] = ts_unix

    try:
        message = json.loads(raw)
    except Exception:
        record["parseError"] = True
        return record

    if not isinstance(message, dict):
        record["parseError"] = True
        return record

    if "id" in message:
        record["id"] = message.get("id")
    method = message.get("method")
    if method is not None:
        record["method"] = method

    if "error" in message and "id" in message:
        rpc_error = message.get("error")
        if isinstance(rpc_error, dict):
            record["rpcError"] = {
                "code": rpc_error.get("code"),
                "message": project_text(rpc_error.get("message")),
            }

    if method == "error":
        params = message.get("params") or {}
        if isinstance(params, dict):
            record["terminalErrorEvidence"] = {
                "source": "errorNotification",
                "threadId": params.get("threadId"),
                "turnId": params.get("turnId"),
                "willRetry": params.get("willRetry"),
                "error": project_turn_error(params.get("error")),
            }

    if method == "turn/completed":
        params = message.get("params") or {}
        turn = params.get("turn") if isinstance(params, dict) else None
        if isinstance(turn, dict):
            record["terminalErrorEvidence"] = {
                "source": "turnCompleted",
                "threadId": params.get("threadId"),
                "turnId": turn.get("id"),
                "status": turn.get("status"),
                "error": project_turn_error(turn.get("error")),
            }

    return record


def verify_schema_contract(error_schema: dict[str, Any], turn_schema: dict[str, Any]) -> None:
    error_props = error_schema.get("properties") or {}
    error_required = set(error_schema.get("required") or [])
    if error_required != {"error", "threadId", "turnId", "willRetry"}:
        raise ValueError(f"ERROR_NOTIFICATION_REQUIRED_DRIFT:{sorted(error_required)}")

    for field in ("error", "threadId", "turnId", "willRetry"):
        if field not in error_props:
            raise ValueError(f"ERROR_NOTIFICATION_FIELD_MISSING:{field}")

    error_defs = error_schema.get("definitions") or {}
    turn_error = error_defs.get("TurnError") or {}
    turn_error_props = turn_error.get("properties") or {}
    turn_error_required = set(turn_error.get("required") or [])
    if "message" not in turn_error_required:
        raise ValueError("TURN_ERROR_MESSAGE_NOT_REQUIRED")
    for field in ("message", "codexErrorInfo", "additionalDetails", "misalignment"):
        if field not in turn_error_props:
            raise ValueError(f"TURN_ERROR_FIELD_MISSING:{field}")

    turn_props = turn_schema.get("properties") or {}
    if "threadId" not in turn_props or "turn" not in turn_props:
        raise ValueError("TURN_COMPLETED_TOPLEVEL_DRIFT")

    turn_defs = turn_schema.get("definitions") or {}
    turn = turn_defs.get("Turn") or {}
    turn_props_inner = turn.get("properties") or {}
    for field in ("id", "status", "error"):
        if field not in turn_props_inner:
            raise ValueError(f"TURN_FIELD_MISSING:{field}")

    status = turn_defs.get("TurnStatus") or {}
    allowed = set(status.get("enum") or [])
    if "failed" not in allowed:
        raise ValueError("TURN_STATUS_FAILED_MISSING")

    turn_error_2 = turn_defs.get("TurnError") or {}
    props_2 = turn_error_2.get("properties") or {}
    required_2 = set(turn_error_2.get("required") or [])
    if "message" not in required_2:
        raise ValueError("TURN_COMPLETED_ERROR_MESSAGE_NOT_REQUIRED")
    for field in ("message", "codexErrorInfo", "additionalDetails", "misalignment"):
        if field not in props_2:
            raise ValueError(f"TURN_COMPLETED_ERROR_FIELD_MISSING:{field}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-error-schema")
    parser.add_argument("--verify-turn-completed-schema")
    args = parser.parse_args()

    if args.verify_error_schema or args.verify_turn_completed_schema:
        if not args.verify_error_schema or not args.verify_turn_completed_schema:
            raise SystemExit("BOTH_SCHEMA_PATHS_REQUIRED")
        error_schema = json.loads(Path(args.verify_error_schema).read_text(encoding="utf-8"))
        turn_schema = json.loads(
            Path(args.verify_turn_completed_schema).read_text(encoding="utf-8")
        )
        verify_schema_contract(error_schema, turn_schema)
        print(
            json.dumps(
                {
                    "schema": "G2E-P5A-CODEX-OBSERVABILITY-PROTOCOL-COMPAT-v1",
                    "source_commit": SOURCE_COMMIT,
                    "status": "PASS",
                },
                sort_keys=True,
            )
        )
        return 0

    parser.error("no action specified")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
