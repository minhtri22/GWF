param(
    [string]$Launcher = "D:\WORK\RESEARCH\codex-chatgpt-web\launcher\artifacts\codex-web-gpt-4.0.7-win-x64-portable\Codex Web GPT.exe",
    [string]$PriorSha256 = "ac152ad499b1f41b2cafe94a3d05f5d4e4d3cd7ddbb417b9c60b118b08bc3cbb",
    [long]$PriorSize = 223980032,
    [string]$PriorFileVersion = "4.0.7",
    [string]$PriorProductVersion = "4.0.7.0"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) {
    throw "LAUNCHER_FILE_MISSING: $Launcher"
}

$item = Get-Item -LiteralPath $Launcher
$hash = (Get-FileHash -LiteralPath $Launcher -Algorithm SHA256).Hash.ToLowerInvariant()
$version = $item.VersionInfo

$sig = Get-AuthenticodeSignature -LiteralPath $Launcher

$signerSubject = $null
$signerThumbprint = $null
if ($null -ne $sig.SignerCertificate) {
    $signerSubject = [string]$sig.SignerCertificate.Subject
    $signerThumbprint = [string]$sig.SignerCertificate.Thumbprint
}

$fileVersion = [string]$version.FileVersion
$productVersion = [string]$version.ProductVersion

$exactPrior = (
    $hash -eq $PriorSha256.ToLowerInvariant() -and
    [long]$item.Length -eq $PriorSize
)

$sameVersion = (
    $fileVersion -eq $PriorFileVersion -and
    $productVersion -eq $PriorProductVersion
)

$classification = if ($exactPrior) {
    "EXACT_PRIOR_QUALIFIED_LAUNCHER"
}
elseif ($sameVersion -and [string]$sig.Status -eq "Valid") {
    "SAME_VERSION_DIFFERENT_BINARY_SIGNATURE_VALID"
}
elseif ($sameVersion) {
    "SAME_VERSION_DIFFERENT_BINARY_SIGNATURE_NOT_VALID"
}
else {
    "LAUNCHER_VERSION_OR_IDENTITY_DRIFT"
}

$result = [ordered]@{
    schema = "G2E-P5A-CGW-FX001-RP-L1-v1"
    zero_science = $true
    process_launch = $false
    http_request = $false
    responses_request = $false
    model_execution = $false
    browser_submission = $false
    mcp_invocation = $false
    launcher = [ordered]@{
        path = $item.FullName
        sha256 = $hash
        size = [long]$item.Length
        file_version = $fileVersion
        product_version = $productVersion
        company_name = [string]$version.CompanyName
        product_name = [string]$version.ProductName
        original_filename = [string]$version.OriginalFilename
        internal_name = [string]$version.InternalName
        authenticode_status = [string]$sig.Status
        authenticode_status_message = [string]$sig.StatusMessage
        signer_subject = $signerSubject
        signer_thumbprint = $signerThumbprint
    }
    prior_qualified = [ordered]@{
        sha256 = $PriorSha256
        size = $PriorSize
        file_version = $PriorFileVersion
        product_version = $PriorProductVersion
    }
    comparisons = [ordered]@{
        exact_prior_identity = $exactPrior
        same_file_and_product_version = $sameVersion
    }
    classification = $classification
}

$result | ConvertTo-Json -Depth 10
