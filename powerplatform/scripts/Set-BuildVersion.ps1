[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$RepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')),
    [string]$Version,
    [bool]$IncrementSolutionVersion = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepositoryRoot = [System.IO.Path]::GetFullPath($RepositoryRoot)
$versionFile = Join-Path $RepositoryRoot 'powerplatform/VERSION'
$configPath = Join-Path $RepositoryRoot 'powerplatform/scripts/DeveloperPlatform.psd1'

$candidates = @(
    (Join-Path $RepositoryRoot 'powerplatform/canvas/GovernancePortal'),
    (Join-Path $RepositoryRoot 'powerplatform/canvas-editable/GovernancePortal')
)
$matches = @($candidates | Where-Object {
    Test-Path -LiteralPath (Join-Path $_ 'Src/App.pa.yaml') -PathType Leaf
})
if ($matches.Count -ne 1) {
    throw "Expected exactly one canonical Canvas source tree. Found $($matches.Count):`n$($matches -join "`n")"
}
$canvasSource = $matches[0]

if ([string]::IsNullOrWhiteSpace($Version)) {
    if (-not (Test-Path -LiteralPath $versionFile -PathType Leaf)) {
        throw "Version file not found: $versionFile"
    }
    $Version = (Get-Content -LiteralPath $versionFile -Raw).Trim()
}

if ($Version -notmatch '^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$') {
    throw "Version '$Version' is not valid Semantic Versioning."
}

$appPath = Join-Path $canvasSource 'Src/App.pa.yaml'
$appText = Get-Content -LiteralPath $appPath -Raw
$pattern = 'Set\s*\(\s*gblAppVersion\s*[,;]\s*"[^"]*"\s*\)\s*;?'
if ([regex]::Matches($appText, $pattern).Count -ne 1) {
    throw "Expected exactly one Set(gblAppVersion, ...) expression in $appPath."
}
$appText = [regex]::Replace($appText, $pattern, ('Set(gblAppVersion, "{0}");' -f $Version), 1)

[System.IO.File]::WriteAllText($appPath, $appText, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($versionFile, "$Version`n", [System.Text.UTF8Encoding]::new($false))

if (Test-Path -LiteralPath $configPath -PathType Leaf) {
    $configText = Get-Content -LiteralPath $configPath -Raw
    $configText = [regex]::Replace(
        $configText,
        "(?m)^(\s*Version\s*=\s*)'[^']+'",
        ('$1' + "'$Version'"),
        1
    )
    [System.IO.File]::WriteAllText($configPath, $configText, [System.Text.UTF8Encoding]::new($false))
}

$solutionXmlPath = Join-Path $RepositoryRoot 'powerplatform/solution/Other/Solution.xml'
if (-not (Test-Path -LiteralPath $solutionXmlPath -PathType Leaf)) {
    throw "Solution manifest not found: $solutionXmlPath"
}

[xml]$solutionXml = Get-Content -LiteralPath $solutionXmlPath -Raw
$versionNode = $solutionXml.SelectSingleNode('//ImportExportXml/SolutionManifest/Version')
if ($null -eq $versionNode) { throw "Solution version node not found in $solutionXmlPath" }

$current = [version]$versionNode.InnerText
if ($IncrementSolutionVersion) {
    if ($current.Revision -ge 65535) {
        throw "Solution build number has reached 65535."
    }
    $next = [version]::new($current.Major, $current.Minor, $current.Build, $current.Revision + 1)
}
else {
    $next = $current
}
$versionNode.InnerText = $next.ToString()

$settings = [System.Xml.XmlWriterSettings]::new()
$settings.Indent = $true
$settings.Encoding = [System.Text.UTF8Encoding]::new($false)
$writer = [System.Xml.XmlWriter]::Create($solutionXmlPath, $settings)
try { $solutionXml.Save($writer) } finally { $writer.Dispose() }

Write-Host "Version synchronized: Canvas=$Version; Solution=$next"
