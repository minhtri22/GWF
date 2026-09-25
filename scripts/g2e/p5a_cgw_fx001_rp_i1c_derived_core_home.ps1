param(
    [int]$ExpectedPort = 17841,
    [string]$ExpectedVersion = "4.0.7",
    [string]$ExpectedLauncherSha256 = "ac152ad499b1f41b2cafe94a3d05f5d4e4d3cd7ddbb417b9c60b118b08bc3cbb"
)

$ErrorActionPreference = "Stop"

function Convert-ToUtcIso([object]$Value) {
    if ($null -eq $Value) { return $null }
    if ($Value -is [DateTime]) {
        return $Value.ToUniversalTime().ToString("o")
    }
    if ($Value -is [DateTimeOffset]) {
        return $Value.UtcDateTime.ToString("o")
    }
    $text = [string]$Value
    try {
        return ([DateTimeOffset]::Parse($text)).UtcDateTime.ToString("o")
    }
    catch {
        try {
            return [Management.ManagementDateTimeConverter]::ToDateTime($text).ToUniversalTime().ToString("o")
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

function Get-ProcessInfo([int]$ProcessId) {
    if ($ProcessId -le 0) { return $null }
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if ($null -eq $p) { return $null }
    $cmd = [string]$p.CommandLine
    return [ordered]@{
        pid = [int]$p.ProcessId
        parent_pid = [int]$p.ParentProcessId
        name = [string]$p.Name
        executable_path = [string]$p.ExecutablePath
        creation_time_utc = Convert-ToUtcIso $p.CreationDate
        command_contains_serve = ($cmd -match "(^|\s)serve(\s|$)")
        command_has_dev_profile_flag = ($cmd -match "(^|\s)--dev-profile(\s|$)")
        command_has_electron_child_type = ($cmd -match "(^|\s)--type=")
    }
}

$health = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:$ExpectedPort/healthz" -TimeoutSec 3
$healthPid = [int]$health.pid

$listeners = @(Get-NetTCPConnection -LocalPort $ExpectedPort -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalAddress -eq "127.0.0.1" -or $_.LocalAddress -eq "0.0.0.0" -or $_.LocalAddress -eq "::" })
$listenerPids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
$listenerPid = if ($listenerPids.Count -eq 1) { [int]$listenerPids[0] } else { -1 }
$listenerProc = Get-ProcessInfo $listenerPid
$parentProc = if ($listenerProc) { Get-ProcessInfo ([int]$listenerProc.parent_pid) } else { $null }

$result = [ordered]@{
    schema = "G2E-P5A-CGW-FX001-RP-I1C-v1"
    zero_science = $true
    model_execution = $false
    responses_request = $false
    browser_submission = $false
    mcp_invocation = $false
    observed = [ordered]@{}
    classification = "UNCLASSIFIED"
}

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

$coreHome = $null
$versionDir = $null
if ($listenerProc -and $listenerProc.executable_path) {
    $exe = [IO.Path]::GetFullPath([string]$listenerProc.executable_path)
    $runtimeDir = Split-Path -Parent $exe
    $versionDir = Split-Path -Parent $runtimeDir
    $versionsDir = Split-Path -Parent $versionDir
    if ((Split-Path -Leaf $versionsDir) -ieq "versions") {
        $coreHome = Split-Path -Parent $versionsDir
    }
}

$result.observed.derived = [ordered]@{
    core_home = $coreHome
    version_dir = $versionDir
}

if (-not $coreHome) {
    $result.classification = "RUNTIME_PATH_NOT_DERIVABLE"
    $result | ConvertTo-Json -Depth 16
    return
}

$SupervisorPath = Join-Path $coreHome "runtime\launcher-supervisor.json"
$DescriptorPath = Join-Path $coreHome "runtime\launcher-browser.json"
$ConfigPath = Join-Path $coreHome "config.json"
$DiagnosticsRoot = Join-Path $coreHome "diagnostics\browser-turns"

$state = Read-JsonSafe $SupervisorPath
$descriptor = Read-JsonSafe $DescriptorPath
$config = Read-JsonSafe $ConfigPath

$ownerPid = if ($state) { [int]$state.ownerPid } else { -1 }
$daemonPid = if ($state -and $null -ne $state.daemonPid) { [int]$state.daemonPid } else { -1 }
$descriptorPid = if ($descriptor) { [int]$descriptor.pid } else { -1 }
$purpose = if ($config -and $null -ne $config.PSObject.Properties["purpose"]) { [string]$config.purpose } else { $null }

$result.observed.paths = [ordered]@{
    supervisor = $SupervisorPath
    descriptor = $DescriptorPath
    config = $ConfigPath
    diagnostics_root = $DiagnosticsRoot
}
$result.observed.supervisor = if ($state) {
    [ordered]@{
        version = $state.version
        ownerPid = $ownerPid
        daemonPid = $daemonPid
        tunnelPid = $state.tunnelPid
        status = [string]$state.status
        updatedAt = [string]$state.updatedAt
    }
} else { $null }
$result.observed.descriptor = if ($descriptor) {
    [ordered]@{
        version = $descriptor.version
        kind = [string]$descriptor.kind
        profile = [string]$descriptor.profile
        pid = $descriptorPid
        endpoint = [string]$descriptor.endpoint
        createdAt = [string]$descriptor.createdAt
    }
} else { $null }
$result.observed.config = if ($config) {
    [ordered]@{
        version = $config.version
        releaseVersion = [string]$config.releaseVersion
        mode = [string]$config.mode
        host = [string]$config.host
        port = [int]$config.port
        browserHost = [string]$config.browserHost
        purpose = $purpose
    }
} else { $null }

$launcherSha = $null
if ($parentProc -and $parentProc.executable_path -and (Test-Path -LiteralPath $parentProc.executable_path -PathType Leaf)) {
    $launcherSha = (Get-FileHash -LiteralPath $parentProc.executable_path -Algorithm SHA256).Hash.ToLowerInvariant()
}
$result.observed.launcher_sha256 = $launcherSha

$relationships = [ordered]@{
    health_equals_listener = ($healthPid -gt 0 -and $healthPid -eq $listenerPid)
    supervisor_daemon_equals_listener = ($daemonPid -gt 0 -and $daemonPid -eq $listenerPid)
    supervisor_owner_equals_listener_parent = (
        $parentProc -and $ownerPid -gt 0 -and $ownerPid -eq [int]$parentProc.pid
    )
    descriptor_equals_supervisor_owner = (
        $descriptorPid -gt 0 -and $ownerPid -gt 0 -and $descriptorPid -eq $ownerPid
    )
    launcher_sha_matches_qualified = (
        $launcherSha -and $launcherSha -eq $ExpectedLauncherSha256.ToLowerInvariant()
    )
}
$result.observed.relationships = $relationships

$profileEvidence = "UNKNOWN"
if ($descriptor -and [string]$descriptor.profile -eq "development" -and $purpose -eq "dev-harness") {
    $profileEvidence = "DEVELOPMENT"
}
elseif ($descriptor -and [string]$descriptor.profile -eq "production" -and $null -eq $purpose) {
    $profileEvidence = "PRODUCTION"
}
elseif ($descriptor) {
    $profileEvidence = "CONTRADICTORY"
}
$result.observed.profile_evidence = $profileEvidence

if (
    $relationships.health_equals_listener -and
    $relationships.supervisor_daemon_equals_listener -and
    $relationships.supervisor_owner_equals_listener_parent -and
    $relationships.descriptor_equals_supervisor_owner
) {
    if ($profileEvidence -eq "PRODUCTION") {
        $result.classification = "PASS_DERIVED_CORE_HOME_BINDS_PRODUCTION_LAUNCHER"
    }
    elseif ($profileEvidence -eq "DEVELOPMENT") {
        $result.classification = "PASS_DERIVED_CORE_HOME_BINDS_DEVELOPMENT_LAUNCHER"
    }
    else {
        $result.classification = "DERIVED_CORE_HOME_BINDS_WITH_PROFILE_CONTRADICTION"
    }
}
elseif ($state -or $descriptor -or $config) {
    $result.classification = "DERIVED_CORE_HOME_PRESENT_BUT_NOT_BOUND"
}
else {
    $result.classification = "DERIVED_CORE_HOME_HAS_NO_OWNERSHIP_STATE"
}

$result | ConvertTo-Json -Depth 16
