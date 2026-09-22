from __future__ import annotations

import importlib.util
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXTRACTOR = ROOT / "scripts" / "g2e" / "p5a_d2s4_recover_persisted_turn_error.py"
WRAPPER = ROOT / "scripts" / "g2e" / "p5a_d2s4_collect_persisted_turn_error.ps1"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S4_PERSISTED_TURN_ERROR_RECOVERY_SPEC.md"

THREAD_ID = "01a0c9af-d509-7203-9608-06304738b12e"
TURN_ID = "01a0c9af-d523-72f3-84fa-a575e91076b6"


def _run_extractor(codex_home: Path, output: Path) -> dict:
    subprocess.run(
        [
            sys.executable,
            str(EXTRACTOR),
            "--codex-home",
            str(codex_home),
            "--output-dir",
            str(output),
        ],
        check=True,
        cwd=ROOT,
    )
    return json.loads(
        (output / "P5A_D2S4_PERSISTED_TURN_ERROR_RECOVERY.json").read_text(
            encoding="utf-8"
        )
    )


def test_recovery_extracts_exact_turn_error_and_redacts_secrets(tmp_path: Path):
    home = tmp_path / "codex-home"
    sessions = home / "sessions" / "2026" / "09" / "22"
    sessions.mkdir(parents=True)
    logs = home / "log"
    logs.mkdir(parents=True)

    rollout = sessions / "rollout-test.jsonl"
    rows = [
        {
            "type": "turn_event",
            "threadId": THREAD_ID,
            "turnId": TURN_ID,
            "status": "failed",
            "error": {
                "message": "provider request failed",
                "codexErrorInfo": "RateLimitExceeded",
                "additionalDetails": "Bearer SECRET_TOKEN_SHOULD_NOT_LEAK",
            },
        },
        {
            "type": "turn_event",
            "threadId": "unrelated-thread",
            "turnId": "unrelated-turn",
            "status": "completed",
            "message": "unrelated content",
        },
    ]
    rollout.write_text(
        "\n".join(json.dumps(x) for x in rows) + "\n",
        encoding="utf-8",
    )

    (home / "auth.json").write_text(
        json.dumps({"access_token": "TOP_SECRET_AUTH_VALUE"}),
        encoding="utf-8",
    )
    (home / "config.toml").write_text(
        'api_key = "TOP_SECRET_CONFIG_VALUE"\n',
        encoding="utf-8",
    )
    (logs / "app.log").write_text(
        f"turn={TURN_ID} error=provider_failure token=TOP_SECRET_LOG_TOKEN\n",
        encoding="utf-8",
    )

    db = home / "state.db"
    con = sqlite3.connect(db)
    con.execute(
        "create table turns (turn_id text, thread_id text, status text, error text, secret text)"
    )
    con.execute(
        "insert into turns values (?, ?, ?, ?, ?)",
        (
            TURN_ID,
            THREAD_ID,
            "failed",
            '{"message":"sandbox denied","code":"PermissionDenied"}',
            "TOP_SECRET_DB_VALUE",
        ),
    )
    con.commit()
    con.close()

    out = tmp_path / "out"
    result = _run_extractor(home, out)
    rendered = json.dumps(result, sort_keys=True)

    assert result["collection_mode"] == "READ_ONLY_EXISTING_LOCAL_EVIDENCE"
    assert result["codex_started"] is False
    assert result["rpc_sent"] is False
    assert result["vhdx_mounted"] is False
    assert result["scientific_attempt_retried"] is False
    assert result["forbidden_files_read"] is False
    assert result["text_match_count"] >= 2
    assert result["sqlite_match_count"] >= 1

    assert "provider request failed" in rendered
    assert "RateLimitExceeded" in rendered
    assert "sandbox denied" in rendered
    assert "PermissionDenied" in rendered

    assert "TOP_SECRET_AUTH_VALUE" not in rendered
    assert "TOP_SECRET_CONFIG_VALUE" not in rendered
    assert "TOP_SECRET_DB_VALUE" not in rendered
    assert "SECRET_TOKEN_SHOULD_NOT_LEAK" not in rendered

    scanned = json.dumps(
        {
            "text": result["scanned_text_files"],
            "sqlite": result["scanned_sqlite_files"],
        }
    )
    assert "auth.json" not in scanned
    assert "config.toml" not in scanned


def test_extractor_is_static_read_only_and_has_no_execution_transport():
    source = EXTRACTOR.read_text(encoding="utf-8")
    forbidden = [
        "subprocess.",
        "requests.",
        "urllib.request",
        "socket.",
        "os.system",
        "Popen(",
        "turn/start",
        "thread/start",
    ]
    for token in forbidden:
        assert token not in source

    assert 'mode=ro&immutable=1' in source
    assert "sessions" in source
    assert "archived_sessions" in source
    assert "log" in source
    assert "auth.json" in source
    assert "config.toml" in source
    assert "forbidden_files_read" in source


def test_wrapper_is_single_read_only_collection_path():
    source = WRAPPER.read_text(encoding="utf-8")
    # Forbidden words may appear inside the wrapper's own InfrastructureSelfTest
    # deny-list. Prohibit executable call shapes rather than deny-list literals.
    forbidden_execution_shapes = [
        "& $CodexExe",
        "Start-Process -",
        "Mount-DiskImage -",
        "Dismount-DiskImage -",
        "diskpart /",
        "Invoke-WebRequest -",
    ]
    for token in forbidden_execution_shapes:
        assert token not in source

    assert "P5A-D2S4-SCIENCE-001" in source
    assert "P5A-D2S4-PERSISTED-ERROR-RECOVERY" in source
    assert "RECOVERY_OUTPUT_ROOT_ALREADY_EXISTS" in source
    assert "P5A_D2S4_PERSISTED_TURN_ERROR_RECOVERY_LOCK.json" in source
    assert "CODEX      : NOT STARTED" in source
    assert "RPC        : NONE" in source
    assert "VHDX       : NOT MOUNTED" in source
    assert "RETRY      : FALSE" in source


def test_recovery_spec_is_postclosure_and_no_retry():
    text = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "POST-CLOSURE / READ-ONLY / NO SCIENTIFIC RETRY" in text
    assert "MUST NOT read, copy, emit, or hash as evidence" in text
    assert "auth.json" in text
    assert "config.toml" in text
    assert "No successor execution is authorized" in text
