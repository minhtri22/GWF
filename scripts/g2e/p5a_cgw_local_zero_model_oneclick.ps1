param(
    [string]$OutputRoot = "",
    [string]$BridgeHome = "",
    [string]$CodexHome = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Probe = Join-Path $RepoRoot "scripts\g2e\p5a_cgw_bridge_qualification.py"

if (-not $OutputRoot) {
    $OutputRoot = Join-Path $RepoRoot "g2e\.local\P5A-CGW-ZERO-MODEL-001"
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw "P5A_CGW_ZERO_MODEL_ROOT_ALREADY_EXISTS:$OutputRoot"
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
if (-not (Test-Path -LiteralPath $Probe)) { throw "P5A_CGW_PROBE_NOT_FOUND:$Probe" }

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) { throw "PYTHON_NOT_FOUND" }

# Read locally only to discover the loopback health endpoint. The raw config is never copied.
$BridgeObject = Get-Content -LiteralPath $BridgeConfig -Raw | ConvertFrom-Json
if ([string]$BridgeObject.host -ne "127.0.0.1") { throw "CGW_NOT_LOOPBACK" }
$Port = [int]$BridgeObject.port
if ($Port -lt 1 -or $Port -gt 65535) { throw "CGW_INVALID_PORT" }

$HealthPath = Join-Path $OutputRoot "CGW_HEALTH_SAFE.json"
$HealthUri = "http://127.0.0.1:$Port/healthz"
try {
    $Health = Invoke-RestMethod -Method Get -Uri $HealthUri -TimeoutSec 3
} catch {
    throw "CGW_HEALTH_UNAVAILABLE:$($_.Exception.Message)"
}
$Health | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $HealthPath -Encoding UTF8

# Prefer the installed launcher recorded by the official launcher installer.
$CgwBinary = $null
$InstallRegistry = "HKCU:\Software\d1a6026a-6210-588e-9a2b-da3936f94e02"
try {
    $InstallLocation = [string](Get-ItemPropertyValue -LiteralPath $InstallRegistry -Name "InstallLocation")
    $Candidate = Join-Path $InstallLocation "Codex Web GPT.exe"
    if (Test-Path -LiteralPath $Candidate) { $CgwBinary = $Candidate }
} catch {}

if (-not $CgwBinary) {
    $RuntimeCommand = @($BridgeObject.runtimeCommand)
    if ($RuntimeCommand.Count -lt 1) { throw "CGW_RUNTIME_COMMAND_MISSING" }
    $Candidate = [string]$RuntimeCommand[0]
    if (-not (Test-Path -LiteralPath $Candidate)) { throw "CGW_RUNTIME_BINARY_NOT_FOUND:$Candidate" }
    $CgwBinary = $Candidate
}

$CodexCommand = Get-Command codex -ErrorAction SilentlyContinue
if (-not $CodexCommand) { throw "CODEX_COMMAND_NOT_FOUND" }
$CodexCommandPath = [string]$CodexCommand.Source
if (-not (Test-Path -LiteralPath $CodexCommandPath)) { throw "CODEX_COMMAND_PATH_NOT_FOUND:$CodexCommandPath" }

$ReportPath = Join-Path $OutputRoot "P5A_CGW_LOCAL_ZERO_MODEL_ADMISSION.json"

# CRITICAL ZERO-MODEL FIREWALL:
# - only /healthz was called;
# - no /v1/models;
# - no /v1/responses;
# - no Codex thread/start or turn/start;
# - no browser submission;
# - no MCP tool invocation.
$ProbeArgs = @(
    $Probe,
    "--local-output", $ReportPath,
    "--cgw-config", $BridgeConfig,
    "--codex-config", $CodexConfig,
    "--health-json", $HealthPath,
    "--cgw-binary", $CgwBinary,
    "--codex-command-path", $CodexCommandPath
)
& $Python.Source @ProbeArgs

$ExitCode = $LASTEXITCODE
if ($ExitCode -ne 0) {
    Write-Host "P5A-CGW local zero-model admission BLOCKED. Inspect:" -ForegroundColor Yellow
    Write-Host $ReportPath
    exit $ExitCode
}

$Report = Get-Content -LiteralPath $ReportPath -Raw | ConvertFrom-Json
if ([bool]$Report.model_turn_executed) { throw "ZERO_MODEL_FIREWALL_BREACH" }
if ([bool]$Report.responses_endpoint_called) { throw "RESPONSES_ENDPOINT_FIREWALL_BREACH" }
if ([bool]$Report.scientific_attempt_created) { throw "SCIENTIFIC_ATTEMPT_FIREWALL_BREACH" }

Write-Host ""
Write-Host "=== P5A-CGW LOCAL ZERO-MODEL ADMISSION ===" -ForegroundColor Cyan
Write-Host ("STATUS: " + [string]$Report.status)
Write-Host ("MODE: " + [string]$Report.bridge_config.mode)
Write-Host ("CONNECTOR: " + [string]$Report.bridge_config.active_connector)
Write-Host ("ROUTE: " + [string]$Report.codex_route.openai_base_url)
Write-Host ("EVIDENCE_SHA256: " + [string]$Report.evidence_sha256)
Write-Host ("REPORT: " + $ReportPath)
Write-Host "No ChatGPT/Codex model turn was sent." -ForegroundColor Green
