from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_rp_i4_sink_source_binding.py"
DESIGN = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_RP_I4_DESIGN.json"


def load_module():
    spec = spec_from_file_location("rp_i4", SCRIPT)
    mod = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_exact_reviewed_source_blobs_are_frozen():
    mod = load_module()
    assert mod.UPSTREAM_TAG_COMMIT == "b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494"
    assert mod.CRITICAL["src/server.ts"] == "af4cd5c3886f119f35efa4fc0e28bd2ecfc48530"
    assert mod.CRITICAL["src/adapters/chatgpt-web/index.ts"] == "c7e7f291ae6ea6d23818aba8803ad83e39171dbd"
    assert mod.CRITICAL["launcher/electron/runtime-supervisor.cjs"] == "19b19e24b4ab02ae02f762006f750ca9054d7bc6"


def test_pass_requires_package_live_and_source_equivalence():
    s = SCRIPT.read_text(encoding="utf-8")
    assert "manifest_identity_equal" in s
    assert "runtime_files_equal" in s
    assert "critical_equal" in s
    assert 'verdict = "BLOCKED_CUSTOM_CRITICAL_SOURCE_DRIFT"' in s
    assert 'verdict = "PASS_SINK_CONTRACT_BOUND"' in s


def test_probe_is_zero_science_and_has_no_network_client():
    s = SCRIPT.read_text(encoding="utf-8")
    for forbidden in (
        "requests.",
        "urllib.request",
        "http.client",
        "Invoke-RestMethod",
        "/v1/responses",
    ):
        assert forbidden not in s
    assert '"responses_post": False' in s
    assert '"model_execution": False' in s
    assert '"browser_submission": False' in s
    assert '"mcp_invocation": False' in s


def test_design_requires_fail_closed_custom_source_equivalence():
    d = json.loads(DESIGN.read_text(encoding="utf-8"))
    assert d["pass"] == "PASS_SINK_CONTRACT_BOUND"
    assert d["blocked_custom_source_drift"] == "BLOCKED_CUSTOM_CRITICAL_SOURCE_DRIFT"
    assert "replacement attempt activation" in d["prohibited"]
    assert len(d["critical_source_blobs"]) == 10
