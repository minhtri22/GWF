from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
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
        if p.returncode != 0 or not match:
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
