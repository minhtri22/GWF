from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COLLECTOR = ROOT / "scripts" / "g2e" / "p5a_d2s2_a2_binary_component_lineage.ps1"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S2_A2_BINARY_COMPONENT_LINEAGE_SPEC.md"


def test_collector_binds_exact_codex_identity():
    source = COLLECTOR.read_text(encoding="utf-8")
    assert "A337B7433EBB351C0165DD074CF2500A20FCA9CEAB3680A71DF593653BF70DC8" in source
    assert "3d2ee51ca2d5db578f328aa75e20aa22c0197c9a" in source
    assert "Programs\\OpenAI\\Codex\\bin\\codex.exe" in source
    assert "CODEX_EXE_HASH_MISMATCH" in source


def test_collector_reproduces_frozen_helper_priority():
    source = COLLECTOR.read_text(encoding="utf-8")
    assert '$HelperName = "codex-windows-sandbox-setup.exe"' in source
    assert '"$SourceKind-direct-sibling"' in source
    assert '"$SourceKind-package-resources"' in source
    assert '"$SourceKind-exe-dir-resources"' in source
    assert '[G2EFinalPath]::Resolve($ExePath)' in source
    assert "lexical-direct-sibling" in source
    assert "lexical-package-resources" in source


def test_collector_has_windows_resolver_selftest():
    source = COLLECTOR.read_text(encoding="utf-8")
    assert "[switch]$ResolverSelfTest" in source
    assert "RESOLVER_SELFTEST_PACKAGE_PRIORITY_FAILED" in source
    assert "RESOLVER_SELFTEST_DIRECT_PRIORITY_FAILED" in source
    assert "RESOLVER_SELFTEST_PASS" in source


def test_collector_reports_hash_version_and_mode_markers_only():
    source = COLLECTOR.read_text(encoding="utf-8")
    assert '$Markers = @("interactive-provision", "full", "provision-only", "read-acls-only")' in source
    for field in [
        "size_bytes",
        "sha256",
        "file_version",
        "product_version",
        "markers",
        "helper_candidates",
        "selected_helper",
        "existing_helper_candidate_count",
        "multiple_existing_helper_candidates",
    ]:
        assert field in source


def test_production_path_does_not_execute_or_replace_binaries():
    source = COLLECTOR.read_text(encoding="utf-8")
    forbidden = [
        "Start-Process",
        "Invoke-Expression",
        "Copy-Item",
        "Move-Item",
        "Rename-Item",
        "Set-Content",
        "diskpart",
        "windowsSandbox/",
        "thread/start",
        "turn/start",
    ]
    for token in forbidden:
        assert token not in source

    assert "& $CodexExe" not in source
    assert "& $HelperName" not in source
    assert "ProcessStartInfo" not in source


def test_collector_preserves_scientific_firewalls():
    source = COLLECTOR.read_text(encoding="utf-8")
    assert "evidence_return_only = $true" in source
    assert "turn_start_request_sent = $false" in source
    assert "scientific_attempt_consumed = $false" in source


def test_spec_is_component_lineage_only():
    normalized = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "SPEC-LOCKED / ZERO-SCIENCE / READ-ONLY-BINARY-LINEAGE" in normalized
    assert "The collector MUST NOT:" in normalized
    assert "execute `codex.exe`" in normalized
    assert "A PASS authorizes exactly one local read-only binary lineage diagnostic." in normalized
