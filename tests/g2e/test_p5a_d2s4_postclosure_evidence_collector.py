from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "g2e" / "p5a_d2s4_collect_postclosure_evidence.ps1"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S4_POSTCLOSURE_TERMINAL_FAILURE_DECOMPOSITION.md"


def test_collector_is_read_only_existing_evidence_only():
    source = SCRIPT.read_text(encoding="utf-8")
    forbidden = [
        "Start-Process",
        "app-server",
        "thread/start",
        "turn/start",
        "Mount-DiskImage",
        "Dismount-DiskImage",
        "diskpart",
        "Invoke-WebRequest",
        "Remove-Item -LiteralPath $ScienceRoot",
    ]
    for token in forbidden:
        assert token not in source

    assert 'collection_mode = "READ_ONLY_EXISTING_EVIDENCE"' in source
    assert "codex_started = $false" in source
    assert "rpc_sent = $false" in source
    assert "vhdx_mounted = $false" in source
    assert "scientific_attempt_retried = $false" in source


def test_collector_binds_exact_d2s4_science001_hashes():
    source = SCRIPT.read_text(encoding="utf-8")
    for token in [
        "E98EE53C550E13DD42715C63CA6CBF887AA69396F50C90ABC6637A54A3DC9536",
        "6E1EF9D48BF640A8A285370549771F76048E0280EAF121450F3FA6679C069F5D",
        "BF0E848C1EBA9E8C0BF8A74DA5FCF96DBE29898EC26D1EF91D21ACA13A7BE01",
        "P5A-D2S4-SCIENCE-001",
    ]:
        assert token in source


def test_collector_requires_protocol_marker_and_verification_and_tracks_optional_stderr():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "P5A_D2S4_SCIENTIFIC_RUNNER_EVIDENCE.json" in source
    assert "P5A_D2S4_TURN_START_SENT.marker" in source
    assert "P5A_D2S4_SCIENTIFIC_VERIFICATION.json" in source
    assert "protocol_file" in source
    assert "stderr_hash_file" in source
    assert "REFERENCED_PROTOCOL_EVIDENCE_MISSING" in source
    assert "$StderrHashExists" in source
    assert 'exists = $false' in source
    assert 'RPC_CLIENT_MATERIALIZES_STDERR_HASH_FILE_ONLY_AFTER_FIRST_STDERR_RECORD' in source
    assert "Assert-UnderRoot" in source


def test_collector_preserves_science001_and_uses_separate_bundle():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "P5A-D2S4-POSTCLOSURE-BUNDLE" in source
    assert "POSTCLOSURE_BUNDLE_ROOT_ALREADY_EXISTS" in source
    assert "POSTCLOSURE_BUNDLE_ZIP_ALREADY_EXISTS" in source
    assert "Copy-Item" in source
    assert "Compress-Archive -Path" in source


def test_decomposition_spec_forbids_retry_and_execution():
    normalized = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "POST-CLOSURE / EVIDENCE-ONLY / NO SCIENTIFIC RETRY" in normalized
    assert "MUST NOT:" in normalized
    assert "send any RPC" in normalized
    assert "authorize a replacement D2-S4 attempt" in normalized
    assert "terminal turn with status `failed`" in normalized


def test_verification_hash_mismatch_is_preserved_not_silently_accepted_or_dropped():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "VERIFICATION_HASH_DRIFT" not in source
    assert "$ActualVerificationSha256 = Get-Sha256 $Verification" in source
    assert "$VerificationHashMatch = ($ActualVerificationSha256 -eq $ExpectedVerificationSha256)" in source
    assert "verification_identity = [ordered]@{" in source
    assert 'finding = if ($VerificationHashMatch) { $null } else { "VERIFICATION_HASH_MISMATCH_PRESERVED" }' in source
    assert "expected_sha256" in source
    assert "actual_sha256" in source
    assert "hash_match" in source
    assert 'P5A_D2S4_SCIENTIFIC_VERIFICATION.json' in source


def test_primary_frozen_sources_still_fail_closed_on_hash_drift():
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'throw "TOP_REPORT_HASH_DRIFT"' in source
    assert 'throw "RUNNER_EVIDENCE_HASH_DRIFT"' in source
