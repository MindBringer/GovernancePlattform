[CmdletBinding()]
param(
    [string]$RepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')),
    [string]$OutputPath,
    [string]$PacCommand = 'pac'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepositoryRoot = [System.IO.Path]::GetFullPath($RepositoryRoot)
$solutionSource = Join-Path $RepositoryRoot 'powerplatform/solution'
$versionFile = Join-Path $RepositoryRoot 'powerplatform/VERSION'

if (-not (Test-Path -LiteralPath $solutionSource -PathType Container)) {
    throw "Solution source not found: $solutionSource"
}
if (-not (Test-Path -LiteralPath $versionFile -PathType Leaf)) {
    throw "Version file not found: $versionFile"
}

$version = (Get-Content -LiteralPath $versionFile -Raw).Trim()
$safeVersion = $version -replace '[^0-9A-Za-z.-]', '-'
$solutionXmlPath = Join-Path $solutionSource 'Other/Solution.xml'
[xml]$solutionXml = Get-Content -LiteralPath $solutionXmlPath -Raw
$solutionVersion = $solutionXml.SelectSingleNode('//ImportExportXml/SolutionManifest/Version').InnerText

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $artifactDirectory = Join-Path $RepositoryRoot 'artifacts/outbound'
    New-Item -ItemType Directory -Force -Path $artifactDirectory | Out-Null
    $OutputPath = Join-Path $artifactDirectory "GovernancePortal_${solutionVersion}_${safeVersion}.zip"
}
else {
    $OutputPath = [System.IO.Path]::GetFullPath($OutputPath)
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
}

$pac = Get-Command $PacCommand -ErrorAction SilentlyContinue
if ($null -eq $pac) {
    throw "PAC CLI command '$PacCommand' was not found in PATH."
}

& $PacCommand solution pack `
    --zipfile $OutputPath `
    --folder $solutionSource `
    --packagetype Unmanaged

if ($LASTEXITCODE -ne 0) {
    throw "pac solution pack failed with exit code $LASTEXITCODE"
}

if (-not (Test-Path -LiteralPath $OutputPath -PathType Leaf)) {
    throw "PAC reported success, but the solution package was not created: $OutputPath"
}

Write-Host "Solution packed: $OutputPath"
