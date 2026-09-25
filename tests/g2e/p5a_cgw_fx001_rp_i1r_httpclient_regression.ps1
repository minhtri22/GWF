$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Net.Http

$client = [Net.Http.HttpClient]::new()
try {
    if ($null -eq $client) {
        throw "HTTPCLIENT_CONSTRUCTION_RETURNED_NULL"
    }
}
finally {
    $client.Dispose()
}

Write-Host "RP_I1R_HTTPCLIENT_POWERSHELL51_PASS"
