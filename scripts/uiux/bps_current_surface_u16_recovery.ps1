param([int]$Port = 18767)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Schema = "GWF-BPS-CURRENT-SURFACE-U16-RECOVERY-v1"
$RepairHead = "277dd6c32f10563ebaafca9618b3c479fcea8d41"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$PriorReport = Join-Path $RepoRoot ".local\BPS-CURRENT-SURFACE\report\CURRENT_SURFACE_UAT_REPORT.json"
$RecoveryRoot = Join-Path $RepoRoot ".local\BPS-CURRENT-SURFACE\u16-recovery"
$RunStamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$RunRoot = Join-Path $RecoveryRoot "evidence\$RunStamp"
$RuntimeRoot = Join-Path $RunRoot "runtime"
$RecoveryReport = Join-Path $RecoveryRoot "CURRENT_SURFACE_U16_RECOVERY_REPORT.json"
$Stdout = Join-Path $RunRoot "server.stdout.log"
$Stderr = Join-Path $RunRoot "server.stderr.log"
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$BaseUrl = "http://127.0.0.1:$Port"
$AppUrl = "http://localhost:$Port/app/system/diagnostics"

New-Item -ItemType Directory -Force -Path $RunRoot,$RuntimeRoot | Out-Null

$EnvNames = @(
 "GWR_AUTH_SECRET","GWR_BOOTSTRAP_USERNAME","GWR_BOOTSTRAP_PASSWORD",
 "GWR_DATABASE_URL","GWR_OBJECT_STORE_ROOT","GWR_OBSERVABILITY_PATH",
 "GWR_DOMAIN_PATH","GWR_WEB_ROOT","GWR_BUILD_SHA","GWR_BROWSER_COOKIE_SECURE"
)
$OldEnv = @{}
foreach($n in $EnvNames){$OldEnv[$n]=[Environment]::GetEnvironmentVariable($n,"Process")}

$Started = $false
$Proc = $null
$Verdict = "FAIL"
$Fatal = $null
$Prior = $null
$Head = $null
$PriorHash = $null
$Checks = [System.Collections.Generic.List[object]]::new()

function Add-Check([string]$Name,[bool]$Pass,[object]$Details=$null){
 $Checks.Add([pscustomobject]@{name=$Name;status=$(if($Pass){"PASS"}else{"FAIL"});details=$Details})
 if(-not $Pass){throw "Mandatory U16 recovery check failed: $Name"}
}
function Restore-Env{
 foreach($n in $EnvNames){
  $v=$OldEnv[$n]
  if($null -eq $v){Remove-Item ("Env:"+$n) -ErrorAction SilentlyContinue}
  else{[Environment]::SetEnvironmentVariable($n,[string]$v,"Process")}
 }
}
function Wait-Ready{
 for($i=0;$i -lt 60;$i++){
  try{$r=Invoke-RestMethod -Uri "$BaseUrl/ready" -TimeoutSec 2;if($r.ok -eq $true){return $r}}catch{}
  Start-Sleep -Milliseconds 500
 }
 throw "U16 recovery server did not become ready."
}
function Write-RecoveryReport{
 $obj=[ordered]@{
  schema=$Schema
  composite_final_verdict=$Verdict
  repair_head=$RepairHead
  current_head=$Head
  prior_report=$PriorReport
  prior_report_sha256=$PriorHash
  inherited_manual_uat=$(if($null -eq $Prior){$null}else{@($Prior.manual_uat|Where-Object{$_.id -ne "U16"})})
  recovered_u16=$(if($null -eq $Prior){$null}else{@($Prior.manual_uat|Where-Object{$_.id -eq "U16"})})
  checks=@($Checks)
  app_url=$AppUrl
  fatal_error=$Fatal
  evidence_root=$RunRoot
 }
 $obj|ConvertTo-Json -Depth 12|Set-Content $RecoveryReport -Encoding UTF8
}

try{
 Add-Check "prior_report_exists" (Test-Path $PriorReport) $PriorReport
 $Prior=Get-Content $PriorReport -Raw|ConvertFrom-Json
 $PriorHash=(Get-FileHash -Algorithm SHA256 $PriorReport).Hash.ToLowerInvariant()
 Add-Check "prior_schema" ($Prior.schema -eq "GWF-BPS-CURRENT-SURFACE-UAT-v1") $Prior.schema
 Add-Check "prior_final_fail" ($Prior.final_local_verdict -eq "FAIL") $Prior.final_local_verdict

 $manual=@($Prior.manual_uat)
 $failed=@($manual|Where-Object{$_.status -ne "PASS"})
 Add-Check "prior_manual_count_19" ($manual.Count -eq 19) $manual.Count
 Add-Check "prior_only_u16_failed" (($failed.Count -eq 1)-and($failed[0].id -eq "U16")) @($failed)
 Add-Check "prior_other_18_pass" (@($manual|Where-Object{$_.id -ne "U16" -and $_.status -ne "PASS"}).Count -eq 0) $true

 $Head=(& git -C $RepoRoot rev-parse HEAD).Trim()
 $Branch=(& git -C $RepoRoot rev-parse --abbrev-ref HEAD).Trim()
 Add-Check "implementation_branch" ($Branch -eq "feature/bps-i00-product-shell") $Branch
 & git -C $RepoRoot merge-base --is-ancestor $RepairHead HEAD
 Add-Check "repair_head_is_ancestor" ($LASTEXITCODE -eq 0) $RepairHead

 $priorHead=[string]$Prior.git_head_end
 & git -C $RepoRoot merge-base --is-ancestor $priorHead $RepairHead
 Add-Check "prior_head_precedes_repair" ($LASTEXITCODE -eq 0) @{prior=$priorHead;repair=$RepairHead}
 $repairDiff=@(& git -C $RepoRoot diff --name-only $priorHead $RepairHead -- src web install.ps1 scripts/gwf_server.ps1)
 Add-Check "repair_is_styles_only" (($repairDiff.Count -eq 1)-and($repairDiff[0] -eq "web/styles.css")) @($repairDiff)
 $postRepair=@(& git -C $RepoRoot diff --name-only $RepairHead HEAD -- src web install.ps1 scripts/gwf_server.ps1)
 Add-Check "no_product_drift_after_repair" ($postRepair.Count -eq 0) @($postRepair)
 Add-Check "venv_python_exists" (Test-Path $Python) $Python

 $nonce=[Guid]::NewGuid().ToString("N").Substring(0,12)
 $User="u16-recovery"
 $Password="Gwf-U16-$nonce!"
 $env:GWR_AUTH_SECRET=[Guid]::NewGuid().ToString("N")+[Guid]::NewGuid().ToString("N")
 $env:GWR_BOOTSTRAP_USERNAME=$User
 $env:GWR_BOOTSTRAP_PASSWORD=$Password
 $env:GWR_DATABASE_URL=Join-Path $RuntimeRoot "gwr.db"
 $env:GWR_OBJECT_STORE_ROOT=Join-Path $RuntimeRoot "objects"
 $env:GWR_OBSERVABILITY_PATH=Join-Path $RuntimeRoot "observability.jsonl"
 $env:GWR_DOMAIN_PATH=Join-Path $RepoRoot "domains\research.workflow.yaml"
 $env:GWR_WEB_ROOT=Join-Path $RepoRoot "web"
 $env:GWR_BUILD_SHA=$Head
 $env:GWR_BROWSER_COOKIE_SECURE="false"

 & $Python -m gwr.server --repo-root $RepoRoot --host 127.0.0.1 --port $Port --check-config
 if($LASTEXITCODE -ne 0){throw "Canonical server configuration validation failed."}

 $args=@("-m","gwr.server","--repo-root",$RepoRoot,"--host","127.0.0.1","--port","$Port")
 $Proc=Start-Process -FilePath $Python -ArgumentList $args -WorkingDirectory $RepoRoot -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -PassThru
 $Started=$true
 $ready=Wait-Ready
 Add-Check "server_ready" ($ready.ok -eq $true) $ready
 Add-Check "build_exact" ($ready.build_sha -eq $Head) $ready.build_sha

 Write-Host ""
 Write-Host "=== U16 TARGETED RECOVERY ===" -ForegroundColor Cyan
 Write-Host "This inherits U01-U15 and U17-U19 PASS from the frozen prior report."
 Write-Host "Only U16 is re-observed because the bounded product repair is web/styles.css only."
 Write-Host "URL: $AppUrl"
 Write-Host "Username: $User"
 Write-Host "Password: $Password"
 Start-Process $AppUrl|Out-Null

 do{$a=(Read-Host "U16: Diagnostics rows/cards no longer overlap; migration IDs/status/checksums and service/GitHub rows remain readable [P=PASS / F=FAIL]").Trim().ToUpperInvariant()}until($a -in @("P","PASS","F","FAIL"))
 $pass=$a -in @("P","PASS")
 Add-Check "u16_visual_recovery" $pass @{status=$(if($pass){"PASS"}else{"FAIL"});route="/app/system/diagnostics"}

 $u16=@($Prior.manual_uat|Where-Object{$_.id -eq "U16"})[0]
 $u16.status="PASS"
 $Verdict="PASS"
}catch{
 $Fatal=$_.Exception.Message
 Write-Host "U16 RECOVERY FAILED: $Fatal" -ForegroundColor Red
}finally{
 if($Started -and $null -ne $Proc){
  try{
   if(-not $Proc.HasExited){
    Stop-Process -Id $Proc.Id -ErrorAction Stop
    [void]$Proc.WaitForExit(10000)
   }
  }catch{}
 }
 Restore-Env
 Write-RecoveryReport
}

Write-Host ""
Write-Host "COMPOSITE_FINAL_VERDICT=$Verdict"
Write-Host "REPORT=$RecoveryReport"
Write-Host "EVIDENCE=$RunRoot"
if($Verdict -ne "PASS"){exit 1}
exit 0
