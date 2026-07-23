[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot 'Common.ps1')

$root = Get-RepositoryRoot
$config = Get-DeveloperPlatformConfig -RepositoryRoot $root
$source = Resolve-RepoPath $root $config.CanvasSourceRelativePath

if (-not (Test-Path -LiteralPath $source -PathType Container)) {
    throw "Canvas SourceCode directory not found: $source"
}

$src = Join-Path $source 'Src'
$app = Join-Path $src 'App.pa.yaml'
if (-not (Test-Path -LiteralPath $app -PathType Leaf)) {
    throw "Missing canonical source file: $app"
}

$fxFiles = @(Get-ChildItem -LiteralPath $source -Recurse -File -Filter '*.fx.yaml' -ErrorAction SilentlyContinue)
if ($fxFiles.Count -gt 0) {
    throw "Retired Experimental sources found. Remove all *.fx.yaml files:`n$($fxFiles.FullName -join "`n")"
}

$nestedOtherSources = Join-Path $source 'Other/Src'
if (Test-Path -LiteralPath $nestedOtherSources) {
    throw "Mixed source layouts detected: $nestedOtherSources. Recreate the baseline with SourceCode layout."
}

$paFiles = @(Get-ChildItem -LiteralPath $src -Recurse -File -Filter '*.pa.yaml')
if ($paFiles.Count -lt 2) {
    throw "Canvas source appears incomplete: expected App.pa.yaml and at least one screen/component file."
}

$versionPattern = [regex]::Escape([string]$config.Version)
$appText = Get-Content -LiteralPath $app -Raw
if ($appText -notmatch $versionPattern) {
    throw "Configured version '$($config.Version)' is not present in Src/App.pa.yaml."
}

Remove-PlatformNoise -Path $source
Write-Host "Canvas SourceCode validation passed. Files=$($paFiles.Count); Version=$($config.Version)"
