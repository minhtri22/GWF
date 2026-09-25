param(
    [string]$CgwRepo = "D:\WORK\RESEARCH\codex-chatgpt-web",
    [string]$PortableLauncher = "D:\WORK\RESEARCH\codex-chatgpt-web\launcher\artifacts\codex-web-gpt-4.0.7-win-x64-portable\Codex Web GPT.exe",
    [string]$ExpectedReleaseCommit = "b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494",
    [string]$OfficialInstallerSha256 = "90f47feaa5c6c17612ac9bee6a49b11b65e0241b046b7380e2c5219792a55354",
    [string]$PriorQualifiedLauncherSha256 = "ac152ad499b1f41b2cafe94a3d05f5d4e4d3cd7ddbb417b9c60b118b08bc3cbb"
)

$ErrorActionPreference = "Stop"

function File-Identity([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return [ordered]@{ path = $Path; exists = $false }
    }
    $item = Get-Item -LiteralPath $Path
    $vi = $item.VersionInfo
    return [ordered]@{
        path = $item.FullName
        exists = $true
        sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
        size = [long]$item.Length
        file_version = [string]$vi.FileVersion
        product_version = [string]$vi.ProductVersion
        product_name = [string]$vi.ProductName
        company_name = [string]$vi.CompanyName
        creation_time_utc = $item.CreationTimeUtc.ToString("o")
        last_write_time_utc = $item.LastWriteTimeUtc.ToString("o")
    }
}

$result = [ordered]@{
    schema = "G2E-P5A-CGW-FX001-RP-L2-v1"
    zero_science = $true
    process_launch = $false
    http_request = $false
    download = $false
    install_or_extract = $false
    responses_request = $false
    model_execution = $false
    browser_submission = $false
    mcp_invocation = $false
    source = [ordered]@{}
    portable_launcher = $null
    local_release_installer = $null
    registered_launcher = $null
    comparisons = [ordered]@{}
    classification = "UNCLASSIFIED"
}

if (Test-Path -LiteralPath (Join-Path $CgwRepo ".git")) {
    $head = (& git -C $CgwRepo rev-parse HEAD).Trim()
    $branch = (& git -C $CgwRepo branch --show-current).Trim()
    $statusLines = @(& git -C $CgwRepo status --porcelain=v1)
    $tagCommit = $null
    try {
        $tagCommit = (& git -C $CgwRepo rev-list -n 1 v4.0.7 2>$null).Trim()
    } catch {}

    $result.source = [ordered]@{
        repo = $CgwRepo
        exists = $true
        head = $head
        branch = $branch
        dirty = ($statusLines.Count -gt 0)
        dirty_entry_count = $statusLines.Count
        v4_0_7_tag_commit = $tagCommit
        head_matches_release_commit = ($head -eq $ExpectedReleaseCommit)
        tag_matches_release_commit = ($tagCommit -eq $ExpectedReleaseCommit)
    }
} else {
    $result.source = [ordered]@{ repo = $CgwRepo; exists = $false }
}

$result.portable_launcher = File-Identity $PortableLauncher

$artifactDir = Join-Path $CgwRepo "launcher\artifacts"
$installerPath = Join-Path $artifactDir "codex-web-gpt-4.0.7-win-x64.exe"
$result.local_release_installer = File-Identity $installerPath

$registryPath = "HKCU:\Software\d1a6026a-6210-588e-9a2b-da3936f94e02"
$installLocation = $null
try {
    $installLocation = (Get-ItemProperty -LiteralPath $registryPath -Name InstallLocation -ErrorAction Stop).InstallLocation
} catch {}

if ($installLocation) {
    $registeredExe = Join-Path ([string]$installLocation) "Codex Web GPT.exe"
    $registered = File-Identity $registeredExe
    $registered.install_location = [string]$installLocation
    $result.registered_launcher = $registered
} else {
    $result.registered_launcher = [ordered]@{
        install_location = $null
        exists = $false
    }
}

$portableSha = if ($result.portable_launcher.exists) { [string]$result.portable_launcher.sha256 } else { $null }
$installerSha = if ($result.local_release_installer.exists) { [string]$result.local_release_installer.sha256 } else { $null }
$registeredSha = if ($result.registered_launcher.exists) { [string]$result.registered_launcher.sha256 } else { $null }

$result.comparisons = [ordered]@{
    portable_matches_prior_qualified = ($portableSha -eq $PriorQualifiedLauncherSha256)
    local_installer_matches_official_release = ($installerSha -eq $OfficialInstallerSha256)
    registered_matches_prior_qualified = ($registeredSha -eq $PriorQualifiedLauncherSha256)
    source_head_matches_release_commit = ($result.source.exists -and $result.source.head_matches_release_commit)
    source_tag_matches_release_commit = ($result.source.exists -and $result.source.tag_matches_release_commit)
    source_tree_clean = ($result.source.exists -and -not $result.source.dirty)
}

if ($result.comparisons.registered_matches_prior_qualified) {
    $result.classification = "PRIOR_QUALIFIED_REGISTERED_LAUNCHER_AVAILABLE"
}
elseif ($result.comparisons.local_installer_matches_official_release) {
    $result.classification = "OFFICIAL_RELEASE_INSTALLER_AVAILABLE_LOCAL"
}
elseif ($result.comparisons.source_head_matches_release_commit -and $result.comparisons.source_tree_clean) {
    $result.classification = "EXACT_RELEASE_SOURCE_TREE_AVAILABLE"
}
elseif ($result.comparisons.source_head_matches_release_commit) {
    $result.classification = "EXACT_RELEASE_HEAD_DIRTY_TREE"
}
else {
    $result.classification = "NO_STRONG_LOCAL_LAUNCHER_PROVENANCE_FOUND"
}

$result | ConvertTo-Json -Depth 12
