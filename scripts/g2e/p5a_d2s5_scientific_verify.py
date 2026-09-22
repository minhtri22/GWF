from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ATTEMPT_ID = "p5a-d2s5-p5-fx-001-attempt-001"
HARNESS_SHA256 = "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b"
INPUT_SHA256 = "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
TASK_SHA256 = "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"
R2_EVIDENCE_SHA256 = "87f18cf15f06eb1bc3e0a9e28f76e3208b2c082c3cd458221242d65db7b8cc28"
OBSERVABLE_CLIENT_GIT_BLOB = "57f5b3e0a1ac13f7722d7bfe244a100bfeb08504"
OBSERVABILITY_GIT_BLOB = "b6d3c6fcb671dd166893edd46388c8d69dca9105"
EXPECTED_RESULT_KEYS = {
    "count",
    "sum",
    "sorted_unique_values",
    "input_sha256",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def load_protocol(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError("protocol record is not an object")
            out.append(obj)
    return out


def parse_marker(path: Path) -> dict:
    if not path.is_file():
        return {
            "exists": False,
            "lines": [],
            "attempt_id": None,
            "execution_config_hash": None,
            "r2_evidence_sha256": None,
        }
    lines = path.read_text(encoding="utf-8").splitlines()
    return {
        "exists": True,
        "lines": lines,
        "attempt_id": lines[1] if len(lines) > 1 else None,
        "execution_config_hash": lines[2] if len(lines) > 2 else None,
        "r2_evidence_sha256": lines[3] if len(lines) > 3 else None,
    }



def _valid_text_projection(value) -> bool:
    if value is None:
        return True
    return (
        isinstance(value, dict)
        and isinstance(value.get("text"), str)
        and isinstance(value.get("rawSha256"), str)
        and len(value.get("rawSha256")) == 64
        and isinstance(value.get("rawLength"), int)
        and isinstance(value.get("redactionApplied"), bool)
    )


def _valid_turn_error_projection(error) -> bool:
    if error is None:
        return False
    if not isinstance(error, dict):
        return False
    if not _valid_text_projection(error.get("message")):
        return False
    if error.get("message") is None:
        return False
    if not _valid_text_projection(error.get("additionalDetails")):
        return False
    if "codexErrorInfo" not in error:
        return False
    if "misalignment" not in error:
        return False
    return True


def verify_observability_contract(protocol: list[dict], evidence: dict) -> dict:
    thread_id = evidence.get("thread_id")
    turn_id = evidence.get("turn_id")
    terminal_status = str(evidence.get("terminal_status") or "").lower()

    error_records = [rec for rec in protocol if rec.get("method") == "error"]
    completed_records = [
        rec for rec in protocol if rec.get("method") == "turn/completed"
    ]

    errors_valid = True
    mechanism_bearing = False
    for rec in error_records:
        projection = rec.get("terminalErrorEvidence")
        valid = (
            isinstance(projection, dict)
            and projection.get("source") == "errorNotification"
            and projection.get("threadId") == thread_id
            and projection.get("turnId") == turn_id
            and isinstance(projection.get("willRetry"), bool)
            and _valid_turn_error_projection(projection.get("error"))
            and isinstance(rec.get("rawSha256"), str)
            and len(rec.get("rawSha256")) == 64
            and isinstance(rec.get("length"), int)
        )
        errors_valid = errors_valid and valid
        mechanism_bearing = mechanism_bearing or valid

    failed_completion_valid = True
    failed_completion_seen = False
    for rec in completed_records:
        projection = rec.get("terminalErrorEvidence")
        if not isinstance(projection, dict):
            if terminal_status == "failed":
                failed_completion_valid = False
            continue
        if str(projection.get("status") or "").lower() != "failed":
            continue
        failed_completion_seen = True
        valid = (
            projection.get("source") == "turnCompleted"
            and projection.get("threadId") == thread_id
            and projection.get("turnId") == turn_id
            and isinstance(rec.get("rawSha256"), str)
            and len(rec.get("rawSha256")) == 64
            and isinstance(rec.get("length"), int)
        )
        if projection.get("error") is not None:
            valid = valid and _valid_turn_error_projection(projection.get("error"))
            mechanism_bearing = mechanism_bearing or valid
        failed_completion_valid = failed_completion_valid and valid

    required = bool(error_records) or terminal_status == "failed"
    if terminal_status == "failed" and not failed_completion_seen:
        failed_completion_valid = False

    valid = True
    if required:
        valid = errors_valid and failed_completion_valid and mechanism_bearing

    return {
        "required": required,
        "error_record_count": len(error_records),
        "failed_completion_seen": failed_completion_seen,
        "error_records_valid": errors_valid,
        "failed_completion_valid": failed_completion_valid,
        "mechanism_bearing_projection_present": mechanism_bearing,
        "contract_valid": valid,
    }

def expected_result(input_payload: dict) -> dict:
    values = input_payload.get("values")
    if not isinstance(values, list) or not all(
        isinstance(value, int) and not isinstance(value, bool)
        for value in values
    ):
        raise ValueError("input values are not a list of integers")
    return {
        "count": len(values),
        "sum": sum(values),
        "sorted_unique_values": sorted(set(values)),
        "input_sha256": INPUT_SHA256,
    }


def verify(
    evidence_path: Path,
    protocol_path: Path,
    marker_path: Path,
    workspace: Path,
    execution_config_hash: str,
) -> dict:
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    protocol = load_protocol(protocol_path)
    marker = parse_marker(marker_path)

    identity_checks = {
        "runner_schema": evidence.get("schema")
        == "G2E-P5A-D2S5-SCIENTIFIC-RUNNER-v1",
        "attempt_id": evidence.get("attempt_id") == ATTEMPT_ID,
        "harness": evidence.get("harness_sha256") == HARNESS_SHA256,
        "input_identity": evidence.get("input_sha256") == INPUT_SHA256,
        "task_identity": evidence.get("task_sha256") == TASK_SHA256,
        "execution_config": evidence.get("execution_config_hash")
        == execution_config_hash,
        "r2_evidence": evidence.get("r2_evidence_sha256")
        == R2_EVIDENCE_SHA256,
        "r2_authorization": evidence.get("r2_authorization_pass") is True,
        "observable_client": evidence.get("observable_client_git_blob")
        == OBSERVABLE_CLIENT_GIT_BLOB,
        "observability": evidence.get("observability_git_blob")
        == OBSERVABILITY_GIT_BLOB,
    }

    marker_checks = {
        "exists": marker["exists"],
        "attempt": marker["attempt_id"] == ATTEMPT_ID,
        "config": marker["execution_config_hash"] == execution_config_hash,
        "r2": marker["r2_evidence_sha256"] == R2_EVIDENCE_SHA256,
        "runner_marker_flag": evidence.get("turn_start_marker_created") is True,
        "runner_consumed_flag": evidence.get("scientific_attempt_consumed") is True,
        "runner_turn_sent": evidence.get("turn_start_request_sent") is True,
    }

    input_path = workspace / "input.json"
    task_path = workspace / "TASK.md"
    result_path = workspace / "result.json"

    input_hash_ok = input_path.is_file() and sha256_file(input_path) == INPUT_SHA256
    task_hash_ok = task_path.is_file() and sha256_file(task_path) == TASK_SHA256

    input_payload = json.loads(input_path.read_text(encoding="utf-8"))
    expected = expected_result(input_payload)

    result_exists = result_path.is_file()
    result_payload = None
    result_parse_error = None
    result_schema_valid = None
    result_values_correct = None

    terminal_status = str(evidence.get("terminal_status") or "").lower()
    executor_completed = (
        1
        if evidence.get("turn_start_accepted") is True
        and evidence.get("turn_terminal") is True
        and terminal_status == "completed"
        else None
    )

    if executor_completed == 1:
        if not result_exists:
            result_schema_valid = 0
            result_values_correct = 0
        else:
            try:
                result_payload = json.loads(
                    result_path.read_text(encoding="utf-8")
                )
                schema_ok = (
                    isinstance(result_payload, dict)
                    and set(result_payload.keys()) == EXPECTED_RESULT_KEYS
                    and isinstance(result_payload.get("count"), int)
                    and not isinstance(result_payload.get("count"), bool)
                    and isinstance(result_payload.get("sum"), int)
                    and not isinstance(result_payload.get("sum"), bool)
                    and isinstance(
                        result_payload.get("sorted_unique_values"), list
                    )
                    and all(
                        isinstance(value, int) and not isinstance(value, bool)
                        for value in result_payload.get(
                            "sorted_unique_values", []
                        )
                    )
                    and isinstance(
                        result_payload.get("input_sha256"), str
                    )
                )
                result_schema_valid = 1 if schema_ok else 0
                result_values_correct = (
                    1 if schema_ok and result_payload == expected else 0
                )
            except Exception as exc:
                result_parse_error = f"{type(exc).__name__}:{exc}"
                result_schema_valid = 0
                result_values_correct = 0

    workspace_post = evidence.get("workspace_post") or {}
    payload_names = sorted(workspace_post.get("payload") or [])
    support_names = sorted(workspace_post.get("support") or [])
    result_names = sorted(workspace_post.get("result") or [])
    unexpected_names = sorted(workspace_post.get("unexpected") or [])

    mutation_scope_ok = (
        input_hash_ok
        and task_hash_ok
        and evidence.get("input_unchanged") is True
        and evidence.get("task_unchanged") is True
        and payload_names == ["TASK.md", "input.json"]
        and set(support_names) <= {"System Volume Information"}
        and unexpected_names == []
        and result_names in ([], ["result.json"])
        and (result_names == ["result.json"]) == result_exists
    )

    protocol_integrity = protocol_path.is_file() and len(protocol) > 0
    observability_checks = verify_observability_contract(protocol, evidence)
    marker_integrity = all(marker_checks.values())
    identity_integrity = all(identity_checks.values())

    attempt_attribution_valid = (
        1
        if marker_integrity
        and evidence.get("thread_id")
        and (
            evidence.get("turn_id")
            or evidence.get("turn_start_accepted") is False
        )
        else 0
    )
    evidence_integrity_valid = (
        1
        if identity_integrity
        and protocol_integrity
        and observability_checks["contract_valid"]
        and input_hash_ok
        and task_hash_ok
        else 0
    )

    authority_violation = any(
        (
            evidence.get("permission_request_seen") is True,
            evidence.get("protocol_command_execution_seen") is True,
            evidence.get("protocol_mcp_tool_seen") is True,
            evidence.get("protocol_web_search_seen") is True,
            evidence.get("unexpected_server_request") is True,
            bool(evidence.get("unexpected_server_requests")),
        )
    )

    infrastructure_or_protocol_failure = any(
        (
            evidence.get("turn_start_accepted") is not True,
            evidence.get("turn_timeout") is True,
            evidence.get("turn_terminal") is not True,
            terminal_status not in ("", "completed"),
            bool(evidence.get("driver_exception")),
        )
    )

    metrics = {
        "executor_completed": executor_completed,
        "result_schema_valid": result_schema_valid,
        "result_values_correct": result_values_correct,
        "mutation_scope_valid": 1 if mutation_scope_ok else 0,
        "attempt_attribution_valid": attempt_attribution_valid,
        "evidence_integrity_valid": evidence_integrity_valid,
    }

    return {
        "schema": "G2E-P5A-D2S5-SCIENTIFIC-VERIFICATION-v1",
        "attempt_id": ATTEMPT_ID,
        "input_artifacts": {
            "runner_evidence_sha256": sha256_file(evidence_path),
            "protocol_sha256": (
                sha256_file(protocol_path) if protocol_path.is_file() else None
            ),
            "turn_start_marker_sha256": (
                sha256_file(marker_path) if marker_path.is_file() else None
            ),
        },
        "identity_checks": identity_checks,
        "marker_checks": marker_checks,
        "observability_checks": observability_checks,
        "metrics": metrics,
        "expected_result": expected,
        "observed_result": result_payload,
        "result_parse_error": result_parse_error,
        "adjudication_inputs": {
            "attempt_consumed_under_frozen_rule": marker["exists"],
            "turn_start_request_sent": evidence.get(
                "turn_start_request_sent"
            )
            is True,
            "turn_start_accepted": evidence.get("turn_start_accepted") is True,
            "turn_terminal": evidence.get("turn_terminal") is True,
            "terminal_status": evidence.get("terminal_status"),
            "turn_timeout": evidence.get("turn_timeout") is True,
            "authority_violation": authority_violation,
            "infrastructure_or_protocol_failure": (
                infrastructure_or_protocol_failure
            ),
            "result_exists": result_exists,
            "retry_budget": 0,
            "replacement_attempt_authorized": False,
        },
        "workspace": {
            "payload_names": payload_names,
            "support_names": support_names,
            "result_names": result_names,
            "unexpected_names": unexpected_names,
            "input_hash_ok": input_hash_ok,
            "task_hash_ok": task_hash_ok,
        },
        "verifier_assigns_scientific_verdict": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--marker", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--execution-config-hash", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = verify(
        Path(args.evidence),
        Path(args.protocol),
        Path(args.marker),
        Path(args.workspace),
        args.execution_config_hash,
    )
    out = Path(args.output)
    out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "attempt_id": ATTEMPT_ID,
                "metrics": report["metrics"],
                "adjudication_inputs": report["adjudication_inputs"],
                "verdict_assigned": False,
                "output": str(out),
                "output_sha256": sha256_file(out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
