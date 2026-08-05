[CmdletBinding()]
param(
    [string]$RepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')),
    [string]$CanvasArtifactRelativePath = 'powerplatform/solution/CanvasApps/gp_governanceportal_c93a1_DocumentUri.msapp'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepositoryRoot = [System.IO.Path]::GetFullPath($RepositoryRoot)
$canvasArtifact = Join-Path $RepositoryRoot $CanvasArtifactRelativePath

$candidates = @(
    (Join-Path $RepositoryRoot 'powerplatform/canvas/GovernancePortal'),
    (Join-Path $RepositoryRoot 'powerplatform/canvas-editable/GovernancePortal')
)

$sourceMatches = @($candidates | Where-Object {
    Test-Path -LiteralPath (Join-Path $_ 'Src/App.pa.yaml') -PathType Leaf
})

if ($sourceMatches.Count -ne 1) {
    throw "Expected exactly one canonical Canvas source tree. Found $($sourceMatches.Count):`n$($sourceMatches -join "`n")"
}

$canvasSource = $sourceMatches[0]
$paFiles = @(
    Get-ChildItem -LiteralPath (Join-Path $canvasSource 'Src') -Recurse -File -Filter '*.pa.yaml'
)

if ($paFiles.Count -eq 0) {
    throw "No Canvas SourceCode files found under $canvasSource."
}

if (-not (Test-Path -LiteralPath $canvasArtifact -PathType Leaf)) {
    throw "Packed Canvas artifact not found: $canvasArtifact. Run Pack-Canvas.ps1 before this validation."
}

$sourceText = ($paFiles | ForEach-Object {
    Get-Content -LiteralPath $_.FullName -Raw
}) -join "`n"

$requiredReferences = [System.Collections.Generic.List[string]]::new()

if ($sourceText -match '\bSystems\b') {
    $requiredReferences.Add('Systems')
}
if ($sourceText -match 'Office365Users\.') {
    $requiredReferences.Add('Office365Users')
}

if ($requiredReferences.Count -eq 0) {
    Write-Host "Canvas reference validation passed. No external Stage-3.5 references detected."
    exit 0
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

$archive = [System.IO.Compression.ZipFile]::OpenRead($canvasArtifact)
try {
    $dataSourceEntry = $archive.Entries |
        Where-Object {
            ($_.FullName -replace '\\', '/') -eq 'References/DataSources.json'
        } |
        Select-Object -First 1

    if ($null -eq $dataSourceEntry) {
        throw "Packed Canvas artifact contains no References/DataSources.json: $canvasArtifact"
    }

    $reader = [System.IO.StreamReader]::new($dataSourceEntry.Open())
    try {
        $dataSourceText = $reader.ReadToEnd()
    }
    finally {
        $reader.Dispose()
    }
}
finally {
    $archive.Dispose()
}

$missingReferences = @(
    $requiredReferences |
    Where-Object {
        $dataSourceText -notmatch [regex]::Escape($_)
    }
)

if ($missingReferences.Count -gt 0) {
    throw @"
Packed Canvas artifact is missing data-source references: $($missingReferences -join ', ').

Artifact:
$canvasArtifact

The SourceCode formulas are valid, but the canonical Canvas source still contains
an outdated reference package. Do not manually copy the .msapp into Solution/CanvasApps.

Refresh the canonical SourceCode once from the Studio-saved .msapp:

  pac canvas unpack `
    --msapp ./artifacts/inbound/GovernancePortal-3.5.1-studio-baseline.msapp `
    --sources ./artifacts/work/GovernancePortal-reference-refresh `
    --layout SourceCode `
    --overwrite

Then copy only the generated *.msapr file from the temporary source root into:

  $canvasSource

Keep the current Src/*.pa.yaml files unchanged and run Build.ps1 again.
"@
}

Write-Host "Canvas reference validation passed."
Write-Host "  Artifact:   $canvasArtifact"
Write-Host "  References: $($requiredReferences -join ', ')"
