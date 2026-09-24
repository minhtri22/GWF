param(
    [ValidateSet("data","error")]
    [string]$Mode = "data",
    [string]$RepoRoot = "",
    [string]$Python = "",
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8877
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
} else {
    $RepoRoot = (Resolve-Path $RepoRoot).Path
}

if (-not $Python) {
    $Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
}

if (-not (Test-Path $Python)) {
    throw "Missing Python runtime: $Python. Run the repository install first or pass -Python explicitly."
}

$Fixture = Join-Path $RepoRoot "scripts\bps_home_uat_fixture.py"
if (-not (Test-Path $Fixture)) {
    throw "Missing Home UAT fixture: $Fixture"
}

$Head = (& git -C $RepoRoot rev-parse HEAD 2>$null | Select-Object -First 1)
if ($LASTEXITCODE -ne 0) {
    throw "Cannot resolve git HEAD for $RepoRoot"
}

Write-Host ""
Write-Host "GWF HOME UAT - ISOLATED FIXTURE" -ForegroundColor Cyan
Write-Host ("MODE={0}" -f $Mode)
Write-Host ("HEAD={0}" -f $Head)
Write-Host ("URL=http://{0}:{1}/app/home" -f $HostName,$Port)
Write-Host "This fixture uses an ephemeral temporary database and does not touch the canonical working DB."
Write-Host "Stop with Ctrl+C."
Write-Host ""

Push-Location $RepoRoot
try {
    & $Python $Fixture --mode $Mode --host $HostName --port $Port
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
