from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_route_instance_probe.ps1"
POST = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_ROUTE_PATH_POSTMORTEM.md"
DESIGN = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_ROUTE_PATH_INSTRUMENTATION_DESIGN.json"


def test_postmortem_does_not_authorize_replacement():
    s = POST.read_text(encoding="utf-8")
    assert "HISTORICAL_ROUTE_UNIDENTIFIABLE" in s
    assert "OBSERVABILITY_INSTANCE_BINDING_GAP_PROVEN" in s
    assert "does **not** authorize a replacement scientific attempt" in s


def test_design_keeps_science_closed():
    d = json.loads(DESIGN.read_text(encoding="utf-8"))
    assert d["parent_final_classification"] == "INVALID_SPENT"
    assert d["status"] == "DESIGNED_NOT_YET_SCIENTIFICALLY_ACTIVATED"
    assert "model_execution" in d["prohibited"]
    assert "replacement_attempt_activation" in d["prohibited"]
    assert len(d["gates"]) == 4
    assert d["evidence_policy"]["no_synthetic_route_events"] is True
    assert d["evidence_policy"]["ingress_witness_required"] is True
    assert d["evidence_policy"]["pid_binding_required"] is True


def test_instance_probe_is_zero_science_and_get_only():
    s = PROBE.read_text(encoding="utf-8")
    assert 'model_execution = $false' in s
    assert 'browser_submission = $false' in s
    assert 'mcp_invocation = $false' in s
    assert '.GetAsync("http://127.0.0.1:$ExpectedPort/v1/responses")' in s
    assert "Add-Type -AssemblyName System.Net.Http" in s
    assert "PostAsync(" not in s
    assert "turn/start" not in s
    assert "attempt_consumed.marker" not in s
    assert "P5A-CGW-FX001-TC-003" not in s


def test_instance_probe_binds_pid_chain_and_sinks():
    s = PROBE.read_text(encoding="utf-8")
    for token in (
        "listener_pid_matches_health",
        "daemon_pid_matches_health",
        "daemon_parent_matches_owner",
        "launcher_log_bound_to_daemon_pid",
        "browser_descriptor_exists",
        "responses_get_returns_426",
        "PASS_INSTANCE_BOUND_ZERO_SCIENCE",
    ):
        assert token in s


def test_instance_probe_preserves_ordered_dictionary_identity():
    s = PROBE.read_text(encoding="utf-8")
    assert "[System.Collections.IDictionary]$Checks" in s
    assert "add_check_shared_container" in s
    assert 'verdict = "INVALID_HARNESS_CONTAINER_BINDING"' in s
    assert "[hashtable]$Checks" not in s
