from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ATTEMPT_ID = "p5a-d2-p5-fx-001-attempt-001"
EXECUTION_CONFIG_HASH = "740d5303d29b757e47571bc50b6367770296f7186a5528cef25adbb806669c3a"
INPUT_SHA256 = "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
TASK_SHA256 = "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"
HARNESS_SHA256 = "a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8"
RUNNER_SHA256 = "f9ef2699f4ff77f43cad9316cb9cce5e496d832f72f9eb210ccfc5bcedca0171"
EVIDENCE_SCHEMA = "G2E-P5A-D2-ISOLATED-RUNNER-v2-EVIDENCE"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_protocol(path: Path) -> list[dict]:
    out = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"protocol line {idx} is not an object")
        out.append(obj)
    return out


def one(items: list[dict], predicate, label: str) -> dict:
    matches = [x for x in items if predicate(x)]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {label}, got {len(matches)}")
    return matches[0]


def verify(evidence_path: Path, protocol_path: Path, marker_path: Path) -> dict:
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    protocol = load_protocol(protocol_path)
    marker_lines = marker_path.read_text(encoding="utf-8").splitlines()

    checks: dict[str, bool] = {}
    checks["evidence_schema_exact"] = evidence.get("schema") == EVIDENCE_SCHEMA
    checks["attempt_id_exact"] = evidence.get("attempt_id") == ATTEMPT_ID
    checks["execution_mode"] = evidence.get("mode") == "execute"
    checks["source_head_exact"] = evidence.get("preflight", {}).get("source_head") == "6938072806d61e6920a86abece79406630653f3c"
    checks["source_clean"] = evidence.get("preflight", {}).get("source_status_clean") is True
    checks["harness_exact"] = evidence.get("preflight", {}).get("harness_sha256") == HARNESS_SHA256
    checks["runner_exact"] = evidence.get("preflight", {}).get("runner_sha256") == RUNNER_SHA256
    checks["config_hash_exact"] = evidence.get("preflight", {}).get("execution_config_hash") == EXECUTION_CONFIG_HASH
    checks["input_hash_exact"] = evidence.get("preflight", {}).get("input_sha256") == INPUT_SHA256
    checks["task_hash_exact"] = evidence.get("preflight", {}).get("task_sha256") == TASK_SHA256
    checks["mcp_zero"] = evidence.get("configured_mcp_count") == 0
    checks["apps_zero"] = evidence.get("installed_app_count") == 0 and evidence.get("callable_or_enabled_app_count") == 0
    checks["auth_ready"] = evidence.get("auth_ready") is True
    checks["instruction_sources_empty"] = evidence.get("instruction_sources") == []
    checks["thread_attributed"] = bool(evidence.get("thread_id")) and evidence.get("thread_id") == evidence.get("session_id")
    checks["turn_send_recorded"] = evidence.get("turn_start_request_sent") is True
    checks["turn_not_accepted"] = evidence.get("turn_start_accepted") is False and evidence.get("turn_id") is None
    checks["no_result"] = evidence.get("result_exists") is False and evidence.get("result_sha256") is None
    checks["input_unchanged"] = evidence.get("input_unchanged") is True
    checks["task_unchanged"] = evidence.get("task_unchanged") is True
    checks["no_unexpected_workspace_entries"] = evidence.get("unexpected_workspace_entries") == []
    checks["no_command_execution"] = evidence.get("protocol_command_execution_seen") is False
    checks["no_mcp_tool"] = evidence.get("protocol_mcp_tool_seen") is False
    checks["no_web_search"] = evidence.get("protocol_web_search_seen") is False
    checks["no_permission_request"] = evidence.get("permission_request_seen") is False
    checks["marker_three_lines"] = len(marker_lines) == 3
    checks["marker_attempt_exact"] = len(marker_lines) >= 2 and marker_lines[1] == ATTEMPT_ID
    checks["marker_config_exact"] = len(marker_lines) >= 3 and marker_lines[2] == EXECUTION_CONFIG_HASH

    thread_started = one(protocol, lambda x: x.get("method") == "thread/started", "thread/started notification")
    turn_response = one(protocol, lambda x: x.get("id") == 6, "turn/start response id=6")
    checks["protocol_thread_started"] = thread_started.get("method") == "thread/started"
    checks["protocol_turn_start_invalid_request"] = turn_response.get("error_code") == -32600
    checks["protocol_turn_start_error_hash_exact"] = (
        turn_response.get("error_message_sha256")
        == "218811c395896f0edd5a4e73b71a122a1501b591a3e9fa782b608ad9424d782f"
    )

    driver_exception = str(evidence.get("driver_exception") or "")
    checks["driver_protocol_rejection_exact"] = (
        "RPC_ERROR id=6" in driver_exception
        and "workspaceWrite.readOnlyAccess is no longer supported" in driver_exception
        and "permissionProfile" in driver_exception
    )

    if not all(checks.values()):
        failed = sorted(k for k, v in checks.items() if not v)
        raise ValueError("verification failed: " + ",".join(failed))

    metrics = {
        "executor_completed": None,
        "result_schema_valid": None,
        "result_values_correct": None,
        "mutation_scope_valid": 1,
        "attempt_attribution_valid": 1,
        "evidence_integrity_valid": 1,
    }

    return {
        "schema": "G2E-P5A-D2-ATTEMPT-001-VERIFICATION-v1",
        "attempt_id": ATTEMPT_ID,
        "input_artifacts": {
            "runner_evidence_sha256": sha256_file(evidence_path),
            "sanitized_protocol_sha256": sha256_file(protocol_path),
            "turn_start_marker_sha256": sha256_file(marker_path),
        },
        "checks": checks,
        "metrics": metrics,
        "metric_observation_notes": {
            "executor_completed": "UNOBSERVABLE_AS_TASK_EXECUTION: turn/start was rejected by protocol validation",
            "result_schema_valid": "UNOBSERVABLE: no result.json exists because turn/start was rejected",
            "result_values_correct": "UNOBSERVABLE: no result.json exists because turn/start was rejected",
            "mutation_scope_valid": "OBSERVED_PASS: only TASK.md and input.json remained and both hashes were unchanged",
            "attempt_attribution_valid": "OBSERVED_PASS: exact attempt marker, config hash, thread attribution, and protocol response are internally consistent",
            "evidence_integrity_valid": "OBSERVED_PASS: exact frozen identities/hashes and sanitized protocol evidence are internally consistent",
        },
        "adjudication_inputs": {
            "attempt_consumed_under_frozen_rule": True,
            "turn_start_request_sent": True,
            "turn_start_accepted": False,
            "protocol_rejected_before_task_execution": True,
            "executor_infrastructure_or_protocol_failure": True,
            "missing_result_due_protocol_failure": True,
            "substantive_task_metric_observed_zero": False,
            "retry_budget": 0,
            "replacement_attempt_authorized_by_current_contract": False,
        },
        "verifier_assigns_scientific_verdict": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", required=True)
    p.add_argument("--protocol", required=True)
    p.add_argument("--marker", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    report = verify(Path(args.evidence), Path(args.protocol), Path(args.marker))
    out = Path(args.output)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({
        "attempt_id": report["attempt_id"],
        "all_checks_pass": all(report["checks"].values()),
        "attempt_consumed": report["adjudication_inputs"]["attempt_consumed_under_frozen_rule"],
        "replacement_attempt_authorized": report["adjudication_inputs"]["replacement_attempt_authorized_by_current_contract"],
        "output": str(out),
        "output_sha256": sha256_file(out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
