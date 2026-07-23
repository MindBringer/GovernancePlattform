[CmdletBinding()]param([string]$RepositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')),[string]$PacCommand='pac')
$ErrorActionPreference='Stop'; Import-Module (Join-Path $PSScriptRoot 'Common/DeveloperPlatform.Common.psm1') -Force
$c=Get-DeveloperPlatformConfig $RepositoryRoot; Assert-Command git; Assert-Command $PacCommand
Push-Location $RepositoryRoot
try {
 git diff --check; if($LASTEXITCODE -ne 0){throw 'git diff --check failed'}
 foreach($p in @($c.SolutionSource,$c.CanvasEditable,$c.CanvasReview)){if(-not(Test-Path $p)){throw "Required path missing: $p"}}
 Get-ChildItem (Join-Path $RepositoryRoot 'powerplatform/scripts') -Filter '*.ps1' -Recurse|ForEach-Object{[void][scriptblock]::Create((Get-Content $_.FullName -Raw))}
 foreach($t in @('Test-PowerShellSyntax.ps1','Test-Architecture.ps1','Test-ArchitectureConsistency.ps1')){$p=Join-Path $RepositoryRoot "provisioning/Scripts/$t";if(Test-Path $p){& $p;if(-not $?){throw "$t failed"}}}
 Write-Host 'Validation completed successfully.'
} finally {Pop-Location}
