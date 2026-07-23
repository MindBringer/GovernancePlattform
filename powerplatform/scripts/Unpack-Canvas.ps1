[CmdletBinding()]param([string]$RepositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')),[string]$PacCommand='pac')
$ErrorActionPreference='Stop'; Import-Module (Join-Path $PSScriptRoot 'Common/DeveloperPlatform.Common.psm1') -Force
$c=Get-DeveloperPlatformConfig $RepositoryRoot; Assert-Command $PacCommand
if(-not(Test-Path $c.CanvasMsApp)){throw "Canvas msapp not found: $($c.CanvasMsApp)"}
Invoke-Native $PacCommand @('canvas','unpack','--msapp',$c.CanvasMsApp,'--sources',$c.CanvasReview,'--layout','SourceCode','--overwrite')
Invoke-Native $PacCommand @('canvas','unpack','--msapp',$c.CanvasMsApp,'--sources',$c.CanvasEditable,'--layout','Experimental','--overwrite')
