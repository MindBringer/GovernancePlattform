function Ensure-GPList {
 param([hashtable]$Def)
 $list=Get-PnPList -Identity $Def.Title -Includes Id,Title,BaseTemplate -ErrorAction SilentlyContinue
 if(-not $list){
   Invoke-GPChange "Create $($Def.Template): $($Def.Title)" { New-PnPList -Title $Def.Title -Template $Def.Template -EnableVersioning -OnQuickLaunch | Out-Null }
   if(-not $global:GPContext.DryRun){$list=Get-PnPList -Identity $Def.Title -Includes Id,Title,BaseTemplate -ErrorAction Stop}
 }
 if($list -and -not $global:GPContext.DryRun){Set-PnPList -Identity $Def.Title -EnableVersioning $true -EnableContentTypes $true|Out-Null}
 return $list
}
function ConvertTo-GPXmlEncoded {[System.Security.SecurityElement]::Escape([string]$args[0])}
function New-GPFieldXml {
 param([hashtable]$F,[string]$LookupListId)
 $required=if($F.Required){'TRUE'}else{'FALSE'};$indexed=if($F.Indexed){'TRUE'}else{'FALSE'};$unique=if($F.EnforceUnique){'TRUE'}else{'FALSE'}
 $name=ConvertTo-GPXmlEncoded $F.InternalName;$display=ConvertTo-GPXmlEncoded $F.DisplayName
 $attrs="Name='$name' StaticName='$name' DisplayName='$display' Required='$required' Indexed='$indexed' EnforceUniqueValues='$unique' Group='$($global:GPContext.FieldGroup)'"
 switch($F.Type){
  'Text' {"<Field Type='Text' $attrs MaxLength='$(if($F.MaxLength){$F.MaxLength}else{255})' />"}
  'Note' {"<Field Type='Note' $attrs NumLines='$(if($F.NumLines){$F.NumLines}else{8})' RichText='FALSE' />"}
  'Number' {$min=if($null-ne $F.Min){" Min='$($F.Min)'"}else{''};$max=if($null-ne $F.Max){" Max='$($F.Max)'"}else{''};"<Field Type='Number' $attrs$min$max />"}
  'Boolean' {"<Field Type='Boolean' $attrs><Default>$(if($F.ContainsKey('Default') -and -not $F.Default){0}else{1})</Default></Field>"}
  'DateTime' {"<Field Type='DateTime' $attrs Format='DateOnly' />"}
  'URL' {"<Field Type='URL' $attrs Format='Hyperlink' />"}
  'User' {"<Field Type='User' $attrs UserSelectionMode='PeopleOnly' />"}
  'Choice' {"<Field Type='Choice' $attrs Format='Dropdown'><CHOICES>$(($F.Choices|ForEach-Object{"<CHOICE>$(ConvertTo-GPXmlEncoded $_)</CHOICE>"}) -join '')</CHOICES></Field>"}
  'MultiChoice' {"<Field Type='MultiChoice' $attrs><CHOICES>$(($F.Choices|ForEach-Object{"<CHOICE>$(ConvertTo-GPXmlEncoded $_)</CHOICE>"}) -join '')</CHOICES></Field>"}
  'Lookup' {"<Field Type='Lookup' $attrs List='{$LookupListId}' ShowField='Title' />"}
  default {throw "Unsupported field type '$($F.Type)' for '$($F.InternalName)'."}
 }
}
function Test-GPFieldTypeCompatible {
 param([string]$Existing,[string]$Expected)
 return $Existing -eq $Expected
}
function Ensure-GPField {
 param(
  [string]$List,
  [hashtable]$F,
  [hashtable]$ExistingFields,
  [hashtable]$ListObjects
 )
 $existing=$ExistingFields[$F.InternalName]
 if(-not $existing){
   $lookupId=$null
   if($F.Type -eq 'Lookup'){
     $lookup=$ListObjects[$F.LookupList]
     if(-not $lookup -and -not $global:GPContext.DryRun){throw "Lookup target '$($F.LookupList)' missing for $List.$($F.InternalName)."}
     if($lookup){$lookupId=$lookup.Id}
   }
   if($global:GPContext.DryRun){Write-GPLog "Create field $List.$($F.InternalName)" DRYRUN;return}
   try {
     Invoke-GPChange "Create field $List.$($F.InternalName)" {Add-PnPFieldFromXml -List $List -FieldXml (New-GPFieldXml $F $lookupId)|Out-Null}
   }
   catch {
     $indexCapacityError=($_.Exception.Message -match 'maximale Anzahl.*indiziert|maximum number.*indexed|cannot be indexed')
     if($indexCapacityError -and $F.Indexed -and -not $F.EnforceUnique){
       Write-GPLog ("Index capacity reached in {0} while creating {1}. Retrying without a physical index." -f $List,$F.InternalName) WARN
       $fallback=@{} + $F;$fallback.Indexed=$false
       Add-PnPFieldFromXml -List $List -FieldXml (New-GPFieldXml $fallback $lookupId)|Out-Null
     }else{throw}
   }
   return
 }
 if(-not(Test-GPFieldTypeCompatible $existing.TypeAsString $F.Type)){
   Write-GPLog "Retain incompatible field $List.$($F.InternalName): existing=$($existing.TypeAsString), model=$($F.Type). Use an explicit migration rule." WARN
   return
 }
 if($global:GPContext.DryRun){return}
 $props=@{}
 if($existing.Title -ne $F.DisplayName){$props.Title=$F.DisplayName}
 if($F.Type -in @('Choice','MultiChoice') -and $F.Choices){$props.Choices=[string[]]@($F.Choices | ForEach-Object { [string]$_ })}
 if($F.Required -and -not $existing.Required){$props.Required=$true}
 if($props.Count){Set-PnPField -List $List -Identity $F.InternalName -Values $props|Out-Null}
 if($F.Indexed -and -not $existing.Indexed){try{Set-PnPField -List $List -Identity $F.InternalName -Values @{Indexed=$true}|Out-Null}catch{Write-GPLog "Index failed $List.$($F.InternalName): $($_.Exception.Message)" WARN}}
}
function ConvertTo-GPViewQuery {
 param([hashtable]$V)
 if($V.Query){return $V.Query}
 $order=''
 if($V.Sort){
   $order='<OrderBy>'+ (($V.Sort|ForEach-Object{"<FieldRef Name='$($_[0])' Ascending='$(if($_[1] -eq "desc"){"FALSE"}else{"TRUE"})'/>"}) -join '') +'</OrderBy>'
 }
 $where=''
 switch -Regex ([string]$V.Filter){
   '^IsActive eq true$' {$where="<Where><Eq><FieldRef Name='IsActive'/><Value Type='Integer'>1</Value></Eq></Where>"}
   '^DocumentStatus eq (Published|Veröffentlicht) and IsActive eq true$' {$where="<Where><And><Eq><FieldRef Name='DocumentStatus'/><Value Type='Choice'>Veröffentlicht</Value></Eq><Eq><FieldRef Name='IsActive'/><Value Type='Integer'>1</Value></Eq></And></Where>"}
   '^DocumentReviewDate le @Today\+30 and IsActive eq true$' {$where="<Where><And><Leq><FieldRef Name='DocumentReviewDate'/><Value Type='DateTime'><Today OffsetDays='30'/></Value></Leq><Eq><FieldRef Name='IsActive'/><Value Type='Integer'>1</Value></Eq></And></Where>"}
   '^NextReviewDate le @Today\+30$' {$where="<Where><Leq><FieldRef Name='NextReviewDate'/><Value Type='DateTime'><Today OffsetDays='30'/></Value></Leq></Where>"}
   default {$where=''}
 }
 return "$where$order"
}
function Ensure-GPView {
 param(
  [string]$List,
  [hashtable]$V,
  [hashtable]$ExistingViews,
  [string[]]$AvailableFields
 )
 $fields=@($V.Fields|Where-Object{$AvailableFields -contains $_})
 $query=ConvertTo-GPViewQuery $V
 $existing=$ExistingViews[$V.Name]
 if(-not $existing){
   if($global:GPContext.DryRun){Write-GPLog "Create view $List/$($V.Name)" DRYRUN;return}
   Invoke-GPChange "Create view $List/$($V.Name)" {Add-PnPView -List $List -Title $V.Name -Fields $fields -Query $query -SetAsDefault:$V.IsDefault|Out-Null}
 }
 elseif(-not $global:GPContext.DryRun){Set-PnPView -List $List -Identity $V.Name -Fields $fields -Values @{ViewQuery=$query;DefaultView=[bool]$V.IsDefault}|Out-Null}
}
function Ensure-GPNavigation {
 param([array]$Nodes)
 Write-GPLog "Schema stage: scan Quick Launch navigation." INFO
 $existingNodes=@(Get-PnPNavigationNode -Location QuickLaunch)
 foreach($n in ($Nodes|Sort-Object order)){
  $existing=$existingNodes|Where-Object Title -eq $n.title|Select-Object -First 1
  $url=$n.url -replace '\{SiteUrl\}',$global:GPContext.SiteUrl
  if(-not $existing){Invoke-GPChange "Create navigation $($n.title)" {Add-PnPNavigationNode -Location QuickLaunch -Title $n.title -Url $url|Out-Null}}
 }
}
function Ensure-GPSchema {
 param([hashtable]$Schema)
 $total=$Schema.Lists.Count
 $listObjects=@{}
 Write-GPLog "Schema stage 1/3: scan and ensure $total lists/libraries." INFO
 $i=0
 foreach($l in $Schema.Lists){
   $i++
   Write-GPLog "List scan $i/$($total): $($l.Title)" INFO
   $list=Ensure-GPList $l
   if($list){$listObjects[$l.Title]=$list}
 }
 Write-GPLog "Schema stage 2/3: scan fields and views once per list/library." INFO
 $i=0
 foreach($l in $Schema.Lists){
   $i++
   $listObject=$listObjects[$l.Title]
   if(-not $listObject -and $global:GPContext.DryRun){
     Write-GPLog "Schema scan $i/$($total): $($l.Title) (planned new list; remote field/view scan skipped)." PLAN
     foreach($f in $l.Fields){Ensure-GPField -List $l.Title -F $f -ExistingFields @{} -ListObjects $listObjects}
     foreach($v in $l.Views){Ensure-GPView -List $l.Title -V $v -ExistingViews @{} -AvailableFields @($l.Fields.InternalName + @('Title','LinkTitle','LinkFilename','DocIcon','Modified'))}
     continue
   }
   Write-GPLog "Schema scan $i/$($total): $($l.Title) - loading fields and views." INFO
   $fieldArray=@(Get-PnPField -List $l.Title)
   $viewArray=@(Get-PnPView -List $l.Title)
   $fieldMap=@{};foreach($field in $fieldArray){$fieldMap[$field.InternalName]=$field}
   $viewMap=@{};foreach($view in $viewArray){$viewMap[$view.Title]=$view}
   Write-GPLog "Schema scan $i/$($total): $($l.Title) - $($fieldArray.Count) fields, $($viewArray.Count) views loaded." INFO
   foreach($f in $l.Fields){Ensure-GPField -List $l.Title -F $f -ExistingFields $fieldMap -ListObjects $listObjects}
   $available=[string[]]@(($fieldArray.InternalName + $l.Fields.InternalName + @('Title','LinkTitle','LinkFilename','DocIcon','Modified'))|Select-Object -Unique)
   foreach($v in $l.Views){Ensure-GPView -List $l.Title -V $v -ExistingViews $viewMap -AvailableFields $available}
 }
 Write-GPLog "Schema stage 3/3: navigation." INFO
 Ensure-GPNavigation $Schema.Navigation
 Write-GPLog "Schema ensure completed for $total lists/libraries." SUCCESS
}
Export-ModuleMember -Function Ensure-GPSchema
