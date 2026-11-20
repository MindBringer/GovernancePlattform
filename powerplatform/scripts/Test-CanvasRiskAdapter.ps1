[CmdletBinding()]
param(
    [string]$RepositoryRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')),
    [string]$PowerFxDirectory
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
# Execute actual canonical formulas over synthetic values; no connector is called.
Import-Module "$RepositoryRoot/provisioning/Modules/Model.psm1" -Force
Import-Module "$RepositoryRoot/provisioning/Modules/Compiler.psm1" -Force
$model=Get-GPArchitectureModel -Root "$RepositoryRoot/provisioning"
$schema=Compile-GPArchitecture $model
$source=Get-Content "$RepositoryRoot/powerplatform/canvas/GovernancePortal/Src/scrShell.pa.yaml" -Raw
$app=Get-Content "$RepositoryRoot/powerplatform/canvas/GovernancePortal/Src/App.pa.yaml" -Raw
function Property([string]$Control,[string]$Name){
    $m=[regex]::Match($source,"(?m)^(?<indent> *)- ${Control}:\r?`n")
    if(!$m.Success){throw "Missing control $Control"}
    $tail=$source.Substring($m.Index+$m.Length);$end=[regex]::Match($tail,"(?m)^ {0,$($m.Groups['indent'].Value.Length)}- \w+:")
    if($end.Success){$tail=$tail.Substring(0,$end.Index)}
    $p=[regex]::Match($tail,"(?m)^(?<indent> *)${Name}: \|-\r?`n(?<formula>(?:\k<indent> +[^\r\n]*\r?`n|\r?`n)+)")
    if($p.Success){return $p.Groups['formula'].Value.Trim().TrimStart('=')}
    $p=[regex]::Match($tail,"(?m)^ *${Name}: =(?<formula>[^\r\n]+)")
    if($p.Success){return $p.Groups['formula'].Value.Trim()};throw "Missing $Control.$Name"
}
function Balanced([string]$Text,[int]$Start,[char]$Open,[char]$Close){
    $depth=0;$quoted=$false
    for($i=$Start;$i -lt $Text.Length;$i++){
        $c=$Text[$i]
        if($c -eq '"'){if($quoted -and $i+1 -lt $Text.Length -and $Text[$i+1] -eq '"'){$i++;continue};$quoted=!$quoted}
        if($quoted){continue};if($c -eq $Open){$depth++};if($c -eq $Close){$depth--;if(!$depth){return $Text.Substring($Start,$i-$Start+1)}}
    };throw 'Unbalanced actual Risk adapter formula'
}
$expected=@($model.RiskPilot.pilotFields);$native=@($schema.Lists|Where-Object ObjectKey -eq 'Risk')[0]
$load=Property 'lblRecordLoad' 'OnSelect';$save=Property 'lblEditorSave' 'OnSelect';$init=Property 'lblEditorInitialize' 'OnSelect'
$part=$load.Substring($load.IndexOf('Refresh(Risks)'));$at=$part.IndexOf('Table(');$projection='Table'+(Balanced $part ($at+5) '(' ')')
$m=[regex]::Match($save,'Patch\(\s*Risks,');if(!$m.Success){throw 'Missing actual native Risk Patch'}
$payload=Balanced $save ($save.IndexOf('{',$m.Index)) '{' '}'
$loaded=@([regex]::Matches($projection,'FieldInternalName: "([^"]+)"')|ForEach-Object {$_.Groups[1].Value})
$written=@([regex]::Matches($payload,'(?m)^\s*(\w+): ')|ForEach-Object {$_.Groups[1].Value})
if($expected.Count -ne 16 -or $loaded.Count -ne 16 -or $written.Count -ne 16 -or (Compare-Object ($expected|Sort-Object) ($loaded|Sort-Object)) -or (Compare-Object ($expected|Sort-Object) ($written|Sort-Object))){throw 'Risk must load and write exactly the sixteen leading pilot fields.'}
foreach($name in $expected){
    $f=@($native.Fields|Where-Object InternalName -eq $name)[0]
    if(!$projection.Contains('FieldInternalName: "'+$name+'", NativeControlType: "'+$f.Type+'"')){throw "Risk.$name projection type differs from the compiler."}
}
if($load -notmatch 'Refresh\(Risks\);\s*Set\(gblRiskRecord, LookUp\(Risks, ID = gblSelectedRecordId\)\)' -or $save -notmatch 'Patch\(\s*Risks,\s*If\([^,]+, gblRiskRecord, Defaults\(Risks\)\)'){throw 'Risk must refresh/load by ID and Patch the original native record.'}
if(([regex]::Matches($save,'Patch\(\s*Risks,')).Count -ne 1 -or $save -notmatch '^If\(\s*Self.DisplayMode = DisplayMode.Edit,'){throw 'Risk has exactly one native Patch under the actual Save guard.'}
$riskNavigation = @($model.NavigationDefinitions | Where-Object { $_.objectTypeKey -ceq 'Risk' -and $_.pageKey -ceq 'ObjectList' })
if ($riskNavigation.Count -ne 1) {
    throw 'Expected one architecture navigation route for the Risk object list.'
}
$riskRoute = $riskNavigation[0].key
$objectTypeItems = Property 'galObjectTypes' 'Items'
$routePattern = '"' + [regex]::Escape($riskRoute) + '",\s*Filter\(\s*colObjectTypes,\s*ObjectTypeKey in \[\s*"Risk"'
if ($objectTypeItems -cnotmatch $routePattern) {
    throw "Risk object list must open from the architecture navigation route '$riskRoute'."
}
$items=Property 'galRiskRecords' 'Items';$open=Property 'galRiskRecords' 'OnSelect'
if($items -notmatch 'Filter\(Risks, ID = gblRecordQueryId\)' -or $items -notmatch 'Filter\(Risks, StartsWith\(Title, gblRecordQuery\)\)' -or $items -match 'FirstN|LastN|ClearCollect|ForAll|\bID\s*[<>]'){throw 'Risk list must retain delegable ID/title filtering without local truncation.'}
foreach($token in 'gblObjectType = "Risk"','gblActiveProvider.ObjectTypeKey = "Risk"','!gblSaveBusy','!gblLoadBusy','!gblEditorDirty','SupportsList','SupportsEdit','Select(lblRecordLoad)'){if(!$open.Contains($token)){throw "Risk gallery open lacks guard: $token"}}
if((Property 'galRiskRecords' 'ShowNavigation') -ne 'true' -or !(Property 'txtRecordSearch' 'OnChange').Contains('Reset(galRiskRecords)') -or !(Property 'lblRefresh' 'OnSelect').Contains('"Risk", Refresh(Risks)') -or !(Property 'lblRecordEmpty' 'Visible').Contains('IsEmpty(galRiskRecords.AllItems)')){throw 'Risk list refresh/search/paging/empty state is incomplete.'}
$conflict=[regex]::Match($save,'IsBlank\(gblRiskCurrent.Modified\) \|\| IsBlank\(gblRiskRecord.Modified\) \|\| gblRiskCurrent.Modified <> gblRiskRecord.Modified').Value
$readback=[regex]::Match($save,'IsBlank\(gblRiskSavedReadback.ID\) \|\| gblRiskSavedReadback.ID <> gblSavedRecordId \|\| IsBlank\(gblRiskSavedReadback.Modified\)').Value
if(!$conflict -or !$readback -or $save -notmatch 'Refresh\(Risks\);\s*Set\(gblRiskSavedReadback, LookUp\(Risks, ID = gblSavedRecordId\)\)'){throw 'Missing Risk fresh conflict check or post-save identity reload.'}
$assetAt=$save.IndexOf('If(gblObjectType = "Risk" && IsBlank(gblSaveError)')
if($assetAt -lt 0){throw 'Missing dedicated Risk linked-Asset preflight.'}
$assetPart=$save.Substring($assetAt,$save.IndexOf('If(IsBlank(gblSaveError),',$assetAt)-$assetAt)
if(!$assetPart.Contains('Refresh(Assets)')){throw 'Risk linked-Asset existence must use a refreshed source.'}
$assetGuard=[regex]::Match($assetPart,'^If\((?<guard>[^\r\n]+),').Groups['guard'].Value
$assetMissingAt=$assetPart.IndexOf('IsBlank(LookUp(Assets,')
if($assetMissingAt -lt 0){throw 'Risk linked Asset must be checked by its selected native ID.'}
$assetMissing='IsBlank'+(Balanced $assetPart ($assetMissingAt+7) '(' ')')
$riskSave=$save.Substring($save.LastIndexOf('"Risk",'));if(([regex]::Matches($riskSave,'Set\(gblEditorConflict, true\)')).Count -lt 3){throw 'Unconfirmed write/readback must lock further saves until reopening.'}
$providers=(Get-Content "$RepositoryRoot/powerplatform/config/ObjectProviderRegistry.json" -Raw|ConvertFrom-Json).providers
foreach($p in $providers){$supported=$p.objectTypeKey -in @('Asset','System','Change','Risk');foreach($key in 'supportsList','supportsCreate','supportsEdit','supportsSave'){if($p.$key -ne $supported){throw "Provider capability disagrees with implemented paths: $($p.objectTypeKey)/$key"}}}
# Verify real connector permissions and DateOnly, independently of the source-field names.
Add-Type -AssemblyName System.IO.Compression.FileSystem
$z=[IO.Compression.ZipFile]::OpenRead("$RepositoryRoot/powerplatform/canvas/GovernancePortal/GovernancePortal-3.5.1-studio-baseline.msapr")
try{
    $entry=@($z.Entries|Where-Object {$_.FullName.Replace('\','/') -match '(^|/)References/DataSources.json$'});if($entry.Count -ne 1){throw 'Expected actual generated DataSources'}
    $reader=[IO.StreamReader]::new($entry[0].Open());try{$ds=($reader.ReadToEnd()|ConvertFrom-Json -AsHashtable).DataSources}finally{$reader.Dispose()}
}finally{$z.Dispose()}
$r=@($ds|Where-Object {$_.Name -eq 'Risks'});if($r.Count -ne 1 -or !$r[0].IsWritable -or $r[0].Type -ne 'ConnectedDataSourceInfo'){throw 'Actual writable generated Risks source is required.'}
$metadata=$r[0].DataEntityMetadataJson;if($metadata -is [string]){$metadata=$metadata|ConvertFrom-Json -AsHashtable}
$entity=$metadata[$r[0].TableName];if($entity -is [string]){$entity=$entity|ConvertFrom-Json -AsHashtable};$props=$entity.schema.items.properties
foreach($name in $expected){if($props[$name]['x-ms-permission'] -ne 'read-write'){throw "Risk.$name connector permission must be read-write."}}
if(@($entity.schema.items.required).Count -ne 1 -or $entity.schema.items.required[0] -ne 'Title' -or $props.Title.maxLength -ne 255){throw 'Risk permanent requirement is exactly Title Text255.'}
foreach($name in 'RiskAcceptanceDate','RiskAcceptanceUntil'){if($props[$name].format -ne 'date'){throw "Risk.$name must preserve actual generated DateOnly."}}
Write-Host 'Risk native adapter source/connector passed: 16 typed load/write fields, original record, delegated queries, conflict and post-save reload; no native access.'
if(!$PowerFxDirectory){return}
foreach($dll in 'Microsoft.PowerFx.Core.dll','Microsoft.PowerFx.Interpreter.dll'){[void][Reflection.Assembly]::LoadFrom((Join-Path $PowerFxDirectory $dll))}
$engine=[Microsoft.PowerFx.RecalcEngine]::new();$options=[Microsoft.PowerFx.ParserOptions]::new();$options.Culture=[Globalization.CultureInfo]::InvariantCulture;$checks=0
$engine.UpdateVariable('gblAssetPilotEnabled', $false)
$engine.UpdateVariable('gblAssetPilotCanWrite', $false)
$engine.UpdateVariable('gblPilotObjectRoutes', $engine.Eval('Table({NavigationKey: "NavGovernance", ObjectTypeKey: "Asset"})', $null, $options))
$engine.UpdateVariable('gblAssetPilotAssetNavigation', [string](
    $model.NavigationDefinitions | Where-Object { $_.objectTypeKey -ceq 'Asset' -and $_.pageKey -ceq 'ObjectList' }
).key)
function Eval([string]$Formula){$v=$engine.Eval($Formula,$null,$options);if($v -is [Microsoft.PowerFx.Types.ErrorValue]){throw "Power Fx failed: $Formula : $($v.ToObject()|ConvertTo-Json -Compress)"};return $v}
function Assert-Fx([string]$Formula,$Expected,[string]$Context){$v=(Eval $Formula).ToObject();if($v -cne $Expected){throw "${Context}: expected '$Expected', got '$v'. Formula: $Formula"};$script:checks++}
function Q([string]$s){'"'+$s.Replace('"','""')+'"'}
$engine.UpdateVariable('colObjectTypes', (Eval 'Table({ObjectTypeKey:"Asset"},{ObjectTypeKey:"Risk"},{ObjectTypeKey:"Control"},{ObjectTypeKey:"Measure"})'))
$engine.UpdateVariable('gblCurrentNavigationKey', $riskRoute)
Assert-Fx ('Concat(' + $objectTypeItems + ', ObjectTypeKey, ",")') 'Risk,Control,Measure' 'Runtime Risk navigation exposes the expected object types'
$engine.UpdateVariable('gblAssetPilotEnabled', $true)
Assert-Fx ('CountRows(' + $objectTypeItems + ')') 0 'A stale Risk route exposes no objects during the Asset pilot'
$engine.UpdateVariable('gblCurrentNavigationKey', (Eval 'gblAssetPilotAssetNavigation'))
Assert-Fx ('Concat(' + $objectTypeItems + ', ObjectTypeKey, ",")') 'Asset' 'The Asset pilot route exposes only Assets'
$engine.UpdateVariable('gblAssetPilotEnabled', $false)
$choiceRows=@();$optionRows=@();$editorRows=@();$recordRows=@('ID:1001','Modified:Date(2026,10,1)+Time(12,34,56)','Description:"SEALED - DO NOT TOUCH"','GovernanceID:"SYN-RISK-1001"')
foreach($name in $expected){
    $f=@($native.Fields|Where-Object InternalName -eq $name)[0];$setKey='';$label=''
    if($f.Type -eq 'Choice'){
        $set=@($model.ChoiceSets|Where-Object key -eq $f.ChoiceSet)[0];$setKey=$set.key
        foreach($c in $set.values){$choiceRows+='{ChoiceSetKey:'+(Q $setKey)+',ChoiceKey:'+(Q "$setKey`:$($c[0])")+',DisplayNameDE:'+(Q $c[1])+',IsActive:true}';$optionRows+='{EditorFieldKey:'+(Q "Risk:$name")+',ChoiceKey:'+(Q "$setKey`:$($c[0])")+',DisplayNameDE:'+(Q $c[1])+',SortOrder:'+$c[2]+'}'}
        $label=$set.values[0][1];if($name -in @('Likelihood','Impact')){$label=$set.values[2][1]}
    }
    $value=switch($f.Type){
        'User'{'{Claims:"i:0#.f|membership|'+$name.ToLower()+'@tenant.invalid",DisplayName:"Synthetic '+$name+'",Email:"alias-'+$name.ToLower()+'@tenant.invalid",Department:"TEST",JobTitle:"TEST",Picture:"retained-picture"}'}
        'Choice'{'{Value:'+(Q $label)+'}'}
        'Lookup'{'{Id:2001,Value:"Synthetic Asset"}'}
        'DateTime'{'DateAdd(Today(),30,TimeUnit.Days)+Time(0,0,0)'}
        'Number'{'9'}
        'Boolean'{'false'}
        'Note'{(Q "Synthetic $name äöü")+' & Char(10) & "zweite Zeile"'}
        default{Q "Synthetic $name äöü"}
    }
    if($name -eq 'RiskLevel'){$value='"Medium"'};if($name -eq 'RiskAcceptanceDate'){$value='If(false,Now(),Blank())'}
    $recordRows+=$name+':'+$value
    $editorRows+='{FieldInternalName:'+(Q $name)+',EditorFieldKey:'+(Q "Risk:$name")+',ControlType:'+(Q $f.Type)+',ChoiceSetKey:'+(Q $setKey)+',IsRequired:'+$f.Required.ToString().ToLowerInvariant()+',ValueText:"",ValueNumber:If(false,0,Blank()),ValueBoolean:If(false,true,Blank()),ValueDate:If(false,Now(),Blank()),ValueLookupId:If(false,0,Blank()),ValueLookupText:"",ValuePersonEmail:"",ValuePersonClaims:"",ValuePersonDepartment:"",ValuePersonJobTitle:"",ValueChoiceKey:"",IsDirty:false,IsValid:true,ErrorMessage:""}'
}
$fixture=Eval ('{'+($recordRows -join ',')+'}');$editorFixture=Eval ('Table('+($editorRows -join ',')+')')
$engine.UpdateVariable('gblRiskRecord',$fixture);$engine.UpdateVariable('colChoiceValues',(Eval ('Table('+($choiceRows -join ',')+')')));$engine.UpdateVariable('colEditorChoiceOptions',(Eval ('Table('+($optionRows -join ',')+')')))
$engine.UpdateVariable('gblEditorMode','Edit');$engine.UpdateVariable('gblRiskOriginalStatusKey','RiskStatus:Identified');$engine.UpdateVariable('gblRiskDecision','')
$at=$init.IndexOf('With(',$init.IndexOf('{editorInput:'));$hydrate='With'+(Balanced $init ($at+4) '(' ')')
function Hydrate{
    $engine.UpdateVariable('colRecordValues',(Eval $projection));$engine.UpdateVariable('colEditorValues',$editorFixture)
    $engine.UpdateVariable('colEditorValues',(Eval ('ForAll(colRecordValues As loadedValue,Patch(LookUp(colEditorValues,FieldInternalName=loadedValue.FieldInternalName),'+$hydrate+'))')))
}
function Edit([string]$Name,[string]$Record){$engine.UpdateVariable('colEditorValues',(Eval ('ForAll(colEditorValues As v,If(v.FieldInternalName='+(Q $Name)+',Patch(v,'+$Record+'),v))')))}
function Bind-Score{
    foreach($n in 'colRiskRatingScale','colRiskScoreBands'){$at=$app.IndexOf('ClearCollect('+$n+',');$start=$app.IndexOf('(',$at);$body=Balanced $app $start '(' ')';$engine.UpdateVariable($n,(Eval ('Table('+$body.Substring($body.IndexOf(',')+1).TrimEnd(')')+')')))}
    $engine.UpdateVariable('lblRiskScore',(Eval ('{Text:'+(Property 'lblRiskScore' 'Text')+'}')));$engine.UpdateVariable('lblRiskLevel',(Eval ('{Text:'+(Property 'lblRiskLevel' 'Text')+'}')))
}
function Save-Payload{$engine.UpdateVariable('testSaved',(Eval $payload))}
function Suffix([string]$Name){switch(@($native.Fields|Where-Object InternalName -eq $Name)[0].Type){'User'{'.Claims'}'Choice'{'.Value'}'Lookup'{'.Id'}default{''}}}
Hydrate;Bind-Score;Save-Payload
Assert-Fx 'CountRows(colRecordValues)' 16 'All native Risk pilot fields load'
Assert-Fx 'CountRows(Filter(colEditorValues,IsDirty || !IsValid))' 0 'Hydration remains clean and valid'
foreach($name in $expected){$suffix=Suffix $name;Assert-Fx ('testSaved.'+$name+$suffix) ((Eval ('gblRiskRecord.'+$name+$suffix)).ToObject()) "Untouched $name preserves native value"}
foreach($name in 'Owner','RiskOwner'){
    Assert-Fx ('testSaved.'+$name+'.Email') ('alias-'+$name.ToLower()+'@tenant.invalid') 'Unchanged native user alias preserved'
    Assert-Fx ('testSaved.'+$name+'.Picture') 'retained-picture' 'Unchanged native user record preserved'
    Assert-Fx ('LookUp(colEditorValues,FieldInternalName='+(Q $name)+',ValuePersonEmail)') ($name.ToLower()+'@tenant.invalid') 'Hydrated principal comes from Claims, not mail alias'
}
# Each edit changes its intended field while every other field round-trips unchanged.
foreach($changed in $expected|Where-Object {$_ -notin @('RiskScore','RiskLevel','RiskAcceptanceDate')}){
    $engine.UpdateVariable('gblRiskRecord',$fixture);Hydrate;Bind-Score;$f=@($native.Fields|Where-Object InternalName -eq $changed)[0]
    $edit=switch($f.Type){
        'User'{'{ValueText:"Changed Person",ValuePersonClaims:"i:0#.f|membership|changed@tenant.invalid",ValuePersonEmail:"changed@tenant.invalid",ValuePersonDepartment:"NEW",ValuePersonJobTitle:"NEW",IsDirty:true}'}
        'Choice'{$set=@($model.ChoiceSets|Where-Object key -eq $f.ChoiceSet)[0];'{ValueChoiceKey:'+(Q "$($set.key):$($set.values[-1][0])")+',IsDirty:true}'}
        'Lookup'{'{ValueLookupId:2002,ValueLookupText:"Other Asset",IsDirty:true}'}
        'Boolean'{'{ValueBoolean:true,IsDirty:true}'}
        'DateTime'{'{ValueDate:DateAdd(Today(),60,TimeUnit.Days)+Time(0,0,0),IsDirty:true}'}
        default{'{ValueText:"  Changed äöü  ",IsDirty:true}'}
    };Edit $changed $edit;Bind-Score;Save-Payload
    foreach($name in $expected|Where-Object {$_ -ne $changed}){$suffix=Suffix $name;Assert-Fx ('testSaved.'+$name+$suffix) ((Eval ('gblRiskRecord.'+$name+$suffix)).ToObject()) "Edit $changed preserves $name"}
    $changedValue=switch($f.Type){'User'{'"i:0#.f|membership|changed@tenant.invalid"'}'Choice'{$set=@($model.ChoiceSets|Where-Object key -eq $f.ChoiceSet)[0];Q $set.values[-1][1]}'Lookup'{'2002'}'Boolean'{'true'}'DateTime'{'DateAdd(Today(),60,TimeUnit.Days)+Time(0,0,0)'}default{if($changed -eq 'Title'){Q 'Changed äöü'}else{Q '  Changed äöü  '}}}
    Assert-Fx ('testSaved.'+$changed+(Suffix $changed)) ((Eval $changedValue).ToObject()) "Actual payload writes $changed"
    if($f.Type -eq 'User'){
        foreach($pair in @(@('DisplayName','Changed Person'),@('Email','changed@tenant.invalid'),@('Department','NEW'),@('JobTitle','NEW'),@('Picture',''))){Assert-Fx ('testSaved.'+$changed+'.'+$pair[0]) $pair[1] 'Changed native person shape retains the selected principal fields'}
    }
    if($f.Type -eq 'Lookup'){Assert-Fx ('testSaved.'+$changed+'.Value') 'Other Asset' 'Changed lookup retains its selected display value'}
    $engine.UpdateVariable('gblRiskRecord',(Eval 'Patch(gblRiskRecord,testSaved)'));Hydrate;Save-Payload
    Assert-Fx ('testSaved.'+$changed+(Suffix $changed)) ((Eval $changedValue).ToObject()) "Actual projection reopens $changed"
}
Assert-Fx 'Patch(gblRiskRecord,testSaved).Description' 'SEALED - DO NOT TOUCH' 'Original native record retains sealed Description'
Assert-Fx 'Patch(gblRiskRecord,testSaved).GovernanceID' 'SYN-RISK-1001' 'Original native record retains unmapped governance identity'
$engine.UpdateVariable('gblRiskRecord',$fixture);$engine.UpdateVariable('gblRiskRecord',(Eval 'Patch(gblRiskRecord,{RiskCategory:{Value:"LEGACY UNKNOWN"},RiskScore:0,IsActive:false,RiskAcceptanceUntil:If(false,Now(),Blank())})'));Hydrate;Bind-Score;Save-Payload
Assert-Fx 'LookUp(colEditorValues,FieldInternalName="RiskCategory",IsValid)' $false 'Unknown native choice is surfaced, not silently erased'
Assert-Fx 'testSaved.RiskCategory.Value' 'LEGACY UNKNOWN' 'Unchanged unknown native choice survives serialization'
Assert-Fx 'testSaved.RiskScore' 0 'Native numeric zero remains zero when untouched'
Assert-Fx 'testSaved.IsActive' $false 'Native false remains false when untouched'
Assert-Fx 'IsBlank(testSaved.RiskAcceptanceUntil)' $true 'Native blank acceptance end stays blank without a default date'
# Optional blanks are not converted to a zero-number, false-person, or empty lookup sentinel.
foreach($name in @('Owner','RiskOwner','LinkedAsset','RiskCategory','Likelihood','Impact','RiskAcceptanceUntil','RiskAcceptanceReason','TreatmentStrategy')){
    $engine.UpdateVariable('gblRiskRecord',$fixture);Hydrate;Bind-Score
    Edit $name '{ValueText:"",ValueChoiceKey:"",ValueLookupId:If(false,0,Blank()),ValuePersonClaims:"",ValueDate:If(false,Now(),Blank()),IsDirty:true}'
    Bind-Score;Save-Payload;Assert-Fx ('IsBlank(testSaved.'+$name+(Suffix $name)+')') $true "Actual payload clears optional $name"
}
foreach($lookup in '{Id:0,Value:""}','If(false,{Id:0,Value:""},Blank())'){
    $engine.UpdateVariable('gblRiskRecord',$fixture);$engine.UpdateVariable('gblRiskRecord',(Eval ('Patch(gblRiskRecord,{LinkedAsset:'+$lookup+'})')));Hydrate;Save-Payload
    Assert-Fx 'IsBlank(testSaved.LinkedAsset.Id)' $true 'Expanded null lookup remains Blank, never ID0'
}
# Evaluate the actual derived-field payload, including new Title-only drafts and explicit acceptance.
$engine.UpdateVariable('gblRiskRecord',$fixture);Hydrate;$engine.UpdateVariable('gblEditorMode','New')
Edit 'Likelihood' '{ValueChoiceKey:""}';Edit 'Impact' '{ValueChoiceKey:""}';Bind-Score;Save-Payload
Assert-Fx 'IsBlank(testSaved.RiskScore)' $true 'Unrated new Risk keeps a typed blank score';Assert-Fx 'IsBlank(testSaved.RiskLevel)' $true 'Unrated new Risk has no invented classification';Assert-Fx 'IsBlank(testSaved.RiskAcceptanceDate)' $true 'Create never invents acceptance date'
$engine.UpdateVariable('gblEditorMode','Edit');Hydrate;Edit 'Likelihood' '{ValueChoiceKey:"RiskLikelihood:AlmostCertain",IsDirty:true}';Edit 'Impact' '{ValueChoiceKey:"RiskImpact:Severe",IsDirty:true}'
Edit 'RiskScore' '{ValueNumber:999,IsDirty:true}';Edit 'RiskLevel' '{ValueText:"INVALID",IsDirty:true}';Bind-Score;Save-Payload
Assert-Fx 'testSaved.RiskScore' 25 'Derived score uses actual ratings, not a forged numeric buffer';Assert-Fx 'testSaved.RiskLevel' 'Critical' 'Derived level uses actual scoring expression'
Hydrate;Bind-Score;Edit 'RiskAcceptanceDate' '{ValueDate:Today()+Time(0,0,0),IsDirty:true}';Save-Payload
Assert-Fx 'IsBlank(testSaved.RiskAcceptanceDate)' $true 'Editing the buffer alone cannot create acceptance'
$engine.UpdateVariable('gblRiskOriginalStatusKey','RiskStatus:Assessed');$engine.UpdateVariable('gblRiskDecision','Accepted');Edit 'RiskStatus' '{ValueChoiceKey:"RiskStatus:Accepted",IsDirty:true}';Save-Payload
Assert-Fx 'testSaved.RiskAcceptanceDate=Today()' $true 'Explicit validated decision writes the calendar date'
$engine.UpdateVariable('gblRiskRecord',(Eval 'Patch(gblRiskRecord,{RiskAcceptanceDate:Date(2026,10,1)+Time(0,0,0)})'));Hydrate;$engine.UpdateVariable('gblRiskOriginalStatusKey','RiskStatus:Accepted');Edit 'RiskStatus' '{ValueChoiceKey:"RiskStatus:Closed",IsDirty:true}';Save-Payload
Assert-Fx 'testSaved.RiskAcceptanceDate' ((Eval 'gblRiskRecord.RiskAcceptanceDate').ToObject()) 'Closing preserves the first persisted acceptance date exactly'
# Actual preflight and post-save predicates reject stale, missing and unverifiable records.
$engine.UpdateVariable('gblRiskRecord',$fixture);$engine.UpdateVariable('gblRiskCurrent',$fixture)
Assert-Fx $conflict $false 'Matching Modified permits preflight'
$engine.UpdateVariable('gblRiskCurrent',(Eval 'Patch(gblRiskRecord,{Modified:Date(2026,10,2)+Time(0,0,0)})'));Assert-Fx $conflict $true 'Changed Modified blocks overwrite'
$engine.UpdateVariable('gblRiskCurrent',(Eval 'Patch(gblRiskRecord,{Modified:If(false,Now(),Blank())})'));Assert-Fx $conflict $true 'Missing Modified blocks overwrite'
$engine.UpdateVariable('gblRiskSavedReadback',$fixture);$engine.UpdateVariable('gblSavedRecordId',1001);Assert-Fx $readback $false 'Confirmed reloaded identity and Modified permit success'
foreach($bad in '{ID:1002}','{ID:If(false,0,Blank())}','{Modified:If(false,Now(),Blank())}'){$engine.UpdateVariable('gblRiskSavedReadback',(Eval ('Patch(gblRiskRecord,'+$bad+')')));Assert-Fx $readback $true 'Unconfirmed post-save readback blocks success'}
# Actual delegated filters are evaluated on a synthetic data source, with no local truncation.
$engine.UpdateVariable('Risks',(Eval 'Table({ID:1001,Title:"Pilot Alpha"},{ID:1002,Title:"Pilot Beta"},{ID:1003,Title:"Other"})'));$engine.UpdateVariable('gblRecordQueryId',1002);$engine.UpdateVariable('gblRecordQuery','Pilot')
$idFilter='Filter'+(Balanced $items ($items.IndexOf('Filter(Risks, ID')+6) '(' ')');$titleFilter='Filter'+(Balanced $items ($items.IndexOf('Filter(Risks, StartsWith')+6) '(' ')')
Assert-Fx ('First('+$idFilter+').ID') 1002 'Actual ID filter loads the selected Risk'
$engine.UpdateVariable('gblRecordQueryId',9999);Assert-Fx ('CountRows('+$idFilter+')') 0 'Unknown Risk ID is empty'
Assert-Fx ('CountRows('+$titleFilter+')') 2 'Actual StartsWith uses the entered title prefix';$engine.UpdateVariable('gblRecordQuery','');Assert-Fx ('CountRows('+$titleFilter+')') 3 'Blank title query leaves the full source available'
# The actual Save/display and gallery guards protect stale controls and incomplete loads.
$saveGuard=(Property 'lblEditorSave' 'DisplayMode').Replace('DisplayMode.Edit','"Edit"').Replace('DisplayMode.Disabled','"Disabled"');$openGuard=[regex]::Match($open,'^If\((?<guard>[^\r\n]+),').Groups['guard'].Value
$engine.UpdateVariable('lblAssetValidation',(Eval '{Text:""}'))
$engine.UpdateVariable('gblObjectType','Risk');$engine.UpdateVariable('gblCurrentPage','ObjectList');$engine.UpdateVariable('gblActiveProvider',(Eval '{ObjectTypeKey:"Risk",SupportsList:true,SupportsCreate:true,SupportsEdit:true,SupportsSave:true}'));$engine.UpdateVariable('gblEditorCanSave',$true);$engine.UpdateVariable('gblEditorLoadComplete',$true);$engine.UpdateVariable('gblEditorDirty',$false);$engine.UpdateVariable('gblSelectedRecordId',1001);$engine.UpdateVariable('gblLoadedRecordId',1001);$engine.UpdateVariable('lblChangeValidation',(Eval '{Text:""}'));$engine.UpdateVariable('lblRiskValidation',(Eval '{Text:""}'))
foreach($flag in 'gblSaveBusy','gblLoadBusy','gblShowDiscardDialog','gblEditorConflict'){$engine.UpdateVariable($flag,$false)}
Hydrate;Assert-Fx $openGuard $true 'Correct provider gallery opens cleanly';$engine.UpdateVariable('gblEditorDirty',$true);Assert-Fx $openGuard $false 'Dirty editor blocks stale gallery opens';Assert-Fx $saveGuard 'Edit' 'Correct loaded Risk can save'
foreach($flag in 'gblSaveBusy','gblLoadBusy','gblShowDiscardDialog','gblEditorConflict'){$engine.UpdateVariable($flag,$true);Assert-Fx $saveGuard 'Disabled' "Risk Save blocks $flag";$engine.UpdateVariable($flag,$false)}
$engine.UpdateVariable('lblRiskValidation',(Eval '{Text:"Invalid lifecycle"}'));Assert-Fx $saveGuard 'Disabled' 'Fresh Risk validation overrides stale CanSave';$engine.UpdateVariable('lblRiskValidation',(Eval '{Text:""}'));$engine.UpdateVariable('gblLoadedRecordId',1002);Assert-Fx $saveGuard 'Disabled' 'Loaded ID mismatch blocks Risk save'
$engine.UpdateVariable('gblLoadedRecordId',1001);$engine.UpdateVariable('gblActiveProvider',(Eval '{ObjectTypeKey:"Asset",SupportsList:true,SupportsCreate:true,SupportsEdit:true,SupportsSave:true}'));Assert-Fx $saveGuard 'Disabled' 'Foreign provider blocks Risk save';$engine.UpdateVariable('gblEditorDirty',$false);Assert-Fx $openGuard $false 'Foreign provider blocks stale Risk gallery'
$engine.UpdateVariable('Assets',(Eval 'Table({ID:2001},{ID:2002})'));$engine.UpdateVariable('gblSaveError','');Hydrate
Assert-Fx $assetGuard $true 'Selected Risk Asset requires fresh preflight'
Assert-Fx $assetMissing $false 'Existing selected Asset passes the actual existence predicate'
Edit 'LinkedAsset' '{ValueLookupId:9999}';Assert-Fx $assetMissing $true 'Deleted or inaccessible selected Asset blocks saving'
Edit 'LinkedAsset' '{ValueLookupId:If(false,0,Blank())}';Assert-Fx $assetGuard $false 'Optional empty Asset in an identified draft makes no unnecessary lookup'
Hydrate;$engine.UpdateVariable('gblSaveError','Preflight failed');Assert-Fx $assetGuard $false 'Earlier Risk preflight failure prevents the Asset lookup'
Write-Host "Risk adapter Power Fx passed: $checks assertions over actual projection, hydration, sixteen-field payload, preservation, blanks, derived values, acceptance date, conflict/reload and query/Save guards. Native delegation, ETag and monitored acceptance remain unverified."
