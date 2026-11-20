[CmdletBinding()]
param(
    [string]$RepositoryRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')),
    [string]$PowerFxDirectory,
    [switch]$RequireNativeBinding
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
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
        $ch=$Text[$i]
        if($ch -eq '"'){if($quoted -and $i+1 -lt $Text.Length -and $Text[$i+1] -eq '"'){$i++;continue};$quoted=!$quoted}
        if($quoted){continue};if($ch -eq $Open){$depth++};if($ch -eq $Close){$depth--;if(!$depth){return $Text.Substring($Start,$i-$Start+1)}}
    };throw 'Unbalanced actual Risk formula'
}
function RuntimeTable([string]$Name){
    $at=$app.IndexOf("ClearCollect($Name,");if($at -lt 0){throw "Missing actual runtime table $Name"}
    $open=$app.IndexOf('(',$at);$body=Balanced $app $open '(' ')';return 'Table('+$body.Substring($body.IndexOf(',')+1).TrimEnd(')')+')'
}
$score=Property 'lblRiskScore' 'Text';$level=Property 'lblRiskLevel' 'Text';$validation=Property 'lblRiskValidation' 'Text'
$init=Property 'lblEditorInitialize' 'OnSelect';$accept=Property 'btnRiskAccept' 'OnSelect';$identity=Property 'lblRiskIdentity' 'OnSelect'
foreach($guard in @((Property 'lblEditorSave' 'DisplayMode'),(Property 'lblEditorRevalidate' 'OnSelect'))){if(!$guard.Contains('IsBlank(lblRiskValidation.Text)')){throw 'Risk validation must gate Save and revalidation.'}}
if($accept -notmatch '^If\(Self.DisplayMode = DisplayMode.Edit,' -or !$accept.Contains('Set(gblRiskDecision, "Accepted")') -or !$accept.Contains('ValueDate: Today()')){throw 'Risk acceptance must be guarded and explicit.'}
if(!$identity.Contains('MyProfileV2({''$select'': "id,userPrincipalName"})') -or $identity -match 'gblUser.Email|\.mail|\.displayName'){throw 'Risk actor requires verified profile ID + UPN.'}
$providers=Get-Content "$RepositoryRoot/powerplatform/config/ObjectProviderRegistry.json" -Raw|ConvertFrom-Json
$riskProvider=@($providers.providers|Where-Object objectTypeKey -eq 'Risk')[0]
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive=[IO.Compression.ZipFile]::OpenRead("$RepositoryRoot/powerplatform/canvas/GovernancePortal/GovernancePortal-3.5.1-studio-baseline.msapr")
try{
    $entry=@($archive.Entries|Where-Object {$_.FullName.Replace('\','/') -match '(^|/)References/DataSources.json$'})
    if($entry.Count -ne 1){throw 'Missing unique generated source reference.'}
    $reader=[IO.StreamReader]::new($entry[0].Open());try{$sources=($reader.ReadToEnd()|ConvertFrom-Json).DataSources}finally{$reader.Dispose()}
}finally{$archive.Dispose()}
$native=@($sources|Where-Object Name -eq 'Risks')
if($RequireNativeBinding){
    if($native.Count -ne 1){throw 'P4b prerequisite missing: real generated Risks connection. No activation/import is accepted.'}
    & "$PSScriptRoot/Test-CanvasRiskAdapter.ps1" -RepositoryRoot $RepositoryRoot
    throw 'Native Risk CRUD acceptance requires a fresh monitored DEV run; the local adapter alone is not native acceptance.'
}
if($native.Count -eq 0){
    if($riskProvider.supportsList -or $riskProvider.supportsCreate -or $riskProvider.supportsEdit -or $riskProvider.supportsSave -or $source -match '\b(Patch|Refresh|LookUp)\(\s*Risks\b'){throw 'Unbound Risk native paths/capabilities must stay disabled.'}
}
$at=$init.IndexOf('Set(gblRiskDecision');if($at -lt 0){throw 'Risk initialization missing.'}
$riskInit=$init.Substring($at);$ro=Balanced $riskInit ($riskInit.IndexOf('{IsReadOnly:')) '{' '}'
$choiceItems=Property 'drpEditorChoice' 'Items';$at=$choiceItems.IndexOf('Filter(');$choiceFilter='Filter'+(Balanced $choiceItems ($at+6) '(' ')')
$saveGuard=(Property 'lblEditorSave' 'DisplayMode').Replace('DisplayMode.Edit','"Edit"').Replace('DisplayMode.Disabled','"Disabled"')
$acceptGuard=(Property 'btnRiskAccept' 'DisplayMode').Replace('DisplayMode.Edit','"Edit"').Replace('DisplayMode.Disabled','"Disabled"')
Write-Host 'Risk source contract passed: actual score/level/validation/decision/identity formulas; no fabricated connection or native Risk activation.'
if(!$PowerFxDirectory){return}
foreach($dll in 'Microsoft.PowerFx.Core.dll','Microsoft.PowerFx.Interpreter.dll'){[void][Reflection.Assembly]::LoadFrom((Join-Path $PowerFxDirectory $dll))}
$engine=[Microsoft.PowerFx.RecalcEngine]::new();$options=[Microsoft.PowerFx.ParserOptions]::new();$options.Culture=[Globalization.CultureInfo]::InvariantCulture
$engine.UpdateVariable('gblAssetPilotEnabled', $false)
$engine.UpdateVariable('gblAssetPilotCanWrite', $false)
$engine.UpdateVariable('gblPilotObjectRoutes', $engine.Eval('Table({ObjectTypeKey: "Asset"})', $null, $null))
$checks=0
function Eval([string]$Formula){$v=$engine.Eval($Formula,$null,$options);if($v -is [Microsoft.PowerFx.Types.ErrorValue]){throw "Power Fx failed: $Formula : $($v.ToObject()|ConvertTo-Json -Compress)"};return $v}
function Assert-Fx([string]$Formula,$Expected,[string]$Context){$v=(Eval $Formula).ToObject();if($v -cne $Expected){throw "${Context}: expected '$Expected', got '$v'. Formula: $Formula"};$script:checks++}
function Q([string]$v){'"'+$v.Replace('"','""')+'"'}
foreach($name in 'colRiskRatingScale','colRiskScoreBands','colRiskTransitions'){$engine.UpdateVariable($name,(Eval (RuntimeTable $name)))}
$engine.UpdateVariable('gblObjectType','Risk');$engine.UpdateVariable('gblChangeOriginalStatusKey','')
foreach($name in 'gblSaveBusy','gblLoadBusy','gblShowDiscardDialog','gblEditorConflict'){$engine.UpdateVariable($name,$false)}
$engine.UpdateVariable('gblEditorCanSave',$true);$engine.UpdateVariable('gblEditorDirty',$true);$engine.UpdateVariable('gblEditorLoadComplete',$true)
$engine.UpdateVariable('gblSelectedRecordId',1001);$engine.UpdateVariable('gblLoadedRecordId',1001)
$engine.UpdateVariable('gblActiveProvider',(Eval '{ObjectTypeKey:"Risk",SupportsList:false,SupportsCreate:false,SupportsEdit:false,SupportsSave:false}'))
$engine.UpdateVariable('lblChangeValidation',(Eval '{Text:""}'))
$engine.UpdateVariable('lblAssetValidation',(Eval '{Text:""}'))
$fields=@(($schema.Lists|Where-Object ObjectKey -eq 'Risk').Fields)
$rows=@();$choices=@()
foreach($name in $model.RiskPilot.pilotFields){
    $f=@($fields|Where-Object InternalName -eq $name)[0]
    $setKey='';$choiceKey=''
    if($f.ContainsKey('ChoiceSet')){
        $setKey=$f.ChoiceSet;$set=@($model.ChoiceSets|Where-Object key -eq $setKey)[0];$choiceKey="$setKey`:$($set.values[0][0])"
        foreach($c in $set.values){$choices+='{EditorFieldKey:'+(Q "Risk:$name")+',ChoiceKey:'+(Q "$setKey`:$($c[0])")+',DisplayNameDE:'+(Q $c[1])+',SortOrder:'+ $c[2]+'}'}
    }
    if($name -eq 'Likelihood'){$choiceKey='RiskLikelihood:Possible'};if($name -eq 'Impact'){$choiceKey='RiskImpact:Moderate'}
    $rows+='{FieldInternalName:'+(Q $name)+',EditorFieldKey:'+(Q "Risk:$name")+',ControlType:'+(Q $f.Type)+',ValueChoiceKey:'+(Q $choiceKey)+',ValueText:'+(Q "Synthetic $name äöü")+',ValueNumber:9,ValueDate:DateAdd(Today(),30,TimeUnit.Days)+Time(0,0,0),ValueBoolean:true,ValueLookupId:2001,ValuePersonClaims:"i:0#.f|membership|owner@tenant.invalid",IsRequired:false,IsReadOnly:false,IsDirty:false,IsValid:true,ErrorMessage:""}'
}
$fixture=Eval ('Table('+($rows -join ',')+')');$engine.UpdateVariable('colEditorChoiceOptions',(Eval ('Table('+($choices -join ',')+')')))
function Edit([string]$Name,[string]$Record){$engine.UpdateVariable('colEditorValues',(Eval ('ForAll(colEditorValues As v,If(v.FieldInternalName='+(Q $Name)+',Patch(v,'+$Record+'),v))')))}
function Reset-Risk([string]$State='Identified'){
    $engine.UpdateVariable('colEditorValues',$fixture);$engine.UpdateVariable('gblEditorMode','Edit');$engine.UpdateVariable('gblRiskOriginalStatusKey',"RiskStatus:$State")
    $engine.UpdateVariable('gblRiskDecision','');$engine.UpdateVariable('gblRiskOriginalOwnerClaims','i:0#.f|membership|owner@tenant.invalid');$engine.UpdateVariable('gblRiskActorClaims','i:0#.f|membership|owner@tenant.invalid')
    Edit 'RiskStatus' ('{ValueChoiceKey:'+(Q "RiskStatus:$State")+'}')
    Edit 'RiskAcceptanceDate' $(if($State -in @('Accepted','Closed')){'{ValueDate:DateAdd(Today(),-3,TimeUnit.Days)+Time(0,0,0)}'}else{'{ValueDate:If(false,Now(),Blank())}'})
    $engine.UpdateVariable('colRecordValues',(Eval 'ForAll(colEditorValues,{FieldInternalName:FieldInternalName,ValueDate:ValueDate})'))
}
function Bind-Risk{
    $engine.UpdateVariable('lblRiskScore',(Eval ('{Text:'+$score+'}')));$engine.UpdateVariable('lblRiskLevel',(Eval ('{Text:'+$level+'}')));$engine.UpdateVariable('lblRiskValidation',(Eval ('{Text:'+$validation+'}')))
}
Reset-Risk
$at=$init.IndexOf('Filter(');$metadataFilter='Filter'+(Balanced $init ($at+6) '(' ')')
$formRows=@($model.RiskPilot.pilotFields|ForEach-Object {'{ObjectTypeKey:"Risk",FieldInternalName:'+(Q $_)+'}'})
$formRows+='{ObjectTypeKey:"Risk",FieldInternalName:"Description"}'
$formRows+='{ObjectTypeKey:"Foreign",FieldInternalName:"Title"}'
$engine.UpdateVariable('gblSelectedObjectTypeKey','Risk');$engine.UpdateVariable('colFormFields',(Eval ('Table('+($formRows -join ',')+')')))
$engine.UpdateVariable('actualRiskForm',(Eval $metadataFilter));Assert-Fx 'CountRows(actualRiskForm)' 16 'Actual metadata filter retains exactly the Risk pilot'
foreach($name in $model.RiskPilot.pilotFields){Assert-Fx ('CountRows(Filter(actualRiskForm,FieldInternalName='+(Q $name)+'))') 1 'Actual form agrees with leading Risk pilot field set'}
$likelihood=@(($model.ChoiceSets|Where-Object key -eq 'RiskLikelihood').values);$impacts=@(($model.ChoiceSets|Where-Object key -eq 'RiskImpact').values)
for($i=0;$i -lt 5;$i++){for($j=0;$j -lt 5;$j++){
    Edit 'Likelihood' ('{ValueChoiceKey:'+(Q "RiskLikelihood:$($likelihood[$i][0])")+'}');Edit 'Impact' ('{ValueChoiceKey:'+(Q "RiskImpact:$($impacts[$j][0])")+'}');Bind-Risk
    $expected=($i+1)*($j+1);$band=if($expected -le 4){'Low'}elseif($expected -le 9){'Medium'}elseif($expected -le 14){'High'}else{'Critical'}
    Assert-Fx 'lblRiskScore.Text' ([string]$expected) "Independent5x5 score $i/$j";Assert-Fx 'lblRiskLevel.Text' $band "Independent5x5 classification $i/$j"
}}
foreach($case in @(@(1,'Low'),@(4,'Low'),@(5,'Medium'),@(9,'Medium'),@(10,'High'),@(14,'High'),@(15,'Critical'),@(25,'Critical'),@(0,''),@(26,''))){
    $engine.UpdateVariable('lblRiskScore',(Eval ('{Text:'+(Q ([string]$case[0]))+'}')));if($case[1] -eq ''){Assert-Fx ('IsBlank('+$level+')') $true 'Out-of-range score has no classification'}else{Assert-Fx $level $case[1] 'Actual score-band boundaries'}
}
foreach($bad in @('','RiskLikelihood:Unknown','RiskImpact:Severe')){Reset-Risk;Edit 'Likelihood' ('{ValueChoiceKey:'+(Q $bad)+'}');Bind-Risk;Assert-Fx 'IsBlank(lblRiskScore.Text)' $true 'Missing/foreign-axis rating never becomes zero or a valid score'}
foreach($old in ($model.StatusModels|Where-Object key -eq 'Risk').states){foreach($target in ($model.StatusModels|Where-Object key -eq 'Risk').states){
    Reset-Risk $old[0];Edit 'RiskStatus' ('{ValueChoiceKey:'+(Q "RiskStatus:$($target[0])")+',IsDirty:true}')
    if($target[0] -eq 'Accepted' -and $old[0] -ne 'Accepted'){$engine.UpdateVariable('gblRiskDecision','Accepted');Edit 'RiskAcceptanceDate' '{ValueDate:Today()+Time(0,0,0)}'}
    Bind-Risk;$allowed=(!$old[3]) -and ($target[0] -eq $old[0] -or $target[0] -in $old[4]);Assert-Fx 'IsBlank(lblRiskValidation.Text)' ([bool]$allowed) "Actual lifecycle $($old[0])->$($target[0])"
}}
# Test the actual dropdown against the leading transition graph: Accepted is never an ordinary transition choice.
foreach($state in ($model.StatusModels|Where-Object key -eq 'Risk').states){
    Reset-Risk $state[0];$engine.UpdateVariable('ThisItem',(Eval ('{EditorFieldKey:"Risk:RiskStatus",ValueChoiceKey:'+(Q "RiskStatus:$($state[0])")+'}')))
    $engine.UpdateVariable('actualChoices',(Eval $choiceFilter))
    foreach($target in ($model.StatusModels|Where-Object key -eq 'Risk').states){$allowed=$target[0] -eq $state[0] -or ($target[0] -ne 'Accepted' -and $target[0] -in $state[4]);Assert-Fx ('CountRows(Filter(actualChoices,ChoiceKey='+(Q "RiskStatus:$($target[0])")+'))') $(if($allowed){1}else{0}) 'Actual Risk status dropdown follows graph and explicit acceptance'}
}
Reset-Risk;$engine.UpdateVariable('gblEditorMode','New');Edit 'RiskStatus' '{ValueChoiceKey:"RiskStatus:Identified"}'
foreach($field in 'LinkedAsset','RiskOwner','RiskScenario','Likelihood','Impact','TreatmentStrategy','RiskAcceptanceUntil','RiskAcceptanceReason'){
    Edit $field '{ValueLookupId:If(false,0,Blank()),ValuePersonClaims:"",ValueText:"",ValueChoiceKey:"",ValueDate:If(false,Now(),Blank())}'
}
Bind-Risk;Assert-Fx 'IsBlank(lblRiskValidation.Text)' $true 'Title-only identified draft remains valid'
Edit 'Title' '{ValueText:"   "}';Bind-Risk;Assert-Fx 'IsBlank(lblRiskValidation.Text)' $false 'Whitespace title blocked'
Edit 'Title' ('{ValueText:'+(Q ('X'*256))+'}');Bind-Risk;Assert-Fx 'IsBlank(lblRiskValidation.Text)' $false '256-character title blocked'
foreach($missing in 'LinkedAsset','RiskOwner','RiskScenario','Likelihood','Impact'){
    Reset-Risk 'Assessed';Edit $missing '{ValueLookupId:If(false,0,Blank()),ValuePersonClaims:"",ValueText:"",ValueChoiceKey:""}';Bind-Risk;Assert-Fx 'IsBlank(lblRiskValidation.Text)' $false "Assessment refuses missing $missing"
}
foreach($actor in '','i:0#.f|membership|foreign@tenant.invalid','owner@tenant.invalid'){
    Reset-Risk 'Assessed';$engine.UpdateVariable('gblRiskActorClaims',$actor);$engine.UpdateVariable('gblRiskDecision','Accepted');Edit 'RiskStatus' '{ValueChoiceKey:"RiskStatus:Accepted",IsDirty:true}';Edit 'RiskAcceptanceDate' '{ValueDate:Today()+Time(0,0,0),IsDirty:true}';Bind-Risk;Assert-Fx 'IsBlank(lblRiskValidation.Text)' $false 'Acceptance refuses missing/foreign/alias principal'
}
Reset-Risk 'Assessed';Edit 'RiskStatus' '{ValueChoiceKey:"RiskStatus:Accepted",IsDirty:true}';Edit 'RiskAcceptanceDate' '{ValueDate:Today()+Time(0,0,0),IsDirty:true}';Bind-Risk;Assert-Fx 'IsBlank(lblRiskValidation.Text)' $false 'Status edit alone is not acceptance'
foreach($bad in 'owner-reassignment','blank-until','expired-until','missing-reason','future-accepted-on'){
    Reset-Risk 'Assessed';$engine.UpdateVariable('gblRiskDecision','Accepted');Edit 'RiskStatus' '{ValueChoiceKey:"RiskStatus:Accepted",IsDirty:true}';Edit 'RiskAcceptanceDate' '{ValueDate:Today()+Time(0,0,0),IsDirty:true}'
    switch($bad){'owner-reassignment'{Edit 'RiskOwner' '{IsDirty:true}'}'blank-until'{Edit 'RiskAcceptanceUntil' '{ValueDate:If(false,Now(),Blank())}'}'expired-until'{Edit 'RiskAcceptanceUntil' '{ValueDate:DateAdd(Today(),-1,TimeUnit.Days)+Time(0,0,0)}'}'missing-reason'{Edit 'RiskAcceptanceReason' '{ValueText:" "}'}'future-accepted-on'{Edit 'RiskAcceptanceDate' '{ValueDate:DateAdd(Today(),1,TimeUnit.Days)+Time(0,0,0)}'}}
    Bind-Risk;Assert-Fx 'IsBlank(lblRiskValidation.Text)' $false "Actual acceptance guard rejects $bad"
}
Reset-Risk 'Accepted';Edit 'RiskAcceptanceUntil' '{ValueDate:DateAdd(Today(),-1,TimeUnit.Days)+Time(0,0,0)}';Bind-Risk;Assert-Fx 'IsBlank(lblRiskValidation.Text)' $false 'Expired acceptance cannot be saved unchanged';Edit 'RiskStatus' '{ValueChoiceKey:"RiskStatus:Closed",IsDirty:true}';Bind-Risk;Assert-Fx 'IsBlank(lblRiskValidation.Text)' $true 'Expired acceptance can still be closed'
Reset-Risk 'Accepted';Edit 'RiskScenario' '{ValueText:"Changed",IsDirty:true}';Bind-Risk;Assert-Fx 'IsBlank(lblRiskValidation.Text)' $false 'Accepted risk core is immutable'
foreach($state in ($model.StatusModels|Where-Object key -eq 'Risk').states){foreach($name in $model.RiskPilot.pilotFields){
    $engine.UpdateVariable('gblRiskOriginalStatusKey',"RiskStatus:$($state[0])");$engine.UpdateVariable('riskField',(Eval ('{FieldInternalName:'+(Q $name)+'}')))
    $expected=$name -in $model.RiskPilot.derivedFields -or $state[0] -eq 'Closed' -or ($state[0] -eq 'Accepted' -and $name -ne 'RiskStatus');Assert-Fx ('('+$ro+').IsReadOnly') ([bool]$expected) "Actual read-only $($state[0])/$name"
}}
Reset-Risk 'Assessed';Bind-Risk;Assert-Fx $acceptGuard 'Disabled' 'Explicitly disabled Risk provider cannot accept';Assert-Fx $saveGuard 'Disabled' 'Explicitly disabled Risk provider cannot save'
$engine.UpdateVariable('gblActiveProvider',(Eval '{ObjectTypeKey:"Risk",SupportsList:true,SupportsCreate:true,SupportsEdit:true,SupportsSave:true}'));Assert-Fx $acceptGuard 'Edit' 'Synthetic future bound provider permits eligible explicit decision'
$engine.UpdateVariable('gblEditorMode','New');Assert-Fx $acceptGuard 'Disabled' 'A new unsaved risk cannot accept even with a synthetic bound provider';$engine.UpdateVariable('gblEditorMode','Edit')
# Evaluate actual button patches, rather than a duplicate acceptance implementation.
foreach($name in 'RiskStatus','RiskAcceptanceDate'){
    $at=$accept.IndexOf('FieldInternalName = "'+$name+'"');$record=Balanced $accept ($accept.IndexOf('{',$at)) '{' '}';Edit $name $record
}
$engine.UpdateVariable('gblRiskDecision','Accepted');Bind-Risk;Assert-Fx 'IsBlank(lblRiskValidation.Text)' $true 'Actual guarded decision records validate';Assert-Fx 'LookUp(colEditorValues,FieldInternalName="RiskAcceptanceDate",ValueDate)=Today()' $true 'Actual decision records calendar date'
$at=$identity.IndexOf('If(');$identityValue='If'+(Balanced $identity ($at+2) '(' ')')
$engine.UpdateVariable('gblUser',(Eval '{EntraObjectId:"synthetic-id"}'));$engine.UpdateVariable('gblRiskProfile',(Eval '{id:"synthetic-id",userPrincipalName:" OWNER@tenant.invalid "}'));Assert-Fx $identityValue 'i:0#.f|membership|owner@tenant.invalid' 'Actual actor normalization verifies id and UPN'
$engine.UpdateVariable('gblRiskProfile',(Eval '{id:"foreign-id",userPrincipalName:"owner@tenant.invalid"}'));Assert-Fx $identityValue '' 'Actual actor rejects mismatched profile id'
Write-Host "Risk Power Fx passed: $checks assertions over actual runtime, score, level, validation, dropdown, read-only, Save and decision/identity expressions. Native CRUD acceptance still requires a fresh monitored DEV run."
