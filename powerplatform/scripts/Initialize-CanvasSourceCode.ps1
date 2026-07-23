[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$MsAppPath,

    [switch]$Force
)

. (Join-Path $PSScriptRoot 'Common.ps1')

$root = Get-RepositoryRoot
$config = Get-DeveloperPlatformConfig -RepositoryRoot $root
Assert-Command pac

$input = [System.IO.Path]::GetFullPath($MsAppPath)
$target = Resolve-RepoPath $root $config.CanvasSourceRelativePath
$backupRoot = Resolve-RepoPath $root $config.InboundRelativePath
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path $backupRoot "canvas-source-before-$timestamp"

if (-not (Test-Path -LiteralPath $input -PathType Leaf)) {
    throw "Fresh .msapp export not found: $input"
}
if ([System.IO.Path]::GetExtension($input) -ne '.msapp') {
    throw "Use a fresh Canvas app export with the .msapp extension. Received: $input"
}

if (Test-Path -LiteralPath $target) {
    if (-not $Force) {
        throw "Target already exists: $target. Re-run with -Force after reviewing/committing current work."
    }
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    Copy-Item -LiteralPath $target -Destination $backup -Recurse -Force
    Remove-Item -LiteralPath $target -Recurse -Force
    Write-Host "Existing Canvas source backed up to: $backup"
}

New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force | Out-Null
Invoke-Native pac @(
    'canvas', 'unpack',
    '--msapp', $input,
    '--sources', $target,
    '--layout', 'SourceCode',
    '--overwrite'
)

Remove-PlatformNoise -Path $target
& (Join-Path $PSScriptRoot 'Validate-CanvasSource.ps1')
Write-Host "Fresh SourceCode baseline created: $target"
