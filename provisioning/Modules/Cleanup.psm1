function Get-GPCleanupConfig {
 [CmdletBinding()]param()
 return (Read-GPJsonYaml (Join-Path $global:GPContext.Root '../architecture/cleanup.yaml'))
}
function Test-GPProtectedLibraries {
 [CmdletBinding()]param([hashtable]$Cleanup)
 foreach($name in $Cleanup.protectedLibraries){
   $list=Get-PnPList -Identity $name -ErrorAction SilentlyContinue
   if(-not $list){throw "Protected library '$name' was not found."}
   if($list.BaseTemplate -ne 101){throw "Protected object '$name' is not a document library."}
 }
 Write-GPLog ("Protected libraries validated: {0}." -f ($Cleanup.protectedLibraries -join ', ')) SUCCESS
}
function Export-GPCleanupInventory {
 [CmdletBinding()]param([hashtable]$Schema,[hashtable]$Cleanup)
 $dir=Join-Path $global:GPContext.Root '../generated/cleanup';if(-not(Test-Path $dir)){New-Item -ItemType Directory -Path $dir -Force|Out-Null}
 $stamp=Get-Date -Format 'yyyyMMdd-HHmmss';$listRows=@();$fieldRows=@();$viewRows=@();$fileRows=@();$assessment=@();$total=@($Schema.Lists).Count;$position=0
 foreach($ld in $Schema.Lists){
   $position++;Write-GPLog ("Cleanup assessment {0}/{1}: {2}" -f $position,$total,$ld.Title) INFO
   $list=Get-PnPList -Identity $ld.Title -Includes BaseTemplate,ItemCount,DefaultViewUrl -ErrorAction SilentlyContinue;if(-not $list){continue}
   $isLibrary=($list.BaseTemplate -eq 101);$listRows+=[pscustomobject]@{Title=$ld.Title;BaseTemplate=$list.BaseTemplate;ItemCount=$list.ItemCount;ProtectedLibrary=($Cleanup.protectedLibraries -contains $ld.Title);DefaultViewUrl=$list.DefaultViewUrl}
   $managedFields=@($ld.Fields.InternalName);foreach($field in @(Get-PnPField -List $ld.Title)){
     $managed=($managedFields -contains $field.InternalName);$protected=($Cleanup.protectedFields -contains $field.InternalName)-or $field.Sealed -or $field.ReadOnlyField
     $action=if($managed){'KeepManaged'}elseif($protected){'KeepProtected'}elseif($isLibrary){'LibraryReview'}else{'RemoveField'}
     $fieldRows+=[pscustomobject]@{List=$ld.Title;InternalName=$field.InternalName;Title=$field.Title;Type=$field.TypeAsString;Managed=$managed;Protected=$protected;Action=$action}
     $assessment+=[pscustomobject]@{List=$ld.Title;Kind='Field';Name=$field.InternalName;Action=$action;Reason=if($managed){'In target schema'}elseif($protected){'System/protected'}elseif($isLibrary){'Protected library metadata requires explicit review'}else{'Not in target schema'}}
   }
   $managedViews=@($ld.Views.Name);foreach($view in @(Get-PnPView -List $ld.Title)){
     $managed=($managedViews -contains $view.Title);$protected=$view.PersonalView -or $view.DefaultView -or ($Cleanup.protectedViews -contains $view.Title)
     $action=if($managed){'KeepManaged'}elseif($protected){'KeepProtected'}elseif($isLibrary){'LibraryReview'}else{'RemoveView'}
     $viewRows+=[pscustomobject]@{List=$ld.Title;Title=$view.Title;Managed=$managed;Protected=$protected;Personal=$view.PersonalView;Default=$view.DefaultView;Action=$action}
     $assessment+=[pscustomobject]@{List=$ld.Title;Kind='View';Name=$view.Title;Action=$action;Reason=if($managed){'In target schema'}elseif($protected){'Default/personal/protected'}elseif($isLibrary){'Protected library view requires explicit review'}else{'Not in target schema'}}
   }
   if($isLibrary -and $Cleanup.protectedLibraries -contains $ld.Title){foreach($item in @(Get-PnPListItem -List $ld.Title -PageSize 2000 -Fields FileLeafRef,FileRef,UniqueId,File_x0020_Size,Modified,Editor -ErrorAction SilentlyContinue)){if($item.FileSystemObjectType -ne 'File'){continue};$v=$item.FieldValues;$fileRows+=[pscustomobject]@{Library=$ld.Title;FileName=$v.FileLeafRef;ServerRelativeUrl=$v.FileRef;ItemID=$item.Id;UniqueId=$v.UniqueId;FileSize=$v.File_x0020_Size;Modified=$v.Modified;ModifiedBy=$v.Editor.Email}}}
 }
 $listRows|Export-Csv (Join-Path $dir "Inventory-Lists-$stamp.csv") -NoTypeInformation -Encoding utf8
 $fieldRows|Export-Csv (Join-Path $dir "Inventory-Fields-$stamp.csv") -NoTypeInformation -Encoding utf8
 $viewRows|Export-Csv (Join-Path $dir "Inventory-Views-$stamp.csv") -NoTypeInformation -Encoding utf8
 $fileRows|Export-Csv (Join-Path $dir "Inventory-LibraryFiles-$stamp.csv") -NoTypeInformation -Encoding utf8
 $path=Join-Path $dir "CleanupAssessment-$stamp.csv";$assessment|Export-Csv $path -NoTypeInformation -Encoding utf8
 Write-GPLog "Cleanup assessment exported: $path" SUCCESS;return @($assessment)
}
function Clear-GPListItems {
 [CmdletBinding()]param([string]$ListTitle,[switch]$PermanentDelete)
 $items=@(Get-PnPListItem -List $ListTitle -PageSize 2000 -ErrorAction Stop)
 if($items.Count -eq 0){Write-GPLog "List $ListTitle is already empty." SKIP;return 0}
 if($global:GPContext.DryRun){Write-GPLog ("Would remove {0} item(s) from {1}." -f $items.Count,$ListTitle) DRYRUN;return $items.Count}
 $batch=New-PnPBatch
 foreach($item in $items){if($PermanentDelete){Remove-PnPListItem -List $ListTitle -Identity $item.Id -Batch $batch}else{Remove-PnPListItem -List $ListTitle -Identity $item.Id -Recycle -Batch $batch}}
 Invoke-PnPBatch -Batch $batch
 Write-GPLog ("Removed {0} item(s) from {1}." -f $items.Count,$ListTitle) SUCCESS;return $items.Count
}
function Remove-GPUnmanagedSchema {
 [CmdletBinding()]param([hashtable]$Schema,[hashtable]$Cleanup,[switch]$RemoveFields,[switch]$RemoveViews,[switch]$CleanupLibraryMetadata)
 $stats=[ordered]@{FieldsRemoved=0;ViewsRemoved=0;FieldsSkipped=0;ViewsSkipped=0}
 foreach($ld in $Schema.Lists){
   $list=Get-PnPList -Identity $ld.Title -Includes BaseTemplate -ErrorAction SilentlyContinue;if(-not $list){continue};$isLibrary=($list.BaseTemplate -eq 101)
   if($isLibrary -and ($Cleanup.protectedLibraries -contains $ld.Title) -and -not $CleanupLibraryMetadata){Write-GPLog "Protected library schema skipped: $($ld.Title)." SKIP;continue}
   if($RemoveFields){$managed=@($ld.Fields.InternalName);foreach($field in @(Get-PnPField -List $ld.Title)){if($managed -contains $field.InternalName -or $Cleanup.protectedFields -contains $field.InternalName -or $field.Sealed -or $field.ReadOnlyField){$stats.FieldsSkipped++;continue};if($global:GPContext.DryRun){Write-GPLog "Would remove unmanaged field $($ld.Title).$($field.InternalName)." DRYRUN}else{Remove-PnPField -List $ld.Title -Identity $field.InternalName -Force;Write-GPLog "Removed unmanaged field $($ld.Title).$($field.InternalName)." SUCCESS};$stats.FieldsRemoved++}}
   if($RemoveViews){$managed=@($ld.Views.Name);foreach($view in @(Get-PnPView -List $ld.Title)){if($managed -contains $view.Title -or $view.PersonalView -or $view.DefaultView -or $Cleanup.protectedViews -contains $view.Title){$stats.ViewsSkipped++;continue};if($global:GPContext.DryRun){Write-GPLog "Would remove unmanaged view $($ld.Title)/$($view.Title)." DRYRUN}else{Remove-PnPView -List $ld.Title -Identity $view.Id -Force;Write-GPLog "Removed unmanaged view $($ld.Title)/$($view.Title)." SUCCESS};$stats.ViewsRemoved++}}
 }
 return $stats
}
Export-ModuleMember -Function Get-GPCleanupConfig,Test-GPProtectedLibraries,Export-GPCleanupInventory,Clear-GPListItems,Remove-GPUnmanagedSchema
