param(
    [int]$Port = 18765
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SliceId = "BPS-I00"
$Schema = "GWF-BPS-I00-LOCAL-UAT-v1"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ReportRoot = Join-Path $RepoRoot ".local\BPS-I00\report"
$EvidenceRoot = Join-Path $RepoRoot ".local\BPS-I00\evidence"
$RunStamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$RunRoot = Join-Path $EvidenceRoot $RunStamp
$CanonicalReport = Join-Path $ReportRoot "BPS-I00_LOCAL_UAT_REPORT.json"
$TimestampedReport = Join-Path $RunRoot "BPS-I00_LOCAL_UAT_REPORT.json"
$InstallLog = Join-Path $RunRoot "install.log"
$LauncherLog = Join-Path $RunRoot "launcher.log"
$RuntimeRoot = Join-Path $RunRoot "runtime"
$ServerLauncher = Join-Path $RepoRoot "scripts\gwf_server.ps1"
$InstallScript = Join-Path $RepoRoot "install.ps1"
$AppUrl = "http://127.0.0.1:$Port/app/system/diagnostics"
$ReadyUrl = "http://127.0.0.1:$Port/ready"
$BaseUrl = "http://127.0.0.1:$Port"

New-Item -ItemType Directory -Force -Path $ReportRoot,$RunRoot,$RuntimeRoot | Out-Null

$Checks = [System.Collections.Generic.List[object]]::new()
$ManualChecks = [System.Collections.Generic.List[object]]::new()
$EvidencePaths = [System.Collections.Generic.List[string]]::new()
$ServerStartedByScript = $false
$FatalError = $null
$FinalVerdict = "FAIL"
$StartUtc = (Get-Date).ToUniversalTime().ToString("o")
$EndUtc = $null
$HeadStart = $null
$HeadEnd = $null
$BranchName = $null
$Origin = $null
$TrackedDirtyAtStart = @()
$MachineSession = $null
$ProductMeta = $null
$ReadyState = $null
$MeAfterRestart = $null

$EnvironmentNames = @(
    "GWR_AUTH_SECRET",
    "GWR_BOOTSTRAP_USERNAME",
    "GWR_BOOTSTRAP_PASSWORD",
    "GWR_DATABASE_URL",
    "GWR_OBJECT_STORE_ROOT",
    "GWR_OBSERVABILITY_PATH",
    "GWR_DOMAIN_PATH",
    "GWR_WEB_ROOT",
    "GWR_BUILD_SHA",
    "GWR_BROWSER_COOKIE_SECURE"
)
$OriginalEnvironment = @{}
foreach ($name in $EnvironmentNames) {
    $OriginalEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
}

function Add-Check {
    param([string]$Name,[bool]$Pass,[object]$Details = $null)
    $Checks.Add([pscustomobject]@{
        name = $Name
        status = $(if ($Pass) { "PASS" } else { "FAIL" })
        details = $Details
    })
    if (-not $Pass) { throw "Mandatory machine check failed: $Name" }
}

function Add-Manual {
    param([string]$Id,[string]$Prompt)
    do {
        $answer = (Read-Host "$Prompt [P=PASS / F=FAIL]").Trim().ToUpperInvariant()
    } until ($answer -in @("P","PASS","F","FAIL"))
    $pass = $answer -in @("P","PASS")
    $ManualChecks.Add([pscustomobject]@{ id=$Id; prompt=$Prompt; status=$(if($pass){"PASS"}else{"FAIL"}) })
    return $pass
}

function Invoke-LoggedPowerShell {
    param([string]$ScriptPath,[string[]]$Arguments,[string]$LogPath)
    $PowerShellExe = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
    if (-not (Test-Path $PowerShellExe)) {
        throw "Unable to resolve current PowerShell executable."
    }
    & $PowerShellExe -NoProfile -ExecutionPolicy Bypass -File $ScriptPath @Arguments 2>&1 |
        Tee-Object -FilePath $LogPath -Append |
        Out-Host
    $code = $LASTEXITCODE
    if ($null -eq $code) { $code = 1 }
    if ($code -ne 0) { throw "Command failed with exit code ${code}: $ScriptPath $($Arguments -join ' ')" }
}

function Invoke-LoggedServerLauncher {
    param([string]$Action,[string]$LogPath)
    & $ServerLauncher -Action $Action -RepoRoot $RepoRoot -Port $Port *>&1 |
        Tee-Object -FilePath $LogPath -Append |
        Out-Host
}

function Wait-Ready {
    param([int]$Attempts = 60)
    for ($i=0; $i -lt $Attempts; $i++) {
        try {
            $state = Invoke-RestMethod -Uri $ReadyUrl -TimeoutSec 2
            if ($state.ok -eq $true) { return $state }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    throw "Canonical GWF server did not become ready at $ReadyUrl"
}

function Restore-Environment {
    foreach ($name in $EnvironmentNames) {
        $value = $OriginalEnvironment[$name]
        if ($null -eq $value) { Remove-Item ("Env:" + $name) -ErrorAction SilentlyContinue }
        else { [Environment]::SetEnvironmentVariable($name,[string]$value,"Process") }
    }
}

function Write-Report {
    $pythonVersion = $null
    $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) { try { $pythonVersion = (& $venvPython --version 2>&1 | Select-Object -First 1) } catch {} }
    $report = [ordered]@{
        schema = $Schema
        slice_id = $SliceId
        final_local_verdict = $FinalVerdict
        started_at = $StartUtc
        ended_at = $EndUtc
        git_head_start = $HeadStart
        git_head_end = $HeadEnd
        branch = $BranchName
        origin = $Origin
        working_tree_clean_at_start = ($TrackedDirtyAtStart.Count -eq 0)
        dirty_tracked_entries_at_start = @($TrackedDirtyAtStart)
        environment = [ordered]@{ windows=[System.Environment]::OSVersion.VersionString; powershell=$PSVersionTable.PSVersion.ToString(); python=$pythonVersion; port=$Port }
        machine_checks = @($Checks)
        manual_uat = @($ManualChecks)
        server_api_evidence = [ordered]@{ app_url=$AppUrl; ready=$ReadyState; product_meta=$ProductMeta; actor_after_restart=$(if($null -ne $MeAfterRestart){$MeAfterRestart.actor_id}else{$null}) }
        evidence_paths = @($EvidencePaths)
        fatal_error = $FatalError
    }
    $json = $report | ConvertTo-Json -Depth 12
    $json | Set-Content -Path $TimestampedReport -Encoding UTF8
    $json | Set-Content -Path $CanonicalReport -Encoding UTF8
}

try {
    if (-not (Test-Path $InstallScript)) { throw "Missing canonical installer: $InstallScript" }
    if (-not (Test-Path $ServerLauncher)) { throw "Missing canonical server launcher: $ServerLauncher" }

    $HeadStart = (& git -C $RepoRoot rev-parse HEAD 2>$null | Select-Object -First 1).Trim()
    $BranchName = (& git -C $RepoRoot rev-parse --abbrev-ref HEAD 2>$null | Select-Object -First 1).Trim()
    $Origin = (& git -C $RepoRoot remote get-url origin 2>$null | Select-Object -First 1).Trim()
    $TrackedDirtyAtStart = @(& git -C $RepoRoot status --porcelain --untracked-files=no)

    Add-Check "git_head_present" (-not [string]::IsNullOrWhiteSpace($HeadStart)) $HeadStart
    Add-Check "implementation_branch" ($BranchName -eq "feature/bps-i00-product-shell") $BranchName
    Add-Check "tracked_worktree_clean_at_start" ($TrackedDirtyAtStart.Count -eq 0) @($TrackedDirtyAtStart)

    Write-Host ""
    Write-Host "=== BPS-I00 LOCAL UAT ===" -ForegroundColor Cyan
    Write-Host ("HEAD={0}" -f $HeadStart)
    Write-Host ("BRANCH={0}" -f $BranchName)
    Write-Host ""

    Write-Host "Step 1/6 - canonical quick install" -ForegroundColor Cyan
    Invoke-LoggedPowerShell -ScriptPath $InstallScript -Arguments @() -LogPath $InstallLog
    $EvidencePaths.Add($InstallLog)
    $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    Add-Check "canonical_install" (Test-Path $venvPython) $venvPython

    $nonce = [Guid]::NewGuid().ToString("N").Substring(0,12)
    $UatUsername = "bps-i00-uat"
    $UatPassword = "BpsI00-UAT-$nonce!"
    $UatSecret = [Guid]::NewGuid().ToString("N") + [Guid]::NewGuid().ToString("N")

    $env:GWR_AUTH_SECRET = $UatSecret
    $env:GWR_BOOTSTRAP_USERNAME = $UatUsername
    $env:GWR_BOOTSTRAP_PASSWORD = $UatPassword
    $env:GWR_DATABASE_URL = Join-Path $RuntimeRoot "gwr.db"
    $env:GWR_OBJECT_STORE_ROOT = Join-Path $RuntimeRoot "objects"
    $env:GWR_OBSERVABILITY_PATH = Join-Path $RuntimeRoot "observability.jsonl"
    $env:GWR_DOMAIN_PATH = Join-Path $RepoRoot "domains\research.workflow.yaml"
    $env:GWR_WEB_ROOT = Join-Path $RepoRoot "web"
    $env:GWR_BUILD_SHA = $HeadStart
    $env:GWR_BROWSER_COOKIE_SECURE = "false"

    Write-Host "Step 2/6 - canonical server start/readiness" -ForegroundColor Cyan
    $preStatus = & $ServerLauncher -Action status -RepoRoot $RepoRoot -Port $Port *>&1
    if (($preStatus -join [Environment]::NewLine) -notmatch "GWF_SERVER=STOPPED") {
        throw "A canonical GWF server is already registered for this repo. Refusing to stop or reuse a process not started by this UAT run."
    }

    Invoke-LoggedServerLauncher -Action "start" -LogPath $LauncherLog
    $ServerStartedByScript = $true
    $EvidencePaths.Add($LauncherLog)

    $ReadyState = Wait-Ready
    Add-Check "canonical_server_ready" ($ReadyState.ok -eq $true) $ReadyState
    Add-Check "core_health_healthy" ($ReadyState.core_health -eq "HEALTHY") $ReadyState.core_health
    Add-Check "ready_build_sha_exact" ($ReadyState.build_sha -eq $HeadStart) $ReadyState.build_sha

    $statusOutput = & $ServerLauncher -Action status -RepoRoot $RepoRoot -Port $Port *>&1
    Add-Check "canonical_server_status_ready" (($statusOutput -join [Environment]::NewLine) -match "GWF_SERVER=READY") ($statusOutput -join [Environment]::NewLine)

    Write-Host "Step 3/6 - authoritative shell/session checks" -ForegroundColor Cyan
    $ProductMeta = Invoke-RestMethod -Uri "$BaseUrl/product/meta" -TimeoutSec 5
    Add-Check "product_build_sha_exact" ($ProductMeta.build_sha -eq $HeadStart) $ProductMeta.build_sha
    Add-Check "server_mode_canonical" ($ProductMeta.server_mode -eq "canonical") $ProductMeta.server_mode

    $bootstrap = Invoke-RestMethod -Uri "$BaseUrl/browser/bootstrap" -TimeoutSec 5
    Add-Check "bootstrap_unauthenticated" ($bootstrap.authenticated -eq $false) $bootstrap.authenticated
    $cap = @{}
    foreach ($item in $bootstrap.capabilities) { $cap[$item.id] = $item }
    Add-Check "home_skeleton_locked" ($cap["home"].state -eq "SKELETON_LOCKED") $cap["home"]
    Add-Check "home_module_m01" ($cap["home"].slice -eq "BPS-M01") $cap["home"].slice
    Add-Check "home_route_exact" ($cap["home"].route -eq "/app/home") $cap["home"].route
    Add-Check "projects_skeleton_locked" ($cap["projects"].state -eq "SKELETON_LOCKED") $cap["projects"]
    Add-Check "projects_module_m02" ($cap["projects"].slice -eq "BPS-M02") $cap["projects"].slice
    Add-Check "diagnostics_live_foundation" ($cap["diagnostics"].state -eq "LIVE_FOUNDATION") $cap["diagnostics"]
    Add-Check "diagnostics_route_exact" ($cap["diagnostics"].route -eq "/app/system/diagnostics") $cap["diagnostics"].route
    Add-Check "shared_library_planned" ($cap["shared-library"].state -eq "PLANNED_BLOCKED") $cap["shared-library"]
    Add-Check "reference_acquisition_planned" ($cap["reference-acquisition"].state -eq "PLANNED_BLOCKED") $cap["reference-acquisition"]
    Add-Check "agents_planned" ($cap["agents"].state -eq "PLANNED_BLOCKED") $cap["agents"]

    $loginBody = @{ username=$UatUsername; password=$UatPassword } | ConvertTo-Json
    $loginResponse = Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/browser/auth/login" -Method POST -ContentType "application/json" -Body $loginBody -SessionVariable MachineSession -TimeoutSec 5
    $setCookie = [string]($loginResponse.Headers["Set-Cookie"] -join ";")
    Add-Check "browser_login_no_access_token" (-not ($loginResponse.Content -match "access_token")) "No access_token in browser login body"
    Add-Check "browser_cookie_httponly" ($setCookie -match "(?i)HttpOnly") "HttpOnly present"
    Add-Check "browser_cookie_samesite_strict" ($setCookie -match "(?i)SameSite=Strict") "SameSite=Strict present"

    $me = Invoke-RestMethod -Uri "$BaseUrl/browser/auth/me" -WebSession $MachineSession -TimeoutSec 5
    Add-Check "browser_session_actor" (-not [string]::IsNullOrWhiteSpace([string]$me.actor_id)) $me.actor_id

    $appJs = (Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/assets/app.js" -TimeoutSec 5).Content
    $stylesCss = (Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/assets/styles.css" -TimeoutSec 5).Content
    Add-Check "no_static_demo_fixture_reference" (-not ($appJs -match "demo-data\.json|gwr-uat-domains|gwr-uat-projects")) "legacy demo references absent"
    Add-Check "no_js_access_token_storage" (-not ($appJs -match "access_token")) "access_token absent from shell JS"
    Add-Check "presentation_storage_only" (($appJs -match "gwr-ui-theme") -and ($appJs -match "gwr-ui-sidebar")) "theme/sidebar preference keys present"
    Add-Check "semantic_icon_system" (($appJs -match "const ICON_PATHS") -and ($appJs -match "iconSvg\(item\.id") -and (-not ($appJs -match "item\.label\.slice\(0, 1\)"))) "semantic SVG icon system present; first-letter placeholder path absent"
    Add-Check "sidebar_true_reflow_contract" (($appJs -match "sidebar-collapsed") -and ($stylesCss -match "grid-template-columns:260px minmax\(0,1fr\)") -and ($stylesCss -match "sidebar-collapsed\{grid-template-columns:68px minmax\(0,1fr\)")) "expanded 260px -> collapsed 68px app-grid reflow contract present"
    Add-Check "full_shell_theme_tokens" (($stylesCss -match "--bg-sidebar:#f9fbff") -and ($stylesCss -match "--bg-sidebar:#08111f") -and ($stylesCss -match "--topbar-bg:rgba\(255,255,255,.92\)") -and ($stylesCss -match "--topbar-bg:rgba\(9,17,29,.92\)")) "Light/Dark sidebar + topbar shell tokens present"
    Add-Check "later_documents_functionality_absent" (-not ($appJs -match "/documents|relation graph|full-screen reader")) "BPS-I00 does not open future Documents/Relations/Reader functionality"
    Add-Check "spa_history_router" (($appJs -match "history\.pushState") -and ($appJs -match "popstate") -and ($appJs -match "renderRoute")) "History API router contract present"
    Add-Check "locked_routes_clickable" (($appJs -match "data-route") -and (-not ($appJs -match 'disabled aria-disabled="true"'))) "locked/planned nav remains clickable"

    $routeChecks = [ordered]@{
        "home" = "/app/home"
        "projects" = "/app/projects"
        "operations" = "/app/operations"
        "packages" = "/app/research/packages"
        "diagnostics" = "/app/system/diagnostics"
        "settings" = "/app/system/settings"
        "shared_library" = "/app/shared-library"
        "reference_acquisition" = "/app/research/reference-acquisition"
        "agents" = "/app/agents"
    }
    foreach ($entry in $routeChecks.GetEnumerator()) {
        $routeResponse = Invoke-WebRequest -UseBasicParsing -Uri ($BaseUrl + $entry.Value) -WebSession $MachineSession -TimeoutSec 5
        Add-Check ("route_http_" + $entry.Key) ($routeResponse.StatusCode -eq 200 -and $routeResponse.Content -match "Governed Knowledge Studio") $entry.Value
    }

    Write-Host "Step 4/6 - restart/session persistence" -ForegroundColor Cyan
    Invoke-LoggedServerLauncher -Action "restart" -LogPath $LauncherLog
    $ReadyState = Wait-Ready
    $MeAfterRestart = Invoke-RestMethod -Uri "$BaseUrl/browser/auth/me" -WebSession $MachineSession -TimeoutSec 5
    Add-Check "session_survives_canonical_restart" ($MeAfterRestart.actor_id -eq $me.actor_id) $MeAfterRestart.actor_id

    Write-Host ""
    Write-Host "Step 5/6 - browser operator checks" -ForegroundColor Cyan
    Write-Host "The script will open the REAL canonical GWF product shell."
    Write-Host ("URL:      {0}" -f $AppUrl)
    Write-Host ("Username: {0}" -f $UatUsername)
    Write-Host ("Password: {0}" -f $UatPassword)
    Write-Host "The password is ephemeral and is NOT written to the report."
    Write-Host ""
    Start-Process $AppUrl | Out-Null

    $manualPrompts = @(
        @("M01","The browser opened the Governed Knowledge Studio login/product shell and it does not look like the legacy v0.8.5 static dashboard."),
        @("M02","Signing in with the displayed local-UAT credentials succeeded and opened the authoritative BPS-I00 shell."),
        @("M03","Refreshing the browser kept the authenticated shell/session without asking for a token."),
        @("M04","System, Light and Dark selections each change the FULL shell (sidebar, top bar and content together) and remain clearly legible."),
        @("M05","The left navigation collapses and expands correctly: collapsed mode produces a narrow icon rail and the main workspace visibly expands to reclaim the released width; expanding restores the full sidebar."),
        @("M06","Navigation uses recognizable semantic icons rather than first-letter placeholders; in collapsed mode hover/focus labels identify the item and its Locked/Planned/Live maturity context."),
        @("M07","The shell hierarchy and compact visual language still match the approved Governed Knowledge Studio visual baseline."),
        @("M08","Click Home, Projects, Operations and Research/Packages. Each click changes the URL and shows a route-specific Locked surface with its owning module; no fake module data or action appears."),
        @("M09","Click Shared Library, Reference Acquisition and Agents/Codex. Each route is navigable but visibly Planned and non-functional."),
        @("M10","Use browser Back and Forward after visiting several routes. The URL, selected navigation item and route surface follow browser history correctly."),
        @("M11","While on /app/projects, refresh the browser. The authenticated session remains and the same Projects locked route is restored."),
        @("M12","Navigate to System/Diagnostics. It is LIVE foundation and shows real exact build, backend/server identity and health rather than placeholder data."),
        @("M13","Locked/Planned route surfaces contain no fake counts, projects, runs, documents or mutation buttons."),
        @("M14","Signing out returns to the real login screen and does not expose a reusable token in the UI.")
    )
    $manualAllPass = $true
    foreach ($entry in $manualPrompts) { if (-not (Add-Manual -Id $entry[0] -Prompt $entry[1])) { $manualAllPass = $false } }
    if (-not $manualAllPass) { throw "One or more mandatory browser UAT observations failed." }

    Write-Host "Step 6/6 - post-browser authoritative re-query and shutdown" -ForegroundColor Cyan
    $postReady = Invoke-RestMethod -Uri $ReadyUrl -TimeoutSec 5
    $postMeta = Invoke-RestMethod -Uri "$BaseUrl/product/meta" -TimeoutSec 5
    Add-Check "post_browser_ready" ($postReady.ok -eq $true) $postReady
    Add-Check "post_browser_head_exact" ($postMeta.build_sha -eq $HeadStart) $postMeta.build_sha

    Invoke-LoggedServerLauncher -Action "stop" -LogPath $LauncherLog
    $ServerStartedByScript = $false
    $stopped = & $ServerLauncher -Action status -RepoRoot $RepoRoot -Port $Port *>&1
    Add-Check "canonical_server_stopped" (($stopped -join [Environment]::NewLine) -match "GWF_SERVER=STOPPED") ($stopped -join [Environment]::NewLine)

    $serverStdout = Join-Path $RepoRoot ".gwr\server\server.stdout.log"
    $serverStderr = Join-Path $RepoRoot ".gwr\server\server.stderr.log"
    if (Test-Path $serverStdout) { $copy=Join-Path $RunRoot "server.stdout.log"; Copy-Item $serverStdout $copy -Force; $EvidencePaths.Add($copy) }
    if (Test-Path $serverStderr) { $copy=Join-Path $RunRoot "server.stderr.log"; Copy-Item $serverStderr $copy -Force; $EvidencePaths.Add($copy) }

    $HeadEnd = (& git -C $RepoRoot rev-parse HEAD 2>$null | Select-Object -First 1).Trim()
    Add-Check "git_head_unchanged" ($HeadEnd -eq $HeadStart) @{start=$HeadStart;end=$HeadEnd}
    $dirtyEnd = @(& git -C $RepoRoot status --porcelain --untracked-files=no)
    Add-Check "tracked_worktree_clean_at_end" ($dirtyEnd.Count -eq 0) @($dirtyEnd)
    $FinalVerdict = "PASS"
}
catch {
    $FatalError = $_.Exception.Message
    Write-Host ""
    Write-Host ("BPS-I00 LOCAL UAT FAILED: {0}" -f $FatalError) -ForegroundColor Red
}
finally {
    if ($ServerStartedByScript) {
        try { & $ServerLauncher -Action stop -RepoRoot $RepoRoot -Port $Port *>&1 | Tee-Object -FilePath $LauncherLog -Append | Out-Null } catch {}
    }
    if ($null -eq $HeadEnd) { try { $HeadEnd = (& git -C $RepoRoot rev-parse HEAD 2>$null | Select-Object -First 1).Trim() } catch {} }
    $EndUtc = (Get-Date).ToUniversalTime().ToString("o")
    Restore-Environment
    Write-Report
}

Write-Host ""
Write-Host ("REPORT_PATH={0}" -f $CanonicalReport) -ForegroundColor Cyan
Write-Host ("EVIDENCE_DIR={0}" -f $RunRoot)
Write-Host ("FINAL_LOCAL_VERDICT={0}" -f $FinalVerdict) -ForegroundColor $(if($FinalVerdict -eq "PASS"){"Green"}else{"Red"})
Write-Host ""
Write-Host "Return this JSON report to ChatGPT:"
Write-Host $CanonicalReport

if ($FinalVerdict -ne "PASS") { exit 1 }
exit 0
