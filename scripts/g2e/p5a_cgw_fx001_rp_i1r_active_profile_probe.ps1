param(
    [string]$ProductionHome = "",
    [string]$DevelopmentHome = "",
    [string]$ProductionLauncherData = "",
    [int]$ExpectedPort = 17841,
    [string]$ExpectedVersion = "4.0.7"
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Net.Http

function Read-JsonSafe([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try { return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }
    catch { return $null }
}

function Get-ProcessInfo([int]$ProcessId) {
    if ($ProcessId -le 0) { return $null }
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if ($null -eq $p) { return $null }
    return [ordered]@{
        pid = [int]$p.ProcessId
        parent_pid = [int]$p.ParentProcessId
        name = [string]$p.Name
        executable_path = [string]$p.ExecutablePath
        command_contains_serve = ([string]$p.CommandLine -match "(^|\s)serve(\s|$)")
    }
}

function Add-Check {
    param(
        [System.Collections.IDictionary]$Checks,
        [string]$Name,
        [bool]$Value,
        [string]$Detail = ""
    )
    $Checks[$Name] = [ordered]@{ pass = $Value; detail = $Detail }
}

if ([string]::IsNullOrWhiteSpace($ProductionHome)) {
    $ProductionHome = Join-Path $HOME ".codex-chatgpt-web"
}
if ([string]::IsNullOrWhiteSpace($DevelopmentHome)) {
    $DevelopmentHome = Join-Path $HOME ".codex-chatgpt-web-dev"
}
if ([string]::IsNullOrWhiteSpace($ProductionLauncherData)) {
    $ProductionLauncherData = Join-Path $env:APPDATA "Codex Web GPT"
}

$ProductionHome = [IO.Path]::GetFullPath($ProductionHome)
$DevelopmentHome = [IO.Path]::GetFullPath($DevelopmentHome)
$ProductionLauncherData = [IO.Path]::GetFullPath($ProductionLauncherData)

$checks = [ordered]@{}
$result = [ordered]@{
    schema = "G2E-P5A-CGW-FX001-RP-I1R-v1"
    zero_science = $true
    model_execution = $false
    responses_post = $false
    browser_submission = $false
    mcp_invocation = $false
    checks = $checks
    observed = [ordered]@{}
    active_profile = $null
    verdict = "BLOCKED"
}

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
Add-Check $checks "health_contract" (
    [string]$health.status -eq "ok" -and
    [string]$health.service -eq "codex-chatgpt-web" -and
    [string]$health.version -eq $ExpectedVersion -and
    [string]$health.mode -eq "full" -and
    [int]$health.port -eq $ExpectedPort -and
    [bool]$health.accepting_turns -and
    [int]$health.active_http_turns -eq 0 -and
    [int]$health.active_browser_turns -eq 0 -and
    $healthPid -gt 0
) ("pid=$healthPid")

$listeners = @(Get-NetTCPConnection -LocalPort $ExpectedPort -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalAddress -eq "127.0.0.1" -or $_.LocalAddress -eq "0.0.0.0" -or $_.LocalAddress -eq "::" })
$listenerPids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
$listenerPid = if ($listenerPids.Count -eq 1) { [int]$listenerPids[0] } else { -1 }
Add-Check $checks "single_listener" ($listenerPids.Count -eq 1) (($listenerPids -join ","))
Add-Check $checks "listener_matches_health" ($listenerPid -gt 0 -and $listenerPid -eq $healthPid) ("listener=$listenerPid health=$healthPid")

$listenerProc = Get-ProcessInfo $listenerPid
$parentProc = if ($listenerProc) { Get-ProcessInfo ([int]$listenerProc.parent_pid) } else { $null }
$result.observed.listener_process = $listenerProc
$result.observed.parent_process = $parentProc
Add-Check $checks "listener_process_exists" ($null -ne $listenerProc) ($(if ($listenerProc) { [string]$listenerProc.name } else { "absent" }))
Add-Check $checks "listener_command_contains_serve" ($listenerProc -and [bool]$listenerProc.command_contains_serve) ""
Add-Check $checks "parent_process_exists" ($null -ne $parentProc) ($(if ($parentProc) { [string]$parentProc.name } else { "absent" }))

$candidates = @(
    [ordered]@{
        name = "production"
        core_home = $ProductionHome
        launcher_data = $ProductionLauncherData
        expected_purpose = $null
    },
    [ordered]@{
        name = "development"
        core_home = $DevelopmentHome
        launcher_data = (Join-Path $DevelopmentHome "launcher")
        expected_purpose = "dev-harness"
    }
)

$profileObservations = @()
$boundProfiles = @()

foreach ($candidate in $candidates) {
    $coreHome = [string]$candidate.core_home
    $launcherData = [string]$candidate.launcher_data
    $supervisorPath = Join-Path $coreHome "runtime\launcher-supervisor.json"
    $descriptorPath = Join-Path $coreHome "runtime\launcher-browser.json"
    $configPath = Join-Path $coreHome "config.json"
    $launcherLog = Join-Path $launcherData "logs\launcher.jsonl"
    $diagnosticsRoot = Join-Path $coreHome "diagnostics\browser-turns"

    $state = Read-JsonSafe $supervisorPath
    $descriptor = Read-JsonSafe $descriptorPath
    $config = Read-JsonSafe $configPath

    $ownerMatches = (
        $state -and $parentProc -and
        [int]$state.ownerPid -eq [int]$parentProc.pid
    )
    $daemonMatches = (
        $state -and
        [int]$state.daemonPid -eq $healthPid -and
        [int]$state.daemonPid -eq $listenerPid
    )
    $descriptorMatches = (
        $descriptor -and $state -and
        [int]$descriptor.pid -eq [int]$state.ownerPid
    )
    $binding = ($ownerMatches -and $daemonMatches -and $descriptorMatches)

    $purpose = if ($config -and $null -ne $config.PSObject.Properties["purpose"]) {
        [string]$config.purpose
    } else {
        $null
    }
    $purposeValid = if ([string]$candidate.name -eq "production") {
        $null -eq $purpose
    } else {
        $purpose -eq "dev-harness"
    }

    $configValid = (
        $config -and
        [string]$config.host -eq "127.0.0.1" -and
        [int]$config.port -eq $ExpectedPort -and
        [string]$config.releaseVersion -eq $ExpectedVersion -and
        [string]$config.mode -eq "full" -and
        [string]$config.browserHost -eq "launcher" -and
        $purposeValid
    )

    $obs = [ordered]@{
        name = [string]$candidate.name
        core_home = $coreHome
        launcher_data = $launcherData
        supervisor_path = $supervisorPath
        descriptor_path = $descriptorPath
        config_path = $configPath
        launcher_log = $launcherLog
        diagnostics_root = $diagnosticsRoot
        supervisor_exists = ($null -ne $state)
        descriptor_exists = ($null -ne $descriptor)
        config_exists = ($null -ne $config)
        owner_matches = [bool]$ownerMatches
        daemon_matches = [bool]$daemonMatches
        descriptor_matches = [bool]$descriptorMatches
        config_valid = [bool]$configValid
        purpose = $purpose
        launcher_log_exists = (Test-Path -LiteralPath $launcherLog -PathType Leaf)
        bound = [bool]$binding
    }
    $profileObservations += $obs

    if ($binding) {
        $boundProfiles += [ordered]@{
            candidate = $candidate
            observation = $obs
            state = $state
            descriptor = $descriptor
            config = $config
        }
    }
}

$result.observed.profiles = $profileObservations
Add-Check $checks "exactly_one_profile_bound" ($boundProfiles.Count -eq 1) ("count=$($boundProfiles.Count)")

if ($boundProfiles.Count -eq 1) {
    $selected = $boundProfiles[0]
    $obs = $selected.observation
    $config = $selected.config
    $state = $selected.state
    $descriptor = $selected.descriptor

    $result.active_profile = [ordered]@{
        name = [string]$selected.candidate.name
        core_home = [string]$obs.core_home
        launcher_data = [string]$obs.launcher_data
        supervisor = [ordered]@{
            ownerPid = [int]$state.ownerPid
            daemonPid = [int]$state.daemonPid
            status = [string]$state.status
            updatedAt = [string]$state.updatedAt
        }
        browser_descriptor = [ordered]@{
            pid = [int]$descriptor.pid
            kind = [string]$descriptor.kind
            profile = [string]$descriptor.profile
            endpoint = [string]$descriptor.endpoint
            createdAt = [string]$descriptor.createdAt
        }
        config = [ordered]@{
            host = [string]$config.host
            port = [int]$config.port
            releaseVersion = [string]$config.releaseVersion
            mode = [string]$config.mode
            browserHost = [string]$config.browserHost
            purpose = if ($null -ne $config.PSObject.Properties["purpose"]) { [string]$config.purpose } else { $null }
        }
        launcher_log = [string]$obs.launcher_log
        diagnostics_root = [string]$obs.diagnostics_root
    }

    Add-Check $checks "active_config_valid" ([bool]$obs.config_valid) ([string]$selected.candidate.name)
    Add-Check $checks "active_launcher_log_exists" ([bool]$obs.launcher_log_exists) ([string]$obs.launcher_log)
}

$client = [Net.Http.HttpClient]::new()
try {
    $response = $client.GetAsync("http://127.0.0.1:$ExpectedPort/v1/responses").GetAwaiter().GetResult()
    $statusCode = [int]$response.StatusCode
    $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    $result.observed.responses_get = [ordered]@{
        status_code = $statusCode
        body_length = $body.Length
    }
    Add-Check $checks "responses_get_returns_426" ($statusCode -eq 426) ("status=$statusCode")
}
finally {
    $client.Dispose()
}

$allPass = $true
foreach ($entry in $checks.GetEnumerator()) {
    if (-not [bool]$entry.Value.pass) { $allPass = $false }
}

if ($allPass) {
    $result.verdict = "PASS_ACTIVE_PROFILE_INSTANCE_BOUND_ZERO_SCIENCE"
}

$result | ConvertTo-Json -Depth 16
