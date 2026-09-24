from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADMISSION = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_tc_admission.py"
RUNNER = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_tc_runner.py"
VERIFIER = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_tc_verify.py"
OLD_RUNNER = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_runner.py"
OLD_VERIFIER = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_verify.py"
PREREG = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_preregister.py"
CONFIG = ROOT / "g2e" / "config" / "P5A_CGW_FX001_TC_EXECUTION_CONFIG.json"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def write_fixture(workspace: Path):
    prereg = load(PREREG, "tc_fixture_prereg")
    payload = prereg.fixture_input()
    input_bytes = prereg.canonical_bytes(payload)
    task_bytes = prereg.TASK_TEXT.encode("utf-8")
    (workspace / "input.json").write_bytes(input_bytes)
    (workspace / "TASK.md").write_bytes(task_bytes)
    return prereg, payload


def synthetic_route(*, executor: str = "codex", bridge_side_effects: bool = False):
    trace = "abc123def456"
    surface = "S" * 32
    call_id = "call_123456789012ABCDEFG"
    binding = "c" * 64
    base = {
        "request_id": trace,
        "outer_thread_id": "thread-1",
        "outer_turn_id": "turn-1",
        "bridge_mode": "full",
        "model": "chatgpt-web/high",
        "bridge_side_effects_performed": bridge_side_effects,
    }
    return [
        {"event": "codex_request", **base},
        {
            "event": "browser_submit",
            **base,
            "browser_lease_id": surface,
            "qualified_response_binding": binding,
        },
        {
            "event": "mcp_roundtrip",
            **base,
            "browser_lease_id": surface,
            "connector": "Codex Native2",
            "capability_token_digest": "sha256-prefix12:abcdef123456",
            "tool_name": "codex_exec",
            "invocation_id": call_id,
            "executor": executor,
            "tool_result_digest": "a" * 64,
        },
        {
            "event": "terminal",
            **base,
            "browser_lease_id": surface,
            "qualified_response_binding": binding,
            "status": "completed",
        },
    ]


def materialize_verify_fixture(
    tmp_path: Path,
    *,
    route_records: list[dict] | None = None,
    unexpected_server_requests: list[dict] | None = None,
    add_web_search: bool = False,
):
    m = load(VERIFIER, "tc_verify_fixture")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    prereg, payload = write_fixture(workspace)
    expected = prereg.expected_result(payload)
    (workspace / "result.json").write_text(json.dumps(expected), encoding="utf-8")

    admission = {
        "schema": "G2E-P5A-CGW-FX001-TC-PREDISPATCH-ADMISSION-v1",
        "status": "PREDISPATCH_ADMISSION_PASS",
        "study_id": m.STUDY_ID,
        "attempt_id": m.ATTEMPT_ID,
        "route_id": m.ROUTE_ID,
        "attempt_consumed": False,
        "model_turn_sent": False,
    }
    admission_path = tmp_path / "admission.json"
    admission_path.write_text(json.dumps(admission), encoding="utf-8")

    marker_path = tmp_path / "attempt_consumed.marker"
    marker_path.write_text(
        "2026-09-24T00:00:00Z\n"
        + m.ATTEMPT_ID + "\n"
        + m.EXECUTION_CONFIG_CANONICAL_SHA256 + "\n"
        + m.sha256_file(admission_path) + "\n",
        encoding="utf-8",
    )

    protocol = [{
        "method": "item/completed",
        "rawSha256": "a" * 64,
        "item": {
            "id": "call_123456789012ABCDEFG",
            "type": "commandExecution",
            "name": "exec",
            "status": "completed",
        },
    }]
    if add_web_search:
        protocol.append({
            "method": "item/completed",
            "rawSha256": "b" * 64,
            "item": {
                "id": "web-1",
                "type": "webSearch",
                "name": "web_search",
                "status": "completed",
            },
        })
    protocol_path = tmp_path / "protocol.jsonl"
    protocol_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in protocol),
        encoding="utf-8",
    )

    route = route_records if route_records is not None else synthetic_route()
    route_path = tmp_path / "route.jsonl"
    route_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in route),
        encoding="utf-8",
    )

    route_check = m.validate_route(route, "thread-1", "turn-1")
    runner = {
        "schema": "G2E-P5A-CGW-FX001-TC-RUNNER-v1",
        "study_id": m.STUDY_ID,
        "attempt_id": m.ATTEMPT_ID,
        "route_id": m.ROUTE_ID,
        "execution_config_hash": m.EXECUTION_CONFIG_CANONICAL_SHA256,
        "predispatch_admission_sha256": m.sha256_file(admission_path),
        "codex_binary_sha256": m.CODEX_BINARY_SHA256,
        "turn_start_marker_created": True,
        "attempt_consumed": True,
        "turn_start_request_sent": True,
        "turn_start_accepted": True,
        "thread_id": "thread-1",
        "turn_id": "turn-1",
        "turn_terminal": True,
        "turn_timeout": False,
        "scientific_absolute_turn_deadline_ms": None,
        "terminal_status": "completed",
        "driver_exception": None,
        "route_evidence_errors": [] if route_check["valid"] else route_check["errors"],
        "unexpected_server_requests": unexpected_server_requests or [],
        "protocol_sha256": m.sha256_file(protocol_path),
        "route_evidence_sha256": m.sha256_file(route_path),
        "input_unchanged": True,
        "task_unchanged": True,
    }
    runner_path = tmp_path / "runner.json"
    runner_path.write_text(json.dumps(runner), encoding="utf-8")

    report = m.verify(
        runner_path=runner_path,
        protocol_path=protocol_path,
        route_path=route_path,
        marker_path=marker_path,
        admission_path=admission_path,
        workspace=workspace,
        execution_config_hash=m.EXECUTION_CONFIG_CANONICAL_SHA256,
    )
    return report


def test_tc_identity_and_hashes_are_new_study_not_spent_attempt():
    admission = load(ADMISSION, "tc_admission_identity")
    runner = load(RUNNER, "tc_runner_identity")
    verifier = load(VERIFIER, "tc_verifier_identity")

    expected_study = "p5a-cgw-v4-p5-fx-001-transport-corrected-qualification"
    expected_attempt = "p5a-cgw-v4-p5-fx-001-tc-attempt-001"
    expected_hash = "6b88011e0bc6ba0164a0e6f4230bb1fb8be6037d7513f348c15d39ea726816f7"

    assert admission.STUDY_ID == runner.STUDY_ID == verifier.STUDY_ID == expected_study
    assert admission.ATTEMPT_ID == runner.ATTEMPT_ID == verifier.ATTEMPT_ID == expected_attempt
    assert runner.EXECUTION_CONFIG_CANONICAL_SHA256 == verifier.EXECUTION_CONFIG_CANONICAL_SHA256 == expected_hash


def test_tc_runner_removes_legacy_absolute_90_second_scientific_deadline():
    old = OLD_RUNNER.read_text(encoding="utf-8")
    new = RUNNER.read_text(encoding="utf-8")

    assert "TURN_TIMEOUT_S = 90.0" in old
    assert "deadline = time.monotonic() + TURN_TIMEOUT_S" in old
    assert "TURN_TIMEOUT_S" not in new
    assert "deadline = time.monotonic() + TURN_TIMEOUT_S" not in new
    assert '"scientific_absolute_turn_deadline_ms": None' in new
    assert 'if turn.get("id") == turn_id:' in new
    assert 'turn.get("id") in (None, turn_id)' not in new


def test_tc_runner_keeps_consumption_boundary_before_only_turn_start():
    source = RUNNER.read_text(encoding="utf-8")
    assert source.count('"method": "turn/start"') == 1
    marker_index = source.index("fsync_text(marker, marker_text)")
    consumed_index = source.index('evidence["attempt_consumed"] = True')
    sent_flag_index = source.index('evidence["turn_start_request_sent"] = True')
    send_index = source.index("client.send(request)")
    assert marker_index < consumed_index < sent_flag_index < send_index


def test_route_invalidity_is_evidence_failure_not_authority_violation(tmp_path):
    route = synthetic_route()
    route = [row for row in route if row["event"] != "mcp_roundtrip"]
    report = materialize_verify_fixture(tmp_path, route_records=route)

    assert report["metrics"]["evidence_integrity_valid"] == 0
    assert report["adjudication_inputs"]["live_mcp_roundtrip_admitted"] is False
    assert report["adjudication_inputs"]["authority_violation"] is False
    assert report["adjudication_inputs"]["protocol_failure"] is False
    assert report["adjudication_inputs"]["scope_violation"] is False


def test_unexpected_server_request_is_protocol_failure_not_authority(tmp_path):
    report = materialize_verify_fixture(
        tmp_path,
        unexpected_server_requests=[{"id": 91, "method": "unsupported/request"}],
    )
    assert report["adjudication_inputs"]["protocol_failure"] is True
    assert report["adjudication_inputs"]["authority_violation"] is False
    assert report["adjudication_inputs"]["scope_violation"] is False


def test_prohibited_web_search_is_scope_violation_not_authority(tmp_path):
    report = materialize_verify_fixture(tmp_path, add_web_search=True)
    assert report["adjudication_inputs"]["scope_violation"] is True
    assert report["adjudication_inputs"]["authority_violation"] is False


def test_positive_non_codex_executor_is_authority_violation(tmp_path):
    report = materialize_verify_fixture(
        tmp_path,
        route_records=synthetic_route(executor="bridge"),
    )
    assert report["adjudication_inputs"]["authority_violation"] is True


def test_positive_bridge_side_effect_is_authority_violation(tmp_path):
    report = materialize_verify_fixture(
        tmp_path,
        route_records=synthetic_route(bridge_side_effects=True),
    )
    assert report["adjudication_inputs"]["authority_violation"] is True


def test_old_verifier_conflation_is_preserved_only_as_spent_evidence():
    old = OLD_VERIFIER.read_text(encoding="utf-8")
    new = VERIFIER.read_text(encoding="utf-8")
    assert 'or not route_check["valid"]' in old
    assert 'or not route_check["valid"]' not in new


def test_tc_config_remains_dispatch_withheld_during_implementation():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert cfg["authorization"]["live_dispatch_authorized"] is False
    assert cfg["transport_contract"]["scientific_absolute_turn_deadline_ms"] is None
