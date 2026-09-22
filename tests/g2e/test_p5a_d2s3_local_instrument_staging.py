from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "g2e" / "p5a_d2s3_stage_release_coherent_instrument.ps1"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S3_LOCAL_INSTRUMENT_STAGING_SPEC.md"


def test_staging_freezes_exact_release_assets():
    source = SCRIPT.read_text(encoding="utf-8")
    for token in [
        "rust-v0.153.4",
        "3d2ee51ca2d5db578f328aa75e20aa22c0197c9a",
        "C016B0E6968B78586919C720D2685A03712F6D5F11BCD9D6F92C91EB8C41BA16",
        "444A3F0008050605CAE73CD9B7A2DCAC61294062DFAAB56DD20430FD6498518B",
        "256C4DEB16946A01A52156E8FD619BAEC38743FF482741767AB5FDB4079E97CB",
        "0C3EEB7CEE8D2BC4C8644DEF3C818E8B06760979572DCEDC919C38D0F38F64C4",
    ]:
        assert token in source


def test_staging_uses_isolated_package_layout():
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'g2e\\.local\\P5A-D2S3-INSTRUMENT' in source
    assert '$BinDir = Join-Path $PackageRoot "bin"' in source
    assert '$ResourcesDir = Join-Path $PackageRoot "codex-resources"' in source
    assert '$FinalCodex = Join-Path $BinDir "codex.exe"' in source
    assert '$FinalHelper = Join-Path $ResourcesDir "codex-windows-sandbox-setup.exe"' in source


def test_staging_never_executes_instrument():
    source = SCRIPT.read_text(encoding="utf-8")
    forbidden = [
        "Start-Process",
        "ProcessStartInfo",
        "app-server",
        "windowsSandbox/",
        "thread/start",
        "turn/start",
        "diskpart",
        "Mount-DiskImage",
        "Dismount-DiskImage",
    ]
    for token in forbidden:
        assert token not in source
    assert "& $FinalCodex" not in source
    assert "& $FinalHelper" not in source
    assert "executables_invoked = $false" in source


def test_staging_fails_closed_on_existing_root_and_marker_drift():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "D2S3_INSTRUMENT_ROOT_ALREADY_EXISTS" in source
    assert "CODEX_INTERACTIVE_PROVISION_MARKER_PRESENT" in source
    assert "HELPER_INTERACTIVE_PROVISION_MARKER_PRESENT" in source
    assert "CODEX_REQUIRED_MODE_MARKER_MISSING" in source
    assert "HELPER_REQUIRED_MODE_MARKER_MISSING" in source


def test_staging_cleans_only_own_temp_root_in_finally():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "finally {" in source
    assert "Remove-Item -LiteralPath $TempRoot -Recurse -Force" in source
    assert source.count("Remove-Item") == 1
    assert "temp_cleanup" in source


def test_staging_report_preserves_firewalls():
    source = SCRIPT.read_text(encoding="utf-8")
    for token in [
        "global_install_modified = $false",
        "executables_invoked = $false",
        "turn_start_request_sent = $false",
        "scientific_attempt_consumed = $false",
        "STAGING_PASS_PLATFORM_PREFLIGHT_GATE_REQUIRED",
    ]:
        assert token in source


def test_spec_forbids_global_install_mutation_and_science():
    normalized = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "modify `%LOCALAPPDATA%\\Programs\\OpenAI\\Codex`" in normalized
    assert "execute `codex.exe`" in normalized
    assert "authorize or consume a scientific attempt" in normalized
    assert "actual end-to-end staging succeeds on a Windows GitHub runner" in normalized
