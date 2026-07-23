[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$steps = @(
    'Validate-CanvasSource.ps1',
    'Pack-Canvas.ps1',
    'Pack-Solution.ps1'
)

foreach ($step in $steps) {
    $path = Join-Path $PSScriptRoot $step
    Write-Host "`n=== $step ==="
    & $path
}

Write-Host "`nBuild completed successfully."
