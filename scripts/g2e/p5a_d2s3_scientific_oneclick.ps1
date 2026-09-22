param(
    [string]$ProjectRoot = "",
    [string]$PythonExe = "",
    [switch]$InfrastructureSelfTest
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedCodexSha256 = "444A3F0008050605CAE73CD9B7A2DCAC61294062DFAAB56DD20430FD6498518B"
$ExpectedHelperSha256 = "0C3EEB7CEE8D2BC4C8644DEF3C818E8B06760979572DCEDC919C38D0F38F64C4"
$ExpectedInputSha256 = "A176454229FEEF1CE8BD7EAB1EA79FBFEFF07C229C88123EDF862FEA9160EEF6"
$ExpectedTaskSha256 = "4C4ABA6A82D540440DFEF725B2568AFDEF4BE3B26C3E4E84E2B34C54E6DD460E"
$ExpectedR2ReportSha256 = "B24AF8E5261BA8E5A90605E7A9B9D63C0025F37650F9A4E657CDAAFD76B0545E"
$ExpectedR2EvidenceSha256 = "87F18CF15F06EB1BC3E0A9E28F76E3208B2C082C3CD458221242D65DB7B8CC28"

$StudyId = "p5a-d2s3-release-coherent-instrument-successor"
$AttemptId = "p5a-d2s3-p5-fx-001-attempt-001"
$ProfileId = "g2e_p5a_d2s3"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Convert-ToLfText([string]$Text) {
    $crlf = ([string][char]13) + ([string][char]10)
    $lf = [string][char]10
    $cr = [string][char]13
    return $Text.Replace($crlf, $lf).Replace($cr, $lf)
}

function Get-OptionalProperty($Object, [string]$Name, $Default = $null) {
    if ($null -eq $Object) { return $Default }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

function Get-FirstFreeDriveLetter {
    foreach ($letter in @("R","S","T","U","V","W","X","Y","Z")) {
        if (-not (Test-Path "$($letter):\")) {
            return $letter
        }
    }
    throw "NO_FREE_DRIVE_LETTER_R_TO_Z"
}

function Get-WorkspaceRootClassification([string]$Root) {
    $payload = @()
    $support = @()
    $result = @()
    $unexpected = @()

    foreach ($item in @(Get-ChildItem -LiteralPath $Root -Force)) {
        $isReparse = [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)

        if (($item.Name -eq "input.json" -or $item.Name -eq "TASK.md") -and
            -not $item.PSIsContainer -and -not $isReparse) {
            $payload += $item.Name
            continue
        }
        if ($item.Name -eq "System Volume Information" -and
            $item.PSIsContainer -and -not $isReparse) {
            $support += $item.Name
            continue
        }
        if ($item.Name -eq "result.json" -and
            -not $item.PSIsContainer -and -not $isReparse) {
            $result += $item.Name
            continue
        }
        $unexpected += $item.Name
    }

    return [pscustomobject]@{
        payload = @($payload | Sort-Object)
        support = @($support | Sort-Object)
        result = @($result | Sort-Object)
        unexpected = @($unexpected | Sort-Object)
    }
}

function Invoke-NativeCaptured([string]$FilePath, [string[]]$Arguments) {
    $previousErrorActionPreference = $ErrorActionPreference
    $output = @()
    $exitCode = $null
    try {
        $ErrorActionPreference = "Continue"
        $output = @(& $FilePath @Arguments 2>&1)
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    return [pscustomobject]@{
        ExitCode = $exitCode
        Output = $output
        Text = (($output | Out-String).Trim())
    }
}

function Write-JsonFile([string]$Path, $Object) {
    $json = $Object | ConvertTo-Json -Depth 20
    [IO.File]::WriteAllText(
        $Path,
        $json + [Environment]::NewLine,
        [Text.UTF8Encoding]::new($false)
    )
}

function Invoke-InfrastructureSelfTest {
    $root = Join-Path ([IO.Path]::GetTempPath()) ("g2e-d2s3-science-" + [Guid]::NewGuid().ToString("N"))
    try {
        New-Item -ItemType Directory -Path $root -Force | Out-Null
        [IO.File]::WriteAllText((Join-Path $root "input.json"), "{}", [Text.UTF8Encoding]::new($false))
        [IO.File]::WriteAllText((Join-Path $root "TASK.md"), "task", [Text.UTF8Encoding]::new($false))
        New-Item -ItemType Directory -Path (Join-Path $root "System Volume Information") -Force | Out-Null

        $class = Get-WorkspaceRootClassification $root
        if (@($class.payload).Count -ne 2 -or @($class.unexpected).Count -ne 0) {
            throw "SCIENCE_ROOT_CLASSIFIER_SELFTEST_FAILED"
        }

        $sample = "alpha" + [char]13 + [char]10 + "beta" + [char]13 + "gamma"
        $expected = "alpha" + [char]10 + "beta" + [char]10 + "gamma" + [char]10
        $normalized = (Convert-ToLfText $sample) + [char]10
        if ($normalized -ne $expected) {
            throw "SCIENCE_CONFIG_SERIALIZER_SELFTEST_FAILED"
        }

        $sampleObject = [pscustomobject]@{present = "ok"}
        if ((Get-OptionalProperty $sampleObject "missing" "fallback") -ne "fallback") {
            throw "SCIENCE_OPTIONAL_PROPERTY_SELFTEST_FAILED"
        }

        $python = (Get-Command python -ErrorAction Stop).Source
        $native = Invoke-NativeCaptured -FilePath $python -Arguments @(
            "-c",
            "import sys; sys.stderr.write('G2E_NATIVE_STDERR_SENTINEL\\n'); sys.exit(7)"
        )
        if ($native.ExitCode -ne 7) {
            throw "SCIENCE_NATIVE_CAPTURE_EXITCODE_SELFTEST_FAILED"
        }
        if ($native.Text -notmatch "G2E_NATIVE_STDERR_SENTINEL") {
            throw "SCIENCE_NATIVE_CAPTURE_STDERR_SELFTEST_FAILED"
        }

        Write-Host "SCIENTIFIC_INFRASTRUCTURE_SELFTEST_PASS"
    }
    finally {
        if (Test-Path -LiteralPath $root) {
            Remove-Item -LiteralPath $root -Recurse -Force
        }
    }
}

if ($InfrastructureSelfTest) {
    Invoke-InfrastructureSelfTest
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
    Write-Host "Administrator elevation is required for the D2-S3 scientific isolated VHDX."
    Write-Host "A UAC prompt will open. This invocation may consume the one authorized scientific attempt."

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

$LockPath = Join-Path $ProjectRoot "g2e\docs\P5A_D2S3_SCIENTIFIC_PREDISPATCH_REPAIR_001_LOCK.json"
if (-not (Test-Path -LiteralPath $LockPath -PathType Leaf)) {
    throw "SCIENTIFIC_LOCK_MISSING"
}
$Lock = Get-Content -LiteralPath $LockPath -Raw | ConvertFrom-Json
if ($Lock.qualified -ne $true -or $Lock.scientific_attempt_authorized -ne $true) {
    throw "SCIENTIFIC_EXECUTION_NOT_AUTHORIZED"
}
if ($Lock.retry_authorized -ne $false -or $Lock.automatic_retry_authorized -ne $false) {
    throw "SCIENTIFIC_RETRY_POLICY_DRIFT"
}
if ($Lock.attempt_id -ne $AttemptId) {
    throw "SCIENTIFIC_ATTEMPT_ID_LOCK_DRIFT"
}

$Dirty = git status --porcelain
if ($LASTEXITCODE -ne 0) { throw "GIT_STATUS_FAILED" }
if ($Dirty) {
    Write-Host $Dirty
    throw "SOURCE_WORKTREE_DIRTY"
}

git fetch --prune origin feature/g2e-framework
if ($LASTEXITCODE -ne 0) { throw "GIT_FETCH_FAILED" }

$RemoteHead = (git rev-parse "origin/feature/g2e-framework").Trim()
git switch --detach "origin/feature/g2e-framework"
if ($LASTEXITCODE -ne 0) { throw "GIT_DETACH_FAILED" }

$Head = (git rev-parse HEAD).Trim()
if ($Head -ne $RemoteHead) { throw "REMOTE_HEAD_CHECKOUT_MISMATCH" }
if (git status --porcelain) { throw "SOURCE_WORKTREE_DIRTY_AFTER_SWITCH" }

$OneclickBlob = (git rev-parse "HEAD:scripts/g2e/p5a_d2s3_scientific_oneclick.ps1").Trim()
$RunnerBlob = (git rev-parse "HEAD:scripts/g2e/p5a_d2s3_scientific_runner.py").Trim()
$VerifierBlob = (git rev-parse "HEAD:scripts/g2e/p5a_d2s3_scientific_verify.py").Trim()
$AdmissionBlob = (git rev-parse "HEAD:scripts/g2e/p5a_d2s3_scientific_admission.py").Trim()
$PreflightBlob = (git rev-parse "HEAD:scripts/g2e/p5a_d2s3_platform_no_turn_preflight.py").Trim()

if ($OneclickBlob -ne $Lock.oneclick_blob) { throw "ONECLICK_BLOB_DRIFT" }
if ($RunnerBlob -ne $Lock.runner_blob) { throw "RUNNER_BLOB_DRIFT" }
if ($VerifierBlob -ne $Lock.verifier_blob) { throw "VERIFIER_BLOB_DRIFT" }
if ($AdmissionBlob -ne $Lock.admission_blob) { throw "ADMISSION_BLOB_DRIFT" }
if ($PreflightBlob -ne $Lock.preflight_blob) { throw "PREFLIGHT_BLOB_DRIFT" }

$InstrumentRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S3-INSTRUMENT"
$CodexExe = Join-Path $InstrumentRoot "package\bin\codex.exe"
$HelperExe = Join-Path $InstrumentRoot "package\codex-resources\codex-windows-sandbox-setup.exe"
if ((Get-Sha256 $CodexExe) -ne $ExpectedCodexSha256) { throw "STAGED_CODEX_HASH_DRIFT" }
if ((Get-Sha256 $HelperExe) -ne $ExpectedHelperSha256) { throw "STAGED_HELPER_HASH_DRIFT" }

$R2Root = Join-Path $ProjectRoot "g2e\.local\P5A-D2S3-PREFLIGHT-R2"
$R2Report = Join-Path $R2Root "report\P5A_D2S3_PLATFORM_NO_TURN_R2_REPORT.json"
$R2Evidence = Join-Path $R2Root "evidence\preturn-001\P5A_D2S3_PLATFORM_NO_TURN_PREFLIGHT.json"
if ((Get-Sha256 $R2Report) -ne $ExpectedR2ReportSha256) { throw "R2_REPORT_HASH_DRIFT" }
if ((Get-Sha256 $R2Evidence) -ne $ExpectedR2EvidenceSha256) { throw "R2_EVIDENCE_HASH_DRIFT" }
if ($Lock.r2_report_sha256.ToUpperInvariant() -ne $ExpectedR2ReportSha256) { throw "LOCK_R2_REPORT_DRIFT" }
if ($Lock.r2_evidence_sha256.ToUpperInvariant() -ne $ExpectedR2EvidenceSha256) { throw "LOCK_R2_EVIDENCE_DRIFT" }

$LocalRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S3-SCIENCE-002"
if (Test-Path -LiteralPath $LocalRoot) {
    throw "SCIENTIFIC_ROOT_ALREADY_EXISTS_NO_RETRY"
}

$VolumeDir = Join-Path $LocalRoot "volume"
$CodexHome = Join-Path $LocalRoot "codex-home\science-002"
$EvidenceDir = Join-Path $LocalRoot "evidence\science-002"
$ReportDir = Join-Path $LocalRoot "report"
$VerificationDir = Join-Path $LocalRoot "verification"
New-Item -ItemType Directory -Path $VolumeDir -Force | Out-Null
New-Item -ItemType Directory -Path $CodexHome -Force | Out-Null
New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
New-Item -ItemType Directory -Path $VerificationDir -Force | Out-Null

$ReportPath = Join-Path $ReportDir "P5A_D2S3_SCIENTIFIC_EXECUTION_REPORT.json"
$VhdxPath = Join-Path $VolumeDir "P5A-D2S3-SCIENCE-002-TASK.vhdx"
$DiskpartScript = Join-Path $VolumeDir "create_science_vhdx.diskpart.txt"

$Report = [ordered]@{
    schema = "G2E-P5A-D2S3-SCIENTIFIC-EXECUTION-REPORT-v1"
    status = "STARTED"
    study_id = $StudyId
    attempt_id = $AttemptId
    source_head = $Head
    execution_config_hash = $Lock.execution_config_hash
    r2_report_sha256 = $ExpectedR2ReportSha256.ToLowerInvariant()
    r2_evidence_sha256 = $ExpectedR2EvidenceSha256.ToLowerInvariant()
    codex_sha256 = $ExpectedCodexSha256.ToLowerInvariant()
    helper_sha256 = $ExpectedHelperSha256.ToLowerInvariant()
    selected_drive = $null
    vhdx_path = $VhdxPath
    runner_exit_code = $null
    runner_evidence_sha256 = $null
    verifier_exit_code = $null
    verification_sha256 = $null
    scientific_attempt_consumed = $false
    turn_start_request_sent = $false
    turn_start_accepted = $false
    turn_id = $null
    result_exists = $false
    result_sha256 = $null
    metrics = $null
    adjudication_inputs = $null
    diagnostic = $null
    cleanup = [ordered]@{
        attached_before_cleanup = $null
        cleanup_action = "NOT_ATTACHED"
        attached_after_cleanup = $null
        cleanup_error = $null
    }
}

$FinalExitCode = 0
$VhdxMayBeAttached = $false

# PROTECTED_SCIENTIFIC_VHDX_BODY_START
try {
    try {
        $DriveLetter = Get-FirstFreeDriveLetter
        $VolumeRoot = "$($DriveLetter):\"
        $Report.selected_drive = "$($DriveLetter):"

        $diskpart = @(
            "create vdisk file=""$VhdxPath"" maximum=128 type=expandable",
            "select vdisk file=""$VhdxPath""",
            "attach vdisk",
            "create partition primary",
            "format fs=ntfs quick label=G2ED2S3S02",
            "assign letter=$DriveLetter"
        )
        [IO.File]::WriteAllLines($DiskpartScript, $diskpart, [Text.ASCIIEncoding]::new())
        $VhdxMayBeAttached = $true
        & diskpart.exe /s $DiskpartScript | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "SCIENTIFIC_DISKPART_FAILED" }
        if (-not (Test-Path -LiteralPath $VolumeRoot -PathType Container)) {
            throw "SCIENTIFIC_VOLUME_MISSING"
        }

        $SourceFixture = Join-Path $ProjectRoot "g2e\.local\P5A-D2S1\execution\P5-FX-001"
        $SourceInput = Join-Path $SourceFixture "input.json"
        $SourceTask = Join-Path $SourceFixture "TASK.md"
        if ((Get-Sha256 $SourceInput) -ne $ExpectedInputSha256) { throw "SOURCE_INPUT_HASH_DRIFT" }
        if ((Get-Sha256 $SourceTask) -ne $ExpectedTaskSha256) { throw "SOURCE_TASK_HASH_DRIFT" }

        Copy-Item -LiteralPath $SourceInput -Destination (Join-Path $VolumeRoot "input.json")
        Copy-Item -LiteralPath $SourceTask -Destination (Join-Path $VolumeRoot "TASK.md")

        $PreClass = Get-WorkspaceRootClassification $VolumeRoot
        if (@($PreClass.payload).Count -ne 2 -or
            @($PreClass.result).Count -ne 0 -or
            @($PreClass.unexpected).Count -ne 0) {
            throw "SCIENTIFIC_VOLUME_PRESTATE_DRIFT"
        }
        if ((Get-Sha256 (Join-Path $VolumeRoot "input.json")) -ne $ExpectedInputSha256) {
            throw "VOLUME_INPUT_HASH_DRIFT"
        }
        if ((Get-Sha256 (Join-Path $VolumeRoot "TASK.md")) -ne $ExpectedTaskSha256) {
            throw "VOLUME_TASK_HASH_DRIFT"
        }

        $ResultPath = Join-Path $VolumeRoot "result.json"
        $TomlResultPath = $ResultPath.Replace("\", "\\")
        $ConfigPath = Join-Path $LocalRoot "config.toml"
        $config = @"
default_permissions = "$ProfileId"

[windows]
sandbox = "elevated"

[permissions.$ProfileId]
description = "G2E P5A D2-S3 scientific isolated-volume authority"

[permissions.$ProfileId.filesystem]
":root" = "read"
"$TomlResultPath" = "write"

[permissions.$ProfileId.network]
enabled = false
"@
        [IO.File]::WriteAllText(
            $ConfigPath,
            (Convert-ToLfText $config) + [char]10,
            [Text.UTF8Encoding]::new($false)
        )
        $ConfigHash = Get-Sha256 $ConfigPath

        $DefaultAuth = Join-Path $env:USERPROFILE ".codex\auth.json"
        if (-not (Test-Path -LiteralPath $DefaultAuth -PathType Leaf)) {
            throw "DEFAULT_AUTH_MISSING"
        }
        Copy-Item -LiteralPath $DefaultAuth -Destination (Join-Path $CodexHome "auth.json")
        Copy-Item -LiteralPath $ConfigPath -Destination (Join-Path $CodexHome "config.toml")

        $Runner = Join-Path $ProjectRoot "scripts\g2e\p5a_d2s3_scientific_runner.py"
        $RunnerArgs = @(
            $Runner,
            "--project-root", $ProjectRoot,
            "--local-root", $LocalRoot,
            "--expected-head", $Head,
            "--workspace", $VolumeRoot,
            "--config", $ConfigPath,
            "--expected-config-sha256", $ConfigHash,
            "--codex-home", $CodexHome,
            "--evidence-dir", $EvidenceDir,
            "--codex", $CodexExe,
            "--execution-config-hash", $Lock.execution_config_hash,
            "--r2-evidence", $R2Evidence
        )
        $RunnerNative = Invoke-NativeCaptured -FilePath $PythonExe -Arguments $RunnerArgs
        $RunnerOutput = $RunnerNative.Output
        $RunnerExit = $RunnerNative.ExitCode
        $Report.runner_exit_code = $RunnerExit
        if ($RunnerNative.Text) { Write-Host $RunnerNative.Text }

        $RunnerEvidence = Join-Path $EvidenceDir "P5A_D2S3_SCIENTIFIC_RUNNER_EVIDENCE.json"
        $Marker = Join-Path $EvidenceDir "P5A_D2S3_TURN_START_SENT.marker"

        if (Test-Path -LiteralPath $RunnerEvidence -PathType Leaf) {
            $RunnerData = Get-Content -LiteralPath $RunnerEvidence -Raw | ConvertFrom-Json
            $Report.runner_evidence_sha256 = (Get-Sha256 $RunnerEvidence).ToLowerInvariant()
            $Report.scientific_attempt_consumed = [bool](Get-OptionalProperty $RunnerData "scientific_attempt_consumed" $false)
            $Report.turn_start_request_sent = [bool](Get-OptionalProperty $RunnerData "turn_start_request_sent" $false)
            $Report.turn_start_accepted = [bool](Get-OptionalProperty $RunnerData "turn_start_accepted" $false)
            $Report.turn_id = Get-OptionalProperty $RunnerData "turn_id" $null
            $Report.result_exists = [bool](Get-OptionalProperty $RunnerData "result_exists" $false)
            $Report.result_sha256 = Get-OptionalProperty $RunnerData "result_sha256" $null
            $Report.diagnostic = Get-OptionalProperty $RunnerData "driver_exception" $null
        }

        if (Test-Path -LiteralPath $Marker -PathType Leaf) {
            if (-not (Test-Path -LiteralPath $RunnerEvidence -PathType Leaf)) {
                throw "ATTEMPT_CONSUMED_BUT_RUNNER_EVIDENCE_MISSING"
            }

            $RunnerData = Get-Content -LiteralPath $RunnerEvidence -Raw | ConvertFrom-Json
            $ProtocolPath = [string](Get-OptionalProperty $RunnerData "protocol_file" "")
            if ([string]::IsNullOrWhiteSpace($ProtocolPath)) {
                throw "PROTOCOL_PATH_MISSING_AFTER_ATTEMPT_CONSUMPTION"
            }

            $Verifier = Join-Path $ProjectRoot "scripts\g2e\p5a_d2s3_scientific_verify.py"
            $VerificationPath = Join-Path $VerificationDir "P5A_D2S3_SCIENTIFIC_VERIFICATION.json"
            $VerifierArgs = @(
                $Verifier,
                "--evidence", $RunnerEvidence,
                "--protocol", $ProtocolPath,
                "--marker", $Marker,
                "--workspace", $VolumeRoot,
                "--execution-config-hash", $Lock.execution_config_hash,
                "--output", $VerificationPath
            )
            $VerifierNative = Invoke-NativeCaptured -FilePath $PythonExe -Arguments $VerifierArgs
            $VerifierOutput = $VerifierNative.Output
            $VerifierExit = $VerifierNative.ExitCode
            $Report.verifier_exit_code = $VerifierExit
            if ($VerifierNative.Text) { Write-Host $VerifierNative.Text }

            if ($VerifierExit -ne 0 -or -not (Test-Path -LiteralPath $VerificationPath -PathType Leaf)) {
                $Report.status = "SCIENTIFIC_EVIDENCE_INVALID"
                $Report.diagnostic = "INDEPENDENT_VERIFIER_FAILED"
                $FinalExitCode = 2
            }
            else {
                $Verification = Get-Content -LiteralPath $VerificationPath -Raw | ConvertFrom-Json
                $Report.verification_sha256 = (Get-Sha256 $VerificationPath).ToLowerInvariant()
                $Report.metrics = $Verification.metrics
                $Report.adjudication_inputs = $Verification.adjudication_inputs
                $Report.status = "SCIENTIFIC_EVIDENCE_READY_FOR_ADJUDICATION"
                $FinalExitCode = 0
            }
        }
        else {
            $Report.scientific_attempt_consumed = $false
            $Report.status = "SCIENTIFIC_DISPATCH_BLOCKED_NO_ATTEMPT_CONSUMED"
            if ([string]::IsNullOrWhiteSpace([string]$Report.diagnostic)) {
                if ($RunnerNative.Text) {
                    $Report.diagnostic = $RunnerNative.Text
                }
                else {
                    $Report.diagnostic = "PRE_DISPATCH_BLOCKED"
                }
            }
            if ($RunnerExit -eq 0) { $FinalExitCode = 1 } else { $FinalExitCode = $RunnerExit }
        }
    }
    catch {
        $Report.status = "SCIENTIFIC_COLLECTION_BLOCKED"
        $Report.diagnostic = $_.Exception.Message
        $FinalExitCode = 1
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
                $Report.status = "SCIENTIFIC_EVIDENCE_INVALID"
                $Report.diagnostic = "VHDX_CLEANUP_VERIFICATION_FAILED"
                $FinalExitCode = 2
            }
        }
        catch {
            $Report.cleanup.cleanup_error = $_.Exception.Message
            $Report.status = "SCIENTIFIC_EVIDENCE_INVALID"
            $Report.diagnostic = "VHDX_CLEANUP_EXCEPTION"
            $FinalExitCode = 2
        }
    }
    else {
        $Report.cleanup.attached_before_cleanup = $false
        $Report.cleanup.attached_after_cleanup = $false
        $Report.cleanup.cleanup_action = "NOT_ATTACHED"
    }

    try {
        Write-JsonFile $ReportPath $Report
    }
    catch {
        Write-Error "SCIENTIFIC_REPORT_WRITE_FAILED:$($_.Exception.Message)"
        $FinalExitCode = 3
    }
}
# PROTECTED_SCIENTIFIC_VHDX_BODY_END

Write-Host ""
Write-Host "=== D2-S3 SCIENTIFIC EXECUTION COMPLETE ==="
Write-Host "STATUS       : $($Report.status)"
Write-Host "ATTEMPT USED : $($Report.scientific_attempt_consumed)"
Write-Host "TURN SENT    : $($Report.turn_start_request_sent)"
Write-Host "VHDX AFTER   : $($Report.cleanup.attached_after_cleanup)"
Write-Host "REPORT JSON  : $ReportPath"

exit $FinalExitCode
