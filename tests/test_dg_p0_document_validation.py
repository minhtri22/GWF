from pathlib import Path
import hashlib
import subprocess

from gwr.document_validation import MarkdownlintCli2Adapter, ValidatorExecution


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_execution_invariants():
    ValidatorExecution(
        validator_id="x",
        validator_version="1",
        observed_validator_version="1",
        config_sha256="c",
        subject_path="a.md",
        subject_sha256="s",
        execution_status="SUCCEEDED",
        content_status="PASS",
        return_code=0,
        findings=(),
    )


def test_parse_default_formatter_strips_context(tmp_path):
    subject = _write(tmp_path, "bad.md", "bad")
    line = f'{subject}:1:1 MD041/first-line-heading First line in a file should be a top-level heading [Context: "secret"]'
    findings = MarkdownlintCli2Adapter._parse_findings(line, subject)
    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "MD041"
    assert f.line == 1 and f.column == 1
    assert "secret" not in f.message


def test_validate_normalizes_findings_and_hashes(tmp_path, monkeypatch):
    subject = _write(tmp_path, "bad.md", "plain text")
    config = _write(tmp_path, "cfg.yaml", "config: {}\n")
    adapter = MarkdownlintCli2Adapter(config, command_prefix=("fake",))
    calls = []

    def fake_run(args):
        calls.append(list(args))
        if args == ["--help"]:
            return subprocess.CompletedProcess(args, 0, "markdownlint-cli2 v0.23.3 (markdownlint v0.41.1)\n", "")
        return subprocess.CompletedProcess(args, 1, "", f"{subject}:1 MD041/first-line-heading First line in a file should be a top-level heading\n")

    monkeypatch.setattr(adapter, "_run", fake_run)
    result = adapter.validate(subject)
    assert result.execution_status == "SUCCEEDED"
    assert result.content_status == "FINDINGS"
    assert result.return_code == 1
    assert result.observed_validator_version == "0.23.3"
    assert result.finding_count == 1
    assert result.subject_sha256 == hashlib.sha256(subject.read_bytes()).hexdigest()
    assert result.config_sha256 == hashlib.sha256(config.read_bytes()).hexdigest()
    assert "--fix" not in calls[-1]
    assert "--format" not in calls[-1]


def test_unavailable_is_not_document_failure(tmp_path):
    subject = _write(tmp_path, "good.md", "# Good\n")
    config = _write(tmp_path, "cfg.yaml", "config: {}\n")
    adapter = MarkdownlintCli2Adapter(config, command_prefix=("definitely-not-a-real-validator-p0",))
    result = adapter.validate(subject)
    assert result.execution_status == "UNAVAILABLE"
    assert result.content_status == "NOT_EVALUATED"
    assert result.error_code == "EXECUTABLE_NOT_FOUND"


def test_exit_2_is_tool_error(tmp_path, monkeypatch):
    subject = _write(tmp_path, "good.md", "# Good\n")
    config = _write(tmp_path, "cfg.yaml", "config: {}\n")
    adapter = MarkdownlintCli2Adapter(config, command_prefix=("fake",))

    def fake_run(args):
        if args == ["--help"]:
            return subprocess.CompletedProcess(args, 0, "markdownlint-cli2 v0.23.3\n", "")
        return subprocess.CompletedProcess(args, 2, "", "raw error with secret context")

    monkeypatch.setattr(adapter, "_run", fake_run)
    result = adapter.validate(subject)
    assert result.execution_status == "TOOL_ERROR"
    assert result.content_status == "NOT_EVALUATED"
    assert result.error_code == "VALIDATOR_EXECUTION_FAILED"
    assert "secret" not in str(result.to_dict())


def test_exit_1_without_parseable_findings_fails_closed(tmp_path, monkeypatch):
    subject = _write(tmp_path, "bad.md", "bad")
    config = _write(tmp_path, "cfg.yaml", "config: {}\n")
    adapter = MarkdownlintCli2Adapter(config, command_prefix=("fake",))

    def fake_run(args):
        if args == ["--help"]:
            return subprocess.CompletedProcess(args, 0, "markdownlint-cli2 v0.23.3\n", "")
        return subprocess.CompletedProcess(args, 1, "", "new upstream format that parser cannot read")

    monkeypatch.setattr(adapter, "_run", fake_run)
    result = adapter.validate(subject)
    assert result.execution_status == "TOOL_ERROR"
    assert result.error_code == "UNPARSEABLE_FINDINGS"


def test_windows_style_path_parses_column():
    subject = Path(r"C:\\work\\docs\\bad.md")
    line = r'C:\work\docs\bad.md:12:3 MD047/single-trailing-newline Files should end with a single newline character'
    findings = MarkdownlintCli2Adapter._parse_findings(line, subject)
    assert len(findings) == 1
    assert findings[0].line == 12
    assert findings[0].column == 3
    assert findings[0].rule_id == "MD047"


def test_version_mismatch_fails_closed(tmp_path, monkeypatch):
    subject = _write(tmp_path, "good.md", "# Good\n")
    config = _write(tmp_path, "cfg.yaml", "config: {}\n")
    adapter = MarkdownlintCli2Adapter(config, command_prefix=("fake",))

    def fake_run(args):
        return subprocess.CompletedProcess(args, 0, "markdownlint-cli2 v9.9.9\n", "")

    monkeypatch.setattr(adapter, "_run", fake_run)
    result = adapter.validate(subject)
    assert result.execution_status == "TOOL_ERROR"
    assert result.content_status == "NOT_EVALUATED"
    assert result.error_code == "VERSION_MISMATCH"
    assert result.observed_validator_version == "9.9.9"


def test_source_mutation_is_detected(tmp_path, monkeypatch):
    subject = _write(tmp_path, "good.md", "# Good\n")
    config = _write(tmp_path, "cfg.yaml", "config: {}\n")
    adapter = MarkdownlintCli2Adapter(config, command_prefix=("fake",))

    def fake_run(args):
        if args == ["--help"]:
            return subprocess.CompletedProcess(args, 0, "markdownlint-cli2 v0.23.3\n", "")
        subject.write_text("MUTATED\n", encoding="utf-8")
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(adapter, "_run", fake_run)
    result = adapter.validate(subject)
    assert result.execution_status == "TOOL_ERROR"
    assert result.content_status == "NOT_EVALUATED"
    assert result.error_code == "SOURCE_MUTATED"


def test_repeated_identical_output_normalizes_equally(tmp_path, monkeypatch):
    subject = _write(tmp_path, "bad.md", "bad")
    config = _write(tmp_path, "cfg.yaml", "config: {}\n")
    adapter = MarkdownlintCli2Adapter(config, command_prefix=("fake",))

    def fake_run(args):
        if args == ["--help"]:
            return subprocess.CompletedProcess(args, 0, "markdownlint-cli2 v0.23.3\n", "")
        return subprocess.CompletedProcess(args, 1, "", f"{subject}:1 MD041/first-line-heading First line in a file should be a top-level heading\n")

    monkeypatch.setattr(adapter, "_run", fake_run)
    assert adapter.validate(subject).to_dict() == adapter.validate(subject).to_dict()


def test_help_exit_2_with_version_banner_is_accepted(tmp_path, monkeypatch):
    subject = _write(tmp_path, "good.md", "# Good\n")
    config = _write(tmp_path, "cfg.yaml", "config: {}\n")
    adapter = MarkdownlintCli2Adapter(config, command_prefix=("fake",))

    def fake_run(args):
        if args == ["--help"]:
            return subprocess.CompletedProcess(args, 2, "markdownlint-cli2 v0.23.3\n", "")
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(adapter, "_run", fake_run)
    result = adapter.validate(subject)
    assert result.execution_status == "SUCCEEDED"
    assert result.content_status == "PASS"
    assert result.observed_validator_version == "0.23.3"
