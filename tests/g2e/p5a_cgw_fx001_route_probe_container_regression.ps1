$ErrorActionPreference = "Stop"

function Add-Check {
    param(
        [System.Collections.IDictionary]$Checks,
        [string]$Name,
        [bool]$Value,
        [string]$Detail = ""
    )
    $Checks[$Name] = [ordered]@{ pass = $Value; detail = $Detail }
}

$checks = [ordered]@{}
Add-Check $checks "alpha" $true "one"
Add-Check $checks "beta" $false "two"

if ($checks.Count -ne 2) {
    throw "ORDERED_DICTIONARY_SHARED_CONTAINER_FAILED: count=$($checks.Count)"
}
if (-not [bool]$checks.alpha.pass) {
    throw "ORDERED_DICTIONARY_ALPHA_MISSING"
}
if ([bool]$checks.beta.pass) {
    throw "ORDERED_DICTIONARY_BETA_VALUE_WRONG"
}
if ([string]$checks.beta.detail -ne "two") {
    throw "ORDERED_DICTIONARY_BETA_DETAIL_WRONG"
}

Write-Host "RP_I1_ORDERED_DICTIONARY_BINDING_PASS"
