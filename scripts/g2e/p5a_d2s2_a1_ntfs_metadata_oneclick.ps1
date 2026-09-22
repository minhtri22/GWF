param(
    [string]$ProjectRoot = "",
    [string]$PythonExe = "",
    [string]$CodexExe = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$StudyId = "p5a-d2s2-isolated-volume-root-read-successor"
$AttemptId = "p5a-d2s2-p5-fx-001-attempt-001"
$ProfileId = "g2e_p5a_d2s2"

$ExpectedInputSha256 = "A176454229FEEF1CE8BD7EAB1EA79FBFEFF07C229C88123EDF862FEA9160EEF6"
$ExpectedTaskSha256  = "4C4ABA6A82D540440DFEF725B2568AFDEF4BE3B26C3E4E84E2B34C54E6DD460E"
$ExpectedCodexSha256 = "A337B7433EBB351C0165DD074CF2500A20FCA9CEAB3680A71DF593653BF70DC8"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}


function Quote-NativeArgument([string]$Value) {
    if ($null -eq $Value -or $Value.Length -eq 0) { return '""' }
    if ($Value -notmatch '[\s"]') { return $Value }
    return '"' + $Value.Replace('"', '\\"') + '"'
}

function Invoke-Git([string]$Root, [string[]]$GitArgs) {
    if ($null -eq $GitArgs -or $GitArgs.Count -eq 0) { throw "GIT_ARGUMENT_VECTOR_EMPTY" }
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "git"
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $allArgs = @("-C", $Root) + $GitArgs
    if ($psi.PSObject.Properties.Name -contains "ArgumentList") {
        foreach ($arg in $allArgs) { [void]$psi.ArgumentList.Add([string]$arg) }
    } else {
        $psi.Arguments = (($allArgs | ForEach-Object { Quote-NativeArgument ([string]$_) }) -join " ")
    }
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    try {
        if (-not $proc.Start()) { throw "GIT_PROCESS_START_FAILED" }
        $stdoutTask = $proc.StandardOutput.ReadToEndAsync()
        $stderrTask = $proc.StandardError.ReadToEndAsync()
        $proc.WaitForExit()
        $stdout = $stdoutTask.Result
        $stderr = $stderrTask.Result
        $code = $proc.ExitCode
    } finally { $proc.Dispose() }
    if ($code -ne 0) {
        throw "GIT_FAILED[$code]: $($GitArgs -join ' ') :: STDOUT=$($stdout.Trim()) :: STDERR=$($stderr.Trim())"
    }
    return $stdout.Trim()
}

function Write-JsonFile([string]$Path, $Object) {
    $json = $Object | ConvertTo-Json -Depth 12
    [IO.File]::WriteAllText($Path, $json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
}

function Write-MarkdownReport([string]$Path, $Report) {
    $lines = @(
        "# G2E P5A D2-S2 One-Click Report",
        "",
        "- status: $($Report.status)",
        "- study_id: $($Report.study_id)",
        "- attempt_id: $($Report.attempt_id)",
        "- source_head: $($Report.source_head)",
        "- qualified_candidate_sha: $($Report.qualified_candidate_sha)",
        "- selected_drive: $($Report.selected_drive)",
        "- volume_root: $($Report.volume_root)",
        "- vhdx_path: $($Report.vhdx_path)",
        "- input_sha256: $($Report.input_sha256)",
        "- task_sha256: $($Report.task_sha256)",
        "- config_sha256: $($Report.config_sha256)",
        "- preturn_gate_pass: $($Report.preturn_gate_pass)",
        "- turn_start_request_sent: false",
        "- scientific_attempt_consumed: false",
        "",
        "## Diagnostic",
        "",
        "$($Report.diagnostic)",
        ""
    )
    [IO.File]::WriteAllLines($Path, $lines, [Text.UTF8Encoding]::new($false))
}

function Get-FirstFreeDriveLetter {
    foreach ($letter in @("R","S","T","U","V","W","X","Y","Z")) {
        if (-not (Test-Path "$($letter):\")) {
            return $letter
        }
    }
    throw "NO_FREE_DRIVE_LETTER_R_TO_Z"
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

if ([string]::IsNullOrWhiteSpace($CodexExe)) {
    $CodexExe = Join-Path $env:LOCALAPPDATA "Programs\OpenAI\Codex\bin\codex.exe"
}

$ThisScript = $MyInvocation.MyCommand.Path

if (-not (Test-IsAdministrator)) {
    Write-Host "Administrator elevation is required for isolated VHDX creation."
    Write-Host "A UAC prompt will open. No model turn is executed by this script."

    $elevatedArgs = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $ThisScript,
        "-ProjectRoot", $ProjectRoot,
        "-PythonExe", $PythonExe,
        "-CodexExe", $CodexExe
    )
    $p = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $elevatedArgs -Wait -PassThru
    exit $p.ExitCode
}

Set-Location $ProjectRoot

$LockPath = Join-Path $ProjectRoot "g2e\docs\P5A_D2S2_A1_ONECLICK_LOCK.json"
if (-not (Test-Path $LockPath)) {
    throw "QUALIFICATION_LOCK_MISSING:$LockPath"
}
$Lock = Get-Content -LiteralPath $LockPath -Raw | ConvertFrom-Json
if ($Lock.qualified -ne $true) {
    throw "ONECLICK_NOT_QUALIFIED"
}

$Dirty = Invoke-Git -Root $ProjectRoot -GitArgs @("status","--porcelain")
if ($Dirty) {
    Write-Host $Dirty
    throw "SOURCE_WORKTREE_DIRTY"
}
Invoke-Git -Root $ProjectRoot -GitArgs @("fetch","--prune","origin","feature/g2e-framework") | Out-Null
$RemoteHead = (Invoke-Git -Root $ProjectRoot -GitArgs @("rev-parse","origin/feature/g2e-framework")).Trim()
Invoke-Git -Root $ProjectRoot -GitArgs @("switch","--detach","origin/feature/g2e-framework") | Out-Null
$Head = (Invoke-Git -Root $ProjectRoot -GitArgs @("rev-parse","HEAD")).Trim()
if ($Head -ne $RemoteHead) { throw "REMOTE_HEAD_CHECKOUT_MISMATCH:$($Head):$($RemoteHead)" }
if (Invoke-Git -Root $ProjectRoot -GitArgs @("status","--porcelain")) { throw "SOURCE_WORKTREE_DIRTY_AFTER_SWITCH" }
$ScriptBlob = (Invoke-Git -Root $ProjectRoot -GitArgs @("rev-parse","HEAD:scripts/g2e/p5a_d2s2_a1_ntfs_metadata_oneclick.ps1")).Trim()
$PreflightBlob = (Invoke-Git -Root $ProjectRoot -GitArgs @("rev-parse","HEAD:scripts/g2e/p5a_d2s2_a1_ntfs_metadata_preflight.py")).Trim()

if ($ScriptBlob -ne $Lock.oneclick_blob) {
    throw "ONECLICK_BLOB_DRIFT:$ScriptBlob"
}
if ($PreflightBlob -ne $Lock.preflight_blob) {
    throw "PREFLIGHT_BLOB_DRIFT:$PreflightBlob"
}

if (-not (Test-Path $PythonExe)) {
    throw "PYTHON_EXE_MISSING:$PythonExe"
}
if (-not (Test-Path $CodexExe)) {
    throw "CODEX_EXE_MISSING:$CodexExe"
}
if ((Get-Sha256 $CodexExe) -ne $ExpectedCodexSha256) {
    throw "CODEX_HASH_DRIFT"
}

$LocalRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S2-A1"
if (Test-Path $LocalRoot) {
    throw "D2S2_LOCAL_ROOT_ALREADY_EXISTS:$LocalRoot"
}

$VolumeDir = Join-Path $LocalRoot "volume"
$CodexHome = Join-Path $LocalRoot "codex-home\preturn-a1"
$EvidenceDir = Join-Path $LocalRoot "evidence\preturn-a1"
$ReportDir = Join-Path $LocalRoot "report"

New-Item -ItemType Directory -Path $VolumeDir -Force | Out-Null
New-Item -ItemType Directory -Path $CodexHome -Force | Out-Null
New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null

$ReportJson = Join-Path $ReportDir "P5A_D2S2_A1_ONECLICK_REPORT.json"
$ReportMd   = Join-Path $ReportDir "P5A_D2S2_A1_ONECLICK_REPORT.md"

$Report = [ordered]@{
    schema = "G2E-P5A-D2S2-A1-ONECLICK-REPORT-v1"
    status = "STARTED"
    study_id = $StudyId
    attempt_id = $AttemptId
    source_head = $Head
    qualified_candidate_sha = $Lock.qualified_candidate_sha
    oneclick_blob = $ScriptBlob
    preflight_blob = $PreflightBlob
    selected_drive = $null
    volume_root = $null
    vhdx_path = $null
    input_sha256 = $null
    task_sha256 = $null
    config_sha256 = $null
    preturn_gate_pass = $false
    turn_start_request_sent = $false
    scientific_attempt_consumed = $false
    diagnostic = $null
    preflight_evidence_file = $null
    preflight_evidence_sha256 = $null
    task_payload_names = @()
    filesystem_support_metadata_names = @()
    unexpected_root_names = @()
}

$VhdxPath = Join-Path $VolumeDir "P5A-D2S2-A1-TASK.vhdx"
$DiskpartScript = Join-Path $VolumeDir "create_vhdx.diskpart.txt"
$DriveLetter = $null

try {
    if (Test-Path $VhdxPath) {
        throw "VHDX_ALREADY_EXISTS"
    }

    $DriveLetter = Get-FirstFreeDriveLetter
    $VolumeRoot = "$($DriveLetter):\"

    $Report.selected_drive = "$($DriveLetter):"
    $Report.volume_root = $VolumeRoot
    $Report.vhdx_path = $VhdxPath

    $diskpart = @(
        "create vdisk file=""$VhdxPath"" maximum=128 type=expandable",
        "select vdisk file=""$VhdxPath""",
        "attach vdisk",
        "create partition primary",
        "format fs=ntfs quick label=G2ED2S2A1",
        "assign letter=$DriveLetter"
    )
    [IO.File]::WriteAllLines($DiskpartScript, $diskpart, [Text.ASCIIEncoding]::new())

    & diskpart.exe /s $DiskpartScript | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "DISKPART_FAILED:$LASTEXITCODE"
    }

    if (-not (Test-Path $VolumeRoot)) {
        throw "MOUNTED_VOLUME_MISSING:$VolumeRoot"
    }

    $SourceFixture = Join-Path $ProjectRoot "g2e\.local\P5A-D2S1\execution\P5-FX-001"
    $SourceInput = Join-Path $SourceFixture "input.json"
    $SourceTask  = Join-Path $SourceFixture "TASK.md"

    if (-not (Test-Path $SourceInput) -or -not (Test-Path $SourceTask)) {
        throw "FROZEN_SOURCE_FIXTURE_MISSING"
    }

    if ((Get-Sha256 $SourceInput) -ne $ExpectedInputSha256) {
        throw "SOURCE_INPUT_HASH_DRIFT"
    }
    if ((Get-Sha256 $SourceTask) -ne $ExpectedTaskSha256) {
        throw "SOURCE_TASK_HASH_DRIFT"
    }

    Copy-Item -LiteralPath $SourceInput -Destination (Join-Path $VolumeRoot "input.json")
    Copy-Item -LiteralPath $SourceTask -Destination (Join-Path $VolumeRoot "TASK.md")

    $RootItems = @(Get-ChildItem -LiteralPath $VolumeRoot -Force)
    $RootNames = @($RootItems | Select-Object -ExpandProperty Name | Sort-Object)
    $AllowedRootNames = @("input.json", "TASK.md", "System Volume Information")
    $UnexpectedRootNames = @($RootNames | Where-Object { $_ -notin $AllowedRootNames })
    if ($UnexpectedRootNames.Count -gt 0) {
        throw "ISOLATED_VOLUME_UNEXPECTED_ROOT_ENTRIES:$($UnexpectedRootNames -join ',')"
    }
    $Svi = @($RootItems | Where-Object { $_.Name -eq "System Volume Information" })
    if ($Svi.Count -gt 1 -or ($Svi.Count -eq 1 -and -not $Svi[0].PSIsContainer)) {
        throw "SYSTEM_VOLUME_INFORMATION_INVALID"
    }
    $PayloadNames = @($RootItems | Where-Object { -not $_.PSIsContainer } | Select-Object -ExpandProperty Name | Sort-Object)
    if (($PayloadNames -join "|") -ne "input.json|TASK.md") {
        throw "ISOLATED_VOLUME_TASK_PAYLOAD_DRIFT:$($PayloadNames -join ',')"
    }
    $Report.task_payload_names = $PayloadNames
    $Report.filesystem_support_metadata_names = @($Svi | Select-Object -ExpandProperty Name)
    $Report.unexpected_root_names = $UnexpectedRootNames

    $InputHash = Get-Sha256 (Join-Path $VolumeRoot "input.json")
    $TaskHash = Get-Sha256 (Join-Path $VolumeRoot "TASK.md")
    if ($InputHash -ne $ExpectedInputSha256) {
        throw "VOLUME_INPUT_HASH_DRIFT"
    }
    if ($TaskHash -ne $ExpectedTaskSha256) {
        throw "VOLUME_TASK_HASH_DRIFT"
    }

    $Report.input_sha256 = $InputHash.ToLowerInvariant()
    $Report.task_sha256 = $TaskHash.ToLowerInvariant()

    $ResultPath = Join-Path $VolumeRoot "result.json"
    $TomlResultPath = $ResultPath.Replace("\", "\\")
    $ConfigPath = Join-Path $LocalRoot "config.toml"

    $config = @"
default_permissions = "$ProfileId"

[windows]
sandbox = "elevated"

[permissions.$ProfileId]
description = "G2E P5A D2-S2 isolated-volume root-read authority"

[permissions.$ProfileId.filesystem]
":root" = "read"
"$TomlResultPath" = "write"

[permissions.$ProfileId.network]
enabled = false
"@
    [IO.File]::WriteAllText($ConfigPath, $config.Replace([Environment]::NewLine, [char]10) + [char]10, [Text.UTF8Encoding]::new($false))

    $ConfigHash = Get-Sha256 $ConfigPath
    $Report.config_sha256 = $ConfigHash.ToLowerInvariant()

    $DefaultAuth = Join-Path $env:USERPROFILE ".codex\auth.json"
    if (-not (Test-Path $DefaultAuth)) {
        throw "DEFAULT_AUTH_MISSING"
    }

    Copy-Item -LiteralPath $DefaultAuth -Destination (Join-Path $CodexHome "auth.json")
    Copy-Item -LiteralPath $ConfigPath -Destination (Join-Path $CodexHome "config.toml")

    $HomeNames = @(Get-ChildItem -LiteralPath $CodexHome -Force | Select-Object -ExpandProperty Name | Sort-Object)
    if (($HomeNames -join "|") -ne "auth.json|config.toml") {
        throw "CODEX_HOME_PRESTATE_DRIFT:$($HomeNames -join ',')"
    }

    $PreflightScript = Join-Path $ProjectRoot "scripts\g2e\p5a_d2s2_a1_ntfs_metadata_preflight.py"

    $PreflightOutput = & $PythonExe $PreflightScript --project-root $ProjectRoot --local-root $LocalRoot --expected-head $Head --workspace $VolumeRoot --config $ConfigPath --expected-config-sha256 $ConfigHash --codex-home $CodexHome --evidence-dir $EvidenceDir --codex $CodexExe 2>&1
    $PreflightExit = $LASTEXITCODE
    $PreflightText = ($PreflightOutput | Out-String).Trim()
    Write-Host $PreflightText

    $EvidenceFile = Join-Path $EvidenceDir "P5A_D2S2_LOCAL_PRETURN_PREFLIGHT.json"
    if (Test-Path $EvidenceFile) {
        $Evidence = Get-Content -LiteralPath $EvidenceFile -Raw | ConvertFrom-Json
        $Report.preturn_gate_pass = [bool]$Evidence.preturn_gate_pass
        $Report.preflight_evidence_file = $EvidenceFile
        $Report.preflight_evidence_sha256 = (Get-Sha256 $EvidenceFile).ToLowerInvariant()

        if ($Evidence.windows_sandbox_setup_error_redacted) {
            $Report.diagnostic = [string]$Evidence.windows_sandbox_setup_error_redacted
        }
        elseif ($Evidence.driver_exception) {
            $Report.diagnostic = [string]$Evidence.driver_exception
        }
        else {
            $Report.diagnostic = "NO_DIAGNOSTIC_ERROR"
        }

        if ($Evidence.turn_start_request_sent -ne $false) {
            throw "SCIENTIFIC_DISPATCH_FIREWALL_VIOLATION"
        }
        if ($Evidence.scientific_attempt_consumed -ne $false) {
            throw "SCIENTIFIC_ATTEMPT_CONSUMPTION_VIOLATION"
        }
    }
    else {
        $Report.diagnostic = "PREFLIGHT_EVIDENCE_MISSING"
    }

    if ($PreflightExit -ne 0) {
        $Report.status = "PRETURN_BLOCKED"
        Write-JsonFile $ReportJson $Report
        Write-MarkdownReport $ReportMd $Report
        Write-Host ""
        Write-Host "REPORT JSON: $ReportJson"
        Write-Host "REPORT MD  : $ReportMd"
        exit $PreflightExit
    }

    if ($Report.preturn_gate_pass -ne $true) {
        throw "PREFLIGHT_EXITED_ZERO_WITHOUT_PASS"
    }

    $Report.status = "PRETURN_PASS"
    $Report.diagnostic = "ISOLATED_VOLUME_NO_TURN_PREFLIGHT_PASS"

    Write-JsonFile $ReportJson $Report
    Write-MarkdownReport $ReportMd $Report

    Write-Host ""
    Write-Host "=== D2-S2 ONE-CLICK COMPLETE ==="
    Write-Host "STATUS      : $($Report.status)"
    Write-Host "VOLUME ROOT : $VolumeRoot"
    Write-Host "REPORT JSON : $ReportJson"
    Write-Host "REPORT MD   : $ReportMd"
    Write-Host "TURN START  : FALSE"
    Write-Host "ATTEMPT USED: FALSE"

    exit 0
}
catch {
    $Report.status = "PRETURN_INVALID_OR_BLOCKED"
    $Report.diagnostic = $_.Exception.Message

    try {
        Write-JsonFile $ReportJson $Report
        Write-MarkdownReport $ReportMd $Report
        Write-Host ""
        Write-Host "REPORT JSON: $ReportJson"
        Write-Host "REPORT MD  : $ReportMd"
    }
    catch {
        Write-Host "REPORT_WRITE_FAILED:$($_.Exception.Message)"
    }

    Write-Error $Report.diagnostic
    exit 1
}