from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
ADMISSION = ROOT / "scripts" / "g2e" / "p5a_d2s3_scientific_admission.py"
RUNNER = ROOT / "scripts" / "g2e" / "p5a_d2s3_scientific_runner.py"
VERIFIER = ROOT / "scripts" / "g2e" / "p5a_d2s3_scientific_verify.py"
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_d2s3_scientific_oneclick.ps1"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S3_SCIENTIFIC_EXECUTION_MACRO_SPEC.md"


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


def test_successor_admission_is_deterministic_and_binds_official_harness():
    module = _load(ADMISSION, "d2s3_admission")
    discovery = fake_discovery()
    first = module.build_final_admission(discovery)
    second = module.build_final_admission(discovery)
    assert first == second
    module.verify_final_admission(first, discovery)

    assert first["attempt_id"] == module.ATTEMPT_ID
    assert first["final_agent_binding"]["harness_ref"] == f"sha256:{module.HARNESS_SHA256}"
    assert first["predispatch_attempt"]["harness_ref"] == f"sha256:{module.HARNESS_SHA256}"
    assert first["execution_config"]["r2_evidence_sha256"] == module.R2_EVIDENCE_SHA256
    assert first["execution_config"]["max_invalid_replacement_attempts"] == 0
    assert first["authorization"]["exact_scientific_attempts_authorized_after_lock"] == 1
    assert first["authorization"]["retry_authorized"] is False


def test_successor_manifest_does_not_prematurely_claim_functional_capability():
    module = _load(ADMISSION, "d2s3_admission_manifest")
    pack = module.build_final_admission(fake_discovery())
    caps = {
        item["capability_id"]: item["available"]
        for item in pack["manifest"]["capabilities"]
    }
    assert caps["repository_read"] is False
    assert caps["repository_write"] is False
    assert caps["app_server_launch"] is True
    assert caps["jsonrpc_initialize"] is True
    assert caps["turn_stream_surface"] is True


def test_successor_structural_discovery_rejects_old_or_unqualified_harness():
    module = _load(ADMISSION, "d2s3_admission_negative")

    with pytest.raises(ValueError, match="official harness SHA256 mismatch"):
        module.build_final_admission(fake_discovery("a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8"))

    bad = fake_discovery()
    bad["status"] = "D1_MINIMUM_NOT_QUALIFIED"
    with pytest.raises(ValueError, match="not qualified"):
        module.build_final_admission(bad)


def test_admission_builder_has_no_runtime_dispatch_surface():
    source = ADMISSION.read_text(encoding="utf-8")
    for token in (
        "subprocess",
        "Popen(",
        "os.system",
        '"method": "turn/start"',
        '"method": "thread/start"',
        "requests.",
        "httpx.",
    ):
        assert token not in source


def test_runner_has_exactly_one_scientific_turn_start_and_marker_precedes_send():
    source = RUNNER.read_text(encoding="utf-8")
    assert source.count('"method": "turn/start"') == 1
    assert source.count("P5A_D2S3_TURN_START_SENT.marker") == 1
    marker_index = source.index("fsync_text(marker_path, marker_text)")
    send_index = source.index('client.send(request)')
    assert marker_index < send_index
    assert 'evidence["scientific_attempt_consumed"] = True' in source[marker_index:send_index]
    assert "R2_AUTHORIZATION_PREDICATE_FAILED" in source
    assert source.count('"permissions": profile_id') == 1
    assert source.count('"permissions": PROFILE_ID') == 0
    assert '"sandboxPolicy"' not in source
    assert "TURN_TIMEOUT_S = 90.0" in source


def test_runner_fresh_control_plane_is_before_attempt_consumption():
    source = RUNNER.read_text(encoding="utf-8")
    control_index = source.index("perform_control_plane(")
    marker_index = source.index("fsync_text(marker_path, marker_text)")
    assert control_index < marker_index
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
    assert "EXPECTED_RESULT_KEYS" in source
    assert "result_schema_valid" in source
    assert "result_values_correct" in source
    assert "mutation_scope_valid" in source
    assert "authority_violation" in source
    assert "replacement_attempt_authorized" in source


def test_oneclick_is_one_shot_and_cleanup_non_bypassable():
    source = ONECLICK.read_text(encoding="utf-8")
    assert "P5A-D2S3-SCIENCE-001" in source
    assert "SCIENTIFIC_ROOT_ALREADY_EXISTS_NO_RETRY" in source
    assert "P5A_D2S3_SCIENTIFIC_EXECUTION_LOCK.json" in source
    assert "retry_authorized" in source
    assert "automatic_retry_authorized" in source

    start = source.index("# PROTECTED_SCIENTIFIC_VHDX_BODY_START")
    end = source.index("# PROTECTED_SCIENTIFIC_VHDX_BODY_END")
    protected = source[start:end]
    assert "Dismount-DiskImage -ImagePath $VhdxPath" in protected
    assert "attached_after_cleanup" in protected
    assert "exit " not in protected
    assert "Remove-Item -LiteralPath $VhdxPath" not in source


def test_oneclick_binds_exact_r2_and_official_instrument():
    source = ONECLICK.read_text(encoding="utf-8")
    for token in (
        "B24AF8E5261BA8E5A90605E7A9B9D63C0025F37650F9A4E657CDAAFD76B0545E",
        "87F18CF15F06EB1BC3E0A9E28F76E3208B2C082C3CD458221242D65DB7B8CC28",
        "444A3F0008050605CAE73CD9B7A2DCAC61294062DFAAB56DD20430FD6498518B",
        "0C3EEB7CEE8D2BC4C8644DEF3C818E8B06760979572DCEDC919C38D0F38F64C4",
    ):
        assert token in source


def test_macro_spec_freezes_single_attempt_and_no_rescue():
    text = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "retry budget: zero" in text.lower()
    assert "Exactly one scientific request is allowed." in text
    assert "marker creation prospectively consumes the single attempt" in text.lower()
    assert "No automatic retry." in text
    assert "verifier does not assign the scientific verdict" in text
