[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot 'Common.ps1')

$root = Get-RepositoryRoot
$config = Get-DeveloperPlatformConfig -RepositoryRoot $root
Assert-Command pac

$source = Resolve-RepoPath $root $config.CanvasSourceRelativePath
$work = Resolve-RepoPath $root $config.WorkRelativePath
$solutionArtifact = Resolve-RepoPath $root $config.CanvasSolutionArtifactRelativePath
$stagedMsApp = Join-Path $work "$($config.CanvasAppName).msapp"
$verification = Join-Path $work "$($config.CanvasAppName)-verify"

& (Join-Path $PSScriptRoot 'Validate-CanvasSource.ps1')

New-Item -ItemType Directory -Path $work -Force | Out-Null
New-Item -ItemType Directory -Path (Split-Path $solutionArtifact -Parent) -Force | Out-Null
Remove-Item -LiteralPath $stagedMsApp -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $verification -Recurse -Force -ErrorAction SilentlyContinue
Remove-PlatformNoise -Path $source

Invoke-Native pac @(
    'canvas', 'pack',
    '--sources', $source,
    '--msapp', $stagedMsApp,
    '--layout', 'SourceCode',
    '--overwrite'
)

if (-not (Test-Path -LiteralPath $stagedMsApp -PathType Leaf)) {
    throw "PAC did not create the staged .msapp: $stagedMsApp"
}

# Round-trip verification: proves that the binary was built from Src/*.pa.yaml.
Invoke-Native pac @(
    'canvas', 'unpack',
    '--msapp', $stagedMsApp,
    '--sources', $verification,
    '--layout', 'SourceCode',
    '--overwrite'
)

$verifiedApp = Join-Path $verification 'Src/App.pa.yaml'
if (-not (Test-Path -LiteralPath $verifiedApp -PathType Leaf)) {
    throw "Round-trip verification failed: missing $verifiedApp"
}
$verifiedText = Get-Content -LiteralPath $verifiedApp -Raw
if ($verifiedText -notmatch [regex]::Escape([string]$config.Version)) {
    throw "Round-trip verification failed: version '$($config.Version)' not found in packed app."
}

# The unpacked solution expects the compiled canvas payload under its DocumentUri artifact name.
Copy-Item -LiteralPath $stagedMsApp -Destination $solutionArtifact -Force
Write-Host "Canvas packed and verified: $stagedMsApp"
Write-Host "Solution canvas artifact updated: $solutionArtifact"
