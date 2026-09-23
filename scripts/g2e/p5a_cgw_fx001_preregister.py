from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

STUDY_ID = "p5a-cgw-v4-p5-fx-001-functional-qualification"
ATTEMPT_ID = "p5a-cgw-v4-p5-fx-001-attempt-001"
ROUTE_ID = "p5a-cgw"

GWF_ZERO_MODEL_CLOSE_COMMIT = "62db95d06f61716d3a8cf8a674c329bf9c37a7d2"
GWF_ZERO_MODEL_CLOSE_BLOB = "b00f52e29497acd6e04f61db114311394c7936f0"

CGW_RELEASE = "4.0.7"
CGW_SOURCE_COMMIT = "b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494"
CGW_MODEL_REGISTRY_BLOB = "dae14ce18737d4bdd7206b3df453b20f30a073ea"
CGW_INSTALLED_BINARY_SHA256 = "ac152ad499b1f41b2cafe94a3d05f5d4e4d3cd7ddbb417b9c60b118b08bc3cbb"
CGW_BRIDGE_CONFIG_SHA256 = "f8ba628c60faf5c95409ee3a37ad359f74dd0eb41bb961312b67758f9ba53858"

CODEX_BINARY_SHA256 = "a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8"
CODEX_D1_MANIFEST = {
    "object_id": "agent-capability-manifest-codex-d1",
    "revision_id": "a337b7433ebb351c-d1-v1",
    "content_hash": "585d59b32457484e8d4706c3e79a94398569ab4bc3e39ff8fca5502541ece5c5",
}
CODEX_D1_MANIFEST_FILE_SHA256 = "0b5ad6c71ee5fa74a1ca917a943a38bd96687d7b5571901daa8a6acb8e927eac"

MODEL_SLUG = "chatgpt-web/high"
BACKEND_MODEL = "gpt-5.6-sol"
CODEX_EFFORT = "high"
ADAPTER_EFFORT = "high"

INPUT_SHA256 = "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
TASK_SHA256 = "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"
EXPECTED_RESULT_SHA256 = "6dd3ebce33677409bec596309e061cc421bfa38b3160c5b577ffe5f7fbc9980d"

TASK_TEXT = """Read input.json in the current workspace.

Create exactly one file named result.json in the current workspace.
Do not modify input.json or TASK.md.
Do not create, rename, or delete any other file or directory.
Do not use network access.

result.json must be valid JSON with exactly these keys:
- count
- sum
- sorted_unique_values
- input_sha256

count is the number of integers in input.json.values.
sum is their mathematical integer sum.
sorted_unique_values is the ascending sorted list of distinct integers.
input_sha256 is the lowercase SHA-256 of canonical input.json bytes supplied by the qualification harness.

Do not include commentary in result.json.
When the file is written, stop.
"""


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def fixture_input(seed: str = "g2e-p5-agent-profile-v1", count: int = 32) -> dict[str, Any]:
    values: list[int] = []
    block = seed.encode("utf-8")
    while len(values) < count:
        block = hashlib.sha256(block).digest()
        for i in range(0, len(block), 4):
            chunk = block[i:i + 4]
            if len(chunk) < 4:
                continue
            values.append(int.from_bytes(chunk, "big", signed=False) - (1 << 31))
            if len(values) == count:
                break
    return {"generator_version": "p5-fx-001-v1", "seed": seed, "values": values}


def expected_result(input_payload: dict[str, Any]) -> dict[str, Any]:
    values = input_payload["values"]
    return {
        "count": len(values),
        "sum": sum(values),
        "sorted_unique_values": sorted(set(values)),
        "input_sha256": INPUT_SHA256,
    }


def build_preregistration() -> dict[str, Any]:
    inp = fixture_input()
    inp_sha = hashlib.sha256(canonical_bytes(inp)).hexdigest()
    task_sha = hashlib.sha256(TASK_TEXT.encode("utf-8")).hexdigest()
    expected = expected_result(inp)
    expected_sha = canonical_sha256(expected)

    if inp_sha != INPUT_SHA256:
        raise RuntimeError("INPUT_HASH_DRIFT")
    if task_sha != TASK_SHA256:
        raise RuntimeError("TASK_HASH_DRIFT")
    if expected_sha != EXPECTED_RESULT_SHA256:
        raise RuntimeError("EXPECTED_RESULT_HASH_DRIFT")

    contract: dict[str, Any] = {
        "schema": "G2E-P5A-CGW-FX001-PREREGISTRATION-v1",
        "status": "PREREGISTERED_ZERO_MODEL_NO_DISPATCH",
        "study_id": STUDY_ID,
        "attempt_id": ATTEMPT_ID,
        "route_id": ROUTE_ID,
        "scientific_question": (
            "Can G2E use the exact Codex -> codex-chatgpt-web v4.0.7 -> ChatGPT Web Full-mode route "
            "to complete frozen P5-FX-001 while Codex remains the sole local execution authority?"
        ),
        "lineage": {
            "zero_model_close_commit": GWF_ZERO_MODEL_CLOSE_COMMIT,
            "zero_model_close_blob": GWF_ZERO_MODEL_CLOSE_BLOB,
            "p5a_official_replacement": False,
            "p5a_official_cross_credit": False,
            "comparative_ab": False,
        },
        "runtime_identity": {
            "cgw_release": CGW_RELEASE,
            "cgw_source_commit": CGW_SOURCE_COMMIT,
            "cgw_model_registry_blob": CGW_MODEL_REGISTRY_BLOB,
            "cgw_installed_binary_sha256": CGW_INSTALLED_BINARY_SHA256,
            "cgw_bridge_config_sha256": CGW_BRIDGE_CONFIG_SHA256,
            "codex_binary_sha256": CODEX_BINARY_SHA256,
            "codex_cli_version_string_is_identity": False,
            "codex_d1_manifest": CODEX_D1_MANIFEST,
            "codex_d1_manifest_file_sha256": CODEX_D1_MANIFEST_FILE_SHA256,
        },
        "route": {
            "bridge_mode": "full",
            "connector": "Codex Native2",
            "bridge_host": "127.0.0.1",
            "bridge_port": 17841,
            "codex_openai_base_url": "http://127.0.0.1:17841/v1",
            "model_slug": MODEL_SLUG,
            "backend_model": BACKEND_MODEL,
            "codex_effort": CODEX_EFFORT,
            "adapter_effort": ADAPTER_EFFORT,
            "requires_pro": False,
            "silent_model_fallback": False,
            "silent_transport_fallback": False,
            "official_p5a_fallback": False,
            "model_substitution": False,
            "mode_substitution": False,
            "connector_substitution": False,
        },
        "fixture": {
            "id": "P5-FX-001",
            "input": inp,
            "input_sha256": inp_sha,
            "task_text": TASK_TEXT,
            "task_sha256": task_sha,
            "pre_workspace_payload": ["TASK.md", "input.json"],
            "only_permitted_post_addition": "result.json",
        },
        "result_contract": {
            "format": "json",
            "exact_keys": ["count", "input_sha256", "sorted_unique_values", "sum"],
            "additional_keys_allowed": False,
            "types": {
                "count": "integer_non_bool",
                "sum": "integer_non_bool",
                "sorted_unique_values": "array_integer_non_bool",
                "input_sha256": "lowercase_sha256_hex",
            },
            "expected_value": expected,
            "expected_canonical_sha256": expected_sha,
        },
        "authority": {
            "g2e": "attempt_and_evidence_authority",
            "codex": "sole_local_execution_authority",
            "cgw": "transport_and_inference_mediation_only",
            "chatgpt_web": "inference_and_admitted_tool_request_only",
            "mcp_connector": "turn_bound_capability_transport_only",
            "delegation_invariant": "bridge<=outer_codex_turn<=g2e_attempt",
            "workspace": "isolated_ntfs_vhdx",
            "allowed_reads": ["TASK.md", "input.json"],
            "allowed_writes": ["result.json"],
            "outside_workspace": "DENY",
            "interactive_approval": "DENY",
            "approval_policy": "never",
            "task_tool_network": "DENY",
            "route_transport_network": "ALLOW_ONLY_FROZEN_CGW_BROWSER_PATH",
            "web_search": "DENY",
            "arbitrary_mcp_server": "DENY",
            "bridge_local_side_effects": "DENY",
            "prompt_text_is_authority": False,
        },
        "predispatch_admission": {
            "must_pass_before_consumption": [
                "fresh_local_root_absent",
                "zero_model_formal_close_exact",
                "codex_binary_exact",
                "cgw_binary_exact",
                "cgw_release_4_0_7_exact",
                "cgw_bridge_config_hash_exact",
                "bridge_health_ok_and_idle",
                "bridge_mode_full",
                "connector_codex_native2",
                "codex_base_url_exact",
                "codex_selected_model_chatgpt_web_high",
                "no_route_or_model_fallback_configured",
                "frozen_input_and_task_hashes_exact",
                "isolated_workspace_prestate_exact",
            ],
            "selected_model_literal_must_be_observed": MODEL_SLUG,
            "predispatch_codex_config_sha256": "CAPTURE_AND_BIND_BEFORE_MARKER",
            "browser_authenticated_state": "NOT_CLAIMED_PRETURN; LIVE_ATTEMPT_TESTS_IT",
        },
        "attempt_consumption": {
            "boundary": "durable marker fsync immediately before sole Codex turn/start transport write",
            "pre_marker_failure_consumes_attempt": False,
            "post_marker_attempt_consumed": True,
            "max_turn_start_transport_writes": 1,
            "retry_budget": 0,
            "automatic_retry": False,
            "replacement_attempt_under_same_lock": False,
            "turn_timeout_seconds": 90,
            "timeout_extension_after_marker": False,
        },
        "evidence_requirements": {
            "required_artifacts": [
                "predispatch_admission.json",
                "attempt_consumed.marker",
                "codex_protocol.jsonl",
                "cgw_route_evidence.jsonl",
                "runner_evidence.json",
                "verification.json",
            ],
            "conditional_artifacts": ["result.json"],
            "required_identity_fields": [
                "study_id",
                "attempt_id",
                "execution_config_hash",
                "codex_binary_sha256",
                "cgw_binary_sha256",
                "cgw_release",
                "cgw_source_commit",
                "bridge_config_sha256",
                "codex_config_sha256",
                "route_id",
                "bridge_mode",
                "connector",
                "model_slug",
                "backend_model",
                "outer_codex_thread_id",
                "outer_codex_turn_id",
            ],
            "required_route_fields": [
                "bridge_request_id",
                "browser_surface_or_lease_identity",
                "chatgpt_turn_or_qualified_response_binding",
                "terminal_status",
                "no_model_substitution",
                "no_transport_substitution",
                "bridge_side_effects_performed_false",
            ],
            "required_mcp_roundtrip_fields": [
                "at_least_one_live_roundtrip",
                "connector_identity",
                "outer_codex_turn_id",
                "capability_token_digest_only",
                "tool_invocation_id",
                "exact_tool_name",
                "executor_codex",
                "tool_result_digest",
            ],
            "secrets_forbidden": [
                "raw_cookies",
                "raw_auth_tokens",
                "raw_tunnel_credentials",
                "raw_capability_tokens",
                "browser_storage_state",
            ],
            "result_evidence": [
                "result_exists",
                "result_sha256",
                "result_schema_valid",
                "result_values_correct",
                "input_unchanged",
                "task_unchanged",
                "workspace_post_listing",
            ],
        },
        "decision": {
            "scientific_metrics": [
                "executor_completed",
                "result_schema_valid",
                "result_values_correct",
                "mutation_scope_valid",
                "attempt_attribution_valid",
                "evidence_integrity_valid",
            ],
            "pass": "all six scientific metrics equal 1 and route evidence admission passes",
            "fail": (
                "execution attributable and structurally valid, executor completed, and one or more "
                "substantive task metrics result_schema_valid/result_values_correct/mutation_scope_valid equal 0"
            ),
            "invalid": [
                "terminal_failed_without_admitted_result",
                "timeout",
                "infrastructure_or_protocol_failure",
                "authority_violation",
                "route_or_model_substitution",
                "missing_or_ambiguous_browser_response_binding",
                "missing_live_mcp_roundtrip",
                "evidence_integrity_failure",
                "missing_required_metric",
                "verifier_inability",
            ],
        },
        "no_rescue": {
            "after_marker": [
                "no_retry",
                "no_prompt_or_task_mutation",
                "no_model_change",
                "no_mode_change",
                "no_connector_change",
                "no_timeout_extension",
                "no_permission_widening",
                "no_route_fallback",
                "no_observability_mutation",
            ],
            "successor_requires_new_lineage": True,
        },
        "local_root": "g2e/.local/P5A-CGW-FX001-V4-001",
        "authorization": {
            "preregistration_complete": True,
            "model_turn": False,
            "functional_attempt": False,
            "scientific_attempt": False,
            "comparative_ab": False,
            "next": "STATIC_PREREGISTRATION_QA_THEN_CREATE_EXECUTION_ENVELOPE_LOCK",
        },
    }
    contract["contract_sha256"] = canonical_sha256(contract)
    return contract


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="P5A_CGW_FX001_PREREGISTRATION.json")
    args = parser.parse_args()
    report = build_preregistration()
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": report["status"],
        "study_id": report["study_id"],
        "attempt_id": report["attempt_id"],
        "contract_sha256": report["contract_sha256"],
        "model_turn": report["authorization"]["model_turn"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
