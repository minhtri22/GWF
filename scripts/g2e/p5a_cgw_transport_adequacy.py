from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def classify_signals(
    *,
    route_valid: bool,
    unexpected_server_request_count: int,
    prohibited_tool_or_network_seen: bool,
    bridge_side_effects_performed: bool,
    executor_is_outer_codex: bool | None,
) -> dict[str, bool]:
    """Decompose transport/evidence/scope/authority signals without conflation."""
    return {
        "evidence_integrity_failure": not route_valid,
        "protocol_failure": unexpected_server_request_count > 0,
        "scope_violation": prohibited_tool_or_network_seen,
        "authority_violation": (
            bridge_side_effects_performed
            or executor_is_outer_codex is False
        ),
    }


def audit_sources(runner_source: str, verifier_source: str, policy: dict[str, Any]) -> dict[str, Any]:
    legacy_timeout_present = (
        "TURN_TIMEOUT_S = 90.0" in runner_source
        and "deadline = time.monotonic() + TURN_TIMEOUT_S" in runner_source
    )
    legacy_authority_conflation_present = (
        'authority_violation = web_search_seen or bool(unexpected_server_requests) or not route_check["valid"]'
        in verifier_source
    )
    future = policy["future_transport_contract"]
    upstream = policy["qualified_upstream"]["codex_chatgpt_web"]["source_contract"]

    checks = {
        "spent_attempt_reuse_forbidden": future["reuse_spent_attempt"] is False,
        "spent_lock_reuse_forbidden": future["reuse_spent_execution_lock"] is False,
        "future_scientific_absolute_deadline_absent": future["scientific_adjudication_absolute_turn_deadline_ms"] is None,
        "upstream_browser_deadline_default_absent": upstream["browser_turn_absolute_deadline_default_ms"] is None,
        "upstream_bridge_stall_is_300s": upstream["bridge_stall_timeout_sec"] == 300,
        "upstream_mcp_invocation_is_90s": upstream["mcp_invocation_timeout_ms"] == 90_000,
        "upstream_tunnel_deadline_is_120s": upstream["tunnel_command_response_deadline_ms"] == 120_000,
        "legacy_90s_absolute_timeout_detected": legacy_timeout_present,
        "legacy_authority_conflation_detected": legacy_authority_conflation_present,
        "route_invalidity_is_evidence_failure": future["route_invalidity_class"] == "evidence_integrity_failure",
        "unexpected_server_request_is_protocol_failure": future["unexpected_server_request_class"] == "protocol_failure",
        "positive_authority_evidence_required": future["authority_violation_requires_positive_authority_evidence"] is True,
        "firewall_no_model_turn": policy["firewall"]["model_turn"] is False,
        "firewall_no_browser_submission": policy["firewall"]["browser_submission"] is False,
        "firewall_no_mcp": policy["firewall"]["mcp_invocation"] is False,
        "firewall_no_attempt_consumption": policy["firewall"]["scientific_attempt_consumption"] is False,
    }

    return {
        "schema": "G2E-P5A-CGW-TRANSPORT-ADEQUACY-AUDIT-v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "INFRASTRUCTURE_CONTRACT_MISMATCH_CONFIRMED" if all(checks.values()) else "UNRESOLVED",
        "checks": checks,
        "legacy": {
            "outer_absolute_timeout_sec": 90 if legacy_timeout_present else None,
            "authority_conflation_present": legacy_authority_conflation_present,
        },
        "future_contract": future,
        "scientific_attempt_touched": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--runner", required=True)
    p.add_argument("--verifier", required=True)
    p.add_argument("--policy", required=True)
    p.add_argument("--output")
    a = p.parse_args()

    runner = Path(a.runner).read_text(encoding="utf-8")
    verifier = Path(a.verifier).read_text(encoding="utf-8")
    policy = json.loads(Path(a.policy).read_text(encoding="utf-8"))
    report = audit_sources(runner, verifier, policy)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if a.output:
        Path(a.output).write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
