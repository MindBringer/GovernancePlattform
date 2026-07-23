[CmdletBinding(SupportsShouldProcess)]param([string]$RepositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')),[string]$ZipFile,[string]$PacCommand='pac')
$ErrorActionPreference='Stop'; Import-Module (Join-Path $PSScriptRoot 'Common/DeveloperPlatform.Common.psm1') -Force
$c=Get-DeveloperPlatformConfig $RepositoryRoot; Assert-Command $PacCommand
if(-not $ZipFile){$ZipFile=(Get-ChildItem (Join-Path $c.Inbound '*.zip')|Sort-Object LastWriteTime -Descending|Select-Object -First 1).FullName}
if(-not $ZipFile -or -not(Test-Path $ZipFile)){throw 'No inbound solution ZIP found.'}
if($PSCmdlet.ShouldProcess($c.SolutionSource,"Unpack $ZipFile")){Invoke-Native $PacCommand @('solution','unpack','--zipfile',$ZipFile,'--folder',$c.SolutionSource,'--packagetype','Unmanaged','--allowDelete','--allowWrite','--clobber')}
