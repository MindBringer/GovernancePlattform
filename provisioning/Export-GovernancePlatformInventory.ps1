[CmdletBinding()]
param(
 [Parameter(Mandatory)][string]$SiteUrl,
 [string]$ClientId='05f890bd-e131-4d1f-ba60-1ffc0298d137',
 [switch]$Interactive,
 [switch]$DeviceLogin,
 [switch]$OSLogin
)
& (Join-Path $PSScriptRoot 'Reset-GovernancePlatform.ps1') `
 -SiteUrl $SiteUrl `
 -ClientId $ClientId `
 -Interactive:$Interactive `
 -DeviceLogin:$DeviceLogin `
 -OSLogin:$OSLogin `
 -AssessmentOnly
