from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADJ_PATH = ROOT / "scripts" / "g2e" / "p5a_adjudicate_d1.py"
LOCK_PATH = ROOT / "g2e" / "docs" / "P5A_D1_ADJUDICATION_LOCK.md"


def _load_adjudicator():
    spec = importlib.util.spec_from_file_location("p5a_adjudicate_d1", ADJ_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _inventory(module):
    files = [
        {"path": "ClientRequest.json", "sha256": "a" * 64, "size": 10},
        {"path": "ServerNotification.json", "sha256": "b" * 64, "size": 20},
    ]
    return files, module._canonical_inventory_digest(files)


def _pass_bundle(module):
    files, digest = _inventory(module)
    return {
        "schema": "G2E-P5A-CODEX-DISCOVERY-v1",
        "status": "D1_MINIMUM_QUALIFIED",
        "observed_at": "2026-09-21T11:00:00Z",
        "platform": {"system": "Windows", "release": "fixture", "machine": "AMD64", "python": "3.12"},
        "codex_command": "codex",
        "executable_path": "C:/fixture/codex.exe",
        "executable_sha256": "c" * 64,
        "codex_version_stdout": "codex-cli 1.2.3",
        "codex_version_stderr_sha256": "d" * 64,
        "app_server_help_exit_code": 0,
        "app_server_help_sha256": "e" * 64,
        "schema_generation_exit_code": 0,
        "generated_schema_files": files,
        "schema_inventory_digest": digest,
        "required_protocol_tokens": {
            "initialize": True,
            "thread/start": True,
            "thread/resume": True,
            "turn/start": True,
            "item/started": True,
            "item/completed": True,
        },
        "optional_protocol_tokens": {"thread/fork": True},
        "initialize_handshake": {
            "success": True,
            "sanitized_response": {
                "response_id": 1,
                "result_present": True,
                "metadata": {
                    "userAgent": "fixture",
                    "platformFamily": "windows",
                    "platformOs": "windows",
                },
            },
            "error": None,
        },
        "secrets_persisted": False,
        "functional_task_executed": False,
        "errors": [],
        "limitations": ["D1 structural discovery only"],
    }


def test_d1_lock_is_zero_fresh_and_forbids_rescue():
    text = LOCK_PATH.read_text(encoding="utf-8")
    assert "Fresh actual-harness evidence consumed:** NONE" in text
    assert "D1 is PASS if and only if" in text
    assert "D1 is FAIL" in text
    assert "D1 is INVALID" in text
    assert "changing required protocol tokens" in text
    assert "rerunning until PASS" in text


def test_d1_adjudicator_passes_exact_consistent_bundle():
    module = _load_adjudicator()
    bundle = _pass_bundle(module)
    result = module.adjudicate_data(bundle, "1" * 64, "2" * 64)
    assert result["verdict"] == "PASS"
    assert result["reason_codes"] == []
    assert result["codex_profile_available_for_d1_surface"] is True
    assert result["d2_authorized"] is False
    assert result["runtime_adapter_authorized"] is False


def test_d1_adjudicator_fails_recognized_nonpass_discovery():
    module = _load_adjudicator()
    bundle = {
        "schema": "G2E-P5A-CODEX-DISCOVERY-v1",
        "status": "HARNESS_NOT_FOUND",
        "secrets_persisted": False,
        "functional_task_executed": False,
        "errors": ["codex executable not found"],
        "limitations": ["D1 structural discovery only"],
    }
    result = module.adjudicate_data(bundle, "1" * 64, "2" * 64)
    assert result["verdict"] == "FAIL"
    assert result["codex_profile_available_for_d1_surface"] is False


def test_d1_adjudicator_invalidates_digest_mismatch():
    module = _load_adjudicator()
    bundle = _pass_bundle(module)
    bundle["schema_inventory_digest"] = "0" * 64
    result = module.adjudicate_data(bundle, "1" * 64, "2" * 64)
    assert result["verdict"] == "INVALID"
    assert "SCHEMA_INVENTORY_DIGEST_MISMATCH" in result["reason_codes"]


def test_d1_adjudicator_invalidates_required_token_contradiction():
    module = _load_adjudicator()
    bundle = _pass_bundle(module)
    bundle["required_protocol_tokens"]["turn/start"] = False
    result = module.adjudicate_data(bundle, "1" * 64, "2" * 64)
    assert result["verdict"] == "INVALID"
    assert "REQUIRED_TOKEN_FALSE:turn/start" in result["reason_codes"]


def test_d1_adjudicator_invalidates_unsorted_or_duplicate_inventory():
    module = _load_adjudicator()
    bundle = _pass_bundle(module)
    bundle["generated_schema_files"] = list(reversed(bundle["generated_schema_files"]))
    bundle["schema_inventory_digest"] = module._canonical_inventory_digest(bundle["generated_schema_files"])
    result = module.adjudicate_data(bundle, "1" * 64, "2" * 64)
    assert result["verdict"] == "INVALID"
    assert "INVENTORY_PATHS_NOT_SORTED" in result["reason_codes"]


def test_d1_adjudicator_invalidates_forbidden_secret_or_account_field():
    module = _load_adjudicator()
    bundle = _pass_bundle(module)
    bundle["initialize_handshake"]["sanitized_response"]["metadata"]["accountEmail"] = "x@example.com"
    result = module.adjudicate_data(bundle, "1" * 64, "2" * 64)
    assert result["verdict"] == "INVALID"
    assert "FORBIDDEN_SENSITIVE_FIELD" in result["reason_codes"]


def test_d1_adjudicator_file_fingerprints_input_and_writes_separate_result(tmp_path: Path):
    module = _load_adjudicator()
    bundle = _pass_bundle(module)
    source = tmp_path / "P5A_CODEX_DISCOVERY.json"
    target = tmp_path / "P5A_CODEX_D1_ADJUDICATION.json"
    source.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = module.adjudicate_file(source, target)
    assert result["verdict"] == "PASS"
    assert len(result["discovery_input_sha256"]) == 64
    assert len(result["adjudicator_source_sha256"]) == 64
    assert target.exists()


def test_d1_adjudicator_never_executes_codex_or_g2e_runtime():
    source = ADJ_PATH.read_text(encoding="utf-8")
    forbidden = (
        "subprocess",
        "ProofObligation",
        "ExecutionAttemptEnvelope",
        "AgentBinding",
        "thread/start",
        "codex app-server",
    )
    for token in forbidden:
        assert token not in source
