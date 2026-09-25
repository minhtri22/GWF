$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Net.Http

$client = [Net.Http.HttpClient]::new()
try {
    if ($null -eq $client) {
        throw "HTTPCLIENT_CONSTRUCTION_FAILED"
    }
    Write-Host "RP_I2_HTTPCLIENT_POWERSHELL51_PASS"
}
finally {
    $client.Dispose()
}
