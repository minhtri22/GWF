param(
    [ValidateSet("start","stop","restart","status","foreground")]
    [string]$Action = "start",
    [string]$RepoRoot = "",
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8765
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
} else {
    $RepoRoot = (Resolve-Path $RepoRoot).Path
}

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$StateDir = Join-Path $RepoRoot ".gwr\server"
$PidPath = Join-Path $StateDir "server-process.json"
$StdoutPath = Join-Path $StateDir "server.stdout.log"
$StderrPath = Join-Path $StateDir "server.stderr.log"

function Require-Python {
    if (-not (Test-Path $Python)) {
        throw "Missing .venv Python. Run .\install.ps1 first."
    }
}

function Get-ServerMeta {
    if (-not (Test-Path $PidPath)) { return $null }
    try {
        return Get-Content $PidPath -Raw | ConvertFrom-Json
    } catch {
        throw "Invalid server process metadata: $PidPath"
    }
}

function Get-OwnedProcess {
    $meta = Get-ServerMeta
    if (-not $meta) { return $null }

    $proc = Get-Process -Id ([int]$meta.pid) -ErrorAction SilentlyContinue
    if (-not $proc) { return $null }

    $actualStart = $proc.StartTime.ToUniversalTime()
    $expectedStart = [DateTime]::Parse($meta.process_started_at).ToUniversalTime()
    if ([Math]::Abs(($actualStart - $expectedStart).TotalSeconds) -gt 3) {
        throw "PID $($meta.pid) is no longer the GWF process recorded by this launcher. Refusing to operate on it."
    }

    try {
        $cim = Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $meta.pid) -ErrorAction Stop
        if ($cim.CommandLine -and $cim.CommandLine -notmatch "gwr\.server") {
            throw "PID $($meta.pid) command line does not identify gwr.server. Refusing to operate on it."
        }
    } catch {
        if ($_.Exception.Message -like "*Refusing to operate*") { throw }
    }

    return $proc
}

function Test-Ready {
    param([int]$Attempts = 1)
    for ($i=0; $i -lt $Attempts; $i++) {
        try {
            $r = Invoke-RestMethod -Uri ("http://{0}:{1}/ready" -f $HostName,$Port) -TimeoutSec 2
            if ($r.ok -eq $true) { return $true }
        } catch {}
        if ($Attempts -gt 1) { Start-Sleep -Milliseconds 500 }
    }
    return $false
}

function Start-Gwf {
    Require-Python
    if (-not $env:GWR_AUTH_SECRET -or ([Text.Encoding]::UTF8.GetByteCount($env:GWR_AUTH_SECRET) -lt 32)) {
        throw "GWR_AUTH_SECRET must be set to at least 32 bytes before starting the canonical server."
    }

    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

    $existing = Get-OwnedProcess
    if ($existing) {
        throw "GWF server is already running with PID $($existing.Id)."
    }
    Remove-Item $PidPath -Force -ErrorAction SilentlyContinue
    Remove-Item $StdoutPath,$StderrPath -Force -ErrorAction SilentlyContinue

    Push-Location $RepoRoot
    try {
        & $Python -m gwr.server --repo-root $RepoRoot --host $HostName --port $Port --check-config
        if ($LASTEXITCODE -ne 0) {
            throw "Canonical server configuration validation failed."
        }

        $args = @("-m","gwr.server","--repo-root",$RepoRoot,"--host",$HostName,"--port","$Port")
        $proc = Start-Process -FilePath $Python -ArgumentList $args -WorkingDirectory $RepoRoot -RedirectStandardOutput $StdoutPath -RedirectStandardError $StderrPath -PassThru
    } finally {
        Pop-Location
    }

    $head = (& git -C $RepoRoot rev-parse HEAD 2>$null | Select-Object -First 1)
    $meta = [ordered]@{
        schema = "GWF-SERVER-PROCESS-v1"
        pid = $proc.Id
        process_started_at = $proc.StartTime.ToUniversalTime().ToString("o")
        repo_root = $RepoRoot
        git_head = $head
        host = $HostName
        port = $Port
        stdout = $StdoutPath
        stderr = $StderrPath
        recorded_at = (Get-Date).ToUniversalTime().ToString("o")
    }
    $meta | ConvertTo-Json -Depth 5 | Set-Content -Path $PidPath -Encoding UTF8

    if (-not (Test-Ready -Attempts 40)) {
        if (-not $proc.HasExited) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
        Write-Host "--- server stdout ---"
        if (Test-Path $StdoutPath) { Get-Content $StdoutPath }
        Write-Host "--- server stderr ---"
        if (Test-Path $StderrPath) { Get-Content $StderrPath }
        throw "Canonical GWF server did not become ready."
    }

    Write-Host "GWF_SERVER=RUNNING" -ForegroundColor Green
    Write-Host ("PID={0}" -f $proc.Id)
    Write-Host ("URL=http://{0}:{1}/app" -f $HostName,$Port)
    Write-Host ("READY=http://{0}:{1}/ready" -f $HostName,$Port)
    Write-Host ("HEAD={0}" -f $head)
}

function Stop-Gwf {
    $proc = Get-OwnedProcess
    if (-not $proc) {
        Remove-Item $PidPath -Force -ErrorAction SilentlyContinue
        Write-Host "GWF_SERVER=STOPPED"
        return
    }

    Stop-Process -Id $proc.Id -ErrorAction Stop
    if (-not $proc.WaitForExit(10000)) {
        throw "GWF server did not stop within 10 seconds."
    }
    Remove-Item $PidPath -Force -ErrorAction SilentlyContinue
    Write-Host "GWF_SERVER=STOPPED" -ForegroundColor Green
}

function Show-Status {
    $proc = Get-OwnedProcess
    if (-not $proc) {
        Write-Host "GWF_SERVER=STOPPED"
        return
    }
    $ready = Test-Ready
    $state = if ($ready) { "READY" } else { "RUNNING_NOT_READY" }
    Write-Host ("GWF_SERVER={0}" -f $state)
    Write-Host ("PID={0}" -f $proc.Id)
    Write-Host ("URL=http://{0}:{1}/app" -f $HostName,$Port)
}

switch ($Action) {
    "start" { Start-Gwf }
    "stop" { Stop-Gwf }
    "restart" { Stop-Gwf; Start-Gwf }
    "status" { Show-Status }
    "foreground" {
        Require-Python
        if (-not $env:GWR_AUTH_SECRET -or ([Text.Encoding]::UTF8.GetByteCount($env:GWR_AUTH_SECRET) -lt 32)) {
            throw "GWR_AUTH_SECRET must be set to at least 32 bytes."
        }
        Push-Location $RepoRoot
        try {
            & $Python -m gwr.server --repo-root $RepoRoot --host $HostName --port $Port
            exit $LASTEXITCODE
        } finally {
            Pop-Location
        }
    }
}
