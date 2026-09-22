from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "g2e" / "p5a_d2s3_collect_postclosure_evidence.ps1"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S3_POSTCLOSURE_PROTOCOL_FAILURE_DECOMPOSITION.md"


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


def test_collector_binds_exact_science002_evidence_hashes():
    source = SCRIPT.read_text(encoding="utf-8")
    for token in [
        "09E71058BD9E9B4B4FD2E5C4F5F0C412C228932FA183D08DC7D6DF4D0FC5E712",
        "AE60858BFD53268FBB43FB5F1166AAA3ACD4FE322F23279B139412BB260B8017",
        "528B1FD3460C1EFDD180DFAB703DC264A5102D44FABF887411DC3F1BBC51C418",
        "P5A-D2S3-SCIENCE-002",
    ]:
        assert token in source


def test_collector_requires_protocol_stderr_marker_and_verification():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "P5A_D2S3_SCIENTIFIC_RUNNER_EVIDENCE.json" in source
    assert "P5A_D2S3_TURN_START_SENT.marker" in source
    assert "P5A_D2S3_SCIENTIFIC_VERIFICATION.json" in source
    assert "protocol_file" in source
    assert "stderr_hash_file" in source
    assert "Assert-UnderRoot" in source


def test_collector_preserves_science002_and_uses_separate_bundle():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "P5A-D2S3-POSTCLOSURE-BUNDLE" in source
    assert "POSTCLOSURE_BUNDLE_ROOT_ALREADY_EXISTS" in source
    assert "POSTCLOSURE_BUNDLE_ZIP_ALREADY_EXISTS" in source
    assert "Copy-Item" in source
    assert "Compress-Archive -Path" in source


def test_postclosure_spec_forbids_retry_and_execution():
    normalized = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "POST-CLOSURE / EVIDENCE-ONLY / NO SCIENTIFIC RETRY" in normalized
    assert "MUST NOT:" in normalized
    assert "send any RPC" in normalized
    assert "authorize a replacement D2-S3 attempt" in normalized
