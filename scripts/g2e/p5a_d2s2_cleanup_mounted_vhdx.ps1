param(
    [string]$ProjectRoot = "",
    [switch]$PlanOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Write-JsonFile([string]$Path, $Object) {
    $json = $Object | ConvertTo-Json -Depth 12
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

$Targets = @(
    [pscustomobject]@{
        id = "PREDECESSOR"
        relative_path = "g2e\.local\P5A-D2S2\volume\P5A-D2S2-TASK.vhdx"
    },
    [pscustomobject]@{
        id = "A1"
        relative_path = "g2e\.local\P5A-D2S2-A1\volume\P5A-D2S2-A1-TASK.vhdx"
    },
    [pscustomobject]@{
        id = "A2"
        relative_path = "g2e\.local\P5A-D2S2-A2\volume\P5A-D2S2-A2-TASK.vhdx"
    }
)

if ($PlanOnly) {
    Write-Host "D2-S2 VHDX CLEANUP PLAN"
    foreach ($target in $Targets) {
        Write-Host "$($target.id): $(Join-Path $ProjectRoot $target.relative_path)"
    }
    Write-Host "PLAN_ONLY_PASS"
    exit 0
}

$ThisScript = $MyInvocation.MyCommand.Path
$CleanupRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S2-CLEANUP"
$ReportDir = Join-Path $CleanupRoot "report"

if (-not (Test-IsAdministrator)) {
    Write-Host "Administrator elevation is required to dismount D2-S2 VHDX images."
    Write-Host "A UAC prompt will open. No Codex/App Server/model turn is executed."

    $args = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $ThisScript,
        "-ProjectRoot", $ProjectRoot
    )

    $p = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $args -Wait -PassThru

    if (Test-Path -LiteralPath $ReportDir -PathType Container) {
        $latest = Get-ChildItem -LiteralPath $ReportDir -Filter "P5A_D2S2_VHDX_CLEANUP_*.json" -File |
            Sort-Object LastWriteTimeUtc -Descending |
            Select-Object -First 1
        if ($null -ne $latest) {
            Write-Host "REPORT JSON : $($latest.FullName)"
        }
    }

    exit $p.ExitCode
}

New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
$stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")
$ReportPath = Join-Path $ReportDir "P5A_D2S2_VHDX_CLEANUP_$stamp.json"

$records = @()
$overallPass = $true

foreach ($target in $Targets) {
    $path = Join-Path $ProjectRoot $target.relative_path
    $record = [ordered]@{
        id = $target.id
        vhdx_path = $path
        file_exists = (Test-Path -LiteralPath $path -PathType Leaf)
        attached_before = $null
        action = "NOT_PRESENT"
        attached_after = $null
        cleanup_error = $null
    }

    if (-not $record.file_exists) {
        $records += [pscustomobject]$record
        continue
    }

    try {
        $imageBefore = Get-DiskImage -ImagePath $path -ErrorAction Stop
        $record.attached_before = [bool]$imageBefore.Attached

        if ($imageBefore.Attached) {
            Dismount-DiskImage -ImagePath $path -ErrorAction Stop | Out-Null
            $record.action = "DISMOUNTED"
        }
        else {
            $record.action = "ALREADY_DETACHED"
        }

        Start-Sleep -Milliseconds 250
        $imageAfter = Get-DiskImage -ImagePath $path -ErrorAction Stop
        $record.attached_after = [bool]$imageAfter.Attached

        if ($imageAfter.Attached) {
            $overallPass = $false
            $record.cleanup_error = "ATTACHED_AFTER_CLEANUP"
        }
    }
    catch {
        $overallPass = $false
        $record.action = "CLEANUP_FAILED"
        $record.cleanup_error = $_.Exception.Message
    }

    $records += [pscustomobject]$record
}

$report = [ordered]@{
    schema = "G2E-P5A-D2S2-VHDX-CLEANUP-v1"
    created_utc = [DateTime]::UtcNow.ToString("o")
    project_root = $ProjectRoot
    evidence_preserved = $true
    vhdx_deleted = $false
    turn_start_request_sent = $false
    scientific_attempt_consumed = $false
    targets = $records
    status = if ($overallPass) { "CLEANUP_PASS" } else { "CLEANUP_BLOCKED" }
}

Write-JsonFile $ReportPath $report

Write-Host ""
Write-Host "=== D2-S2 VHDX CLEANUP COMPLETE ==="
Write-Host "STATUS      : $($report.status)"
foreach ($record in $records) {
    Write-Host ("{0,-11}: exists={1} before={2} action={3} after={4}" -f
        $record.id,
        $record.file_exists,
        $record.attached_before,
        $record.action,
        $record.attached_after)
}
Write-Host "REPORT JSON : $ReportPath"
Write-Host "VHDX DELETE : FALSE"
Write-Host "TURN START  : FALSE"
Write-Host "ATTEMPT USED: FALSE"

if (-not $overallPass) {
    exit 1
}
exit 0
