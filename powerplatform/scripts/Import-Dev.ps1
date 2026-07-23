[CmdletBinding(SupportsShouldProcess,ConfirmImpact='High')]param([string]$RepositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')),[string]$ZipFile,[string]$EnvironmentUrl,[string]$PacCommand='pac',[switch]$PublishChanges)
$ErrorActionPreference='Stop'; Import-Module (Join-Path $PSScriptRoot 'Common/DeveloperPlatform.Common.psm1') -Force
$c=Get-DeveloperPlatformConfig $RepositoryRoot; Assert-Command $PacCommand
if(-not $ZipFile){$ZipFile=(Get-ChildItem (Join-Path $c.Outbound '*.zip')|Sort LastWriteTime -Descending|Select -First 1).FullName};if(-not(Test-Path $ZipFile)){throw 'No outbound ZIP found.'}
if(-not $EnvironmentUrl){$EnvironmentUrl=$c.EnvironmentUrl};$args=@('solution','import','--path',$ZipFile,'--force-overwrite','--async');if($EnvironmentUrl){$args+=@('--environment',$EnvironmentUrl)}
if($PSCmdlet.ShouldProcess($EnvironmentUrl,"Import $ZipFile")){Invoke-Native $PacCommand $args;if($PublishChanges){$p=@('solution','publish');if($EnvironmentUrl){$p+=@('--environment',$EnvironmentUrl)};Invoke-Native $PacCommand $p}}
