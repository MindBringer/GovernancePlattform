function Get-GPMigrationPlan {
 [CmdletBinding()]
 param([hashtable]$Model)
 return @($Model.Migration.rules|ForEach-Object{[pscustomobject]@{
   Id=$_.id;List=$_.list;Field=$_.field;CurrentType=$_.currentType;TargetType=$_.targetType
   Strategy=$_.strategy;AutoExecute=[bool]$_.autoExecute;Reason=$_.reason
 }})
}
function Invoke-GPMigrationAssessment {
 [CmdletBinding()]
 param([hashtable]$Model,[switch]$Export)
 $rows=[System.Collections.Generic.List[object]]::new()
 foreach($r in $Model.Migration.rules){
   $list=Get-PnPList -Identity $r.list -ErrorAction SilentlyContinue
   $field=if($list){Get-PnPField -List $r.list -Identity $r.field -ErrorAction SilentlyContinue}else{$null}
   $status=if(-not $list){'ListMissing'}elseif(-not $field){'FieldMissing'}elseif(-not $r.currentType){'Candidate'}elseif($field.TypeAsString -eq $r.currentType){'Candidate'}else{"CurrentType:$($field.TypeAsString)"}
   $rows.Add([pscustomobject]@{Id=$r.id;List=$r.list;Field=$r.field;Detected=$status;Strategy=$r.strategy;AutoExecute=$r.autoExecute;Reason=$r.reason})
   Write-GPLog "$($r.id) $($r.list).$($r.field): $status; strategy=$($r.strategy)" PLAN
 }
 if($Export){
   $path=Join-Path $global:GPContext.Root ("../generated/MigrationAssessment-{0}.csv" -f (Get-Date -Format yyyyMMdd-HHmmss))
   $rows|Export-Csv $path -NoTypeInformation -Encoding utf8
   Write-GPLog "Migration assessment written: $path" SUCCESS
 }
 return $rows
}
function Invoke-GPApprovedMigrations {
 [CmdletBinding()]
 param([hashtable]$Model,[string[]]$ApprovedMigrationIds)
 if(-not $ApprovedMigrationIds){Write-GPLog 'No explicit migration IDs approved; no field-type migration executed.' SKIP;return}
 foreach($id in $ApprovedMigrationIds){
   $rule=$Model.Migration.rules|Where-Object id -eq $id|Select-Object -First 1
   if(-not $rule){throw "Unknown migration ID '$id'."}
   if(-not $rule.autoExecute){Write-GPLog "Migration $id is assessment-only in v6.2.5 and was not executed." WARN;continue}
 }
}
Export-ModuleMember -Function Get-GPMigrationPlan,Invoke-GPMigrationAssessment,Invoke-GPApprovedMigrations
