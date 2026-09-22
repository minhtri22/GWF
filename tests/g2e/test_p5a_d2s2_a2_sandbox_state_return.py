from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COLLECTOR = ROOT / "scripts" / "g2e" / "p5a_d2s2_a2_sandbox_state_return.ps1"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S2_A2_SANDBOX_STATE_RETURN_SPEC.md"


def test_collector_binds_setup_evidence_return():
    source = COLLECTOR.read_text(encoding="utf-8")
    assert "6F1F178AAC74037ED8AB1661B5B98BEEF5871F0CDE0456237A52AFD84FB23CEB" in source
    assert 'g2e\\.local\\P5A-D2S2-A2' in source
    assert 'codex-home\\preturn-a2\\.sandbox' in source
    assert "P5A_D2S2_A2_SANDBOX_STATE_RETURN_" in source


def test_collector_reads_only_sandbox_support_state_and_return_dir():
    source = COLLECTOR.read_text(encoding="utf-8")
    assert "setup_error.json" in source
    assert "setup_marker.json" in source
    assert 'Filter "sandbox.*.log"' in source
    assert "Get-ChildItem -LiteralPath $SandboxDir -Force" in source
    assert "Get-Content -LiteralPath $SetupErrorPath -Raw" in source
    assert "Get-Content -LiteralPath $SetupMarkerPath -Raw" in source


def test_collector_has_no_execution_or_mutation_surface():
    source = COLLECTOR.read_text(encoding="utf-8")
    forbidden = [
        "Start-Process",
        "diskpart.exe",
        "codex.exe",
        "app-server",
        "windowsSandbox/",
        "thread/start",
        "turn/start",
        "Remove-Item",
        "Move-Item",
        "Rename-Item",
        "Set-Acl",
        "New-LocalUser",
        "net.exe",
        "netsh.exe",
    ]
    for token in forbidden:
        assert token not in source


def test_collector_limits_and_sanitizes_log_return():
    source = COLLECTOR.read_text(encoding="utf-8")
    assert "Sanitize-Text" in source
    assert "<PROJECT_ROOT>" in source
    assert "<USERPROFILE>" in source
    assert "<USER>" in source
    assert '$tokens = @("setup","helper","sandbox","firewall","acl","user","error","fail")' in source
    assert "$relevant.Count -gt 80" in source
    assert "[switch]$SanitizationSelfTest" in source
    assert "SANITIZATION_SELFTEST_PASS" in source


def test_collector_returns_structured_setup_artifacts_only():
    source = COLLECTOR.read_text(encoding="utf-8")
    for field in [
        "sandbox_entries",
        "setup_error",
        "setup_marker",
        "sandbox_logs",
        "setup_relevant_log_tail_sanitized",
        "message_sha256",
        "message_sanitized",
        "reparse_point",
    ]:
        assert field in source


def test_collector_preserves_firewalls():
    source = COLLECTOR.read_text(encoding="utf-8")
    assert "evidence_return_only = $true" in source
    assert "turn_start_request_sent = $false" in source
    assert "scientific_attempt_consumed = $false" in source


def test_spec_requires_readonly_sandbox_state_collection():
    normalized = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "SPEC-LOCKED / ZERO-SCIENCE / READ-ONLY-LOCAL-EVIDENCE" in normalized
    assert "This is not a rerun." in normalized
    assert "No raw unfiltered log is returned." in normalized
    assert "A PASS authorizes exactly one local read-only sandbox-state collection." in normalized
