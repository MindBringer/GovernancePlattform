[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Join-Path $PSScriptRoot '../..')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = [System.IO.Path]::GetFullPath($RepositoryRoot)
$registryPath = Join-Path $root 'powerplatform/config/ObjectProviderRegistry.json'
if (-not (Test-Path -LiteralPath $registryPath -PathType Leaf)) {
    throw "Object provider registry not found: $registryPath"
}

$registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json -Depth 10
if ($registry.schemaVersion -ne 1) {
    throw "Unsupported object provider registry schemaVersion: $($registry.schemaVersion)"
}

$requiredKeys = @('Asset','System','Contact','Incident','Problem','Change','Risk','Control','Measure')
$providers = @($registry.providers)
$duplicates = $providers | Group-Object objectTypeKey | Where-Object Count -gt 1
if ($duplicates) {
    throw "Duplicate object providers: $($duplicates.Name -join ', ')"
}

foreach ($required in $requiredKeys) {
    if (-not ($providers.objectTypeKey -contains $required)) {
        throw "Required object provider is missing: $required"
    }
}

foreach ($provider in $providers) {
    foreach ($property in @('objectTypeKey','dataSource','titleField','governanceIdField','activeField')) {
        if ([string]::IsNullOrWhiteSpace([string]$provider.$property)) {
            throw "Provider '$($provider.objectTypeKey)' has an empty '$property'."
        }
    }
    if ($provider.supportsSave -and -not $provider.supportsEdit) {
        throw "Provider '$($provider.objectTypeKey)' supports save but not edit."
    }
}

Write-Host "Object provider registry valid: $($providers.Count) providers." -ForegroundColor Green
