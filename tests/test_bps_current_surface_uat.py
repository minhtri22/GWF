from __future__ import annotations

import importlib.util
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from gwr.auth import HumanAuthService

ROOT = Path(__file__).parents[1]
PS1 = ROOT / "scripts" / "uiux" / "bps_current_surface_uat.ps1"
SEED = ROOT / "scripts" / "uiux" / "bps_current_surface_uat_seed.py"
QUALIFIED_HEAD = "4e95d406e346eba42567835b5a1bd44366618baf"


def _load_seed_module():
    spec = importlib.util.spec_from_file_location(
        "bps_current_surface_uat_seed", SEED
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_surface_uat_script_contract_is_current_and_bounded():
    text = PS1.read_text(encoding="utf-8")
    assert 'Set-StrictMode -Version Latest' in text
    assert '$ErrorActionPreference = "Stop"' in text
    assert QUALIFIED_HEAD in text
    assert 'feature/bps-i00-product-shell' in text
    assert 'no_product_drift_after_qualified_head' in text
    assert 'git diff --name-only $QualifiedImplementationHead HEAD -- src web install.ps1 scripts/gwf_server.ps1' in text

    for token in (
        'home=@("LIVE_MODULE","BPS-M01")',
        'projects=@("LIVE_MODULE","BPS-M02")',
        'access=@("LIVE_MODULE","BPS-M02")',
        'operations=@("LIVE_MODULE","BPS-M03")',
        'packages=@("LIVE_MODULE","BPS-M06")',
        'github=@("LIVE_MODULE","BPS-M07")',
        'diagnostics=@("LIVE_FOUNDATION","BPS-I00")',
        'settings_locked',
        'shared-library',
        'reference-acquisition',
        'agents',
    ):
        assert token in text
    assert "home_skeleton_locked" not in text
    assert "projects_skeleton_locked" not in text

    for path in (
        "/browser/home-summary",
        "/browser/projects-index",
        "/browser/projects/create-options",
        "/browser/access-summary",
        "/browser/operations/runs",
        "/browser/operations/approvals",
        "/browser/operations/audit",
        "/browser/operations/runtime",
        "/browser/packages",
        "/browser/github",
        "/browser/diagnostics",
        "/browser/projects/project_uat_execution/overview",
        "/browser/projects/project_uat_execution/execution",
        "/browser/projects/project_uat_recovery/execution",
    ):
        assert path in text

    assert "http://localhost:$Port/app/home" in text
    assert "CURRENT_SURFACE_UAT_REPORT.json" in text
    assert "session_survives_restart" in text
    assert "head_unchanged" in text
    assert "server_stopped" in text

    assert "UAT Created Project" in text
    assert "Lifecycle Project Renamed" in text
    assert "proposal_current_surface_uat" in text
    assert "phase_current_surface_recovery" in text
    for i in range(1, 20):
        assert f'"U{i:02d}"' in text

    assert "M07-B/M08/M09/M10 remain closed" in text
    assert "M07-B/M08/M09/M10 are not simulated" in text
    assert "FINAL_LOCAL_VERDICT=$Verdict" in text


def test_current_surface_uat_scripts_are_windows_powershell_51_text_safe():
    text = PS1.read_text(encoding="utf-8")
    assert sorted({ch for ch in text if ord(ch) > 127}) == []


@pytest.mark.skipif(sys.platform != "win32", reason="PowerShell parser check is Windows-only")
def test_current_surface_uat_script_parses_on_windows():
    shell = shutil.which("pwsh") or shutil.which("powershell")
    assert shell
    parser = (
        "$tokens=$null; $errors=$null; "
        "$path=$env:BPS_CURRENT_SURFACE_UAT_SCRIPT; "
        "[System.Management.Automation.Language.Parser]::ParseFile("
        "$path,[ref]$tokens,[ref]$errors) | Out-Null; "
        "if($errors.Count -gt 0){"
        "$errors | ForEach-Object { Write-Error $_.Message }; exit 1}; exit 0"
    )
    env = os.environ.copy()
    env["BPS_CURRENT_SURFACE_UAT_SCRIPT"] = str(PS1)
    subprocess.run(
        [shell, "-NoProfile", "-Command", parser],
        cwd=ROOT,
        env=env,
        check=True,
    )


def test_current_surface_seed_materializes_authoritative_states(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    db_path = tmp_path / "uat.db"
    monkeypatch.setenv("GWR_UAT_USERNAME", "seed-test-user")
    monkeypatch.setenv("GWR_UAT_PASSWORD", "seed-test-password-long")
    monkeypatch.setenv("GWR_AUTH_SECRET", "s" * 64)
    monkeypatch.setenv("GWR_DATABASE_URL", str(db_path))
    monkeypatch.setenv("GWR_OBJECT_STORE_ROOT", str(tmp_path / "objects"))
    monkeypatch.setenv(
        "GWR_OBSERVABILITY_PATH", str(tmp_path / "observability.jsonl")
    )

    seed_module = _load_seed_module()
    result = seed_module.seed()

    assert result["execution_project_id"] == "project_uat_execution"
    assert result["lifecycle_project_id"] == "project_uat_lifecycle"
    assert result["recovery_project_id"] == "project_uat_recovery"
    assert result["archived_project_id"] == "project_uat_archived"
    assert result["approval_id"] == "proposal_current_surface_uat"
    assert result["recovery_phase_id"] == "phase_current_surface_recovery"
    assert result["github_binding_id"]
    assert result["github_change_set_id"]

    conn = sqlite3.connect(db_path)
    try:
        lifecycle = dict(
            conn.execute(
                "SELECT project_id,status FROM project_lifecycle "
                "WHERE project_id IN ('project_uat_execution','project_uat_lifecycle',"
                "'project_uat_recovery','project_uat_archived')"
            ).fetchall()
        )
        assert lifecycle == {
            "project_uat_execution": "ACTIVE",
            "project_uat_lifecycle": "ACTIVE",
            "project_uat_recovery": "ACTIVE",
            "project_uat_archived": "ARCHIVED",
        }
        assert conn.execute(
            "SELECT status FROM proposals WHERE proposal_id=?",
            ("proposal_current_surface_uat",),
        ).fetchone()[0] == "PENDING_APPROVAL"
        assert conn.execute(
            "SELECT status FROM phase_recovery_proposals WHERE proposal_id=?",
            (result["recovery_proposal_id"],),
        ).fetchone()[0] == "WAITING_HUMAN"
        assert conn.execute(
            "SELECT COUNT(*) FROM github_repository_bindings WHERE binding_id=?",
            (result["github_binding_id"],),
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM distributed_jobs"
        ).fetchone()[0] >= 1
    finally:
        conn.close()
