param(
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedTopReportSha256 = "09E71058BD9E9B4B4FD2E5C4F5F0C412C228932FA183D08DC7D6DF4D0FC5E712"
$ExpectedRunnerEvidenceSha256 = "AE60858BFD53268FBB43FB5F1166AAA3ACD4FE322F23279B139412BB260B8017"
$ExpectedVerificationSha256 = "528B1FD3460C1EFDD180DFAB703DC264A5102D44FABF887411DC3F1BBC51C418"

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Assert-UnderRoot([string]$Root, [string]$Path) {
    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    $pathFull = [IO.Path]::GetFullPath($Path)
    if (-not $pathFull.StartsWith($rootFull, [StringComparison]::OrdinalIgnoreCase)) {
        throw "EVIDENCE_PATH_ESCAPES_SCIENCE_ROOT:$pathFull"
    }
    return $pathFull
}

function Write-JsonFile([string]$Path, $Object) {
    [IO.File]::WriteAllText(
        $Path,
        (($Object | ConvertTo-Json -Depth 16) + [Environment]::NewLine),
        [Text.UTF8Encoding]::new($false)
    )
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
else {
    $ProjectRoot = (Resolve-Path $ProjectRoot).Path
}

$ScienceRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S3-SCIENCE-002"
$BundleRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S3-POSTCLOSURE-BUNDLE"
$ZipPath = Join-Path $ProjectRoot "g2e\.local\P5A-D2S3-POSTCLOSURE-BUNDLE.zip"

if (-not (Test-Path -LiteralPath $ScienceRoot -PathType Container)) {
    throw "SCIENCE002_ROOT_MISSING:$ScienceRoot"
}
if (Test-Path -LiteralPath $BundleRoot) {
    throw "POSTCLOSURE_BUNDLE_ROOT_ALREADY_EXISTS:$BundleRoot"
}
if (Test-Path -LiteralPath $ZipPath) {
    throw "POSTCLOSURE_BUNDLE_ZIP_ALREADY_EXISTS:$ZipPath"
}

$TopReport = Join-Path $ScienceRoot "report\P5A_D2S3_SCIENTIFIC_EXECUTION_REPORT.json"
$RunnerEvidence = Join-Path $ScienceRoot "evidence\science-002\P5A_D2S3_SCIENTIFIC_RUNNER_EVIDENCE.json"
$Marker = Join-Path $ScienceRoot "evidence\science-002\P5A_D2S3_TURN_START_SENT.marker"
$Verification = Join-Path $ScienceRoot "verification\P5A_D2S3_SCIENTIFIC_VERIFICATION.json"

foreach ($path in @($TopReport, $RunnerEvidence, $Marker, $Verification)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "REQUIRED_EVIDENCE_MISSING:$path"
    }
}

if ((Get-Sha256 $TopReport) -ne $ExpectedTopReportSha256) {
    throw "TOP_REPORT_HASH_DRIFT"
}
if ((Get-Sha256 $RunnerEvidence) -ne $ExpectedRunnerEvidenceSha256) {
    throw "RUNNER_EVIDENCE_HASH_DRIFT"
}
if ((Get-Sha256 $Verification) -ne $ExpectedVerificationSha256) {
    throw "VERIFICATION_HASH_DRIFT"
}

$RunnerData = Get-Content -LiteralPath $RunnerEvidence -Raw | ConvertFrom-Json
$ProtocolPathRaw = [string]$RunnerData.protocol_file
$StderrHashPathRaw = [string]$RunnerData.stderr_hash_file

if ([string]::IsNullOrWhiteSpace($ProtocolPathRaw)) {
    throw "RUNNER_PROTOCOL_FILE_MISSING"
}
if ([string]::IsNullOrWhiteSpace($StderrHashPathRaw)) {
    throw "RUNNER_STDERR_HASH_FILE_MISSING"
}

$ProtocolPath = Assert-UnderRoot $ScienceRoot $ProtocolPathRaw
$StderrHashPath = Assert-UnderRoot $ScienceRoot $StderrHashPathRaw

foreach ($path in @($ProtocolPath, $StderrHashPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "REFERENCED_EVIDENCE_MISSING:$path"
    }
}

New-Item -ItemType Directory -Path $BundleRoot -Force | Out-Null

$items = @(
    [pscustomobject]@{ Name = "P5A_D2S3_SCIENTIFIC_EXECUTION_REPORT.json"; Source = $TopReport },
    [pscustomobject]@{ Name = "P5A_D2S3_SCIENTIFIC_RUNNER_EVIDENCE.json"; Source = $RunnerEvidence },
    [pscustomobject]@{ Name = "P5A_D2S3_TURN_START_SENT.marker"; Source = $Marker },
    [pscustomobject]@{ Name = "P5A_D2S3_SCIENTIFIC_VERIFICATION.json"; Source = $Verification },
    [pscustomobject]@{ Name = "P5A_D2S3_PROTOCOL_SANITIZED.jsonl"; Source = $ProtocolPath },
    [pscustomobject]@{ Name = "P5A_D2S3_STDERR_HASHES.jsonl"; Source = $StderrHashPath }
)

$manifestItems = @()
foreach ($item in $items) {
    $destination = Join-Path $BundleRoot $item.Name
    Copy-Item -LiteralPath $item.Source -Destination $destination
    $manifestItems += [ordered]@{
        name = $item.Name
        source = $item.Source
        sha256 = (Get-Sha256 $destination).ToLowerInvariant()
        size_bytes = (Get-Item -LiteralPath $destination).Length
    }
}

$manifest = [ordered]@{
    schema = "G2E-P5A-D2S3-POSTCLOSURE-EVIDENCE-BUNDLE-v1"
    science002_root = $ScienceRoot
    collection_mode = "READ_ONLY_EXISTING_EVIDENCE"
    codex_started = $false
    rpc_sent = $false
    vhdx_mounted = $false
    scientific_attempt_retried = $false
    items = $manifestItems
}

$ManifestPath = Join-Path $BundleRoot "P5A_D2S3_POSTCLOSURE_BUNDLE_MANIFEST.json"
Write-JsonFile $ManifestPath $manifest

Compress-Archive -LiteralPath (Join-Path $BundleRoot "*") -DestinationPath $ZipPath -CompressionLevel Optimal

Write-Host ""
Write-Host "=== D2-S3 POST-CLOSURE EVIDENCE BUNDLE READY ==="
Write-Host "BUNDLE DIR : $BundleRoot"
Write-Host "ZIP        : $ZipPath"
Write-Host "CODEX      : NOT STARTED"
Write-Host "RPC        : NONE"
Write-Host "VHDX       : NOT MOUNTED"
Write-Host "RETRY      : FALSE"
