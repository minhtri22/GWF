param(
    [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"

$Version = "0.153.4"
$PackageName = "codex-package-x86_64-pc-windows-msvc.tar.gz"
$PackageSha256 = "A6EF3442CB12766A88B39311D79244289E4F9763E2C53FF4FBEB C2CB653CC5F3".Replace(" ","")
$ExpectedCodexSha256 = "444A3F0008050605CAE73CD9B7A2DCAC61294062DFAAB56DD20430FD6498518B"
$ExpectedHelperSha256 = "0C3EEB7CEE8D2BC4C8644DEF3C818E8B06760979572DCEDC919C38D0F38F64C4"
$Url = "https://github.com/openai/codex/releases/download/rust-v$Version/$PackageName"

if ([string]::IsNullOrWhiteSpace($OutDir)) {
    $OutDir = Join-Path $PSScriptRoot "..\..\g2e\.local\codex-official-0.153.4"
}
$OutDir = [System.IO.Path]::GetFullPath($OutDir)
$DownloadDir = Join-Path $OutDir "_download"
$ExtractDir = Join-Path $OutDir "package"
$Archive = Join-Path $DownloadDir $PackageName

if (Test-Path -LiteralPath $OutDir) {
    throw "OUTDIR_ALREADY_EXISTS_FAIL_CLOSED:$OutDir"
}

New-Item -ItemType Directory -Path $DownloadDir,$ExtractDir -Force | Out-Null

Invoke-WebRequest -Uri $Url -OutFile $Archive -UseBasicParsing
$ObservedPackageSha = (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToUpperInvariant()
if ($ObservedPackageSha -ne $PackageSha256) {
    throw "PACKAGE_SHA256_MISMATCH:observed=$ObservedPackageSha expected=$PackageSha256"
}

$Tar = (Get-Command tar.exe -ErrorAction Stop).Source
& $Tar -xzf $Archive -C $ExtractDir
if ($LASTEXITCODE -ne 0) {
    throw "PACKAGE_EXTRACTION_FAILED:$LASTEXITCODE"
}

$CodexCandidates = @(Get-ChildItem -LiteralPath $ExtractDir -Recurse -File -Filter "codex.exe")
$HelperCandidates = @(Get-ChildItem -LiteralPath $ExtractDir -Recurse -File -Filter "codex-windows-sandbox-setup.exe")

if ($CodexCandidates.Count -ne 1) {
    throw "CODEX_CARDINALITY_INVALID:$($CodexCandidates.Count)"
}
if ($HelperCandidates.Count -ne 1) {
    throw "HELPER_CARDINALITY_INVALID:$($HelperCandidates.Count)"
}

$Codex = $CodexCandidates[0].FullName
$Helper = $HelperCandidates[0].FullName
$ObservedCodexSha = (Get-FileHash -LiteralPath $Codex -Algorithm SHA256).Hash.ToUpperInvariant()
$ObservedHelperSha = (Get-FileHash -LiteralPath $Helper -Algorithm SHA256).Hash.ToUpperInvariant()

if ($ObservedCodexSha -ne $ExpectedCodexSha256) {
    throw "CODEX_SHA256_MISMATCH:observed=$ObservedCodexSha expected=$ExpectedCodexSha256"
}
if ($ObservedHelperSha -ne $ExpectedHelperSha256) {
    throw "HELPER_SHA256_MISMATCH:observed=$ObservedHelperSha expected=$ExpectedHelperSha256"
}

$VersionOutput = (& $Codex --version 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "CODEX_VERSION_COMMAND_FAILED:$LASTEXITCODE"
}
if ($VersionOutput -notmatch "(^|\s)0\.153\.4($|\s)") {
    throw "CODEX_VERSION_MISMATCH:$VersionOutput"
}

$Report = [ordered]@{
    schema = "G2E-P5A-CGW-OFFICIAL-CODEX-01534-PACKAGE-QUALIFICATION-v1"
    status = "PASS"
    version = $Version
    source_url = $Url
    package = [ordered]@{
        name = $PackageName
        sha256 = $ObservedPackageSha.ToLowerInvariant()
    }
    codex = [ordered]@{
        path = $Codex
        sha256 = $ObservedCodexSha.ToLowerInvariant()
        version_output = $VersionOutput
    }
    sandbox_helper = [ordered]@{
        path = $Helper
        sha256 = $ObservedHelperSha.ToLowerInvariant()
    }
    firewall = [ordered]@{
        model_turn = $false
        browser_submission = $false
        mcp_invocation = $false
        sandbox_setup = $false
        attempt_consumed = $false
    }
}
$ReportPath = Join-Path $OutDir "QUALIFICATION_REPORT.json"
$Report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
$Report | ConvertTo-Json -Depth 8
