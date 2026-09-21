from __future__ import annotations

from pathlib import Path

from gwr.document_validation import MarkdownlintCli2Adapter


def _write_fake(tmp_path: Path, body: str, name: str = "markdownlint-cli2") -> str:
    path = tmp_path / name
    path.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")
    path.chmod(0o755)
    return str(path)


def _cfg(tmp_path: Path) -> Path:
    path = tmp_path / ".markdownlint-cli2.jsonc"
    path.write_text('{"config":{"default":true}}\n', encoding="utf-8")
    return path


def _doc(tmp_path: Path, text: str = "# Good\n") -> Path:
    path = tmp_path / "doc.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_pass_records_hashes_and_version(tmp_path):
    exe = _write_fake(
        tmp_path,
        'import sys\nprint("markdownlint-cli2 v0.23.3 (markdownlint v0.41.1)") '
        'if "--help" in sys.argv else None\nsys.exit(0)\n',
    )
    cfg, doc = _cfg(tmp_path), _doc(tmp_path)
    result = MarkdownlintCli2Adapter(
        executable=exe,
        expected_version="0.23.3",
        config_path=cfg,
    ).validate(doc)

    assert result.execution_status == "SUCCEEDED"
    assert result.content_status == "PASS"
    assert result.validator_version == "0.23.3"
    assert len(result.subject_hash) == len(result.config_hash) == 64
    assert not result.findings


def test_findings_parse_line_and_column(tmp_path):
    exe = _write_fake(
        tmp_path,
        'import sys\n'
        'if "--help" in sys.argv: '
        'print("markdownlint-cli2 v0.23.3 (markdownlint v0.41.1)"); sys.exit(0)\n'
        'print("doc.md:2:3 MD009/no-trailing-spaces Trailing spaces '
        '[Expected: 0 or 2; Actual: 1]")\n'
        'sys.exit(1)\n',
    )
    result = MarkdownlintCli2Adapter(
        executable=exe,
        expected_version="0.23.3",
        config_path=_cfg(tmp_path),
    ).validate(_doc(tmp_path))

    assert result.execution_status == "SUCCEEDED"
    assert result.content_status == "FINDINGS"
    assert result.findings[0].rule_id == "MD009/no-trailing-spaces"
    assert result.findings[0].line == 2
    assert result.findings[0].column == 3


def test_unavailable_is_not_document_fail(tmp_path):
    result = MarkdownlintCli2Adapter(
        executable=str(tmp_path / "missing"),
        expected_version="0.23.3",
        config_path=_cfg(tmp_path),
    ).validate(_doc(tmp_path))

    assert result.execution_status == "UNAVAILABLE"
    assert result.content_status == "NOT_EVALUATED"
    assert result.error_code == "EXECUTABLE_NOT_FOUND"


def test_version_mismatch_fails_closed(tmp_path):
    exe = _write_fake(
        tmp_path,
        'import sys\nprint("markdownlint-cli2 v0.23.2 '
        '(markdownlint v0.41.0)")\nsys.exit(0)\n',
    )
    result = MarkdownlintCli2Adapter(
        executable=exe,
        expected_version="0.23.3",
        config_path=_cfg(tmp_path),
    ).validate(_doc(tmp_path))

    assert result.execution_status == "TOOL_ERROR"
    assert result.content_status == "NOT_EVALUATED"
    assert result.error_code == "VERSION_MISMATCH"


def test_source_mutation_is_detected(tmp_path):
    exe = _write_fake(
        tmp_path,
        'import sys, pathlib\n'
        'if "--help" in sys.argv: '
        'print("markdownlint-cli2 v0.23.3 (markdownlint v0.41.1)"); sys.exit(0)\n'
        'p=pathlib.Path(sys.argv[1]); '
        'p.write_text(p.read_text()+"mutated", encoding="utf-8"); sys.exit(0)\n',
    )
    doc = _doc(tmp_path)
    result = MarkdownlintCli2Adapter(
        executable=exe,
        expected_version="0.23.3",
        config_path=_cfg(tmp_path),
    ).validate(doc)

    assert result.execution_status == "TOOL_ERROR"
    assert result.error_code == "SOURCE_MUTATED"


def test_malformed_location_output_fails_closed(tmp_path):
    exe = _write_fake(
        tmp_path,
        'import sys\n'
        'if "--help" in sys.argv: '
        'print("markdownlint-cli2 v0.23.3 (markdownlint v0.41.1)"); sys.exit(0)\n'
        'print("doc.md:2 ??? malformed")\nsys.exit(1)\n',
    )
    result = MarkdownlintCli2Adapter(
        executable=exe,
        expected_version="0.23.3",
        config_path=_cfg(tmp_path),
    ).validate(_doc(tmp_path))

    assert result.execution_status == "TOOL_ERROR"
    assert result.content_status == "NOT_EVALUATED"
    assert result.error_code == "OUTPUT_PARSE_ERROR"


def test_windows_style_path_parser():
    findings = MarkdownlintCli2Adapter._parse_findings(
        r"C:\work\doc.md:12:7 MD013/line-length Line length"
    )
    assert findings is not None
    assert findings[0].line == 12
    assert findings[0].column == 7


def test_repeated_invocation_normalizes_identically(tmp_path):
    exe = _write_fake(
        tmp_path,
        'import sys\nprint("markdownlint-cli2 v0.23.3 (markdownlint v0.41.1)") '
        'if "--help" in sys.argv else None\nsys.exit(0)\n',
    )
    adapter = MarkdownlintCli2Adapter(
        executable=exe,
        expected_version="0.23.3",
        config_path=_cfg(tmp_path),
    )
    doc = _doc(tmp_path)

    assert adapter.validate(doc).to_dict() == adapter.validate(doc).to_dict()


def test_context_is_redacted_from_persisted_message():
    findings = MarkdownlintCli2Adapter._parse_findings(
        'doc.md:2 MD009/no-trailing-spaces Trailing spaces '
        '[Context: "SECRET_TOKEN=abc"]'
    )
    assert findings is not None
    assert findings[0].message == "Trailing spaces"
    assert "SECRET_TOKEN" not in findings[0].message
