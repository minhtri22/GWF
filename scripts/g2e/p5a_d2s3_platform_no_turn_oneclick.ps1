param(
    [string]$ProjectRoot = "",
    [string]$PythonExe = "",
    [switch]$ConfigSerializationSelfTest
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$StudyId = "p5a-d2s3-release-coherent-instrument-successor"
$AttemptId = "p5a-d2s3-p5-fx-001-attempt-001"
$ProfileId = "g2e_p5a_d2s3"

$ExpectedInputSha256 = "A176454229FEEF1CE8BD7EAB1EA79FBFEFF07C229C88123EDF862FEA9160EEF6"
$ExpectedTaskSha256 = "4C4ABA6A82D540440DFEF725B2568AFDEF4BE3B26C3E4E84E2B34C54E6DD460E"
$ExpectedCodexSha256 = "444A3F0008050605CAE73CD9B7A2DCAC61294062DFAAB56DD20430FD6498518B"
$ExpectedHelperSha256 = "0C3EEB7CEE8D2BC4C8644DEF3C818E8B06760979572DCEDC919C38D0F38F64C4"
$ExpectedStagingReportSha256 = "21DEDDE191D144AD561AF7E78903FCE73990D8FFBB6D8BB701A34EB95E336C76"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Convert-ToLfText([string]$Text) {
    return $Text.Replace("`r`n", "`n").Replace("`r", "`n")
}

function Invoke-ConfigSerializationSelfTest {
    $tempRoot = Join-Path ([IO.Path]::GetTempPath()) ("g2e-d2s3-config-" + [Guid]::NewGuid().ToString("N"))
    $path = Join-Path $tempRoot "config.toml"
    try {
        New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
        $sample = "alpha`r`nbeta`rgamma"
        $normalized = (Convert-ToLfText $sample) + "`n"
        [IO.File]::WriteAllText(
            $path,
            $normalized,
            [Text.UTF8Encoding]::new($false)
        )
        $bytes = [IO.File]::ReadAllBytes($path)
        if ($bytes.Length -lt 2) { throw "CONFIG_SERIALIZATION_SELFTEST_TOO_SHORT" }
        if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB) {
            throw "CONFIG_SERIALIZATION_SELFTEST_BOM_PRESENT"
        }
        if ($bytes -contains 13) {
            throw "CONFIG_SERIALIZATION_SELFTEST_CR_PRESENT"
        }
        if ($bytes[$bytes.Length - 1] -ne 10) {
            throw "CONFIG_SERIALIZATION_SELFTEST_NO_TRAILING_LF"
        }
        if ($bytes[$bytes.Length - 2] -eq 10) {
            throw "CONFIG_SERIALIZATION_SELFTEST_DOUBLE_TRAILING_LF"
        }
        $roundTrip = [Text.Encoding]::UTF8.GetString($bytes)
        if ($roundTrip -ne "alpha`nbeta`ngamma`n") {
            throw "CONFIG_SERIALIZATION_SELFTEST_CONTENT_MISMATCH"
        }
        Write-Host "CONFIG_SERIALIZATION_SELFTEST_PASS"
    }
    finally {
        if (Test-Path -LiteralPath $tempRoot) {
            Remove-Item -LiteralPath $tempRoot -Recurse -Force
        }
    }
}

function Write-JsonFile([string]$Path, $Object) {
    $json = $Object | ConvertTo-Json -Depth 16
    [IO.File]::WriteAllText(
        $Path,
        $json + [Environment]::NewLine,
        [Text.UTF8Encoding]::new($false)
    )
}

function Get-FirstFreeDriveLetter {
    foreach ($letter in @("R","S","T","U","V","W","X","Y","Z")) {
        if (-not (Test-Path "$($letter):\")) {
            return $letter
        }
    }
    throw "NO_FREE_DRIVE_LETTER_R_TO_Z"
}

if ($ConfigSerializationSelfTest) {
    Invoke-ConfigSerializationSelfTest
    exit 0
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

$ThisScript = $MyInvocation.MyCommand.Path

if (-not (Test-IsAdministrator)) {
    Write-Host "Administrator elevation is required for the D2-S3 isolated VHDX preflight."
    Write-Host "A UAC prompt will open. No model turn is executed by this script."

    $ElevatedArgs = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $ThisScript,
        "-ProjectRoot", $ProjectRoot,
        "-PythonExe", $PythonExe
    )

    $p = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $ElevatedArgs -Wait -PassThru
    exit $p.ExitCode
}

Set-Location $ProjectRoot

$LockPath = Join-Path $ProjectRoot "g2e\docs\P5A_D2S3_PRETURN_CONFIG_SERIALIZATION_REPAIR_001_LOCK.json"
if (-not (Test-Path -LiteralPath $LockPath -PathType Leaf)) {
    throw "PREFLIGHT_LOCK_MISSING:$LockPath"
}

$Lock = Get-Content -LiteralPath $LockPath -Raw | ConvertFrom-Json
if ($Lock.qualified -ne $true) {
    throw "PREFLIGHT_NOT_QUALIFIED"
}

$Dirty = git status --porcelain
if ($LASTEXITCODE -ne 0) {
    throw "GIT_STATUS_FAILED"
}
if ($Dirty) {
    Write-Host $Dirty
    throw "SOURCE_WORKTREE_DIRTY"
}

git fetch --prune origin feature/g2e-framework
if ($LASTEXITCODE -ne 0) {
    throw "GIT_FETCH_FAILED"
}

$RemoteHead = (git rev-parse "origin/feature/g2e-framework").Trim()
git switch --detach "origin/feature/g2e-framework"
if ($LASTEXITCODE -ne 0) {
    throw "GIT_DETACH_FAILED"
}

$Head = (git rev-parse HEAD).Trim()
if ($Head -ne $RemoteHead) {
    throw "REMOTE_HEAD_CHECKOUT_MISMATCH:$($Head):$($RemoteHead)"
}

if (git status --porcelain) {
    throw "SOURCE_WORKTREE_DIRTY_AFTER_SWITCH"
}

$ScriptBlob = (git rev-parse "HEAD:scripts/g2e/p5a_d2s3_platform_no_turn_oneclick.ps1").Trim()
$PreflightBlob = (git rev-parse "HEAD:scripts/g2e/p5a_d2s3_platform_no_turn_preflight.py").Trim()

if ($ScriptBlob -ne $Lock.oneclick_blob) {
    throw "ONECLICK_BLOB_DRIFT:$ScriptBlob"
}
if ($PreflightBlob -ne $Lock.preflight_blob) {
    throw "PREFLIGHT_BLOB_DRIFT:$PreflightBlob"
}

if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
    throw "PYTHON_EXE_MISSING:$PythonExe"
}

$InstrumentRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S3-INSTRUMENT"
$StagingReport = Join-Path $InstrumentRoot "report\P5A_D2S3_INSTRUMENT_STAGING_REPORT.json"
$CodexExe = Join-Path $InstrumentRoot "package\bin\codex.exe"
$HelperExe = Join-Path $InstrumentRoot "package\codex-resources\codex-windows-sandbox-setup.exe"

if (-not (Test-Path -LiteralPath $StagingReport -PathType Leaf)) {
    throw "STAGING_REPORT_MISSING"
}
if ((Get-Sha256 $StagingReport) -ne $ExpectedStagingReportSha256) {
    throw "STAGING_REPORT_HASH_DRIFT"
}

$Staging = Get-Content -LiteralPath $StagingReport -Raw | ConvertFrom-Json
if ($Staging.status -ne "STAGING_PASS_PLATFORM_PREFLIGHT_GATE_REQUIRED") {
    throw "STAGING_STATUS_NOT_PASS"
}
if ($Staging.global_install_modified -ne $false) {
    throw "STAGING_GLOBAL_MUTATION_FLAG"
}
if ($Staging.executables_invoked -ne $false) {
    throw "STAGING_EXECUTION_FLAG"
}
if ($Staging.turn_start_request_sent -ne $false) {
    throw "STAGING_TURN_FLAG"
}
if ($Staging.scientific_attempt_consumed -ne $false) {
    throw "STAGING_ATTEMPT_FLAG"
}

if (-not (Test-Path -LiteralPath $CodexExe -PathType Leaf)) {
    throw "STAGED_CODEX_MISSING"
}
if (-not (Test-Path -LiteralPath $HelperExe -PathType Leaf)) {
    throw "STAGED_HELPER_MISSING"
}
if ((Get-Sha256 $CodexExe) -ne $ExpectedCodexSha256) {
    throw "STAGED_CODEX_HASH_DRIFT"
}
if ((Get-Sha256 $HelperExe) -ne $ExpectedHelperSha256) {
    throw "STAGED_HELPER_HASH_DRIFT"
}

$LocalRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S3-PREFLIGHT-R1"
if (Test-Path -LiteralPath $LocalRoot) {
    throw "D2S3_PREFLIGHT_R1_ROOT_ALREADY_EXISTS:$LocalRoot"
}

$VolumeDir = Join-Path $LocalRoot "volume"
$CodexHome = Join-Path $LocalRoot "codex-home\preturn-001"
$EvidenceDir = Join-Path $LocalRoot "evidence\preturn-001"
$ReportDir = Join-Path $LocalRoot "report"

New-Item -ItemType Directory -Path $VolumeDir -Force | Out-Null
New-Item -ItemType Directory -Path $CodexHome -Force | Out-Null
New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null

$ReportJson = Join-Path $ReportDir "P5A_D2S3_PLATFORM_NO_TURN_R1_REPORT.json"
$VhdxPath = Join-Path $VolumeDir "P5A-D2S3-PREFLIGHT-R1-TASK.vhdx"
$DiskpartScript = Join-Path $VolumeDir "create_vhdx.diskpart.txt"

$Report = [ordered]@{
    schema = "G2E-P5A-D2S3-PLATFORM-NO-TURN-R1-REPORT-v1"
    status = "STARTED"
    study_id = $StudyId
    attempt_id = $AttemptId
    profile_id = $ProfileId
    source_head = $Head
    qualified_candidate_sha = $Lock.qualified_candidate_sha
    oneclick_blob = $ScriptBlob
    preflight_blob = $PreflightBlob
    staging_report_sha256 = $ExpectedStagingReportSha256.ToLowerInvariant()
    codex_sha256 = $ExpectedCodexSha256.ToLowerInvariant()
    helper_sha256 = $ExpectedHelperSha256.ToLowerInvariant()
    selected_drive = $null
    volume_root = $null
    vhdx_path = $VhdxPath
    input_sha256 = $null
    task_sha256 = $null
    config_sha256 = $null
    preturn_gate_pass = $false
    turn_start_request_sent = $false
    scientific_attempt_consumed = $false
    result_exists = $false
    diagnostic = $null
    preflight_evidence_file = $null
    preflight_evidence_sha256 = $null
    cleanup = [ordered]@{
        attached_before_cleanup = $null
        cleanup_action = "NOT_ATTACHED"
        attached_after_cleanup = $null
        cleanup_error = $null
    }
}

$FinalExitCode = 0
$VhdxMayBeAttached = $false
$DriveLetter = $null

# PROTECTED_VHDX_BODY_START
try {
    try {
        if (Test-Path -LiteralPath $VhdxPath) {
            throw "VHDX_ALREADY_EXISTS"
        }

        $DriveLetter = Get-FirstFreeDriveLetter
        $VolumeRoot = "$($DriveLetter):\"

        $Report.selected_drive = "$($DriveLetter):"
        $Report.volume_root = $VolumeRoot

        $diskpart = @(
            "create vdisk file=""$VhdxPath"" maximum=128 type=expandable",
            "select vdisk file=""$VhdxPath""",
            "attach vdisk",
            "create partition primary",
            "format fs=ntfs quick label=G2ED2S3R1",
            "assign letter=$DriveLetter"
        )
        [IO.File]::WriteAllLines(
            $DiskpartScript,
            $diskpart,
            [Text.ASCIIEncoding]::new()
        )

        $VhdxMayBeAttached = $true
        & diskpart.exe /s $DiskpartScript | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "DISKPART_FAILED:$LASTEXITCODE"
        }

        if (-not (Test-Path -LiteralPath $VolumeRoot -PathType Container)) {
            throw "MOUNTED_VOLUME_MISSING:$VolumeRoot"
        }

        $SourceFixture = Join-Path $ProjectRoot "g2e\.local\P5A-D2S1\execution\P5-FX-001"
        $SourceInput = Join-Path $SourceFixture "input.json"
        $SourceTask = Join-Path $SourceFixture "TASK.md"

        if (-not (Test-Path -LiteralPath $SourceInput -PathType Leaf) -or
            -not (Test-Path -LiteralPath $SourceTask -PathType Leaf)) {
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

        $RootNames = @(
            Get-ChildItem -LiteralPath $VolumeRoot -Force |
                Select-Object -ExpandProperty Name |
                Sort-Object
        )
        if (($RootNames -join "|") -ne "input.json|TASK.md") {
            throw "ISOLATED_VOLUME_PRESTATE_DRIFT:$($RootNames -join ',')"
        }

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
description = "G2E P5A D2-S3 release-coherent isolated-volume preturn authority"

[permissions.$ProfileId.filesystem]
":root" = "read"
"$TomlResultPath" = "write"

[permissions.$ProfileId.network]
enabled = false
"@
        [IO.File]::WriteAllText(
            $ConfigPath,
            (Convert-ToLfText $config) + "`n",
            [Text.UTF8Encoding]::new($false)
        )

        $ConfigHash = Get-Sha256 $ConfigPath
        $Report.config_sha256 = $ConfigHash.ToLowerInvariant()

        $DefaultAuth = Join-Path $env:USERPROFILE ".codex\auth.json"
        if (-not (Test-Path -LiteralPath $DefaultAuth -PathType Leaf)) {
            throw "DEFAULT_AUTH_MISSING"
        }

        Copy-Item -LiteralPath $DefaultAuth -Destination (Join-Path $CodexHome "auth.json")
        Copy-Item -LiteralPath $ConfigPath -Destination (Join-Path $CodexHome "config.toml")

        $HomeNames = @(
            Get-ChildItem -LiteralPath $CodexHome -Force |
                Select-Object -ExpandProperty Name |
                Sort-Object
        )
        if (($HomeNames -join "|") -ne "auth.json|config.toml") {
            throw "CODEX_HOME_PRESTATE_DRIFT:$($HomeNames -join ',')"
        }

        $PreflightScript = Join-Path $ProjectRoot "scripts\g2e\p5a_d2s3_platform_no_turn_preflight.py"
        $PreflightArgs = @(
            $PreflightScript,
            "--project-root", $ProjectRoot,
            "--local-root", $LocalRoot,
            "--expected-head", $Head,
            "--workspace", $VolumeRoot,
            "--config", $ConfigPath,
            "--expected-config-sha256", $ConfigHash,
            "--codex-home", $CodexHome,
            "--evidence-dir", $EvidenceDir,
            "--codex", $CodexExe
        )

        $PreflightOutput = & $PythonExe @PreflightArgs 2>&1
        $PreflightExit = $LASTEXITCODE
        $PreflightText = ($PreflightOutput | Out-String).Trim()
        if ($PreflightText) {
            Write-Host $PreflightText
        }

        $EvidenceFile = Join-Path $EvidenceDir "P5A_D2S3_PLATFORM_NO_TURN_PREFLIGHT.json"

        if (Test-Path -LiteralPath $EvidenceFile -PathType Leaf) {
            $Evidence = Get-Content -LiteralPath $EvidenceFile -Raw | ConvertFrom-Json
            $Report.preturn_gate_pass = [bool]$Evidence.preturn_gate_pass
            $Report.preflight_evidence_file = $EvidenceFile
            $Report.preflight_evidence_sha256 = (Get-Sha256 $EvidenceFile).ToLowerInvariant()
            $Report.result_exists = [bool]$Evidence.result_exists

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
            if ($Evidence.result_exists -ne $false) {
                throw "PRETURN_RESULT_FILE_VIOLATION"
            }
        }
        else {
            $Report.diagnostic = "PREFLIGHT_EVIDENCE_MISSING"
        }

        if ($PreflightExit -ne 0) {
            $Report.status = "PRETURN_BLOCKED"
            $FinalExitCode = $PreflightExit
        }
        elseif ($Report.preturn_gate_pass -ne $true) {
            throw "PREFLIGHT_EXITED_ZERO_WITHOUT_PASS"
        }
        else {
            $Report.status = "PRETURN_PASS_SCIENTIFIC_AUTHORIZATION_REVIEW_REQUIRED"
            $Report.diagnostic = "RELEASE_COHERENT_PLATFORM_NO_TURN_PREFLIGHT_PASS"
            $FinalExitCode = 0
        }
    }
    catch {
        if ($Report.status -ne "PRETURN_BLOCKED") {
            $Report.status = "PRETURN_INVALID_OR_BLOCKED"
            $Report.diagnostic = $_.Exception.Message
            $FinalExitCode = 1
        }
    }
}
finally {
    if ($VhdxMayBeAttached -and (Test-Path -LiteralPath $VhdxPath -PathType Leaf)) {
        try {
            $imageBefore = Get-DiskImage -ImagePath $VhdxPath -ErrorAction Stop
            $Report.cleanup.attached_before_cleanup = [bool]$imageBefore.Attached

            if ($imageBefore.Attached) {
                Dismount-DiskImage -ImagePath $VhdxPath -ErrorAction Stop | Out-Null
                $Report.cleanup.cleanup_action = "DISMOUNTED"
            }
            else {
                $Report.cleanup.cleanup_action = "ALREADY_DETACHED"
            }

            Start-Sleep -Milliseconds 250
            $imageAfter = Get-DiskImage -ImagePath $VhdxPath -ErrorAction Stop
            $Report.cleanup.attached_after_cleanup = [bool]$imageAfter.Attached

            if ($imageAfter.Attached) {
                $Report.cleanup.cleanup_error = "ATTACHED_AFTER_CLEANUP"
                $Report.status = "PRETURN_INVALID_OR_BLOCKED"
                $Report.diagnostic = "VHDX_CLEANUP_VERIFICATION_FAILED"
                $FinalExitCode = 1
            }
        }
        catch {
            $Report.cleanup.cleanup_error = $_.Exception.Message
            $Report.status = "PRETURN_INVALID_OR_BLOCKED"
            $Report.diagnostic = "VHDX_CLEANUP_EXCEPTION"
            $FinalExitCode = 1
        }
    }
    else {
        $Report.cleanup.attached_before_cleanup = $false
        $Report.cleanup.attached_after_cleanup = $false
        $Report.cleanup.cleanup_action = "NOT_ATTACHED"
    }

    try {
        Write-JsonFile $ReportJson $Report
    }
    catch {
        Write-Error "REPORT_WRITE_FAILED:$($_.Exception.Message)"
        $FinalExitCode = 2
    }
}
# PROTECTED_VHDX_BODY_END

Write-Host ""
Write-Host "=== D2-S3 PLATFORM NO-TURN PREFLIGHT COMPLETE ==="
Write-Host "STATUS      : $($Report.status)"
Write-Host "REPORT JSON : $ReportJson"
Write-Host "VHDX AFTER  : $($Report.cleanup.attached_after_cleanup)"
Write-Host "TURN START  : FALSE"
Write-Host "ATTEMPT USED: FALSE"

exit $FinalExitCode
