from __future__ import annotations

import importlib.util
import json
import queue
import threading
import time
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / "scripts" / "g2e" / "p5a_d2s5_observable_client.py"
OBSERVABILITY = ROOT / "scripts" / "g2e" / "p5a_codex_observability.py"
ADMISSION = ROOT / "scripts" / "g2e" / "p5a_d2s5_scientific_admission.py"
RUNNER = ROOT / "scripts" / "g2e" / "p5a_d2s5_scientific_runner.py"
VERIFIER = ROOT / "scripts" / "g2e" / "p5a_d2s5_scientific_verify.py"
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_d2s5_scientific_oneclick.ps1"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S5_OBSERVABILITY_QUALIFIED_SUCCESSOR_PREIMPLEMENTATION.md"

OBS_BLOB = "b6d3c6fcb671dd166893edd46388c8d69dca9105"
CLIENT_BLOB = "72c77c1fbd1e2c20881723f18ef2f1435ded2b2b"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def fake_discovery(
    harness: str = "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b",
):
    required = {
        "initialize": True,
        "thread/start": True,
        "thread/resume": True,
        "turn/start": True,
        "item/started": True,
        "item/completed": True,
    }
    return {
        "schema": "G2E-P5A-CODEX-DISCOVERY-v1",
        "status": "D1_MINIMUM_QUALIFIED",
        "executable_sha256": harness,
        "app_server_help_exit_code": 0,
        "schema_generation_exit_code": 0,
        "schema_inventory_digest": "1" * 64,
        "generated_schema_files": [
            {"path": "v2/TurnStartParams.json", "sha256": "2" * 64, "size": 100}
        ],
        "required_protocol_tokens": required,
        "optional_protocol_tokens": {"sessionId": True},
        "initialize_handshake": {"success": True},
        "functional_task_executed": False,
        "secrets_persisted": False,
    }


def _bare_client(module, tmp_path: Path):
    client = object.__new__(module.RpcClient)
    client.q = queue.Queue()
    client.protocol_path = tmp_path / "protocol.jsonl"
    client.stderr_path = tmp_path / "stderr.jsonl"
    client.unexpected_server_requests = []
    client.pending_notifications = []
    return client


def _read_records(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_client_enforces_exact_oq1_blob_and_delegates_recorder():
    module = _load(CLIENT, "d2s5_client_binding")
    assert module.OBSERVABILITY_GIT_BLOB == OBS_BLOB
    assert module.git_blob_sha1(OBSERVABILITY) == OBS_BLOB
    source = CLIENT.read_text(encoding="utf-8")
    assert "OBSERVABILITY.project_protocol_message(raw, ts)" in source


def test_live_recorder_preserves_error_notification_and_redacts_secret(tmp_path, monkeypatch):
    module = _load(CLIENT, "d2s5_client_error")
    client = _bare_client(module, tmp_path)
    monkeypatch.setenv("USERPROFILE", r"C:\Users\Alice")

    message = {
        "method": "error",
        "params": {
            "threadId": "thread-1",
            "turnId": "turn-1",
            "willRetry": False,
            "error": {
                "message": (
                    r"failed under C:\Users\Alice\repo "
                    "Bearer abcdefghijklmnop"
                ),
                "codexErrorInfo": {
                    "responseStreamDisconnected": {"httpStatusCode": 503}
                },
                "additionalDetails": "api_key=TOPSECRET_VALUE request=req-7",
                "misalignment": None,
            },
        },
    }
    raw = json.dumps(message, separators=(",", ":"), sort_keys=True)
    parsed = client._record_stdout(raw, 123.0)
    assert parsed == message

    records = _read_records(client.protocol_path)
    assert len(records) == 1
    rec = records[0]
    ev = rec["terminalErrorEvidence"]

    assert rec["method"] == "error"
    assert ev["source"] == "errorNotification"
    assert ev["threadId"] == "thread-1"
    assert ev["turnId"] == "turn-1"
    assert ev["willRetry"] is False
    assert ev["error"]["codexErrorInfo"] == {
        "responseStreamDisconnected": {"httpStatusCode": 503}
    }
    assert ev["error"]["message"]["redactionApplied"] is True
    assert ev["error"]["additionalDetails"]["redactionApplied"] is True

    rendered = json.dumps(rec, sort_keys=True)
    assert "abcdefghijk" not in rendered
    assert "TOPSECRET_VALUE" not in rendered
    assert "Alice" not in rendered
    assert "<USER_HOME>" in rendered
    assert "<REDACTED_SECRET>" in rendered


def test_live_recorder_preserves_failed_turn_completed_error(tmp_path):
    module = _load(CLIENT, "d2s5_client_failed_turn")
    client = _bare_client(module, tmp_path)

    message = {
        "method": "turn/completed",
        "params": {
            "threadId": "thread-2",
            "turn": {
                "id": "turn-2",
                "items": [],
                "status": "failed",
                "error": {
                    "message": "sandbox denied",
                    "codexErrorInfo": "sandboxError",
                    "additionalDetails": "write denied",
                    "misalignment": None,
                },
            },
        },
    }
    raw = json.dumps(message, separators=(",", ":"), sort_keys=True)
    client._record_stdout(raw, 124.0)
    rec = _read_records(client.protocol_path)[0]
    ev = rec["terminalErrorEvidence"]

    assert ev["source"] == "turnCompleted"
    assert ev["threadId"] == "thread-2"
    assert ev["turnId"] == "turn-2"
    assert ev["status"] == "failed"
    assert ev["error"]["message"]["text"] == "sandbox denied"
    assert ev["error"]["codexErrorInfo"] == "sandboxError"
    assert ev["error"]["additionalDetails"]["text"] == "write denied"
    assert len(rec["rawSha256"]) == 64
    assert rec["length"] == len(raw)


def test_live_recorder_keeps_unrelated_notification_payload_minimal(tmp_path):
    module = _load(CLIENT, "d2s5_client_minimal")
    client = _bare_client(module, tmp_path)

    message = {
        "method": "item/completed",
        "params": {
            "threadId": "thread",
            "item": {"id": "x", "text": "DO_NOT_PERSIST_PAYLOAD"},
        },
    }
    client._record_stdout(
        json.dumps(message, separators=(",", ":"), sort_keys=True),
        125.0,
    )
    rec = _read_records(client.protocol_path)[0]
    rendered = json.dumps(rec, sort_keys=True)
    assert rec["method"] == "item/completed"
    assert "terminalErrorEvidence" not in rec
    assert "params" not in rec
    assert "DO_NOT_PERSIST_PAYLOAD" not in rendered


def test_queue_empty_remains_normalized_to_timeout(tmp_path):
    module = _load(CLIENT, "d2s5_client_timeout")
    client = _bare_client(module, tmp_path)
    with pytest.raises(TimeoutError):
        client.next_message(0.02)


def test_delayed_terminal_still_survives_multiple_empty_polls(tmp_path):
    client_module = _load(CLIENT, "d2s5_client_delayed")
    runner = _load(RUNNER, "d2s5_runner_delayed")
    client = _bare_client(client_module, tmp_path)
    turn_id = "synthetic-turn"

    def delayed():
        time.sleep(2.2)
        message = {
            "method": "turn/completed",
            "params": {
                "threadId": "synthetic-thread",
                "turn": {
                    "id": turn_id,
                    "items": [],
                    "status": "completed",
                    "error": None,
                },
            },
        }
        client.q.put(("stdout", json.dumps(message), time.time()))

    thread = threading.Thread(target=delayed, daemon=True)
    thread.start()
    result = runner.wait_for_turn(client, turn_id, 4.0)
    thread.join(timeout=1)

    assert result["terminal"] is True
    assert result["timeout"] is False
    assert result["completion"]["method"] == "turn/completed"


def test_admission_is_deterministic_and_binds_observability():
    module = _load(ADMISSION, "d2s5_admission")
    first = module.build_final_admission(fake_discovery())
    second = module.build_final_admission(fake_discovery())
    assert first == second
    module.verify_final_admission(first, fake_discovery())

    assert first["study_id"] == "p5a-d2s5-observability-qualified-functional-successor"
    assert first["attempt_id"] == "p5a-d2s5-p5-fx-001-attempt-001"
    config = first["execution_config"]
    assert config["observable_client_git_blob"] == CLIENT_BLOB
    assert config["observability_git_blob"] == OBS_BLOB
    assert config["turn_timeout_seconds"] == 90
    assert config["max_invalid_replacement_attempts"] == 0
    assert first["authorization"]["retry_authorized"] is False
    assert first["authorization"]["automatic_retry_authorized"] is False
    assert first["authorization"]["exact_scientific_attempts_authorized_after_lock"] == 1


def test_manifest_does_not_prematurely_promote_capability():
    module = _load(ADMISSION, "d2s5_admission_caps")
    pack = module.build_final_admission(fake_discovery())
    caps = {x["capability_id"]: x["available"] for x in pack["manifest"]["capabilities"]}
    assert caps["repository_read"] is False
    assert caps["repository_write"] is False


def test_runner_binds_exact_client_and_observability_and_one_turn_path():
    source = RUNNER.read_text(encoding="utf-8")
    assert 'STUDY_ID = "p5a-d2s5-observability-qualified-functional-successor"' in source
    assert 'ATTEMPT_ID = "p5a-d2s5-p5-fx-001-attempt-001"' in source
    assert f'PREFLIGHT_MODULE_GIT_BLOB = "{CLIENT_BLOB}"' in source
    assert f'OBSERVABILITY_GIT_BLOB = "{OBS_BLOB}"' in source
    assert "p5a_d2s5_observable_client.py" in source
    assert source.count('"method": "turn/start"') == 1
    assert source.count("P5A_D2S5_TURN_START_SENT.marker") == 1
    assert "TURN_TIMEOUT_S = 90.0" in source

    marker_index = source.index("fsync_text(marker_path, marker_text)")
    send_index = source.index("client.send(request)")
    assert marker_index < send_index
    assert 'evidence["scientific_attempt_consumed"] = True' in source[marker_index:send_index]


def test_verifier_accepts_matching_failed_turn_projection_and_rejects_missing_projection():
    verifier = _load(VERIFIER, "d2s5_verifier_observability")

    evidence = {
        "thread_id": "thread-x",
        "turn_id": "turn-x",
        "terminal_status": "failed",
    }
    good = [
        {
            "method": "error",
            "rawSha256": "a" * 64,
            "length": 100,
            "terminalErrorEvidence": {
                "source": "errorNotification",
                "threadId": "thread-x",
                "turnId": "turn-x",
                "willRetry": False,
                "error": {
                    "message": {
                        "text": "provider failed",
                        "rawSha256": "b" * 64,
                        "rawLength": 15,
                        "redactionApplied": False,
                    },
                    "codexErrorInfo": "serverOverloaded",
                    "additionalDetails": None,
                    "misalignment": None,
                },
            },
        },
        {
            "method": "turn/completed",
            "rawSha256": "c" * 64,
            "length": 120,
            "terminalErrorEvidence": {
                "source": "turnCompleted",
                "threadId": "thread-x",
                "turnId": "turn-x",
                "status": "failed",
                "error": {
                    "message": {
                        "text": "provider failed",
                        "rawSha256": "d" * 64,
                        "rawLength": 15,
                        "redactionApplied": False,
                    },
                    "codexErrorInfo": "serverOverloaded",
                    "additionalDetails": None,
                    "misalignment": None,
                },
            },
        },
    ]
    result = verifier.verify_observability_contract(good, evidence)
    assert result["required"] is True
    assert result["contract_valid"] is True
    assert result["mechanism_bearing_projection_present"] is True

    bad = [
        {
            "method": "turn/completed",
            "rawSha256": "e" * 64,
            "length": 50,
        }
    ]
    result_bad = verifier.verify_observability_contract(bad, evidence)
    assert result_bad["required"] is True
    assert result_bad["contract_valid"] is False


def test_verifier_remains_verdict_neutral_and_observability_is_evidence_integrity():
    verifier = _load(VERIFIER, "d2s5_verifier_binding")
    assert verifier.OBSERVABLE_CLIENT_GIT_BLOB == CLIENT_BLOB
    assert verifier.OBSERVABILITY_GIT_BLOB == OBS_BLOB
    source = VERIFIER.read_text(encoding="utf-8")
    assert '"verifier_assigns_scientific_verdict": False' in source
    assert 'observability_checks["contract_valid"]' in source
    assert "result_schema_valid" in source
    assert "result_values_correct" in source


def test_oneclick_is_fresh_single_shot_observability_bound_and_cleanup_protected():
    source = ONECLICK.read_text(encoding="utf-8")
    assert "P5A-D2S5-SCIENCE-001" in source
    assert "SCIENTIFIC_ROOT_ALREADY_EXISTS_NO_RETRY" in source
    assert "P5A_D2S5_SCIENTIFIC_EXECUTION_LOCK.json" in source
    assert 'HEAD:scripts/g2e/p5a_codex_observability.py' in source
    assert 'OBSERVABILITY_BLOB_DRIFT' in source
    assert "retry_authorized" in source
    assert "automatic_retry_authorized" in source

    start = source.index("# PROTECTED_SCIENTIFIC_VHDX_BODY_START")
    end = source.index("# PROTECTED_SCIENTIFIC_VHDX_BODY_END")
    protected = source[start:end]
    assert "Dismount-DiskImage -ImagePath $VhdxPath" in protected
    assert "attached_after_cleanup" in protected
    assert "exit " not in protected
    assert "Remove-Item -LiteralPath $VhdxPath" not in source


def test_spec_keeps_science_frozen_and_execution_unauthorized_until_lock():
    normalized = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "Sole prospective measurement change" in normalized
    assert "turn wall-clock timeout = 90 seconds" in normalized
    assert "retry budget = 0" in normalized
    assert "Observability does not convert a terminal `failed` turn into substantive FAIL or PASS." in normalized
    assert "MODEL EXECUTION NOT AUTHORIZED" in normalized
