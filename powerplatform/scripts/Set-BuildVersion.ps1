[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$RepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')),
    [string]$Version
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepositoryRoot = [System.IO.Path]::GetFullPath($RepositoryRoot)
$versionFile = Join-Path $RepositoryRoot 'powerplatform/VERSION'

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

if ([string]::IsNullOrWhiteSpace($Version)) {
    if (-not (Test-Path -LiteralPath $versionFile -PathType Leaf)) {
        throw "Version file not found: $versionFile. Pass -Version or create powerplatform/VERSION."
    }
    $Version = (Get-Content -LiteralPath $versionFile -Raw).Trim()
}

$semVerPattern = '^(?<major>0|[1-9]\d*)\.(?<minor>0|[1-9]\d*)\.(?<patch>0|[1-9]\d*)(?:-(?<pre>[0-9A-Za-z.-]+))?(?:\+(?<meta>[0-9A-Za-z.-]+))?$'
$match = [regex]::Match($Version, $semVerPattern)
if (-not $match.Success) {
    throw "Version '$Version' is not valid Semantic Versioning."
}

$canvasSource = Resolve-CanvasSource -Root $RepositoryRoot
$appPath = Join-Path $canvasSource 'Src/App.pa.yaml'
$appText = Get-Content -LiteralPath $appPath -Raw

$appVersionPattern = 'Set\s*\(\s*gblAppVersion\s*,\s*"[^"]*"\s*\)\s*;'
$appVersionMatches = [regex]::Matches($appText, $appVersionPattern)
if ($appVersionMatches.Count -ne 1) {
    throw "Expected exactly one Set(gblAppVersion, ...) expression in $appPath; found $($appVersionMatches.Count)."
}

$updatedAppText = [regex]::Replace(
    $appText,
    $appVersionPattern,
    ('Set(gblAppVersion, "{0}");' -f $Version),
    1
)

if ($PSCmdlet.ShouldProcess($appPath, "Set Canvas version to $Version")) {
    [System.IO.File]::WriteAllText(
        $appPath,
        $updatedAppText,
        [System.Text.UTF8Encoding]::new($false)
    )
}

if ($PSCmdlet.ShouldProcess($versionFile, "Set repository version to $Version")) {
    [System.IO.File]::WriteAllText(
        $versionFile,
        "$Version`n",
        [System.Text.UTF8Encoding]::new($false)
    )
}

# Map SemVer to Dataverse's numeric four-part version.
# Example: 1.0.0-alpha.3.4.1 -> 1.0.0.30401
$major = [int]$match.Groups['major'].Value
$minor = [int]$match.Groups['minor'].Value
$patch = [int]$match.Groups['patch'].Value
$build = 0

$preRelease = $match.Groups['pre'].Value
if (-not [string]::IsNullOrWhiteSpace($preRelease)) {
    $numericParts = @(
        [regex]::Matches($preRelease, '\d+') |
        ForEach-Object { [int]$_.Value }
    )

    foreach ($part in $numericParts) {
        if ($part -gt 99) {
            throw "Prerelease numeric component '$part' exceeds 99 in version '$Version'."
        }
        $build = ($build * 100) + $part
    }
}

if ($build -gt 65535) {
    throw "Derived Dataverse build number '$build' exceeds 65535 for version '$Version'."
}

$solutionVersion = "$major.$minor.$patch.$build"
$solutionXmlPath = Join-Path $RepositoryRoot 'powerplatform/solution/Other/Solution.xml'

if (Test-Path -LiteralPath $solutionXmlPath -PathType Leaf) {
    [xml]$solutionXml = Get-Content -LiteralPath $solutionXmlPath -Raw
    $versionNode = $solutionXml.SelectSingleNode('//ImportExportXml/SolutionManifest/Version')
    if ($null -eq $versionNode) {
        throw "Solution version node not found in $solutionXmlPath."
    }

    $versionNode.InnerText = $solutionVersion

    if ($PSCmdlet.ShouldProcess($solutionXmlPath, "Set solution version to $solutionVersion")) {
        $settings = [System.Xml.XmlWriterSettings]::new()
        $settings.Indent = $true
        $settings.Encoding = [System.Text.UTF8Encoding]::new($false)

        $writer = [System.Xml.XmlWriter]::Create($solutionXmlPath, $settings)
        try {
            $solutionXml.Save($writer)
        }
        finally {
            $writer.Dispose()
        }
    }
}
else {
    Write-Warning "Solution.xml not found. Canvas and VERSION were updated, but no solution version was changed."
}

Write-Host "Version synchronized: Canvas=$Version; Solution=$solutionVersion"
