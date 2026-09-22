from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_d2s3_platform_no_turn_oneclick.ps1"
PREFLIGHT = ROOT / "scripts" / "g2e" / "p5a_d2s3_platform_no_turn_preflight.py"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S3_PRETURN_NTFS_ROOT_CLOSURE_REPAIR_002_SPEC.md"


def test_r2_uses_fresh_support_root_and_lock():
    source = ONECLICK.read_text(encoding="utf-8")
    assert 'P5A_D2S3_PRETURN_NTFS_ROOT_CLOSURE_REPAIR_002_LOCK.json' in source
    assert 'g2e\\.local\\P5A-D2S3-PREFLIGHT-R2' in source
    assert 'P5A-D2S3-PREFLIGHT-R2-TASK.vhdx' in source
    assert 'label=G2ED2S3R2' in source
    assert 'P5A_D2S3_PLATFORM_NO_TURN_R2_REPORT.json' in source
    assert 'G2E-P5A-D2S3-PLATFORM-NO-TURN-R2-REPORT-v1' in source


def test_root_classifier_allows_only_payload_plus_optional_svi_directory():
    source = ONECLICK.read_text(encoding="utf-8")
    assert 'function Get-WorkspaceRootClassification([string]$Root)' in source
    assert '$item.Name -eq "input.json" -or $item.Name -eq "TASK.md"' in source
    assert '$item.Name -eq "System Volume Information"' in source
    assert '$item.PSIsContainer' in source
    assert '$isReparse' in source
    assert 'workspace_payload_names = @()' in source
    assert 'workspace_metadata_names = @()' in source
    assert 'workspace_unexpected_names = @()' in source
    assert 'ISOLATED_VOLUME_PRESTATE_DRIFT:' in source
    assert '($RootNames -join "|") -ne "input.json|TASK.md"' not in source


def test_root_classifier_exposes_real_runtime_selftest():
    source = ONECLICK.read_text(encoding="utf-8")
    assert '[switch]$RootClassificationSelfTest' in source
    assert 'Invoke-RootClassificationSelfTest' in source
    assert 'ROOT_CLASSIFICATION_SELFTEST_PASS' in source
    assert 'ROOT_CLASSIFICATION_SELFTEST_PAYLOAD_ONLY_FAILED' in source
    assert 'ROOT_CLASSIFICATION_SELFTEST_SVI_DIR_FAILED' in source
    assert 'ROOT_CLASSIFICATION_SELFTEST_UNEXPECTED_FILE_FAILED' in source
    assert 'ROOT_CLASSIFICATION_SELFTEST_UNEXPECTED_DIR_FAILED' in source
    assert 'ROOT_CLASSIFICATION_SELFTEST_SVI_FILE_FAILED' in source


def test_config_serialization_repair_is_preserved():
    source = ONECLICK.read_text(encoding="utf-8")
    assert 'function Convert-ToLfText([string]$Text)' in source
    assert '$Text.Replace("`r`n", "`n").Replace("`r", "`n")' in source
    assert '(Convert-ToLfText $config) + "`n"' in source
    assert '$config.Replace([Environment]::NewLine, [char]10)' not in source
    assert '[switch]$ConfigSerializationSelfTest' in source


def test_scientific_identity_and_instrument_remain_frozen():
    source = ONECLICK.read_text(encoding="utf-8")
    for token in [
        'p5a-d2s3-release-coherent-instrument-successor',
        'p5a-d2s3-p5-fx-001-attempt-001',
        'g2e_p5a_d2s3',
        '444A3F0008050605CAE73CD9B7A2DCAC61294062DFAAB56DD20430FD6498518B',
        '0C3EEB7CEE8D2BC4C8644DEF3C818E8B06760979572DCEDC919C38D0F38F64C4',
        '21DEDDE191D144AD561AF7E78903FCE73990D8FFBB6D8BB701A34EB95E336C76',
    ]:
        assert token in source


def test_driver_remains_exact_no_turn_control_plane():
    source = PREFLIGHT.read_text(encoding="utf-8")
    assert 'turn/start' not in source
    methods = set(re.findall(r'"method"\s*:\s*"([^"]+)"', source))
    assert methods == {
        'initialize',
        'initialized',
        'windowsSandbox/readiness',
        'windowsSandbox/setupStart',
        'mcpServerStatus/list',
        'app/installed',
        'account/read',
        'permissionProfile/list',
        'thread/start',
    }


def test_cleanup_contract_is_still_non_bypassable():
    source = ONECLICK.read_text(encoding="utf-8")
    start = source.index('# PROTECTED_VHDX_BODY_START')
    end = source.index('# PROTECTED_VHDX_BODY_END')
    protected = source[start:end]
    assert 'finally {' in protected
    assert 'Dismount-DiskImage -ImagePath $VhdxPath' in protected
    assert 'attached_after_cleanup' in protected
    assert re.search(r'\bexit\b', protected) is None


def test_r2_preserves_r1_evidence():
    source = ONECLICK.read_text(encoding="utf-8")
    assert 'Remove-Item -LiteralPath $LocalRoot' not in source
    assert 'P5A-D2S3-PREFLIGHT-R1-TASK.vhdx' not in source


def test_spec_is_bounded_zero_science_macro_gate():
    normalized = ' '.join(SPEC.read_text(encoding='utf-8').split())
    assert 'SPEC-LOCKED / ZERO-SCIENCE / IMPLEMENTATION-REPAIR-ONLY' in normalized
    assert 'Python preflight driver blob:' in normalized
    assert 'P1/P1.4/P1.5/P2/P3/P4 regressions PASS' in normalized
    assert 'does not authorize scientific execution' in normalized
