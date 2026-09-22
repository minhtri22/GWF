param(
    [string]$ProjectRoot = "",
    [string]$PythonExe = "",
    [switch]$InfrastructureSelfTest
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
else {
    $ProjectRoot = (Resolve-Path $ProjectRoot).Path
}

if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    $PythonExe = (Get-Command python -ErrorAction Stop).Source
}

$Extractor = Join-Path $ProjectRoot "scripts\g2e\p5a_d2s4_recover_persisted_turn_error.py"
$ScienceRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S4-SCIENCE-001"
$CodexHome = Join-Path $ScienceRoot "codex-home"
$OutputRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S4-PERSISTED-ERROR-RECOVERY"
$ZipPath = Join-Path $ProjectRoot "g2e\.local\P5A-D2S4-PERSISTED-ERROR-RECOVERY.zip"
$LockPath = Join-Path $ProjectRoot "g2e\docs\P5A_D2S4_PERSISTED_TURN_ERROR_RECOVERY_LOCK.json"

if ($InfrastructureSelfTest) {
    if (-not (Test-Path -LiteralPath $Extractor -PathType Leaf)) {
        throw "RECOVERY_EXTRACTOR_MISSING"
    }
    $source = Get-Content -LiteralPath $Extractor -Raw
    foreach ($forbidden in @(
        "subprocess.",
        "requests.",
        "urllib.request",
        "socket.",
        "Start-Process",
        "turn/start",
        "thread/start"
    )) {
        if ($source.Contains($forbidden)) {
            throw "RECOVERY_EXTRACTOR_FORBIDDEN_TOKEN:$forbidden"
        }
    }
    Write-Host "D2S4_PERSISTED_ERROR_RECOVERY_INFRASTRUCTURE_SELFTEST_PASS"
    exit 0
}

if (-not (Test-Path -LiteralPath $LockPath -PathType Leaf)) {
    throw "RECOVERY_LOCK_MISSING:$LockPath"
}
$Lock = Get-Content -LiteralPath $LockPath -Raw | ConvertFrom-Json
if ($Lock.qualified -ne $true) {
    throw "RECOVERY_LOCK_NOT_QUALIFIED"
}

$head = (& git -C $ProjectRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw "GIT_HEAD_READ_FAILED" }

$extractorBlob = (& git -C $ProjectRoot rev-parse "HEAD:scripts/g2e/p5a_d2s4_recover_persisted_turn_error.py").Trim()
if ($LASTEXITCODE -ne 0) { throw "EXTRACTOR_BLOB_READ_FAILED" }
$selfBlob = (& git -C $ProjectRoot rev-parse "HEAD:scripts/g2e/p5a_d2s4_collect_persisted_turn_error.ps1").Trim()
if ($LASTEXITCODE -ne 0) { throw "WRAPPER_BLOB_READ_FAILED" }

if ($extractorBlob -ne [string]$Lock.extractor_blob) {
    throw "EXTRACTOR_BLOB_DRIFT"
}
if ($selfBlob -ne [string]$Lock.wrapper_blob) {
    throw "WRAPPER_BLOB_DRIFT"
}

if (-not (Test-Path -LiteralPath $CodexHome -PathType Container)) {
    throw "SCIENCE001_CODEX_HOME_MISSING:$CodexHome"
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw "RECOVERY_OUTPUT_ROOT_ALREADY_EXISTS:$OutputRoot"
}
if (Test-Path -LiteralPath $ZipPath) {
    throw "RECOVERY_ZIP_ALREADY_EXISTS:$ZipPath"
}

& $PythonExe $Extractor --codex-home $CodexHome --output-dir $OutputRoot
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    throw "RECOVERY_EXTRACTOR_EXIT_$exitCode"
}

$RecoveryJson = Join-Path $OutputRoot "P5A_D2S4_PERSISTED_TURN_ERROR_RECOVERY.json"
if (-not (Test-Path -LiteralPath $RecoveryJson -PathType Leaf)) {
    throw "RECOVERY_JSON_MISSING"
}

Compress-Archive -Path (Join-Path $OutputRoot "*") -DestinationPath $ZipPath -CompressionLevel Optimal

Write-Host ""
Write-Host "=== D2-S4 PERSISTED TURN-ERROR RECOVERY READY ==="
Write-Host "HEAD       : $head"
Write-Host "OUTPUT     : $RecoveryJson"
Write-Host "ZIP        : $ZipPath"
Write-Host "CODEX      : NOT STARTED"
Write-Host "RPC        : NONE"
Write-Host "NETWORK    : NONE"
Write-Host "VHDX       : NOT MOUNTED"
Write-Host "RETRY      : FALSE"
