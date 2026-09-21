from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts" / "g2e" / "p5a_d2_final_admission.py"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2_FINAL_ADMISSION_MATERIALIZATION_AND_ZERO_FRESH_QUALIFICATION.md"


def _load():
    spec = importlib.util.spec_from_file_location("p5a_d2_final_admission", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_spec_freezes_no_model_turn_boundary():
    text = SPEC.read_text(encoding="utf-8")
    assert "D2 model turn during this phase:** PROHIBITED" in text
    assert "Codex runtime adapter:** NOT AUTHORIZED" in text
    assert "FINAL_ADMISSION_PASS" in text
    assert "No model turn occurs in this qualification phase." in text


def test_final_admission_materialization_is_deterministic_and_valid():
    module = _load()
    first = module.build_final_admission()
    second = module.build_final_admission()
    assert first == second
    module.verify_final_admission(first)
    assert first["model_turn_executed"] is False
    assert first["fresh_outcome_consumed"] is False
    assert first["runtime_adapter_authorized"] is False
    assert first["d2_scientific_attempts_authorized_after_gate"] == 1


def test_exact_p5_fx_001_graph_is_frozen():
    module = _load()
    pack = module.build_final_admission()
    assert pack["refs"]["manifest"]["content_hash"] == module.MANIFEST_HASH
    assert pack["refs"]["proof"]["content_hash"] == module.PROOF_HASH
    assert pack["qualification_authority_grant"]["attempt_id"] == module.ATTEMPT_ID
    assert pack["final_agent_binding"]["resolved_attempt_id"] == module.ATTEMPT_ID
    assert pack["predispatch_attempt"]["attempt_id"] == module.ATTEMPT_ID
    assert pack["predispatch_attempt"]["state"] == "LOCKED"
    assert tuple(pack["final_agent_binding"]["required_capability_ids"]) == module.REQUIRED_PREREQUISITES
    assert tuple(pack["final_agent_binding"]["qualification_target_capability_ids"]) == module.QUALIFICATION_TARGETS
    assert tuple(pack["final_agent_binding"]["authority_scope"]) == module.GRANTED_AUTHORITY


def test_authority_policy_is_exactly_two_actions_for_one_role():
    module = _load()
    pack = module.build_final_admission()
    actions = pack["authority_policy"]["actions"]
    assert actions == [
        {"action": "READ_FROZEN_FIXTURE", "allowed_roles": ["qualification_executor"]},
        {"action": "WRITE_DESIGNATED_OUTPUT", "allowed_roles": ["qualification_executor"]},
    ]
    assert pack["authority_policy"]["delegated_authority_may_exceed_parent"] is False


def test_grant_paths_and_side_effects_are_exact():
    module = _load()
    pack = module.build_final_admission()
    grant = pack["qualification_authority_grant"]
    assert tuple(grant["allowed_read_paths"]) == module.READ_PATHS
    assert tuple(grant["allowed_write_paths"]) == module.WRITE_PATHS
    assert tuple(grant["granted_authority_scope"]) == module.GRANTED_AUTHORITY
    assert grant["network_allowed"] is False
    assert grant["interactive_approval_allowed"] is False
    assert grant["may_imply_capability_available"] is False
    assert grant["may_be_reused_for_operational_binding"] is False


def test_execution_config_hash_covers_exact_frozen_contract():
    module = _load()
    pack = module.build_final_admission()
    config = pack["execution_config"]
    assert config["input_sha256"] == module.INPUT_SHA256
    assert config["task_sha256"] == module.TASK_SHA256
    assert config["harness_sha256"] == module.HARNESS_SHA256
    assert config["max_invalid_replacement_attempts"] == 0
    assert config["network_allowed"] is False
    assert config["interactive_approval_allowed"] is False
    assert pack["execution_config_hash"] == module._sha256_json(config)
    assert pack["predispatch_attempt"]["config_hash"] == pack["execution_config_hash"]


@pytest.mark.parametrize(
    "mutator,match",
    [
        (lambda p: p["refs"]["proof"].__setitem__("content_hash", "0" * 64), "proof exact ref drift"),
        (lambda p: p["refs"]["manifest"].__setitem__("content_hash", "0" * 64), "manifest exact ref drift"),
        (lambda p: p["execution_config"].__setitem__("input_sha256", "0" * 64), "fixture or task hash drift"),
        (lambda p: p["execution_config"].__setitem__("task_sha256", "0" * 64), "fixture or task hash drift"),
        (lambda p: p["execution_config"].__setitem__("network_allowed", True), "side-effect policy drift"),
        (lambda p: p["execution_config"].__setitem__("interactive_approval_allowed", True), "side-effect policy drift"),
        (lambda p: p.__setitem__("model_turn_executed", True), "model turn executed before final admission"),
        (lambda p: p.__setitem__("fresh_outcome_consumed", True), "fresh D2 outcome present"),
    ],
)
def test_final_admission_verifier_rejects_top_level_and_config_drift(mutator, match):
    module = _load()
    pack = copy.deepcopy(module.build_final_admission())
    mutator(pack)
    with pytest.raises(ValueError, match=match):
        module.verify_final_admission(pack)


def test_final_admission_verifier_rejects_authority_policy_drift():
    module = _load()
    pack = copy.deepcopy(module.build_final_admission())
    pack["authority_policy"]["actions"][1]["action"] = "ARBITRARY_SHELL"
    with pytest.raises(ValueError):
        module.verify_final_admission(pack)


def test_final_admission_verifier_rejects_grant_and_binding_drift():
    module = _load()

    pack = copy.deepcopy(module.build_final_admission())
    pack["qualification_authority_grant"]["allowed_write_paths"] = ["other.json"]
    with pytest.raises(ValueError):
        module.verify_final_admission(pack)

    pack = copy.deepcopy(module.build_final_admission())
    pack["final_agent_binding"]["authority_scope"] = ["READ_FROZEN_FIXTURE"]
    with pytest.raises(ValueError):
        module.verify_final_admission(pack)

    pack = copy.deepcopy(module.build_final_admission())
    pack["final_agent_binding"]["qualification_target_capability_ids"] = ["repository_read"]
    with pytest.raises(ValueError):
        module.verify_final_admission(pack)


def test_final_admission_verifier_rejects_attempt_identity_and_harness_drift():
    module = _load()

    pack = copy.deepcopy(module.build_final_admission())
    pack["predispatch_attempt"]["attempt_id"] = "attempt-other"
    with pytest.raises(ValueError):
        module.verify_final_admission(pack)

    pack = copy.deepcopy(module.build_final_admission())
    pack["predispatch_attempt"]["harness_ref"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError):
        module.verify_final_admission(pack)


def test_target_capabilities_remain_unavailable_before_d2():
    module = _load()
    _, manifest, _, _ = module.inherited_contract()
    caps = {cap.capability_id: cap for cap in manifest.capabilities}
    assert caps["repository_read"].available is False
    assert caps["repository_write"].available is False
    assert caps["repository_read"].qualification_refs == ()
    assert caps["repository_write"].qualification_refs == ()


def test_materializer_writes_only_governance_objects(tmp_path: Path):
    module = _load()
    pack = module.materialize(tmp_path)
    expected = {
        "P5A_D2_AUTHORITY_POLICY.json",
        "P5A_D2_QUALIFICATION_AUTHORITY_GRANT.json",
        "P5A_D2_FINAL_AGENT_BINDING.json",
        "P5A_D2_PREDISPATCH_ATTEMPT.json",
        "P5A_D2_FINAL_ADMISSION.json",
    }
    assert {path.name for path in tmp_path.iterdir()} == expected
    assert not any("result" in path.name.lower() for path in tmp_path.iterdir())
    assert pack["model_turn_executed"] is False


def test_final_admission_builder_has_no_execution_or_network_path():
    source = BUILDER.read_text(encoding="utf-8")
    forbidden = (
        "subprocess",
        "Popen(",
        "os.system",
        "shutil.which",
        "requests.",
        "httpx.",
        "thread/start",
        "turn/start",
        "codex app-server",
    )
    for token in forbidden:
        assert token not in source
