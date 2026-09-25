param(
    [string]$DevHome = "",
    [int]$ExpectedPort = 17841
)

$ErrorActionPreference = "Stop"

function Convert-ToUtcIso([object]$Value) {
    if ($null -eq $Value) { return $null }
    try {
        if ($Value -is [DateTime]) {
            return $Value.ToUniversalTime().ToString("o")
        }
        return ([DateTimeOffset]::Parse([string]$Value)).UtcDateTime.ToString("o")
    }
    catch {
        try {
            return [Management.ManagementDateTimeConverter]::ToDateTime([string]$Value).ToUniversalTime().ToString("o")
        }
        catch {
            return $null
        }
    }
}

function Read-JsonSafe([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try { return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }
    catch { return $null }
}

function Get-FileSha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-ProcessInfo([int]$ProcessId) {
    if ($ProcessId -le 0) { return $null }
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if ($null -eq $p) {
        return [ordered]@{
            pid = $ProcessId
            alive = $false
        }
    }
    return [ordered]@{
        pid = [int]$p.ProcessId
        alive = $true
        parent_pid = [int]$p.ParentProcessId
        name = [string]$p.Name
        executable_path = [string]$p.ExecutablePath
        creation_time_utc = Convert-ToUtcIso $p.CreationDate
        command_contains_serve = ([string]$p.CommandLine -match "(^|\s)serve(\s|$)")
    }
}

if ([string]::IsNullOrWhiteSpace($DevHome)) {
    $DevHome = Join-Path $HOME ".codex-chatgpt-web-dev"
}
$DevHome = [IO.Path]::GetFullPath($DevHome)

$SupervisorPath = Join-Path $DevHome "runtime\launcher-supervisor.json"
$DescriptorPath = Join-Path $DevHome "runtime\launcher-browser.json"

$result = [ordered]@{
    schema = "G2E-P5A-CGW-FX001-RP-I1S-v1"
    zero_science = $true
    model_execution = $false
    responses_request = $false
    browser_submission = $false
    mcp_invocation = $false
    dev_home = $DevHome
    observed = [ordered]@{}
    classification = "UNCLASSIFIED"
}

$health = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:$ExpectedPort/healthz" -TimeoutSec 3
$healthPid = [int]$health.pid

$listeners = @(Get-NetTCPConnection -LocalPort $ExpectedPort -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalAddress -eq "127.0.0.1" -or $_.LocalAddress -eq "0.0.0.0" -or $_.LocalAddress -eq "::" })
$listenerPids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
$listenerPid = if ($listenerPids.Count -eq 1) { [int]$listenerPids[0] } else { -1 }

$listenerProc = Get-ProcessInfo $listenerPid
$listenerParent = if ($listenerProc -and $listenerProc.alive) {
    Get-ProcessInfo ([int]$listenerProc.parent_pid)
} else { $null }

$state = Read-JsonSafe $SupervisorPath
$descriptor = Read-JsonSafe $DescriptorPath

$supervisorFile = Get-Item -LiteralPath $SupervisorPath -ErrorAction SilentlyContinue
$descriptorFile = Get-Item -LiteralPath $DescriptorPath -ErrorAction SilentlyContinue

$ownerPid = if ($state) { [int]$state.ownerPid } else { -1 }
$daemonPid = if ($state -and $null -ne $state.daemonPid) { [int]$state.daemonPid } else { -1 }
$tunnelPid = if ($state -and $null -ne $state.tunnelPid) { [int]$state.tunnelPid } else { -1 }
$descriptorPid = if ($descriptor) { [int]$descriptor.pid } else { -1 }

$result.observed.health = [ordered]@{
    pid = $healthPid
    status = [string]$health.status
    service = [string]$health.service
    version = [string]$health.version
    mode = [string]$health.mode
    port = [int]$health.port
}
$result.observed.listener = [ordered]@{
    pids = @($listenerPids)
    process = $listenerProc
    parent_process = $listenerParent
}
$result.observed.supervisor_file = [ordered]@{
    exists = ($null -ne $supervisorFile)
    path = $SupervisorPath
    sha256 = Get-FileSha256 $SupervisorPath
    creation_time_utc = if ($supervisorFile) { $supervisorFile.CreationTimeUtc.ToString("o") } else { $null }
    last_write_time_utc = if ($supervisorFile) { $supervisorFile.LastWriteTimeUtc.ToString("o") } else { $null }
}
$result.observed.supervisor = if ($state) {
    [ordered]@{
        version = $state.version
        ownerPid = $ownerPid
        daemonPid = $daemonPid
        tunnelPid = $tunnelPid
        status = [string]$state.status
        updatedAt = [string]$state.updatedAt
    }
} else { $null }
$result.observed.browser_descriptor_file = [ordered]@{
    exists = ($null -ne $descriptorFile)
    path = $DescriptorPath
    sha256 = Get-FileSha256 $DescriptorPath
    creation_time_utc = if ($descriptorFile) { $descriptorFile.CreationTimeUtc.ToString("o") } else { $null }
    last_write_time_utc = if ($descriptorFile) { $descriptorFile.LastWriteTimeUtc.ToString("o") } else { $null }
}
$result.observed.browser_descriptor = if ($descriptor) {
    [ordered]@{
        version = $descriptor.version
        kind = [string]$descriptor.kind
        profile = [string]$descriptor.profile
        pid = $descriptorPid
        endpoint = [string]$descriptor.endpoint
        createdAt = [string]$descriptor.createdAt
    }
} else { $null }

$referenced = [ordered]@{}
foreach ($pair in @(
    @("supervisor_owner", $ownerPid),
    @("supervisor_daemon", $daemonPid),
    @("supervisor_tunnel", $tunnelPid),
    @("descriptor_pid", $descriptorPid)
)) {
    $name = [string]$pair[0]
    $pidValue = [int]$pair[1]
    if ($pidValue -gt 0) {
        $referenced[$name] = Get-ProcessInfo $pidValue
    } else {
        $referenced[$name] = $null
    }
}
$result.observed.referenced_processes = $referenced

$result.observed.relationships = [ordered]@{
    health_equals_listener = ($healthPid -gt 0 -and $healthPid -eq $listenerPid)
    supervisor_daemon_equals_listener = ($daemonPid -gt 0 -and $daemonPid -eq $listenerPid)
    supervisor_owner_equals_listener_parent = (
        $listenerParent -and $listenerParent.alive -and
        $ownerPid -gt 0 -and $ownerPid -eq [int]$listenerParent.pid
    )
    descriptor_equals_supervisor_owner = (
        $descriptorPid -gt 0 -and $ownerPid -gt 0 -and
        $descriptorPid -eq $ownerPid
    )
}

$ownerAlive = ($referenced.supervisor_owner -and [bool]$referenced.supervisor_owner.alive)
$daemonAlive = ($referenced.supervisor_daemon -and [bool]$referenced.supervisor_daemon.alive)
$descriptorAlive = ($referenced.descriptor_pid -and [bool]$referenced.descriptor_pid.alive)

if (-not $state -or -not $descriptor) {
    $result.classification = "OWNERSHIP_FILES_INCOMPLETE"
}
elseif (
    $result.observed.relationships.supervisor_daemon_equals_listener -and
    $result.observed.relationships.supervisor_owner_equals_listener_parent -and
    $result.observed.relationships.descriptor_equals_supervisor_owner
) {
    $result.classification = "OWNERSHIP_STATE_MATCHES_LIVE_INSTANCE"
}
elseif ($descriptorPid -ne $ownerPid) {
    $result.classification = "SUPERVISOR_DESCRIPTOR_GENERATION_SPLIT"
}
elseif (-not $ownerAlive -or -not $daemonAlive -or -not $descriptorAlive) {
    $result.classification = "OWNERSHIP_STATE_REFERENCES_NONLIVE_PROCESS"
}
elseif ($ownerAlive -and $daemonAlive -and $descriptorAlive) {
    $result.classification = "OWNERSHIP_STATE_BINDS_DIFFERENT_LIVE_INSTANCE"
}
else {
    $result.classification = "OWNERSHIP_STATE_UNRESOLVED"
}

$result | ConvertTo-Json -Depth 16
