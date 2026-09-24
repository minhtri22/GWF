from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ONECLICK = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_tc3_oneclick.ps1"
PLAN = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC3_RUNTIME_READINESS_REPAIR_PLAN.md"


def test_tc3_uses_fresh_root_and_lock():
    s = ONECLICK.read_text(encoding="utf-8")
    assert "P5A-CGW-FX001-TC-003" in s
    assert "P5A-CGW-FX001-TC-002" not in s
    assert "P5A_CGW_FX001_TC3_EXECUTION_LOCK.json" in s
    assert "DISPATCH_AUTHORIZED_EXECUTION_LOCK_TC3" in s


def test_runtime_health_gate_precedes_uac_and_root_creation():
    s = ONECLICK.read_text(encoding="utf-8")
    health = s.index('Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:17841/healthz"')
    uac = s.index("if (-not (Test-IsAdministrator))")
    create_root = s.index("New-Item -ItemType Directory -Path $VolumeDir,$CodexHome,$ReportDir,$VerificationDir")
    assert 0 <= health < uac < create_root


def test_runtime_health_gate_is_strict():
    s = ONECLICK.read_text(encoding="utf-8")
    for token in (
        "CGW_RUNTIME_READINESS_UNAVAILABLE",
        "CGW_RUNTIME_READINESS_STATUS",
        "CGW_RUNTIME_READINESS_SERVICE",
        "CGW_RUNTIME_READINESS_VERSION",
        "CGW_RUNTIME_READINESS_MODE",
        "CGW_RUNTIME_READINESS_PORT",
        "CGW_RUNTIME_READINESS_NOT_ACCEPTING",
        "CGW_RUNTIME_READINESS_HTTP_BUSY",
        "CGW_RUNTIME_READINESS_BROWSER_BUSY",
    ):
        assert token in s
    assert '[string]$RuntimeHealth.version -ne "4.0.7"' in s
    assert '[string]$RuntimeHealth.mode -ne "full"' in s
    assert '[int]$RuntimeHealth.port -ne 17841' in s


def test_tc3_reuses_qualified_semantic_admission():
    s = ONECLICK.read_text(encoding="utf-8")
    assert "scripts\\g2e\\p5a_cgw_fx001_tc2_admission.py" in s
    assert "scripts/g2e/p5a_cgw_fx001_tc2_admission.py" in s


def test_plan_forbids_live_activation():
    s = PLAN.read_text(encoding="utf-8")
    assert "RESERVED_UNCONSUMED" in s
    assert "No live dispatch is authorized by this plan." in s
    assert "retry budget=0" in s
