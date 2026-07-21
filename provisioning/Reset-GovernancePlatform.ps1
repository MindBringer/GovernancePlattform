<#
.SYNOPSIS
  Assesses, resets and cleans Governance Platform lists while preserving protected document libraries.
#>
[CmdletBinding()]
param(
 [Parameter(Mandatory)][string]$SiteUrl,
 [string]$ClientId='05f890bd-e131-4d1f-ba60-1ffc0298d137',
 [switch]$Interactive,[switch]$DeviceLogin,[switch]$OSLogin,[switch]$DryRun,[switch]$AssessmentOnly,[switch]$ResetLists,
 [switch]$RemoveUnmanagedFields,[switch]$RemoveUnmanagedViews,[switch]$CleanupLibraryMetadata,
 [switch]$PermanentDelete,[string]$ConfirmationToken
)
Set-StrictMode -Version Latest;$ErrorActionPreference='Stop'
$global:GPContext=[ordered]@{SiteUrl=$SiteUrl;ClientId=$ClientId;Interactive=$Interactive.IsPresent;DeviceLogin=$DeviceLogin.IsPresent;OSLogin=$OSLogin.IsPresent;DryRun=$DryRun.IsPresent;Root=$PSScriptRoot;SkipWritePermissionTest=$false;LogFile=(Join-Path $PSScriptRoot ("../Logs/GovernancePlatform-reset-v6.2.5-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss')));FieldGroup='Governance Platform 6.2.5';SchemaVersion='6.2.5';StartedAt=(Get-Date)}
foreach($m in @('Logging','Model','Compiler','Core','Cleanup')){Import-Module (Join-Path $PSScriptRoot "Modules/$m.psm1") -Force -DisableNameChecking}
try{
 Write-GPLog 'Start Governance Platform 6.2.5 cleanup/reset.' INFO
 $model=Get-GPArchitectureModel -Root $PSScriptRoot;Test-GPArchitectureModel $model|Out-Null;$schema=Compile-GPArchitecture $model;$cleanup=Get-GPCleanupConfig
 Test-GPPreflight;Write-GPLog 'Stage: SharePoint authentication.' INFO;Connect-GPSite;Test-GPProtectedLibraries $cleanup
 $actions=@();if($ResetLists){$actions+='ResetLists'};if($RemoveUnmanagedFields){$actions+='RemoveUnmanagedFields'};if($RemoveUnmanagedViews){$actions+='RemoveUnmanagedViews'}
 if($DryRun){Write-GPLog ("Dry run enabled; no destructive write will be executed. Requested actions: {0}." -f $(if($actions.Count){$actions -join ', '}else{'AssessmentOnly'})) INFO}
 elseif($actions.Count -gt 0){if($ConfirmationToken -ne $cleanup.confirmationToken){throw ("Requested destructive action(s): {0}. Re-run with -ConfirmationToken '{1}'." -f ($actions -join ', '),$cleanup.confirmationToken)};Write-GPLog ("Destructive actions confirmed: {0}." -f ($actions -join ', ')) WARN;Test-GPWritePermission}
 Write-GPLog 'Stage 1/5: inventory and assessment.' INFO;$null=Export-GPCleanupInventory -Schema $schema -Cleanup $cleanup
 if($AssessmentOnly -and $actions.Count -eq 0){Write-GPLog 'Assessment-only run completed.' SUCCESS;return}
 Write-GPLog 'Stage 2/5: protected-library safety check.' INFO;Test-GPProtectedLibraries $cleanup
 if($ResetLists){Write-GPLog 'Stage 3/5: reset generic list data.' INFO;$targets=@($schema.Lists|Where-Object{$_.Template -eq 'GenericList'});$i=0;foreach($ld in $targets){$i++;Write-GPLog ("Reset list {0}/{1}: {2}" -f $i,$targets.Count,$ld.Title) INFO;$null=Clear-GPListItems -ListTitle $ld.Title -PermanentDelete:$PermanentDelete}}
 else{Write-GPLog 'Stage 3/5: list reset not requested.' SKIP}
 if($RemoveUnmanagedFields -or $RemoveUnmanagedViews){Write-GPLog 'Stage 4/5: unmanaged schema cleanup.' INFO;$stats=Remove-GPUnmanagedSchema -Schema $schema -Cleanup $cleanup -RemoveFields:$RemoveUnmanagedFields -RemoveViews:$RemoveUnmanagedViews -CleanupLibraryMetadata:$CleanupLibraryMetadata;Write-GPLog ("Cleanup summary: fields={0}, views={1}, skipped fields={2}, skipped views={3}." -f $stats.FieldsRemoved,$stats.ViewsRemoved,$stats.FieldsSkipped,$stats.ViewsSkipped) SUCCESS}
 else{Write-GPLog 'Stage 4/5: schema cleanup not requested.' SKIP}
 Write-GPLog 'Stage 5/5: completed.' SUCCESS
}catch{Write-GPLog "Cleanup/reset failed: $($_.Exception.Message)" ERROR;throw}finally{Disconnect-PnPOnline -ErrorAction SilentlyContinue}
