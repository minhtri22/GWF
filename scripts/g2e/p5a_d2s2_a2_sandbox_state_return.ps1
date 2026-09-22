param(
    [string]$ProjectRoot = "",
    [switch]$SanitizationSelfTest
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$BoundSetupEvidenceReturnSha256 = "6F1F178AAC74037ED8AB1661B5B98BEEF5871F0CDE0456237A52AFD84FB23CEB"

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-OptionalProperty($Object, [string]$Name) {
    if ($null -eq $Object) { return $null }
    $p = $Object.PSObject.Properties[$Name]
    if ($null -eq $p) { return $null }
    return $p.Value
}

function Sanitize-Text(
    [string]$Text,
    [string]$Root,
    [string]$UserProfile,
    [string]$Username
) {
    if ($null -eq $Text) { return $null }
    $out = [string]$Text

    if (-not [string]::IsNullOrWhiteSpace($Root)) {
        $out = $out.Replace($Root, "<PROJECT_ROOT>")
    }
    if (-not [string]::IsNullOrWhiteSpace($UserProfile)) {
        $out = $out.Replace($UserProfile, "<USERPROFILE>")
    }
    if (-not [string]::IsNullOrWhiteSpace($Username)) {
        $pattern = "(?i)(?<=\\|/)" + [regex]::Escape($Username) + "(?=\\|/)"
        $out = [regex]::Replace($out, $pattern, "<USER>")
    }
    return $out
}

function Write-JsonFile([string]$Path, $Object) {
    $json = $Object | ConvertTo-Json -Depth 16
    [IO.File]::WriteAllText(
        $Path,
        $json + [Environment]::NewLine,
        [Text.UTF8Encoding]::new($false)
    )
}

if ($SanitizationSelfTest) {
    $sample = "D:\\WORK\\ROOT\\x C:\\Users\\Alice\\secret D:\\Else\\Alice\\y"
    $actual = Sanitize-Text $sample "D:\\WORK\\ROOT" "C:\\Users\\Alice" "Alice"
    $expected = "<PROJECT_ROOT>\\x <USERPROFILE>\\secret D:\\Else\\<USER>\\y"
    if ($actual -ne $expected) {
        throw "SANITIZATION_SELFTEST_FAILED:$actual"
    }
    Write-Host "SANITIZATION_SELFTEST_PASS"
    exit 0
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
else {
    $ProjectRoot = (Resolve-Path $ProjectRoot).Path
}

$A2Root = Join-Path $ProjectRoot "g2e\.local\P5A-D2S2-A2"
$SandboxDir = Join-Path $A2Root "codex-home\preturn-a2\.sandbox"
$ReturnDir = Join-Path $A2Root "return"

if (-not (Test-Path -LiteralPath $SandboxDir -PathType Container)) {
    throw "A2_SANDBOX_DIR_MISSING:$SandboxDir"
}

$SandboxFull = [IO.Path]::GetFullPath($SandboxDir)
$A2RootFull = [IO.Path]::GetFullPath($A2Root)
if (-not $SandboxFull.StartsWith(
    $A2RootFull.TrimEnd("\") + "\",
    [StringComparison]::OrdinalIgnoreCase
)) {
    throw "SANDBOX_SCOPE_ESCAPE"
}

$UserProfile = [Environment]::GetFolderPath("UserProfile")
$Username = $env:USERNAME

$entries = @()
foreach ($item in @(Get-ChildItem -LiteralPath $SandboxDir -Force | Sort-Object Name)) {
    $record = [ordered]@{
        name = $item.Name
        kind = if ($item.PSIsContainer) { "directory" } else { "file" }
        size_bytes = if ($item.PSIsContainer) { $null } else { [int64]$item.Length }
        sha256 = if ($item.PSIsContainer) { $null } else { Get-Sha256 $item.FullName }
        reparse_point = [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
    }
    $entries += [pscustomobject]$record
}

$SetupErrorPath = Join-Path $SandboxDir "setup_error.json"
$setupError = [ordered]@{
    exists = $false
    sha256 = $null
    code = $null
    message_sanitized = $null
    message_sha256 = $null
    parse_error = $null
}
if (Test-Path -LiteralPath $SetupErrorPath -PathType Leaf) {
    $setupError.exists = $true
    $setupError.sha256 = Get-Sha256 $SetupErrorPath
    try {
        $raw = Get-Content -LiteralPath $SetupErrorPath -Raw
        $parsed = $raw | ConvertFrom-Json
        $setupError.code = Get-OptionalProperty $parsed "code"
        $msg = [string](Get-OptionalProperty $parsed "message")
        if (-not [string]::IsNullOrWhiteSpace($msg)) {
            $msgBytes = [Text.Encoding]::UTF8.GetBytes($msg)
            $sha = [Security.Cryptography.SHA256]::Create()
            try {
                $setupError.message_sha256 = ([BitConverter]::ToString($sha.ComputeHash($msgBytes))).Replace("-", "").ToLowerInvariant()
            }
            finally {
                $sha.Dispose()
            }
            $setupError.message_sanitized = Sanitize-Text $msg $ProjectRoot $UserProfile $Username
        }
    }
    catch {
        $setupError.parse_error = Sanitize-Text $_.Exception.Message $ProjectRoot $UserProfile $Username
    }
}

$SetupMarkerPath = Join-Path $SandboxDir "setup_marker.json"
$setupMarker = [ordered]@{
    exists = $false
    sha256 = $null
    version = $null
    parse_error = $null
}
if (Test-Path -LiteralPath $SetupMarkerPath -PathType Leaf) {
    $setupMarker.exists = $true
    $setupMarker.sha256 = Get-Sha256 $SetupMarkerPath
    try {
        $marker = Get-Content -LiteralPath $SetupMarkerPath -Raw | ConvertFrom-Json
        $setupMarker.version = Get-OptionalProperty $marker "version"
    }
    catch {
        $setupMarker.parse_error = Sanitize-Text $_.Exception.Message $ProjectRoot $UserProfile $Username
    }
}

$logMetadata = @()
$relevant = New-Object System.Collections.Generic.List[string]
$tokens = @("setup","helper","sandbox","firewall","acl","user","error","fail")

foreach ($log in @(Get-ChildItem -LiteralPath $SandboxDir -File -Filter "sandbox.*.log" | Sort-Object Name)) {
    $lineCount = 0
    foreach ($line in [IO.File]::ReadLines($log.FullName)) {
        $lineCount++
        $lower = $line.ToLowerInvariant()
        $matches = $false
        foreach ($token in $tokens) {
            if ($lower.Contains($token)) {
                $matches = $true
                break
            }
        }
        if ($matches) {
            $relevant.Add((Sanitize-Text $line $ProjectRoot $UserProfile $Username))
        }
    }
    $logMetadata += [pscustomobject][ordered]@{
        name = $log.Name
        sha256 = Get-Sha256 $log.FullName
        size_bytes = [int64]$log.Length
        line_count = $lineCount
    }
}

if ($relevant.Count -gt 80) {
    $relevantTail = @($relevant.GetRange($relevant.Count - 80, 80))
}
else {
    $relevantTail = @($relevant)
}

New-Item -ItemType Directory -Path $ReturnDir -Force | Out-Null
$stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")
$ReturnPath = Join-Path $ReturnDir "P5A_D2S2_A2_SANDBOX_STATE_RETURN_$stamp.json"

$return = [ordered]@{
    schema = "G2E-P5A-D2S2-A2-SANDBOX-STATE-RETURN-v1"
    created_utc = [DateTime]::UtcNow.ToString("o")
    evidence_return_only = $true
    bound_setup_evidence_return_sha256 = $BoundSetupEvidenceReturnSha256.ToLowerInvariant()
    sandbox_dir_exists = $true
    sandbox_entries = $entries
    setup_error = $setupError
    setup_marker = $setupMarker
    sandbox_logs = $logMetadata
    setup_relevant_log_tail_sanitized = $relevantTail
    turn_start_request_sent = $false
    scientific_attempt_consumed = $false
}

Write-JsonFile $ReturnPath $return

Write-Host ""
Write-Host "=== D2-S2 A2 SANDBOX STATE RETURN READY ==="
Write-Host "RETURN JSON : $ReturnPath"
Write-Host "TURN START  : FALSE"
Write-Host "ATTEMPT USED: FALSE"
