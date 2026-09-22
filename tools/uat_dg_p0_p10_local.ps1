param(
    [string]$RepoRoot = "D:\WORK\RESEARCH\4.GWF",
    [string]$ExpectedHead = "a09f79ae74a838d2c5998813560373c849669872"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Section([string]$Text) {
    Write-Host ""
    Write-Host ("=" * 88) -ForegroundColor DarkGray
    Write-Host $Text -ForegroundColor Cyan
    Write-Host ("=" * 88) -ForegroundColor DarkGray
}

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$FilePath,
        [Parameter(Mandatory=$true)][string[]]$Arguments,
        [Parameter(Mandatory=$true)][string]$LogPath
    )

    Write-Section $Name
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $commandOutput = @(& $FilePath @Arguments 2>&1)
    $code = $LASTEXITCODE
    $commandOutput | Set-Content -Path $LogPath -Encoding UTF8
    foreach ($line in $commandOutput) {
        Write-Host $line
    }
    $sw.Stop()

    $result = [ordered]@{
        name = $Name
        exit_code = $code
        elapsed_seconds = [math]::Round($sw.Elapsed.TotalSeconds, 3)
        status = if ($code -eq 0) { "PASS" } else { "FAIL" }
        log = $LogPath
        command = "$FilePath $($Arguments -join ' ')"
    }

    if ($code -ne 0) {
        Write-Host "RESULT=$($result.status) EXIT=$code" -ForegroundColor Red
    } else {
        Write-Host "RESULT=$($result.status)" -ForegroundColor Green
    }
    return [pscustomobject]$result
}

$RepoRoot = (Resolve-Path $RepoRoot).Path
Push-Location $RepoRoot
try {
    if (-not (Test-Path ".git")) {
        throw "RepoRoot is not a Git checkout: $RepoRoot"
    }

    $ActualHead = (& git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "git rev-parse HEAD failed."
    }
    if ($ActualHead -ne $ExpectedHead) {
        throw "HEAD mismatch. Expected $ExpectedHead but found $ActualHead. UAT aborted."
    }

    $TrackedBefore = @(& git status --porcelain --untracked-files=no)
    if ($LASTEXITCODE -ne 0) {
        throw "git status failed."
    }
    if ($TrackedBefore.Count -gt 0) {
        throw "Tracked working tree is not clean. UAT aborted. Changes: $($TrackedBefore -join '; ')"
    }

    $Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $Python)) {
        throw "Missing .venv. Run .\install.ps1 -SkipTests -SkipPostgres first, then rerun this UAT."
    }

    $env:PYTHONPATH = Join-Path $RepoRoot "src"

    $RunId = (Get-Date).ToString("yyyyMMdd-HHmmss")
    $OutDir = Join-Path $RepoRoot ".gwr\uat\dg-p0-p10\$RunId"
    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

    $Started = Get-Date
    $Results = New-Object System.Collections.Generic.List[object]

    Write-Section "GWF LOCAL ACCEPTANCE UAT - DG-P0 THROUGH DG-P10"
    Write-Host "repo=$RepoRoot"
    Write-Host "head=$ActualHead"
    Write-Host "python=$Python"
    Write-Host "output=$OutDir"

    $commands = @(
        @{
            Name = "BASELINE - research domain contract"
            Args = @("tools/gwr_domain.py", "validate", "domains/research.workflow.yaml")
        },
        @{
            Name = "BASELINE - software domain contract"
            Args = @("tools/gwr_domain.py", "validate", "domains/software.workflow.yaml")
        },
        @{
            Name = "BASELINE - CQG pilot contract"
            Args = @("tools/gwr_pilot.py", "validate", "pilots/cqg.research.yaml")
        },
        @{
            Name = "BASELINE - GWF self-upgrade pilot contract"
            Args = @("tools/gwr_pilot.py", "validate", "pilots/gwf.self-upgrade.yaml")
        },
        @{
            Name = "DG-P0..P3 - document ingress, validation and exact Git blob identity"
            Args = @("-m","pytest","-vv","--tb=short","-p","no:cacheprovider",
                "tests/test_document_validation_p0.py",
                "tests/test_document_validation_p1.py",
                "tests/test_document_validation_p2.py",
                "tests/test_dg_p3_git_blob_resolver.py")
        },
        @{
            Name = "DG-P4 - stable document/revision identity and facade"
            Args = @("-m","pytest","-vv","--tb=short","-p","no:cacheprovider","tests/test_dg_p4_document_facade.py")
        },
        @{
            Name = "DG-P5 - QA evidence and finding lifecycle"
            Args = @("-m","pytest","-vv","--tb=short","-p","no:cacheprovider","tests/test_dg_p5_qa_findings.py")
        },
        @{
            Name = "DG-P6 - document lifecycle and validity"
            Args = @("-m","pytest","-vv","--tb=short","-p","no:cacheprovider","tests/test_dg_p6_lifecycle_validity.py")
        },
        @{
            Name = "DG-P7 - document authority"
            Args = @("-m","pytest","-vv","--tb=short","-p","no:cacheprovider","tests/test_dg_p7_authority.py")
        },
        @{
            Name = "DG-P8 - explicit document relations"
            Args = @("-m","pytest","-vv","--tb=short","-p","no:cacheprovider","tests/test_dg_p8_relations.py")
        },
        @{
            Name = "DG-P9 - relation binding and exact revision resolution"
            Args = @("-m","pytest","-vv","--tb=short","-p","no:cacheprovider","tests/test_dg_p9_relations.py")
        },
        @{
            Name = "DG-P10 - change classification, authority decision and lineage plan"
            Args = @("-m","pytest","-vv","--tb=short","-p","no:cacheprovider","tests/test_dg_p10_change_classification.py")
        }
    )

    $index = 0
    foreach ($cmd in $commands) {
        $index++
        $safe = ($cmd.Name -replace '[^A-Za-z0-9._-]+','_').Trim('_')
        $log = Join-Path $OutDir ("{0:D2}-{1}.log" -f $index,$safe)
        $r = Invoke-NativeChecked -Name $cmd.Name -FilePath $Python -Arguments $cmd.Args -LogPath $log
        $Results.Add($r)
        if ($r.status -ne "PASS") {
            break
        }
    }

    if (($Results | Where-Object { $_.status -ne "PASS" }).Count -eq 0) {
        $GatePath = Join-Path $OutDir "DG_P10_UAT_GATE.json"
        $r = Invoke-NativeChecked -Name "DG-P10 - bounded end-to-end governance gate" -FilePath $Python -Arguments @("tools/run_dg_p10_gate.py","--out",$GatePath) -LogPath (Join-Path $OutDir "99-DG-P10-bounded-gate.log")
        $Results.Add($r)
    }

    $TrackedAfter = @(& git status --porcelain --untracked-files=no)
    if ($LASTEXITCODE -ne 0) {
        throw "git status after UAT failed."
    }

    $Finished = Get-Date
    $Failed = @($Results | Where-Object { $_.status -ne "PASS" })
    $NoTrackedMutation = ($TrackedAfter.Count -eq 0)
    $Overall = if (($Failed.Count -eq 0) -and $NoTrackedMutation) { "PASS" } else { "FAIL" }

    $Report = [ordered]@{
        schema = "GWF-LOCAL-UAT-DG-P0-P10-v1"
        status = $Overall
        repository = $RepoRoot
        expected_head = $ExpectedHead
        actual_head = $ActualHead
        started_at = $Started.ToUniversalTime().ToString("o")
        finished_at = $Finished.ToUniversalTime().ToString("o")
        elapsed_seconds = [math]::Round(($Finished - $Started).TotalSeconds, 3)
        tracked_tree_clean_before = $true
        tracked_tree_clean_after = $NoTrackedMutation
        tracked_changes_after = @($TrackedAfter)
        groups = @($Results)
        dg_p11_exercised = $false
        source_mutation_exercised = $false
    }

    $ReportPath = Join-Path $OutDir "UAT_REPORT.json"
    $Report | ConvertTo-Json -Depth 8 | Set-Content -Path $ReportPath -Encoding UTF8

    Write-Section "UAT SUMMARY"
    foreach ($r in $Results) {
        Write-Host ("{0,-72} {1,5}  {2,9:N2}s" -f $r.name,$r.status,$r.elapsed_seconds)
    }
    Write-Host ""
    Write-Host "HEAD=$ActualHead"
    Write-Host "TRACKED_TREE_CLEAN_AFTER=$NoTrackedMutation"
    Write-Host "DG_P11_EXERCISED=False"
    Write-Host "SOURCE_MUTATION_EXERCISED=False"
    Write-Host "REPORT=$ReportPath"

    if ($Overall -eq "PASS") {
        Write-Host "OVERALL=PASS" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "OVERALL=FAIL" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host ""
    Write-Host "UAT HARNESS ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}
finally {
    Pop-Location
}
