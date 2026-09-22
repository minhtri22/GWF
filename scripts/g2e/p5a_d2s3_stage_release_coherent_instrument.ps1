param(
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ProgressPreference = "SilentlyContinue"

$ReleaseTag = "rust-v0.153.4"
$SourceCommit = "3d2ee51ca2d5db578f328aa75e20aa22c0197c9a"

$CodexZipUrl = "https://github.com/openai/codex/releases/download/rust-v0.153.4/codex-x86_64-pc-windows-msvc.exe.zip"
$CodexZipSha256 = "C016B0E6968B78586919C720D2685A03712F6D5F11BCD9D6F92C91EB8C41BA16"
$CodexZipSize = [int64]104174469
$CodexBinaryName = "codex-x86_64-pc-windows-msvc.exe"
$CodexBinarySha256 = "444A3F0008050605CAE73CD9B7A2DCAC61294062DFAAB56DD20430FD6498518B"
$CodexBinarySize = [int64]295408944

$HelperZipUrl = "https://github.com/openai/codex/releases/download/rust-v0.153.4/codex-windows-sandbox-setup-x86_64-pc-windows-msvc.exe.zip"
$HelperZipSha256 = "256C4DEB16946A01A52156E8FD619BAEC38743FF482741767AB5FDB4079E97CB"
$HelperZipSize = [int64]5562782
$HelperBinaryName = "codex-windows-sandbox-setup-x86_64-pc-windows-msvc.exe"
$HelperBinarySha256 = "0C3EEB7CEE8D2BC4C8644DEF3C818E8B06760979572DCEDC919C38D0F38F64C4"
$HelperBinarySize = [int64]15413040

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-MarkerMatrix([string]$Path) {
    $bytes = [IO.File]::ReadAllBytes($Path)
    $ascii = [Text.Encoding]::ASCII.GetString($bytes)
    return [ordered]@{
        "interactive-provision" = $ascii.Contains("interactive-provision")
        "full" = $ascii.Contains("full")
        "provision-only" = $ascii.Contains("provision-only")
        "read-acls-only" = $ascii.Contains("read-acls-only")
    }
}

function Assert-FileIdentity(
    [string]$Path,
    [int64]$ExpectedSize,
    [string]$ExpectedSha256,
    [string]$Label
) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$($Label)_MISSING:$Path"
    }

    $item = Get-Item -LiteralPath $Path
    if ([int64]$item.Length -ne $ExpectedSize) {
        throw "$($Label)_SIZE_MISMATCH:$($item.Length):$ExpectedSize"
    }

    $hash = Get-Sha256 $Path
    if ($hash -ne $ExpectedSha256) {
        throw "$($Label)_HASH_MISMATCH:$hash:$ExpectedSha256"
    }
}

function Get-ExactlyOneFile([string]$Root, [string]$Name) {
    $matches = @(Get-ChildItem -LiteralPath $Root -Recurse -File | Where-Object { $_.Name -eq $Name })
    if ($matches.Count -ne 1) {
        throw "EXPECTED_EXACTLY_ONE_FILE:$Name:$($matches.Count)"
    }
    return $matches[0].FullName
}

function Write-JsonFile([string]$Path, $Object) {
    $json = $Object | ConvertTo-Json -Depth 16
    [IO.File]::WriteAllText(
        $Path,
        $json + [Environment]::NewLine,
        [Text.UTF8Encoding]::new($false)
    )
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
else {
    $ProjectRoot = (Resolve-Path $ProjectRoot).Path
}

$LocalRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S3-INSTRUMENT"
if (Test-Path -LiteralPath $LocalRoot) {
    throw "D2S3_INSTRUMENT_ROOT_ALREADY_EXISTS:$LocalRoot"
}

$PackageRoot = Join-Path $LocalRoot "package"
$BinDir = Join-Path $PackageRoot "bin"
$ResourcesDir = Join-Path $PackageRoot "codex-resources"
$ReportDir = Join-Path $LocalRoot "report"
$TempRoot = Join-Path $LocalRoot ("temp-" + [Guid]::NewGuid().ToString("N"))

New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
New-Item -ItemType Directory -Path $TempRoot -Force | Out-Null

$ReportPath = Join-Path $ReportDir "P5A_D2S3_INSTRUMENT_STAGING_REPORT.json"

$report = [ordered]@{
    schema = "G2E-P5A-D2S3-INSTRUMENT-STAGING-v1"
    status = "STARTED"
    release_tag = $ReleaseTag
    source_commit = $SourceCommit
    global_install_modified = $false
    executables_invoked = $false
    turn_start_request_sent = $false
    scientific_attempt_consumed = $false
    codex = $null
    helper = $null
    final_layout = [ordered]@{
        codex = "package/bin/codex.exe"
        helper = "package/codex-resources/codex-windows-sandbox-setup.exe"
    }
    temp_cleanup = [ordered]@{
        attempted = $false
        removed = $false
        error = $null
    }
    diagnostic = $null
}

$exitCode = 0

try {
    $CodexZip = Join-Path $TempRoot "codex.zip"
    $HelperZip = Join-Path $TempRoot "helper.zip"
    $CodexExtract = Join-Path $TempRoot "codex-extract"
    $HelperExtract = Join-Path $TempRoot "helper-extract"

    New-Item -ItemType Directory -Path $CodexExtract -Force | Out-Null
    New-Item -ItemType Directory -Path $HelperExtract -Force | Out-Null

    Invoke-WebRequest -UseBasicParsing -Uri $CodexZipUrl -OutFile $CodexZip
    Invoke-WebRequest -UseBasicParsing -Uri $HelperZipUrl -OutFile $HelperZip

    Assert-FileIdentity $CodexZip $CodexZipSize $CodexZipSha256 "CODEX_ARCHIVE"
    Assert-FileIdentity $HelperZip $HelperZipSize $HelperZipSha256 "HELPER_ARCHIVE"

    Expand-Archive -LiteralPath $CodexZip -DestinationPath $CodexExtract
    Expand-Archive -LiteralPath $HelperZip -DestinationPath $HelperExtract

    $CodexExtracted = Get-ExactlyOneFile $CodexExtract $CodexBinaryName
    $HelperExtracted = Get-ExactlyOneFile $HelperExtract $HelperBinaryName

    Assert-FileIdentity $CodexExtracted $CodexBinarySize $CodexBinarySha256 "CODEX_EXTRACTED"
    Assert-FileIdentity $HelperExtracted $HelperBinarySize $HelperBinarySha256 "HELPER_EXTRACTED"

    $CodexMarkers = Get-MarkerMatrix $CodexExtracted
    $HelperMarkers = Get-MarkerMatrix $HelperExtracted

    if ($CodexMarkers["interactive-provision"]) {
        throw "CODEX_INTERACTIVE_PROVISION_MARKER_PRESENT"
    }
    if ($HelperMarkers["interactive-provision"]) {
        throw "HELPER_INTERACTIVE_PROVISION_MARKER_PRESENT"
    }
    if (-not $CodexMarkers["full"] -or -not $CodexMarkers["provision-only"]) {
        throw "CODEX_REQUIRED_MODE_MARKER_MISSING"
    }
    if (-not $HelperMarkers["full"] -or
        -not $HelperMarkers["provision-only"] -or
        -not $HelperMarkers["read-acls-only"]) {
        throw "HELPER_REQUIRED_MODE_MARKER_MISSING"
    }

    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
    New-Item -ItemType Directory -Path $ResourcesDir -Force | Out-Null

    $FinalCodex = Join-Path $BinDir "codex.exe"
    $FinalHelper = Join-Path $ResourcesDir "codex-windows-sandbox-setup.exe"

    Copy-Item -LiteralPath $CodexExtracted -Destination $FinalCodex
    Copy-Item -LiteralPath $HelperExtracted -Destination $FinalHelper

    Assert-FileIdentity $FinalCodex $CodexBinarySize $CodexBinarySha256 "FINAL_CODEX"
    Assert-FileIdentity $FinalHelper $HelperBinarySize $HelperBinarySha256 "FINAL_HELPER"

    $report.codex = [ordered]@{
        archive_sha256 = (Get-Sha256 $CodexZip).ToLowerInvariant()
        extracted_sha256 = (Get-Sha256 $CodexExtracted).ToLowerInvariant()
        final_sha256 = (Get-Sha256 $FinalCodex).ToLowerInvariant()
        size_bytes = (Get-Item -LiteralPath $FinalCodex).Length
        markers = $CodexMarkers
    }
    $report.helper = [ordered]@{
        archive_sha256 = (Get-Sha256 $HelperZip).ToLowerInvariant()
        extracted_sha256 = (Get-Sha256 $HelperExtracted).ToLowerInvariant()
        final_sha256 = (Get-Sha256 $FinalHelper).ToLowerInvariant()
        size_bytes = (Get-Item -LiteralPath $FinalHelper).Length
        markers = $HelperMarkers
    }

    $report.status = "STAGING_PASS_PLATFORM_PREFLIGHT_GATE_REQUIRED"
    $report.diagnostic = "OFFICIAL_RELEASE_INSTRUMENT_STAGED"
}
catch {
    $exitCode = 1
    $report.status = "STAGING_BLOCKED"
    $report.diagnostic = $_.Exception.Message
}
finally {
    $report.temp_cleanup.attempted = $true
    try {
        if (Test-Path -LiteralPath $TempRoot) {
            Remove-Item -LiteralPath $TempRoot -Recurse -Force
        }
        $report.temp_cleanup.removed = -not (Test-Path -LiteralPath $TempRoot)
        if (-not $report.temp_cleanup.removed) {
            $report.temp_cleanup.error = "TEMP_ROOT_STILL_EXISTS"
            $exitCode = 1
            if ($report.status -eq "STAGING_PASS_PLATFORM_PREFLIGHT_GATE_REQUIRED") {
                $report.status = "STAGING_BLOCKED"
                $report.diagnostic = "TEMP_CLEANUP_FAILED"
            }
        }
    }
    catch {
        $report.temp_cleanup.removed = $false
        $report.temp_cleanup.error = $_.Exception.Message
        $exitCode = 1
        if ($report.status -eq "STAGING_PASS_PLATFORM_PREFLIGHT_GATE_REQUIRED") {
            $report.status = "STAGING_BLOCKED"
            $report.diagnostic = "TEMP_CLEANUP_EXCEPTION"
        }
    }

    try {
        Write-JsonFile $ReportPath $report
    }
    catch {
        Write-Error "STAGING_REPORT_WRITE_FAILED:$($_.Exception.Message)"
        exit 2
    }
}

Write-Host ""
Write-Host "=== D2-S3 INSTRUMENT STAGING COMPLETE ==="
Write-Host "STATUS      : $($report.status)"
Write-Host "REPORT JSON : $ReportPath"
Write-Host "GLOBAL MOD  : FALSE"
Write-Host "EXECUTED    : FALSE"
Write-Host "TURN START  : FALSE"
Write-Host "ATTEMPT USED: FALSE"

exit $exitCode
