function Test-GPCompiledSchema {
 [CmdletBinding()]
 param([hashtable]$Schema)
 $errors=[System.Collections.Generic.List[string]]::new();$warnings=[System.Collections.Generic.List[string]]::new()
 $total=@($Schema.Lists).Count;$position=0
 foreach($ld in $Schema.Lists){
   $position++
   Write-GPLog ("Schema validation {0}/{1}: {2}." -f $position,$total,$ld.Title) INFO
   $list=Get-PnPList -Identity $ld.Title -ErrorAction SilentlyContinue
   if(-not $list){if($global:GPContext.DryRun){Write-GPLog "List '$($ld.Title)' will be created." DRYRUN}else{$errors.Add("Missing list '$($ld.Title)'.")};continue}
   foreach($fd in $ld.Fields){
     $field=Get-PnPField -List $ld.Title -Identity $fd.InternalName -ErrorAction SilentlyContinue
     if(-not $field){if($global:GPContext.DryRun){Write-GPLog "Field '$($ld.Title).$($fd.InternalName)' will be created." DRYRUN}else{$errors.Add("Missing field '$($ld.Title).$($fd.InternalName)'.")};continue}
     if($field.TypeAsString -ne $fd.Type){$warnings.Add("Type mismatch retained: $($ld.Title).$($fd.InternalName), actual=$($field.TypeAsString), model=$($fd.Type).")}
     if($fd.Indexed -and -not $field.Indexed){$warnings.Add("Planned index missing: $($ld.Title).$($fd.InternalName).")}
   }
 }
 $warnings|ForEach-Object{Write-GPLog $_ WARN}
 if($errors.Count){$errors|ForEach-Object{Write-GPLog $_ ERROR};throw "Schema validation failed with $($errors.Count) error(s)."}
 Write-GPLog 'Compiled schema validation completed.' SUCCESS
}
function Test-GPMetadataIntegrity {
 if($global:GPContext.DryRun){Write-GPLog 'Metadata integrity validation planned.' DRYRUN;return}
 $required=@('ObjectTypes','FieldDefinitions','FormDefinitions','StatusModels','ChoiceValues','RelationTypes','AppSettings','ViewDefinitions','WorkflowDefinitions','AIPrompts','AISkills','PermissionDefinitions','FormFieldDefinitions','PageDefinitions','NavigationDefinitions','DashboardDefinitions','WidgetDefinitions','CommandDefinitions','ValidationDefinitions','BusinessRuleDefinitions','TextResources','NotificationTemplates','StatusPresentation','SavedViews')
 $total=$required.Count;$position=0
 foreach($list in $required){
   $position++
   Write-GPLog ("Metadata validation {0}/{1}: {2}." -f $position,$total,$list) INFO
   $items=@(Get-PnPListItem -List $list -PageSize 2000 -ErrorAction SilentlyContinue)
   if($items.Count -eq 0){Write-GPLog "Metadata list '$list' is empty." WARN}else{Write-GPLog "Metadata list '$list': $($items.Count) item(s)." INFO}
 }
 $objectTypes=@(Get-PnPListItem -List ObjectTypes -PageSize 2000)
 $objectKeys=@($objectTypes|ForEach-Object{$_.FieldValues.ObjectTypeKey})
 foreach($d in ($objectKeys|Group-Object|Where-Object Count -gt 1)){throw "Duplicate ObjectTypeKey '$($d.Name)' in ObjectTypes."}
 $choiceSets=@(Get-PnPListItem -List ChoiceValues -PageSize 2000|ForEach-Object{$_.FieldValues.ChoiceSetKey}|Select-Object -Unique)
 foreach($fd in @(Get-PnPListItem -List FieldDefinitions -PageSize 2000)){
   $v=$fd.FieldValues
   if($objectKeys -notcontains $v.ObjectTypeKey){throw "FieldDefinitions contains unknown ObjectTypeKey '$($v.ObjectTypeKey)'."}
   if($v.ChoiceSetKey -and $choiceSets -notcontains $v.ChoiceSetKey){throw "FieldDefinitions '$($v.FieldDefinitionKey)' references unknown ChoiceSetKey '$($v.ChoiceSetKey)'."}
 }
 foreach($vd in @(Get-PnPListItem -List ViewDefinitions -PageSize 2000)){
   $v=$vd.FieldValues
   if($v.ObjectTypeKey -ne '*' -and $v.ObjectTypeKey -notin @('BusinessObject','DocumentObject','ConfigurationObject','TechnicalObject','AuditObject','RelationObject') -and $objectKeys -notcontains $v.ObjectTypeKey){throw "ViewDefinitions '$($v.ViewDefinitionKey)' references unknown ObjectTypeKey '$($v.ObjectTypeKey)'."}
 }
 $pages=@(Get-PnPListItem -List PageDefinitions -PageSize 2000|ForEach-Object{$_.FieldValues.PageKey})
 foreach($n in @(Get-PnPListItem -List NavigationDefinitions -PageSize 2000)){if($pages -notcontains $n.FieldValues.PageKey){throw "NavigationDefinitions '$($n.FieldValues.NavigationKey)' references unknown PageKey '$($n.FieldValues.PageKey)'."}}
 $dashboards=@(Get-PnPListItem -List DashboardDefinitions -PageSize 2000|ForEach-Object{$_.FieldValues.DashboardKey})
 foreach($w in @(Get-PnPListItem -List WidgetDefinitions -PageSize 2000)){if($dashboards -notcontains $w.FieldValues.DashboardKey){throw "WidgetDefinitions '$($w.FieldValues.WidgetKey)' references unknown DashboardKey '$($w.FieldValues.DashboardKey)'."}}
 Write-GPLog 'Metadata referential integrity validation completed.' SUCCESS
}
Export-ModuleMember -Function Test-GPCompiledSchema,Test-GPMetadataIntegrity
