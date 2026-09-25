param(
    [int]$TimeoutSeconds = 180
)

$ErrorActionPreference = "Stop"

$Repo = "D:\WORK\RESEARCH\4.GWF"
$Codex = Join-Path $Repo "g2e\.local\codex-official-0.153.4\package\bin\codex.exe"
$BridgeHome = "$env:USERPROFILE\.codex-chatgpt-web-dev\core-home"
$LauncherData = "$env:USERPROFILE\.codex-chatgpt-web-dev"
$Smoke = Join-Path $Repo "scripts\g2e\g2e_product_smoke.py"

Set-Location $Repo

Write-Host ""
Write-Host "=== G2E PRODUCT SMOKE ===" -ForegroundColor Cyan
Write-Host "Mode: PRODUCT"
Write-Host "Goal: Codex -> CGW -> ChatGPT Web -> tool -> result.json"
Write-Host ""

$Args = @(
    $Smoke,
    "--repo", $Repo,
    "--codex-exe", $Codex,
    "--bridge-home", $BridgeHome,
    "--launcher-data", $LauncherData,
    "--timeout", "$TimeoutSeconds"
)

& python @Args

if ($LASTEXITCODE -ne 0) {
    throw "G2E_PRODUCT_SMOKE_FAIL"
}

Write-Host ""
Write-Host "G2E_PRODUCT_SMOKE_PASS" -ForegroundColor Green
