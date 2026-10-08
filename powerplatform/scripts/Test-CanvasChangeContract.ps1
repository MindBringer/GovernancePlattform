[CmdletBinding()]
param(
    [string]$RepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')),
    [string]$PowerFxDirectory
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# Actual Canvas expressions and synthetic records only; no auth or native writes.
Import-Module (Join-Path $RepositoryRoot 'provisioning/Modules/Model.psm1') -Force
Import-Module (Join-Path $RepositoryRoot 'provisioning/Modules/Compiler.psm1') -Force
$model = Get-GPArchitectureModel -Root (Join-Path $RepositoryRoot 'provisioning')
$schema = Compile-GPArchitecture $model
$source = Get-Content (Join-Path $RepositoryRoot 'powerplatform/canvas/GovernancePortal/Src/scrShell.pa.yaml') -Raw
function Property([string]$Control, [string]$Name) {
    $m = [regex]::Match($source, "(?m)^(?<indent> *)- ${Control}:\r?`n")
    if (-not $m.Success) { throw "Missing control $Control" }
    $tail = $source.Substring($m.Index + $m.Length)
    $end = [regex]::Match($tail, "(?m)^ {0,$($m.Groups['indent'].Value.Length)}- \w+:")
    if ($end.Success) { $tail = $tail.Substring(0, $end.Index) }
    $p = [regex]::Match($tail, "(?m)^(?<indent> *)${Name}: \|-\r?`n(?<formula>(?:\k<indent> +[^\r\n]*\r?`n|\r?`n)+)")
    if ($p.Success) { return $p.Groups['formula'].Value.Trim().TrimStart('=') }
    $p = [regex]::Match($tail, "(?m)^ *${Name}: =(?<formula>[^\r\n]+)")
    if ($p.Success) { return $p.Groups['formula'].Value.Trim() }
    throw "Missing $Control.$Name"
}
function Balanced([string]$Text, [int]$Start, [char]$Open, [char]$Close) {
    $depth = 0; $quoted = $false
    for ($i=$Start; $i -lt $Text.Length; $i++) {
        $ch = $Text[$i]
        if ($ch -eq '"') {
            if ($quoted -and $i+1 -lt $Text.Length -and $Text[$i+1] -eq '"') { $i++; continue }
            $quoted = -not $quoted
        }
        if ($quoted) { continue }
        if ($ch -eq $Open) { $depth++ }
        if ($ch -eq $Close) { $depth--; if ($depth -eq 0) { return $Text.Substring($Start,$i-$Start+1) } }
    }
    throw 'Unbalanced actual Canvas expression'
}
$expected = 'Title LinkedAsset IsActive Owner Approver ChangeType ChangeStatus ApprovalStatus ChangeRisk PlannedStart PlannedEnd ImplementationPlan RollbackPlan ActualEnd ApprovedDate EmergencyChange DowntimeExpected DowntimeMinutes RollbackValidated'.Split(' ')
$load = Property 'lblRecordLoad' 'OnSelect'
$save = Property 'lblEditorSave' 'OnSelect'
$init = Property 'lblEditorInitialize' 'OnSelect'
$part = $load.Substring($load.IndexOf('Refresh(Changes)'))
$at = $part.IndexOf('Table(')
$projection = 'Table' + (Balanced $part ($at+5) '(' ')')
$at = $save.IndexOf('Patch(', $save.IndexOf('"Change",', $save.IndexOf('If(IsBlank(gblSaveError),')))
$payload = Balanced $save ($save.IndexOf('{',$at)) '{' '}'
$loaded = @([regex]::Matches($projection, 'FieldInternalName: "([^"]+)"') | ForEach-Object {$_.Groups[1].Value})
$written = @([regex]::Matches($payload, '(?m)^\s*(\w+): ') | ForEach-Object {$_.Groups[1].Value})
if ($loaded.Count -ne 19 -or $written.Count -ne 19 -or (Compare-Object ($expected|Sort-Object) ($loaded|Sort-Object)) -or (Compare-Object ($expected|Sort-Object) ($written|Sort-Object))) { throw 'Change must load/write exactly the 19 pilot fields.' }
$native = @($schema.Lists | Where-Object ObjectKey -eq 'Change')[0]
foreach ($name in $expected) {
    $field = @($native.Fields | Where-Object InternalName -eq $name)[0]
    if ($projection -notmatch ('FieldInternalName: "'+$name+'", NativeControlType: "'+$field.Type+'"')) { throw "Change.$name native type mismatch" }
}
if ($save -notmatch 'Patch\(\s*Changes,\s*If\([^,]+, gblChangeRecord, Defaults\(Changes\)\)' -or
    $load -notmatch 'Refresh\(Changes\);\s*Set\(gblChangeRecord, LookUp\(Changes, ID = gblSelectedRecordId\)\)') { throw 'Change must preserve the original connector record and delegable ID load.' }
$items = Property 'galChangeRecords' 'Items'
if ($items -notmatch 'Filter\(Changes, ID = gblRecordQueryId\)' -or $items -notmatch 'Filter\(Changes, StartsWith\(Title, gblRecordQuery\)\)' -or $items -match 'FirstN|LastN|ClearCollect|ForAll|\bID\s*[<>]') { throw 'Change gallery must remain delegated without local truncation.' }
$validation = Property 'lblChangeValidation' 'Text'
$saveGuard = (Property 'lblEditorSave' 'DisplayMode').Replace('DisplayMode.Edit','"Edit"').Replace('DisplayMode.Disabled','"Disabled"')
if ($saveGuard -notmatch 'IsBlank\(lblChangeValidation.Text\)' -or (Property 'lblEditorRevalidate' 'OnSelect') -notmatch 'IsBlank\(lblChangeValidation.Text\)') { throw 'Change invariants must guard both Save and revalidation.' }
foreach ($decision in @('Approve','Reject')) {
    if ((Property "btnChange$decision" 'OnSelect') -notmatch '^If\(Self.DisplayMode = DisplayMode.Edit,' -or (Property "btnChange$decision" 'OnSelect') -notmatch 'Set\(gblChangeDecision,') { throw 'Approval requires an explicit guarded decision action.' }
}
$identity = Property 'lblChangeIdentity' 'OnSelect'
if (-not $identity.Contains('MyProfileV2({''$select'': "id,userPrincipalName"})') -or $identity -match 'gblUser.Email|\.mail|\.displayName') { throw 'Current principal must use connector profile ID + UPN, never display name or mail aliases.' }
$at = $identity.IndexOf('If(')
$identityExpression = 'If' + (Balanced $identity ($at+2) '(' ')')
$at = $init.IndexOf('With(', $init.IndexOf('{editorInput:'))
$hydrate = 'With' + (Balanced $init ($at+4) '(' ')')
$at = $init.IndexOf('{IsReadOnly:')
$readOnly = Balanced $init $at '{' '}'
$conflict = [regex]::Match($save, 'IsBlank\(gblChangeCurrent.Modified\) \|\| IsBlank\(gblChangeRecord.Modified\) \|\| gblChangeCurrent.Modified <> gblChangeRecord.Modified').Value
if (-not $conflict -or $save -notmatch 'LookUp\(Assets, ID = LookUp\(colEditorValues, FieldInternalName = "LinkedAsset", ValueLookupId\), ID\)') { throw 'Missing fresh Changed/Asset identity readback before Patch.' }
Write-Host 'Change source/compiler passed: 19 pilot fields, original record, lifecycle, decision, identity and delegated read paths.'
if (-not $PowerFxDirectory) { return }
foreach ($dll in 'Microsoft.PowerFx.Core.dll','Microsoft.PowerFx.Interpreter.dll') { [void][Reflection.Assembly]::LoadFrom((Join-Path $PowerFxDirectory $dll)) }
$engine = [Microsoft.PowerFx.RecalcEngine]::new()
$options = [Microsoft.PowerFx.ParserOptions]::new(); $options.Culture = [Globalization.CultureInfo]::InvariantCulture
$checks=0
function Eval([string]$Formula) {
    $value=$engine.Eval($Formula,$null,$options)
    if ($value -is [Microsoft.PowerFx.Types.ErrorValue]) { throw "Power Fx failed: $Formula : $($value.ToObject()|ConvertTo-Json -Compress)" }
    return $value
}
function Assert-Fx([string]$Formula, $Expected, [string]$Context) {
    $actual=(Eval $Formula).ToObject()
    if ($actual -cne $Expected) { throw "${Context}: expected '$Expected', got '$actual'. Formula: $Formula" }
    $script:checks++
}
function FxString([string]$Value) { '"'+$Value.Replace('"','""')+'"' }
$engine.UpdateVariable('gblObjectType','Change'); $engine.UpdateVariable('gblEditorMode','Edit')
$engine.UpdateVariable('gblChangeOriginalStatusKey','ChangeStatus:Draft'); $engine.UpdateVariable('gblChangeDecision','')
$engine.UpdateVariable('gblChangeActorClaims','i:0#.f|membership|synthetic@tenant.invalid')
$choiceRows=@(); $optionRows=@(); $metadata=@(); $nativeFields=@('ID: 1001','Modified: Date(2026,10,1)+Time(12,0,0)','Description: "DO NOT TOUCH"','GovernanceID: "SYN-1001"')
foreach ($name in $expected) {
    $field = @($native.Fields | Where-Object InternalName -eq $name)[0]
    $setKey=''; $choiceValue=''
    if ($field.Type -eq 'Choice') {
        $set=@($model.ChoiceSets | Where-Object key -eq $field.ChoiceSet)[0]; $setKey=$set.key
        foreach ($choice in $set.values) {
            $choiceRows += '{ChoiceSetKey: '+(FxString $setKey)+', ChoiceKey: '+(FxString "$setKey`:$($choice[0])")+', DisplayNameDE: '+(FxString $choice[1])+', IsActive: true}'
            $optionRows += '{EditorFieldKey: '+(FxString "Change:$name")+', ChoiceKey: '+(FxString "$setKey`:$($choice[0])")+', DisplayNameDE: '+(FxString $choice[1])+', SortOrder: '+$choice[2]+'}'
        }
        $choiceValue=$set.values[0][1]
    }
    $value = switch ($field.Type) {
        'User' {'{Claims: "i:0#.f|membership|synthetic@tenant.invalid", DisplayName: "Synthetic Person", Email: "alias@tenant.invalid", Department: "TEST", JobTitle: "TEST", Picture: ""}'}
        'Choice' {'{Value: '+(FxString $choiceValue)+'}'}
        'DateTime' {'Date(2026,10,1)+Time(13,14,15)'}
        'Number' {'0'}
        'Boolean' {'false'}
        'Lookup' {'{Id: 3001, Value: "Synthetic Asset"}'}
        default {FxString ('Synthetic '+$name+' äöü')}
    }
    if ($name -eq 'PlannedEnd') {$value='Date(2026,10,2)+Time(13,14,15)'}
    if ($name -eq 'ApprovedDate') {$value='If(false,Now(),Blank())'}
    $nativeFields += $name+': '+$value
    $metadata += '{FieldInternalName: '+(FxString $name)+', EditorFieldKey: '+(FxString "Change:$name")+', ControlType: '+(FxString $field.Type)+', ChoiceSetKey: '+(FxString $setKey)+', IsRequired: '+$field.Required.ToString().ToLowerInvariant()+', ValueText: "", ValueNumber: If(false,0,Blank()), ValueBoolean: If(false,true,Blank()), ValueDate: If(false,Now(),Blank()), ValueLookupId: If(false,0,Blank()), ValueLookupText: "", ValuePersonEmail: "", ValuePersonClaims: "", ValuePersonDepartment: "", ValuePersonJobTitle: "", ValueChoiceKey: "", IsDirty: false, IsValid: true, ErrorMessage: ""}'
}
$fixture=Eval ('{'+($nativeFields -join ',')+'}')
$engine.UpdateVariable('gblChangeRecord',$fixture)
$engine.UpdateVariable('colChoiceValues',(Eval ('Table('+($choiceRows -join ',')+')')))
$engine.UpdateVariable('colEditorChoiceOptions',(Eval ('Table('+($optionRows -join ',')+')')))
$metadataFixture=Eval ('Table('+($metadata -join ',')+')')
$at=$init.IndexOf('Filter(');$metadataFilter='Filter'+(Balanced $init ($at+6) '(' ')')
$formRows=@($expected|ForEach-Object {'{ObjectTypeKey:"Change",FieldInternalName:'+(FxString $_)+'}'})
$formRows+=' {ObjectTypeKey:"Foreign",FieldInternalName:"Title"}'
$formRows+=' {ObjectTypeKey:"Change",FieldInternalName:"Description"}'
$engine.UpdateVariable('gblSelectedObjectTypeKey','Change')
$engine.UpdateVariable('colFormFields',(Eval ('Table('+($formRows -join ',')+')')))
Assert-Fx ('CountRows('+$metadataFilter+')') 19 'Actual editor metadata filter keeps exactly the pilot fields'
function Hydrate {
    $engine.UpdateVariable('colRecordValues',(Eval $projection)); $engine.UpdateVariable('colEditorValues',$metadataFixture)
    $engine.UpdateVariable('colEditorValues',(Eval ('ForAll(colRecordValues As loadedValue, Patch(LookUp(colEditorValues, FieldInternalName = loadedValue.FieldInternalName), '+$hydrate+'))')))
}
function EditField([string]$Name, [string]$Record) {
    $engine.UpdateVariable('colEditorValues',(Eval ('ForAll(colEditorValues As v, If(v.FieldInternalName = '+(FxString $Name)+', Patch(v, '+$Record+'), v))')))
}
function Eligible {
    $engine.UpdateVariable('lblChangeValidation',(Eval ('{Text: '+$validation+'}')))
    return [string](Eval 'lblChangeValidation.Text').ToObject()
}
Hydrate
Assert-Fx 'CountRows(colRecordValues)' 19 'Complete Change projection'
Assert-Fx 'CountRows(Filter(colEditorValues, IsDirty || !IsValid))' 0 'Hydration stays clean and valid'
$engine.UpdateVariable('testSaved',(Eval $payload))
foreach ($name in $expected) {
    $type=@($native.Fields|Where-Object InternalName -eq $name)[0].Type
    $suffix=switch($type){'User'{'.Claims'}'Choice'{'.Value'}'Lookup'{'.Id'}default{''}}
    Assert-Fx ('testSaved.'+$name+$suffix) ((Eval ('gblChangeRecord.'+$name+$suffix)).ToObject()) "Unchanged $name survives round-trip"
}
Assert-Fx 'testSaved.Owner.Email' 'alias@tenant.invalid' 'Untouched connector email alias retained'
Assert-Fx 'LookUp(colEditorValues, FieldInternalName = "Owner", ValuePersonEmail)' 'synthetic@tenant.invalid' 'Loaded identity uses Claims principal'
Assert-Fx ('IsBlank('+ $validation +')') $true 'Complete draft is valid'
EditField 'Title' '{ValueText: "  Changed title  ", IsDirty: true}'
$engine.UpdateVariable('testSaved',(Eval $payload))
Assert-Fx 'testSaved.Title' 'Changed title' 'Explicit title edit trims'
foreach ($name in $expected|Where-Object {$_ -ne 'Title'}) {
    $type=@($native.Fields|Where-Object InternalName -eq $name)[0].Type
    $suffix=switch($type){'User'{'.Claims'}'Choice'{'.Value'}'Lookup'{'.Id'}default{''}}
    Assert-Fx ('testSaved.'+$name+$suffix) ((Eval ('gblChangeRecord.'+$name+$suffix)).ToObject()) "$name survives title-only edit"
}
Assert-Fx 'Patch(gblChangeRecord,testSaved).Description' 'DO NOT TOUCH' 'Unmapped sealed Description untouched'
Assert-Fx 'Patch(gblChangeRecord,testSaved).GovernanceID' 'SYN-1001' 'Unmapped field retained by original-record Patch'

# Independent leading status model drives the exhaustive actual guard matrix.
$statusModel=@($model.StatusModels|Where-Object key -eq 'Change')[0]
foreach ($state in $statusModel.states) {
    foreach ($target in $statusModel.states) {
        $old=[string]$state[0]; $next=[string]$target[0]
        $oldLabel=$state[1]; $nextLabel=$target[1]
        $approved=if($old -in @('Approved','Scheduled','Implemented','Closed')){'Date(2026,9,30)+Time(11,12,13)'}else{'If(false,Now(),Blank())'}
        $oldApproval=if($old -eq 'Draft'){'Entwurf'}elseif($old -eq 'Submitted'){'Eingereicht'}elseif($old -eq 'Rejected'){'Abgelehnt'}else{'Genehmigt'}
        $nextApproval=if($next -eq 'Draft'){'Draft'}elseif($next -eq 'Submitted'){'Submitted'}elseif($next -eq 'Rejected'){'Rejected'}else{'Approved'}
        $engine.UpdateVariable('gblChangeRecord',$fixture)
        $engine.UpdateVariable('gblChangeRecord',(Eval ('Patch(gblChangeRecord, {ChangeStatus: {Value: '+(FxString $oldLabel)+'}, ApprovalStatus: {Value: '+(FxString $oldApproval)+'}, ApprovedDate: '+$approved+'})')))
        Hydrate
        $engine.UpdateVariable('gblChangeOriginalStatusKey',"ChangeStatus:$old")
        $engine.UpdateVariable('gblChangeDecision',$next)
        EditField 'ChangeStatus' ('{ValueChoiceKey: '+(FxString "ChangeStatus:$next")+', IsDirty: true}')
        EditField 'ApprovalStatus' ('{ValueChoiceKey: '+(FxString "ApprovalStatus:$nextApproval")+', IsDirty: true}')
        $allowed= -not $state[3] -and ($next -eq $old -or $next -in $state[4])
        Assert-Fx ('IsBlank('+$validation+')') ([bool]$allowed) "Actual lifecycle $old -> $next"
        if ($allowed) {
            $engine.UpdateVariable('testSaved',(Eval $payload))
            Assert-Fx 'testSaved.ChangeStatus.Value' $nextLabel "$old->$next writes native status label"
            Assert-Fx 'testSaved.ApprovalStatus.Value' (@{Draft='Entwurf';Submitted='Eingereicht';Rejected='Abgelehnt';Approved='Genehmigt'}[$nextApproval]) "$old->$next derives approval status"
            if ($old -eq 'Submitted' -and $next -eq 'Approved') { Assert-Fx 'IsBlank(testSaved.ApprovedDate)' $false 'First explicit approval sets timestamp' }
            else { Assert-Fx 'testSaved.ApprovedDate' ((Eval 'gblChangeRecord.ApprovedDate').ToObject()) "$old->$next preserves approval timestamp" }
        }
    }
}
$engine.UpdateVariable('gblChangeRecord',$fixture); Hydrate
$engine.UpdateVariable('gblChangeOriginalStatusKey','ChangeStatus:Draft'); $engine.UpdateVariable('gblChangeDecision','')
foreach ($missing in @('LinkedAsset','Owner','Approver','ChangeType','ChangeRisk','ImplementationPlan','RollbackPlan','PlannedStart','PlannedEnd')) {
    Hydrate
    EditField 'ChangeStatus' '{ValueChoiceKey: "ChangeStatus:Submitted", IsDirty: true}'
    EditField 'ApprovalStatus' '{ValueChoiceKey: "ApprovalStatus:Submitted", IsDirty: true}'
    EditField $missing '{ValueText: "", ValueChoiceKey: "", ValuePersonClaims: "", ValueLookupId: If(false,0,Blank()), ValueDate: If(false,Now(),Blank()), IsDirty: true}'
    Assert-Fx ('IsBlank('+$validation+')') $false "Submit refuses missing $missing"
    EditField 'ChangeStatus' '{ValueChoiceKey: "ChangeStatus:Draft", IsDirty: true}'
    EditField 'ApprovalStatus' '{ValueChoiceKey: "ApprovalStatus:Draft", IsDirty: true}'
    Assert-Fx ('IsBlank('+$validation+')') $true "Draft accepts missing $missing"
}
Hydrate; EditField 'DowntimeMinutes' '{ValueNumber: -1, IsDirty: true}'
Assert-Fx ('IsBlank('+$validation+')') $false 'Negative downtime blocked'
Hydrate; EditField 'PlannedEnd' '{ValueDate: Date(2026,9,30)+Time(0,0,0), IsDirty: true}'
Assert-Fx ('IsBlank('+$validation+')') $false 'Reversed planning dates blocked'
Hydrate; EditField 'DowntimeExpected' '{ValueBoolean: false, IsDirty: true}'
$engine.UpdateVariable('testSaved',(Eval $payload)); Assert-Fx 'testSaved.DowntimeMinutes' 0 'False downtime flag preserves zero minutes'
Hydrate; EditField 'Owner' '{ValuePersonClaims: "", ValuePersonEmail: "", ValueText: "", IsDirty: true}'
$engine.UpdateVariable('testSaved',(Eval $payload)); Assert-Fx 'IsBlank(testSaved.Owner)' $true 'Explicit optional person clear stays native blank'
Hydrate; EditField 'PlannedStart' '{ValueDate: If(false,Now(),Blank()), IsDirty: true}'
$engine.UpdateVariable('testSaved',(Eval $payload)); Assert-Fx 'IsBlank(testSaved.PlannedStart)' $true 'Explicit date clear stays native blank'

# Every ordinary field edit must preserve the other pilot fields and native types.
foreach ($changed in $expected | Where-Object {$_ -notin @('ChangeStatus','ApprovalStatus','ApprovedDate')}) {
    Hydrate
    $type=@($native.Fields|Where-Object InternalName -eq $changed)[0].Type
    $edit=switch($type) {
        'User' {'{ValuePersonClaims:"i:0#.f|membership|changed@tenant.invalid",ValuePersonEmail:"changed@tenant.invalid",ValueText:"Changed",ValuePersonDepartment:"NEW",ValuePersonJobTitle:"NEW",IsDirty:true}'}
        'Choice' {'{ValueChoiceKey:"ChangeType:Emergency",IsDirty:true}'}
        'DateTime' {'{ValueDate:Date(2026,11,30)+Time(0,0,0),IsDirty:true}'}
        'Boolean' {'{ValueBoolean:true,IsDirty:true}'}
        'Number' {'{ValueNumber:12,IsDirty:true}'}
        'Lookup' {'{ValueLookupId:3002,ValueLookupText:"Changed asset",IsDirty:true}'}
        default {'{ValueText:"Changed text äöü",IsDirty:true}'}
    }
    EditField $changed $edit
    $engine.UpdateVariable('testSaved',(Eval $payload))
    foreach ($name in $expected | Where-Object {$_ -ne $changed}) {
        $fieldType=@($native.Fields|Where-Object InternalName -eq $name)[0].Type
        $suffix=switch($fieldType){'User'{'.Claims'}'Choice'{'.Value'}'Lookup'{'.Id'}default{''}}
        Assert-Fx ('testSaved.'+$name+$suffix) ((Eval ('gblChangeRecord.'+$name+$suffix)).ToObject()) "$name survives edit of $changed"
    }
    if ($type -eq 'DateTime') { Assert-Fx ('Hour(testSaved.'+$changed+')') 0 "$changed explicit calendar-day edit" }
    if ($type -eq 'User') {
        Assert-Fx ('testSaved.'+$changed+'.Claims') 'i:0#.f|membership|changed@tenant.invalid' "$changed changed principal"
        Assert-Fx ('testSaved.'+$changed+'.Department') 'NEW' "$changed changed metadata"
    }
}
foreach ($lookup in @('{Id:0,Value:""}','{Id:-1,Value:"invalid"}','If(false,{Id:3001,Value:"asset"},Blank())')) {
    $engine.UpdateVariable('gblChangeRecord',$fixture)
    $engine.UpdateVariable('gblChangeRecord',(Eval ('Patch(gblChangeRecord,{LinkedAsset:'+$lookup+'})')))
    Hydrate
    Assert-Fx 'IsBlank(LookUp(colRecordValues,FieldInternalName="LinkedAsset",ValueLookupId))' $true 'Empty/invalid lookup projects typed blank'
    $engine.UpdateVariable('testSaved',(Eval $payload))
    Assert-Fx 'IsBlank(testSaved.LinkedAsset)' $true 'Empty/invalid lookup never sends zero ID'
}
$engine.UpdateVariable('gblChangeRecord',$fixture);Hydrate
$engine.UpdateVariable('gblEditorMode','New')
$engine.UpdateVariable('gblChangeOriginalStatusKey','ChangeStatus:Draft')
$engine.UpdateVariable('gblChangeRecord',(Eval 'Patch(gblChangeRecord,{ApprovedDate:Date(2026,9,30)+Time(11,12,13)})'))
foreach ($name in $expected | Where-Object {$_ -ne 'Title'}) {
    EditField $name '{ValueText:"",ValueNumber:If(false,0,Blank()),ValueBoolean:false,ValueDate:If(false,Now(),Blank()),ValueLookupId:If(false,0,Blank()),ValueLookupText:"",ValuePersonClaims:"",ValuePersonEmail:"",ValueChoiceKey:"",IsDirty:false,IsValid:true}'
}
EditField 'ChangeStatus' '{ValueChoiceKey:"ChangeStatus:Draft"}'
EditField 'ApprovalStatus' '{ValueChoiceKey:"ApprovalStatus:Draft"}'
Assert-Fx ('IsBlank('+$validation+')') $true 'New incomplete draft is valid'
$engine.UpdateVariable('testSaved',(Eval $payload))
Assert-Fx 'testSaved.ChangeStatus.Value' 'Entwurf' 'New draft uses native status label'
Assert-Fx 'testSaved.ApprovalStatus.Value' 'Entwurf' 'New draft derives native approval label'
foreach ($name in @('Owner','Approver','ChangeType','LinkedAsset','PlannedStart','PlannedEnd','ActualEnd','ApprovedDate','DowntimeMinutes')) {
    Assert-Fx ('IsBlank(testSaved.'+$name+')') $true "New $name cannot inherit a previous loaded record"
}
Assert-Fx 'testSaved.IsActive' $false 'New explicit false remains false'
EditField 'ChangeStatus' '{ValueChoiceKey:"ChangeStatus:Submitted",IsDirty:true}'
EditField 'ApprovalStatus' '{ValueChoiceKey:"ApprovalStatus:Submitted",IsDirty:true}'
Assert-Fx ('IsBlank('+$validation+')') $false 'New row cannot bypass Draft'
$engine.UpdateVariable('gblEditorMode','Edit')
$engine.UpdateVariable('gblChangeRecord',$fixture)
$engine.UpdateVariable('gblChangeRecord',(Eval 'Patch(gblChangeRecord,{ChangeStatus:If(false,{Value:"Entwurf"},Blank())})'));Hydrate
$engine.UpdateVariable('gblChangeOriginalStatusKey','')
Assert-Fx 'IsBlank(LookUp(colEditorValues,FieldInternalName="ChangeStatus",ValueChoiceKey))' $true 'Legacy native blank remains blank after hydration'
Assert-Fx ('IsBlank('+$validation+')') $false 'Legacy row needs an explicit status assignment'
EditField 'ChangeStatus' '{ValueChoiceKey:"ChangeStatus:Draft",IsDirty:true}'
Assert-Fx ('IsBlank('+$validation+')') $true 'Legacy Draft assignment is explicit'
EditField 'ChangeStatus' '{ValueChoiceKey:"ChangeStatus:Submitted",IsDirty:true}'
EditField 'ApprovalStatus' '{ValueChoiceKey:"ApprovalStatus:Submitted",IsDirty:true}'
Assert-Fx ('IsBlank('+$validation+')') $false 'Legacy row cannot be silently submitted'

$engine.UpdateVariable('gblChangeRecord',$fixture)
$engine.UpdateVariable('gblChangeRecord',(Eval 'Patch(gblChangeRecord,{ChangeStatus:{Value:"Geplant"},ApprovalStatus:{Value:"Genehmigt"},ApprovedDate:Date(2026,9,30)+Time(11,12,13),ActualEnd:If(false,Now(),Blank())})'));Hydrate
$engine.UpdateVariable('gblChangeOriginalStatusKey','ChangeStatus:Scheduled')
EditField 'ChangeStatus' '{ValueChoiceKey:"ChangeStatus:Implemented",IsDirty:true}'
Assert-Fx ('IsBlank('+$validation+')') $false 'Implementation requires actual end'
EditField 'ActualEnd' '{ValueDate:Date(2026,10,2)+Time(0,0,0),IsDirty:true}'
Assert-Fx ('IsBlank('+$validation+')') $true 'Implementation with retained approval and actual end permitted'
$engine.UpdateVariable('gblChangeRecord',(Eval 'Patch(gblChangeRecord,{ApprovedDate:If(false,Now(),Blank())})'))
Assert-Fx ('IsBlank('+$validation+')') $false 'Later transition refuses missing original approval stamp'
$engine.UpdateVariable('gblChangeRecord',$fixture)

# A forged choice or mail alias cannot stand in for the explicit assigned decision.
$engine.UpdateVariable('gblChangeRecord',(Eval 'Patch(gblChangeRecord,{ChangeStatus:{Value:"Eingereicht"},ApprovalStatus:{Value:"Eingereicht"}})')); Hydrate
$engine.UpdateVariable('gblChangeOriginalStatusKey','ChangeStatus:Submitted')
foreach ($target in @('Approved','Rejected')) {
    EditField 'ChangeStatus' ('{ValueChoiceKey: '+(FxString "ChangeStatus:$target")+', IsDirty:true}')
    EditField 'ApprovalStatus' ('{ValueChoiceKey: '+(FxString "ApprovalStatus:$target")+', IsDirty:true}')
    $engine.UpdateVariable('gblChangeDecision','')
    Assert-Fx ('IsBlank('+$validation+')') $false 'Status selection without a decision is rejected'
    $engine.UpdateVariable('gblChangeDecision',$target)
    foreach ($actor in @('', 'i:0#.f|membership|foreign@tenant.invalid','i:0#.f|membership|alias@tenant.invalid')) {
        $engine.UpdateVariable('gblChangeActorClaims',$actor)
        Assert-Fx ('IsBlank('+$validation+')') $false "Decision refuses actor $actor"
    }
    $engine.UpdateVariable('gblChangeActorClaims','i:0#.f|membership|synthetic@tenant.invalid')
    Assert-Fx ('IsBlank('+$validation+')') $true 'Assigned verified actor can decide'
}
foreach ($field in @('LinkedAsset','Owner','Approver','ChangeType','ChangeRisk','ImplementationPlan','RollbackPlan')) {
    Hydrate; EditField $field '{IsDirty:true}'
    Assert-Fx ('IsBlank('+$validation+')') $false "Submitted locks $field even against stale controls"
    $engine.UpdateVariable('changeField',(Eval ('{FieldInternalName:'+(FxString $field)+'}')))
    Assert-Fx ('('+$readOnly+').IsReadOnly') $true "Actual submitted UI locks $field"
}
$engine.UpdateVariable('gblUser',(Eval '{EntraObjectId:GUID("11111111-1111-1111-1111-111111111111"),Email:"alias@tenant.invalid"}'))
foreach ($case in @(
    @{Id='11111111-1111-1111-1111-111111111111';Upn='Synthetic@Tenant.Invalid';Expected='i:0#.f|membership|synthetic@tenant.invalid'},
    @{Id='22222222-2222-2222-2222-222222222222';Upn='synthetic@tenant.invalid';Expected=''},
    @{Id='';Upn='synthetic@tenant.invalid';Expected=''},
    @{Id='11111111-1111-1111-1111-111111111111';Upn='';Expected=''}
)) {
    $engine.UpdateVariable('gblChangeProfile',(Eval ('{id:'+(FxString $case.Id)+',userPrincipalName:'+(FxString $case.Upn)+'}')))
    Assert-Fx $identityExpression $case.Expected 'Connector identity requires object ID match and canonical UPN'
}
$engine.UpdateVariable('gblChangeRecord',$fixture); $engine.UpdateVariable('gblChangeCurrent',$fixture)
Assert-Fx $conflict $false 'Fresh Modified matches original'
$engine.UpdateVariable('gblChangeCurrent',(Eval 'Patch(gblChangeRecord,{Modified:Date(2026,10,2)+Time(0,0,0)})'))
Assert-Fx $conflict $true 'Parallel change blocks patch'
$engine.UpdateVariable('gblChangeCurrent',(Eval 'Patch(gblChangeRecord,{Modified:If(false,Now(),Blank())})'))
Assert-Fx $conflict $true 'Missing concurrency stamp blocks patch'

# Evaluate the actual Save guard with fresh lifecycle output, including stale CanSave.
$engine.UpdateVariable('gblChangeRecord',$fixture);Hydrate
$engine.UpdateVariable('gblChangeOriginalStatusKey','ChangeStatus:Draft')
foreach ($flag in @('gblSaveBusy','gblLoadBusy','gblShowDiscardDialog','gblEditorConflict')) {$engine.UpdateVariable($flag,$false)}
$engine.UpdateVariable('gblEditorCanSave',$true);$engine.UpdateVariable('gblEditorDirty',$true);$engine.UpdateVariable('gblEditorLoadComplete',$true)
$engine.UpdateVariable('gblSelectedRecordId',1001);$engine.UpdateVariable('gblLoadedRecordId',1001)
$engine.UpdateVariable('gblActiveProvider',(Eval '{ObjectTypeKey:"Change",SupportsList:true,SupportsCreate:true,SupportsEdit:true,SupportsSave:true}'))
[void](Eligible)
Assert-Fx $saveGuard 'Edit' 'Loaded draft can save'
foreach ($flag in @('gblSaveBusy','gblLoadBusy','gblShowDiscardDialog','gblEditorConflict')) {
    $engine.UpdateVariable($flag,$true);Assert-Fx $saveGuard 'Disabled' "Change save blocks $flag";$engine.UpdateVariable($flag,$false)
}
EditField 'ChangeStatus' '{ValueChoiceKey:"ChangeStatus:Closed",IsDirty:true}'
[void](Eligible)
Assert-Fx $saveGuard 'Disabled' 'Stale CanSave cannot permit an illegal jump'
Hydrate;EditField 'Title' '{ValueText:"",IsDirty:true}'
[void](Eligible)
Assert-Fx $saveGuard 'Disabled' 'Blank Title blocks native save'
EditField 'Title' ('{ValueText:'+(FxString ('x'*256))+',IsDirty:true}')
Assert-Fx $saveGuard 'Disabled' 'Title above native limit blocks save'
EditField 'Title' ('{ValueText:'+(FxString ('x'*255))+',IsDirty:true}')
Assert-Fx $saveGuard 'Edit' 'Title boundary 255 permitted'
$engine.UpdateVariable('gblLoadedRecordId',1002)
Assert-Fx $saveGuard 'Disabled' 'Loaded ID mismatch blocks save'

$engine.UpdateVariable('gblChangeOriginalStatusKey','ChangeStatus:Submitted');Hydrate
foreach ($name in @('ApprovedDate','ApprovalStatus')) {
    $engine.UpdateVariable('changeField',(Eval ('{FieldInternalName:'+(FxString $name)+'}')))
    Assert-Fx ('('+$readOnly+').IsReadOnly') $true "$name cannot be edited independently"
}
foreach ($final in @('ChangeStatus:Rejected','ChangeStatus:Closed')) {
    $engine.UpdateVariable('gblChangeOriginalStatusKey',$final)
    foreach ($name in $expected) {
        $engine.UpdateVariable('changeField',(Eval ('{FieldInternalName:'+(FxString $name)+'}')))
        Assert-Fx ('('+$readOnly+').IsReadOnly') $true "$final field $name is read-only"
    }
}
$sync = Property 'lblChangeSyncApproval' 'OnSelect'
$at = $sync.IndexOf('Switch(');$syncExpression='Switch'+(Balanced $sync ($at+6) '(' ')')
foreach ($state in $statusModel.states) {
    EditField 'ChangeStatus' ('{ValueChoiceKey:'+(FxString "ChangeStatus:$($state[0])")+'}')
    $approval=if($state[0] -in @('Draft','Submitted','Rejected')){[string]$state[0]}else{'Approved'}
    Assert-Fx $syncExpression "ApprovalStatus:$approval" 'Actual status event derives approval key'
}
$dropdownItems=Property 'drpEditorChoice' 'Items'
$engine.UpdateVariable('ThisItem',(Eval '{EditorFieldKey:"Change:ChangeStatus",ValueChoiceKey:"ChangeStatus:Approved"}'))
$engine.UpdateVariable('gblChangeOriginalStatusKey','ChangeStatus:Submitted')
Assert-Fx ('CountRows(Filter('+$dropdownItems+',ChoiceKey="ChangeStatus:Approved"))') 1 'Pending explicit approval remains visible in read-only dropdown'
$engine.UpdateVariable('ThisItem',(Eval 'Patch(ThisItem,{ValueChoiceKey:"ChangeStatus:Draft"})'))
$engine.UpdateVariable('gblChangeOriginalStatusKey','ChangeStatus:Draft');$engine.UpdateVariable('gblEditorMode','New')
Assert-Fx ('CountRows(Filter('+$dropdownItems+',ChoiceKey="ChangeStatus:Submitted"))') 0 'New row offers only Draft'
$engine.UpdateVariable('gblEditorMode','Edit')
Assert-Fx ('CountRows(Filter('+$dropdownItems+',ChoiceKey="ChangeStatus:Submitted"))') 1 'Saved draft offers Submit'
$rows=1..3000|ForEach-Object {'{ID:'+$_+',Title:'+(FxString $(if($_ -eq 3000){'FINAL'}else{'OTHER'}))+'}'}
$engine.UpdateVariable('Changes',(Eval ('Table('+($rows -join ',')+')')))
$engine.UpdateVariable('gblCurrentPage','ObjectList');$engine.UpdateVariable('gblActiveProvider',(Eval '{SupportsList:true}'))
$engine.UpdateVariable('gblRecordQuery','FINAL');$engine.UpdateVariable('gblRecordQueryId',0)
Assert-Fx ('First('+$items+').ID') 3000 'Actual prefix query finds row beyond 2000'
$engine.UpdateVariable('gblRecordQueryId',3000);$engine.UpdateVariable('gblRecordQuery','NO MATCH')
Assert-Fx ('First('+$items+').ID') 3000 'Actual ID query ignores title filter'
$engine.UpdateVariable('gblRecordQueryId',-1)
Assert-Fx ('CountRows('+$items+')') 0 'Invalid ID cannot fall back to unfiltered query'
Write-Host "Actual Change Power Fx passed: $checks assertions. Native roles, delegation and approval actor require separate DEV acceptance."
