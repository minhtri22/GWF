param(
    [string]$DevHome = "",
    [int]$ExpectedPort = 17841,
    [string]$WindowStartUtc = "2026-09-25T02:59:15Z",
    [string]$WindowEndUtc = "2026-09-25T03:40:47Z"
)

$ErrorActionPreference = "Stop"

function Convert-ToUtc([object]$Value) {
    if ($null -eq $Value) { return $null }
    if ($Value -is [DateTime]) { return $Value.ToUniversalTime() }
    $text = [string]$Value
    if ([string]::IsNullOrWhiteSpace($text)) { return $null }
    try { return [DateTimeOffset]::Parse($text).UtcDateTime }
    catch {
        try {
            return [Management.ManagementDateTimeConverter]::ToDateTime($text).ToUniversalTime()
        } catch {
            return $null
        }
    }
}

function Read-JsonSafe([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try { return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }
    catch { return $null }
}

function Get-ProcessInfo([int]$ProcessId) {
    if ($ProcessId -le 0) { return $null }
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if ($null -eq $p) { return $null }
    $created = Convert-ToUtc $p.CreationDate
    return [ordered]@{
        pid = [int]$p.ProcessId
        parent_pid = [int]$p.ParentProcessId
        name = [string]$p.Name
        executable_path = [string]$p.ExecutablePath
        creation_time_utc = if ($created) { $created.ToString("o") } else { $null }
        command_contains_serve = ([string]$p.CommandLine -match "(^|\s)serve(\s|$)")
    }
}

$windowStart = [DateTimeOffset]::Parse($WindowStartUtc).UtcDateTime
$windowEnd = [DateTimeOffset]::Parse($WindowEndUtc).UtcDateTime

if ([string]::IsNullOrWhiteSpace($DevHome)) {
    $DevHome = Join-Path $HOME ".codex-chatgpt-web-dev"
}
$DevHome = [IO.Path]::GetFullPath($DevHome)

$SupervisorPath = Join-Path $DevHome "runtime\launcher-supervisor.json"
$DescriptorPath = Join-Path $DevHome "runtime\launcher-browser.json"
$DevLauncherData = Join-Path $DevHome "launcher"
$DevLauncherLog = Join-Path $DevLauncherData "logs\launcher.jsonl"
$DevLauncherLogRotated = "$DevLauncherLog.1"

$result = [ordered]@{
    schema = "G2E-P5A-CGW-FX001-RP-I1T-v1"
    zero_science = $true
    model_execution = $false
    responses_request = $false
    browser_submission = $false
    mcp_invocation = $false
    window = [ordered]@{
        start_utc = $windowStart.ToString("o")
        end_utc = $windowEnd.ToString("o")
    }
    dev_home = $DevHome
    checks = [ordered]@{}
    observed = [ordered]@{}
    verdict = "BLOCKED"
}

$health = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:$ExpectedPort/healthz" -TimeoutSec 3
$healthPid = [int]$health.pid

$listeners = @(Get-NetTCPConnection -LocalPort $ExpectedPort -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalAddress -eq "127.0.0.1" -or $_.LocalAddress -eq "0.0.0.0" -or $_.LocalAddress -eq "::" })
$listenerPids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
$listenerPid = if ($listenerPids.Count -eq 1) { [int]$listenerPids[0] } else { -1 }

$listenerProc = Get-ProcessInfo $listenerPid
$parentProc = if ($listenerProc) { Get-ProcessInfo ([int]$listenerProc.parent_pid) } else { $null }

$result.observed.health = [ordered]@{
    pid = $healthPid
    status = [string]$health.status
    service = [string]$health.service
    version = [string]$health.version
    mode = [string]$health.mode
    port = [int]$health.port
}
$result.observed.listener_pids = @($listenerPids)
$result.observed.listener_process = $listenerProc
$result.observed.parent_process = $parentProc
$result.observed.dev_paths = [ordered]@{
    supervisor = $SupervisorPath
    descriptor = $DescriptorPath
    launcher_log = $DevLauncherLog
    launcher_log_rotated = $DevLauncherLogRotated
}

$listenerCreated = if ($listenerProc -and $listenerProc.creation_time_utc) {
    [DateTimeOffset]::Parse($listenerProc.creation_time_utc).UtcDateTime
} else { $null }
$parentCreated = if ($parentProc -and $parentProc.creation_time_utc) {
    [DateTimeOffset]::Parse($parentProc.creation_time_utc).UtcDateTime
} else { $null }

$result.checks.health_matches_listener = ($healthPid -gt 0 -and $healthPid -eq $listenerPid)
$result.checks.listener_created_before_window = ($listenerCreated -and $listenerCreated -le $windowStart)
$result.checks.listener_command_is_serve = ($listenerProc -and [bool]$listenerProc.command_contains_serve)
$result.checks.listener_path_is_dev = ($listenerProc -and [string]$listenerProc.executable_path -like "$DevHome\*")
$result.checks.parent_created_before_window = ($parentCreated -and $parentCreated -le $windowStart)
$result.checks.parent_is_portable_launcher = ($parentProc -and [string]$parentProc.executable_path -like "*codex-chatgpt-web\launcher\artifacts\*\Codex Web GPT.exe")
$result.checks.dev_launcher_log_exists = (Test-Path -LiteralPath $DevLauncherLog -PathType Leaf)
$result.checks.dev_supervisor_exists = (Test-Path -LiteralPath $SupervisorPath -PathType Leaf)
$result.checks.dev_descriptor_exists = (Test-Path -LiteralPath $DescriptorPath -PathType Leaf)

$daemonStartMatches = @()
$daemonExitAfterStart = @()
$browserInitRecords = @()
foreach ($logPath in @($DevLauncherLogRotated, $DevLauncherLog)) {
    if (-not (Test-Path -LiteralPath $logPath -PathType Leaf)) { continue }
    foreach ($line in Get-Content -LiteralPath $logPath) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        try {
            $record = $line | ConvertFrom-Json
            $at = Convert-ToUtc $record.at
            if ([string]$record.event -eq "runtime.daemon_started" -and [int]$record.detail.pid -eq $listenerPid) {
                $daemonStartMatches += [ordered]@{
                    at = if ($at) { $at.ToString("o") } else { [string]$record.at }
                    pid = [int]$record.detail.pid
                    source = $logPath
                }
            }
            if ([string]$record.event -eq "runtime.daemon_exited" -and $at -and $at -ge $windowStart -and $at -le $windowEnd) {
                $daemonExitAfterStart += [ordered]@{
                    at = $at.ToString("o")
                    source = $logPath
                }
            }
            if ([string]$record.event -eq "browser.initialized" -and $at -and $at -le $windowStart) {
                $browserInitRecords += [ordered]@{
                    at = $at.ToString("o")
                    source = $logPath
                }
            }
        } catch {}
    }
}

$result.observed.daemon_start_matches = @($daemonStartMatches)
$result.observed.daemon_exit_records_in_tc3_window = @($daemonExitAfterStart)
$result.observed.browser_initialized_before_window = @($browserInitRecords | Select-Object -Last 5)

$startBeforeWindow = $false
foreach ($m in $daemonStartMatches) {
    $at = Convert-ToUtc $m.at
    if ($at -and $at -le $windowStart) { $startBeforeWindow = $true }
}

$result.checks.dev_log_binds_listener_before_window = $startBeforeWindow
$result.checks.no_daemon_exit_in_tc3_window = ($daemonExitAfterStart.Count -eq 0)
$result.checks.browser_initialized_before_window = ($browserInitRecords.Count -gt 0)

$allPass = $true
foreach ($entry in $result.checks.GetEnumerator()) {
    if (-not [bool]$entry.Value) { $allPass = $false }
}
if ($allPass) {
    $result.verdict = "PASS_TC3_DEV_INSTANCE_TEMPORAL_BINDING"
}
else {
    $result.verdict = "BLOCKED_TEMPORAL_BINDING_INCOMPLETE"
}

$result | ConvertTo-Json -Depth 14
