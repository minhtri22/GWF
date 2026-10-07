from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "uiux" / "bps_i00_local_uat.ps1"


def test_bps_i00_local_uat_script_contract():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'Set-StrictMode -Version Latest' in text
    assert '$ErrorActionPreference = "Stop"' in text
    assert 'feature/bps-i00-product-shell' in text
    assert 'git_head_start' in text
    assert 'git_head_end' in text
    assert 'working_tree_clean_at_start' in text
    assert 'BPS-I00_LOCAL_UAT_REPORT.json' in text
    assert r'.local\BPS-I00\evidence' in text
    assert 'install.ps1' in text
    assert r'scripts\gwf_server.ps1' in text
    assert '/ready' in text
    assert '/browser/auth/login' in text
    assert '/browser/auth/me' in text
    assert '/app/home' in text
    assert '/app/projects' in text
    assert '/app/system/diagnostics' in text
    assert 'spa_history_router' in text
    assert '$routeChecks = [ordered]@{' in text
    assert '"home" = "/app/home"' in text
    assert '("route_http_" + $entry.Key)' in text
    assert 'HttpOnly' in text
    assert 'SameSite=Strict' in text
    assert 'Start-Process $AppUrl' in text
    assert 'System, Light and Dark' in text
    assert 'navigation collapses and expands' in text
    assert 'browser Back and Forward' in text
    assert 'route-specific Locked surface' in text
    assert 'same Projects locked route is restored' in text
    assert 'LIVE foundation' in text
    assert 'FINAL_LOCAL_VERDICT' in text
    assert 'session_survives_canonical_restart' in text
    assert 'canonical_server_stopped' in text
    assert 'tracked_worktree_clean_at_end' in text
    assert '[System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName' in text
    assert '-NoProfile -ExecutionPolicy Bypass -File $ScriptPath' in text
    report_start = text.index("function Write-Report {")
    report_end = text.index("\ntry {", report_start)
    report_section = text[report_start:report_end].lower()
    assert "gwr_bootstrap_password" not in report_section
    assert "gwr_auth_secret" not in report_section
    assert "uatpassword" not in report_section
    assert "uatsecret" not in report_section
    assert "access_token" not in report_section


def test_bps_i00_local_uat_server_launcher_runs_inline_not_child_process():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'function Invoke-LoggedServerLauncher {' in text
    assert '& $ServerLauncher -Action $Action -RepoRoot $RepoRoot -Port $Port *>&1' in text
    assert 'Invoke-LoggedServerLauncher -Action "start"' in text
    assert 'Invoke-LoggedServerLauncher -Action "restart"' in text
    assert 'Invoke-LoggedServerLauncher -Action "stop"' in text
    assert 'Invoke-LoggedPowerShell -ScriptPath $ServerLauncher' not in text


def test_bps_i00_local_uat_captures_launcher_host_information_stream():
    text = SCRIPT.read_text(encoding="utf-8")
    assert '$preStatus = & $ServerLauncher -Action status -RepoRoot $RepoRoot -Port $Port *>&1' in text
    assert '$statusOutput = & $ServerLauncher -Action status -RepoRoot $RepoRoot -Port $Port *>&1' in text
    assert '$stopped = & $ServerLauncher -Action status -RepoRoot $RepoRoot -Port $Port *>&1' in text
    assert '-Action status -RepoRoot $RepoRoot -Port $Port 2>&1' not in text


def test_bps_i00_local_uat_does_not_trust_leaked_nested_last_exit_code():
    text = SCRIPT.read_text(encoding="utf-8")
    fn_start = text.index("function Invoke-LoggedPowerShell {")
    fn_end = text.index("\nfunction Wait-Ready {", fn_start)
    fn = text[fn_start:fn_end]
    assert "& $ScriptPath @Arguments" not in fn
    assert "& $PowerShellExe -NoProfile -ExecutionPolicy Bypass -File $ScriptPath @Arguments" in fn
    assert "$global:LASTEXITCODE = 0" not in fn


def test_bps_i00_local_uat_script_is_windows_powershell_51_encoding_safe():
    text = SCRIPT.read_text(encoding="utf-8")
    non_ascii = sorted({ch for ch in text if ord(ch) > 127})
    assert non_ascii == [], f"Windows PowerShell 5.1 local UAT script must be ASCII-only; found: {non_ascii!r}"


@pytest.mark.skipif(sys.platform != "win32", reason="PowerShell parser check is Windows-only")
def test_bps_i00_local_uat_script_parses_on_windows():
    shell = shutil.which("pwsh") or shutil.which("powershell")
    assert shell, "PowerShell executable is required on Windows"
    parser = (
        "$tokens=$null; $errors=$null; "
        "$path=$env:BPS_I00_UAT_SCRIPT; "
        "[System.Management.Automation.Language.Parser]::ParseFile("
        "$path,[ref]$tokens,[ref]$errors) | Out-Null; "
        "if($errors.Count -gt 0){"
        "$errors | ForEach-Object { Write-Error $_.Message }; exit 1 }; exit 0"
    )
    env = os.environ.copy()
    env["BPS_I00_UAT_SCRIPT"] = str(SCRIPT)
    subprocess.run([shell, "-NoProfile", "-Command", parser], cwd=ROOT, env=env, check=True)
