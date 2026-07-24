[CmdletBinding()]
param(
    [string]$RepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')),
    [string]$PacCommand = 'pac',
    [ValidateSet('Experimental', 'SourceCode')]
    [string]$CanvasLayout = 'SourceCode'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepositoryRoot = [System.IO.Path]::GetFullPath($RepositoryRoot)

$candidates = @(
    (Join-Path $RepositoryRoot 'powerplatform/canvas-editable/GovernancePortal'),
    (Join-Path $RepositoryRoot 'powerplatform/canvas/GovernancePortal')
)
$matches = @($candidates | Where-Object {
    Test-Path -LiteralPath (Join-Path $_ 'Src/App.pa.yaml') -PathType Leaf
})

if ($matches.Count -ne 1) {
    throw "Expected exactly one Canvas source tree. Found $($matches.Count):`n$($matches -join "`n")"
}

$source = $matches[0]
$target = Join-Path $RepositoryRoot 'powerplatform/solution/CanvasApps/gp_governanceportal_c93a1_DocumentUri.msapp'
$targetDirectory = Split-Path -Parent $target
New-Item -ItemType Directory -Force -Path $targetDirectory | Out-Null

$pac = Get-Command $PacCommand -ErrorAction SilentlyContinue
if ($null -eq $pac) {
    throw "PAC CLI command '$PacCommand' was not found in PATH."
}

& $PacCommand canvas pack `
    --sources $source `
    --msapp $target `
    --layout $CanvasLayout `
    --overwrite

if ($LASTEXITCODE -ne 0) {
    throw "pac canvas pack failed with exit code $LASTEXITCODE"
}

if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
    throw "PAC reported success, but the .msapp file was not created: $target"
}

Write-Host "Canvas app packed: $target"
