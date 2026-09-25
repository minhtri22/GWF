param(
    [int]$TimeoutSeconds = 180,
    [int]$RuntimeStartupSeconds = 45
)

$ErrorActionPreference = "Stop"

$Repo = "D:\WORK\RESEARCH\4.GWF"
$Codex = Join-Path $Repo "g2e\.local\codex-official-0.153.4\package\bin\codex.exe"
$DevDir = "$env:USERPROFILE\.codex-chatgpt-web-dev"
$BridgeHome = Join-Path $DevDir "core-home"
$LauncherData = $DevDir
$Smoke = Join-Path $Repo "scripts\g2e\g2e_product_smoke.py"
$Launcher = "D:\WORK\RESEARCH\codex-chatgpt-web\launcher\artifacts\codex-web-gpt-4.0.7-win-x64-portable\Codex Web GPT.exe"
$HealthUri = "http://127.0.0.1:17841/healthz"

function Get-CgwHealth {
    try {
        return Invoke-RestMethod -Method Get -Uri $HealthUri -TimeoutSec 2
    }
    catch {
        return $null
    }
}

function Get-CustomLauncherProcesses {
    return @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -ieq "Codex Web GPT.exe" -and
            -not [string]::IsNullOrWhiteSpace([string]$_.ExecutablePath) -and
            [string]$_.ExecutablePath -ieq $Launcher
        }
    )
}

function Start-CustomCgwRuntime {
    if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) {
        throw "CUSTOM_CGW_LAUNCHER_MISSING: $Launcher"
    }

    $ExistingListener = @(
        Get-NetTCPConnection -LocalPort 17841 -State Listen -ErrorAction SilentlyContinue
    )
    if ($ExistingListener.Count -gt 0) {
        $Pids = @($ExistingListener | Select-Object -ExpandProperty OwningProcess -Unique)
        throw "PORT_17841_LISTENER_PRESENT_BUT_HEALTH_UNAVAILABLE: pids=$($Pids -join ',')"
    }

    $Existing = @(Get-CustomLauncherProcesses)
    if ($Existing.Count -gt 0) {
        $Pids = @($Existing | Select-Object -ExpandProperty ProcessId)
        Write-Host "CUSTOM_CGW_LAUNCHER_ALREADY_RUNNING=pids=$($Pids -join ',')" -ForegroundColor Yellow
        Write-Host "Waiting for its runtime instead of starting another launcher..."
    }
    else {
        $LauncherSha = (Get-FileHash -LiteralPath $Launcher -Algorithm SHA256).Hash.ToLowerInvariant()
        Write-Host "CUSTOM_CGW_LAUNCHER=$Launcher"
        Write-Host "CUSTOM_CGW_LAUNCHER_SHA256=$LauncherSha"

        $OldLauncherData = $env:CODEX_WEB_GPT_LAUNCHER_DATA_DIR
        $OldBridgeHome = $env:CODEX_CHATGPT_WEB_HOME
        $OldCodexHome = $env:CODEX_HOME

        try {
            $env:CODEX_WEB_GPT_LAUNCHER_DATA_DIR = $DevDir
            $env:CODEX_CHATGPT_WEB_HOME = $BridgeHome
            $env:CODEX_HOME = Join-Path $DevDir "codex-home"

            $Started = Start-Process -FilePath $Launcher -PassThru
            Write-Host "CUSTOM_CGW_LAUNCHER_STARTED_PID=$($Started.Id)" -ForegroundColor Yellow
        }
        finally {
            if ($null -eq $OldLauncherData) {
                Remove-Item Env:CODEX_WEB_GPT_LAUNCHER_DATA_DIR -ErrorAction SilentlyContinue
            } else {
                $env:CODEX_WEB_GPT_LAUNCHER_DATA_DIR = $OldLauncherData
            }

            if ($null -eq $OldBridgeHome) {
                Remove-Item Env:CODEX_CHATGPT_WEB_HOME -ErrorAction SilentlyContinue
            } else {
                $env:CODEX_CHATGPT_WEB_HOME = $OldBridgeHome
            }

            if ($null -eq $OldCodexHome) {
                Remove-Item Env:CODEX_HOME -ErrorAction SilentlyContinue
            } else {
                $env:CODEX_HOME = $OldCodexHome
            }
        }
    }

    $Deadline = (Get-Date).AddSeconds($RuntimeStartupSeconds)
    do {
        Start-Sleep -Milliseconds 500
        $Health = Get-CgwHealth
        if ($null -ne $Health -and [string]$Health.status -eq "ok") {
            return $Health
        }
    } while ((Get-Date) -lt $Deadline)

    $Existing = @(Get-CustomLauncherProcesses)
    $Pids = @($Existing | Select-Object -ExpandProperty ProcessId)
    throw "CUSTOM_CGW_RUNTIME_START_TIMEOUT: launcher_pids=$($Pids -join ',')"
}

Set-Location $Repo

Write-Host ""
Write-Host "=== G2E PRODUCT SMOKE ===" -ForegroundColor Cyan
Write-Host "Mode: PRODUCT"
Write-Host "Goal: Codex -> CGW -> ChatGPT Web -> tool -> result.json"
Write-Host ""

$Health = Get-CgwHealth
if ($null -eq $Health -or [string]$Health.status -ne "ok") {
    Write-Host "CGW_RUNTIME=DOWN — auto-starting custom runtime" -ForegroundColor Yellow
    $Health = Start-CustomCgwRuntime
}
else {
    Write-Host "CGW_RUNTIME=READY"
}

Write-Host "CGW_HEALTH_PID=$($Health.pid)"
Write-Host "CGW_HEALTH_MODE=$($Health.mode)"
Write-Host "CGW_HEALTH_VERSION=$($Health.version)"

$Args = @(
    $Smoke,
    "--repo", $Repo,
    "--codex-exe", $Codex,
    "--bridge-home", $BridgeHome,
    "--launcher-data", $LauncherData,
    "--timeout", "$TimeoutSeconds"
)

& python @Args

if ($LASTEXITCODE -ne 0) {
    throw "G2E_PRODUCT_SMOKE_FAIL"
}

Write-Host ""
Write-Host "G2E_PRODUCT_SMOKE_PASS" -ForegroundColor Green
