param(
    [ValidateSet("Launcher", "Elevated")]
    [string]$Mode = "Launcher",
    [string]$ProjectRoot = "",
    [string]$PythonExe = "",
    [string]$CodexExe = "",
    [string]$ReportRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedCodexSha256 = "A337B7433EBB351C0165DD074CF2500A20FCA9CEAB3680A71DF593653BF70DC8"
$DiagnosticLockName = "P5A_D2S2_ELEVATION_BOOTSTRAP_DIAGNOSTIC_LOCK.json"
$ExistingD2S2LockName = "P5A_D2S2_ONECLICK_LOCK.json"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-UtcNow {
    return [DateTime]::UtcNow.ToString("o")
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Set-Property($Object, [string]$Name, $Value) {
    if ($null -ne $Object.PSObject.Properties[$Name]) {
        $Object.$Name = $Value
    }
    else {
        $Object | Add-Member -MemberType NoteProperty -Name $Name -Value $Value
    }
}

function Set-Gate($Report, [string]$Name, [bool]$Pass, [string]$Detail) {
    $gate = [pscustomobject][ordered]@{
        pass = $Pass
        detail = $Detail
    }
    if ($null -ne $Report.gates.PSObject.Properties[$Name]) {
        $Report.gates.$Name = $gate
    }
    else {
        $Report.gates | Add-Member -MemberType NoteProperty -Name $Name -Value $gate
    }
}

function Write-JsonFile([string]$Path, $Object) {
    $json = $Object | ConvertTo-Json -Depth 16
    [IO.File]::WriteAllText($Path, $json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
}

function Write-MarkdownFile([string]$Path, $Report) {
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("# G2E P5A D2-S2 Elevation Bootstrap Diagnostic")
    $lines.Add("")
    $lines.Add("- status: $($Report.status)")
    $lines.Add("- phase: $($Report.phase)")
    $lines.Add("- project_root: $($Report.project_root)")
    $lines.Add("- source_head: $($Report.source_head)")
    $lines.Add("- diagnostic_candidate_sha: $($Report.diagnostic_candidate_sha)")
    $lines.Add("- launcher_admin: $($Report.launcher_admin)")
    $lines.Add("- elevated_process_started: $($Report.elevated_process_started)")
    $lines.Add("- elevated_admin: $($Report.elevated_admin)")
    $lines.Add("- elevated_exit_code: $($Report.elevated_exit_code)")
    $lines.Add("- scientific_attempt_consumed: false")
    $lines.Add("- model_turn_executed: false")
    $lines.Add("")
    $lines.Add("## Gates")
    $lines.Add("")
    foreach ($prop in $Report.gates.PSObject.Properties) {
        $lines.Add("- $($prop.Name): pass=$($prop.Value.pass) detail=$($prop.Value.detail)")
    }
    $lines.Add("")
    $lines.Add("## Diagnostic")
    $lines.Add("")
    $lines.Add("$($Report.diagnostic)")
    $lines.Add("")
    [IO.File]::WriteAllLines($Path, $lines, [Text.UTF8Encoding]::new($false))
}

function Save-Report($Report, [string]$JsonPath, [string]$MdPath) {
    Set-Property $Report "updated_utc" (Get-UtcNow)
    Write-JsonFile $JsonPath $Report
    Write-MarkdownFile $MdPath $Report
}

function Read-Report([string]$JsonPath) {
    return Get-Content -LiteralPath $JsonPath -Raw | ConvertFrom-Json
}

function Quote-ProcessArgument([string]$Value) {
    return '"' + $Value.Replace('"', '\"') + '"'
}

function Invoke-GitCapture([string]$Root, [string[]]$GitArgs) {
    $output = & git -C $Root @GitArgs 2>&1
    $exitCode = $LASTEXITCODE
    return [pscustomobject]@{
        exit_code = $exitCode
        output = (($output | Out-String).Trim())
    }
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
}

if ([string]::IsNullOrWhiteSpace($ReportRoot)) {
    $ReportRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S2-BOOTSTRAP\report"
}

$ReportJson = Join-Path $ReportRoot "P5A_D2S2_ELEVATION_BOOTSTRAP_REPORT.json"
$ReportMd = Join-Path $ReportRoot "P5A_D2S2_ELEVATION_BOOTSTRAP_REPORT.md"

if ($Mode -eq "Launcher") {
    try {
        New-Item -ItemType Directory -Path $ReportRoot -Force | Out-Null

        if ([string]::IsNullOrWhiteSpace($PythonExe)) {
            $PythonExe = (Get-Command python -ErrorAction Stop).Source
        }
        if ([string]::IsNullOrWhiteSpace($CodexExe)) {
            $CodexExe = Join-Path $env:LOCALAPPDATA "Programs\OpenAI\Codex\bin\codex.exe"
        }

        $preStatus = Invoke-GitCapture $ProjectRoot @("status", "--porcelain")
        $preStatusLines = @()
        if ($preStatus.exit_code -eq 0 -and -not [string]::IsNullOrWhiteSpace($preStatus.output)) {
            $preStatusLines = @($preStatus.output -split "\r?\n" | Where-Object {
                $_ -and ($_ -notmatch 'g2e[\\/]\.local[\\/]')
            })
        }

        $report = [pscustomobject][ordered]@{
            schema = "G2E-P5A-D2S2-ELEVATION-BOOTSTRAP-DIAGNOSTIC-v1"
            status = "LAUNCHER_READY"
            phase = "UNELEVATED"
            started_utc = Get-UtcNow
            updated_utc = Get-UtcNow
            project_root = $ProjectRoot
            script_path = $MyInvocation.MyCommand.Path
            report_json = $ReportJson
            report_md = $ReportMd
            launcher_pid = $PID
            launcher_admin = (Test-IsAdministrator)
            powershell_version = $PSVersionTable.PSVersion.ToString()
            python_exe = $PythonExe
            codex_exe = $CodexExe
            source_head = $null
            diagnostic_candidate_sha = $null
            elevated_process_started = $false
            elevated_admin = $null
            elevated_pid = $null
            elevated_exit_code = $null
            pre_uac_worktree_status_exit_code = $preStatus.exit_code
            pre_uac_worktree_nonlocal_entries = $preStatusLines
            gates = [pscustomobject][ordered]@{}
            diagnostic = "UNELEVATED_REPORT_CREATED_BEFORE_UAC"
            scientific_attempt_consumed = $false
            model_turn_executed = $false
        }
        Save-Report $report $ReportJson $ReportMd

        if (Test-IsAdministrator) {
            $report.status = "LAUNCHER_BLOCKED"
            $report.diagnostic = "LAUNCHER_WAS_ALREADY_ADMIN; RUN_ELEVATED_MODE_DIRECTLY_IS_NOT_AUTHORIZED"
            Save-Report $report $ReportJson $ReportMd
            Write-Host "REPORT JSON: $ReportJson"
            exit 2
        }

        $argLine = @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", (Quote-ProcessArgument $MyInvocation.MyCommand.Path),
            "-Mode", "Elevated",
            "-ProjectRoot", (Quote-ProcessArgument $ProjectRoot),
            "-PythonExe", (Quote-ProcessArgument $PythonExe),
            "-CodexExe", (Quote-ProcessArgument $CodexExe),
            "-ReportRoot", (Quote-ProcessArgument $ReportRoot)
        ) -join " "

        try {
            $process = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $argLine -Wait -PassThru
        }
        catch {
            $report = Read-Report $ReportJson
            $report.status = "LAUNCHER_BLOCKED"
            $report.phase = "UNELEVATED"
            $report.elevated_process_started = $false
            $report.diagnostic = "UAC_OR_ELEVATED_PROCESS_START_FAILED:$($_.Exception.Message)"
            Save-Report $report $ReportJson $ReportMd
            Write-Host "REPORT JSON: $ReportJson"
            exit 3
        }

        $report = Read-Report $ReportJson
        $report.elevated_exit_code = $process.ExitCode
        if ($report.status -eq "ELEVATED_ENTERED") {
            $report.status = "DIAGNOSTIC_INTERNAL_ERROR"
            $report.diagnostic = "ELEVATED_CHILD_EXITED_WITHOUT_FINAL_ADJUDICATION"
        }
        elseif ($process.ExitCode -ne 0 -and $report.status -eq "DIAGNOSTIC_PASS") {
            $report.status = "DIAGNOSTIC_INTERNAL_ERROR"
            $report.diagnostic = "CHILD_EXIT_NONZERO_AFTER_PASS:$($process.ExitCode)"
        }
        Save-Report $report $ReportJson $ReportMd

        Write-Host ""
        Write-Host "=== D2-S2 ELEVATION BOOTSTRAP DIAGNOSTIC COMPLETE ==="
        Write-Host "STATUS      : $($report.status)"
        Write-Host "REPORT JSON : $ReportJson"
        Write-Host "REPORT MD   : $ReportMd"
        Write-Host "TURN START  : FALSE"
        Write-Host "ATTEMPT USED: FALSE"

        if ($report.status -eq "DIAGNOSTIC_PASS") {
            exit 0
        }
        exit 4
    }
    catch {
        try {
            New-Item -ItemType Directory -Path $ReportRoot -Force | Out-Null
            $fallback = [pscustomobject][ordered]@{
                schema = "G2E-P5A-D2S2-ELEVATION-BOOTSTRAP-DIAGNOSTIC-v1"
                status = "DIAGNOSTIC_INTERNAL_ERROR"
                phase = "UNELEVATED"
                started_utc = Get-UtcNow
                updated_utc = Get-UtcNow
                project_root = $ProjectRoot
                script_path = $MyInvocation.MyCommand.Path
                launcher_pid = $PID
                launcher_admin = (Test-IsAdministrator)
                elevated_process_started = $false
                elevated_admin = $null
                elevated_exit_code = $null
                source_head = $null
                diagnostic_candidate_sha = $null
                gates = [pscustomobject][ordered]@{}
                diagnostic = "UNELEVATED_INTERNAL_ERROR:$($_.Exception.Message)"
                scientific_attempt_consumed = $false
                model_turn_executed = $false
            }
            Save-Report $fallback $ReportJson $ReportMd
            Write-Host "REPORT JSON: $ReportJson"
        }
        catch {
            Write-Error "DIAGNOSTIC_REPORT_WRITE_FAILED:$($_.Exception.Message)"
        }
        exit 5
    }
}

# Elevated mode: enter report-producing code before any diagnostic gate.
try {
    if (-not (Test-Path -LiteralPath $ReportJson)) {
        throw "UNELEVATED_REPORT_MISSING:$ReportJson"
    }

    $report = Read-Report $ReportJson
    $report.phase = "ELEVATED"
    $report.status = "ELEVATED_ENTERED"
    $report.elevated_process_started = $true
    $report.elevated_admin = (Test-IsAdministrator)
    $report.elevated_pid = $PID
    $report.diagnostic = "ELEVATED_CHILD_ENTERED"
    Save-Report $report $ReportJson $ReportMd

    $allPass = $true

    $isAdmin = Test-IsAdministrator
    Set-Gate $report "elevation" $isAdmin ($(if ($isAdmin) { "ADMIN_TOKEN_PRESENT" } else { "ADMIN_TOKEN_MISSING" }))
    if (-not $isAdmin) { $allPass = $false }

    $projectExists = Test-Path -LiteralPath $ProjectRoot -PathType Container
    Set-Gate $report "project_root_exists" $projectExists ($(if ($projectExists) { $ProjectRoot } else { "MISSING:$ProjectRoot" }))
    if (-not $projectExists) { $allPass = $false }

    $diagnosticLockPath = Join-Path $ProjectRoot "g2e\docs\$DiagnosticLockName"
    $existingLockPath = Join-Path $ProjectRoot "g2e\docs\$ExistingD2S2LockName"

    $diagnosticLock = $null
    if (Test-Path -LiteralPath $diagnosticLockPath) {
        try {
            $diagnosticLock = Get-Content -LiteralPath $diagnosticLockPath -Raw | ConvertFrom-Json
            $lockPass = ($diagnosticLock.qualified -eq $true)
            Set-Gate $report "diagnostic_lock" $lockPass ($(if ($lockPass) { "QUALIFIED" } else { "QUALIFIED_FALSE" }))
            if (-not $lockPass) { $allPass = $false }
        }
        catch {
            Set-Gate $report "diagnostic_lock" $false "PARSE_ERROR:$($_.Exception.Message)"
            $allPass = $false
        }
    }
    else {
        Set-Gate $report "diagnostic_lock" $false "MISSING:$diagnosticLockPath"
        $allPass = $false
    }

    $existingLock = $null
    if (Test-Path -LiteralPath $existingLockPath) {
        try {
            $existingLock = Get-Content -LiteralPath $existingLockPath -Raw | ConvertFrom-Json
            $lockPass = ($existingLock.qualified -eq $true)
            Set-Gate $report "existing_d2s2_lock" $lockPass ($(if ($lockPass) { "QUALIFIED" } else { "QUALIFIED_FALSE" }))
            if (-not $lockPass) { $allPass = $false }
        }
        catch {
            Set-Gate $report "existing_d2s2_lock" $false "PARSE_ERROR:$($_.Exception.Message)"
            $allPass = $false
        }
    }
    else {
        Set-Gate $report "existing_d2s2_lock" $false "MISSING:$existingLockPath"
        $allPass = $false
    }

    $headResult = Invoke-GitCapture $ProjectRoot @("rev-parse", "HEAD")
    $headPass = ($headResult.exit_code -eq 0 -and $headResult.output -match '^[0-9a-fA-F]{40}$')
    if ($headPass) {
        $report.source_head = $headResult.output.ToLowerInvariant()
    }
    Set-Gate $report "git_head" $headPass ($(if ($headPass) { $report.source_head } else { "EXIT=$($headResult.exit_code):$($headResult.output)" }))
    if (-not $headPass) { $allPass = $false }

    $statusResult = Invoke-GitCapture $ProjectRoot @("status", "--porcelain")
    $nonlocal = @()
    if ($statusResult.exit_code -eq 0 -and -not [string]::IsNullOrWhiteSpace($statusResult.output)) {
        $nonlocal = @($statusResult.output -split "\r?\n" | Where-Object {
            $_ -and ($_ -notmatch 'g2e[\\/]\.local[\\/]')
        })
    }
    $cleanPass = ($statusResult.exit_code -eq 0 -and $nonlocal.Count -eq 0)
    Set-Gate $report "git_worktree_clean_excluding_local" $cleanPass ($(if ($cleanPass) { "CLEAN" } else { ($nonlocal -join " | ") }))
    if (-not $cleanPass) { $allPass = $false }

    if ($null -ne $diagnosticLock -and $headPass) {
        $report.diagnostic_candidate_sha = [string]$diagnosticLock.qualified_candidate_sha

        $ancestorResult = Invoke-GitCapture $ProjectRoot @("merge-base", "--is-ancestor", $diagnosticLock.qualified_candidate_sha, "HEAD")
        $ancestorPass = ($ancestorResult.exit_code -eq 0)
        Set-Gate $report "diagnostic_candidate_is_ancestor" $ancestorPass ($(if ($ancestorPass) { $diagnosticLock.qualified_candidate_sha } else { "NOT_ANCESTOR" }))
        if (-not $ancestorPass) { $allPass = $false }

        $selfBlobResult = Invoke-GitCapture $ProjectRoot @("rev-parse", "HEAD:scripts/g2e/p5a_d2s2_elevation_bootstrap_diagnostic.ps1")
        $selfBlobPass = ($selfBlobResult.exit_code -eq 0 -and $selfBlobResult.output -eq $diagnosticLock.diagnostic_blob)
        Set-Gate $report "diagnostic_blob_identity" $selfBlobPass ($(if ($selfBlobPass) { $selfBlobResult.output } else { "ACTUAL=$($selfBlobResult.output);EXPECTED=$($diagnosticLock.diagnostic_blob)" }))
        if (-not $selfBlobPass) { $allPass = $false }
    }

    if ($null -ne $existingLock) {
        $oneclickBlobResult = Invoke-GitCapture $ProjectRoot @("rev-parse", "HEAD:scripts/g2e/p5a_d2s2_isolated_volume_oneclick.ps1")
        $oneclickPass = ($oneclickBlobResult.exit_code -eq 0 -and $oneclickBlobResult.output -eq $existingLock.oneclick_blob)
        Set-Gate $report "qualified_oneclick_blob_identity" $oneclickPass ($(if ($oneclickPass) { $oneclickBlobResult.output } else { "ACTUAL=$($oneclickBlobResult.output);EXPECTED=$($existingLock.oneclick_blob)" }))
        if (-not $oneclickPass) { $allPass = $false }

        $preflightBlobResult = Invoke-GitCapture $ProjectRoot @("rev-parse", "HEAD:scripts/g2e/p5a_d2s2_isolated_volume_preflight.py")
        $preflightPass = ($preflightBlobResult.exit_code -eq 0 -and $preflightBlobResult.output -eq $existingLock.preflight_blob)
        Set-Gate $report "qualified_preflight_blob_identity" $preflightPass ($(if ($preflightPass) { $preflightBlobResult.output } else { "ACTUAL=$($preflightBlobResult.output);EXPECTED=$($existingLock.preflight_blob)" }))
        if (-not $preflightPass) { $allPass = $false }
    }

    $pythonPass = (-not [string]::IsNullOrWhiteSpace($PythonExe) -and (Test-Path -LiteralPath $PythonExe -PathType Leaf))
    Set-Gate $report "python_executable" $pythonPass ($(if ($pythonPass) { $PythonExe } else { "MISSING:$PythonExe" }))
    if (-not $pythonPass) { $allPass = $false }

    $codexExists = (-not [string]::IsNullOrWhiteSpace($CodexExe) -and (Test-Path -LiteralPath $CodexExe -PathType Leaf))
    Set-Gate $report "codex_executable_exists" $codexExists ($(if ($codexExists) { $CodexExe } else { "MISSING:$CodexExe" }))
    if (-not $codexExists) {
        $allPass = $false
    }
    else {
        try {
            $codexHash = Get-Sha256 $CodexExe
            $codexHashPass = ($codexHash -eq $ExpectedCodexSha256)
            Set-Gate $report "codex_executable_hash" $codexHashPass ($(if ($codexHashPass) { $codexHash.ToLowerInvariant() } else { "ACTUAL=$($codexHash.ToLowerInvariant());EXPECTED=$($ExpectedCodexSha256.ToLowerInvariant())" }))
            if (-not $codexHashPass) { $allPass = $false }
        }
        catch {
            Set-Gate $report "codex_executable_hash" $false "HASH_ERROR:$($_.Exception.Message)"
            $allPass = $false
        }
    }

    $oldLocalRoot = Join-Path $ProjectRoot "g2e\.local\P5A-D2S2"
    $oldLocalExists = Test-Path -LiteralPath $oldLocalRoot
    $oldLocalDetail = "ABSENT"
    if ($oldLocalExists) {
        try {
            $names = @(Get-ChildItem -LiteralPath $oldLocalRoot -Force | Select-Object -ExpandProperty Name | Sort-Object)
            $oldLocalDetail = "EXISTS:" + ($names -join ",")
        }
        catch {
            $oldLocalDetail = "EXISTS_ENUMERATION_ERROR:$($_.Exception.Message)"
        }
    }
    Set-Gate $report "prior_d2s2_local_root_absent" (-not $oldLocalExists) $oldLocalDetail
    if ($oldLocalExists) { $allPass = $false }

    if ($allPass) {
        $report.status = "DIAGNOSTIC_PASS"
        $report.diagnostic = "ELEVATION_AND_ALL_FROZEN_PRE_REPORT_GATES_PASS"
        Save-Report $report $ReportJson $ReportMd
        exit 0
    }

    $report.status = "DIAGNOSTIC_BLOCKED"
    $report.diagnostic = "ONE_OR_MORE_FROZEN_PRE_REPORT_GATES_FAILED"
    Save-Report $report $ReportJson $ReportMd
    exit 10
}
catch {
    try {
        $report = Read-Report $ReportJson
        $report.phase = "ELEVATED"
        $report.status = "DIAGNOSTIC_INTERNAL_ERROR"
        $report.elevated_process_started = $true
        $report.elevated_admin = (Test-IsAdministrator)
        $report.elevated_pid = $PID
        $report.diagnostic = "ELEVATED_INTERNAL_ERROR:$($_.Exception.Message)"
        Save-Report $report $ReportJson $ReportMd
    }
    catch {
        Write-Error "ELEVATED_REPORT_UPDATE_FAILED:$($_.Exception.Message)"
    }
    exit 11
}
