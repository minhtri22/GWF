param(
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedTopReportSha256 = "E98EE53C550E13DD42715C63CA6CBF887AA69396F50C90ABC6637A54A3DC9536"
$ExpectedRunnerEvidenceSha256 = "6E1EF9D48BF640A8A285370549771F76048E0280EAF121450F3FA6679C069F5D"
$ExpectedVerificationSha256 = "BF0E848C1EBA9E8C0BF8A74DA5FCF96DBE29898EC26D1EF91D21ACA13A7BE01"

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

$ScienceRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S4-SCIENCE-001"
$BundleRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S4-POSTCLOSURE-BUNDLE"
$ZipPath = Join-Path $ProjectRoot "g2e\.local\P5A-D2S4-POSTCLOSURE-BUNDLE.zip"

if (-not (Test-Path -LiteralPath $ScienceRoot -PathType Container)) {
    throw "SCIENCE001_ROOT_MISSING:$ScienceRoot"
}
if (Test-Path -LiteralPath $BundleRoot) {
    throw "POSTCLOSURE_BUNDLE_ROOT_ALREADY_EXISTS:$BundleRoot"
}
if (Test-Path -LiteralPath $ZipPath) {
    throw "POSTCLOSURE_BUNDLE_ZIP_ALREADY_EXISTS:$ZipPath"
}

$TopReport = Join-Path $ScienceRoot "report\P5A_D2S4_SCIENTIFIC_EXECUTION_REPORT.json"
$RunnerEvidence = Join-Path $ScienceRoot "evidence\science-001\P5A_D2S4_SCIENTIFIC_RUNNER_EVIDENCE.json"
$Marker = Join-Path $ScienceRoot "evidence\science-001\P5A_D2S4_TURN_START_SENT.marker"
$Verification = Join-Path $ScienceRoot "verification\P5A_D2S4_SCIENTIFIC_VERIFICATION.json"

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
$ActualVerificationSha256 = Get-Sha256 $Verification
$VerificationHashMatch = ($ActualVerificationSha256 -eq $ExpectedVerificationSha256)

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

if (-not (Test-Path -LiteralPath $ProtocolPath -PathType Leaf)) {
    throw "REFERENCED_PROTOCOL_EVIDENCE_MISSING:$ProtocolPath"
}

$StderrHashExists = Test-Path -LiteralPath $StderrHashPath -PathType Leaf

New-Item -ItemType Directory -Path $BundleRoot -Force | Out-Null

$items = @(
    [pscustomobject]@{ Name = "P5A_D2S4_SCIENTIFIC_EXECUTION_REPORT.json"; Source = $TopReport; ExpectedSha256 = $ExpectedTopReportSha256 },
    [pscustomobject]@{ Name = "P5A_D2S4_SCIENTIFIC_RUNNER_EVIDENCE.json"; Source = $RunnerEvidence; ExpectedSha256 = $ExpectedRunnerEvidenceSha256 },
    [pscustomobject]@{ Name = "P5A_D2S4_TURN_START_SENT.marker"; Source = $Marker; ExpectedSha256 = $null },
    [pscustomobject]@{ Name = "P5A_D2S4_SCIENTIFIC_VERIFICATION.json"; Source = $Verification; ExpectedSha256 = $ExpectedVerificationSha256 },
    [pscustomobject]@{ Name = "P5A_D2S4_PROTOCOL_SANITIZED.jsonl"; Source = $ProtocolPath; ExpectedSha256 = $null }
)

$manifestItems = @()
foreach ($item in $items) {
    $destination = Join-Path $BundleRoot $item.Name
    Copy-Item -LiteralPath $item.Source -Destination $destination
    $actualSha256 = Get-Sha256 $destination
    $expectedSha256 = $item.ExpectedSha256
    $hashMatch = if ([string]::IsNullOrWhiteSpace([string]$expectedSha256)) {
        $null
    }
    else {
        ($actualSha256 -eq [string]$expectedSha256)
    }

    $manifestItems += [ordered]@{
        name = $item.Name
        source = $item.Source
        exists = $true
        sha256 = $actualSha256.ToLowerInvariant()
        expected_sha256 = if ([string]::IsNullOrWhiteSpace([string]$expectedSha256)) { $null } else { ([string]$expectedSha256).ToLowerInvariant() }
        hash_match = $hashMatch
        size_bytes = (Get-Item -LiteralPath $destination).Length
    }
}

if ($StderrHashExists) {
    $stderrDestination = Join-Path $BundleRoot "P5A_D2S4_STDERR_HASHES.jsonl"
    Copy-Item -LiteralPath $StderrHashPath -Destination $stderrDestination
    $manifestItems += [ordered]@{
        name = "P5A_D2S4_STDERR_HASHES.jsonl"
        source = $StderrHashPath
        exists = $true
        sha256 = (Get-Sha256 $stderrDestination).ToLowerInvariant()
        size_bytes = (Get-Item -LiteralPath $stderrDestination).Length
    }
}
else {
    $manifestItems += [ordered]@{
        name = "P5A_D2S4_STDERR_HASHES.jsonl"
        source = $StderrHashPath
        exists = $false
        sha256 = $null
        size_bytes = 0
        absence_semantics = "RPC_CLIENT_MATERIALIZES_STDERR_HASH_FILE_ONLY_AFTER_FIRST_STDERR_RECORD"
    }
}

$manifest = [ordered]@{
    schema = "G2E-P5A-D2S4-POSTCLOSURE-EVIDENCE-BUNDLE-v1"
    science001_root = $ScienceRoot
    collection_mode = "READ_ONLY_EXISTING_EVIDENCE"
    codex_started = $false
    rpc_sent = $false
    vhdx_mounted = $false
    scientific_attempt_retried = $false
    verification_identity = [ordered]@{
        expected_sha256 = $ExpectedVerificationSha256.ToLowerInvariant()
        actual_sha256 = $ActualVerificationSha256.ToLowerInvariant()
        hash_match = $VerificationHashMatch
        finding = if ($VerificationHashMatch) { $null } else { "VERIFICATION_HASH_MISMATCH_PRESERVED" }
    }
    items = $manifestItems
}

$ManifestPath = Join-Path $BundleRoot "P5A_D2S4_POSTCLOSURE_BUNDLE_MANIFEST.json"
Write-JsonFile $ManifestPath $manifest

Compress-Archive -Path (Join-Path $BundleRoot "*") -DestinationPath $ZipPath -CompressionLevel Optimal

Write-Host ""
Write-Host "=== D2-S4 POST-CLOSURE EVIDENCE BUNDLE READY ==="
Write-Host "BUNDLE DIR : $BundleRoot"
Write-Host "ZIP        : $ZipPath"
Write-Host "CODEX      : NOT STARTED"
Write-Host "RPC        : NONE"
Write-Host "VHDX       : NOT MOUNTED"
Write-Host "RETRY      : FALSE"
Write-Host "VERIFY HASH: expected=$($ExpectedVerificationSha256.ToLowerInvariant())"
Write-Host "VERIFY HASH: actual=$($ActualVerificationSha256.ToLowerInvariant())"
Write-Host "VERIFY MATCH: $VerificationHashMatch"
