[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")),
    [string]$OutputPath,
    [string]$PacCommand = "pac"
)

$ErrorActionPreference = "Stop"
$solutionSource = Join-Path $RepositoryRoot "powerplatform/solution"
if (-not $OutputPath) {
    $artifactDirectory = Join-Path $RepositoryRoot "artifacts/outbound"
    New-Item -ItemType Directory -Force -Path $artifactDirectory | Out-Null
    $OutputPath = Join-Path $artifactDirectory "GovernancePortal_1_0_0_alpha_2.zip"
}

& $PacCommand solution pack --zipfile $OutputPath --folder $solutionSource --packagetype Unmanaged
if ($LASTEXITCODE -ne 0) { throw "pac solution pack failed with exit code $LASTEXITCODE" }

Write-Host "Solution packed: $OutputPath"
