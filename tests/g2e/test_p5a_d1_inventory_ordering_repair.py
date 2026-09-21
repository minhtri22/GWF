from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADJ_PATH = ROOT / "scripts" / "g2e" / "p5a_adjudicate_d1.py"
REPAIR_SPEC = ROOT / "g2e" / "docs" / "P5A_D1_INVENTORY_ORDERING_INVALIDITY_REPAIR.md"


def _load_adjudicator():
    spec = importlib.util.spec_from_file_location("p5a_adjudicate_d1_repair", ADJ_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _inventory(module, *, windows_order: bool = True):
    files = [
        {"path": "ClientRequest.json", "sha256": "a" * 64, "size": 10},
        {"path": "codex_app_server_protocol.schemas.json", "sha256": "b" * 64, "size": 20},
        {"path": "CommandExecutionRequestApprovalParams.json", "sha256": "c" * 64, "size": 30},
        {"path": "v2/ItemCompletedNotification.json", "sha256": "d" * 64, "size": 40},
    ]
    if not windows_order:
        files = [files[0], files[2], files[1], files[3]]
    return files, module._canonical_inventory_digest(files)


def _bundle(module, *, platform_system: str, windows_order: bool):
    files, digest = _inventory(module, windows_order=windows_order)
    return {
        "schema": "G2E-P5A-CODEX-DISCOVERY-v1",
        "status": "D1_MINIMUM_QUALIFIED",
        "observed_at": "2026-09-21T11:00:00Z",
        "platform": {"system": platform_system, "release": "fixture", "machine": "AMD64", "python": "3.12"},
        "codex_command": "codex",
        "executable_path": "C:/fixture/codex.exe",
        "executable_sha256": "e" * 64,
        "codex_version_stdout": "codex-cli 1.2.3",
        "codex_version_stderr_sha256": "f" * 64,
        "app_server_help_exit_code": 0,
        "app_server_help_sha256": "1" * 64,
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
        "optional_protocol_tokens": {},
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


def test_repair_spec_binds_original_invalidity_without_recollection():
    text = REPAIR_SPEC.read_text(encoding="utf-8")
    assert "ba098a56be39e996488e5a543af8c373199f8b4cc66f922be6d7bc6386c6e860" in text
    assert "INVENTORY_PATHS_NOT_SORTED" in text
    assert "Fresh Codex recollection:** PROHIBITED" in text
    assert "does **not**" in text
    assert "change any required protocol token" in text


def test_windows_path_order_from_qualified_probe_is_accepted():
    module = _load_adjudicator()
    bundle = _bundle(module, platform_system="Windows", windows_order=True)
    result = module.adjudicate_data(bundle, "2" * 64, "3" * 64)
    assert result["verdict"] == "PASS"
    assert result["reason_codes"] == []


def test_windows_inventory_in_posix_order_is_rejected():
    module = _load_adjudicator()
    bundle = _bundle(module, platform_system="Windows", windows_order=False)
    result = module.adjudicate_data(bundle, "2" * 64, "3" * 64)
    assert result["verdict"] == "INVALID"
    assert "INVENTORY_PATHS_NOT_SORTED" in result["reason_codes"]


def test_same_windows_order_is_rejected_for_linux_probe_semantics():
    module = _load_adjudicator()
    bundle = _bundle(module, platform_system="Linux", windows_order=True)
    result = module.adjudicate_data(bundle, "2" * 64, "3" * 64)
    assert result["verdict"] == "INVALID"
    assert "INVENTORY_PATHS_NOT_SORTED" in result["reason_codes"]


def test_posix_order_is_accepted_for_linux_probe_semantics():
    module = _load_adjudicator()
    bundle = _bundle(module, platform_system="Linux", windows_order=False)
    result = module.adjudicate_data(bundle, "2" * 64, "3" * 64)
    assert result["verdict"] == "PASS"


def test_repair_does_not_rescue_digest_mismatch():
    module = _load_adjudicator()
    bundle = _bundle(module, platform_system="Windows", windows_order=True)
    bundle["schema_inventory_digest"] = "0" * 64
    result = module.adjudicate_data(bundle, "2" * 64, "3" * 64)
    assert result["verdict"] == "INVALID"
    assert "SCHEMA_INVENTORY_DIGEST_MISMATCH" in result["reason_codes"]


def test_repair_does_not_rescue_required_token_contradiction():
    module = _load_adjudicator()
    bundle = _bundle(module, platform_system="Windows", windows_order=True)
    bundle["required_protocol_tokens"]["turn/start"] = False
    result = module.adjudicate_data(bundle, "2" * 64, "3" * 64)
    assert result["verdict"] == "INVALID"
    assert "REQUIRED_TOKEN_FALSE:turn/start" in result["reason_codes"]


def test_repair_does_not_rescue_sensitive_field():
    module = _load_adjudicator()
    bundle = _bundle(module, platform_system="Windows", windows_order=True)
    bundle["initialize_handshake"]["sanitized_response"]["metadata"]["accountEmail"] = "x@example.com"
    result = module.adjudicate_data(bundle, "2" * 64, "3" * 64)
    assert result["verdict"] == "INVALID"
    assert "FORBIDDEN_SENSITIVE_FIELD" in result["reason_codes"]


def test_repair_keeps_recognized_discovery_failure_as_fail():
    module = _load_adjudicator()
    bundle = {
        "schema": "G2E-P5A-CODEX-DISCOVERY-v1",
        "status": "HARNESS_NOT_FOUND",
        "secrets_persisted": False,
        "functional_task_executed": False,
        "errors": ["codex executable not found"],
        "limitations": ["D1 structural discovery only"],
    }
    result = module.adjudicate_data(bundle, "2" * 64, "3" * 64)
    assert result["verdict"] == "FAIL"


def test_repair_adjudicator_still_has_no_execution_path():
    source = ADJ_PATH.read_text(encoding="utf-8")
    forbidden = (
        "subprocess",
        "ProofObligation",
        "ExecutionAttemptEnvelope",
        "AgentBinding",
        "Popen(",
        "os.system",
        "shutil.which",
    )
    for token in forbidden:
        assert token not in source
