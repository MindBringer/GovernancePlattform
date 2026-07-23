Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-RepositoryRoot {
    param([string]$StartPath = $PSScriptRoot)
    $item = Get-Item -LiteralPath $StartPath
    while ($null -ne $item) {
        if (Test-Path -LiteralPath (Join-Path $item.FullName '.git')) { return $item.FullName }
        $item = $item.Parent
    }
    throw "Repository root (.git) not found from '$StartPath'."
}

function Get-DeveloperPlatformConfig {
    param([string]$RepositoryRoot)
    $path = Join-Path $RepositoryRoot 'powerplatform/scripts/DeveloperPlatform.psd1'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Configuration not found: $path"
    }
    Import-PowerShellDataFile -LiteralPath $path
}

function Resolve-RepoPath {
    param([string]$RepositoryRoot, [Parameter(Mandatory)][string]$RelativePath)
    [System.IO.Path]::GetFullPath((Join-Path $RepositoryRoot $RelativePath))
}

function Assert-Command {
    param([Parameter(Mandatory)][string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found in PATH."
    }
}

function Invoke-Native {
    param([Parameter(Mandatory)][string]$Command, [Parameter(Mandatory)][string[]]$Arguments)
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE: $Command $($Arguments -join ' ')"
    }
}

function Remove-PlatformNoise {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    Get-ChildItem -LiteralPath $Path -Recurse -Force -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -in @('.DS_Store', 'Thumbs.db') } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}
