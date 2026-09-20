from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

TEXT_SUFFIXES = {".html", ".js", ".json", ".css", ".txt", ".md", ".map"}

# Concrete credential formats must never appear in a public static bundle.
SECRET_VALUE_PATTERNS = [
    ("github_classic_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("github_fine_grained_token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("openai_style_secret", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("bearer_credential", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{12,}=*")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

# Public Pages must not even offer/persist credential-bearing fields. Security
# notices may mention words such as "API key", so these patterns target code/
# markup contexts rather than plain prose.
CREDENTIAL_FIELD_PATTERNS = [
    (
        "password_input",
        re.compile(r"(?is)<input\b[^>]*\btype\s*=\s*['\"]password['\"][^>]*>"),
    ),
    (
        "credential_form_field",
        re.compile(
            r"(?is)<(?:input|textarea)\b[^>]*(?:id|name)\s*=\s*['\"]"
            r"[^'\"]*(?:api[-_]?key|access[-_]?token|refresh[-_]?token|password|secret)"
            r"[^'\"]*['\"][^>]*>"
        ),
    ),
    (
        "credential_local_storage",
        re.compile(
            r"(?is)localStorage\.(?:setItem|getItem)\s*\(\s*['\"]"
            r"[^'\"]*(?:api[-_]?key|access[-_]?token|refresh[-_]?token|password|secret)"
            r"[^'\"]*['\"]"
        ),
    ),
    (
        "authorization_header_assignment",
        re.compile(r"(?is)['\"]Authorization['\"]\s*:\s*['\"](?:Bearer\s+)?[^'\"]+['\"]"),
    ),
    (
        "credential_object_property",
        re.compile(
            r"(?im)(?:^|[,{]\s*)['\"]?"
            r"(?:apiKey|api_key|accessToken|access_token|refreshToken|refresh_token|password|clientSecret|client_secret)"
            r"['\"]?\s*:\s*['\"][^'\"]+['\"]"
        ),
    ),
]


def iter_text_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        if root.suffix.lower() in TEXT_SUFFIXES:
            yield root
        return
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def scan_public_tree(root: str | Path) -> list[dict]:
    root = Path(root)
    findings: list[dict] = []
    for path in iter_text_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        for kind, pattern in [*SECRET_VALUE_PATTERNS, *CREDENTIAL_FIELD_PATTERNS]:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(
                    {
                        "kind": kind,
                        "path": str(path.relative_to(root) if root.is_dir() else path.name),
                        "line": line,
                    }
                )
    return findings


def assert_public_tree_safe(root: str | Path) -> None:
    findings = scan_public_tree(root)
    if findings:
        raise RuntimeError(
            "Public site secret boundary violated: " + json.dumps(findings, sort_keys=True)
        )


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Fail when a public static site contains credentials or credential-bearing UI/storage."
    )
    ap.add_argument("path", nargs="?", default="web")
    args = ap.parse_args()
    findings = scan_public_tree(args.path)
    result = {
        "status": "PASS" if not findings else "FAIL",
        "path": str(Path(args.path)),
        "findings": findings,
        "policy": "PUBLIC_STATIC_NO_CREDENTIALS",
    }
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if not findings else 1)


if __name__ == "__main__":
    main()
