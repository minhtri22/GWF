from __future__ import annotations

import importlib.util
import json
import queue
import threading
import time
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / "scripts" / "g2e" / "p5a_d2s4_queue_safe_client.py"
ADMISSION = ROOT / "scripts" / "g2e" / "p5a_d2s4_scientific_admission.py"
RUNNER = ROOT / "scripts" / "g2e" / "p5a_d2s4_scientific_runner.py"
VERIFIER = ROOT / "scripts" / "g2e" / "p5a_d2s4_scientific_verify.py"
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_d2s4_scientific_oneclick.ps1"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S4_QUEUE_SAFE_SUCCESSOR_SPEC.md"
D2S3_CLOSE = ROOT / "g2e" / "docs" / "P5A_D2S3_SCIENCE002_FORMAL_ADJUDICATION.md"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def fake_discovery(harness: str = "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b"):
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


def test_queue_empty_is_normalized_to_timeout(tmp_path):
    module = _load(CLIENT, "d2s4_client_timeout")
    client = _bare_client(module, tmp_path)
    with pytest.raises(TimeoutError):
        client.next_message(0.02)


def test_delayed_terminal_survives_more_than_two_empty_poll_intervals(tmp_path):
    client_module = _load(CLIENT, "d2s4_client_delayed")
    runner = _load(RUNNER, "d2s4_runner_delayed")
    client = _bare_client(client_module, tmp_path)
    turn_id = "synthetic-turn"

    def delayed():
        time.sleep(2.2)
        message = {
            "method": "turn/completed",
            "params": {"turn": {"id": turn_id, "status": "completed"}},
        }
        client.q.put(("stdout", json.dumps(message), time.time()))

    thread = threading.Thread(target=delayed, daemon=True)
    thread.start()
    result = runner.wait_for_turn(client, turn_id, 4.0)
    thread.join(timeout=1)

    assert result["terminal"] is True
    assert result["timeout"] is False
    assert result["unexpected_server_request"] is False
    assert result["completion"]["method"] == "turn/completed"


def test_total_deadline_remains_authoritative(tmp_path):
    client_module = _load(CLIENT, "d2s4_client_deadline")
    runner = _load(RUNNER, "d2s4_runner_deadline")
    client = _bare_client(client_module, tmp_path)

    started = time.monotonic()
    result = runner.wait_for_turn(client, "never-arrives", 0.08)
    elapsed = time.monotonic() - started

    assert result["terminal"] is False
    assert result["timeout"] is True
    assert result["unexpected_server_request"] is False
    assert elapsed < 0.8


def test_stdout_eof_remains_fatal(tmp_path):
    module = _load(CLIENT, "d2s4_client_eof")
    client = _bare_client(module, tmp_path)
    client.q.put(("stdout_eof", "", time.time()))
    with pytest.raises(EOFError, match="app-server stdout closed"):
        client.next_message(0.2)


def test_unexpected_server_request_remains_fail_closed(tmp_path):
    client_module = _load(CLIENT, "d2s4_client_request")
    runner = _load(RUNNER, "d2s4_runner_request")
    client = _bare_client(client_module, tmp_path)
    client.unexpected_server_requests.append({"id": 99, "method": "approval/request"})
    result = runner.wait_for_turn(client, "x", 1.0)
    assert result["terminal"] is False
    assert result["timeout"] is False
    assert result["unexpected_server_request"] is True


def test_admission_is_deterministic_and_binds_successor_lineage():
    module = _load(ADMISSION, "d2s4_admission")
    first = module.build_final_admission(fake_discovery())
    second = module.build_final_admission(fake_discovery())
    assert first == second
    module.verify_final_admission(first, fake_discovery())

    assert first["study_id"] == "p5a-d2s4-queue-safe-scientific-successor"
    assert first["attempt_id"] == "p5a-d2s4-p5-fx-001-attempt-001"
    assert first["execution_config"]["queue_safe_client_git_blob"] == module.QUEUE_SAFE_CLIENT_GIT_BLOB
    assert first["execution_config"]["predecessor_postclosure_bundle_sha256"] == module.PREDECESSOR_POSTCLOSURE_BUNDLE_SHA256
    assert first["authorization"]["retry_authorized"] is False
    assert first["authorization"]["exact_scientific_attempts_authorized_after_lock"] == 1


def test_manifest_does_not_prematurely_promote_functional_capability():
    module = _load(ADMISSION, "d2s4_admission_caps")
    pack = module.build_final_admission(fake_discovery())
    caps = {x["capability_id"]: x["available"] for x in pack["manifest"]["capabilities"]}
    assert caps["repository_read"] is False
    assert caps["repository_write"] is False


def test_runner_uses_successor_identity_and_predecessor_r2_only_as_provenance():
    source = RUNNER.read_text(encoding="utf-8")
    assert 'STUDY_ID = "p5a-d2s4-queue-safe-scientific-successor"' in source
    assert 'ATTEMPT_ID = "p5a-d2s4-p5-fx-001-attempt-001"' in source
    assert 'PREDECESSOR_STUDY_ID = "p5a-d2s3-release-coherent-instrument-successor"' in source
    assert 'PREDECESSOR_ATTEMPT_ID = "p5a-d2s3-p5-fx-001-attempt-001"' in source
    assert 'p5a_d2s4_queue_safe_client.py' in source


def test_runner_has_exactly_one_turn_start_and_marker_precedes_send():
    source = RUNNER.read_text(encoding="utf-8")
    assert source.count('"method": "turn/start"') == 1
    assert source.count("P5A_D2S4_TURN_START_SENT.marker") == 1
    marker_index = source.index("fsync_text(marker_path, marker_text)")
    send_index = source.index("client.send(request)")
    assert marker_index < send_index
    assert 'evidence["scientific_attempt_consumed"] = True' in source[marker_index:send_index]
    assert "TURN_TIMEOUT_S = 90.0" in source
    assert '"sandboxPolicy"' not in source


def test_fresh_control_plane_precedes_attempt_consumption():
    source = RUNNER.read_text(encoding="utf-8")
    assert source.index("perform_control_plane(") < source.index("fsync_text(marker_path, marker_text)")
    for method in (
        "windowsSandbox/readiness",
        "windowsSandbox/setupStart",
        "mcpServerStatus/list",
        "app/installed",
        "account/read",
        "permissionProfile/list",
        "thread/start",
    ):
        assert method in source


def test_verifier_never_assigns_scientific_verdict():
    source = VERIFIER.read_text(encoding="utf-8")
    assert '"verifier_assigns_scientific_verdict": False' in source
    assert "result_schema_valid" in source
    assert "result_values_correct" in source
    assert "mutation_scope_valid" in source


def test_oneclick_is_fresh_single_shot_and_cleanup_non_bypassable():
    source = ONECLICK.read_text(encoding="utf-8")
    assert "P5A-D2S4-SCIENCE-001" in source
    assert "SCIENTIFIC_ROOT_ALREADY_EXISTS_NO_RETRY" in source
    assert "P5A_D2S4_SCIENTIFIC_EXECUTION_LOCK.json" in source
    assert "retry_authorized" in source
    assert "automatic_retry_authorized" in source

    start = source.index("# PROTECTED_SCIENTIFIC_VHDX_BODY_START")
    end = source.index("# PROTECTED_SCIENTIFIC_VHDX_BODY_END")
    protected = source[start:end]
    assert "Dismount-DiskImage -ImagePath $VhdxPath" in protected
    assert "attached_after_cleanup" in protected
    assert "exit " not in protected
    assert "Remove-Item -LiteralPath $VhdxPath" not in source


def test_predecessor_d2s3_formal_close_remains_no_retry():
    text = " ".join(D2S3_CLOSE.read_text(encoding="utf-8").split())
    assert "FORMALLY CLOSED / NO RETRY" in text
    assert "D2-S3 MUST NOT be rerun" in text


def test_successor_spec_freezes_only_queue_mechanism_change():
    text = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "Sole mechanism change" in text
    assert "queue.Empty" in text
    assert "turn timeout = 90 seconds" in text
    assert "retry budget = 0" in text
    assert "No automatic retry is allowed" in text
