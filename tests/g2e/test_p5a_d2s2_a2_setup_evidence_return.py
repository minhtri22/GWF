from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COLLECTOR = ROOT / "scripts" / "g2e" / "p5a_d2s2_a2_setup_evidence_return.ps1"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S2_A2_SETUP_EVIDENCE_RETURN_SPEC.md"


def test_collector_binds_exact_a2_artifacts():
    source = COLLECTOR.read_text(encoding="utf-8")
    assert "2DD26DD7CE3A337307147C4BE82DA1F653AB76048ABF3CBA6BCA7C0C8555C5D8" in source
    assert "984F828C4796B77D7BD125D5E5A8421C04F9B496D9117B6F1F5003D9B8A1E2C3" in source
    assert "17bf616138433f96ee3447e8f846aad430df3771" in source
    assert "c714da50f577fad5e4fdd7b64ede894330459243" in source
    assert "8d449867586663195a998ce6eefbcbf8a218030f" in source


def test_collector_reads_only_fixed_a2_local_tree():
    source = COLLECTOR.read_text(encoding="utf-8")
    assert 'g2e\\.local\\P5A-D2S2-A2' in source
    assert "P5A_D2S2_A2_ONECLICK_REPORT.json" in source
    assert "evidence\\preturn-a2" in source
    assert "P5A_D2S2_A2_PREFLIGHT_PROTOCOL_SANITIZED.jsonl" in source
    assert "P5A_D2S2_A2_PREFLIGHT_STDERR_HASHES.jsonl" in source
    assert "A2_EVIDENCE_PATH_OUTSIDE_FIXED_ROOT" in source


def test_collector_is_zero_execution_read_only():
    source = COLLECTOR.read_text(encoding="utf-8")
    forbidden = [
        "Start-Process",
        "diskpart.exe",
        "codex.exe",
        "app-server",
        "windowsSandbox/setupStart",
        "thread/start",
        "turn/start",
        "subprocess",
    ]
    for token in forbidden:
        assert token not in source
    assert "Remove-Item" not in source
    assert "Move-Item" not in source
    assert "Rename-Item" not in source


def test_collector_preserves_firewalls():
    source = COLLECTOR.read_text(encoding="utf-8")
    assert "A2_REPORT_TURN_FIREWALL_VIOLATION" in source
    assert "A2_REPORT_ATTEMPT_FIREWALL_VIOLATION" in source
    assert "A2_EVIDENCE_TURN_FIREWALL_VIOLATION" in source
    assert "A2_EVIDENCE_ATTEMPT_FIREWALL_VIOLATION" in source
    assert "turn_start_request_sent = $false" in source
    assert "scientific_attempt_consumed = $false" in source
    assert "evidence_return_only = $true" in source


def test_collector_returns_setup_and_downstream_gate_state():
    source = COLLECTOR.read_text(encoding="utf-8")
    for field in [
        "windows_sandbox_readiness_before",
        "windows_sandbox_setup_requested",
        "windows_sandbox_setup_started",
        "windows_sandbox_setup_completed",
        "windows_sandbox_setup_success",
        "windows_sandbox_setup_mode",
        "windows_sandbox_setup_error_code",
        "windows_sandbox_setup_error_redacted",
        "windows_sandbox_setup_error_sha256",
        "windows_sandbox_readiness_after",
        "driver_exception",
        "app_server_exit_code",
        "configured_mcp_count",
        "installed_app_count",
        "auth_ready",
        "profile_present",
        "profile_allowed",
        "active_permission_profile",
        "instruction_sources",
    ]:
        assert field in source


def test_spec_requires_read_only_evidence_return():
    normalized = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "ZERO-SCIENCE / READ-ONLY-EVIDENCE-RETURN" in normalized
    assert "No raw App Server stderr is returned." in normalized
    assert "A PASS authorizes exactly one local evidence-return execution." in normalized
