param(
    [string]$ProjectRoot = "",
    [switch]$ResolverSelfTest
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedCodexSha256 = "A337B7433EBB351C0165DD074CF2500A20FCA9CEAB3680A71DF593653BF70DC8"
$HelperName = "codex-windows-sandbox-setup.exe"
$Markers = @("interactive-provision", "full", "provision-only", "read-acls-only")

Add-Type -TypeDefinition @"
using System;
using System.IO;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
using System.Text;

public static class G2EFinalPath {
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern uint GetFinalPathNameByHandleW(
        SafeFileHandle hFile,
        StringBuilder lpszFilePath,
        uint cchFilePath,
        uint dwFlags
    );

    public static string Resolve(string path) {
        using (var stream = new FileStream(
            path,
            FileMode.Open,
            FileAccess.Read,
            FileShare.ReadWrite | FileShare.Delete
        )) {
            var sb = new StringBuilder(32768);
            uint len = GetFinalPathNameByHandleW(stream.SafeFileHandle, sb, (uint)sb.Capacity, 0);
            if (len == 0 || len >= sb.Capacity) {
                throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            }
            string value = sb.ToString();
            if (value.StartsWith(@"\\?\UNC\", StringComparison.OrdinalIgnoreCase)) {
                return @"\\" + value.Substring(8);
            }
            if (value.StartsWith(@"\\?\", StringComparison.OrdinalIgnoreCase)) {
                return value.Substring(4);
            }
            return value;
        }
    }
}
"@

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Sanitize-Path([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $Path }
    $userProfile = [Environment]::GetFolderPath("UserProfile")
    if (-not [string]::IsNullOrWhiteSpace($userProfile) -and
        $Path.StartsWith($userProfile, [StringComparison]::OrdinalIgnoreCase)) {
        return "<USERPROFILE>" + $Path.Substring($userProfile.Length)
    }
    return $Path
}

function Get-ResolverCandidates([string]$ExePath) {
    $records = New-Object System.Collections.Generic.List[object]
    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    $order = 0

    function Add-CandidatesForExe([string]$SourceExe, [string]$SourceKind) {
        $dir = Split-Path -Parent $SourceExe
        if ([string]::IsNullOrWhiteSpace($dir)) { return }

        $candidateSpecs = New-Object System.Collections.Generic.List[object]
        $candidateSpecs.Add([pscustomobject]@{
            type = "$SourceKind-direct-sibling"
            path = Join-Path $dir $HelperName
        })

        $dirItem = Get-Item -LiteralPath $dir -ErrorAction Stop
        if ($dirItem.Name -ieq "bin") {
            $packageDir = Split-Path -Parent $dir
            if (-not [string]::IsNullOrWhiteSpace($packageDir)) {
                $candidateSpecs.Add([pscustomobject]@{
                    type = "$SourceKind-package-resources"
                    path = Join-Path (Join-Path $packageDir "codex-resources") $HelperName
                })
            }
        }

        $candidateSpecs.Add([pscustomobject]@{
            type = "$SourceKind-exe-dir-resources"
            path = Join-Path (Join-Path $dir "codex-resources") $HelperName
        })

        foreach ($spec in $candidateSpecs) {
            $full = [IO.Path]::GetFullPath([string]$spec.path)
            if ($seen.Add($full)) {
                $script:g2eResolverOrder++
                $records.Add([pscustomobject]@{
                    order = $script:g2eResolverOrder
                    candidate_type = [string]$spec.type
                    path = $full
                    exists = (Test-Path -LiteralPath $full -PathType Leaf)
                })
            }
        }
    }

    $script:g2eResolverOrder = 0
    Add-CandidatesForExe $ExePath "lexical"

    try {
        $canonicalExe = [G2EFinalPath]::Resolve($ExePath)
        if (-not [string]::Equals(
            [IO.Path]::GetFullPath($canonicalExe),
            [IO.Path]::GetFullPath($ExePath),
            [StringComparison]::OrdinalIgnoreCase
        )) {
            Add-CandidatesForExe $canonicalExe "canonical"
        }
    }
    catch {
        $canonicalExe = $null
    }

    return [pscustomobject]@{
        canonical_exe = $canonicalExe
        candidates = $records.ToArray()
    }
}

function Get-BinaryRecord(
    [string]$Path,
    [string]$Role,
    [Nullable[int]]$ResolverOrder,
    [string]$CandidateType
) {
    $record = [ordered]@{
        role = $Role
        resolver_order = $ResolverOrder
        candidate_type = $CandidateType
        path_sanitized = Sanitize-Path $Path
        exists = (Test-Path -LiteralPath $Path -PathType Leaf)
        size_bytes = $null
        sha256 = $null
        file_version = $null
        product_version = $null
        markers = [ordered]@{}
    }

    foreach ($marker in $Markers) {
        $record.markers[$marker] = $false
    }

    if (-not $record.exists) {
        return [pscustomobject]$record
    }

    $item = Get-Item -LiteralPath $Path
    $record.size_bytes = [int64]$item.Length
    $record.sha256 = Get-Sha256 $Path
    $record.file_version = $item.VersionInfo.FileVersion
    $record.product_version = $item.VersionInfo.ProductVersion

    $ascii = [Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes($Path))
    foreach ($marker in $Markers) {
        $record.markers[$marker] = $ascii.Contains($marker)
    }

    return [pscustomobject]$record
}

function Invoke-ResolverSelfTest {
    $root = Join-Path ([IO.Path]::GetTempPath()) ("g2e-resolver-" + [Guid]::NewGuid().ToString("N"))
    try {
        $package = Join-Path $root "package"
        $bin = Join-Path $package "bin"
        $resources = Join-Path $package "codex-resources"
        New-Item -ItemType Directory -Path $bin -Force | Out-Null
        New-Item -ItemType Directory -Path $resources -Force | Out-Null

        $exe = Join-Path $bin "codex.exe"
        [IO.File]::WriteAllText($exe, "codex", [Text.UTF8Encoding]::new($false))
        $direct = Join-Path $bin $HelperName
        $packageHelper = Join-Path $resources $HelperName

        [IO.File]::WriteAllText($packageHelper, "package-helper", [Text.UTF8Encoding]::new($false))
        $r1 = Get-ResolverCandidates $exe
        $first1 = @($r1.candidates | Where-Object { $_.exists } | Sort-Object order)[0]
        if ($first1.candidate_type -ne "lexical-package-resources") {
            throw "RESOLVER_SELFTEST_PACKAGE_PRIORITY_FAILED:$($first1.candidate_type)"
        }

        [IO.File]::WriteAllText($direct, "direct-helper", [Text.UTF8Encoding]::new($false))
        $r2 = Get-ResolverCandidates $exe
        $first2 = @($r2.candidates | Where-Object { $_.exists } | Sort-Object order)[0]
        if ($first2.candidate_type -ne "lexical-direct-sibling") {
            throw "RESOLVER_SELFTEST_DIRECT_PRIORITY_FAILED:$($first2.candidate_type)"
        }

        Write-Host "RESOLVER_SELFTEST_PASS"
    }
    finally {
        if (Test-Path -LiteralPath $root) {
            Remove-Item -LiteralPath $root -Recurse -Force
        }
    }
}

if ($ResolverSelfTest) {
    Invoke-ResolverSelfTest
    exit 0
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
else {
    $ProjectRoot = (Resolve-Path $ProjectRoot).Path
}

$CodexExe = Join-Path $env:LOCALAPPDATA "Programs\OpenAI\Codex\bin\codex.exe"
if (-not (Test-Path -LiteralPath $CodexExe -PathType Leaf)) {
    throw "CODEX_EXE_MISSING:$CodexExe"
}

$codexHash = Get-Sha256 $CodexExe
if ($codexHash.ToUpperInvariant() -ne $ExpectedCodexSha256) {
    throw "CODEX_EXE_HASH_MISMATCH:$codexHash"
}

$resolution = Get-ResolverCandidates $CodexExe
$candidateRecords = @()
foreach ($c in @($resolution.candidates | Sort-Object order)) {
    $candidateRecords += Get-BinaryRecord -Path $c.path -Role "setup-helper-candidate" -ResolverOrder ([int]$c.order) -CandidateType ([string]$c.candidate_type)
}

$existingCandidates = @($candidateRecords | Where-Object { $_.exists } | Sort-Object resolver_order)

$selected = $null
if ($existingCandidates.Count -gt 0) {
    $selected = $existingCandidates[0]
}

$codexRecord = Get-BinaryRecord -Path $CodexExe -Role "codex-executable" -ResolverOrder $null -CandidateType $null

$A2Root = Join-Path $ProjectRoot "g2e\.local\P5A-D2S2-A2"
$ReturnDir = Join-Path $A2Root "return"
New-Item -ItemType Directory -Path $ReturnDir -Force | Out-Null
$stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")
$ReturnPath = Join-Path $ReturnDir "P5A_D2S2_A2_BINARY_COMPONENT_LINEAGE_$stamp.json"

$return = [ordered]@{
    schema = "G2E-P5A-D2S2-A2-BINARY-COMPONENT-LINEAGE-v1"
    created_utc = [DateTime]::UtcNow.ToString("o")
    evidence_return_only = $true
    frozen_codex_commit = "3d2ee51ca2d5db578f328aa75e20aa22c0197c9a"
    expected_codex_sha256 = $ExpectedCodexSha256.ToLowerInvariant()
    codex = $codexRecord
    canonical_exe_path_sanitized = Sanitize-Path $resolution.canonical_exe
    helper_candidates = $candidateRecords
    selected_helper = $selected
    existing_helper_candidate_count = $existingCandidates.Count
    multiple_existing_helper_candidates = ($existingCandidates.Count -gt 1)
    selected_helper_exists = ($null -ne $selected)
    turn_start_request_sent = $false
    scientific_attempt_consumed = $false
}

$json = $return | ConvertTo-Json -Depth 16
[IO.File]::WriteAllText(
    $ReturnPath,
    $json + [Environment]::NewLine,
    [Text.UTF8Encoding]::new($false)
)

Write-Host ""
Write-Host "=== D2-S2 A2 BINARY COMPONENT LINEAGE READY ==="
Write-Host "CODEX SHA   : $codexHash"
Write-Host "HELPERS     : $($existingCandidates.Count)"
Write-Host "SELECTED    : $(if ($null -eq $selected) { '<none>' } else { $selected.path_sanitized })"
Write-Host "RETURN JSON : $ReturnPath"
Write-Host "TURN START  : FALSE"
Write-Host "ATTEMPT USED: FALSE"
