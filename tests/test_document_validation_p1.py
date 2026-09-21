from __future__ import annotations

import json
from pathlib import Path

from gwr.document_validation import ValeAdapter


def _write_fake(tmp_path: Path, body: str, name: str = "vale") -> str:
    path = tmp_path / name
    path.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")
    path.chmod(0o755)
    return str(path)


def _config(tmp_path: Path) -> tuple[Path, Path]:
    styles = tmp_path / "styles"
    rule_dir = styles / "GWF"
    rule_dir.mkdir(parents=True)
    cfg = tmp_path / ".vale.ini"
    cfg.write_text(
        "StylesPath = styles\nMinAlertLevel = suggestion\n\n"
        "[*.md]\nBasedOnStyles = GWF\n",
        encoding="utf-8",
    )
    (rule_dir / "Terminology.yml").write_text(
        "extends: substitution\n"
        'message: "Use \'%s\' instead of \'%s\'."\n'
        "level: error\n"
        "swap:\n"
        "  'ARC fallback layer': 'ARC Agent Pool / Worker Fabric transport'\n",
        encoding="utf-8",
    )
    return cfg, styles


def _doc(tmp_path: Path, text: str = "# Good\n\nARC is a transport.\n") -> Path:
    path = tmp_path / "doc.md"
    path.write_text(text, encoding="utf-8")
    return path


def _alert(match: str = "ARC fallback layer", severity: str = "error") -> str:
    return json.dumps(
        {
            "/tmp/doc.md": [
                {
                    "Span": [1, 18],
                    "Check": "GWF.Terminology",
                    "Message": (
                        "Use 'ARC Agent Pool / Worker Fabric transport' "
                        "instead of 'ARC fallback layer'."
                    ),
                    "Severity": severity,
                    "Match": match,
                    "Line": 3,
                }
            ]
        }
    )


def test_vale_pass_records_version_and_config_hash(tmp_path):
    exe = _write_fake(
        tmp_path,
        'import sys\n'
        'if "--version" in sys.argv: print("vale version 3.22.0"); sys.exit(0)\n'
        'print("{}"); sys.exit(0)\n',
    )
    cfg, styles = _config(tmp_path)
    result = ValeAdapter(
        executable=exe, expected_version="3.22.0",
        config_path=cfg, styles_path=styles,
    ).validate(_doc(tmp_path))
    assert result.execution_status == "SUCCEEDED"
    assert result.content_status == "PASS"
    assert result.validator_version == "3.22.0"
    assert len(result.subject_hash) == len(result.config_hash) == 64


def test_vale_finding_preserves_rule_severity_location_but_redacts_match(tmp_path):
    payload = _alert()
    exe = _write_fake(
        tmp_path,
        'import sys\n'
        'if "--version" in sys.argv: print("vale version 3.22.0"); sys.exit(0)\n'
        f'print({payload!r}); sys.exit(1)\n',
    )
    cfg, styles = _config(tmp_path)
    result = ValeAdapter(
        executable=exe, expected_version="3.22.0",
        config_path=cfg, styles_path=styles,
    ).validate(_doc(tmp_path, "# Drift\n\nARC fallback layer handles workers.\n"))
    assert result.execution_status == "SUCCEEDED"
    assert result.content_status == "FINDINGS"
    finding = result.findings[0]
    assert finding.rule_id == "GWF.Terminology"
    assert finding.severity == "ERROR"
    assert finding.line == 3
    assert finding.column == 1
    assert "ARC fallback layer" not in finding.message
    assert "<redacted-match>" in finding.message


def test_vale_warning_findings_can_exit_zero(tmp_path):
    payload = _alert(severity="warning")
    exe = _write_fake(
        tmp_path,
        'import sys\n'
        'if "--version" in sys.argv: print("vale version 3.22.0"); sys.exit(0)\n'
        f'print({payload!r}); sys.exit(0)\n',
    )
    cfg, styles = _config(tmp_path)
    result = ValeAdapter(
        executable=exe, expected_version="3.22.0",
        config_path=cfg, styles_path=styles,
    ).validate(_doc(tmp_path))
    assert result.execution_status == "SUCCEEDED"
    assert result.content_status == "FINDINGS"
    assert result.findings[0].severity == "WARNING"


def test_vale_unavailable_is_not_document_fail(tmp_path):
    cfg, styles = _config(tmp_path)
    result = ValeAdapter(
        executable=str(tmp_path / "missing-vale"), expected_version="3.22.0",
        config_path=cfg, styles_path=styles,
    ).validate(_doc(tmp_path))
    assert result.execution_status == "UNAVAILABLE"
    assert result.content_status == "NOT_EVALUATED"
    assert result.error_code == "EXECUTABLE_NOT_FOUND"


def test_vale_version_mismatch_fails_closed(tmp_path):
    exe = _write_fake(tmp_path, 'import sys\nprint("vale version 3.21.0"); sys.exit(0)\n')
    cfg, styles = _config(tmp_path)
    result = ValeAdapter(
        executable=exe, expected_version="3.22.0",
        config_path=cfg, styles_path=styles,
    ).validate(_doc(tmp_path))
    assert result.execution_status == "TOOL_ERROR"
    assert result.content_status == "NOT_EVALUATED"
    assert result.error_code == "VERSION_MISMATCH"


def test_vale_malformed_json_fails_closed(tmp_path):
    exe = _write_fake(
        tmp_path,
        'import sys\n'
        'if "--version" in sys.argv: print("vale version 3.22.0"); sys.exit(0)\n'
        'print("not-json"); sys.exit(1)\n',
    )
    cfg, styles = _config(tmp_path)
    result = ValeAdapter(
        executable=exe, expected_version="3.22.0",
        config_path=cfg, styles_path=styles,
    ).validate(_doc(tmp_path))
    assert result.execution_status == "TOOL_ERROR"
    assert result.content_status == "NOT_EVALUATED"
    assert result.error_code == "OUTPUT_PARSE_ERROR"


def test_vale_source_mutation_is_detected(tmp_path):
    exe = _write_fake(
        tmp_path,
        'import pathlib, sys\n'
        'if "--version" in sys.argv: print("vale version 3.22.0"); sys.exit(0)\n'
        'p=pathlib.Path(sys.argv[-1]); '
        'p.write_text(p.read_text()+"mutated", encoding="utf-8"); '
        'print("{}"); sys.exit(0)\n',
    )
    cfg, styles = _config(tmp_path)
    doc = _doc(tmp_path)
    result = ValeAdapter(
        executable=exe, expected_version="3.22.0",
        config_path=cfg, styles_path=styles,
    ).validate(doc)
    assert result.execution_status == "TOOL_ERROR"
    assert result.error_code == "SOURCE_MUTATED"


def test_vale_exit_one_without_findings_fails_closed(tmp_path):
    exe = _write_fake(
        tmp_path,
        'import sys\n'
        'if "--version" in sys.argv: print("vale version 3.22.0"); sys.exit(0)\n'
        'print("{}"); sys.exit(1)\n',
    )
    cfg, styles = _config(tmp_path)
    result = ValeAdapter(
        executable=exe, expected_version="3.22.0",
        config_path=cfg, styles_path=styles,
    ).validate(_doc(tmp_path))
    assert result.execution_status == "TOOL_ERROR"
    assert result.error_code == "FINDINGS_MISSING"


def test_vale_config_hash_changes_when_vocabulary_changes(tmp_path):
    cfg, styles = _config(tmp_path)
    adapter = ValeAdapter(
        executable="vale", expected_version="3.22.0",
        config_path=cfg, styles_path=styles,
    )
    before = adapter._config_hash()
    rule = styles / "GWF" / "Terminology.yml"
    rule.write_text(rule.read_text(encoding="utf-8") + "# revision\n", encoding="utf-8")
    assert before != adapter._config_hash()
