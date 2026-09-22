param(
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Get-UtcNow {
    return [DateTime]::UtcNow.ToString("o")
}

function Write-Json([string]$Path, $Object) {
    $json = $Object | ConvertTo-Json -Depth 16
    [IO.File]::WriteAllText($Path, $json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
}

function Invoke-Git([string]$Root, [string[]]$Args) {
    $out = & git -C $Root @Args 2>&1
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        throw "GIT_FAILED[$code]: git -C $Root $($Args -join ' ') :: $((($out | Out-String).Trim()))"
    }
    return (($out | Out-String).Trim())
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
}

$InvocationStart = [DateTime]::UtcNow
$InvocationStartText = $InvocationStart.ToString("o")

$BootstrapRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S2-BOOTSTRAP"
$ReportDir = Join-Path $BootstrapRoot "report"
$ReturnDir = Join-Path $BootstrapRoot "return"
$ArchiveDir = Join-Path $BootstrapRoot "archive"
$CanonicalReport = Join-Path $ReportDir "P5A_D2S2_ELEVATION_BOOTSTRAP_REPORT.json"
$CanonicalMd = Join-Path $ReportDir "P5A_D2S2_ELEVATION_BOOTSTRAP_REPORT.md"
$DiagnosticScript = Join-Path $ProjectRoot "scripts\g2e\p5a_d2s2_elevation_bootstrap_diagnostic.ps1"

New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
New-Item -ItemType Directory -Path $ReturnDir -Force | Out-Null
New-Item -ItemType Directory -Path $ArchiveDir -Force | Out-Null

Write-Host "Fetching exact qualified branch state..."
Invoke-Git $ProjectRoot @("fetch", "--prune", "origin", "feature/g2e-framework") | Out-Null
Invoke-Git $ProjectRoot @("switch", "--detach", "origin/feature/g2e-framework") | Out-Null
$Head = (Invoke-Git $ProjectRoot @("rev-parse", "HEAD")).ToLowerInvariant()

Write-Host "HEAD: $Head"

$stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")

if (Test-Path -LiteralPath $CanonicalReport) {
    $archiveJson = Join-Path $ArchiveDir "P5A_D2S2_ELEVATION_BOOTSTRAP_REPORT_STALE_$stamp.json"
    Copy-Item -LiteralPath $CanonicalReport -Destination $archiveJson -Force
}
if (Test-Path -LiteralPath $CanonicalMd) {
    $archiveMd = Join-Path $ArchiveDir "P5A_D2S2_ELEVATION_BOOTSTRAP_REPORT_STALE_$stamp.md"
    Copy-Item -LiteralPath $CanonicalMd -Destination $archiveMd -Force
}

if (-not (Test-Path -LiteralPath $DiagnosticScript -PathType Leaf)) {
    throw "DIAGNOSTIC_SCRIPT_MISSING:$DiagnosticScript"
}

Write-Host "Running qualified elevation bootstrap diagnostic..."
& $DiagnosticScript -ProjectRoot $ProjectRoot
$DiagnosticExit = $LASTEXITCODE

if (-not (Test-Path -LiteralPath $CanonicalReport -PathType Leaf)) {
    throw "NEW_DIAGNOSTIC_REPORT_MISSING:$CanonicalReport"
}

$Report = Get-Content -LiteralPath $CanonicalReport -Raw | ConvertFrom-Json

if ([string]::IsNullOrWhiteSpace([string]$Report.source_head)) {
    throw "RETURN_REPORT_SOURCE_HEAD_MISSING"
}
if (([string]$Report.source_head).ToLowerInvariant() -ne $Head) {
    throw "RETURN_REPORT_HEAD_MISMATCH:REPORT=$($Report.source_head);HEAD=$Head"
}

try {
    $ReportStarted = [DateTime]::Parse(
        [string]$Report.started_utc,
        [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::AdjustToUniversal
    ).ToUniversalTime()
}
catch {
    throw "RETURN_REPORT_STARTED_UTC_INVALID:$($Report.started_utc)"
}

if ($ReportStarted -lt $InvocationStart.AddSeconds(-2)) {
    throw "RETURN_REPORT_STALE:STARTED=$($Report.started_utc);WRAPPER_START=$InvocationStartText"
}

if ($Report.scientific_attempt_consumed -ne $false) {
    throw "SCIENTIFIC_ATTEMPT_CONSUMPTION_FIREWALL_VIOLATION"
}
if ($Report.model_turn_executed -ne $false) {
    throw "MODEL_TURN_FIREWALL_VIOLATION"
}

$head12 = $Head.Substring(0, 12)
$returnStamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")
$ReturnJson = Join-Path $ReturnDir "P5A_D2S2_ELEVATION_BOOTSTRAP_REPORT_${head12}_${returnStamp}.json"

$returnEnvelope = [pscustomobject][ordered]@{
    schema = "G2E-P5A-D2S2-ELEVATION-BOOTSTRAP-RETURN-v1"
    wrapper_started_utc = $InvocationStartText
    wrapper_completed_utc = Get-UtcNow
    exact_head = $Head
    diagnostic_exit_code = $DiagnosticExit
    return_freshness_verified = $true
    scientific_attempt_consumed = $false
    model_turn_executed = $false
    diagnostic_report = $Report
}

Write-Json $ReturnJson $returnEnvelope

Write-Host ""
Write-Host "=== D2-S2 DIAGNOSTIC RETURN READY ==="
Write-Host "HEAD        : $Head"
Write-Host "STATUS      : $($Report.status)"
Write-Host "RETURN JSON : $ReturnJson"
Write-Host "TURN START  : FALSE"
Write-Host "ATTEMPT USED: FALSE"

exit $DiagnosticExit
