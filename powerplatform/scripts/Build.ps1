[CmdletBinding()]
param(
    [string]$Version,
    [switch]$SkipVersionSync,
    [switch]$SkipSolutionIncrement,
    [switch]$SkipCanvasPack,
    [switch]$SkipSolutionPack,
    [string]$PacCommand = 'pac'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))

function Invoke-CheckedScript {
    param(
        [Parameter(Mandatory)][string]$ScriptName,
        [hashtable]$Parameters = @{}
    )
    $scriptPath = Join-Path $PSScriptRoot $ScriptName
    if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
        throw "Required build script not found: $scriptPath"
    }
    Write-Host "`n=== $ScriptName ==="
    & $scriptPath @Parameters
    if (-not $?) { throw "Build step failed: $ScriptName" }
}

if (-not $SkipVersionSync) {
    $versionParameters = @{
        RepositoryRoot = $repositoryRoot
        IncrementSolutionVersion = (-not $SkipSolutionIncrement)
    }
    if (-not [string]::IsNullOrWhiteSpace($Version)) {
        $versionParameters.Version = $Version
    }
    Invoke-CheckedScript -ScriptName 'Set-BuildVersion.ps1' -Parameters $versionParameters
}

Invoke-CheckedScript -ScriptName 'Validate-CanvasSource.ps1' -Parameters @{ RepositoryRoot = $repositoryRoot }

if (-not $SkipCanvasPack) {
    Invoke-CheckedScript -ScriptName 'Pack-Canvas.ps1' -Parameters @{
        RepositoryRoot = $repositoryRoot
        PacCommand = $PacCommand
    }

    Invoke-CheckedScript -ScriptName 'Validate-CanvasReferences.ps1' -Parameters @{
        RepositoryRoot = $repositoryRoot
    }
}
else {
    Write-Warning "Canvas packing and post-pack reference validation were skipped."
}

if (-not $SkipSolutionPack) {
    Invoke-CheckedScript -ScriptName 'Pack-Solution.ps1' -Parameters @{
        RepositoryRoot = $repositoryRoot
        PacCommand = $PacCommand
    }
}

Write-Host "`nBuild completed successfully."
