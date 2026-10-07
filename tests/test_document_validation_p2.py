from __future__ import annotations

import json
from pathlib import Path
import os
import sys

from gwr.document_validation import LycheeAdapter


def _write_python_fake(tmp_path: Path, name: str, body: str) -> str:
    script = tmp_path / f"{name}.py"
    script.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")
    if os.name == "nt":
        wrapper = tmp_path / f"{name}.cmd"
        wrapper.write_text(
            f'@"{sys.executable}" "{script}" %*\r\n',
            encoding="utf-8",
        )
        return str(wrapper)
    script.chmod(0o755)
    return str(script)


def _config(tmp_path: Path) -> Path:
    path = tmp_path / "lychee.toml"
    path.write_text(
        'format = "json"\nmode = "plain"\nno_progress = true\ncache = false\nmax_retries = 0\ntimeout = 5\n',
        encoding="utf-8",
    )
    return path


def _subject(tmp_path: Path, name: str = "doc.md") -> Path:
    path = tmp_path / name
    path.write_text("# Fixture\n", encoding="utf-8")
    return path


def _fake_lychee(
    tmp_path: Path,
    report: dict,
    *,
    code: int = 0,
    version: str = "0.24.2",
    mutate: bool = False,
    stderr_text: str = "",
) -> str:
    body = f"""import pathlib
import sys
if "--version" in sys.argv:
    print("lychee {version}")
    raise SystemExit(0)
subject = pathlib.Path(sys.argv[-1])
if {mutate!r}:
    subject.write_text(subject.read_text(encoding="utf-8") + "mutated", encoding="utf-8")
print({json.dumps(report)!r})
if {stderr_text!r}:
    print({stderr_text!r}, file=sys.stderr)
raise SystemExit({code})
"""
    return _write_python_fake(tmp_path, "lychee", body)


def _clean_report() -> dict:
    return {"errors": 0, "timeouts": 0, "error_map": {}, "timeout_map": {}}


def test_lychee_clean_fixture_passes(tmp_path: Path):
    adapter = LycheeAdapter(
        executable=_fake_lychee(tmp_path, _clean_report()),
        expected_version="0.24.2",
        config_path=_config(tmp_path),
    )
    result = adapter.validate(_subject(tmp_path))
    assert result.execution_status == "SUCCEEDED"
    assert result.content_status == "PASS"
    assert result.findings == ()


def test_lychee_internal_broken_link_is_content_finding(tmp_path: Path):
    report = {
        "errors": 1,
        "timeouts": 0,
        "error_map": {
            "doc.md": [{
                "url": "file:///workspace/missing.md",
                "status": {"text": "Cannot find file"},
                "span": {"line": 3, "column": 7},
            }]
        },
        "timeout_map": {},
    }
    adapter = LycheeAdapter(
        executable=_fake_lychee(tmp_path, report, code=2),
        expected_version="0.24.2",
        config_path=_config(tmp_path),
    )
    result = adapter.validate(_subject(tmp_path))
    assert result.execution_status == "SUCCEEDED"
    assert result.content_status == "FINDINGS"
    assert result.findings[0].rule_id == "LYCHEE.INTERNAL_BROKEN"
    assert result.findings[0].line == 3
    assert "missing.md" not in result.findings[0].message


def test_lychee_external_http_error_is_distinguishable(tmp_path: Path):
    report = {
        "errors": 1,
        "timeouts": 0,
        "error_map": {
            "doc.md": [{
                "url": "https://example.invalid/private?token=SECRET",
                "status": {"text": "404 Not Found", "code": 404},
                "span": {"line": 4, "column": 2},
            }]
        },
        "timeout_map": {},
    }
    adapter = LycheeAdapter(
        executable=_fake_lychee(tmp_path, report, code=2),
        expected_version="0.24.2",
        config_path=_config(tmp_path),
    )
    result = adapter.validate(_subject(tmp_path))
    assert result.execution_status == "SUCCEEDED"
    assert result.content_status == "FINDINGS"
    assert result.findings[0].rule_id == "LYCHEE.EXTERNAL_BROKEN"
    assert result.findings[0].message == "Broken external link (HTTP 404)"
    assert "SECRET" not in result.findings[0].message


def test_lychee_network_error_is_tool_error_not_broken_link(tmp_path: Path):
    report = {
        "errors": 1,
        "timeouts": 0,
        "error_map": {
            "doc.md": [{
                "url": "https://example.invalid/",
                "status": {"text": "Network error", "details": "connection refused"},
                "span": {"line": 2, "column": 1},
            }]
        },
        "timeout_map": {},
    }
    adapter = LycheeAdapter(
        executable=_fake_lychee(tmp_path, report, code=2),
        expected_version="0.24.2",
        config_path=_config(tmp_path),
    )
    result = adapter.validate(_subject(tmp_path))
    assert result.execution_status == "TOOL_ERROR"
    assert result.content_status == "NOT_EVALUATED"
    assert result.error_code == "NETWORK_FAILURE"
    assert result.findings == ()


def test_lychee_timeout_is_tool_error(tmp_path: Path):
    report = {
        "errors": 0,
        "timeouts": 1,
        "error_map": {},
        "timeout_map": {"doc.md": [{"url": "https://example.invalid/slow"}]},
    }
    adapter = LycheeAdapter(
        executable=_fake_lychee(tmp_path, report, code=2),
        expected_version="0.24.2",
        config_path=_config(tmp_path),
    )
    result = adapter.validate(_subject(tmp_path))
    assert result.execution_status == "TOOL_ERROR"
    assert result.content_status == "NOT_EVALUATED"
    assert result.error_code == "NETWORK_FAILURE"


def test_lychee_missing_executable_is_unavailable(tmp_path: Path):
    adapter = LycheeAdapter(
        executable=str(tmp_path / "missing-lychee"),
        expected_version="0.24.2",
        config_path=_config(tmp_path),
    )
    result = adapter.validate(_subject(tmp_path))
    assert result.execution_status == "UNAVAILABLE"
    assert result.content_status == "NOT_EVALUATED"
    assert result.error_code == "EXECUTABLE_NOT_FOUND"


def test_lychee_version_mismatch_fails_closed(tmp_path: Path):
    adapter = LycheeAdapter(
        executable=_fake_lychee(tmp_path, _clean_report(), version="0.24.1"),
        expected_version="0.24.2",
        config_path=_config(tmp_path),
    )
    result = adapter.validate(_subject(tmp_path))
    assert result.execution_status == "TOOL_ERROR"
    assert result.error_code == "VERSION_MISMATCH"


def test_lychee_malformed_json_fails_closed(tmp_path: Path):
    exe = _write_python_fake(
        tmp_path,
        "lychee-malformed",
        'import sys\n'
        'print("lychee 0.24.2") if "--version" in sys.argv else print("not-json")\n',
    )
    adapter = LycheeAdapter(
        executable=exe,
        expected_version="0.24.2",
        config_path=_config(tmp_path),
    )
    result = adapter.validate(_subject(tmp_path))
    assert result.execution_status == "TOOL_ERROR"
    assert result.error_code == "OUTPUT_PARSE_ERROR"


def test_lychee_detects_source_mutation(tmp_path: Path):
    adapter = LycheeAdapter(
        executable=_fake_lychee(tmp_path, _clean_report(), mutate=True),
        expected_version="0.24.2",
        config_path=_config(tmp_path),
    )
    result = adapter.validate(_subject(tmp_path))
    assert result.execution_status == "TOOL_ERROR"
    assert result.error_code == "SOURCE_MUTATED"


def test_lychee_config_hash_and_stderr_are_deterministic(tmp_path: Path):
    config = _config(tmp_path)
    adapter = LycheeAdapter(
        executable=_fake_lychee(tmp_path, _clean_report(), stderr_text="Hint: human-only output"),
        expected_version="0.24.2",
        config_path=config,
    )
    subject = _subject(tmp_path)
    first = adapter.validate(subject)
    second = adapter.validate(subject)
    assert first.to_dict() == second.to_dict()
    before_hash = first.config_hash
    config.write_text(config.read_text(encoding="utf-8") + "# revision\n", encoding="utf-8")
    third = adapter.validate(subject)
    assert third.config_hash != before_hash
