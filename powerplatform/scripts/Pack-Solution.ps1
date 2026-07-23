[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot 'Common.ps1')

$root = Get-RepositoryRoot
$config = Get-DeveloperPlatformConfig -RepositoryRoot $root
Assert-Command pac

$solutionSource = Resolve-RepoPath $root $config.SolutionSourceRelativePath
$outbound = Resolve-RepoPath $root $config.OutboundRelativePath
$outFile = Join-Path $outbound "$($config.SolutionUniqueName)_$($config.Version).zip"

New-Item -ItemType Directory -Path $outbound -Force | Out-Null
Remove-Item -LiteralPath $outFile -Force -ErrorAction SilentlyContinue
Remove-PlatformNoise -Path $solutionSource

Invoke-Native pac @(
    'solution', 'pack',
    '--folder', $solutionSource,
    '--zipfile', $outFile,
    '--packagetype', 'Unmanaged'
)

if (-not (Test-Path -LiteralPath $outFile -PathType Leaf)) {
    throw "Solution package was not created: $outFile"
}
Write-Host "Solution package created: $outFile"
