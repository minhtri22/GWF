from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_d2s3_platform_no_turn_oneclick.ps1"
PREFLIGHT = ROOT / "scripts" / "g2e" / "p5a_d2s3_platform_no_turn_preflight.py"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S3_PLATFORM_NO_TURN_PREFLIGHT_SPEC.md"


def test_exact_d2s3_identities_and_hashes_bound():
    ps = ONECLICK.read_text(encoding="utf-8")
    py = PREFLIGHT.read_text(encoding="utf-8")
    for token in [
        "p5a-d2s3-release-coherent-instrument-successor",
        "p5a-d2s3-p5-fx-001-attempt-001",
        "g2e_p5a_d2s3",
        "444A3F0008050605CAE73CD9B7A2DCAC61294062DFAAB56DD20430FD6498518B",
        "0C3EEB7CEE8D2BC4C8644DEF3C818E8B06760979572DCEDC919C38D0F38F64C4",
        "21DEDDE191D144AD561AF7E78903FCE73990D8FFBB6D8BB701A34EB95E336C76",
    ]:
        assert token in ps
    assert "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b" in py
    assert "p5a-d2s3-release-coherent-instrument-successor" in py
    assert "p5a-d2s3-p5-fx-001-attempt-001" in py
    assert "g2e_p5a_d2s3" in py


def test_exact_staged_instrument_layout_no_global_fallback():
    ps = ONECLICK.read_text(encoding="utf-8")
    assert 'g2e\\.local\\P5A-D2S3-INSTRUMENT' in ps
    assert 'package\\bin\\codex.exe' in ps
    assert 'package\\codex-resources\\codex-windows-sandbox-setup.exe' in ps
    assert "Programs\\OpenAI\\Codex" not in ps
    assert "STAGED_CODEX_HASH_DRIFT" in ps
    assert "STAGED_HELPER_HASH_DRIFT" in ps


def test_preflight_rpc_surface_is_exact_no_turn():
    source = PREFLIGHT.read_text(encoding="utf-8")
    methods = re.findall(r'"method"\s*:\s*"([^"]+)"', source)
    allowed = {
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
    assert set(methods) == allowed
    assert "turn/start" not in source


def test_preflight_preserves_scientific_firewalls():
    source = PREFLIGHT.read_text(encoding="utf-8")
    assert '"turn_start_request_sent": False' in source
    assert '"scientific_attempt_consumed": False' in source
    assert '"result_exists": False' in source
    assert "mcp_servers={}" in source
    assert "features.apps=false" in source
    assert "features.plugins=false" in source
    assert "features.remote_plugin=false" in source
    assert "features.workspace_dependencies=false" in source


def test_oneclick_has_no_turn_start_and_no_model_dispatch():
    source = ONECLICK.read_text(encoding="utf-8")
    assert "turn/start" not in source
    assert "model=" not in source
    assert "prompt" not in source.lower()
    assert "turn_start_request_sent = $false" in source
    assert "scientific_attempt_consumed = $false" in source


def test_protected_vhdx_body_has_finally_cleanup_before_exit():
    source = ONECLICK.read_text(encoding="utf-8")
    start = source.index("# PROTECTED_VHDX_BODY_START")
    end = source.index("# PROTECTED_VHDX_BODY_END")
    protected = source[start:end]
    assert "finally {" in protected
    assert "Get-DiskImage -ImagePath $VhdxPath" in protected
    assert "Dismount-DiskImage -ImagePath $VhdxPath" in protected
    assert "attached_after_cleanup" in protected
    assert re.search(r"\bexit\b", protected) is None
    after = source[end:]
    assert "exit $FinalExitCode" in after


def test_vhdx_is_preserved_not_deleted():
    source = ONECLICK.read_text(encoding="utf-8")
    assert "Remove-Item -LiteralPath $VhdxPath" not in source
    assert "DeleteVhd" not in source
    assert "Dismount-DiskImage" in source


def test_preflight_output_and_pass_contract():
    ps = ONECLICK.read_text(encoding="utf-8")
    py = PREFLIGHT.read_text(encoding="utf-8")
    assert "P5A_D2S3_PLATFORM_NO_TURN_PREFLIGHT.json" in ps
    assert "P5A_D2S3_PLATFORM_NO_TURN_PREFLIGHT.json" in py
    assert "PRETURN_PASS_SCIENTIFIC_AUTHORIZATION_REVIEW_REQUIRED" in ps
    assert "PRETURN_RESULT_FILE_VIOLATION" in ps


def test_spec_keeps_science_closed_and_cleanup_mandatory():
    normalized = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "SPEC-LOCKED / PRETURN-ONLY / ZERO-SCIENCE" in normalized
    assert "The implementation MUST NOT send:" in normalized
    assert "turn/start" in normalized
    assert "dismount it if attached" in normalized
    assert "No `exit` is allowed inside the protected work body before cleanup." in normalized
    assert "A PASS does not itself authorize scientific execution." in normalized
