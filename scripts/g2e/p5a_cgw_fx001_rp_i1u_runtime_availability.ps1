param(
    [int]$ExpectedPort = 17841,
    [int]$PriorListenerPid = 27240,
    [int]$PriorLauncherPid = 15604
)

$ErrorActionPreference = "Stop"

function Get-ProcessInfo([int]$ProcessId) {
    if ($ProcessId -le 0) { return $null }
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if ($null -eq $p) {
        return [ordered]@{ pid = $ProcessId; alive = $false }
    }
    return [ordered]@{
        pid = [int]$p.ProcessId
        alive = $true
        parent_pid = [int]$p.ParentProcessId
        name = [string]$p.Name
        executable_path = [string]$p.ExecutablePath
        command_contains_serve = ([string]$p.CommandLine -match "(^|\s)serve(\s|$)")
    }
}

$result = [ordered]@{
    schema = "G2E-P5A-CGW-FX001-RP-I1U-v1"
    zero_science = $true
    http_request = $false
    responses_request = $false
    model_execution = $false
    browser_submission = $false
    mcp_invocation = $false
    observed = [ordered]@{}
    classification = "UNCLASSIFIED"
}

$priorListener = Get-ProcessInfo $PriorListenerPid
$priorLauncher = Get-ProcessInfo $PriorLauncherPid

$listeners = @()
try {
    $listeners = @(Get-NetTCPConnection -LocalPort $ExpectedPort -State Listen -ErrorAction Stop)
}
catch {
    $listeners = @()
}

$listenerPids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
$currentListeners = @(
    foreach ($pidValue in $listenerPids) {
        Get-ProcessInfo ([int]$pidValue)
    }
)

$launcherProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { [string]$_.Name -ieq "Codex Web GPT.exe" } |
    ForEach-Object {
        [ordered]@{
            pid = [int]$_.ProcessId
            parent_pid = [int]$_.ParentProcessId
            executable_path = [string]$_.ExecutablePath
        }
    })

$result.observed.prior_listener = $priorListener
$result.observed.prior_launcher = $priorLauncher
$result.observed.port = [ordered]@{
    number = $ExpectedPort
    listener_count = $listeners.Count
    unique_pids = @($listenerPids)
    listeners = @($currentListeners)
}
$result.observed.launcher_processes = $launcherProcesses

$priorListenerAlive = ($priorListener -and [bool]$priorListener.alive)
$priorLauncherAlive = ($priorLauncher -and [bool]$priorLauncher.alive)
$hasListener = ($listenerPids.Count -gt 0)
$priorListenerStillOwnsPort = ($hasListener -and ($listenerPids -contains $PriorListenerPid))

if (-not $hasListener -and -not $priorListenerAlive -and -not $priorLauncherAlive) {
    $result.classification = "PRIOR_RUNTIME_GENERATION_TERMINATED"
}
elseif (-not $hasListener -and -not $priorListenerAlive -and $priorLauncherAlive) {
    $result.classification = "LAUNCHER_ALIVE_DAEMON_NOT_LISTENING"
}
elseif ($priorListenerStillOwnsPort) {
    $result.classification = "PRIOR_RUNTIME_GENERATION_STILL_LISTENING"
}
elseif ($hasListener -and -not $priorListenerStillOwnsPort) {
    $result.classification = "NEW_LISTENER_GENERATION_PRESENT"
}
elseif (-not $hasListener -and $priorListenerAlive) {
    $result.classification = "PRIOR_DAEMON_ALIVE_NOT_LISTENING"
}
else {
    $result.classification = "RUNTIME_AVAILABILITY_UNRESOLVED"
}

$result | ConvertTo-Json -Depth 12
