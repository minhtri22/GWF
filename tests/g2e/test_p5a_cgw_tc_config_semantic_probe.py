from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "scripts" / "g2e" / "p5a_cgw_tc_config_semantic_probe.py"
PLAN = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC_CONFIG_SEMANTIC_PROBE_PLAN.md"


def test_probe_is_read_only_and_redacts_sensitive_values():
    s = PROBE.read_text(encoding="utf-8")
    assert 'urlopen(HEALTH_URL' in s
    assert '/v1/responses' not in s
    assert 'turn/start' not in s
    assert 'attempt_consumed.marker' not in s
    assert 'controlToken")' in s
    assert '"control_token_shape_valid"' in s
    assert '"tunnel_id_shape_valid"' in s
    assert '"runtime_key_path_absolute"' in s
    assert 'raw["controlToken"]' in s
    assert '"control_token":' not in s
    assert '"tunnel_id":' not in s
    assert '"runtime_key_file":' not in s


def test_probe_checks_transport_and_authority_semantics():
    s = PROBE.read_text(encoding="utf-8")
    for token in (
        '"release_4_0_7"',
        '"mode_full"',
        '"connector_native2"',
        '"browser_host_launcher"',
        '"stall_timeout_transport_compatible"',
        '"auto_approve_false"',
        '"sol_available"',
        '"tunnel_present"',
        '"health_accepting"',
        '"health_idle"',
    ):
        assert token in s
    assert 'stall is None or stall == 300' in s


def test_plan_forbids_scientific_rerun_from_probe_alone():
    s = PLAN.read_text(encoding="utf-8")
    assert "No rerun of the TC scientific wrapper is authorized by this probe alone." in s
    assert "RESERVED_UNCONSUMED" in s
    assert "must not be deleted or reused" in s
