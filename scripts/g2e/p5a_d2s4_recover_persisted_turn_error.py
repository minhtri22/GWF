from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any

THREAD_ID = "01a0c9af-d509-7203-9608-06304738b12e"
TURN_ID = "01a0c9af-d523-72f3-84fa-a575e91076b6"

ALLOWED_ROOTS = ("sessions", "archived_sessions", "log")
TEXT_SUFFIXES = {".jsonl", ".json", ".log", ".txt", ".ndjson", ".gz"}
SQLITE_SUFFIXES = {".sqlite", ".sqlite3", ".db"}

FORBIDDEN_BASENAMES = {
    "auth.json",
    "config.toml",
    "credentials.json",
    "secrets.json",
    "tokens.json",
}

SECRET_KEY_RE = re.compile(
    r"(authorization|api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret|credential)",
    re.IGNORECASE,
)
SECRET_TEXT_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s,;]+"),
]

MECHANISM_KEYS = {
    "type",
    "event",
    "method",
    "id",
    "thread_id",
    "threadId",
    "turn_id",
    "turnId",
    "status",
    "error",
    "message",
    "codex_error_info",
    "codexErrorInfo",
    "additional_details",
    "additionalDetails",
    "will_retry",
    "willRetry",
    "code",
    "name",
    "kind",
    "phase",
    "error_type",
    "errorType",
    "timestamp",
    "ts",
    "ts_unix",
}

MAX_TEXT_FILE_BYTES = 32 * 1024 * 1024
MAX_MATCHES_PER_FILE = 200
MAX_SQLITE_ROWS_PER_TABLE = 100


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def redact_text(value: str) -> str:
    out = value
    for pattern in SECRET_TEXT_PATTERNS:
        out = pattern.sub("<REDACTED>", out)
    return out


def safe_scalar(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return redact_text(str(value))


def project_mechanism_fields(obj: Any) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                if SECRET_KEY_RE.search(str(key)):
                    findings.append({"path": child_path, "key": str(key), "value": "<REDACTED>"})
                    continue
                if key in MECHANISM_KEYS:
                    if isinstance(child, (dict, list)):
                        # Preserve only mechanism-bearing descendants, never arbitrary prompt/content.
                        nested_before = len(findings)
                        walk(child, child_path)
                        if len(findings) == nested_before and isinstance(child, dict):
                            findings.append(
                                {
                                    "path": child_path,
                                    "key": str(key),
                                    "value": {
                                        k: safe_scalar(v)
                                        for k, v in child.items()
                                        if k in MECHANISM_KEYS and not SECRET_KEY_RE.search(str(k))
                                    },
                                }
                            )
                    else:
                        findings.append(
                            {"path": child_path, "key": str(key), "value": safe_scalar(child)}
                        )
                else:
                    walk(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(obj, "")
    return findings


def contains_target(text: str) -> bool:
    return THREAD_ID in text or TURN_ID in text


def open_text(path: Path):
    if path.suffix.lower() == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("rt", encoding="utf-8", errors="replace")


def scan_text_file(path: Path, root: Path) -> list[dict[str, Any]]:
    if path.name.lower() in FORBIDDEN_BASENAMES:
        return []
    if path.stat().st_size > MAX_TEXT_FILE_BYTES:
        return []

    source_sha = sha256_file(path)
    matches: list[dict[str, Any]] = []
    try:
        with open_text(path) as fh:
            for line_no, line in enumerate(fh, start=1):
                if not contains_target(line):
                    continue
                raw = line.rstrip("\r\n")
                record: dict[str, Any] = {
                    "source": str(path.relative_to(root)),
                    "source_sha256": source_sha,
                    "line": line_no,
                    "raw_line_sha256": hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest(),
                    "raw_line_length": len(raw),
                    "contains_thread_id": THREAD_ID in raw,
                    "contains_turn_id": TURN_ID in raw,
                }
                try:
                    parsed = json.loads(raw)
                except Exception:
                    # Plain log line: preserve only bounded context around an exact target id.
                    positions = [p for p in (raw.find(THREAD_ID), raw.find(TURN_ID)) if p >= 0]
                    pos = min(positions) if positions else 0
                    lo = max(0, pos - 600)
                    hi = min(len(raw), pos + 1200)
                    record["text_context_redacted"] = redact_text(raw[lo:hi])
                else:
                    record["mechanism_fields"] = project_mechanism_fields(parsed)
                matches.append(record)
                if len(matches) >= MAX_MATCHES_PER_FILE:
                    break
    except (OSError, UnicodeError) as exc:
        return [
            {
                "source": str(path.relative_to(root)),
                "source_sha256": source_sha,
                "read_error": f"{type(exc).__name__}:{exc}",
            }
        ]
    return matches


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def sqlite_value_for_output(column: str, value: Any) -> Any:
    if SECRET_KEY_RE.search(column):
        return "<REDACTED>"
    if value is None or isinstance(value, (int, float)):
        return value
    if isinstance(value, bytes):
        return f"<BLOB:{len(value)}>"
    text = str(value)
    if contains_target(text) or column in MECHANISM_KEYS or any(
        token in column.lower() for token in ("error", "status", "message", "code", "detail")
    ):
        if len(text) > 4000:
            text = text[:4000] + "<TRUNCATED>"
        return redact_text(text)
    return "<OMITTED_NON_MECHANISM_VALUE>"


def scan_sqlite(path: Path, root: Path) -> list[dict[str, Any]]:
    if path.name.lower() in FORBIDDEN_BASENAMES:
        return []
    source_sha = sha256_file(path)
    results: list[dict[str, Any]] = []
    uri = path.resolve().as_uri() + "?mode=ro&immutable=1"
    try:
        con = sqlite3.connect(uri, uri=True)
    except Exception as exc:
        return [
            {
                "source": str(path.relative_to(root)),
                "source_sha256": source_sha,
                "sqlite_open_error": f"{type(exc).__name__}:{exc}",
            }
        ]

    try:
        tables = [
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            if isinstance(row[0], str)
        ]
        for table in tables:
            try:
                columns = [
                    row[1]
                    for row in con.execute(f"PRAGMA table_info({quote_ident(table)})")
                    if isinstance(row[1], str)
                ]
            except sqlite3.Error:
                continue
            if not columns:
                continue

            clauses = []
            params: list[str] = []
            for col in columns:
                qcol = quote_ident(col)
                clauses.append(f"CAST({qcol} AS TEXT) LIKE ?")
                params.append(f"%{THREAD_ID}%")
                clauses.append(f"CAST({qcol} AS TEXT) LIKE ?")
                params.append(f"%{TURN_ID}%")
            sql = (
                f"SELECT rowid, * FROM {quote_ident(table)} WHERE "
                + " OR ".join(clauses)
                + f" LIMIT {MAX_SQLITE_ROWS_PER_TABLE}"
            )
            try:
                cursor = con.execute(sql, params)
                names = [d[0] for d in cursor.description]
                rows = cursor.fetchall()
            except sqlite3.Error:
                continue

            for row in rows:
                values = dict(zip(names, row))
                projected = {
                    key: sqlite_value_for_output(key, value)
                    for key, value in values.items()
                    if key == "rowid"
                    or contains_target(str(value))
                    or key in MECHANISM_KEYS
                    or any(
                        token in key.lower()
                        for token in ("error", "status", "message", "code", "detail")
                    )
                }
                results.append(
                    {
                        "source": str(path.relative_to(root)),
                        "source_sha256": source_sha,
                        "table": table,
                        "row": projected,
                    }
                )
    finally:
        con.close()
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex-home", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    codex_home = Path(args.codex_home).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not codex_home.is_dir():
        raise SystemExit(f"CODEX_HOME_MISSING:{codex_home}")
    if output_dir.exists():
        raise SystemExit(f"OUTPUT_DIR_ALREADY_EXISTS:{output_dir}")

    output_dir.mkdir(parents=True)

    text_matches: list[dict[str, Any]] = []
    scanned_text_files: list[dict[str, Any]] = []
    sqlite_matches: list[dict[str, Any]] = []
    scanned_sqlite_files: list[dict[str, Any]] = []

    for rel_root in ALLOWED_ROOTS:
        base = codex_home / rel_root
        if not base.exists():
            continue
        for path in sorted(p for p in base.rglob("*") if p.is_file()):
            if path.name.lower() in FORBIDDEN_BASENAMES:
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            scanned_text_files.append(
                {
                    "source": str(path.relative_to(codex_home)),
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
            text_matches.extend(scan_text_file(path, codex_home))

    # SQLite can be stored directly under CODEX_HOME or nested. Open only matching extensions, read-only.
    for path in sorted(p for p in codex_home.rglob("*") if p.is_file()):
        if path.name.lower() in FORBIDDEN_BASENAMES:
            continue
        if path.suffix.lower() not in SQLITE_SUFFIXES:
            continue
        scanned_sqlite_files.append(
            {
                "source": str(path.relative_to(codex_home)),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
        sqlite_matches.extend(scan_sqlite(path, codex_home))

    result = {
        "schema": "G2E-P5A-D2S4-PERSISTED-TURN-ERROR-RECOVERY-v1",
        "thread_id": THREAD_ID,
        "turn_id": TURN_ID,
        "collection_mode": "READ_ONLY_EXISTING_LOCAL_EVIDENCE",
        "codex_started": False,
        "rpc_sent": False,
        "vhdx_mounted": False,
        "scientific_attempt_retried": False,
        "forbidden_files_read": False,
        "text_match_count": len(text_matches),
        "sqlite_match_count": len(sqlite_matches),
        "scanned_text_files": scanned_text_files,
        "scanned_sqlite_files": scanned_sqlite_files,
        "text_matches": text_matches,
        "sqlite_matches": sqlite_matches,
    }

    out = output_dir / "P5A_D2S4_PERSISTED_TURN_ERROR_RECOVERY.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(out),
                "text_match_count": len(text_matches),
                "sqlite_match_count": len(sqlite_matches),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
