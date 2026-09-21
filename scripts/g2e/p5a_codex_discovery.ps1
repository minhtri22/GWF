param(
    [string]$CodexCommand = "codex",
    [string]$Output = "P5A_CODEX_DISCOVERY.json",
    [string]$WorkDir = ".p5a-codex-discovery",
    [double]$TimeoutSeconds = 12
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$probe = Join-Path $repoRoot "scripts\g2e\p5a_codex_discovery.py"

if (-not (Test-Path $probe)) {
    throw "P5A discovery probe not found: $probe"
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "python is required to run the P5A discovery probe"
}

& $python.Source $probe --codex-command $CodexCommand --output $Output --work-dir $WorkDir --timeout $TimeoutSeconds

$exit = $LASTEXITCODE
if ($exit -ne 0) {
    Write-Host "P5A discovery did not qualify D1. Inspect $Output" -ForegroundColor Yellow
    exit $exit
}

Write-Host "P5A D1 discovery bundle written to $Output" -ForegroundColor Green
