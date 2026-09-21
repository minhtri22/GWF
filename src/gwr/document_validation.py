from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
import json
import os
import re
import subprocess
from typing import Protocol


@dataclass(frozen=True)
class ValidatorFinding:
    rule_id: str
    message: str
    line: int | None = None
    column: int | None = None
    severity: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ValidatorExecution:
    validator_id: str
    validator_version: str | None
    config_hash: str | None
    subject_path: str
    subject_hash: str
    execution_status: str
    content_status: str
    findings: tuple[ValidatorFinding, ...]
    error_code: str | None = None

    def to_dict(self) -> dict:
        out = asdict(self)
        out["findings"] = [f.to_dict() for f in self.findings]
        return out


class ValidatorAdapter(Protocol):
    validator_id: str

    def validate(self, subject: str | Path) -> ValidatorExecution: ...


_DEFAULT_LINE = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+)(?::(?P<column>\d+))?\s+"
    r"(?:(?P<severity>error|warning)\s+)?"
    r"(?P<rule>MD\d{3}(?:/[A-Za-z0-9_-]+)?)\s+(?P<message>.*)$",
    re.IGNORECASE,
)


class MarkdownlintCli2Adapter:
    validator_id = "markdownlint-cli2"

    def __init__(
        self,
        *,
        executable: str = "markdownlint-cli2",
        expected_version: str,
        config_path: str | Path,
        timeout_seconds: int = 30,
    ) -> None:
        self.executable = executable
        self.expected_version = expected_version
        self.config_path = Path(config_path)
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _hash_bytes(value: bytes) -> str:
        return sha256(value).hexdigest()

    def _config_hash(self) -> str:
        return self._hash_bytes(self.config_path.read_bytes())

    def _version(self) -> tuple[str | None, str | None]:
        try:
            p = subprocess.run(
                [self.executable, "--help"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError:
            return None, "EXECUTABLE_NOT_FOUND"
        except (OSError, subprocess.TimeoutExpired):
            return None, "VERSION_PROBE_FAILED"

        first = next((line.strip() for line in p.stdout.splitlines() if line.strip()), "")
        match = re.search(r"markdownlint-cli2\s+v(?P<v>\d+\.\d+\.\d+)", first)
        # markdownlint-cli2 intentionally returns 2 for --help after printing
        # the banner. Accept only the documented help outcomes when the exact
        # version banner can be parsed; other outcomes fail closed.
        if p.returncode not in {0, 2} or not match:
            return None, "VERSION_PROBE_FAILED"
        return match.group("v"), None

    @staticmethod
    def _sanitize_message(message: str) -> str:
        marker = " [Context: "
        if marker in message:
            message = message.split(marker, 1)[0]
        return message.strip()

    @staticmethod
    def _parse_findings(output: str) -> tuple[ValidatorFinding, ...] | None:
        findings: list[ValidatorFinding] = []
        for raw in output.splitlines():
            line = raw.strip()
            if not line:
                continue
            match = _DEFAULT_LINE.match(line)
            if not match:
                if re.search(r":\d+(?::\d+)?\s", line):
                    return None
                continue
            findings.append(
                ValidatorFinding(
                    rule_id=match.group("rule"),
                    message=MarkdownlintCli2Adapter._sanitize_message(match.group("message")),
                    line=int(match.group("line")),
                    column=int(match.group("column")) if match.group("column") else None,
                    severity=match.group("severity").upper() if match.group("severity") else None,
                )
            )
        return tuple(findings)

    def validate(self, subject: str | Path) -> ValidatorExecution:
        subject_path = Path(subject)
        before = subject_path.read_bytes()
        subject_hash = self._hash_bytes(before)
        config_hash = self._config_hash()

        version, version_error = self._version()
        if version_error:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "UNAVAILABLE" if version_error == "EXECUTABLE_NOT_FOUND" else "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                version_error,
            )
        if version != self.expected_version:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "VERSION_MISMATCH",
            )

        try:
            p = subprocess.run(
                [
                    self.executable,
                    subject_path.name,
                    "--config",
                    str(self.config_path.resolve()),
                ],
                cwd=str(subject_path.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "UNAVAILABLE",
                "NOT_EVALUATED",
                tuple(),
                "EXECUTABLE_NOT_FOUND",
            )
        except subprocess.TimeoutExpired:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "TIMEOUT",
            )
        except OSError:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "EXECUTION_FAILED",
            )

        after = subject_path.read_bytes()
        if after != before:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "SOURCE_MUTATED",
            )

        if p.returncode not in {0, 1}:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                f"EXIT_{p.returncode}",
            )

        findings = self._parse_findings(p.stdout)
        if findings is None:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "OUTPUT_PARSE_ERROR",
            )

        if p.returncode == 0 and findings:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "INCONSISTENT_EXIT_FINDINGS",
            )
        if p.returncode == 1 and not findings:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "FINDINGS_MISSING",
            )

        return ValidatorExecution(
            self.validator_id,
            version,
            config_hash,
            str(subject_path),
            subject_hash,
            "SUCCEEDED",
            "PASS" if p.returncode == 0 else "FINDINGS",
            findings,
            None,
        )



class ValeAdapter:
    validator_id = "vale"

    def __init__(
        self,
        *,
        executable: str = "vale",
        expected_version: str,
        config_path: str | Path,
        styles_path: str | Path,
        timeout_seconds: int = 30,
    ) -> None:
        self.executable = executable
        self.expected_version = expected_version
        self.config_path = Path(config_path)
        self.styles_path = Path(styles_path)
        self.timeout_seconds = timeout_seconds

    def _config_hash(self) -> str:
        root = self.config_path.parent
        entries: list[Path] = [self.config_path]
        entries.extend(sorted(p for p in self.styles_path.rglob("*") if p.is_file()))
        digest = sha256(b"DG-P1-VALE-CONFIG-v1\0")
        for path in entries:
            rel = path.relative_to(root).as_posix()
            content_hash = sha256(path.read_bytes()).hexdigest()
            digest.update(rel.encode("utf-8"))
            digest.update(b"\0")
            digest.update(content_hash.encode("ascii"))
            digest.update(b"\n")
        return digest.hexdigest()

    def _version(self) -> tuple[str | None, str | None]:
        try:
            p = subprocess.run(
                [self.executable, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError:
            return None, "EXECUTABLE_NOT_FOUND"
        except (OSError, subprocess.TimeoutExpired):
            return None, "VERSION_PROBE_FAILED"

        match = re.search(
            r"^vale version (?P<v>\d+\.\d+\.\d+)\s*$",
            p.stdout.strip(),
            re.IGNORECASE,
        )
        if p.returncode != 0 or not match:
            return None, "VERSION_PROBE_FAILED"
        return match.group("v"), None

    @staticmethod
    def _sanitize_message(message: str, matched_text: str) -> str:
        cleaned = message.strip()
        if matched_text:
            cleaned = cleaned.replace(matched_text, "<redacted-match>")
        return cleaned

    @staticmethod
    def _parse_findings(output: str) -> tuple[ValidatorFinding, ...] | None:
        try:
            payload = json.loads(output)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None

        findings: list[ValidatorFinding] = []
        for alerts in payload.values():
            if alerts is None:
                continue
            if not isinstance(alerts, list):
                return None
            for alert in alerts:
                if not isinstance(alert, dict):
                    return None
                rule_id = alert.get("Check")
                message = alert.get("Message")
                severity = alert.get("Severity")
                line = alert.get("Line")
                span = alert.get("Span")
                matched_text = alert.get("Match", "")

                if (
                    not isinstance(rule_id, str)
                    or not rule_id.strip()
                    or not isinstance(message, str)
                    or not isinstance(severity, str)
                    or severity.lower() not in {"suggestion", "warning", "error"}
                    or not isinstance(line, int)
                    or line < 1
                    or not isinstance(span, list)
                    or not span
                    or not isinstance(span[0], int)
                    or span[0] < 1
                    or not isinstance(matched_text, str)
                ):
                    return None

                findings.append(
                    ValidatorFinding(
                        rule_id=rule_id.strip(),
                        message=ValeAdapter._sanitize_message(message, matched_text),
                        line=line,
                        column=span[0],
                        severity=severity.upper(),
                    )
                )

        findings.sort(
            key=lambda f: (
                f.line if f.line is not None else 0,
                f.column if f.column is not None else 0,
                f.rule_id,
                f.message,
            )
        )
        return tuple(findings)

    def validate(self, subject: str | Path) -> ValidatorExecution:
        subject_path = Path(subject)
        before = subject_path.read_bytes()
        subject_hash = sha256(before).hexdigest()

        try:
            config_hash = self._config_hash()
        except OSError:
            return ValidatorExecution(
                self.validator_id,
                None,
                None,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "CONFIG_UNREADABLE",
            )

        version, version_error = self._version()
        if version_error:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "UNAVAILABLE" if version_error == "EXECUTABLE_NOT_FOUND" else "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                version_error,
            )
        if version != self.expected_version:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "VERSION_MISMATCH",
            )

        try:
            p = subprocess.run(
                [
                    self.executable,
                    "--config",
                    str(self.config_path.resolve()),
                    "--output=JSON",
                    str(subject_path.resolve()),
                ],
                cwd=str(self.config_path.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "UNAVAILABLE",
                "NOT_EVALUATED",
                tuple(),
                "EXECUTABLE_NOT_FOUND",
            )
        except subprocess.TimeoutExpired:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "TIMEOUT",
            )
        except OSError:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "EXECUTION_FAILED",
            )

        if subject_path.read_bytes() != before:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "SOURCE_MUTATED",
            )

        if p.returncode not in {0, 1}:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                f"EXIT_{p.returncode}",
            )

        findings = self._parse_findings(p.stdout)
        if findings is None:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "OUTPUT_PARSE_ERROR",
            )
        if p.returncode == 1 and not findings:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "FINDINGS_MISSING",
            )

        return ValidatorExecution(
            self.validator_id,
            version,
            config_hash,
            str(subject_path),
            subject_hash,
            "SUCCEEDED",
            "FINDINGS" if findings else "PASS",
            findings,
            None,
        )



class LycheeAdapter:
    validator_id = "lychee"

    def __init__(
        self,
        *,
        executable: str = "lychee",
        expected_version: str,
        config_path: str | Path,
        timeout_seconds: int = 30,
    ) -> None:
        self.executable = executable
        self.expected_version = expected_version
        self.config_path = Path(config_path)
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _hash_bytes(value: bytes) -> str:
        return sha256(value).hexdigest()

    def _config_hash(self) -> str:
        return self._hash_bytes(self.config_path.read_bytes())

    @staticmethod
    def _subprocess_env() -> dict[str, str]:
        allowed = (
            "PATH",
            "HOME",
            "LANG",
            "LC_ALL",
            "SSL_CERT_FILE",
            "SSL_CERT_DIR",
            "SYSTEMROOT",
            "WINDIR",
        )
        return {key: os.environ[key] for key in allowed if key in os.environ}

    def _version(self) -> tuple[str | None, str | None]:
        try:
            p = subprocess.run(
                [self.executable, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                env=self._subprocess_env(),
            )
        except FileNotFoundError:
            return None, "EXECUTABLE_NOT_FOUND"
        except (OSError, subprocess.TimeoutExpired):
            return None, "VERSION_PROBE_FAILED"

        match = re.search(
            r"^lychee\s+(?P<v>\d+\.\d+\.\d+)\s*$",
            p.stdout.strip(),
            re.IGNORECASE,
        )
        if p.returncode != 0 or not match:
            return None, "VERSION_PROBE_FAILED"
        return match.group("v"), None

    @staticmethod
    def _span(value: object) -> tuple[int | None, int | None] | None:
        if value is None:
            return None, None
        if not isinstance(value, dict):
            return None
        line = value.get("line")
        column = value.get("column")
        if line is not None and (not isinstance(line, int) or line < 1):
            return None
        if column is not None and (not isinstance(column, int) or column < 1):
            return None
        return line, column

    @staticmethod
    def _parse_report(
        output: str,
    ) -> tuple[tuple[ValidatorFinding, ...], bool] | None:
        try:
            payload = json.loads(output)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None

        errors = payload.get("errors")
        timeouts = payload.get("timeouts")
        error_map = payload.get("error_map")
        timeout_map = payload.get("timeout_map")
        if (
            not isinstance(errors, int)
            or errors < 0
            or not isinstance(timeouts, int)
            or timeouts < 0
            or not isinstance(error_map, dict)
            or not isinstance(timeout_map, dict)
        ):
            return None

        findings: list[ValidatorFinding] = []
        error_entries = 0
        network_failure = False

        for entries in error_map.values():
            if not isinstance(entries, list):
                return None
            for entry in entries:
                error_entries += 1
                if not isinstance(entry, dict):
                    return None
                uri = entry.get("url")
                status = entry.get("status")
                span = LycheeAdapter._span(entry.get("span"))
                if not isinstance(uri, str) or not uri or not isinstance(status, dict) or span is None:
                    return None

                line, column = span
                code = status.get("code")
                if code is not None and (not isinstance(code, int) or code < 100 or code > 599):
                    return None

                if uri.startswith("file://"):
                    findings.append(
                        ValidatorFinding(
                            rule_id="LYCHEE.INTERNAL_BROKEN",
                            message="Broken internal link",
                            line=line,
                            column=column,
                            severity="ERROR",
                        )
                    )
                elif uri.startswith("http://") or uri.startswith("https://"):
                    if isinstance(code, int):
                        findings.append(
                            ValidatorFinding(
                                rule_id="LYCHEE.EXTERNAL_BROKEN",
                                message=f"Broken external link (HTTP {code})",
                                line=line,
                                column=column,
                                severity="ERROR",
                            )
                        )
                    else:
                        network_failure = True
                else:
                    return None

        timeout_entries = 0
        for entries in timeout_map.values():
            if not isinstance(entries, list):
                return None
            for entry in entries:
                timeout_entries += 1
                if not isinstance(entry, dict):
                    return None
                network_failure = True

        if error_entries != errors or timeout_entries != timeouts:
            return None

        findings.sort(
            key=lambda f: (
                f.line if f.line is not None else 0,
                f.column if f.column is not None else 0,
                f.rule_id,
                f.message,
            )
        )
        return tuple(findings), network_failure

    def validate(self, subject: str | Path) -> ValidatorExecution:
        subject_path = Path(subject)
        before = subject_path.read_bytes()
        subject_hash = self._hash_bytes(before)

        try:
            config_hash = self._config_hash()
        except OSError:
            return ValidatorExecution(
                self.validator_id,
                None,
                None,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "CONFIG_UNREADABLE",
            )

        version, version_error = self._version()
        if version_error:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "UNAVAILABLE" if version_error == "EXECUTABLE_NOT_FOUND" else "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                version_error,
            )
        if version != self.expected_version:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "VERSION_MISMATCH",
            )

        try:
            p = subprocess.run(
                [
                    self.executable,
                    "--config",
                    str(self.config_path.resolve()),
                    "--format",
                    "json",
                    "--no-progress",
                    "--max-retries",
                    "0",
                    str(subject_path.resolve()),
                ],
                cwd=str(subject_path.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                env=self._subprocess_env(),
            )
        except FileNotFoundError:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "UNAVAILABLE",
                "NOT_EVALUATED",
                tuple(),
                "EXECUTABLE_NOT_FOUND",
            )
        except subprocess.TimeoutExpired:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "TIMEOUT",
            )
        except OSError:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "EXECUTION_FAILED",
            )

        if subject_path.read_bytes() != before:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "SOURCE_MUTATED",
            )

        if p.returncode not in {0, 2}:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                f"EXIT_{p.returncode}",
            )

        parsed = self._parse_report(p.stdout)
        if parsed is None:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "OUTPUT_PARSE_ERROR",
            )
        findings, network_failure = parsed

        if network_failure:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "NETWORK_FAILURE",
            )
        if p.returncode == 0 and findings:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "INCONSISTENT_EXIT_FINDINGS",
            )
        if p.returncode == 2 and not findings:
            return ValidatorExecution(
                self.validator_id,
                version,
                config_hash,
                str(subject_path),
                subject_hash,
                "TOOL_ERROR",
                "NOT_EVALUATED",
                tuple(),
                "FINDINGS_MISSING",
            )

        return ValidatorExecution(
            self.validator_id,
            version,
            config_hash,
            str(subject_path),
            subject_hash,
            "SUCCEEDED",
            "FINDINGS" if findings else "PASS",
            findings,
            None,
        )
