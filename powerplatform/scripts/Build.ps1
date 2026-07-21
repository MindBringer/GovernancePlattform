[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")),
    [string]$PacCommand = "pac"
)

$ErrorActionPreference = "Stop"

& (Join-Path $PSScriptRoot "Pack-Canvas.ps1") -RepositoryRoot $RepositoryRoot -PacCommand $PacCommand
& (Join-Path $PSScriptRoot "Pack-Solution.ps1") -RepositoryRoot $RepositoryRoot -PacCommand $PacCommand

Write-Host "Build completed successfully."
