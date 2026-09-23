from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

STUDY_ID = "p5a-cgw-v4-p5-fx-001-functional-qualification"
ATTEMPT_ID = "p5a-cgw-v4-p5-fx-001-attempt-001"
ROUTE_ID = "p5a-cgw"
INPUT_SHA256 = "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
TASK_SHA256 = "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"
EXPECTED_RESULT_SHA256 = "6dd3ebce33677409bec596309e061cc421bfa38b3160c5b577ffe5f7fbc9980d"
EXECUTION_CONFIG_CANONICAL_SHA256 = "b7097e8a63607e33f520ab370e48106fc7234f782204e3c366be409b5b594ab8"
CODEX_BINARY_SHA256 = "a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8"
EXPECTED_KEYS = {"count", "sum", "sorted_unique_values", "input_sha256"}
_HEX64 = re.compile(r"^[a-f0-9]{64}$")
_CAP = re.compile(r"^sha256-prefix12:[a-f0-9]{12}$")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("JSONL_RECORD_NOT_OBJECT")
        out.append(value)
    return out


def expected_result(input_payload: dict[str, Any]) -> dict[str, Any]:
    values = input_payload.get("values")
    if not isinstance(values, list) or not all(isinstance(v, int) and not isinstance(v, bool) for v in values):
        raise ValueError("INPUT_VALUES_INVALID")
    return {
        "count": len(values),
        "sum": sum(values),
        "sorted_unique_values": sorted(set(values)),
        "input_sha256": INPUT_SHA256,
    }


def validate_route(records: list[dict[str, Any]], thread_id: str | None, turn_id: str | None) -> dict[str, Any]:
    errors: list[str] = []
    by_event: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_event.setdefault(str(record.get("event") or ""), []).append(record)

    def exactly_one(name: str) -> dict[str, Any] | None:
        rows = by_event.get(name, [])
        if len(rows) != 1:
            errors.append(f"ROUTE_{name.upper()}_CARDINALITY")
            return None
        return rows[0]

    start = exactly_one("codex_request")
    submit = exactly_one("browser_submit")
    tool = exactly_one("mcp_roundtrip")
    terminal = exactly_one("terminal")
    if not all((start, submit, tool, terminal)):
        return {"valid": False, "errors": errors}

    assert start and submit and tool and terminal
    request_id = start.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        errors.append("ROUTE_REQUEST_ID_MISSING")

    for row in (start, submit, tool, terminal):
        if row.get("request_id") != request_id:
            errors.append("ROUTE_REQUEST_ID_MISMATCH")
        if row.get("outer_thread_id") != thread_id:
            errors.append("ROUTE_THREAD_MISMATCH")
        if row.get("outer_turn_id") != turn_id:
            errors.append("ROUTE_TURN_MISMATCH")
        if row.get("bridge_mode") != "full":
            errors.append("ROUTE_MODE_MISMATCH")
        if row.get("model") != "chatgpt-web/high":
            errors.append("ROUTE_MODEL_MISMATCH")
        if row.get("bridge_side_effects_performed") is not False:
            errors.append("ROUTE_BRIDGE_SIDE_EFFECT_FLAG")

    surface = submit.get("browser_lease_id")
    if not isinstance(surface, str) or not surface:
        errors.append("ROUTE_BROWSER_SURFACE_MISSING")
    if terminal.get("browser_lease_id") != surface or tool.get("browser_lease_id") != surface:
        errors.append("ROUTE_BROWSER_SURFACE_MISMATCH")

    binding = submit.get("qualified_response_binding")
    if not isinstance(binding, str) or not _HEX64.fullmatch(binding):
        errors.append("ROUTE_RESPONSE_BINDING_INVALID")
    if terminal.get("qualified_response_binding") != binding:
        errors.append("ROUTE_RESPONSE_BINDING_MISMATCH")

    if tool.get("connector") != "Codex Native2":
        errors.append("ROUTE_CONNECTOR_MISMATCH")
    cap = tool.get("capability_token_digest")
    if not isinstance(cap, str) or not _CAP.fullmatch(cap):
        errors.append("ROUTE_CAPABILITY_DIGEST_INVALID")
    invocation = tool.get("invocation_id")
    if not isinstance(invocation, str) or not invocation:
        errors.append("ROUTE_INVOCATION_ID_MISSING")
    tool_name = tool.get("tool_name")
    if not isinstance(tool_name, str) or not tool_name:
        errors.append("ROUTE_TOOL_NAME_MISSING")
    if tool.get("executor") != "codex":
        errors.append("ROUTE_EXECUTOR_NOT_CODEX")
    result_digest = tool.get("tool_result_digest")
    if not isinstance(result_digest, str) or not _HEX64.fullmatch(result_digest):
        errors.append("ROUTE_TOOL_RESULT_DIGEST_INVALID")

    return {
        "valid": not errors,
        "errors": sorted(set(errors)),
        "request_id": request_id,
        "browser_lease_id": surface,
        "qualified_response_binding": binding,
        "tool_name": tool_name,
        "invocation_id": invocation,
        "capability_token_digest": cap,
        "tool_result_digest": result_digest,
        "terminal_status": terminal.get("status"),
    }


def verify(
    *,
    runner_path: Path,
    protocol_path: Path,
    route_path: Path,
    marker_path: Path,
    admission_path: Path,
    workspace: Path,
    execution_config_hash: str,
) -> dict[str, Any]:
    runner = json.loads(runner_path.read_text(encoding="utf-8"))
    admission = json.loads(admission_path.read_text(encoding="utf-8"))
    protocol = load_jsonl(protocol_path)
    route = load_jsonl(route_path)
    route_check = validate_route(route, runner.get("thread_id"), runner.get("turn_id"))

    identity_checks = {
        "runner_schema": runner.get("schema") == "G2E-P5A-CGW-FX001-RUNNER-v1",
        "study": runner.get("study_id") == STUDY_ID,
        "attempt": runner.get("attempt_id") == ATTEMPT_ID,
        "route": runner.get("route_id") == ROUTE_ID,
        "execution_config": runner.get("execution_config_hash") == execution_config_hash == EXECUTION_CONFIG_CANONICAL_SHA256,
        "codex_binary": runner.get("codex_binary_sha256") == CODEX_BINARY_SHA256,
        "admission_sha": runner.get("predispatch_admission_sha256") == sha256_file(admission_path),
        "admission_status": admission.get("status") == "PREDISPATCH_ADMISSION_PASS",
        "admission_attempt": admission.get("attempt_id") == ATTEMPT_ID,
        "admission_unconsumed": admission.get("attempt_consumed") is False and admission.get("model_turn_sent") is False,
    }

    marker_ok = marker_path.is_file()
    marker_lines = marker_path.read_text(encoding="utf-8").splitlines() if marker_ok else []
    marker_checks = {
        "exists": marker_ok,
        "attempt": len(marker_lines) > 1 and marker_lines[1] == ATTEMPT_ID,
        "config": len(marker_lines) > 2 and marker_lines[2] == execution_config_hash,
        "admission": len(marker_lines) > 3 and marker_lines[3] == sha256_file(admission_path),
        "runner_marker_flag": runner.get("turn_start_marker_created") is True,
        "runner_consumed": runner.get("attempt_consumed") is True,
        "turn_sent": runner.get("turn_start_request_sent") is True,
    }

    input_path = workspace / "input.json"
    task_path = workspace / "TASK.md"
    result_path = workspace / "result.json"
    input_ok = input_path.is_file() and sha256_file(input_path) == INPUT_SHA256
    task_ok = task_path.is_file() and sha256_file(task_path) == TASK_SHA256

    expected = expected_result(json.loads(input_path.read_text(encoding="utf-8")))
    expected_hash_ok = canonical_sha256(expected) == EXPECTED_RESULT_SHA256

    terminal_status = str(runner.get("terminal_status") or "").lower()
    executor_completed = (
        1 if runner.get("turn_start_accepted") is True
        and runner.get("turn_terminal") is True
        and terminal_status == "completed"
        else None
    )

    result_exists = result_path.is_file()
    observed = None
    parse_error = None
    schema_valid = None
    values_correct = None
    if executor_completed == 1:
        if not result_exists:
            schema_valid = 0
            values_correct = 0
        else:
            try:
                observed = json.loads(result_path.read_text(encoding="utf-8"))
                schema_ok = (
                    isinstance(observed, dict)
                    and set(observed) == EXPECTED_KEYS
                    and isinstance(observed.get("count"), int) and not isinstance(observed.get("count"), bool)
                    and isinstance(observed.get("sum"), int) and not isinstance(observed.get("sum"), bool)
                    and isinstance(observed.get("sorted_unique_values"), list)
                    and all(isinstance(v, int) and not isinstance(v, bool) for v in observed.get("sorted_unique_values", []))
                    and isinstance(observed.get("input_sha256"), str)
                    and _HEX64.fullmatch(observed.get("input_sha256")) is not None
                )
                schema_valid = 1 if schema_ok else 0
                values_correct = 1 if schema_ok and observed == expected else 0
            except Exception as exc:
                parse_error = f"{type(exc).__name__}:{exc}"
                schema_valid = 0
                values_correct = 0

    names = sorted(p.name for p in workspace.iterdir())
    allowed = {"TASK.md", "input.json", "result.json", "System Volume Information"}
    mutation_ok = (
        input_ok and task_ok
        and runner.get("input_unchanged") is True
        and runner.get("task_unchanged") is True
        and set(names).issubset(allowed)
        and ("result.json" in names) == result_exists
    )

    protocol_integrity = (
        protocol_path.is_file()
        and len(protocol) > 0
        and runner.get("protocol_sha256") == sha256_file(protocol_path)
    )
    route_integrity = (
        route_path.is_file()
        and len(route) > 0
        and runner.get("route_evidence_sha256") == sha256_file(route_path)
        and route_check["valid"]
        and not runner.get("route_evidence_errors")
    )
    attribution = (
        1 if all(marker_checks.values())
        and isinstance(runner.get("thread_id"), str) and runner.get("thread_id")
        and isinstance(runner.get("turn_id"), str) and runner.get("turn_id")
        else 0
    )
    evidence_integrity = (
        1 if all(identity_checks.values())
        and protocol_integrity
        and route_integrity
        and input_ok
        and task_ok
        and expected_hash_ok
        else 0
    )

    web_search_seen = any(
        (
            "websearch" in str((r.get("item") or {}).get("type") or "").lower()
            or "web_search" in str((r.get("item") or {}).get("type") or "").lower()
            or "websearch" in str((r.get("item") or {}).get("name") or "").lower()
            or "web_search" in str((r.get("item") or {}).get("name") or "").lower()
        )
        for r in protocol
    )
    unexpected_server_requests = runner.get("unexpected_server_requests") or []
    authority_violation = web_search_seen or bool(unexpected_server_requests) or not route_check["valid"]

    infrastructure_or_protocol_failure = any((
        runner.get("turn_start_accepted") is not True,
        runner.get("turn_timeout") is True,
        runner.get("turn_terminal") is not True,
        terminal_status not in ("", "completed"),
        bool(runner.get("driver_exception")),
        not protocol_integrity,
        not route_integrity,
        bool(unexpected_server_requests),
    ))

    metrics = {
        "executor_completed": executor_completed,
        "result_schema_valid": schema_valid,
        "result_values_correct": values_correct,
        "mutation_scope_valid": 1 if mutation_ok else 0,
        "attempt_attribution_valid": attribution,
        "evidence_integrity_valid": evidence_integrity,
    }

    return {
        "schema": "G2E-P5A-CGW-FX001-VERIFICATION-v1",
        "study_id": STUDY_ID,
        "attempt_id": ATTEMPT_ID,
        "input_artifacts": {
            "runner_evidence_sha256": sha256_file(runner_path),
            "protocol_sha256": sha256_file(protocol_path) if protocol_path.is_file() else None,
            "route_evidence_sha256": sha256_file(route_path) if route_path.is_file() else None,
            "marker_sha256": sha256_file(marker_path) if marker_path.is_file() else None,
            "admission_sha256": sha256_file(admission_path),
        },
        "identity_checks": identity_checks,
        "marker_checks": marker_checks,
        "route_checks": route_check,
        "metrics": metrics,
        "expected_result": expected,
        "observed_result": observed,
        "result_parse_error": parse_error,
        "workspace": {
            "names": names,
            "input_hash_ok": input_ok,
            "task_hash_ok": task_ok,
        },
        "adjudication_inputs": {
            "attempt_consumed_under_frozen_rule": marker_ok,
            "turn_start_request_sent": runner.get("turn_start_request_sent") is True,
            "turn_start_accepted": runner.get("turn_start_accepted") is True,
            "turn_terminal": runner.get("turn_terminal") is True,
            "terminal_status": runner.get("terminal_status"),
            "turn_timeout": runner.get("turn_timeout") is True,
            "authority_violation": authority_violation,
            "unexpected_server_request_count": len(unexpected_server_requests),
            "infrastructure_or_protocol_failure": infrastructure_or_protocol_failure,
            "live_mcp_roundtrip_admitted": route_check["valid"],
            "result_exists": result_exists,
            "retry_budget": 0,
            "replacement_attempt_authorized": False,
        },
        "verifier_assigns_scientific_verdict": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--runner", required=True)
    p.add_argument("--protocol", required=True)
    p.add_argument("--route", required=True)
    p.add_argument("--marker", required=True)
    p.add_argument("--admission", required=True)
    p.add_argument("--workspace", required=True)
    p.add_argument("--execution-config-hash", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    report = verify(
        runner_path=Path(a.runner),
        protocol_path=Path(a.protocol),
        route_path=Path(a.route),
        marker_path=Path(a.marker),
        admission_path=Path(a.admission),
        workspace=Path(a.workspace),
        execution_config_hash=a.execution_config_hash,
    )
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({
        "metrics": report["metrics"],
        "adjudication_inputs": report["adjudication_inputs"],
        "verdict_assigned": report["verifier_assigns_scientific_verdict"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
