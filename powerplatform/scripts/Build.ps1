[CmdletBinding()]param([string]$RepositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')),[string]$PacCommand='pac',[switch]$SkipValidation)
$ErrorActionPreference='Stop'
if(-not $SkipValidation){& (Join-Path $PSScriptRoot 'Validate.ps1') -RepositoryRoot $RepositoryRoot -PacCommand $PacCommand}
& Get-ChildItem `
    -Path $CanvasEditablePath `
    -Filter ".DS_Store" `
    -Recurse `
    -Force `
    -ErrorAction SilentlyContinue |
Remove-Item -Force -ErrorAction SilentlyContinue
& (Join-Path $PSScriptRoot 'Pack-Canvas.ps1') -RepositoryRoot $RepositoryRoot -PacCommand $PacCommand
& (Join-Path $PSScriptRoot 'Pack-Solution.ps1') -RepositoryRoot $RepositoryRoot -PacCommand $PacCommand
Write-Host 'Build completed successfully.'
