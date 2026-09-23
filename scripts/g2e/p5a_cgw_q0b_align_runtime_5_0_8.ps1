param(
    [string]$OutputRoot = "",
    [string]$BridgeHome = "",
    [string]$CodexHome = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ExpectedSourceVersion = "4.0.7"
$TargetVersion = "5.0.8"
$InstallerScriptUrl = "https://github.com/miuuyy/codex-chatgpt-web/releases/download/v5.0.8/install-launcher.ps1"
$InstallerScriptSha256 = "117ab8e5bfba36d3f611e9294355afe70936a536bf3305d4fe563edab7c40a71"
$InstallerAssetSha256 = "83224d59506462ab2976f437bfaea96b046d4ed55caa7e1cfd6a3d61de0a8ff3"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Admission = Join-Path $RepoRoot "scripts\g2e\p5a_cgw_local_zero_model_oneclick.ps1"

if (-not $OutputRoot) {
    $OutputRoot = Join-Path $RepoRoot "g2e\.local\P5A-CGW-Q0B-ALIGN-001"
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw "P5A_CGW_Q0B_ALIGNMENT_ROOT_ALREADY_EXISTS:$OutputRoot"
}
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

if (-not $BridgeHome) {
    if ($env:CODEX_CHATGPT_WEB_HOME) {
        $BridgeHome = $env:CODEX_CHATGPT_WEB_HOME
    } else {
        $BridgeHome = Join-Path $HOME ".codex-chatgpt-web"
    }
}
if (-not $CodexHome) {
    if ($env:CODEX_HOME) {
        $CodexHome = $env:CODEX_HOME
    } else {
        $CodexHome = Join-Path $HOME ".codex"
    }
}

$BridgeConfig = Join-Path $BridgeHome "config.json"
$CodexConfig = Join-Path $CodexHome "config.toml"
if (-not (Test-Path -LiteralPath $BridgeConfig)) { throw "CGW_CONFIG_NOT_FOUND:$BridgeConfig" }
if (-not (Test-Path -LiteralPath $CodexConfig)) { throw "CODEX_CONFIG_NOT_FOUND:$CodexConfig" }
if (-not (Test-Path -LiteralPath $Admission)) { throw "Q0B_ADMISSION_SCRIPT_NOT_FOUND:$Admission" }

if (Get-Process -Name "Codex Web GPT" -ErrorAction SilentlyContinue) {
    throw "QUIT_CODEX_WEB_GPT_BEFORE_RUNTIME_ALIGNMENT"
}

$PreShaHex = (Get-FileHash -LiteralPath $BridgeConfig -Algorithm SHA256).Hash.ToLowerInvariant()
$Pre = Get-Content -LiteralPath $BridgeConfig -Raw | ConvertFrom-Json

if ([int]$Pre.version -ne 3) { throw "CGW_CONFIG_VERSION_NOT_3" }
if ([string]$Pre.releaseVersion -ne $ExpectedSourceVersion) {
    throw "CGW_ALIGNMENT_SOURCE_VERSION_MISMATCH:$([string]$Pre.releaseVersion)"
}
if ([string]$Pre.host -ne "127.0.0.1") { throw "CGW_ALIGNMENT_HOST_NOT_LOOPBACK" }
if ([string]$Pre.mode -ne "full") { throw "CGW_ALIGNMENT_EXPECTS_FULL_MODE" }
if ([string]$Pre.appName -ne "Codex Native2") { throw "CGW_ALIGNMENT_CONNECTOR_MISMATCH" }
if ([bool]$Pre.autoApproveToolCalls) { throw "CGW_ALIGNMENT_AUTO_APPROVAL_NOT_ALLOWED" }

$PrePort = [int]$Pre.port
$ExpectedRoute = "http://127.0.0.1:$PrePort/v1"
$CodexRawBefore = Get-Content -LiteralPath $CodexConfig -Raw
if ($CodexRawBefore -notmatch [regex]::Escape($ExpectedRoute)) {
    throw "CODEX_ROUTE_NOT_BOUND_TO_PRE_ALIGNMENT_CGW"
}

$Temp = Join-Path ([System.IO.Path]::GetTempPath()) ("g2e-p5a-cgw-align-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $Temp -Force | Out-Null
$InstallerScript = Join-Path $Temp "install-launcher.ps1"

try {
    Invoke-WebRequest -Uri $InstallerScriptUrl -OutFile $InstallerScript -TimeoutSec 120 -UseBasicParsing
    $ObservedInstallerScriptSha = (Get-FileHash -LiteralPath $InstallerScript -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($ObservedInstallerScriptSha -ne $InstallerScriptSha256) {
        throw "PINNED_INSTALLER_SCRIPT_SHA256_MISMATCH"
    }

    $OldVersionEnv = $env:CODEX_WEB_GPT_VERSION
    try {
        $env:CODEX_WEB_GPT_VERSION = $TargetVersion
        $InstallerArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $InstallerScript)
        $InstallerProcess = Start-Process -FilePath "powershell.exe" -ArgumentList $InstallerArgs -Wait -PassThru
        if ($InstallerProcess.ExitCode -ne 0) {
            throw "PINNED_CGW_INSTALLER_FAILED:$($InstallerProcess.ExitCode)"
        }
    } finally {
        if ($null -eq $OldVersionEnv) {
            Remove-Item Env:CODEX_WEB_GPT_VERSION -ErrorAction SilentlyContinue
        } else {
            $env:CODEX_WEB_GPT_VERSION = $OldVersionEnv
        }
    }

    $PostReady = $false
    $Health = $null
    $Post = $null
    for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
        if (Test-Path -LiteralPath $BridgeConfig) {
            try {
                $PostCandidate = Get-Content -LiteralPath $BridgeConfig -Raw | ConvertFrom-Json
                if ([string]$PostCandidate.releaseVersion -eq $TargetVersion) {
                    $HealthUri = "http://127.0.0.1:$([int]$PostCandidate.port)/healthz"
                    $HealthCandidate = Invoke-RestMethod -Method Get -Uri $HealthUri -TimeoutSec 3
                    if (
                        [string]$HealthCandidate.status -eq "ok" -and
                        [string]$HealthCandidate.service -eq "codex-chatgpt-web" -and
                        [string]$HealthCandidate.version -eq $TargetVersion -and
                        [bool]$HealthCandidate.accepting_turns
                    ) {
                        $Post = $PostCandidate
                        $Health = $HealthCandidate
                        $PostReady = $true
                        break
                    }
                }
            } catch {}
        }
        Start-Sleep -Seconds 1
    }
    if (-not $PostReady) { throw "CGW_5_0_8_POST_ALIGNMENT_HEALTH_NOT_READY" }

    if ([string]$Post.host -ne "127.0.0.1") { throw "POST_ALIGNMENT_HOST_CHANGED" }
    if ([string]$Post.mode -ne "full") { throw "POST_ALIGNMENT_MODE_CHANGED" }
    if ([string]$Post.appName -ne "Codex Native2") { throw "POST_ALIGNMENT_CONNECTOR_CHANGED" }
    if ([bool]$Post.autoApproveToolCalls) { throw "POST_ALIGNMENT_AUTO_APPROVAL_CHANGED" }

    $PostPort = [int]$Post.port
    $PostExpectedRoute = "http://127.0.0.1:$PostPort/v1"
    $CodexRawAfter = Get-Content -LiteralPath $CodexConfig -Raw
    if ($CodexRawAfter -notmatch [regex]::Escape($PostExpectedRoute)) {
        throw "CODEX_ROUTE_NOT_BOUND_TO_POST_ALIGNMENT_CGW"
    }

    $PostShaHex = (Get-FileHash -LiteralPath $BridgeConfig -Algorithm SHA256).Hash.ToLowerInvariant()

    $AlignmentReportPath = Join-Path $OutputRoot "P5A_CGW_Q0B_RUNTIME_ALIGNMENT_REPORT.json"
    $AlignmentReport = [ordered]@{
        schema = "G2E-P5A-CGW-Q0B-RUNTIME-ALIGNMENT-v1"
        status = "RUNTIME_ALIGNMENT_PASS_Q0B_RECOLLECTION_REQUIRED"
        source_version = $ExpectedSourceVersion
        target_version = $TargetVersion
        pre_config_sha256 = $PreShaHex
        post_config_sha256 = $PostShaHex
        pre_route = $ExpectedRoute
        post_route = $PostExpectedRoute
        mode = [string]$Post.mode
        connector = [string]$Post.appName
        installer_script_sha256 = $ObservedInstallerScriptSha
        installer_asset_expected_sha256 = $InstallerAssetSha256
        health = [ordered]@{
            status = [string]$Health.status
            service = [string]$Health.service
            version = [string]$Health.version
            accepting_turns = [bool]$Health.accepting_turns
            active_http_turns = [int]$Health.active_http_turns
            active_browser_turns = [int]$Health.active_browser_turns
        }
        model_turn_executed = $false
        responses_endpoint_called = $false
        models_endpoint_called = $false
        scientific_attempt_created = $false
        scientific_attempt_consumed = $false
    }
    $AlignmentReport | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $AlignmentReportPath -Encoding UTF8

    $Q0bRoot = Join-Path $RepoRoot "g2e\.local\P5A-CGW-ZERO-MODEL-Q0B-R2"
    $AdmissionArgs = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $Admission,
        "-OutputRoot", $Q0bRoot,
        "-BridgeHome", $BridgeHome,
        "-CodexHome", $CodexHome
    )
    $AdmissionProcess = Start-Process -FilePath "powershell.exe" -ArgumentList $AdmissionArgs -Wait -PassThru
    if ($AdmissionProcess.ExitCode -ne 0) {
        throw "FRESH_Q0B_COLLECTION_BLOCKED:$($AdmissionProcess.ExitCode)"
    }

    $Q0bReport = Join-Path $Q0bRoot "P5A_CGW_LOCAL_ZERO_MODEL_ADMISSION.json"
    if (-not (Test-Path -LiteralPath $Q0bReport)) { throw "FRESH_Q0B_REPORT_MISSING" }
    $Q0b = Get-Content -LiteralPath $Q0bReport -Raw | ConvertFrom-Json
    if ([string]$Q0b.status -ne "LOCAL_ZERO_MODEL_ADMISSION_PASS") {
        throw "FRESH_Q0B_NOT_PASS:$([string]$Q0b.status)"
    }
    if ([bool]$Q0b.model_turn_executed) { throw "ZERO_MODEL_FIREWALL_BREACH" }
    if ([bool]$Q0b.responses_endpoint_called) { throw "RESPONSES_ENDPOINT_FIREWALL_BREACH" }
    if ([bool]$Q0b.scientific_attempt_created) { throw "SCIENTIFIC_ATTEMPT_FIREWALL_BREACH" }

    Write-Host ""
    Write-Host "=== P5A-CGW Q0b RUNTIME ALIGNMENT ===" -ForegroundColor Cyan
    Write-Host ("ALIGNMENT: " + [string]$AlignmentReport.status)
    Write-Host ("Q0B: " + [string]$Q0b.status)
    Write-Host ("VERSION: " + [string]$Post.releaseVersion)
    Write-Host ("ROUTE: " + [string]$Q0b.codex_route.openai_base_url)
    Write-Host ("ALIGNMENT_REPORT: " + $AlignmentReportPath)
    Write-Host ("Q0B_REPORT: " + $Q0bReport)
    Write-Host "No ChatGPT/Codex model turn was sent." -ForegroundColor Green
} finally {
    Remove-Item -LiteralPath $Temp -Recurse -Force -ErrorAction SilentlyContinue
}
