[CmdletBinding()]param([string]$RepositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')),[string]$OutputPath,[string]$PacCommand='pac')
$ErrorActionPreference='Stop'; Import-Module (Join-Path $PSScriptRoot 'Common/DeveloperPlatform.Common.psm1') -Force
$c=Get-DeveloperPlatformConfig $RepositoryRoot; Assert-Command $PacCommand
New-Item -ItemType Directory -Force $c.Outbound|Out-Null
if(-not $OutputPath){$safe=$c.Version -replace '[^0-9A-Za-z.-]','-';$OutputPath=Join-Path $c.Outbound "GovernancePortal_$safe.zip"}
Invoke-Native $PacCommand @('solution','pack','--zipfile',$OutputPath,'--folder',$c.SolutionSource,'--packagetype','Unmanaged')
if(-not(Test-Path $OutputPath)){throw 'Solution package was not created.'}
Write-Host "Solution packed: $OutputPath"
