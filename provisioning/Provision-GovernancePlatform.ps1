<#
.SYNOPSIS
  Provisions Governance Platform 6.2.5 from its architecture model.
.DESCRIPTION
  Compiles JSON-compatible YAML architecture definitions into an idempotent SharePoint schema,
  publishes Canvas runtime metadata, assesses v4 migration candidates, and preserves incompatible fields.
#>
[CmdletBinding(SupportsShouldProcess=$true)]
param(
 [Parameter(Mandatory)][string]$SiteUrl,
 [string]$ClientId='05f890bd-e131-4d1f-ba60-1ffc0298d137',
 [switch]$Interactive,
 [switch]$DeviceLogin,
 [switch]$OSLogin,
 [switch]$DryRun,
 [switch]$SkipMetadata,
 [switch]$SkipWritePermissionTest,
 [switch]$AssessMigration,
 [string[]]$ApprovedMigrationIds,
 [switch]$ExportArtifacts
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$global:GPContext=[ordered]@{
 SiteUrl=$SiteUrl;ClientId=$ClientId;Interactive=$Interactive.IsPresent;DeviceLogin=$DeviceLogin.IsPresent;OSLogin=$OSLogin.IsPresent;DryRun=$DryRun.IsPresent
 SkipWritePermissionTest=$SkipWritePermissionTest.IsPresent;Root=$PSScriptRoot
 LogFile=(Join-Path $PSScriptRoot ("../Logs/GovernancePlatform-v6.2.5-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss')))
 FieldGroup='Governance Platform 6.2.5';SchemaVersion='6.2.5';StartedAt=(Get-Date)
}
foreach($m in @('Logging','Model','Compiler','Core','Schema','Metadata','Migration','Validation','Reporting')){
 Import-Module (Join-Path $PSScriptRoot "Modules/$m.psm1") -Force -DisableNameChecking
}
try{
 Write-GPLog 'Start Governance Platform 6.2.5 provisioning.' INFO
 $model=Get-GPArchitectureModel -Root $PSScriptRoot
 Test-GPArchitectureModel $model|Out-Null
 $schema=Compile-GPArchitecture $model
 Write-GPLog "Architecture compiled: $($schema.Lists.Count) lists/libraries." SUCCESS
 Test-GPPreflight
 Write-GPLog 'Stage: SharePoint authentication.' INFO
 Connect-GPSite
 Write-GPLog 'Stage: permission validation.' INFO
 Test-GPWritePermission
 Write-GPLog 'Stage: SharePoint schema.' INFO
 Ensure-GPSchema $schema
 Write-GPLog 'Stage: runtime metadata.' INFO
 if(-not $SkipMetadata){Publish-GPMetadata $model}else{Write-GPLog 'Metadata publishing skipped.' SKIP}
 Write-GPLog 'Stage: migration assessment and approved migrations.' INFO
 if($AssessMigration){Invoke-GPMigrationAssessment $model -Export:$ExportArtifacts|Out-Null}
 Invoke-GPApprovedMigrations $model $ApprovedMigrationIds
 Write-GPLog 'Stage: validation.' INFO
 Test-GPCompiledSchema $schema
 if(-not $SkipMetadata){Test-GPMetadataIntegrity}
 Set-GPSchemaVersion $model.schemaVersion
 Write-GPLog 'Stage: artifact export.' INFO
 if($ExportArtifacts){Export-GPCompiledSchema $schema;Export-GPDataDictionary $schema}
 $duration=(Get-Date)-$global:GPContext.StartedAt
 Write-GPLog ("Provisioning completed successfully. Duration: {0:hh\:mm\:ss}; lists/libraries: {1}; warnings are listed above; log: {2}" -f $duration,$schema.Lists.Count,$global:GPContext.LogFile) SUCCESS
}catch{
 Write-GPLog "Provisioning failed: $($_.Exception.Message)" ERROR
 throw
}finally{
 Disconnect-PnPOnline -ErrorAction SilentlyContinue
}
