from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_d2s3_platform_no_turn_oneclick.ps1"
PREFLIGHT = ROOT / "scripts" / "g2e" / "p5a_d2s3_platform_no_turn_preflight.py"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S3_PRETURN_CONFIG_SERIALIZATION_REPAIR_001_SPEC.md"


def test_repair_uses_string_string_lf_normalization():
    source = ONECLICK.read_text(encoding="utf-8")
    assert 'function Convert-ToLfText([string]$Text)' in source
    assert '$Text.Replace("`r`n", "`n").Replace("`r", "`n")' in source
    assert '(Convert-ToLfText $config) + "`n"' in source
    assert '$config.Replace([Environment]::NewLine, [char]10)' not in source


def test_real_serialization_selftest_is_exposed():
    source = ONECLICK.read_text(encoding="utf-8")
    assert "[switch]$ConfigSerializationSelfTest" in source
    assert "Invoke-ConfigSerializationSelfTest" in source
    assert "CONFIG_SERIALIZATION_SELFTEST_PASS" in source
    assert "CONFIG_SERIALIZATION_SELFTEST_CR_PRESENT" in source
    assert "CONFIG_SERIALIZATION_SELFTEST_DOUBLE_TRAILING_LF" in source
    assert '[Text.UTF8Encoding]::new($false)' in source


def test_repair_preserves_invalid_root_and_uses_fresh_r1_root():
    source = ONECLICK.read_text(encoding="utf-8")
    assert 'g2e\\.local\\P5A-D2S3-PREFLIGHT-R1' in source
    assert 'P5A-D2S3-PREFLIGHT-R1-TASK.vhdx' in source
    assert 'label=G2ED2S3R1' in source
    assert 'P5A_D2S3_PLATFORM_NO_TURN_R1_REPORT.json' in source
    assert 'Remove-Item -LiteralPath $LocalRoot' not in source


def test_repair_binds_new_lock_and_same_scientific_identity():
    source = ONECLICK.read_text(encoding="utf-8")
    assert 'P5A_D2S3_PRETURN_CONFIG_SERIALIZATION_REPAIR_001_LOCK.json' in source
    assert 'p5a-d2s3-release-coherent-instrument-successor' in source
    assert 'p5a-d2s3-p5-fx-001-attempt-001' in source
    assert 'g2e_p5a_d2s3' in source


def test_preflight_driver_stays_no_turn_and_same_rpc_contract():
    source = PREFLIGHT.read_text(encoding="utf-8")
    assert "turn/start" not in source
    methods = set(re.findall(r'"method"\s*:\s*"([^"]+)"', source))
    assert methods == {
        "initialize",
        "initialized",
        "windowsSandbox/readiness",
        "windowsSandbox/setupStart",
        "mcpServerStatus/list",
        "app/installed",
        "account/read",
        "permissionProfile/list",
        "thread/start",
    }


def test_cleanup_contract_still_protects_all_exit_paths():
    source = ONECLICK.read_text(encoding="utf-8")
    start = source.index("# PROTECTED_VHDX_BODY_START")
    end = source.index("# PROTECTED_VHDX_BODY_END")
    protected = source[start:end]
    assert "finally {" in protected
    assert "Dismount-DiskImage -ImagePath $VhdxPath" in protected
    assert "attached_after_cleanup" in protected
    assert re.search(r"\bexit\b", protected) is None


def test_repair_spec_is_zero_science_and_preflight_blob_frozen():
    normalized = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "SPEC-LOCKED / ZERO-SCIENCE / IMPLEMENTATION-REPAIR-ONLY" in normalized
    assert "Python preflight driver blob MUST remain unchanged" in normalized
    assert "does not authorize scientific execution" in normalized
