[CmdletBinding()]
param(
    [string]$RepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepositoryRoot = [System.IO.Path]::GetFullPath($RepositoryRoot)

function Resolve-CanvasSource {
    param([Parameter(Mandatory)][string]$Root)

    $candidates = @(
        (Join-Path $Root 'powerplatform/canvas-editable/GovernancePortal'),
        (Join-Path $Root 'powerplatform/canvas/GovernancePortal')
    )

    $matches = @($candidates | Where-Object {
        Test-Path -LiteralPath (Join-Path $_ 'Src/App.pa.yaml') -PathType Leaf
    })

    if ($matches.Count -eq 0) {
        throw "Canvas source not found. Checked:`n$($candidates -join "`n")"
    }
    if ($matches.Count -gt 1) {
        throw "Multiple Canvas source trees found. Keep only one canonical source:`n$($matches -join "`n")"
    }

    return $matches[0]
}

$canvasSource = Resolve-CanvasSource -Root $RepositoryRoot
$src = Join-Path $canvasSource 'Src'
$appPath = Join-Path $src 'App.pa.yaml'
$versionFile = Join-Path $RepositoryRoot 'powerplatform/VERSION'

if (-not (Test-Path -LiteralPath $versionFile -PathType Leaf)) {
    throw "Version file missing: $versionFile"
}

$configuredVersion = (Get-Content -LiteralPath $versionFile -Raw).Trim()
if ($configuredVersion -notmatch '^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$') {
    throw "Invalid Semantic Version in ${versionFile}: '$configuredVersion'"
}

$legacyFxFiles = @(
    Get-ChildItem -LiteralPath $canvasSource -Recurse -File -Filter '*.fx.yaml' -ErrorAction SilentlyContinue
)
if ($legacyFxFiles.Count -gt 0) {
    throw "Legacy *.fx.yaml files found:`n$($legacyFxFiles.FullName -join "`n")"
}

$paFiles = @(
    Get-ChildItem -LiteralPath $src -Recurse -File -Filter '*.pa.yaml' -ErrorAction Stop
)
if ($paFiles.Count -lt 2) {
    throw "Canvas source is incomplete. Expected App.pa.yaml and at least one additional *.pa.yaml file."
}

foreach ($file in $paFiles) {
    if ($file.Length -eq 0) {
        throw "Empty Canvas source file: $($file.FullName)"
    }

    $text = Get-Content -LiteralPath $file.FullName -Raw

    if ($text -match '(?m)^(<<<<<<<|=======|>>>>>>>)') {
        throw "Unresolved Git merge markers in $($file.FullName)"
    }

    if ($text.Contains("`t")) {
        throw "Tab character found in YAML source: $($file.FullName). Use spaces only."
    }
}

$appText = Get-Content -LiteralPath $appPath -Raw
$versionMatches = [regex]::Matches(
    $appText,
    'Set\s*\(\s*gblAppVersion\s*[,;]\s*"(?<version>[^"]+)"\s*\)\s*;?'
)

if ($versionMatches.Count -ne 1) {
    throw "Expected exactly one Set(gblAppVersion, ...) expression in $appPath; found $($versionMatches.Count)."
}

$canvasVersion = $versionMatches[0].Groups['version'].Value
if ($canvasVersion -ne $configuredVersion) {
    throw "Version mismatch: powerplatform/VERSION='$configuredVersion'; App.pa.yaml='$canvasVersion'. Run Set-BuildVersion.ps1."
}

# Guard against accidentally checking in generated platform noise.
$noiseNames = @(
    '.DS_Store',
    'Thumbs.db'
)
$noiseFiles = @(
    Get-ChildItem -LiteralPath $canvasSource -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $noiseNames -contains $_.Name }
)
if ($noiseFiles.Count -gt 0) {
    throw "Platform noise found in Canvas source:`n$($noiseFiles.FullName -join "`n")"
}

$solutionXmlPath = Join-Path $RepositoryRoot 'powerplatform/solution/Other/Solution.xml'
if (-not (Test-Path -LiteralPath $solutionXmlPath -PathType Leaf)) {
    throw "Solution manifest not found: $solutionXmlPath"
}

[xml]$solutionXml = Get-Content -LiteralPath $solutionXmlPath -Raw
$solutionVersionNode = $solutionXml.SelectSingleNode('//ImportExportXml/SolutionManifest/Version')
if ($null -eq $solutionVersionNode -or [string]::IsNullOrWhiteSpace($solutionVersionNode.InnerText)) {
    throw "Solution version is missing in $solutionXmlPath"
}
if ($solutionVersionNode.InnerText -notmatch '^\d+\.\d+\.\d+\.\d+$') {
    throw "Solution version '$($solutionVersionNode.InnerText)' is not numeric four-part format."
}

Write-Host "Canvas validation passed."
Write-Host "  Source:   $canvasSource"
Write-Host "  Files:    $($paFiles.Count)"
Write-Host "  Canvas:   $canvasVersion"
Write-Host "  Solution: $($solutionVersionNode.InnerText)"
