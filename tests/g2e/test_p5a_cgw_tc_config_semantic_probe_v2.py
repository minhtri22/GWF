from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "scripts" / "g2e" / "p5a_cgw_tc_config_semantic_probe_v2.py"
PLAN = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC_CONFIG_SEMANTIC_PROBE_V2_PLAN.md"


def test_v2_is_strictly_offline_and_redacted():
    s = PROBE.read_text(encoding="utf-8")
    for forbidden in ("urllib", "requests", "http://", "/v1/responses", "turn/start"):
        assert forbidden not in s
    assert '"network_request": False' in s
    assert '"control_token_shape_valid"' in s
    assert '"tunnel_id_shape_valid"' in s
    assert '"runtime_key_path_absolute"' in s
    assert '"control_token":' not in s
    assert '"tunnel_id":' not in s
    assert '"runtime_key_file":' not in s


def test_v2_binds_prior_healthy_snapshot_by_provenance_hash_only():
    s = PROBE.read_text(encoding="utf-8")
    assert "6f4347acdcb722d52b2ea4bb166a53c28a809fdf13bb9f358e794bad12c16053" in s
    assert '"health_snapshot_provenance_join"' in s
    assert "raw_hash == EXPECTED_HEALTH_JOIN_SHA256" in s
    plan = PLAN.read_text(encoding="utf-8")
    assert "not promoted to a" in plan
    assert "normative transport invariant" in plan


def test_v2_matches_upstream_durable_runtime_command_constraints():
    s = PROBE.read_text(encoding="utf-8")
    for token in (
        '"runtime_executable_absolute"',
        '"runtime_executable_exists"',
        '"runtime_no_ephemeral_absolute_component"',
    ):
        assert token in s
    assert "tempfile.gettempdir()" in s


def test_v2_requires_full_semantic_contract_and_no_science_rerun():
    s = PROBE.read_text(encoding="utf-8")
    for token in (
        '"config_version_3"',
        '"release_4_0_7"',
        '"mode_full"',
        '"connector_native2"',
        '"browser_host_launcher"',
        '"stall_timeout_transport_compatible"',
        '"auto_approve_false"',
        '"sol_available"',
        '"tunnel_present"',
    ):
        assert token in s
    plan = PLAN.read_text(encoding="utf-8")
    assert "No scientific wrapper rerun is authorized by v2 alone." in plan
