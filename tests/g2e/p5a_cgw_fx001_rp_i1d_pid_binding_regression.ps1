$ErrorActionPreference = "Stop"

function Invoke-PidBindingRegression {
    param([int]$ProcessId)

    if ($ProcessId -ne $PID) {
        throw "PROCESS_ID_PARAMETER_BINDING_MISMATCH"
    }

    return $ProcessId
}

$Observed = Invoke-PidBindingRegression -ProcessId $PID

if ($Observed -ne $PID) {
    throw "PROCESS_ID_PARAMETER_RUNTIME_MISMATCH"
}

Write-Host "RP_I1D_PID_BINDING_REGRESSION_PASS"
