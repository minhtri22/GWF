from __future__ import annotations

import copy
import importlib.util
import tomllib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts" / "g2e" / "p5a_d2s1_profile_materializer.py"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S1_PERMISSION_PROFILE_SUCCESSOR_PREIMPLEMENTATION.md"
QA = ROOT / "g2e" / "docs" / "P5A_D2S1_ZERO_FRESH_SPEC_QA.md"


def _load():
    spec = importlib.util.spec_from_file_location("p5a_d2s1_profile_materializer", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_spec_and_qa_keep_model_turn_prohibited():
    spec_text = SPEC.read_text(encoding="utf-8")
    qa_text = QA.read_text(encoding="utf-8")
    assert "Model turn:** PROHIBITED" in spec_text
    assert "It does **not** authorize a model turn." in spec_text
    assert "Fresh D2-S1 model turn:** NONE" in qa_text
    assert "does not authorize" in qa_text


def test_contract_is_deterministic_and_zero_fresh():
    module = _load()
    first = module.build_contract()
    second = module.build_contract()
    assert first == second
    module.verify_contract(first)
    assert first["model_turn_executed"] is False
    assert first["fresh_outcome_consumed"] is False
    assert first["scientific_attempt_authorized"] is False
    assert first["runtime_adapter_authorized"] is False


def test_exact_successor_identity_and_inherited_fixture():
    module = _load()
    pack = module.build_contract()
    assert pack["attempt_id"] == "p5a-d2s1-p5-fx-001-attempt-001"
    assert pack["profile_id"] == "g2e_p5a_d2s1"
    cfg = pack["execution_config"]
    assert cfg["fixture_id"] == "P5-FX-001"
    assert cfg["input_sha256"] == module.INPUT_SHA256
    assert cfg["task_sha256"] == module.TASK_SHA256
    assert cfg["harness_sha256"] == module.HARNESS_SHA256
    assert cfg["codex_release_tag"] == "rust-v0.153.4"
    assert cfg["codex_release_commit"] == "3d2ee51ca2d5db578f328aa75e20aa22c0197c9a"


def test_config_toml_is_exact_restricted_profile():
    module = _load()
    raw = module.build_config_toml()
    parsed = tomllib.loads(raw.decode("utf-8"))
    assert parsed["default_permissions"] == module.PROFILE_ID
    assert parsed["windows"]["sandbox"] == "elevated"
    profile = parsed["permissions"][module.PROFILE_ID]
    assert "extends" not in profile
    assert profile["network"]["enabled"] is False

    root = module.CANONICAL_WINDOWS_WORKSPACE
    assert profile["filesystem"] == {
        root + r"\input.json": "read",
        root + r"\TASK.md": "read",
        root + r"\result.json": "write",
    }


def test_thread_and_turn_use_named_profile_without_legacy_sandbox_fields():
    module = _load()
    pack = module.build_contract()

    assert pack["initialize_params"]["capabilities"]["experimentalApi"] is True

    thread = pack["thread_start_params"]
    assert thread["permissions"] == module.PROFILE_ID
    assert thread["approvalPolicy"] == "never"
    assert "sandbox" not in thread
    assert "permissionProfile" not in thread

    turn = pack["turn_start_shape"]
    assert turn["approvalPolicy"] == "never"
    assert "sandboxPolicy" not in turn
    assert "permissionProfile" not in turn
    assert "permissions" not in turn


def test_permission_profile_list_is_bound_to_exact_cwd():
    module = _load()
    pack = module.build_contract()
    assert pack["permission_profile_list_params"] == {
        "cursor": None,
        "limit": 100,
        "cwd": module.CANONICAL_WINDOWS_WORKSPACE,
    }


def test_execution_config_covers_profile_and_zero_retry():
    module = _load()
    pack = module.build_contract()
    cfg = pack["execution_config"]
    assert cfg["experimental_api"] is True
    assert cfg["permission_profile_id"] == module.PROFILE_ID
    assert cfg["default_permission_profile_id"] == module.PROFILE_ID
    assert cfg["windows_sandbox_mode"] == "elevated"
    assert cfg["windows_sandbox_setup_required"] is True
    assert cfg["windows_sandbox_setup_cwd"] == module.CANONICAL_WINDOWS_WORKSPACE
    assert cfg["windows_sandbox_readiness_required"] == "ready"
    assert cfg["network_allowed"] is False
    assert cfg["interactive_approval_allowed"] is False
    assert cfg["mcp_count_required"] == 0
    assert cfg["installed_app_count_required"] == 0
    assert cfg["runtime_support_read_policy"] == "exact-harness-support-only-v1"
    assert cfg["max_invalid_replacement_attempts"] == 0
    module.verify_contract(pack)


@pytest.mark.parametrize(
    "mutator,match",
    [
        (lambda p: p.__setitem__("model_turn_executed", True), "model turn present"),
        (lambda p: p.__setitem__("fresh_outcome_consumed", True), "fresh outcome present"),
        (lambda p: p.__setitem__("scientific_attempt_authorized", True), "must not authorize"),
        (
            lambda p: p["execution_config"].__setitem__("network_allowed", True),
            "network authority drift",
        ),
        (
            lambda p: p["execution_config"].__setitem__("default_permission_profile_id", ":workspace"),
            "default permission selection drift",
        ),
        (
            lambda p: p["execution_config"].__setitem__("windows_sandbox_mode", "unelevated"),
            "windows sandbox mode drift",
        ),
        (
            lambda p: p["execution_config"].__setitem__("windows_sandbox_setup_required", False),
            "windows sandbox setup requirement drift",
        ),
        (
            lambda p: p["execution_config"].__setitem__("max_invalid_replacement_attempts", 1),
            "retry budget drift",
        ),
        (
            lambda p: p["thread_start_params"].__setitem__("sandbox", "workspace-write"),
            "thread sandbox must be omitted",
        ),
        (
            lambda p: p["turn_start_shape"].__setitem__("sandboxPolicy", {"type": "workspaceWrite"}),
            "forbidden turn field",
        ),
    ],
)
def test_verifier_fails_closed_on_governance_drift(mutator, match):
    module = _load()
    pack = copy.deepcopy(module.build_contract())
    mutator(pack)
    with pytest.raises(ValueError, match=match):
        module.verify_contract(pack)


def test_materializer_refuses_output_outside_local_root(tmp_path: Path):
    module = _load()
    local_root = tmp_path / "local"
    local_root.mkdir()
    outside = tmp_path / "outside"
    with pytest.raises(ValueError, match="REFUSED_OUTSIDE_LOCAL_ROOT"):
        module.materialize(local_root, outside, module.CANONICAL_WINDOWS_WORKSPACE)


def test_materializer_writes_only_profile_contract(tmp_path: Path):
    module = _load()
    local_root = tmp_path / "local"
    local_root.mkdir()
    output = local_root / "profile-pack"
    pack = module.materialize(local_root, output, module.CANONICAL_WINDOWS_WORKSPACE)

    assert {p.name for p in output.iterdir()} == {
        "config.toml",
        "P5A_D2S1_PROFILE_MATERIALIZATION.json",
    }
    assert pack["scientific_attempt_authorized"] is False
    assert not (output / "result.json").exists()


def test_builder_contains_no_execution_path():
    source = BUILDER.read_text(encoding="utf-8")
    forbidden = (
        "subprocess",
        "Popen(",
        "turn/start",
        "thread/start",
        "codex app-server",
        "requests.",
        "httpx.",
    )
    for token in forbidden:
        assert token not in source
