from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol, Sequence
import hashlib
import os
import re
import shutil
import subprocess


MARKDOWNLINT_CLI2_VERSION = "0.23.3"
_VALID_EXECUTION_STATUS = {"SUCCEEDED", "TOOL_ERROR", "UNAVAILABLE"}
_VALID_CONTENT_STATUS = {"PASS", "FINDINGS", "NOT_EVALUATED"}


@dataclass(frozen=True)
class ValidatorFinding:
    finding_class: str
    severity: str
    rule_id: str
    message: str
    subject_path: str
    line: int | None = None
    column: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ValidatorExecution:
    validator_id: str
    validator_version: str
    observed_validator_version: str | None
    config_sha256: str
    subject_path: str
    subject_sha256: str
    execution_status: str
    content_status: str
    return_code: int | None
    findings: tuple[ValidatorFinding, ...]
    error_code: str | None = None

    def __post_init__(self):
        if self.execution_status not in _VALID_EXECUTION_STATUS:
            raise ValueError(f"Invalid execution_status: {self.execution_status}")
        if self.content_status not in _VALID_CONTENT_STATUS:
            raise ValueError(f"Invalid content_status: {self.content_status}")
        if self.execution_status != "SUCCEEDED" and self.content_status != "NOT_EVALUATED":
            raise ValueError("Failed/unavailable execution must use NOT_EVALUATED content status")
        if self.execution_status == "SUCCEEDED" and self.content_status == "NOT_EVALUATED":
            raise ValueError("Successful execution must evaluate content")

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["finding_count"] = self.finding_count
        payload["findings"] = [x.to_dict() for x in self.findings]
        return payload


class ValidatorAdapter(Protocol):
    validator_id: str
    validator_version: str

    def validate(self, subject_path: str | Path) -> ValidatorExecution:
        ...


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _default_command() -> tuple[str, ...]:
    direct = shutil.which("markdownlint-cli2") or shutil.which("markdownlint-cli2.cmd")
    if direct:
        return (direct,)
    preferred = "npx.cmd" if os.name == "nt" else "npx"
    npx = shutil.which(preferred) or shutil.which("npx") or shutil.which("npx.cmd")
    if npx:
        return (npx, "--no-install", "markdownlint-cli2")
    missing = "markdownlint-cli2.cmd" if os.name == "nt" else "markdownlint-cli2"
    return (missing,)


_DEFAULT_LINE = re.compile(
    r"^(?P<file>.*?):(?P<line>\d+)(?::(?P<column>\d+))?"
    r"(?: (?P<severity>warning|error))? "
    r"(?P<rule>MD\d+(?:/[^ ]+)*) (?P<message>.+)$"
)
_CONTEXT_SUFFIX = re.compile(r' \[Context: ".*"\]$')
_DETAIL_SUFFIX = re.compile(r" \[[^\]]+\]$")
_VERSION = re.compile(r"markdownlint-cli2 v(?P<version>\d+\.\d+\.\d+)")


class MarkdownlintCli2Adapter:
    validator_id = "markdownlint-cli2"

    def __init__(
        self,
        config_path: str | Path,
        *,
        command_prefix: Sequence[str] | None = None,
        validator_version: str = MARKDOWNLINT_CLI2_VERSION,
        timeout_seconds: int = 30,
    ):
        self.config_path = Path(config_path)
        self.command_prefix = tuple(command_prefix or _default_command())
        self.validator_version = validator_version
        self.timeout_seconds = int(timeout_seconds)

    def _base_execution(
        self,
        subject: Path,
        subject_hash: str,
        config_hash: str,
        *,
        execution_status: str,
        content_status: str,
        return_code: int | None,
        findings: tuple[ValidatorFinding, ...] = (),
        error_code: str | None = None,
        observed_validator_version: str | None = None,
    ) -> ValidatorExecution:
        return ValidatorExecution(
            validator_id=self.validator_id,
            validator_version=self.validator_version,
            observed_validator_version=observed_validator_version,
            config_sha256=config_hash,
            subject_path=str(subject),
            subject_sha256=subject_hash,
            execution_status=execution_status,
            content_status=content_status,
            return_code=return_code,
            findings=findings,
            error_code=error_code,
        )

    def _run(self, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [*self.command_prefix, *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=self.timeout_seconds,
            check=False,
        )

    def _probe_version(self) -> tuple[str | None, str | None]:
        try:
            proc = self._run(["--help"])
        except FileNotFoundError:
            return None, "EXECUTABLE_NOT_FOUND"
        except subprocess.TimeoutExpired:
            return None, "VERSION_PROBE_TIMEOUT"
        banner = "\n".join([proc.stdout or "", proc.stderr or ""])
        match = _VERSION.search(banner)
        if match:
            return match.group("version"), None
        if proc.returncode not in {0, 1}:
            return None, "VERSION_PROBE_FAILED"
        return None, "VERSION_UNRESOLVED"

    @staticmethod
    def _parse_findings(output: str, subject: Path) -> tuple[ValidatorFinding, ...]:
        findings: list[ValidatorFinding] = []
        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            match = _DEFAULT_LINE.match(line)
            if not match:
                continue
            message = match.group("message")
            message = _CONTEXT_SUFFIX.sub("", message)
            message = _DETAIL_SUFFIX.sub("", message)
            rule_names = match.group("rule").split("/")
            findings.append(
                ValidatorFinding(
                    finding_class="STRUCTURAL_ERROR",
                    severity=(match.group("severity") or "error").upper(),
                    rule_id=rule_names[0],
                    message=message,
                    subject_path=str(subject),
                    line=int(match.group("line")),
                    column=int(match.group("column")) if match.group("column") else None,
                )
            )
        return tuple(findings)

    def validate(self, subject_path: str | Path) -> ValidatorExecution:
        subject = Path(subject_path)
        if not subject.is_file():
            raise ValueError(f"subject_path is not a file: {subject}")
        if not self.config_path.is_file():
            raise ValueError(f"config_path is not a file: {self.config_path}")

        subject_hash = _sha256_file(subject)
        config_hash = _sha256_file(self.config_path)

        actual_version, probe_error = self._probe_version()
        if probe_error == "EXECUTABLE_NOT_FOUND":
            return self._base_execution(
                subject,
                subject_hash,
                config_hash,
                execution_status="UNAVAILABLE",
                content_status="NOT_EVALUATED",
                return_code=None,
                error_code=probe_error,
            )
        if probe_error:
            return self._base_execution(
                subject,
                subject_hash,
                config_hash,
                execution_status="TOOL_ERROR",
                content_status="NOT_EVALUATED",
                return_code=None,
                error_code=probe_error,
            )
        if actual_version != self.validator_version:
            return self._base_execution(
                subject,
                subject_hash,
                config_hash,
                execution_status="TOOL_ERROR",
                content_status="NOT_EVALUATED",
                return_code=None,
                error_code="VERSION_MISMATCH",
                observed_validator_version=actual_version,
            )

        before_hash = subject_hash
        try:
            proc = self._run([
                str(subject),
                "--config",
                str(self.config_path),
                "--no-globs",
            ])
        except FileNotFoundError:
            return self._base_execution(
                subject,
                subject_hash,
                config_hash,
                execution_status="UNAVAILABLE",
                content_status="NOT_EVALUATED",
                return_code=None,
                error_code="EXECUTABLE_NOT_FOUND",
                observed_validator_version=actual_version,
            )
        except subprocess.TimeoutExpired:
            return self._base_execution(
                subject,
                subject_hash,
                config_hash,
                execution_status="TOOL_ERROR",
                content_status="NOT_EVALUATED",
                return_code=None,
                error_code="VALIDATION_TIMEOUT",
                observed_validator_version=actual_version,
            )

        after_hash = _sha256_file(subject)
        if after_hash != before_hash:
            return self._base_execution(
                subject,
                before_hash,
                config_hash,
                execution_status="TOOL_ERROR",
                content_status="NOT_EVALUATED",
                return_code=proc.returncode,
                error_code="SOURCE_MUTATED",
                observed_validator_version=actual_version,
            )

        if proc.returncode not in {0, 1}:
            return self._base_execution(
                subject,
                subject_hash,
                config_hash,
                execution_status="TOOL_ERROR",
                content_status="NOT_EVALUATED",
                return_code=proc.returncode,
                error_code="VALIDATOR_EXECUTION_FAILED",
                observed_validator_version=actual_version,
            )

        combined = "\n".join([proc.stdout or "", proc.stderr or ""])
        findings = self._parse_findings(combined, subject)
        if proc.returncode == 1 and not findings:
            return self._base_execution(
                subject,
                subject_hash,
                config_hash,
                execution_status="TOOL_ERROR",
                content_status="NOT_EVALUATED",
                return_code=proc.returncode,
                error_code="UNPARSEABLE_FINDINGS",
                observed_validator_version=actual_version,
            )
        return self._base_execution(
            subject,
            subject_hash,
            config_hash,
            execution_status="SUCCEEDED",
            content_status="FINDINGS" if findings else "PASS",
            return_code=proc.returncode,
            findings=findings,
            observed_validator_version=actual_version,
        )
