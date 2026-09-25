param(
    [string]$BridgeHome = "",
    [string]$LauncherData = "",
    [string]$ExpectedVersion = "4.0.7",
    [int]$ExpectedPort = 17841
)

$ErrorActionPreference = "Stop"

function Add-Check {
    param([System.Collections.IDictionary]$Checks, [string]$Name, [bool]$Value, [string]$Detail = "")
    $Checks[$Name] = [ordered]@{ pass = $Value; detail = $Detail }
}

function Read-JsonFile([string]$Path) {
    return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json)
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
$DiagnosticsRoot = Join-Path $BridgeHome "diagnostics\browser-turns"
$LauncherLog = Join-Path $LauncherData "logs\launcher.jsonl"
$LauncherLogRotated = "$LauncherLog.1"

$checks = [ordered]@{}
$result = [ordered]@{
    schema = "G2E-P5A-CGW-FX001-ROUTE-INSTANCE-PROBE-v1"
    zero_science = $true
    model_execution = $false
    browser_submission = $false
    mcp_invocation = $false
    bridge_home = $BridgeHome
    launcher_data = $LauncherData
    checks = $checks
    observed = [ordered]@{}
    harness_integrity = [ordered]@{
        add_check_shared_container = $false
        initial_check_count = 0
    }
    verdict = "BLOCKED"
}

Add-Check $checks "config_exists" (Test-Path -LiteralPath $ConfigPath -PathType Leaf) $ConfigPath
Add-Check $checks "supervisor_state_exists" (Test-Path -LiteralPath $SupervisorPath -PathType Leaf) $SupervisorPath
Add-Check $checks "browser_descriptor_exists" (Test-Path -LiteralPath $DescriptorPath -PathType Leaf) $DescriptorPath
Add-Check $checks "launcher_log_exists" (Test-Path -LiteralPath $LauncherLog -PathType Leaf) $LauncherLog

$result.harness_integrity.initial_check_count = $checks.Count
$result.harness_integrity.add_check_shared_container = ($checks.Count -eq 4)
if (-not $result.harness_integrity.add_check_shared_container) {
    $result.verdict = "INVALID_HARNESS_CONTAINER_BINDING"
    $result | ConvertTo-Json -Depth 12
    return
}

if (-not $checks.config_exists.pass -or -not $checks.supervisor_state_exists.pass -or
    -not $checks.browser_descriptor_exists.pass -or -not $checks.launcher_log_exists.pass) {
    $result | ConvertTo-Json -Depth 12
    return
}

$config = Read-JsonFile $ConfigPath
$state = Read-JsonFile $SupervisorPath
$descriptor = Read-JsonFile $DescriptorPath

Add-Check $checks "config_host" ([string]$config.host -eq "127.0.0.1") ([string]$config.host)
Add-Check $checks "config_port" ([int]$config.port -eq $ExpectedPort) ([string]$config.port)
Add-Check $checks "config_version" ([string]$config.releaseVersion -eq $ExpectedVersion) ([string]$config.releaseVersion)
Add-Check $checks "config_mode_full" ([string]$config.mode -eq "full") ([string]$config.mode)
Add-Check $checks "config_browser_host_launcher" ([string]$config.browserHost -eq "launcher") ([string]$config.browserHost)

$health = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:$ExpectedPort/healthz" -TimeoutSec 3
$healthPid = [int]$health.pid
$result.observed.health = [ordered]@{
    pid = $healthPid
    status = [string]$health.status
    service = [string]$health.service
    version = [string]$health.version
    mode = [string]$health.mode
    port = [int]$health.port
    accepting_turns = [bool]$health.accepting_turns
    active_http_turns = [int]$health.active_http_turns
    active_browser_turns = [int]$health.active_browser_turns
}
Add-Check $checks "health_status" ([string]$health.status -eq "ok") ([string]$health.status)
Add-Check $checks "health_service" ([string]$health.service -eq "codex-chatgpt-web") ([string]$health.service)
Add-Check $checks "health_version" ([string]$health.version -eq $ExpectedVersion) ([string]$health.version)
Add-Check $checks "health_mode_full" ([string]$health.mode -eq "full") ([string]$health.mode)
Add-Check $checks "health_port" ([int]$health.port -eq $ExpectedPort) ([string]$health.port)
Add-Check $checks "health_accepting_turns" ([bool]$health.accepting_turns) ([string]$health.accepting_turns)
Add-Check $checks "health_idle_http" ([int]$health.active_http_turns -eq 0) ([string]$health.active_http_turns)
Add-Check $checks "health_idle_browser" ([int]$health.active_browser_turns -eq 0) ([string]$health.active_browser_turns)
Add-Check $checks "health_pid_positive" ($healthPid -gt 0) ([string]$healthPid)

$listeners = @(Get-NetTCPConnection -LocalPort $ExpectedPort -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalAddress -eq "127.0.0.1" -or $_.LocalAddress -eq "0.0.0.0" -or $_.LocalAddress -eq "::" })
$listenerPids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
$result.observed.listener_pids = @($listenerPids)
Add-Check $checks "single_listener_pid" ($listenerPids.Count -eq 1) (($listenerPids -join ","))
$listenerPid = if ($listenerPids.Count -eq 1) { [int]$listenerPids[0] } else { -1 }
Add-Check $checks "listener_pid_matches_health" ($listenerPid -gt 0 -and $listenerPid -eq $healthPid) ("listener=$listenerPid health=$healthPid")

$daemonPid = [int]$state.daemonPid
$ownerPid = [int]$state.ownerPid
$result.observed.supervisor = [ordered]@{
    version = $state.version
    status = [string]$state.status
    ownerPid = $ownerPid
    daemonPid = $daemonPid
    tunnelPid = $state.tunnelPid
    updatedAt = [string]$state.updatedAt
}
Add-Check $checks "supervisor_version" ([int]$state.version -eq 1) ([string]$state.version)
Add-Check $checks "supervisor_ready" ([string]$state.status -eq "ready") ([string]$state.status)
Add-Check $checks "daemon_pid_matches_health" ($daemonPid -gt 0 -and $daemonPid -eq $healthPid) ("daemon=$daemonPid health=$healthPid")

$ownerProc = Get-CimInstance Win32_Process -Filter "ProcessId=$ownerPid" -ErrorAction SilentlyContinue
$daemonProc = Get-CimInstance Win32_Process -Filter "ProcessId=$daemonPid" -ErrorAction SilentlyContinue
Add-Check $checks "owner_process_exists" ($null -ne $ownerProc) ($(if ($ownerProc) { [string]$ownerProc.Name } else { "absent" }))
Add-Check $checks "daemon_process_exists" ($null -ne $daemonProc) ($(if ($daemonProc) { [string]$daemonProc.Name } else { "absent" }))
$daemonCommand = if ($daemonProc) { [string]$daemonProc.CommandLine } else { "" }
Add-Check $checks "daemon_command_contains_serve" ($daemonCommand -match "(^|\s)serve(\s|$)") ($(if ($daemonCommand) { "serve-present=$($daemonCommand -match '(^|\s)serve(\s|$)')" } else { "absent" }))
$result.observed.process = [ordered]@{
    owner_name = if ($ownerProc) { [string]$ownerProc.Name } else { $null }
    daemon_name = if ($daemonProc) { [string]$daemonProc.Name } else { $null }
    daemon_parent_pid = if ($daemonProc) { [int]$daemonProc.ParentProcessId } else { $null }
    daemon_command_sha256 = if ($daemonCommand) {
        $sha = [Security.Cryptography.SHA256]::Create()
        try {
            ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($daemonCommand)))).Replace("-", "").ToLowerInvariant()
        } finally { $sha.Dispose() }
    } else { $null }
}

Add-Check $checks "daemon_parent_matches_owner" ($daemonProc -and [int]$daemonProc.ParentProcessId -eq $ownerPid) ("parent=$(if($daemonProc){$daemonProc.ParentProcessId}else{'absent'}) owner=$ownerPid")
Add-Check $checks "browser_descriptor_json" ($null -ne $descriptor) $DescriptorPath

$daemonStartedBound = $false
foreach ($logPath in @($LauncherLogRotated, $LauncherLog)) {
    if (-not (Test-Path -LiteralPath $logPath -PathType Leaf)) { continue }
    foreach ($line in Get-Content -LiteralPath $logPath) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        try {
            $record = $line | ConvertFrom-Json
            if ([string]$record.event -eq "runtime.daemon_started" -and [int]$record.detail.pid -eq $daemonPid) {
                $daemonStartedBound = $true
            }
        } catch {}
    }
}
Add-Check $checks "launcher_log_bound_to_daemon_pid" $daemonStartedBound ("daemonPid=$daemonPid")

# Zero-science local-route canary. GET is source-defined as non-executing; never POST.
$client = [Net.Http.HttpClient]::new()
try {
    $response = $client.GetAsync("http://127.0.0.1:$ExpectedPort/v1/responses").GetAwaiter().GetResult()
    $statusCode = [int]$response.StatusCode
    $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    $result.observed.local_route_canary = [ordered]@{
        method = "GET"
        status_code = $statusCode
        body_length = $body.Length
    }
    Add-Check $checks "responses_get_returns_426" ($statusCode -eq 426) ("status=$statusCode")
} finally {
    $client.Dispose()
}

$result.observed.paths = [ordered]@{
    config = $ConfigPath
    supervisor = $SupervisorPath
    descriptor = $DescriptorPath
    diagnostics = $DiagnosticsRoot
    launcher_log = $LauncherLog
}

$allPass = $true
foreach ($entry in $checks.GetEnumerator()) {
    if (-not [bool]$entry.Value.pass) { $allPass = $false }
}
if ($allPass) { $result.verdict = "PASS_INSTANCE_BOUND_ZERO_SCIENCE" }
$result | ConvertTo-Json -Depth 12
