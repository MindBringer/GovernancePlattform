[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")),
    [string]$PacCommand = "pac"
)

$ErrorActionPreference = "Stop"
$source = Join-Path $RepositoryRoot "powerplatform/canvas-editable/GovernancePortal"
$target = Join-Path $RepositoryRoot "powerplatform/solution/CanvasApps/gp_governanceportal_c93a1_DocumentUri.msapp"

if (-not (Test-Path $source)) { throw "Canvas source not found: $source" }

& $PacCommand canvas pack --sources $source --msapp $target --layout Experimental --overwrite
if ($LASTEXITCODE -ne 0) { throw "pac canvas pack failed with exit code $LASTEXITCODE" }

Write-Host "Canvas app packed: $target"
