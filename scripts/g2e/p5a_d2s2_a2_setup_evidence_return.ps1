param(
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedReportSha256 = "2DD26DD7CE3A337307147C4BE82DA1F653AB76048ABF3CBA6BCA7C0C8555C5D8"
$ExpectedEvidenceSha256 = "984F828C4796B77D7BD125D5E5A8421C04F9B496D9117B6F1F5003D9B8A1E2C3"
$ExpectedSourceHead = "17bf616138433f96ee3447e8f846aad430df3771"
$ExpectedOneClickBlob = "c714da50f577fad5e4fdd7b64ede894330459243"
$ExpectedPreflightBlob = "8d449867586663195a998ce6eefbcbf8a218030f"

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-OptionalProperty($Object, [string]$Name) {
    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Get-JsonlMetadata([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return [ordered]@{
            exists = $false
            sha256 = $null
            size_bytes = $null
            line_count = $null
        }
    }

    $item = Get-Item -LiteralPath $Path
    $lineCount = 0
    foreach ($line in [IO.File]::ReadLines($Path)) {
        $lineCount++
    }

    return [ordered]@{
        exists = $true
        sha256 = (Get-Sha256 $Path).ToLowerInvariant()
        size_bytes = [int64]$item.Length
        line_count = $lineCount
    }
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

$A2Root = Join-Path $ProjectRoot "g2e\.local\P5A-D2S2-A2"
$ReportPath = Join-Path $A2Root "report\P5A_D2S2_A2_ONECLICK_REPORT.json"
$EvidenceRoot = Join-Path $A2Root "evidence\preturn-a2"
$ReturnDir = Join-Path $A2Root "return"

if (-not (Test-Path -LiteralPath $ReportPath -PathType Leaf)) {
    throw "A2_REPORT_MISSING:$ReportPath"
}

$reportHash = Get-Sha256 $ReportPath
if ($reportHash -ne $ExpectedReportSha256) {
    throw "A2_REPORT_HASH_MISMATCH:$reportHash"
}

$report = Get-Content -LiteralPath $ReportPath -Raw | ConvertFrom-Json

if ([string](Get-OptionalProperty $report "schema") -ne "G2E-P5A-D2S2-A2-ONECLICK-REPORT-v1") {
    throw "A2_REPORT_SCHEMA_MISMATCH"
}
if ([string](Get-OptionalProperty $report "source_head") -ne $ExpectedSourceHead) {
    throw "A2_REPORT_SOURCE_HEAD_MISMATCH"
}
if ([string](Get-OptionalProperty $report "oneclick_blob") -ne $ExpectedOneClickBlob) {
    throw "A2_REPORT_ONECLICK_BLOB_MISMATCH"
}
if ([string](Get-OptionalProperty $report "preflight_blob") -ne $ExpectedPreflightBlob) {
    throw "A2_REPORT_PREFLIGHT_BLOB_MISMATCH"
}
if ((Get-OptionalProperty $report "turn_start_request_sent") -ne $false) {
    throw "A2_REPORT_TURN_FIREWALL_VIOLATION"
}
if ((Get-OptionalProperty $report "scientific_attempt_consumed") -ne $false) {
    throw "A2_REPORT_ATTEMPT_FIREWALL_VIOLATION"
}

$evidencePathRaw = [string](Get-OptionalProperty $report "preflight_evidence_file")
if ([string]::IsNullOrWhiteSpace($evidencePathRaw)) {
    throw "A2_EVIDENCE_PATH_MISSING"
}

$evidencePath = [IO.Path]::GetFullPath($evidencePathRaw)
$evidenceRootFull = [IO.Path]::GetFullPath($EvidenceRoot)
$expectedPrefix = $evidenceRootFull.TrimEnd("\") + "\"
if (-not $evidencePath.StartsWith(
    $expectedPrefix,
    [StringComparison]::OrdinalIgnoreCase
)) {
    throw "A2_EVIDENCE_PATH_OUTSIDE_FIXED_ROOT:$evidencePath"
}
if (-not (Test-Path -LiteralPath $evidencePath -PathType Leaf)) {
    throw "A2_EVIDENCE_FILE_MISSING:$evidencePath"
}

$evidenceHash = Get-Sha256 $evidencePath
$declaredEvidenceHash = ([string](Get-OptionalProperty $report "preflight_evidence_sha256")).ToUpperInvariant()
if ($evidenceHash -ne $ExpectedEvidenceSha256) {
    throw "A2_EVIDENCE_HASH_MISMATCH:$evidenceHash"
}
if ($evidenceHash -ne $declaredEvidenceHash) {
    throw "A2_EVIDENCE_DECLARED_HASH_MISMATCH:$($evidenceHash):$($declaredEvidenceHash)"
}

$evidence = Get-Content -LiteralPath $evidencePath -Raw | ConvertFrom-Json
if ((Get-OptionalProperty $evidence "turn_start_request_sent") -ne $false) {
    throw "A2_EVIDENCE_TURN_FIREWALL_VIOLATION"
}
if ((Get-OptionalProperty $evidence "scientific_attempt_consumed") -ne $false) {
    throw "A2_EVIDENCE_ATTEMPT_FIREWALL_VIOLATION"
}

$protocolPath = Join-Path $EvidenceRoot "P5A_D2S2_A2_PREFLIGHT_PROTOCOL_SANITIZED.jsonl"
$stderrHashPath = Join-Path $EvidenceRoot "P5A_D2S2_A2_PREFLIGHT_STDERR_HASHES.jsonl"

New-Item -ItemType Directory -Path $ReturnDir -Force | Out-Null
$stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")
$returnPath = Join-Path $ReturnDir "P5A_D2S2_A2_SETUP_EVIDENCE_RETURN_$stamp.json"

$return = [ordered]@{
    schema = "G2E-P5A-D2S2-A2-SETUP-EVIDENCE-RETURN-v1"
    created_utc = [DateTime]::UtcNow.ToString("o")
    evidence_return_only = $true

    bound_report = [ordered]@{
        sha256 = $reportHash.ToLowerInvariant()
        status = Get-OptionalProperty $report "status"
        source_head = Get-OptionalProperty $report "source_head"
        qualified_candidate_sha = Get-OptionalProperty $report "qualified_candidate_sha"
        oneclick_blob = Get-OptionalProperty $report "oneclick_blob"
        preflight_blob = Get-OptionalProperty $report "preflight_blob"
        config_sha256 = Get-OptionalProperty $report "config_sha256"
        preflight_evidence_sha256 = Get-OptionalProperty $report "preflight_evidence_sha256"
        diagnostic = Get-OptionalProperty $report "diagnostic"
    }

    setup = [ordered]@{
        windows_sandbox_readiness_before = Get-OptionalProperty $evidence "windows_sandbox_readiness_before"
        windows_sandbox_setup_requested = Get-OptionalProperty $evidence "windows_sandbox_setup_requested"
        windows_sandbox_setup_started = Get-OptionalProperty $evidence "windows_sandbox_setup_started"
        windows_sandbox_setup_completed = Get-OptionalProperty $evidence "windows_sandbox_setup_completed"
        windows_sandbox_setup_success = Get-OptionalProperty $evidence "windows_sandbox_setup_success"
        windows_sandbox_setup_mode = Get-OptionalProperty $evidence "windows_sandbox_setup_mode"
        windows_sandbox_setup_error_code = Get-OptionalProperty $evidence "windows_sandbox_setup_error_code"
        windows_sandbox_setup_error_redacted = Get-OptionalProperty $evidence "windows_sandbox_setup_error_redacted"
        windows_sandbox_setup_error_sha256 = Get-OptionalProperty $evidence "windows_sandbox_setup_error_sha256"
        windows_sandbox_readiness_after = Get-OptionalProperty $evidence "windows_sandbox_readiness_after"
        driver_exception = Get-OptionalProperty $evidence "driver_exception"
        app_server_exit_code = Get-OptionalProperty $evidence "app_server_exit_code"
    }

    downstream_gates = [ordered]@{
        configured_mcp_count = Get-OptionalProperty $evidence "configured_mcp_count"
        installed_app_count = Get-OptionalProperty $evidence "installed_app_count"
        callable_or_enabled_app_count = Get-OptionalProperty $evidence "callable_or_enabled_app_count"
        auth_ready = Get-OptionalProperty $evidence "auth_ready"
        profile_present = Get-OptionalProperty $evidence "profile_present"
        profile_allowed = Get-OptionalProperty $evidence "profile_allowed"
        thread_id_present = -not [string]::IsNullOrWhiteSpace([string](Get-OptionalProperty $evidence "thread_id"))
        active_permission_profile = Get-OptionalProperty $evidence "active_permission_profile"
        instruction_sources = Get-OptionalProperty $evidence "instruction_sources"
    }

    integrity = [ordered]@{
        evidence_sha256 = $evidenceHash.ToLowerInvariant()
        result_exists = Get-OptionalProperty $evidence "result_exists"
        input_unchanged = Get-OptionalProperty $evidence "input_unchanged"
        task_unchanged = Get-OptionalProperty $evidence "task_unchanged"
        workspace_names = Get-OptionalProperty $evidence "workspace_names"
        codex_home_post_entries = Get-OptionalProperty $evidence "codex_home_post_entries"
        protocol_sanitized = Get-JsonlMetadata $protocolPath
        stderr_hashes = Get-JsonlMetadata $stderrHashPath
    }

    turn_start_request_sent = $false
    scientific_attempt_consumed = $false
}

Write-JsonFile $returnPath $return

Write-Host ""
Write-Host "=== D2-S2 A2 SETUP EVIDENCE RETURN READY ==="
Write-Host "REPORT SHA  : $($reportHash.ToLowerInvariant())"
Write-Host "EVIDENCE SHA: $($evidenceHash.ToLowerInvariant())"
Write-Host "RETURN JSON : $returnPath"
Write-Host "TURN START  : FALSE"
Write-Host "ATTEMPT USED: FALSE"
