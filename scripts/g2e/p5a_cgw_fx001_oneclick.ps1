param(
    [string]$ProjectRoot = "",
    [string]$PythonExe = "",
    [string]$CodexExe = "",
    [string]$GitExe = "",
    [string]$CgwBinary = "",
    [string]$BridgeHome = "",
    [string]$LauncherData = "",
    [string]$HandoffConfig = "",
    [string]$HandoffDiagnostic = "",
    [switch]$ElevatedChild,
    [switch]$PreflightOnly
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
Set-StrictMode -Version Latest

$StudyId = "p5a-cgw-v4-p5-fx-001-functional-qualification"
$AttemptId = "p5a-cgw-v4-p5-fx-001-attempt-001"
$ExecutionConfigCanonicalSha = "b7097e8a63607e33f520ab370e48106fc7234f782204e3c366be409b5b594ab8"
$ExpectedInputSha = "A176454229FEEF1CE8BD7EAB1EA79FBFEFF07C229C88123EDF862FEA9160EEF6"
$ExpectedTaskSha = "4C4ABA6A82D540440DFEF725B2568AFDEF4BE3B26C3E4E84E2B34C54E6DD460E"
$ExpectedCodexSha = "A337B7433EBB351C0165DD074CF2500A20FCA9CEAB3680A71DF593653BF70DC8"
$ProfileId = "g2e_p5a_cgw_fx001"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "FILE_NOT_FOUND:$Path" }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-GitBlob([string]$Repo, [string]$Path) {
    $v = (& $GitExe -C $Repo rev-parse "HEAD:$Path").Trim()
    if ($LASTEXITCODE -ne 0) { throw "GIT_BLOB_FAILED:$Path" }
    return $v
}

function Assert-ExecutionSourceClean([string]$Repo) {
    & $GitExe -C $Repo diff --quiet --no-ext-diff --
    if ($LASTEXITCODE -ne 0) { throw "TRACKED_WORKTREE_DIRTY" }

    & $GitExe -C $Repo diff --cached --quiet --no-ext-diff --
    if ($LASTEXITCODE -ne 0) { throw "TRACKED_INDEX_DIRTY" }

    $CriticalPrefixes = @(
        "scripts/g2e/",
        "g2e/docs/",
        "g2e/config/",
        "src/",
        "tests/g2e/",
        ".github/workflows/"
    )
    $Untracked = @(& $GitExe -C $Repo ls-files --others --exclude-standard)
    if ($LASTEXITCODE -ne 0) { throw "GIT_UNTRACKED_SCAN_FAILED" }

    foreach ($Path in $Untracked) {
        $Normalized = ([string]$Path).Replace("\", "/")
        foreach ($Prefix in $CriticalPrefixes) {
            if ($Normalized.StartsWith($Prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
                throw "CRITICAL_UNTRACKED_SOURCE:$Normalized"
            }
        }
    }
}

function Convert-ToLfText([string]$Text) {
    return ($Text -replace "\r\n", "\n" -replace "\r", "\n").TrimEnd("\n")
}

function Get-FreeDriveLetter {
    $used = @(Get-Volume | Where-Object DriveLetter | ForEach-Object { $_.DriveLetter.ToString().ToUpperInvariant() })
    foreach ($code in ([int][char]'R')..([int][char]'Z')) {
        $letter = ([char]$code).ToString()
        if ($used -notcontains $letter) { return $letter }
    }
    throw "NO_FREE_DRIVE_LETTER"
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
} else {
    $ProjectRoot = (Resolve-Path $ProjectRoot).Path
}
$ThisScript = $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if ([string]::IsNullOrWhiteSpace($HandoffDiagnostic)) {
    $HandoffDiagnostic = Join-Path $ProjectRoot "g2e\.local\P5A-CGW-FX001-V4-001-HANDOFF.json"
}
if ([string]::IsNullOrWhiteSpace($HandoffConfig)) {
    $HandoffConfig = Join-Path $ProjectRoot "g2e\.local\P5A-CGW-FX001-V4-001-HANDOFF-CONFIG.json"
}

if ($ElevatedChild) {
    trap {
        try {
            $diagParent = Split-Path -Parent $HandoffDiagnostic
            if ($diagParent -and -not (Test-Path -LiteralPath $diagParent)) {
                New-Item -ItemType Directory -Path $diagParent -Force | Out-Null
            }
            $diag = [ordered]@{
                schema = "G2E-P5A-CGW-FX001-HANDOFF-DIAGNOSTIC-v1"
                phase = "ELEVATED_CHILD_PREEXECUTION_OR_EXECUTION"
                exception_type = $_.Exception.GetType().FullName
                message = $_.Exception.Message
                script_stack_trace = $_.ScriptStackTrace
                attempt_consumed_marker_present = $false
            }
            $markerCandidate = Join-Path $ProjectRoot "g2e\.local\P5A-CGW-FX001-V4-001\evidence\attempt_consumed.marker"
            $diag.attempt_consumed_marker_present = [bool](Test-Path -LiteralPath $markerCandidate)
            $diag | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $HandoffDiagnostic -Encoding UTF8
        } catch {}
        exit 97
    }

    if (-not (Test-Path -LiteralPath $HandoffConfig -PathType Leaf)) {
        throw "HANDOFF_CONFIG_MISSING:$HandoffConfig"
    }
    $Handoff = Get-Content -LiteralPath $HandoffConfig -Raw | ConvertFrom-Json
    if ([string]$Handoff.project_root -ne $ProjectRoot) {
        throw "HANDOFF_PROJECT_ROOT_MISMATCH"
    }
    $PythonExe = [string]$Handoff.python_exe
    $CodexExe = [string]$Handoff.codex_exe
    $GitExe = [string]$Handoff.git_exe
    $CgwBinary = [string]$Handoff.cgw_binary
    $BridgeHome = [string]$Handoff.bridge_home
    $LauncherData = [string]$Handoff.launcher_data
}

if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    $PythonExe = (Get-Command python -ErrorAction Stop).Source
}
if ([string]::IsNullOrWhiteSpace($CodexExe)) {
    $CodexExe = (Get-Command codex -ErrorAction Stop).Source
}
if ([string]::IsNullOrWhiteSpace($GitExe)) {
    $GitExe = (Get-Command git -ErrorAction Stop).Source
}

$LockPath = Join-Path $ProjectRoot "g2e\docs\P5A_CGW_FX001_EXECUTION_LOCK_V2R5.json"
$AdmissionScript = Join-Path $ProjectRoot "scripts\g2e\p5a_cgw_fx001_admission.py"
$RunnerScript = Join-Path $ProjectRoot "scripts\g2e\p5a_cgw_fx001_runner.py"
$VerifierScript = Join-Path $ProjectRoot "scripts\g2e\p5a_cgw_fx001_verify.py"

if (-not (Test-Path -LiteralPath $LockPath)) { throw "DISPATCH_LOCK_V2_MISSING" }
$Lock = Get-Content -LiteralPath $LockPath -Raw | ConvertFrom-Json
if ($Lock.status -ne "DISPATCH_AUTHORIZED_EXECUTION_LOCK_V2R5") { throw "DISPATCH_LOCK_STATUS_INVALID" }
if ($Lock.authorization.dispatch_authorized -ne $true) { throw "DISPATCH_NOT_AUTHORIZED" }
if ($Lock.authorization.max_dispatches -ne 1) { throw "DISPATCH_CARDINALITY_DRIFT" }
if ($Lock.attempt_id -ne $AttemptId) { throw "ATTEMPT_ID_DRIFT" }

$ExpectedCgwSha = ([string]$Lock.launcher_identity.expected_sha256).Trim().ToUpperInvariant()
if ($ExpectedCgwSha.Length -ne 64 -or $ExpectedCgwSha -match "[^A-F0-9]") {
    throw "LOCK_CGW_LAUNCHER_SHA256_INVALID:$ExpectedCgwSha"
}
if ((Get-GitBlob $ProjectRoot "scripts/g2e/p5a_cgw_fx001_admission.py") -ne $Lock.components.admission_blob) { throw "ADMISSION_BLOB_DRIFT" }
if ((Get-GitBlob $ProjectRoot "scripts/g2e/p5a_cgw_fx001_runner.py") -ne $Lock.components.runner_blob) { throw "RUNNER_BLOB_DRIFT" }
if ((Get-GitBlob $ProjectRoot "scripts/g2e/p5a_cgw_fx001_verify.py") -ne $Lock.components.verifier_blob) { throw "VERIFIER_BLOB_DRIFT" }
if ((Get-GitBlob $ProjectRoot "scripts/g2e/p5a_cgw_fx001_oneclick.ps1") -ne $Lock.components.oneclick_blob) { throw "ONECLICK_BLOB_DRIFT" }
if ((Get-GitBlob $ProjectRoot "g2e/config/P5A_CGW_FX001_EXECUTION_CONFIG.json") -ne $Lock.execution_config.git_blob) { throw "EXECUTION_CONFIG_BLOB_DRIFT" }
Assert-ExecutionSourceClean $ProjectRoot

if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) { throw "PYTHON_NOT_FOUND" }
if (-not (Test-Path -LiteralPath $CodexExe -PathType Leaf)) { throw "CODEX_COMMAND_NOT_FOUND" }
if (-not (Test-Path -LiteralPath $GitExe -PathType Leaf)) { throw "GIT_COMMAND_NOT_FOUND" }
if ((Get-Sha256 $CodexExe) -ne $ExpectedCodexSha) { throw "CODEX_BINARY_HASH_DRIFT" }

if (-not $BridgeHome) {
    if ($env:CODEX_CHATGPT_WEB_HOME) { $BridgeHome = $env:CODEX_CHATGPT_WEB_HOME }
    else { $BridgeHome = Join-Path $HOME ".codex-chatgpt-web" }
}
if (-not $LauncherData) {
    if ($env:CODEX_WEB_GPT_LAUNCHER_DATA_DIR) { $LauncherData = $env:CODEX_WEB_GPT_LAUNCHER_DATA_DIR }
    else { $LauncherData = Join-Path $env:APPDATA "Codex Web GPT" }
}

$BridgeConfig = Join-Path $BridgeHome "config.json"
$DiagnosticsRoot = Join-Path $BridgeHome "diagnostics\browser-turns"
$LauncherLog = Join-Path $LauncherData "logs\launcher.jsonl"
if (-not (Test-Path -LiteralPath $BridgeConfig)) { throw "CGW_CONFIG_NOT_FOUND" }
if (-not (Test-Path -LiteralPath $LauncherLog)) { throw "CGW_LAUNCHER_LOG_NOT_FOUND" }

$BridgeObject = Get-Content -LiteralPath $BridgeConfig -Raw | ConvertFrom-Json
if ([string]$BridgeObject.host -ne "127.0.0.1" -or [int]$BridgeObject.port -ne 17841) { throw "CGW_LOOPBACK_ROUTE_DRIFT" }

if ([string]::IsNullOrWhiteSpace($CgwBinary)) {
    try {
        $InstallRegistry = "HKCU:\Software\d1a6026a-6210-588e-9a2b-da3936f94e02"
        $InstallLocation = [string](Get-ItemPropertyValue -LiteralPath $InstallRegistry -Name "InstallLocation")
        $Candidate = Join-Path $InstallLocation "Codex Web GPT.exe"
        if (Test-Path -LiteralPath $Candidate -PathType Leaf) { $CgwBinary = $Candidate }
    } catch {
        throw "CGW_LAUNCHER_REGISTRY_LOOKUP_FAILED:$($_.Exception.Message)"
    }
}
if ([string]::IsNullOrWhiteSpace($CgwBinary)) { throw "CGW_LAUNCHER_NOT_FOUND" }
if (-not (Test-Path -LiteralPath $CgwBinary -PathType Leaf)) { throw "CGW_LAUNCHER_NOT_FOUND:$CgwBinary" }
$ObservedCgwSha = Get-Sha256 $CgwBinary
if ($ObservedCgwSha -ne $ExpectedCgwSha) {
    throw "CGW_LAUNCHER_HASH_DRIFT:path=$CgwBinary observed=$ObservedCgwSha expected=$ExpectedCgwSha"
}

$LocalRoot = Join-Path $ProjectRoot "g2e\.local\P5A-CGW-FX001-V4-001"
if (Test-Path -LiteralPath $LocalRoot) { throw "FUNCTIONAL_ROOT_ALREADY_EXISTS_FAIL_CLOSED" }

$SourceFixture = Join-Path $ProjectRoot "g2e\.local\P5A-D2S1\execution\P5-FX-001"
$SourceInput = Join-Path $SourceFixture "input.json"
$SourceTask = Join-Path $SourceFixture "TASK.md"
if ((Get-Sha256 $SourceInput) -ne $ExpectedInputSha) { throw "SOURCE_INPUT_HASH_DRIFT" }
if ((Get-Sha256 $SourceTask) -ne $ExpectedTaskSha) { throw "SOURCE_TASK_HASH_DRIFT" }

$DefaultAuth = Join-Path $env:USERPROFILE ".codex\auth.json"
if (-not (Test-Path -LiteralPath $DefaultAuth -PathType Leaf)) { throw "DEFAULT_AUTH_MISSING" }

Write-Host ""
Write-Host "=== P5A-CGW PRE-UAC PREFLIGHT ===" -ForegroundColor Cyan
Write-Host "STATUS: PASS"
Write-Host ("LOCK: " + $Lock.status)
Write-Host ("ATTEMPT: " + $AttemptId)
Write-Host ("PYTHON: " + $PythonExe)
Write-Host ("CODEX: " + $CodexExe)
Write-Host ("GIT: " + $GitExe)
Write-Host ("CGW: " + $CgwBinary)
Write-Host ("BRIDGE_HOME: " + $BridgeHome)
Write-Host ("LAUNCHER_DATA: " + $LauncherData)
Write-Host "ATTEMPT_CONSUMED: False"
Write-Host "MODEL_TURN_SENT: False"

if ($PreflightOnly) {
    Write-Host "PREFLIGHT_ONLY: PASS - no UAC, no VHDX, no LocalRoot, no marker, no model turn." -ForegroundColor Yellow
    return
}

if (-not (Test-IsAdministrator)) {
    Write-Host ""
    Write-Host "Administrator elevation is required for the isolated P5A-CGW VHDX."
    $handoffParent = Split-Path -Parent $HandoffConfig
    if ($handoffParent -and -not (Test-Path -LiteralPath $handoffParent)) {
        New-Item -ItemType Directory -Path $handoffParent -Force | Out-Null
    }
    $handoffPayload = [ordered]@{
        schema = "G2E-P5A-CGW-FX001-HANDOFF-CONFIG-v1"
        project_root = $ProjectRoot
        python_exe = $PythonExe
        codex_exe = $CodexExe
        git_exe = $GitExe
        cgw_binary = $CgwBinary
        bridge_home = $BridgeHome
        launcher_data = $LauncherData
    }
    $handoffPayload | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $HandoffConfig -Encoding UTF8

    if (Test-Path -LiteralPath $HandoffDiagnostic -PathType Leaf) {
        Remove-Item -LiteralPath $HandoffDiagnostic -Force
    }

    $ElevatedArgs = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $ThisScript,
        "-ProjectRoot", $ProjectRoot,
        "-HandoffConfig", $HandoffConfig,
        "-HandoffDiagnostic", $HandoffDiagnostic,
        "-ElevatedChild"
    )
    try {
        $p = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $ElevatedArgs -Wait -PassThru
    } catch {
        Write-Host ("UAC_HANDOFF_ERROR: " + $_.Exception.Message) -ForegroundColor Red
        throw
    }
    if ($p.ExitCode -ne 0) {
        Write-Host ("ELEVATED_CHILD_EXIT_CODE: " + $p.ExitCode) -ForegroundColor Red
        if (Test-Path -LiteralPath $HandoffDiagnostic -PathType Leaf) {
            Write-Host "=== ELEVATED CHILD DIAGNOSTIC ===" -ForegroundColor Red
            Get-Content -LiteralPath $HandoffDiagnostic -Raw
        }
    }
    exit $p.ExitCode
}

if (-not $ElevatedChild) {
    Write-Host "RUNNING_ALREADY_ELEVATED_WITHOUT_HANDOFF: accepted; exact preflight passed." -ForegroundColor Yellow
}

$VolumeDir = Join-Path $LocalRoot "volume"
$CodexHome = Join-Path $LocalRoot "codex-home"
$EvidenceDir = Join-Path $LocalRoot "evidence"
$ReportDir = Join-Path $LocalRoot "report"
$VerificationDir = Join-Path $LocalRoot "verification"
New-Item -ItemType Directory -Path $VolumeDir,$CodexHome,$ReportDir,$VerificationDir -Force | Out-Null

$VhdxPath = Join-Path $VolumeDir "P5A-CGW-FX001.vhdx"
$DiskpartScript = Join-Path $VolumeDir "create_vhdx.diskpart.txt"
$HealthPath = Join-Path $ReportDir "CGW_HEALTH_SAFE.json"
$AdmissionPath = Join-Path $ReportDir "predispatch_admission.json"
$RunnerEvidence = Join-Path $EvidenceDir "runner_evidence.json"
$ProtocolPath = Join-Path $EvidenceDir "codex_protocol.jsonl"
$RoutePath = Join-Path $EvidenceDir "cgw_route_evidence.jsonl"
$MarkerPath = Join-Path $EvidenceDir "attempt_consumed.marker"
$VerifyPath = Join-Path $VerificationDir "verification.json"
$SummaryPath = Join-Path $ReportDir "P5A_CGW_FX001_EXECUTION_REPORT.json"

$Summary = [ordered]@{
    schema = "G2E-P5A-CGW-FX001-EXECUTION-REPORT-v1"
    status = "STARTED"
    study_id = $StudyId
    attempt_id = $AttemptId
    attempt_consumed = $false
    runner_exit_code = $null
    verifier_exit_code = $null
    verification_sha256 = $null
    cleanup = [ordered]@{
        attached_before_cleanup = $null
        cleanup_action = "NOT_ATTACHED"
        attached_after_cleanup = $null
        cleanup_error = $null
    }
}

$FinalExit = 0
$VhdxMayBeAttached = $false

try {
    try {
        $DriveLetter = Get-FreeDriveLetter
        $VolumeRoot = $DriveLetter + ":\"
        $diskpart = @(
            "create vdisk file=""$VhdxPath"" maximum=128 type=expandable",
            "select vdisk file=""$VhdxPath""",
            "attach vdisk",
            "create partition primary",
            "format fs=ntfs quick label=G2ECGWFX01",
            "assign letter=$DriveLetter"
        )
        [IO.File]::WriteAllLines($DiskpartScript, $diskpart, [Text.ASCIIEncoding]::new())
        $VhdxMayBeAttached = $true
        & diskpart.exe /s $DiskpartScript | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "DISKPART_FAILED" }
        if (-not (Test-Path -LiteralPath $VolumeRoot -PathType Container)) { throw "VHDX_VOLUME_MISSING" }

        $SourceFixture = Join-Path $ProjectRoot "g2e\.local\P5A-D2S1\execution\P5-FX-001"
        $SourceInput = Join-Path $SourceFixture "input.json"
        $SourceTask = Join-Path $SourceFixture "TASK.md"
        if ((Get-Sha256 $SourceInput) -ne $ExpectedInputSha) { throw "SOURCE_INPUT_HASH_DRIFT" }
        if ((Get-Sha256 $SourceTask) -ne $ExpectedTaskSha) { throw "SOURCE_TASK_HASH_DRIFT" }
        Copy-Item -LiteralPath $SourceInput -Destination (Join-Path $VolumeRoot "input.json")
        Copy-Item -LiteralPath $SourceTask -Destination (Join-Path $VolumeRoot "TASK.md")

        $ResultPath = Join-Path $VolumeRoot "result.json"
        $TomlResultPath = $ResultPath.Replace("\", "\\")
        $ConfigPath = Join-Path $LocalRoot "codex-config.toml"
        $config = @"
model = "chatgpt-web/high"
model_provider = "openai"
openai_base_url = "http://127.0.0.1:17841/v1"
default_permissions = "$ProfileId"

[windows]
sandbox = "elevated"

[permissions.$ProfileId]
description = "G2E P5A-CGW P5-FX-001 bounded functional authority"

[permissions.$ProfileId.filesystem]
":root" = "read"
"$TomlResultPath" = "write"

[permissions.$ProfileId.network]
enabled = false
"@
        [IO.File]::WriteAllText($ConfigPath, (Convert-ToLfText $config) + [char]10, [Text.UTF8Encoding]::new($false))

        $DefaultAuth = Join-Path $env:USERPROFILE ".codex\auth.json"
        if (-not (Test-Path -LiteralPath $DefaultAuth)) { throw "DEFAULT_AUTH_MISSING" }
        Copy-Item -LiteralPath $DefaultAuth -Destination (Join-Path $CodexHome "auth.json")
        Copy-Item -LiteralPath $ConfigPath -Destination (Join-Path $CodexHome "config.toml")

        $Health = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:17841/healthz" -TimeoutSec 3
        $Health | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $HealthPath -Encoding UTF8

        $AdmissionArgs = @(
            $AdmissionScript,
            "--bridge-config", $BridgeConfig,
            "--health-json", $HealthPath,
            "--codex-config", $ConfigPath,
            "--cgw-binary", $CgwBinary,
            "--codex-binary", $CodexExe,
            "--workspace", $VolumeRoot,
            "--diagnostics-root", $DiagnosticsRoot,
            "--launcher-log", $LauncherLog,
            "--marker", $MarkerPath,
            "--output", $AdmissionPath
        )
        & $PythonExe @AdmissionArgs
        if ($LASTEXITCODE -ne 0) {
            $Summary.status = "PREDISPATCH_BLOCKED_NO_ATTEMPT_CONSUMPTION"
            throw "PREDISPATCH_ADMISSION_BLOCKED"
        }

        $RunnerArgs = @(
            $RunnerScript,
            "--workspace", $VolumeRoot,
            "--codex-home", $CodexHome,
            "--codex", $CodexExe,
            "--admission", $AdmissionPath,
            "--diagnostics-root", $DiagnosticsRoot,
            "--launcher-log", $LauncherLog,
            "--evidence-dir", $EvidenceDir,
            "--execution-config-hash", $ExecutionConfigCanonicalSha
        )
        & $PythonExe @RunnerArgs
        $Summary.runner_exit_code = $LASTEXITCODE

        if (Test-Path -LiteralPath $RunnerEvidence) {
            $Runner = Get-Content -LiteralPath $RunnerEvidence -Raw | ConvertFrom-Json
            $Summary.attempt_consumed = [bool]$Runner.attempt_consumed
        }
        if ($Summary.runner_exit_code -ne 0 -and -not $Summary.attempt_consumed) {
            $Summary.status = "RUNNER_BLOCKED_NO_ATTEMPT_CONSUMPTION"
            throw "RUNNER_BLOCKED_BEFORE_ATTEMPT_CONSUMPTION"
        }

        $VerifierArgs = @(
            $VerifierScript,
            "--runner", $RunnerEvidence,
            "--protocol", $ProtocolPath,
            "--route", $RoutePath,
            "--marker", $MarkerPath,
            "--admission", $AdmissionPath,
            "--workspace", $VolumeRoot,
            "--execution-config-hash", $ExecutionConfigCanonicalSha,
            "--output", $VerifyPath
        )
        & $PythonExe @VerifierArgs
        $Summary.verifier_exit_code = $LASTEXITCODE

        if (Test-Path -LiteralPath $VerifyPath) {
            $Summary.verification_sha256 = (Get-Sha256 $VerifyPath).ToLowerInvariant()
            $Verification = Get-Content -LiteralPath $VerifyPath -Raw | ConvertFrom-Json
            $Summary.metrics = $Verification.metrics
            $Summary.adjudication_inputs = $Verification.adjudication_inputs
        }
        $Summary.status = "FUNCTIONAL_EVIDENCE_READY_FOR_ADJUDICATION"
    } catch {
        if ($Summary.status -eq "STARTED") { $Summary.status = "EXECUTION_WRAPPER_ERROR" }
        $Summary.diagnostic = $_.Exception.Message
        $FinalExit = 2
    }
} finally {
    if ($VhdxMayBeAttached -and (Test-Path -LiteralPath $VhdxPath -PathType Leaf)) {
        try {
            $before = Get-DiskImage -ImagePath $VhdxPath -ErrorAction Stop
            $Summary.cleanup.attached_before_cleanup = [bool]$before.Attached
            if ($before.Attached) {
                Dismount-DiskImage -ImagePath $VhdxPath -ErrorAction Stop | Out-Null
                $Summary.cleanup.cleanup_action = "DISMOUNTED"
            }
            $after = Get-DiskImage -ImagePath $VhdxPath -ErrorAction Stop
            $Summary.cleanup.attached_after_cleanup = [bool]$after.Attached
            if ($after.Attached) {
                $Summary.cleanup.cleanup_error = "VHDX_STILL_ATTACHED"
                $FinalExit = 2
            }
        } catch {
            $Summary.cleanup.cleanup_error = $_.Exception.Message
            $FinalExit = 2
        }
    }
    $Summary | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $SummaryPath -Encoding UTF8
}

Write-Host ""
Write-Host "=== P5A-CGW FX001 EXECUTION ===" -ForegroundColor Cyan
Write-Host ("STATUS: " + $Summary.status)
Write-Host ("ATTEMPT_CONSUMED: " + $Summary.attempt_consumed)
Write-Host ("REPORT: " + $SummaryPath)
exit $FinalExit
