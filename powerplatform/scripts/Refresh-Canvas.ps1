[CmdletBinding()]param([string]$RepositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')),[string]$PacCommand='pac')
& (Join-Path $PSScriptRoot 'Unpack-Canvas.ps1') -RepositoryRoot $RepositoryRoot -PacCommand $PacCommand
