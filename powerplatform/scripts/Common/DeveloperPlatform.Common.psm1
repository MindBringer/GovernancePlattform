Set-StrictMode -Version Latest
function Get-RepositoryRoot { param([string]$StartPath=$PSScriptRoot) (Resolve-Path (Join-Path $StartPath '../../..')).Path }
function Get-DeveloperPlatformConfig {
 param([string]$RepositoryRoot)
 $cfg=Import-PowerShellDataFile (Join-Path $RepositoryRoot 'powerplatform/scripts/DeveloperPlatform.psd1')
 $cfg.RepositoryRoot=$RepositoryRoot
 foreach($k in @('SolutionSource','CanvasMsApp','CanvasEditable','CanvasReview','Inbound','Outbound','DeploymentSettings')){
  $map=@{SolutionSource='SolutionSourceRelativePath';CanvasMsApp='CanvasMsAppRelativePath';CanvasEditable='CanvasEditableRelativePath';CanvasReview='CanvasReviewRelativePath';Inbound='InboundRelativePath';Outbound='OutboundRelativePath';DeploymentSettings='DeploymentSettingsRelativePath'}
  $cfg[$k]=Join-Path $RepositoryRoot $cfg[$map[$k]]
 }
 $cfg
}
function Assert-Command { param([string]$Name) if(-not (Get-Command $Name -ErrorAction SilentlyContinue)){throw "Required command not found: $Name"} }
function Invoke-Native {
 param([string]$Command,[string[]]$Arguments)
 Write-Host "> $Command $($Arguments -join ' ')"
 & $Command @Arguments
 if($LASTEXITCODE -ne 0){throw "$Command failed with exit code $LASTEXITCODE"}
}
function Assert-CleanGitWorkingTree { param([string]$RepositoryRoot) Push-Location $RepositoryRoot; try { $s=git status --porcelain; if($s){throw 'Git working tree is not clean.'} } finally {Pop-Location} }
Export-ModuleMember -Function *
