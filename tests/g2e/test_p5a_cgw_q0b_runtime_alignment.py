from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "g2e" / "p5a_cgw_q0b_align_runtime_5_0_8.ps1"


def source() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_alignment_is_exactly_4_0_7_to_5_0_8():
    s = source()
    assert '$ExpectedSourceVersion = "4.0.7"' in s
    assert '$TargetVersion = "5.0.8"' in s
    assert "CGW_ALIGNMENT_SOURCE_VERSION_MISMATCH" in s


def test_exact_release_installer_script_is_pinned():
    s = source()
    assert "releases/download/v5.0.8/install-launcher.ps1" in s
    assert "117ab8e5bfba36d3f611e9294355afe70936a536bf3305d4fe563edab7c40a71" in s
    assert "83224d59506462ab2976f437bfaea96b046d4ed55caa7e1cfd6a3d61de0a8ff3" in s
    assert "CODEX_WEB_GPT_VERSION" in s
    assert "PINNED_INSTALLER_SCRIPT_SHA256_MISMATCH" in s


def test_no_latest_release_resolution_in_alignment_wrapper():
    s = source()
    assert "/releases/latest" not in s
    assert "latest/download" not in s


def test_pre_alignment_requires_existing_full_route_contract():
    s = source()
    for token in [
        "127.0.0.1",
        "full",
        "Codex Native2",
        "CGW_ALIGNMENT_AUTO_APPROVAL_NOT_ALLOWED",
        "CODEX_ROUTE_NOT_BOUND_TO_PRE_ALIGNMENT_CGW",
    ]:
        assert token in s


def test_post_alignment_requires_version_health_route_preservation():
    s = source()
    for token in [
        "CGW_5_0_8_POST_ALIGNMENT_HEALTH_NOT_READY",
        "POST_ALIGNMENT_HOST_CHANGED",
        "POST_ALIGNMENT_MODE_CHANGED",
        "POST_ALIGNMENT_CONNECTOR_CHANGED",
        "CODEX_ROUTE_NOT_BOUND_TO_POST_ALIGNMENT_CGW",
    ]:
        assert token in s


def test_wrapper_invokes_fresh_q0b_root_not_consumed_root():
    s = source()
    assert "P5A-CGW-ZERO-MODEL-Q0B-R2" in s
    assert "p5a_cgw_local_zero_model_oneclick.ps1" in s
    assert "LOCAL_ZERO_MODEL_ADMISSION_PASS" in s


def test_wrapper_has_zero_model_firewall():
    s = source()
    assert "model_turn_executed = $false" in s
    assert "responses_endpoint_called = $false" in s
    assert "models_endpoint_called = $false" in s
    assert "scientific_attempt_created = $false" in s
    assert "scientific_attempt_consumed = $false" in s
    assert "turn/start" not in s
    assert not re.search(r"Invoke-(?:RestMethod|WebRequest)[^\r\n]+/v1/(?:responses|models)", s, re.I)


def test_wrapper_refuses_overwrite_and_requires_launcher_quit():
    s = source()
    assert "P5A_CGW_Q0B_ALIGNMENT_ROOT_ALREADY_EXISTS" in s
    assert "QUIT_CODEX_WEB_GPT_BEFORE_RUNTIME_ALIGNMENT" in s
