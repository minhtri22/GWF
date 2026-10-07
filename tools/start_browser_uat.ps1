param(
    [string]$RepoRoot = "D:\WORK\RESEARCH\4.GWF",
    [string]$ExpectedHead = "a09f79ae74a838d2c5998813560373c849669872",
    [int]$Port = 8765
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path $RepoRoot).Path
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$BrowserRoot = Join-Path $RepoRoot ".gwr\uat\browser"
$PidPath = Join-Path $BrowserRoot "server.pid"
$Stdout = Join-Path $BrowserRoot "server.stdout.log"
$Stderr = Join-Path $BrowserRoot "server.stderr.log"
$ServerScript = Join-Path $PSScriptRoot "browser_uat_server.py"

if (-not (Test-Path $Python)) {
    throw "Missing .venv. Run .\install.ps1 first."
}
if (-not (Test-Path $ServerScript)) {
    throw "browser_uat_server.py must be next to this launcher."
}

Push-Location $RepoRoot
try {
    $ActualHead = (& git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw "git rev-parse failed." }

    if ($ActualHead -ne $ExpectedHead) {
        throw "HEAD mismatch. Expected $ExpectedHead, found $ActualHead."
    }

    $Tracked = @(& git status --porcelain --untracked-files=no)
    if ($LASTEXITCODE -ne 0) { throw "git status failed." }
    if ($Tracked.Count -gt 0) {
        throw "Tracked working tree is not clean. Refusing browser UAT."
    }
}
finally {
    Pop-Location
}

New-Item -ItemType Directory -Force -Path $BrowserRoot | Out-Null

if (Test-Path $PidPath) {
    $oldPid = (Get-Content $PidPath -Raw).Trim()
    if ($oldPid) {
        $oldProc = Get-Process -Id ([int]$oldPid) -ErrorAction SilentlyContinue
        if ($oldProc) {
            throw "A browser UAT server is already running with PID $oldPid. Stop it before starting another."
        }
    }
    Remove-Item $PidPath -Force -ErrorAction SilentlyContinue
}

& $Python -c "import uvicorn" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "uvicorn is not present in the formal-close install environment." -ForegroundColor Yellow
    Write-Host "Installing UAT-only server dependency into .venv; product source is unchanged." -ForegroundColor Yellow
    & $Python -m pip install "uvicorn>=0.30,<1"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not install uvicorn for browser UAT."
    }
}

Remove-Item $Stdout,$Stderr -Force -ErrorAction SilentlyContinue

$argList = @(
    $ServerScript,
    "--repo-root", $RepoRoot,
    "--expected-head", $ExpectedHead,
    "--host", "127.0.0.1",
    "--port", "$Port"
)

$proc = Start-Process -FilePath $Python -ArgumentList $argList -WorkingDirectory $RepoRoot -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -PassThru

Set-Content -Path $PidPath -Value $proc.Id -Encoding ASCII

$url = "http://127.0.0.1:$Port/uat"
$health = "http://127.0.0.1:$Port/health"

$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    if ($proc.HasExited) { break }
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri $health -TimeoutSec 2
        if ($r.StatusCode -eq 200) {
            $ready = $true
            break
        }
    }
    catch {}
}

if (-not $ready) {
    Write-Host ""
    Write-Host "Browser UAT server failed to become ready." -ForegroundColor Red
    if (Test-Path $Stdout) {
        Write-Host "--- stdout ---"
        Get-Content $Stdout
    }
    if (Test-Path $Stderr) {
        Write-Host "--- stderr ---"
        Get-Content $Stderr
    }
    if (-not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    throw "Browser UAT startup failed."
}

Write-Host ""
Write-Host "GWF LIVE BROWSER UAT READY" -ForegroundColor Green
Write-Host "HEAD=$ActualHead"
Write-Host "PID=$($proc.Id)"
Write-Host "URL=$url"
Write-Host "API_DOCS=http://127.0.0.1:$Port/docs"
Write-Host "USERNAME=operator"
Write-Host "PASSWORD=operator-password-long"
Write-Host "STDOUT=$Stdout"
Write-Host "STDERR=$Stderr"
Write-Host ""
Write-Host "Stop command:"
Write-Host "Stop-Process -Id $($proc.Id)"

Start-Process $url
