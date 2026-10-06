param([int]$Port = 18766)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Schema = "GWF-BPS-CURRENT-SURFACE-UAT-v1"
$QualifiedImplementationHead = "4e95d406e346eba42567835b5a1bd44366618baf"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$InstallScript = Join-Path $RepoRoot "install.ps1"
$ServerLauncher = Join-Path $RepoRoot "scripts\gwf_server.ps1"
$SeedScript = Join-Path $RepoRoot "scripts\uiux\bps_current_surface_uat_seed.py"
$ReportRoot = Join-Path $RepoRoot ".local\BPS-CURRENT-SURFACE\report"
$EvidenceRoot = Join-Path $RepoRoot ".local\BPS-CURRENT-SURFACE\evidence"
$RunStamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$RunRoot = Join-Path $EvidenceRoot $RunStamp
$RuntimeRoot = Join-Path $RunRoot "runtime"
$Report = Join-Path $ReportRoot "CURRENT_SURFACE_UAT_REPORT.json"
$RunReport = Join-Path $RunRoot "CURRENT_SURFACE_UAT_REPORT.json"
$InstallLog = Join-Path $RunRoot "install.log"
$SeedLog = Join-Path $RunRoot "seed.log"
$LauncherLog = Join-Path $RunRoot "launcher.log"
$BaseUrl = "http://127.0.0.1:$Port"
$AppUrl = "http://localhost:$Port/app/home"

New-Item -ItemType Directory -Force -Path $ReportRoot,$RunRoot,$RuntimeRoot | Out-Null
$Checks = [System.Collections.Generic.List[object]]::new()
$Manual = [System.Collections.Generic.List[object]]::new()
$Evidence = [System.Collections.Generic.List[string]]::new()
$Started = $false
$Verdict = "FAIL"
$Fatal = $null
$HeadStart = $null
$HeadEnd = $null
$Branch = $null
$Origin = $null
$Seed = $null
$Ready = $null
$Meta = $null
$MachineSession = $null
$StartUtc = (Get-Date).ToUniversalTime().ToString("o")
$EndUtc = $null

$EnvNames = @(
 "GWR_AUTH_SECRET","GWR_BOOTSTRAP_USERNAME","GWR_BOOTSTRAP_PASSWORD",
 "GWR_DATABASE_URL","GWR_OBJECT_STORE_ROOT","GWR_OBSERVABILITY_PATH",
 "GWR_DOMAIN_PATH","GWR_WEB_ROOT","GWR_BUILD_SHA","GWR_BROWSER_COOKIE_SECURE",
 "GWR_UAT_USERNAME","GWR_UAT_PASSWORD"
)
$OldEnv = @{}
foreach($n in $EnvNames){$OldEnv[$n]=[Environment]::GetEnvironmentVariable($n,"Process")}

function Add-Check([string]$Name,[bool]$Pass,[object]$Details=$null){
 $Checks.Add([pscustomobject]@{name=$Name;status=$(if($Pass){"PASS"}else{"FAIL"});details=$Details})
 if(-not $Pass){throw "Mandatory machine check failed: $Name"}
}
function Ask([string]$Id,[string]$Prompt){
 do{$a=(Read-Host "$Prompt [P=PASS / F=FAIL]").Trim().ToUpperInvariant()}until($a -in @("P","PASS","F","FAIL"))
 $p=$a -in @("P","PASS")
 $Manual.Add([pscustomobject]@{id=$Id;prompt=$Prompt;status=$(if($p){"PASS"}else{"FAIL"})})
 return $p
}
function Run-Ps([string]$Path,[string]$Log){
 $exe=[System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
 $savedErrorActionPreference=$ErrorActionPreference
 try{
  # Windows PowerShell surfaces native stderr redirected with 2>&1 as ErrorRecord.
  # Preserve stderr in the evidence log, but judge the child process by exit code.
  $ErrorActionPreference="Continue"
  & $exe -NoProfile -ExecutionPolicy Bypass -File $Path 2>&1 | Tee-Object -FilePath $Log -Append | Out-Host
  $childExitCode=$LASTEXITCODE
 }finally{
  $ErrorActionPreference=$savedErrorActionPreference
 }
 if($childExitCode -ne 0){throw "Command failed ($childExitCode): $Path"}
}
function Server([string]$Action){
 & $ServerLauncher -Action $Action -RepoRoot $RepoRoot -Port $Port *>&1 | Tee-Object -FilePath $LauncherLog -Append | Out-Host
}
function Wait-Ready{
 for($i=0;$i -lt 60;$i++){
  try{$r=Invoke-RestMethod -Uri "$BaseUrl/ready" -TimeoutSec 2;if($r.ok -eq $true){return $r}}catch{}
  Start-Sleep -Milliseconds 500
 }
 throw "GWF server did not become ready."
}
function Get200([string]$Name,[string]$Path){
 $r=Invoke-WebRequest -UseBasicParsing -Uri ($BaseUrl+$Path) -WebSession $MachineSession -TimeoutSec 10
 Add-Check $Name ($r.StatusCode -eq 200) $Path
}
function Restore-Env{
 foreach($n in $EnvNames){
  $v=$OldEnv[$n]
  if($null -eq $v){Remove-Item ("Env:"+$n) -ErrorAction SilentlyContinue}
  else{[Environment]::SetEnvironmentVariable($n,[string]$v,"Process")}
 }
}
function Write-Report{
 $obj=[ordered]@{
  schema=$Schema
  final_local_verdict=$Verdict
  qualified_implementation_head=$QualifiedImplementationHead
  started_at=$StartUtc
  ended_at=$EndUtc
  git_head_start=$HeadStart
  git_head_end=$HeadEnd
  branch=$Branch
  origin=$Origin
  machine_checks=@($Checks)
  manual_uat=@($Manual)
  seeded_ids=$(if($null -eq $Seed){$null}else{[ordered]@{
   tenant_id=$Seed.tenant_id;workspace_id=$Seed.workspace_id
   execution_project_id=$Seed.execution_project_id
   lifecycle_project_id=$Seed.lifecycle_project_id
   recovery_project_id=$Seed.recovery_project_id
   approval_id=$Seed.approval_id
   recovery_phase_id=$Seed.recovery_phase_id
   recovery_proposal_id=$Seed.recovery_proposal_id
   github_binding_id=$Seed.github_binding_id
  }})
  server_api_evidence=[ordered]@{app_url=$AppUrl;ready=$Ready;product_meta=$Meta}
  evidence_paths=@($Evidence)
  fatal_error=$Fatal
 }
 $json=$obj|ConvertTo-Json -Depth 14
 $json|Set-Content -Path $RunReport -Encoding UTF8
 $json|Set-Content -Path $Report -Encoding UTF8
}

function Test-LocalPortAvailable([int]$CandidatePort){
 $listener=$null
 try{
  $address=[System.Net.IPAddress]::Parse("127.0.0.1")
  $listener=[System.Net.Sockets.TcpListener]::new($address,$CandidatePort)
  $listener.Start()
  return $true
 }catch{
  return $false
 }finally{
  if($null -ne $listener){try{$listener.Stop()}catch{}}
 }
}
function Select-FreeUatPort([int]$StartPort){
 for($candidate=$StartPort+1;$candidate -le $StartPort+100;$candidate++){
  if(Test-LocalPortAvailable $candidate){return $candidate}
 }
 throw "No free loopback UAT port found after $StartPort."
}
function Recover-StaleServerMetadata{
 $pidPath=Join-Path $RepoRoot ".gwr\server\server-process.json"
 if(-not(Test-Path $pidPath)){return}

 try{$serverMeta=Get-Content $pidPath -Raw|ConvertFrom-Json}
 catch{throw "Invalid server process metadata: $pidPath"}

 $owned=$false
 $staleReason=$null
 $proc=Get-Process -Id ([int]$serverMeta.pid) -ErrorAction SilentlyContinue
 if($null -eq $proc){
  $staleReason="recorded PID is not running"
 }else{
  $actualStart=$proc.StartTime.ToUniversalTime()
  $expectedStart=[DateTime]::Parse($serverMeta.process_started_at).ToUniversalTime()
  if([Math]::Abs(($actualStart-$expectedStart).TotalSeconds)-gt 3){
   $staleReason="recorded PID has been reused by a different process start time"
  }else{
   $commandMismatch=$false
   try{
    $cim=Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $serverMeta.pid) -ErrorAction Stop
    if($cim.CommandLine -and $cim.CommandLine -notmatch "gwr\.server"){$commandMismatch=$true}
   }catch{
    # If command-line identity cannot be inspected, fail closed and let the canonical launcher decide.
   }
   if($commandMismatch){$staleReason="recorded PID command line is not gwr.server"}
   else{$owned=$true}
  }
 }
 if($owned){return}

 $archive=Join-Path $RunRoot "stale-server-process.json"
 Copy-Item $pidPath $archive -Force
 Remove-Item $pidPath -Force
 $Evidence.Add($archive)
 Add-Check "stale_launcher_metadata_recovered" $true @{
  pid=$serverMeta.pid
  recorded_at=$serverMeta.recorded_at
  reason=$staleReason
  process_terminated=$false
  metadata_only=$true
 }

 if(-not(Test-LocalPortAvailable $script:Port)){
  $requestedPort=$script:Port
  $script:Port=Select-FreeUatPort $requestedPort
  $script:BaseUrl="http://127.0.0.1:$script:Port"
  $script:AppUrl="http://localhost:$script:Port/app/home"
  Add-Check "uat_port_isolated_from_unowned_listener" $true @{
   requested_port=$requestedPort
   selected_port=$script:Port
   existing_listener_terminated=$false
  }
 }
}

try{
 $HeadStart=(& git -C $RepoRoot rev-parse HEAD).Trim()
 $Branch=(& git -C $RepoRoot rev-parse --abbrev-ref HEAD).Trim()
 $Origin=(& git -C $RepoRoot remote get-url origin).Trim()
 $dirty=@(& git -C $RepoRoot status --porcelain --untracked-files=no)
 Add-Check "implementation_branch" ($Branch -eq "feature/bps-i00-product-shell") $Branch
 Add-Check "tracked_worktree_clean" ($dirty.Count -eq 0) @($dirty)
 & git -C $RepoRoot merge-base --is-ancestor $QualifiedImplementationHead HEAD
 Add-Check "qualified_head_is_ancestor" ($LASTEXITCODE -eq 0) $QualifiedImplementationHead
 $drift=@(& git -C $RepoRoot diff --name-only $QualifiedImplementationHead HEAD -- src web install.ps1 scripts/gwf_server.ps1)
 Add-Check "no_product_drift_after_qualified_head" ($drift.Count -eq 0) @($drift)

 Write-Host ""
 Write-Host "=== GWF CURRENT SURFACE USER UAT ===" -ForegroundColor Cyan
 Write-Host "Scope: I00 + LIVE M01..M07-A. M07-B/M08/M09/M10 remain closed."
 Write-Host "HEAD=$HeadStart"
 Write-Host ""

 Write-Host "Step 1/7 - canonical install" -ForegroundColor Cyan
 Run-Ps $InstallScript $InstallLog
 $Evidence.Add($InstallLog)
 $py=Join-Path $RepoRoot ".venv\Scripts\python.exe"
 Add-Check "canonical_install" (Test-Path $py) $py

 $nonce=[Guid]::NewGuid().ToString("N").Substring(0,12)
 $User="current-surface-uat"
 $Password="Gwf-UAT-$nonce!"
 $Secret=[Guid]::NewGuid().ToString("N")+[Guid]::NewGuid().ToString("N")
 $env:GWR_AUTH_SECRET=$Secret
 $env:GWR_BOOTSTRAP_USERNAME=$User
 $env:GWR_BOOTSTRAP_PASSWORD=$Password
 $env:GWR_UAT_USERNAME=$User
 $env:GWR_UAT_PASSWORD=$Password
 $env:GWR_DATABASE_URL=Join-Path $RuntimeRoot "gwr.db"
 $env:GWR_OBJECT_STORE_ROOT=Join-Path $RuntimeRoot "objects"
 $env:GWR_OBSERVABILITY_PATH=Join-Path $RuntimeRoot "observability.jsonl"
 $env:GWR_DOMAIN_PATH=Join-Path $RepoRoot "domains\research.workflow.yaml"
 $env:GWR_WEB_ROOT=Join-Path $RepoRoot "web"
 $env:GWR_BUILD_SHA=$HeadStart
 $env:GWR_BROWSER_COOKIE_SECURE="false"

 Write-Host "Step 2/7 - seed isolated authoritative UAT state" -ForegroundColor Cyan
 $raw=@(& $py $SeedScript 2>&1)
 $raw|Set-Content $SeedLog -Encoding UTF8
 $Evidence.Add($SeedLog)
 if($LASTEXITCODE -ne 0){$raw|Out-Host;throw "UAT seed failed."}
 $Seed=([string]($raw|Select-Object -Last 1))|ConvertFrom-Json
 Add-Check "seed_execution_project" ($Seed.execution_project_id -eq "project_uat_execution") $Seed.execution_project_id
 Add-Check "seed_lifecycle_project" ($Seed.lifecycle_project_id -eq "project_uat_lifecycle") $Seed.lifecycle_project_id
 Add-Check "seed_recovery_project" ($Seed.recovery_project_id -eq "project_uat_recovery") $Seed.recovery_project_id

 Write-Host "Step 3/7 - canonical server + capability contract" -ForegroundColor Cyan
 Recover-StaleServerMetadata
 $pre=& $ServerLauncher -Action status -RepoRoot $RepoRoot -Port $Port *>&1
 if(($pre-join [Environment]::NewLine) -notmatch "GWF_SERVER=STOPPED"){throw "A GWF server is already registered for this repo. UAT refuses to stop/reuse it."}
 Server "start";$Started=$true;$Evidence.Add($LauncherLog)
 $Ready=Wait-Ready
 Add-Check "server_ready" ($Ready.ok -eq $true) $Ready
 Add-Check "build_exact" ($Ready.build_sha -eq $HeadStart) $Ready.build_sha
 $Meta=Invoke-RestMethod -Uri "$BaseUrl/product/meta"
 Add-Check "server_mode_canonical" ($Meta.server_mode -eq "canonical") $Meta.server_mode
 $boot=Invoke-RestMethod -Uri "$BaseUrl/browser/bootstrap"
 $cap=@{};foreach($x in $boot.capabilities){$cap[$x.id]=$x}
 $expected=@{
  home=@("LIVE_MODULE","BPS-M01");projects=@("LIVE_MODULE","BPS-M02")
  access=@("LIVE_MODULE","BPS-M02");operations=@("LIVE_MODULE","BPS-M03")
  packages=@("LIVE_MODULE","BPS-M06");github=@("LIVE_MODULE","BPS-M07")
  diagnostics=@("LIVE_FOUNDATION","BPS-I00")
 }
 foreach($id in $expected.Keys){
  Add-Check ("cap_"+$id) (($cap[$id].state -eq $expected[$id][0])-and($cap[$id].slice -eq $expected[$id][1])) $cap[$id]
 }
 Add-Check "settings_locked" ($cap.settings.state -eq "SKELETON_LOCKED") $cap.settings
 foreach($id in @("shared-library","reference-acquisition","agents")){
  Add-Check ("future_"+$id+"_planned") ($cap[$id].state -eq "PLANNED_BLOCKED") $cap[$id]
 }

 $body=@{username=$User;password=$Password}|ConvertTo-Json
 $login=Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/browser/auth/login" -Method POST -ContentType "application/json" -Body $body -SessionVariable MachineSession
 $cookie=[string]($login.Headers["Set-Cookie"]-join ";")
 Add-Check "cookie_httponly" ($cookie -match "(?i)HttpOnly") "HttpOnly"
 Add-Check "cookie_samesite_strict" ($cookie -match "(?i)SameSite=Strict") "SameSite=Strict"
 Add-Check "no_access_token_in_browser_login" (-not($login.Content -match "access_token")) "No bearer token in body"

 Write-Host "Step 4/7 - all LIVE API surfaces preflight" -ForegroundColor Cyan
 Get200 "api_home" "/browser/home-summary"
 Get200 "api_projects" "/browser/projects-index"
 Get200 "api_create_options" "/browser/projects/create-options"
 Get200 "api_access" "/browser/access-summary"
 Get200 "api_runs" "/browser/operations/runs"
 Get200 "api_approvals" "/browser/operations/approvals"
 Get200 "api_audit" "/browser/operations/audit"
 Get200 "api_runtime" "/browser/operations/runtime"
 Get200 "api_packages" "/browser/packages"
 Get200 "api_github" "/browser/github"
 Get200 "api_diagnostics" "/browser/diagnostics"
 Get200 "api_overview" "/browser/projects/project_uat_execution/overview"
 Get200 "api_execution" "/browser/projects/project_uat_execution/execution"
 Get200 "api_recovery" "/browser/projects/project_uat_recovery/execution"

 Server "restart";$Ready=Wait-Ready
 $me=Invoke-RestMethod -Uri "$BaseUrl/browser/auth/me" -WebSession $MachineSession
 Add-Check "session_survives_restart" (-not [string]::IsNullOrWhiteSpace([string]$me.actor_id)) $me.actor_id

 Write-Host ""
 Write-Host "Step 5/7 - browser UAT" -ForegroundColor Cyan
 Write-Host "URL: $AppUrl"
 Write-Host "Username: $User"
 Write-Host "Password: $Password"
 Write-Host "Required mutations:" -ForegroundColor Yellow
 Write-Host "  1) Create project exactly: UAT Created Project"
 Write-Host "  2) Rename Lifecycle Project exactly: Lifecycle Project Renamed"
 Write-Host "  3) Archive it, then Restore it"
 Write-Host "  4) Approve proposal_current_surface_uat"
 Write-Host "  5) APPROVE the WAITING_HUMAN recovery in Recovery Project"
 Start-Process $AppUrl|Out-Null

 $prompts=@(
  @("U01","Login/topbar are truthful: All authorized scope, canonical runtime/backend/domain, no token."),
  @("U02","Refresh and deep links preserve authenticated session and exact route."),
  @("U03","Theme/sidebar/icons/command palette work; palette is LIVE-only and does not promise document/artifact global search."),
  @("U04","Home shows seeded executing run + attention/activity and its Project/Run links open exact Overview/Execution."),
  @("U05","Projects shows Execution/Lifecycle/Recovery/Archived projects, hides Hidden Project, and search/filter/navigation work."),
  @("U06","Create 'UAT Created Project' in Current Surface UAT Workspace and verify exact Project Overview opens."),
  @("U07","Rename Lifecycle Project to 'Lifecycle Project Renamed', archive after governed confirmation, restore, and verify ACTIVE."),
  @("U08","Operations Runs/Audit/Runtime show exact seeded records with no raw lease token or worker mutation."),
  @("U09","Approvals shows proposal_current_surface_uat with exact hash/context; approve it and verify it leaves Pending."),
  @("U10","Execution Project Overview shows exact scope/domain/run/phase/failure/GitHub/runtime summaries without secrets."),
  @("U11","Execution Project > Execution preserves persisted orchestration/phase/run/event truth; derived view is clearly derived."),
  @("U12","Recovery Project shows WAITING_HUMAN; APPROVE it, controls disappear after refresh, and no Apply/Retry/Verify/Handoff/Complete mechanics appear."),
  @("U13","Packages shows seeded Domain plus skill/usage semantics and exposes no create/publish/install/upgrade mutation."),
  @("U14","System/GitHub shows binding/readiness/ChangeSet read state distinctly and remains M07-A read-only."),
  @("U15","System/Access shows seeded authorized scope/members and does not disclose hidden scope."),
  @("U16","Diagnostics shows exact build/server/backend/domain/readiness/migrations/storage/observability/GitHub state without secrets."),
  @("U17","Settings is Locked; Shared Library/Reference Acquisition/Agents are Planned and non-functional; M07-B/M08/M09/M10 are not simulated."),
  @("U18","Back/Forward and cross-screen links preserve exact project/run context and clear stale prior-screen content."),
  @("U19","Logout returns to real login and exposes no reusable bearer token.")
 )
 $ok=$true
 foreach($p in $prompts){if(-not(Ask $p[0] $p[1])){$ok=$false}}
 if(-not $ok){throw "One or more manual UAT observations failed."}

 Write-Host "Step 6/7 - authoritative post-UAT verification" -ForegroundColor Cyan
 $projects=Invoke-RestMethod -Uri "$BaseUrl/browser/projects-index" -WebSession $MachineSession
 $created=@($projects.projects|Where-Object{$_.name -eq "UAT Created Project"})
 Add-Check "created_project_persisted" ($created.Count -eq 1) @($created)
 $life=Invoke-RestMethod -Uri "$BaseUrl/browser/projects/project_uat_lifecycle/overview" -WebSession $MachineSession
 Add-Check "rename_persisted" ($life.project.name -eq "Lifecycle Project Renamed") $life.project
 Add-Check "restore_active" ($life.lifecycle.status -eq "ACTIVE") $life.lifecycle
 $approvals=Invoke-RestMethod -Uri "$BaseUrl/browser/operations/approvals" -WebSession $MachineSession
 $pending=@($approvals.pending|Where-Object{$_.proposal_id -eq "proposal_current_surface_uat"})
 Add-Check "approval_left_pending" ($pending.Count -eq 0) @($pending)
 $phase=Invoke-RestMethod -Uri "$BaseUrl/browser/projects/project_uat_recovery/execution/phases/phase_current_surface_recovery" -WebSession $MachineSession
 $rows=@($phase.agent_protocol.problems|ForEach-Object{@($_.recoveries)}|Where-Object{$_.proposal_id -eq $Seed.recovery_proposal_id})
 Add-Check "recovery_decided" (($rows.Count -eq 1)-and($rows[0].status -ne "WAITING_HUMAN")) @($rows)
 $post=Invoke-RestMethod -Uri "$BaseUrl/ready"
 Add-Check "post_uat_ready" ($post.ok -eq $true) $post

 Write-Host "Step 7/7 - exact HEAD + shutdown" -ForegroundColor Cyan
 $HeadEnd=(& git -C $RepoRoot rev-parse HEAD).Trim()
 Add-Check "head_unchanged" ($HeadEnd -eq $HeadStart) @{start=$HeadStart;end=$HeadEnd}
 Server "stop";$Started=$false
 $st=& $ServerLauncher -Action status -RepoRoot $RepoRoot -Port $Port *>&1
 Add-Check "server_stopped" (($st-join [Environment]::NewLine)-match "GWF_SERVER=STOPPED") ($st-join [Environment]::NewLine)
 $Verdict="PASS"
}catch{
 $Fatal=$_.Exception.Message
 Write-Host "UAT FAILED: $Fatal" -ForegroundColor Red
 if($Started){try{Server "stop";$Started=$false}catch{}}
}finally{
 if($null -eq $HeadEnd){try{$HeadEnd=(& git -C $RepoRoot rev-parse HEAD).Trim()}catch{}}
 $EndUtc=(Get-Date).ToUniversalTime().ToString("o")
 Restore-Env
 Write-Report
}

Write-Host ""
Write-Host "FINAL_LOCAL_VERDICT=$Verdict"
Write-Host "REPORT=$Report"
Write-Host "EVIDENCE=$RunRoot"
if($Verdict -ne "PASS"){exit 1}
exit 0
