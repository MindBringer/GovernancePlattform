[CmdletBinding()]param([string]$RepositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')),[string]$EnvironmentUrl,[string]$PacCommand='pac',[switch]$Unpack)
$ErrorActionPreference='Stop'; Import-Module (Join-Path $PSScriptRoot 'Common/DeveloperPlatform.Common.psm1') -Force
$c=Get-DeveloperPlatformConfig $RepositoryRoot; Assert-Command $PacCommand; New-Item -ItemType Directory -Force $c.Inbound|Out-Null
if(-not $EnvironmentUrl){$EnvironmentUrl=$c.EnvironmentUrl};$path=Join-Path $c.Inbound "$($c.SolutionUniqueName)_$(Get-Date -Format yyyyMMdd-HHmmss).zip"
$args=@('solution','export','--name',$c.SolutionUniqueName,'--path',$path,'--managed','false','--overwrite')
if($EnvironmentUrl){$args+=@('--environment',$EnvironmentUrl)}
Invoke-Native $PacCommand $args
if($Unpack){& (Join-Path $PSScriptRoot 'Unpack-Solution.ps1') -RepositoryRoot $RepositoryRoot -ZipFile $path -PacCommand $PacCommand;& (Join-Path $PSScriptRoot 'Unpack-Canvas.ps1') -RepositoryRoot $RepositoryRoot -PacCommand $PacCommand}
Write-Host "Exported: $path"
