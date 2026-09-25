param(
    [string]$BridgeHome = "",
    [string]$LauncherData = "",
    [int]$ExpectedPort = 17841
)

$ErrorActionPreference = "Stop"

function Get-Sha256Text([string]$Value) {
    if ([string]::IsNullOrEmpty($Value)) { return $null }
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString(
            $sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Value))
        )).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Read-JsonSafe([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try { return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }
    catch { return $null }
}

function Get-ProcessSnapshot([int]$ProcessId) {
    if ($ProcessId -le 0) { return $null }
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if ($null -eq $p) { return $null }
    $cmd = [string]$p.CommandLine
    return [ordered]@{
        pid = [int]$p.ProcessId
        parent_pid = [int]$p.ParentProcessId
        name = [string]$p.Name
        executable_path = [string]$p.ExecutablePath
        command_sha256 = Get-Sha256Text $cmd
        command_contains_serve = ($cmd -match "(^|\s)serve(\s|$)")
    }
}

if ([string]::IsNullOrWhiteSpace($BridgeHome)) {
    if ($env:CODEX_CHATGPT_WEB_HOME) { $BridgeHome = $env:CODEX_CHATGPT_WEB_HOME }
    else { $BridgeHome = Join-Path $HOME ".codex-chatgpt-web" }
}
if ([string]::IsNullOrWhiteSpace($LauncherData)) {
    if ($env:CODEX_WEB_GPT_LAUNCHER_DATA_DIR) { $LauncherData = $env:CODEX_WEB_GPT_LAUNCHER_DATA_DIR }
    else { $LauncherData = Join-Path $env:APPDATA "Codex Web GPT" }
}

$BridgeHome = [IO.Path]::GetFullPath($BridgeHome)
$LauncherData = [IO.Path]::GetFullPath($LauncherData)

$ConfigPath = Join-Path $BridgeHome "config.json"
$SupervisorPath = Join-Path $BridgeHome "runtime\launcher-supervisor.json"
$DescriptorPath = Join-Path $BridgeHome "runtime\launcher-browser.json"
$LauncherLog = Join-Path $LauncherData "logs\launcher.jsonl"
$LauncherLogRotated = "$LauncherLog.1"

$result = [ordered]@{
    schema = "G2E-P5A-CGW-FX001-RP-I1D-v1"
    zero_science = $true
    model_execution = $false
    responses_post = $false
    browser_submission = $false
    mcp_invocation = $false
    bridge_home = $BridgeHome
    launcher_data = $LauncherData
    observed = [ordered]@{}
    classification = "UNCLASSIFIED"
}

$config = Read-JsonSafe $ConfigPath
$state = Read-JsonSafe $SupervisorPath
$descriptor = Read-JsonSafe $DescriptorPath

$result.observed.files = [ordered]@{
    config_exists = (Test-Path -LiteralPath $ConfigPath -PathType Leaf)
    supervisor_state_exists = (Test-Path -LiteralPath $SupervisorPath -PathType Leaf)
    browser_descriptor_exists = (Test-Path -LiteralPath $DescriptorPath -PathType Leaf)
    launcher_log_exists = (Test-Path -LiteralPath $LauncherLog -PathType Leaf)
    launcher_log_rotated_exists = (Test-Path -LiteralPath $LauncherLogRotated -PathType Leaf)
}

$result.observed.config = if ($config) {
    [ordered]@{
        host = [string]$config.host
        port = [int]$config.port
        releaseVersion = [string]$config.releaseVersion
        mode = [string]$config.mode
        browserHost = [string]$config.browserHost
    }
} else { $null }

$result.observed.supervisor = if ($state) {
    [ordered]@{
        version = $state.version
        ownerPid = $state.ownerPid
        daemonPid = $state.daemonPid
        tunnelPid = $state.tunnelPid
        status = $state.status
        updatedAt = $state.updatedAt
    }
} else { $null }

$result.observed.browser_descriptor = if ($descriptor) {
    [ordered]@{
        version = $descriptor.version
        kind = $descriptor.kind
        profile = $descriptor.profile
        pid = $descriptor.pid
        endpoint = $descriptor.endpoint
        createdAt = $descriptor.createdAt
    }
} else { $null }

$health = $null
$healthError = $null
try {
    $health = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:$ExpectedPort/healthz" -TimeoutSec 3
}
catch {
    $healthError = $_.Exception.Message
}

$result.observed.health = if ($health) {
    [ordered]@{
        reachable = $true
        pid = $health.pid
        status = $health.status
        service = $health.service
        version = $health.version
        mode = $health.mode
        port = $health.port
        accepting_turns = $health.accepting_turns
        active_http_turns = $health.active_http_turns
        active_browser_turns = $health.active_browser_turns
    }
} else {
    [ordered]@{
        reachable = $false
        error = $healthError
    }
}

$listeners = @()
try {
    $listeners = @(Get-NetTCPConnection -LocalPort $ExpectedPort -State Listen -ErrorAction Stop)
}
catch {
    $listeners = @()
}
$listenerPids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
$result.observed.listener = [ordered]@{
    count = $listeners.Count
    unique_pids = @($listenerPids)
    endpoints = @($listeners | ForEach-Object {
        [ordered]@{
            local_address = $_.LocalAddress
            local_port = $_.LocalPort
            owning_pid = $_.OwningProcess
        }
    })
}

$pidSet = New-Object 'System.Collections.Generic.HashSet[int]'
foreach ($pidValue in $listenerPids) {
    [void]$pidSet.Add([int]$pidValue)
}
if ($health -and [int]$health.pid -gt 0) {
    [void]$pidSet.Add([int]$health.pid)
}
if ($state) {
    if ([int]$state.ownerPid -gt 0) { [void]$pidSet.Add([int]$state.ownerPid) }
    if ([int]$state.daemonPid -gt 0) { [void]$pidSet.Add([int]$state.daemonPid) }
    if ([int]$state.tunnelPid -gt 0) { [void]$pidSet.Add([int]$state.tunnelPid) }
}
if ($descriptor -and [int]$descriptor.pid -gt 0) {
    [void]$pidSet.Add([int]$descriptor.pid)
}

$result.observed.bound_processes = @(
    foreach ($pidValue in $pidSet) {
        $snap = Get-ProcessSnapshot $pidValue
        if ($snap) { $snap }
    }
)

$launcherProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { [string]$_.Name -ieq "Codex Web GPT.exe" } |
    ForEach-Object {
        [ordered]@{
            pid = [int]$_.ProcessId
            parent_pid = [int]$_.ParentProcessId
            executable_path = [string]$_.ExecutablePath
            command_sha256 = Get-Sha256Text ([string]$_.CommandLine)
        }
    })
$result.observed.launcher_processes = $launcherProcesses

$interestingEvents = @(
    "launcher.window_created",
    "browser.initialized",
    "runtime.daemon_started",
    "runtime.tunnel_started",
    "runtime.external_owner_detected",
    "runtime.daemon_exited",
    "runtime.tunnel_exited",
    "runtime.state_write_failed",
    "runtime.setup_required"
)
$logRecords = @()
foreach ($logPath in @($LauncherLogRotated, $LauncherLog)) {
    if (-not (Test-Path -LiteralPath $logPath -PathType Leaf)) { continue }
    foreach ($line in Get-Content -LiteralPath $logPath) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        try {
            $record = $line | ConvertFrom-Json
            if ($interestingEvents -contains [string]$record.event) {
                $detail = [ordered]@{}
                foreach ($key in @("pid","port","status","message")) {
                    if ($null -ne $record.detail.$key) {
                        $detail[$key] = $record.detail.$key
                    }
                }
                $logRecords += [ordered]@{
                    at = [string]$record.at
                    level = [string]$record.level
                    event = [string]$record.event
                    detail = $detail
                }
            }
        } catch {}
    }
}
$result.observed.latest_launcher_events = @($logRecords | Select-Object -Last 30)

$healthPid = if ($health -and [int]$health.pid -gt 0) { [int]$health.pid } else { -1 }
$singleListenerPid = if ($listenerPids.Count -eq 1) { [int]$listenerPids[0] } else { -1 }
$hasLauncher = $launcherProcesses.Count -gt 0
$hasSupervisor = $null -ne $state
$hasDescriptor = $null -ne $descriptor
$listenerMatchesHealth = ($healthPid -gt 0 -and $singleListenerPid -eq $healthPid)

if (-not $health -and $listenerPids.Count -eq 0 -and -not $hasLauncher) {
    $result.classification = "NO_ACTIVE_LAUNCHER_OR_LISTENER"
}
elseif ($health -and $listenerMatchesHealth -and -not $hasSupervisor -and -not $hasDescriptor) {
    $result.classification = "LIVE_LISTENER_WITHOUT_LAUNCHER_OWNERSHIP_MARKERS"
}
elseif ($health -and $listenerMatchesHealth -and $hasLauncher -and -not $hasSupervisor -and -not $hasDescriptor) {
    $result.classification = "LAUNCHER_PROCESS_PRESENT_BUT_OWNERSHIP_MARKERS_MISSING"
}
elseif ($hasSupervisor -or $hasDescriptor) {
    $result.classification = "PARTIAL_OR_RESTORED_LAUNCHER_OWNERSHIP_STATE"
}
elseif ($listenerPids.Count -gt 0 -and -not $health) {
    $result.classification = "PORT_LISTENER_NOT_MATCHING_HEALTH_CONTRACT"
}
else {
    $result.classification = "UNRESOLVED_RUNTIME_OWNERSHIP_STATE"
}

$result | ConvertTo-Json -Depth 14
