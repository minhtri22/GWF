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

$dt = [DateTime]::SpecifyKind([DateTime]::Parse("2026-09-25T02:54:17"), [DateTimeKind]::Utc)
$dtIso = Convert-ToUtcIso $dt
if ($dtIso -notmatch "^2026-09-25T02:54:17") {
    throw "DATETIME_NORMALIZATION_FAILED: $dtIso"
}

$dmtf = "20260925025417.653038+000"
$dmtfIso = Convert-ToUtcIso $dmtf
if ([string]::IsNullOrWhiteSpace($dmtfIso)) {
    throw "DMTF_NORMALIZATION_FAILED"
}

$offset = [DateTimeOffset]::Parse("2026-09-25T09:54:17+07:00")
$offsetIso = Convert-ToUtcIso $offset
if ($offsetIso -notmatch "^2026-09-25T02:54:17") {
    throw "DATETIMEOFFSET_NORMALIZATION_FAILED: $offsetIso"
}

Write-Host "RP_I1C_TIMESTAMP_RUNTIME_REGRESSION_PASS"
