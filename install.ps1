param(
    [string]$PythonVersion = "3.12",
    [bool]$InstallPythonIfMissing = $true,
    [switch]$FreshVenv,
    [switch]$Qualification,
    [switch]$SkipTests,
    [switch]$SkipPostgres,
    [switch]$RequirePostgres,
    [switch]$SkipUat,
    [string]$PostgresUrl = $env:GWR_TEST_DATABASE_URL
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $RepoRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$ReportDir = Join-Path $RepoRoot ".gwr\install"
$ReportPath = Join-Path $ReportDir "install-report.json"
$DgP10ReportPath = Join-Path $ReportDir "dg-p10-gate.json"
$UatRoot = Join-Path $RepoRoot ".gwr\uat"
$StartedAt = (Get-Date).ToUniversalTime().ToString("o")
$DockerContainer = $null
$OriginalPostgresUrl = $env:GWR_TEST_DATABASE_URL
$TotalTimer = [Diagnostics.Stopwatch]::StartNew()
$Timings = [ordered]@{}
$LegacyQualificationRequested = @("SkipTests","SkipPostgres","RequirePostgres","SkipUat","PostgresUrl") | Where-Object { $PSBoundParameters.ContainsKey($_) }
$QualificationMode = $Qualification.IsPresent -or ($LegacyQualificationRequested.Count -gt 0)

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments
    )
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $FilePath $($Arguments -join ' ')"
    }
}

function Get-PythonExecutable {
    $requested = $PythonVersion.Trim()

    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            $candidate = (& py "-$requested" -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1)
            if ($candidate -and (Test-Path $candidate)) {
                return (Resolve-Path $candidate).Path
            }
        } catch {}
    }

    foreach ($name in @("python", "python3")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) {
            try {
                $info = & $cmd.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}'); print(sys.executable)"
                $version = [Version]($info | Select-Object -First 1)
                if ($version -ge [Version]"3.11") {
                    $candidate = ($info | Select-Object -Skip 1 -First 1)
                    if ($candidate -and (Test-Path $candidate)) {
                        return (Resolve-Path $candidate).Path
                    }
                }
            } catch {}
        }
    }

    $known = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
        "C:\Python312\python.exe"
    )
    foreach ($candidate in $known) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    if (-not $InstallPythonIfMissing) {
        throw "Python >=3.11 was not found. Install Python 3.12 or enable automatic Python installation."
    }

    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "Python >=3.11 was not found and winget is unavailable. Install Python 3.12, then rerun .\install.ps1."
    }

    Write-Step "Python not found; installing Python 3.12 with winget"
    Invoke-Checked -FilePath $winget.Source -Arguments @("install", "--id", "Python.Python.3.12", "-e", "--source", "winget", "--accept-package-agreements", "--accept-source-agreements", "--silent")

    foreach ($candidate in $known) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $candidate = (& py "-$requested" -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1)
        if ($candidate -and (Test-Path $candidate)) {
            return (Resolve-Path $candidate).Path
        }
    }
    throw "Python installation completed but python.exe could not be resolved in this PowerShell session."
}

function Test-Docker {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) { return $false }
    try {
        & $docker.Source version --format "{{.Server.Version}}" *> $null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Start-EphemeralPostgres {
    $docker = (Get-Command docker -ErrorAction Stop).Source
    $name = "gwr-install-pg-$PID"
    $port = 55432
    Write-Step "Starting ephemeral PostgreSQL 17 with Docker"
    & $docker rm -f $name *> $null
    $portMap = ("{0}:5432" -f $port)
    $container = & $docker run -d --rm --name $name -e POSTGRES_USER=gwr -e POSTGRES_PASSWORD=gwr_install_password -e POSTGRES_DB=gwr_install -p $portMap postgres:17
    if ($LASTEXITCODE -ne 0 -or -not $container) {
        throw "Could not start PostgreSQL Docker container."
    }

    $ready = $false
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 500
        & $docker exec $name pg_isready -U gwr -d gwr_install *> $null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
    }
    if (-not $ready) {
        & $docker logs $name
        throw "Ephemeral PostgreSQL did not become ready."
    }
    return @{
        Name = $name
        Url = "postgresql://gwr:gwr_install_password@127.0.0.1:55432/gwr_install"
    }
}

if (-not (Test-Path (Join-Path $RepoRoot "pyproject.toml"))) {
    throw "install.ps1 must be run from the GWF repository checkout."
}
if (-not (Test-Path (Join-Path $RepoRoot "domains\research.workflow.yaml"))) {
    throw "Research domain package is missing."
}
if (-not (Test-Path (Join-Path $RepoRoot "domains\software.workflow.yaml"))) {
    throw "Software domain package is missing."
}

$GitSha = $null
$GitDirty = $null
if (Get-Command git -ErrorAction SilentlyContinue) {
    Push-Location $RepoRoot
    try {
        $GitSha = (& git rev-parse HEAD 2>$null | Select-Object -First 1)
        $dirty = (& git status --porcelain 2>$null)
        $GitDirty = [bool]$dirty
    } finally {
        Pop-Location
    }
}

$Python = Get-PythonExecutable
$PythonInfo = & $Python -c "import json,sys; print(json.dumps({'version':sys.version.split()[0],'executable':sys.executable}))" | ConvertFrom-Json
if ([Version]$PythonInfo.version -lt [Version]"3.11") {
    throw "GWF requires Python >=3.11; resolved $($PythonInfo.version)."
}

Write-Step "Repository baseline"
Write-Host "repo=$RepoRoot"
Write-Host "git_sha=$GitSha"
Write-Host "git_dirty=$GitDirty"
Write-Host "python=$($PythonInfo.version) [$($PythonInfo.executable)]"

if ($FreshVenv -and (Test-Path $VenvDir)) {
    Write-Step "Removing existing virtual environment"
    Remove-Item -Recurse -Force $VenvDir
}

if (-not (Test-Path $VenvPython)) {
    Write-Step "Creating isolated virtual environment"
    Invoke-Checked -FilePath $Python -Arguments @("-m", "venv", $VenvDir)
}

Write-Step $(if ($QualificationMode) { "Installing GWF with development/PostgreSQL qualification dependencies" } else { "Installing GWF runtime dependencies" })
$DependencyTimer = [Diagnostics.Stopwatch]::StartNew()
Invoke-Checked -FilePath $VenvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")
Push-Location $RepoRoot
try {
    $InstallTarget = if ($QualificationMode) { ".[dev,postgres]" } else { "." }
    Invoke-Checked -FilePath $VenvPython -Arguments @("-m", "pip", "install", "-e", $InstallTarget)
} finally {
    Pop-Location
}
$DependencyTimer.Stop()
$Timings.dependencies = [Math]::Round($DependencyTimer.Elapsed.TotalSeconds, 3)

$env:PYTHONPATH = (Join-Path $RepoRoot "src")
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

Write-Step "Validating production domain/pilot contracts and compiling runtime"
$ValidationTimer = [Diagnostics.Stopwatch]::StartNew()
Push-Location $RepoRoot
try {
    Invoke-Checked -FilePath $VenvPython -Arguments @("tools/gwr_domain.py", "validate", "domains/research.workflow.yaml")
    Invoke-Checked -FilePath $VenvPython -Arguments @("tools/gwr_domain.py", "validate", "domains/software.workflow.yaml")
    Invoke-Checked -FilePath $VenvPython -Arguments @("tools/gwr_pilot.py", "validate", "pilots/cqg.research.yaml")
    Invoke-Checked -FilePath $VenvPython -Arguments @("tools/gwr_pilot.py", "validate", "pilots/gwf.self-upgrade.yaml")
    $CompileTargets = if ($QualificationMode) { @("src", "tests", "tools") } else { @("src") }
    Invoke-Checked -FilePath $VenvPython -Arguments (@("-m", "compileall", "-q") + $CompileTargets)
    $OriginalAuthSecret = $env:GWR_AUTH_SECRET
    if (-not $env:GWR_AUTH_SECRET) { $env:GWR_AUTH_SECRET = "install-smoke-only-secret-0123456789abcdef" }
    try {
        Invoke-Checked -FilePath $VenvPython -Arguments @("-m", "gwr.server", "--repo-root", $RepoRoot, "--check-config")
    } finally {
        if ($OriginalAuthSecret) { $env:GWR_AUTH_SECRET = $OriginalAuthSecret } else { Remove-Item Env:GWR_AUTH_SECRET -ErrorAction SilentlyContinue }
    }
} finally {
    Pop-Location
}
$ValidationTimer.Stop()
$Timings.validation = [Math]::Round($ValidationTimer.Elapsed.TotalSeconds, 3)

$QualificationTimer = [Diagnostics.Stopwatch]::StartNew()
$DgP10Status = "SKIPPED"
if ($QualificationMode -and -not $SkipUat) {
    Write-Step "Running bounded DG-P10 governance/UAT gate"
    Push-Location $RepoRoot
    try {
        Invoke-Checked -FilePath $VenvPython -Arguments @("tools/run_dg_p10_gate.py", "--out", $DgP10ReportPath)
        $dg = Get-Content $DgP10ReportPath -Raw | ConvertFrom-Json
        if ($dg.status -ne "PASS") { throw "DG-P10 gate status=$($dg.status)" }
        $DgP10Status = "PASS"
    } finally {
        Pop-Location
    }

    Write-Step "Preparing local project-document UAT workspace"
    New-Item -ItemType Directory -Force -Path (Join-Path $UatRoot "docs\gov\archive") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $UatRoot "docs\phase1\archive") | Out-Null
    @"
# GWF local UAT

This workspace is disposable and is not an authoritative project.

Prepared document layout:

```text
docs/
  gov/
    archive/
  phase1/
    archive/
```

Re-run the bounded DG-P10 gate:

```powershell
.\.venv\Scripts\python.exe tools\run_dg_p10_gate.py --out .gwr\uat\DG_P10_UAT.json
```

Expected gate result: PASS.

Policy checks exercised by the automated suite include AUTO owner-scope authority,
HUMAN_APPROVE, GOV/FROZEN blocking, semantic escalation, exact proposed-content
digest, deterministic vN -> archive/vN + vN+1 lineage planning, and zero DG-P11
source-mutation side effects.
"@ | Set-Content -Path (Join-Path $UatRoot "UAT.md") -Encoding UTF8
}

$LocalTests = "SKIPPED"
if ($QualificationMode -and -not $SkipTests) {
    Write-Step "Running local full test suite"
    Push-Location $RepoRoot
    try {
        Invoke-Checked -FilePath $VenvPython -Arguments @("-m", "pytest", "-q")
        $LocalTests = "PASS"
    } finally {
        Pop-Location
    }
}

$PostgresStatus = "SKIPPED"
$PostgresSource = $null
try {
    if ($QualificationMode -and -not $SkipPostgres) {
        if ($PostgresUrl) {
            $PostgresSource = "GWR_TEST_DATABASE_URL"
        } elseif (Test-Docker) {
            $pg = Start-EphemeralPostgres
            $DockerContainer = $pg.Name
            $PostgresUrl = $pg.Url
            $PostgresSource = "ephemeral-docker"
        } elseif ($RequirePostgres) {
            throw "PostgreSQL qualification is required, but neither GWR_TEST_DATABASE_URL nor a running Docker engine is available."
        }

        if ($PostgresUrl) {
            Write-Step "Running PostgreSQL domain/orchestrator qualification"
            $env:GWR_TEST_DATABASE_URL = $PostgresUrl
            $env:GWR_TEST_NAMESPACE_PREFIX = "gwr_install_$PID"
            Push-Location $RepoRoot
            try {
                Invoke-Checked -FilePath $VenvPython -Arguments @("-m", "pytest", "-q", "tests/test_v085_domain_skills.py")
                $PostgresStatus = "PASS"
            } finally {
                Pop-Location
            }
        } else {
            Write-Host "PostgreSQL qualification skipped: no DSN and Docker is unavailable." -ForegroundColor Yellow
        }
    }
} finally {
    if ($DockerContainer) {
        Write-Step "Removing ephemeral PostgreSQL container"
        & docker rm -f $DockerContainer *> $null
    }
    if ($OriginalPostgresUrl) {
        $env:GWR_TEST_DATABASE_URL = $OriginalPostgresUrl
    } else {
        Remove-Item Env:GWR_TEST_DATABASE_URL -ErrorAction SilentlyContinue
    }
    Remove-Item Env:GWR_TEST_NAMESPACE_PREFIX -ErrorAction SilentlyContinue
}

$QualificationTimer.Stop()
$Timings.qualification = [Math]::Round($QualificationTimer.Elapsed.TotalSeconds, 3)
$TotalTimer.Stop()
$Timings.total = [Math]::Round($TotalTimer.Elapsed.TotalSeconds, 3)

$RuntimeVersion = (& $VenvPython -c "import importlib.metadata; print(importlib.metadata.version('governed-workflow-runtime'))" | Select-Object -First 1)
$report = [ordered]@{
    project = "Governed Workflow Runtime (GWF)"
    runtime_version = $RuntimeVersion
    status = "PASS"
    mode = if ($QualificationMode) { "QUALIFICATION" } else { "INSTALL" }
    started_at = $StartedAt
    finished_at = (Get-Date).ToUniversalTime().ToString("o")
    repository = $RepoRoot
    git_sha = $GitSha
    git_dirty = $GitDirty
    python_version = $PythonInfo.version
    venv_python = $VenvPython
    timings_seconds = $Timings
    domains = @{
        research = "PASS"
        software = "PASS"
    }
    pilots = @{
        cqg_next_study = "PASS"
        gwf_self_upgrade = "PASS"
    }
    compileall = "PASS"
    local_tests = $LocalTests
    dg_p10 = @{
        status = $DgP10Status
        evidence = if ($DgP10Status -eq "PASS") { $DgP10ReportPath } else { $null }
    }
    uat = @{
        prepared = ($QualificationMode -and -not $SkipUat)
        root = if ($QualificationMode -and -not $SkipUat) { $UatRoot } else { $null }
    }
    postgres = @{
        status = $PostgresStatus
        source = $PostgresSource
        dsn_persisted = $false
    }
}
$report | ConvertTo-Json -Depth 6 | Set-Content -Path $ReportPath -Encoding UTF8

Write-Step "GWF installation complete"
Write-Host "status=PASS" -ForegroundColor Green
Write-Host "venv=$VenvDir"
Write-Host "report=$ReportPath"
Write-Host ("mode={0}" -f $(if ($QualificationMode) { "QUALIFICATION" } else { "INSTALL" }))
Write-Host "uat=$UatRoot"
Write-Host ""
Write-Host "Activate when needed:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "Re-run after any git pull:"
Write-Host "  .\install.ps1"
