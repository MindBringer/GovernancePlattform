[CmdletBinding()]
param(
    [string]$RepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')),
    [string]$PowerFxDirectory
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# Offline source/compiler/real Power Fx contracts. No authentication or connector calls.
Import-Module (Join-Path $RepositoryRoot 'provisioning/Modules/Model.psm1') -Force
Import-Module (Join-Path $RepositoryRoot 'provisioning/Modules/Compiler.psm1') -Force
$model = Get-GPArchitectureModel -Root (Join-Path $RepositoryRoot 'provisioning')
$schema = Compile-GPArchitecture $model
$source = Get-Content (Join-Path $RepositoryRoot 'powerplatform/canvas/GovernancePortal/Src/scrShell.pa.yaml') -Raw
$app = Get-Content (Join-Path $RepositoryRoot 'powerplatform/canvas/GovernancePortal/Src/App.pa.yaml') -Raw
function Get-Property([string]$Control, [string]$Property) {
    $m = [regex]::Match($source, "(?m)^(?<indent> *)- ${Control}:\r?`n")
    if (-not $m.Success) { throw "Missing control $Control" }
    $tail = $source.Substring($m.Index + $m.Length)
    $end = [regex]::Match($tail, "(?m)^ {0,$($m.Groups['indent'].Value.Length)}- \w+:")
    if ($end.Success) { $tail = $tail.Substring(0, $end.Index) }
    $p = [regex]::Match($tail, "(?m)^(?<indent> *)${Property}: \|-\r?`n(?<formula>(?:\k<indent> +[^\r\n]*\r?`n|\r?`n)+)")
    if (-not $p.Success) {
        $inline = [regex]::Match($tail, "(?m)^ *${Property}: =(?<formula>[^\r\n]+)")
        if ($inline.Success) { return $inline.Groups['formula'].Value.Trim() }
        throw "Missing formula $Control.$Property"
    }
    return $p.Groups['formula'].Value.Trim().TrimStart('=')
}
function Get-Balanced([string]$Text, [int]$Start, [char]$Open, [char]$Close) {
    $depth = 0; $quoted = $false
    for ($i=$Start; $i -lt $Text.Length; $i++) {
        $ch = $Text[$i]
        if ($ch -eq '"') {
            if ($quoted -and $i+1 -lt $Text.Length -and $Text[$i+1] -eq '"') { $i++; continue }
            $quoted = -not $quoted
        }
        if ($quoted) { continue }
        if ($ch -eq $Open) { $depth++ }
        if ($ch -eq $Close) {
            $depth--
            if ($depth -eq 0) { return $Text.Substring($Start,$i-$Start+1) }
        }
    }
    throw 'Unbalanced expression in actual Canvas source.'
}
$load = Get-Property 'lblRecordLoad' 'OnSelect'
$init = Get-Property 'lblEditorInitialize' 'OnSelect'
$initFilterStart = $init.IndexOf('Filter(')
if ($initFilterStart -lt 0) { throw 'Missing actual editor metadata Filter.' }
$initFilter = 'Filter' + (Get-Balanced $init ($initFilterStart + 6) '(' ')')
if ($initFilter -notmatch 'colFormFields As formField,\s*formField\.ObjectTypeKey = gblSelectedObjectTypeKey') {
    throw 'Editor metadata alias must qualify ObjectTypeKey; implicit binding fails in Power Fx and Studio.'
}
$save = Get-Property 'lblEditorSave' 'OnSelect'
$loadGuard = [regex]::Match($load, '(?s)^If\(\s*(?<guard>.*?)\s*,\s*Set\(gblLoadBusy').Groups['guard'].Value
if ($loadGuard -notmatch '!gblEditorDirty' -or $loadGuard -notmatch 'SupportsList' -or $loadGuard -notmatch 'SupportsEdit' -or $loadGuard -notmatch 'gblSelectedRecordId > 0') { throw 'Missing record load capability/identity/dirty guard.' }
$projections = @([regex]::Matches($load, 'ClearCollect\(colRecordValues, Table\('))
if ($projections.Count -ne 3) { throw 'Exactly three native load providers are expected; Change is verified by Test-CanvasChangeContract.ps1.' }
$records = @{}
foreach ($pair in @(@('Asset','Assets'),@('System','Systems'))) {
    $key = $pair[0]; $ds = $pair[1]
    $index = if ($key -eq 'Asset') {0} else {1}
    $start = $projections[$index].Index + $projections[$index].Value.LastIndexOf('Table(')
    $projection = 'Table' + (Get-Balanced $load ($start+5) '(' ')')
    $patchStart = [regex]::Match($save, "Patch\(\s*${ds},").Index
    if ($patchStart -le 0) { throw "Missing $key Patch" }
    $payloadStart = $save.IndexOf('{', $patchStart)
    $payload = Get-Balanced $save $payloadStart '{' '}'
    $loadedNames = @([regex]::Matches($projection, 'FieldInternalName: "([^"]+)"') | ForEach-Object { $_.Groups[1].Value })
    $writtenNames = @([regex]::Matches($payload, '(?m)^\s*(\w+): ') | Where-Object { $_.Groups[1].Value -notin @('Claims','DisplayName','Email','Department','JobTitle','Picture','Id','Value') } | ForEach-Object { $_.Groups[1].Value })
    $expectedCount = if ($key -eq 'Asset') {17} else {16}
    if ($loadedNames.Count -ne $expectedCount -or ($loadedNames | Sort-Object -Unique).Count -ne $expectedCount -or ($writtenNames.Count -ne $expectedCount) -or (Compare-Object ($loadedNames | Sort-Object) ($writtenNames | Sort-Object))) { throw "$key native load/write sets differ; existing fields could be erased." }
    if ($save -notmatch "(?s)Patch\(\s*${ds},\s*If\([^,]+,\s*gbl${key}Record,\s*Defaults\(${ds}\)") { throw "$key Edit must patch the original loaded native record, preserving connector identity." }
    if ($load -notmatch "Refresh\(${ds}\);\s*Set\(gbl${key}Record, LookUp\(${ds}, ID = gblSelectedRecordId\)\)") { throw "$key must refresh and load by delegable ID equality." }
    $items = Get-Property "gal${key}Records" 'Items'
    if ($items -notmatch "Filter\(${ds}, ID = gblRecordQueryId\)" -or $items -notmatch "Filter\(${ds}, StartsWith\(Title, gblRecordQuery\)\)" -or $items -match 'FirstN|LastN|ClearCollect|ForAll|\bID\s*[<>]') { throw "$key list must retain server delegation without local truncation or ID range filtering." }
    $open = Get-Property "gal${key}Records" 'OnSelect'
    if ($open -notmatch "gblObjectType = `"$key`"" -or $open -notmatch 'gblActiveProvider.ObjectTypeKey' -or $open -notmatch '!gblLoadBusy' -or $open -notmatch 'Select\(lblRecordLoad\)') { throw "$key stale gallery must not open another provider's record." }
    $native = @($schema.Lists | Where-Object ObjectKey -eq $key)[0]
    foreach ($name in $loadedNames) {
        if (-not ($native.Fields.InternalName -contains $name)) { throw "$key.$name has no architecture field." }
        $nativeField = @($native.Fields | Where-Object InternalName -eq $name)[0]
        $row = [regex]::Match($projection, '\{FieldInternalName: "'+$name+'", NativeControlType: "(?<type>[^"]+)"').Groups['type'].Value
        if ($row -ne $nativeField.Type) { throw "$key.$name load type $row differs from compiler $($nativeField.Type)." }
    }
    $records[$key] = @{Projection=$projection; Payload=$payload; Fields=$loadedNames; Schema=$native}
}
if ('SystemDescription' -notin $records.System.Fields -or 'Description' -in $records.System.Fields) {
    throw 'System business description must round-trip through its own Note column; the native sealed Description column must not be patched.'
}
$errorLabel = [regex]::Match($source, '(?ms)- lblEditorSaveError:\r?\n(?<control>.*?)(?=^ {0,36}- \w+:|\z)').Groups['control'].Value
if ($errorLabel -notmatch 'AutoHeight: =true' -or $errorLabel -notmatch 'Live: =Live.Assertive') {
    throw 'Editor error must grow for long messages and announce them to assistive technology.'
}
$providers = (Get-Content (Join-Path $RepositoryRoot 'powerplatform/config/ObjectProviderRegistry.json') -Raw | ConvertFrom-Json).providers
foreach ($p in $providers) {
    $supported = $p.objectTypeKey -in @('Asset','System','Change')
    if ($p.supportsList -ne $supported -or $p.supportsCreate -ne $supported -or $p.supportsEdit -ne $supported -or $p.supportsSave -ne $supported) { throw "Capabilities overstate available record paths: $($p.objectTypeKey)" }
}
foreach ($fragment in @('gblEditorLoadComplete','gblLoadedRecordId = gblSelectedRecordId','!gblEditorConflict','gblEditorDirty','FirstError.Kind = ErrorKind.Conflict','If(IsBlank(gblSaveError),')) {
    if (-not $save.Contains($fragment) -and -not (Get-Property 'lblEditorSave' 'DisplayMode').Contains($fragment)) { throw "Missing edit safety: $fragment" }
}
if ($init -notmatch 'ControlType\) <> loadedValue.NativeControlType' -or $init -notmatch '__unmapped__' -or $init -notmatch 'IsDirty: false' -or $source -notmatch 'ShowNavigation: =true' -or $app -notmatch 'OnError: \|-') { throw 'Missing hydration/type, unmapped-choice, paging or data-error contract.' }
$lookupControl = [regex]::Match($source, '(?ms)^ *- cmbEditorLookup:\r?\n(?<control>.*?)(?=^ {0,42}- \w+:|\z)').Groups['control'].Value
if ($lookupControl -match '(?m)^ +SearchItems:') {
    throw 'Lookup SearchItems is a private Studio-generated rule; restore public bindings in Studio and verify its export.'
}
if ($lookupControl -notmatch 'DisplayFields: =\["DisplayText"\]' -or
    $lookupControl -notmatch 'SearchFields: =\["DisplayText", "SecondaryText"\]' -or
    $lookupControl -notmatch 'IsSearchable: =true') {
    throw 'Lookup public display/search contract must explicitly use DisplayText/SecondaryText and enable search.'
}
$dateClear = Get-Property 'btnEditorDateClear' 'OnSelect'
foreach ($token in @('!ThisItem.IsRequired','!IsBlank(ThisItem.ValueDate)','ValueDate: If(false, Now(), Blank())','Reset(datEditorDate)','Select(lblEditorRevalidate)')) {
    if (-not $dateClear.Contains($token)) { throw "Missing optional date clear contract: $token" }
}
if ((Get-Property 'datEditorDate' 'OnChange') -notmatch 'ValueDate: If\(IsBlank\(Self.SelectedDate\), If\(false, Now\(\), Blank\(\)\), Self.SelectedDate \+ Time\(0, 0, 0\)\)') {
    throw 'Date picker must explicitly update the DateTime editor contract and retain typed blank.'
}
Write-Host 'Record core source/compiler passed: Asset 17 / System 16 fields; native lists, original Patch bases, capability and conflict contracts.'
if (-not $PowerFxDirectory) { return }
foreach ($dll in 'Microsoft.PowerFx.Core.dll','Microsoft.PowerFx.Interpreter.dll') { [void][Reflection.Assembly]::LoadFrom((Join-Path $PowerFxDirectory $dll)) }
$engine = [Microsoft.PowerFx.RecalcEngine]::new()
$engine.UpdateVariable('lblChangeValidation', $engine.Eval('{Text: ""}', $null, $null))
$engine.UpdateVariable('gblChangeOriginalStatusKey', '')
$engine.UpdateVariable('gblObjectType', 'Asset')
$options = [Microsoft.PowerFx.ParserOptions]::new()
$options.Culture = [Globalization.CultureInfo]::InvariantCulture
$parseOptions = [Microsoft.PowerFx.ParserOptions]::new(); $parseOptions.AllowsSideEffects = $true; $parseOptions.Culture = [Globalization.CultureInfo]::InvariantCulture
$checks=0; $syntax=0
function Eval([string]$Formula) {
    $value = $engine.Eval($Formula, $null, $options)
    if ($value -is [Microsoft.PowerFx.Types.ErrorValue]) { throw "Power Fx error in $Formula : $($value.ToObject() | ConvertTo-Json -Compress)" }
    return $value
}
function Assert-Fx([string]$Formula, $Expected, [string]$Context) {
    $actual = (Eval $Formula).ToObject()
    if ($actual -cne $Expected) { throw "${Context}: expected '$Expected', got '$actual'. Formula: $Formula" }
    $script:checks++
}
function FxString([string]$Value) { '"'+$Value.Replace('"','""')+'"' }
# The browser treats maxlength=0 as zero characters, not an unlimited input.
# Evaluate the actual control property for every mapped native Text column.
$textMaxLength = Get-Property 'txtEditorText' 'MaxLength'
foreach ($key in @('Asset','System')) {
    foreach ($field in $records[$key].Schema.Fields | Where-Object { $_.Type -eq 'Text' -and $_.InternalName -in $records[$key].Fields }) {
        $nativeLimit = if ($field.ContainsKey('maxLength')) { [int]$field.maxLength } else { 255 }
        $limit = 'With({ThisItem: {FieldInternalName: '+(FxString $field.InternalName)+'}}, '+$textMaxLength+')'
        Assert-Fx ('Len("P2 Synthetic Test") <= ('+$limit+')') $true "$key/$($field.InternalName) accepts ordinary keyboard input"
        Assert-Fx ('('+ $limit +') <= '+$nativeLimit) $true "$key/$($field.InternalName) input respects the native text limit"
        if ($field.InternalName -eq 'Title') {
            Assert-Fx ('255 <= ('+$limit+')') $true "$key native Title accepts its full 255-character boundary"
        }
    }
}
foreach ($text in @($source,$app)) {
    foreach ($m in [regex]::Matches($text,'(?m)^(?<indent> *)(?<key>\w+): \|-\r?\n(?<formula>(?:\k<indent> +[^\r\n]*\r?\n|\r?\n)+)')) {
        $formula=$m.Groups['formula'].Value.Trim().TrimStart('=')
        $parsed=$engine.Parse($formula,$parseOptions);$syntax++
        if(-not $parsed.IsSuccess){ Write-Host ($formula.Substring(0,[Math]::Min(100,$formula.Length))); foreach($err in $parsed.Errors){Write-Host ($err.Span | Out-String)}; throw "Actual $($m.Groups['key'].Value) syntax: $(($parsed.Errors | ForEach-Object Message) -join '; ')"}
    }
}
$hydrateStart = $init.IndexOf('With(', $init.IndexOf('{editorInput:'))
$hydrate = 'With'+(Get-Balanced $init ($hydrateStart+4) '(' ')')
$saveGuard = (Get-Property 'lblEditorSave' 'DisplayMode').Replace('DisplayMode.Edit','"Edit"').Replace('DisplayMode.Disabled','"Disabled"')
# Evaluate the actual event guards: hydrated defaults must never dirty or erase a row.
$engine.UpdateVariable('gblEditorMode','Edit')
$baseline = '{ValueText: "SYNTHETIC", ValueNumber: 0, ValueDate: Date(2026,10,1)+Time(13,14,15), ValueBoolean: false, ValueChoiceKey: "Criticality:High", ValueLookupId: 3001, ValuePersonClaims: "i:0#.f|membership|synthetic@tenant.invalid", ValuePersonEmail: "synthetic@tenant.invalid"}'
$engine.UpdateVariable('ThisItem',(Eval $baseline))
foreach ($control in @('txtEditorText','txtEditorMultiline','txtEditorNumber','datEditorDate','togEditorBoolean','drpEditorChoice','cmbEditorLookup','cmbEditorPerson')) {
    $events=if($control -eq 'togEditorBoolean'){@('OnCheck','OnUncheck')}else{@('OnChange')}
    foreach($event in $events) {
        $handler=Get-Property $control $event
        $guard=[regex]::Match($handler,'^If\(\s*(?<guard>[^\r\n]+),').Groups['guard'].Value.Replace('Self.','testControl.').Replace('DisplayMode.Edit','"Edit"')
        if(-not $guard){throw "Missing actual $control.$event guard."}
        $sameText=if($control -eq 'txtEditorNumber'){'0'}else{'SYNTHETIC'}
        $engine.UpdateVariable('testControl',(Eval ('{Visible: true, DisplayMode: "Edit", Text: '+(FxString $sameText)+', Value: false, SelectedDate: Date(2026,10,1), Selected: {ChoiceKey: "Criticality:High"}, SelectedItems: Table({LookupId: 3001, UserPrincipalName: "synthetic@tenant.invalid", DisplayName: "SYNTHETIC"})}')))
        Assert-Fx $guard $false "$control.$event loaded default does not rewrite or dirty"
        $engine.UpdateVariable('testControl',(Eval '{Visible: true, DisplayMode: "Edit", Text: "1", Value: true, SelectedDate: Date(2026,10,2), Selected: {ChoiceKey: "Criticality:Low"}, SelectedItems: Table({LookupId: 3002, UserPrincipalName: "changed@tenant.invalid", DisplayName: "CHANGED"})}'))
        Assert-Fx $guard $true "$control.$event explicit change reaches update"
        if($control -in @('drpEditorChoice','cmbEditorLookup','cmbEditorPerson')) {
            $engine.UpdateVariable('testControl',(Eval 'Patch(testControl, {Selected: {ChoiceKey: ""}, SelectedItems: FirstN(testControl.SelectedItems,0)})'))
            Assert-Fx $guard $true "$control explicit optional clearing reaches update"
        }
        if($control -eq 'drpEditorChoice') {
            $engine.UpdateVariable('ThisItem',(Eval 'Patch(ThisItem, {ValueChoiceKey: "Criticality:__unmapped__:OLD"})'))
            Assert-Fx $guard $false 'Unknown persisted choice cannot silently disappear in empty default event'
            $engine.UpdateVariable('testControl',(Eval 'Patch(testControl, {Selected: {ChoiceKey: "Criticality:High"}})'))
            Assert-Fx $guard $true 'Unknown persisted choice permits explicit valid replacement'
            $engine.UpdateVariable('ThisItem',(Eval $baseline))
        }
    }
}
# P2: evaluate presence changes through the actual numeric event guard,
# including zero/blank; do not infer behavior from Power Fx coercion rules.
$numberHandler = Get-Property 'txtEditorNumber' 'OnChange'
$numberGuard = [regex]::Match($numberHandler,'^If\(\s*(?<guard>[^\r\n]+),').Groups['guard'].Value.Replace('Self.','testControl.').Replace('DisplayMode.Edit','"Edit"')
$engine.UpdateVariable('ThisItem',(Eval $baseline))
$engine.UpdateVariable('testControl',(Eval '{Visible: true, DisplayMode: "Edit", Text: ""}'))
Assert-Fx $numberGuard $true 'Optional numeric zero can be explicitly cleared'
$engine.UpdateVariable('ThisItem',(Eval 'Patch(ThisItem, {ValueNumber: If(false,0,Blank())})'))
$engine.UpdateVariable('testControl',(Eval 'Patch(testControl, {Text: "0"})'))
Assert-Fx $numberGuard $true 'Optional blank and numeric zero remain distinct'
$engine.UpdateVariable('testControl',(Eval 'Patch(testControl, {Text: ""})'))
Assert-Fx $numberGuard $false 'Hydrated blank number remains clean'
$engine.UpdateVariable('ThisItem',(Eval $baseline))
# Initial editor values must use the same DateTime column type as hydration.
$dateDefaultStart = $init.IndexOf('ValueDate: If(') + 'ValueDate: If'.Length
$dateDefault = 'If' + (Get-Balanced $init $dateDefaultStart '(' ')')
$engine.UpdateVariable('fieldDefinition',(Eval '{ControlType: "DateTime", DefaultValue: ""}'))
$engine.UpdateVariable('testDateDefault',(Eval ('Patch({ValueDate: Date(2026,10,1)+Time(13,14,15)}, {ValueDate: '+$dateDefault+'})')))
Assert-Fx 'IsBlank(testDateDefault.ValueDate)' $true 'Empty review default retains typed DateTime blank'
$engine.UpdateVariable('fieldDefinition',(Eval 'Patch(fieldDefinition, {DefaultValue: "2026-11-30T13:14:15"})'))
$engine.UpdateVariable('testDateDefault',(Eval ('Patch({ValueDate: Date(2026,10,1)+Time(13,14,15)}, {ValueDate: '+$dateDefault+'})')))
Assert-Fx 'Hour(testDateDefault.ValueDate)' 13 'DateTime metadata default retains its hour'
Assert-Fx 'Minute(testDateDefault.ValueDate)' 14 'DateTime metadata default retains its minute'
Assert-Fx 'Second(testDateDefault.ValueDate)' 15 'DateTime metadata default retains its second'
# Complete native rows, synthetic identities only, including alias email vs claims principal.
foreach ($key in @('Asset','System')) {
    $engine = [Microsoft.PowerFx.RecalcEngine]::new()
    $engine.UpdateVariable('lblChangeValidation', $engine.Eval('{Text: ""}', $null, $null))
    $engine.UpdateVariable('gblChangeOriginalStatusKey', '')
    $engine.UpdateVariable('gblObjectType', 'Asset')
    $contract=$records[$key]
    $engine.UpdateVariable('gblObjectType',$key)
    $engine.UpdateVariable('gblEditorMode','Edit')
    $engine.UpdateVariable('gblSelectedObjectTypeKey',$key)
    $formRows = @()
    foreach ($type in @('Asset','System')) {
        foreach ($fieldName in $records[$type].Fields) {
            $formRows += '{ObjectTypeKey: '+(FxString $type)+', FieldInternalName: '+(FxString $fieldName)+'}'
        }
        $formRows += '{ObjectTypeKey: '+(FxString $type)+', FieldInternalName: "UnsupportedField"}'
    }
    $formRows += '{ObjectTypeKey: "Foreign", FieldInternalName: "Title"}'
    $engine.UpdateVariable('colFormFields',(Eval ('Table('+($formRows -join ',')+')')))
    # Check/evaluate the actual aliased filter, not only parse it or mirror its predicate.
    $engine.UpdateVariable('testFormFields',(Eval $initFilter))
    Assert-Fx 'CountRows(testFormFields)' $contract.Fields.Count "$key actual metadata scope retains all native fields"
    Assert-Fx 'CountRows(Filter(testFormFields, FieldInternalName = "UnsupportedField"))' 0 "$key unsupported form field excluded"
    Assert-Fx ('CountRows(Filter(testFormFields, ObjectTypeKey <> '+(FxString $key)+'))') 0 "$key foreign metadata excluded"
    $choiceRows=@(); $choiceCases=@{}
    foreach ($field in ($contract.Schema.Fields | Where-Object { $_.InternalName -in $contract.Fields -and $_.Type -eq 'Choice' })) {
        $set=@($model.ChoiceSets | Where-Object key -eq $field.ChoiceSet)[0]
        $choiceCases[$field.InternalName]=@{Set=$set.key; Value=$set.values[-1][1]; Key="$($set.key):$($set.values[-1][0])"}
        foreach($choice in $set.values){$choiceRows += '{ChoiceSetKey: '+(FxString $set.key)+', ChoiceKey: '+(FxString "$($set.key):$($choice[0])")+', DisplayNameDE: '+(FxString $choice[1])+', IsActive: true}'}
    }
    $engine.UpdateVariable('colChoiceValues',(Eval ('Table('+($choiceRows -join ',')+')')))
    foreach($empty in @($false,$true)) {
        $nativeFields=@('ID: 1001','Modified: Date(2026,10,1)+Time(12,0,0)')
        $metadata=@()
        foreach($name in $contract.Fields) {
            $field=@($contract.Schema.Fields | Where-Object InternalName -eq $name)[0]
            $value = switch($field.Type) {
                'User' { '{Claims: "i:0#.f|membership|synthetic@tenant.invalid", DisplayName: "Synthetische Person", Email: "alias@example.invalid", Department: "TEST", JobTitle: "TEST", Picture: ""}' }
                'Choice' { '{Value: '+(FxString $choiceCases[$name].Value)+'}' }
                'DateTime' { 'Date(2026,9,23)+Time(13,14,15)' }
                'Number' { '0' }
                'Boolean' { 'false' }
                'Lookup' { '{Id: 3001, Value: "Synthetisches Ziel"}' }
                default { FxString ('Wert "'+$name+'" äöü') }
            }
            if($name -eq 'Title') {$value='"P1-SYNTHETIC"'}
            elseif($empty -and $field.Type -ne 'Boolean') {$value='If(false, '+$value+', Blank())'}
            $nativeFields += $name+': '+$value
            $set = if($choiceCases.ContainsKey($name)) {$choiceCases[$name].Set} else {''}
            $metadata += '{FieldInternalName: '+(FxString $name)+', EditorFieldKey: '+(FxString "$key`:$name")+', ControlType: '+(FxString $field.Type)+', ChoiceSetKey: '+(FxString $set)+', IsRequired: '+$field.Required.ToString().ToLowerInvariant()+', ValueText: "", ValueNumber: If(false,0,Blank()), ValueBoolean: If(false,true,Blank()), ValueDate: If(false,Now(),Blank()), ValueLookupId: If(false,0,Blank()), ValueLookupText: "", ValuePersonEmail: "", ValuePersonClaims: "", ValuePersonDepartment: "", ValuePersonJobTitle: "", ValueChoiceKey: "", IsDirty: false, IsValid: true, ErrorMessage: ""}'
        }
        $nativeRecord=Eval ('{'+($nativeFields -join ',')+'}')
        if(-not $empty){$nonemptyFixture=$nativeRecord}
        $engine.UpdateVariable("gbl${key}Record",$nativeRecord)
        $engine.UpdateVariable('colRecordValues',(Eval $contract.Projection))
        Assert-Fx 'CountRows(colRecordValues)' $contract.Fields.Count "$key complete projection"
        $engine.UpdateVariable('colEditorValues',(Eval ('Table('+($metadata -join ',')+')')))
        $values=Eval ('ForAll(colRecordValues As loadedValue, Patch(LookUp(colEditorValues, FieldInternalName = loadedValue.FieldInternalName), '+$hydrate+'))')
        $engine.UpdateVariable('colEditorValues',$values)
        Assert-Fx 'CountRows(Filter(colEditorValues, IsDirty))' 0 "$key hydration is clean"
        Assert-Fx 'CountRows(Filter(colEditorValues, !IsValid))' 0 "$key optional blanks remain valid"
        $optionRows=@()
        foreach($field in $choiceCases.Keys) {
            $set=@($model.ChoiceSets | Where-Object key -eq $choiceCases[$field].Set)[0]
            foreach($choice in $set.values){$optionRows += '{EditorFieldKey: '+(FxString "$key`:$field")+', ChoiceKey: '+(FxString "$($set.key):$($choice[0])")+', DisplayNameDE: '+(FxString $choice[1])+'}'}
        }
        $engine.UpdateVariable('colEditorChoiceOptions',(Eval ('Table('+($optionRows -join ',')+')')))
        $saved=Eval $contract.Payload
        $engine.UpdateVariable('testSaved',$saved)
        foreach($name in $contract.Fields) {
            $field=@($contract.Schema.Fields | Where-Object InternalName -eq $name)[0]
            $suffix = switch($field.Type){'Choice'{'.Value'}'User'{'.Claims'}'Lookup'{'.Id'}default{''}}
            $expected=(Eval ("gbl${key}Record.$name"+$suffix)).ToObject()
            Assert-Fx ('testSaved.'+$name+$suffix) $expected "$key/$name unchanged native round-trip (blank=$empty)"
            if($field.Type -eq 'Choice' -and $empty) {
                Assert-Fx ('IsBlank(testSaved.'+$name+')') $true "$key/$name optional choice sends a blank connector field, not a record with blank Value"
            }
            if($field.Type -eq 'User' -and -not $empty) {
                Assert-Fx ('testSaved.'+$name+'.Email') 'alias@example.invalid' "$key/$name untouched native email retained"
                Assert-Fx ('testSaved.'+$name+'.Department') 'TEST' "$key/$name department retained"
                Assert-Fx ('testSaved.'+$name+'.JobTitle') 'TEST' "$key/$name job title retained"
                Assert-Fx ('LookUp(colEditorValues, FieldInternalName = '+(FxString $name)+', ValuePersonEmail)') 'synthetic@tenant.invalid' "$key/$name uses claims principal rather than email alias"
            }
        }
        # Change one field using the hydrated editor; all other native values survive.
        $engine.UpdateVariable('colEditorValues',(Eval 'ForAll(colEditorValues As fieldValue, If(fieldValue.FieldInternalName = "Title", Patch(fieldValue, {ValueText: "  P1-CHANGED  ", IsDirty: true}), fieldValue))'))
        $engine.UpdateVariable('testSaved',(Eval $contract.Payload))
        Assert-Fx 'testSaved.Title' 'P1-CHANGED' "$key changed Title trims"
        foreach($name in ($contract.Fields | Where-Object {$_ -ne 'Title'})) {
            $field=@($contract.Schema.Fields | Where-Object InternalName -eq $name)[0]
            $suffix=switch($field.Type){'Choice'{'.Value'}'User'{'.Claims'}'Lookup'{'.Id'}default{''}}
            Assert-Fx ('testSaved.'+$name+$suffix) ((Eval ("gbl${key}Record.$name"+$suffix)).ToObject()) "$key/$name survives another field's edit"
        }
        foreach($g in @('gblSaveBusy','gblLoadBusy','gblShowDiscardDialog','gblEditorConflict')) {$engine.UpdateVariable($g,$false)}
        $engine.UpdateVariable('gblEditorMode','Edit');$engine.UpdateVariable('gblCurrentPage','ObjectList')
        $engine.UpdateVariable('gblEditorCanSave',$true);$engine.UpdateVariable('gblEditorLoadComplete',$true)
        $engine.UpdateVariable('gblEditorDirty',$true);$engine.UpdateVariable('gblSelectedRecordId',1001);$engine.UpdateVariable('gblLoadedRecordId',1001)
        $engine.UpdateVariable('gblActiveProvider',(Eval ('{ObjectTypeKey: '+(FxString $key)+', SupportsList: true, SupportsCreate: true, SupportsEdit: true, SupportsSave: true}')))
        Assert-Fx $saveGuard 'Edit' "$key loaded changed record permits save"
        foreach($state in @(@('gblEditorConflict',$true),@('gblEditorLoadComplete',$false),@('gblEditorDirty',$false),@('gblLoadBusy',$true),@('gblLoadedRecordId',1002))) {
            $original=(Eval $state[0]);$engine.UpdateVariable($state[0],$state[1])
            Assert-Fx $saveGuard 'Disabled' "$key blocks $($state[0]) despite stale CanSave"
            $engine.UpdateVariable($state[0],$original)
        }
        $conflict=[regex]::Match($save,'IsBlank\(gbl'+$key+'Current.Modified\) \|\| IsBlank\(gbl'+$key+'Record.Modified\) \|\| gbl'+$key+'Current.Modified <> gbl'+$key+'Record.Modified').Value
        if(-not $conflict){throw 'Missing native Modified preflight.'}
        $engine.UpdateVariable("gbl${key}Current",$nativeRecord)
        Assert-Fx $conflict $false "$key unchanged source"
        $engine.UpdateVariable("gbl${key}Current",(Eval ("Patch(gbl${key}Record, {Modified: Date(2026,10,2)+Time(0,0,0)})")))
        Assert-Fx $conflict $true "$key detects parallel modification"
        $engine.UpdateVariable("gbl${key}Current",(Eval ("Patch(gbl${key}Record, {Modified: If(false, Now(), Blank())})")))
        Assert-Fx $conflict $true "$key refuses missing concurrency stamp"
        $engine.UpdateVariable("gbl${key}Current",(Eval ("Patch(gbl${key}Record, {ID: If(false, 0, Blank())})")))
        Assert-Fx ("IsBlank(gbl${key}Current.ID)") $true "$key detects deleted/inaccessible source"
    }
    if ($key -eq 'System') {
        # Exercise the actual load/hydration/payload when SharePoint represents an
        # empty lookup as Id=0. A title-only edit must never send that sentinel.
        $lookupDefault = Get-Property 'cmbEditorLookup' 'DefaultSelectedItems'
        $lookupItems = Get-Property 'cmbEditorLookup' 'Items'
        $lookupHandler = Get-Property 'cmbEditorLookup' 'OnChange'
        $lookupGuard = [regex]::Match($lookupHandler, '^If\(\s*(?<guard>[^\r\n]+),').Groups['guard'].Value.Replace('Self.','testControl.').Replace('DisplayMode.Edit','"Edit"')
        $engine.UpdateVariable('colLookupValues',(Eval 'Table({LookupObjectTypeKey: "Asset", LookupId: 3001, DisplayText: "Synthetisches Ziel", SecondaryText: "SYN-3001", IsActiveValue: true}, {LookupObjectTypeKey: "System", LookupId: 3001, DisplayText: "Fremder Typ", SecondaryText: "", IsActiveValue: true}, {LookupObjectTypeKey: "Asset", LookupId: 3002, DisplayText: "Inaktiv", SecondaryText: "", IsActiveValue: false}, {LookupObjectTypeKey: "Asset", LookupId: 0, DisplayText: "", SecondaryText: "", IsActiveValue: true})'))
        $engine.UpdateVariable('colEditorLookupSelections',(Eval 'FirstN(Table({EditorFieldKey: "System:LinkedAsset", LookupId: 3001}),0)'))
        foreach ($case in @(
            @{Name='zero sentinel'; Lookup='{Id: 0, Value: ""}'; Id=$null; Text=''},
            @{Name='native blank'; Lookup='If(false,{Id: 3001, Value: "Synthetisches Ziel"},Blank())'; Id=$null; Text=''},
            @{Name='negative invalid ID'; Lookup='{Id: -1, Value: "Kein gültiges Ziel"}'; Id=$null; Text=''},
            @{Name='existing positive ID'; Lookup='{Id: 3001, Value: "Synthetisches Ziel"}'; Id=3001; Text='Synthetisches Ziel'}
        )) {
            $engine.UpdateVariable('gblSystemRecord',$nonemptyFixture)
            $engine.UpdateVariable('gblSystemRecord',(Eval ('Patch(gblSystemRecord, {LinkedAsset: '+$case.Lookup+'})')))
            $engine.UpdateVariable('colRecordValues',(Eval $contract.Projection))
            Assert-Fx 'LookUp(colRecordValues, FieldInternalName = "LinkedAsset", ValueLookupId)' $case.Id "System/$($case.Name) load normalizes lookup identity"
            Assert-Fx 'LookUp(colRecordValues, FieldInternalName = "LinkedAsset", ValueLookupText)' $case.Text "System/$($case.Name) load normalizes lookup label"
            $engine.UpdateVariable('colEditorValues',(Eval ('Table('+($metadata -join ',')+')')))
            $engine.UpdateVariable('colEditorValues',(Eval ('ForAll(colRecordValues As loadedValue, Patch(LookUp(colEditorValues, FieldInternalName = loadedValue.FieldInternalName), '+$hydrate+'))')))
            Assert-Fx 'CountRows(Filter(colEditorValues, IsDirty))' 0 "System/$($case.Name) hydration stays clean"
            Assert-Fx 'CountRows(Filter(colEditorValues, !IsValid))' 0 "System/$($case.Name) optional lookup remains valid"
            $engine.UpdateVariable('ThisItem',(Eval 'Patch(LookUp(colEditorValues, FieldInternalName = "LinkedAsset"), {AllowMultiple: false, LookupObjectTypeKey: "Asset"})'))
            $defaults=Eval $lookupDefault
            $engine.UpdateVariable('testLookupDefaults',$defaults)
            $expectedCount=if($null -eq $case.Id){0}else{1}
            Assert-Fx 'CountRows(testLookupDefaults)' $expectedCount "System/$($case.Name) default has no phantom target"
            $engine.UpdateVariable('testControl',(Eval '{Visible: true, DisplayMode: "Edit", SelectedItems: testLookupDefaults}'))
            Assert-Fx $lookupGuard $false "System/$($case.Name) default event does not dirty lookup"
            $engine.UpdateVariable('loadedValue',(Eval 'LookUp(colRecordValues, FieldInternalName = "LinkedAsset")'))
            $engine.UpdateVariable('colEditorValues',(Eval 'ForAll(colEditorValues As v, If(v.FieldInternalName = "LinkedAsset", Patch(v, {IsRequired: true}), v))'))
            $engine.UpdateVariable('testRequiredLookup',(Eval $hydrate))
            Assert-Fx 'testRequiredLookup.IsValid' ($null -ne $case.Id) "System/$($case.Name) required lookup needs real identity"
            $engine.UpdateVariable('colEditorValues',(Eval 'ForAll(colEditorValues As v, If(v.FieldInternalName = "LinkedAsset", Patch(v, {IsRequired: false}), v))'))
            $engine.UpdateVariable('colEditorValues',(Eval 'ForAll(colEditorValues As v, If(v.FieldInternalName = "Title", Patch(v, {ValueText: "  P1-LOOKUP-EDIT  ", IsDirty: true}), v))'))
            $engine.UpdateVariable('testSaved',(Eval $contract.Payload))
            Assert-Fx 'testSaved.Title' 'P1-LOOKUP-EDIT' "System/$($case.Name) title edit persists"
            Assert-Fx 'testSaved.LinkedAsset.Id' $case.Id "System/$($case.Name) title edit never sends a lookup sentinel"
            foreach($name in ($contract.Fields | Where-Object {$_ -notin @('Title','LinkedAsset')})) {
                $field=@($contract.Schema.Fields | Where-Object InternalName -eq $name)[0]
                $suffix=switch($field.Type){'Choice'{'.Value'}'User'{'.Claims'}default{''}}
                Assert-Fx ('testSaved.'+$name+$suffix) ((Eval ('gblSystemRecord.'+$name+$suffix)).ToObject()) "System/$($case.Name) title edit retains $name"
            }
        }
        Assert-Fx ('CountRows('+$lookupItems+')') 1 'Lookup Items exclude foreign, inactive and zero-ID targets'
        $engine.UpdateVariable('ThisItem',(Eval 'Patch(ThisItem, {AllowMultiple: true})'))
        $engine.UpdateVariable('colEditorLookupSelections',(Eval 'Table({EditorFieldKey: "System:LinkedAsset", LookupId: 3001}, {EditorFieldKey: "System:LinkedAsset", LookupId: 3002}, {EditorFieldKey: "OtherField", LookupId: 0})'))
        Assert-Fx ('CountRows('+$lookupDefault+')') 2 'Multiple lookup defaults retain selected active and inactive identities, scoped by field/type'
        # A stale editor value must not resurrect an invalid target at serialization.
        $engine.UpdateVariable('colEditorValues',(Eval 'ForAll(colEditorValues As v, If(v.FieldInternalName = "LinkedAsset", Patch(v, {ValueLookupId: 0, ValueLookupText: ""}), v))'))
        $engine.UpdateVariable('testSaved',(Eval $contract.Payload))
        Assert-Fx 'IsBlank(testSaved.LinkedAsset)' $true 'System payload rejects a stale zero lookup ID'
        $engine.UpdateVariable('colEditorValues',(Eval 'ForAll(colEditorValues As v, If(v.FieldInternalName = "SystemDescription", Patch(v, {ValueText: "Zeile 1" & Char(10) & "Zeile 2 äöü", IsDirty: true}), v))'))
        $engine.UpdateVariable('testSaved',(Eval $contract.Payload))
        Assert-Fx 'testSaved.SystemDescription' "Zeile 1`nZeile 2 äöü" 'System description preserves multiline text in the actual payload'
        $engine.UpdateVariable('colEditorValues',(Eval 'ForAll(colEditorValues As v, If(v.FieldInternalName = "SystemDescription", Patch(v, {ValueText: "", IsDirty: true}), v))'))
        $engine.UpdateVariable('testSaved',(Eval $contract.Payload))
        Assert-Fx 'IsBlank(testSaved.SystemDescription)' $true 'System description can be explicitly cleared'
    }
    $engine.UpdateVariable("gbl${key}Record",$nonemptyFixture)
    $engine.UpdateVariable('colRecordValues',(Eval $contract.Projection))
    $engine.UpdateVariable('colEditorValues',(Eval ('ForAll(colRecordValues As loadedValue, Patch(LookUp(colEditorValues, FieldInternalName = loadedValue.FieldInternalName), '+$hydrate+'))')))
    $complete=[regex]::Match($init,'(?m)Set\(gblEditorLoadComplete, (?<expression>CountRows\(Filter\(colRecordValues[^\r\n]+ = 0)\),').Groups['expression'].Value
    if(-not $complete){throw 'Missing actual metadata completeness/type expression.'}
    Assert-Fx $complete $true "$key complete metadata permits hydration"
    $completeValues=Eval 'colEditorValues'
    $engine.UpdateVariable('colEditorValues',(Eval 'Filter(colEditorValues, FieldInternalName <> "Owner")'))
    Assert-Fx $complete $false "$key missing metadata blocks hydration"
    $engine.UpdateVariable('colEditorValues',$completeValues)
    $engine.UpdateVariable('colEditorValues',(Eval 'ForAll(colEditorValues As v, If(v.FieldInternalName = "Owner", Patch(v, {ControlType: "Text"}), v))'))
    Assert-Fx $complete $false "$key incorrect metadata type blocks hydration"
    $engine.UpdateVariable('colEditorValues',$completeValues)
    if ($key -eq 'Asset') {
        # P2 uses actual control update records and actual load/hydrate/save
        # expressions with synthetic directory identities. No connector writes.
        function EventGuard([string]$Handler) {
            [regex]::Match($Handler,'^If\(\s*(?<guard>[^\r\n]+),').Groups['guard'].Value.Replace('Self.','testControl.').Replace('DisplayMode.Edit','"Edit"')
        }
        function UpdateRecord([string]$Handler, [int]$Index = 0) {
            $patches = @([regex]::Matches($Handler,'Patch\(\s*colEditorValues,\s*ThisItem,\s*'))
            if ($patches.Count -le $Index) { throw 'Missing actual field event update record.' }
            Get-Balanced $Handler ($patches[$Index].Index + $patches[$Index].Length) '{' '}'
        }
        function ApplyFieldUpdate([string]$Update) {
            $engine.UpdateVariable('colEditorValues',(Eval ('ForAll(colEditorValues As row, If(row.EditorFieldKey = ThisItem.EditorFieldKey, Patch(row, '+$Update+'), row))')))
            $engine.UpdateVariable('testSaved',(Eval $contract.Payload))
        }
        function AssertOtherAssetFields([string]$ChangedField, [string]$Context) {
            foreach ($other in ($contract.Fields | Where-Object { $_ -ne $ChangedField })) {
                $f = @($contract.Schema.Fields | Where-Object InternalName -eq $other)[0]
                $suffixes = switch ($f.Type) {
                    'User' { @('.Claims','.DisplayName','.Email','.Department','.JobTitle','.Picture') }
                    'Choice' { @('.Value') }
                    default { @('') }
                }
                foreach ($suffix in $suffixes) {
                    $base = if ((Eval 'gblEditorMode').ToObject() -eq 'New') {'testBaseline.'} else {'gblAssetRecord.'}
                    Assert-Fx ('testSaved.'+$other+$suffix) ((Eval ($base+$other+$suffix)).ToObject()) "$Context preserves $other$suffix"
                }
            }
            Assert-Fx 'CountRows(Filter(colEditorValues, IsDirty))' 1 "$Context changes exactly one editor row"
        }
        $personHandler = Get-Property 'cmbEditorPerson' 'OnChange'
        $personDefault = Get-Property 'cmbEditorPerson' 'DefaultSelectedItems'
        foreach ($personField in @('Owner','DeputyOwner','BusinessOwner','TechnicalOwner','DataSteward')) {
            foreach ($mode in @('Edit','New')) {
                foreach ($clear in @($false,$true)) {
                    $engine.UpdateVariable('gblEditorMode',$mode)
                    $engine.UpdateVariable('gblAssetRecord',$nonemptyFixture)
                    $engine.UpdateVariable('colEditorValues',$completeValues)
                    $engine.UpdateVariable('testBaseline',(Eval $contract.Payload))
                    $engine.UpdateVariable('ThisItem',(Eval ('LookUp(colEditorValues, FieldInternalName = '+(FxString $personField)+')')))
                    $engine.UpdateVariable('testControl',(Eval '{Visible: true, DisplayMode: "Edit", SelectedDate: Date(2026,11,30), Selected: {ChoiceKey: "", DisplayNameDE: ""}, SelectedItems: Table({UserPrincipalName: "Changed.Person@tenant.invalid", DisplayName: "Andere synthetische Person"})}'))
                    if ($clear) { $engine.UpdateVariable('testControl',(Eval 'Patch(testControl, {SelectedItems: FirstN(testControl.SelectedItems,0)})')) }
                    Assert-Fx (EventGuard $personHandler) $true "Asset/$personField/$mode clear=$clear explicit event"
                    $update = (UpdateRecord $personHandler $(if ($clear) {0} else {1})).Replace('Self.','testControl.')
                    if (-not $clear) { $engine.UpdateVariable('selectedPerson',(Eval 'First(testControl.SelectedItems)')) }
                    ApplyFieldUpdate $update
                    if ($clear) {
                        Assert-Fx ('IsBlank(testSaved.'+$personField+')') $true "Asset/$personField/$mode clear writes native blank"
                    } else {
                        Assert-Fx ('testSaved.'+$personField+'.Claims') 'i:0#.f|membership|changed.person@tenant.invalid' "Asset/$personField/$mode uses normalized UPN identity"
                        Assert-Fx ('testSaved.'+$personField+'.Email') 'Changed.Person@tenant.invalid' "Asset/$personField/$mode retains selected principal"
                        Assert-Fx ('testSaved.'+$personField+'.DisplayName') 'Andere synthetische Person' "Asset/$personField/$mode selected display name"
                        Assert-Fx ('IsBlank(testSaved.'+$personField+'.Department)') $true "Asset/$personField/$mode old department cannot leak"
                        Assert-Fx ('IsBlank(testSaved.'+$personField+'.JobTitle)') $true "Asset/$personField/$mode old job title cannot leak"
                    }
                    AssertOtherAssetFields $personField "Asset/$personField/$mode clear=$clear"
                    # Local saved-value round-trip; it is not a SharePoint/Studio acceptance.
                    $engine.UpdateVariable('gblAssetRecord',(Eval 'Patch(gblAssetRecord, testSaved)'))
                    $engine.UpdateVariable('gblEditorMode','Edit')
                    $engine.UpdateVariable('colRecordValues',(Eval $contract.Projection))
                    $engine.UpdateVariable('colEditorValues',(Eval ('ForAll(colRecordValues As loadedValue, Patch(LookUp(colEditorValues, FieldInternalName = loadedValue.FieldInternalName), '+$hydrate+'))')))
                    Assert-Fx 'CountRows(Filter(colEditorValues, IsDirty || !IsValid))' 0 "Asset/$personField/$mode clean valid reopen"
                    $engine.UpdateVariable('ThisItem',(Eval ('LookUp(colEditorValues, FieldInternalName = '+(FxString $personField)+')')))
                    $engine.UpdateVariable('testDefault',(Eval $personDefault))
                    if ($clear) { Assert-Fx 'IsBlank(testDefault)' $true "Asset/$personField/$mode cleared default" }
                    else { Assert-Fx 'First(testDefault).UserPrincipalName' 'changed.person@tenant.invalid' "Asset/$personField/$mode reopened claims principal" }
                }
            }
        }
        $engine.UpdateVariable('gblEditorMode','Edit')
        $engine.UpdateVariable('gblAssetRecord',$nonemptyFixture)
        $dateHandler = Get-Property 'datEditorDate' 'OnChange'
        $dateClearHandler = Get-Property 'btnEditorDateClear' 'OnSelect'
        if ($dateClearHandler -notmatch 'Reset\(datEditorDate\);\s*Select\(lblEditorRevalidate\)') { throw 'Date clear must reset the picker and revalidate the editor.' }
        foreach ($dateField in @('LastReviewDate','NextReviewDate')) {
            foreach ($clear in @($false,$true)) {
                $engine.UpdateVariable('colEditorValues',$completeValues)
                $engine.UpdateVariable('ThisItem',(Eval ('LookUp(colEditorValues, FieldInternalName = '+(FxString $dateField)+')')))
                $engine.UpdateVariable('testControl',(Eval 'Patch(testControl, {Visible: true, DisplayMode: "Edit", SelectedDate: Date(2026,11,30)})'))
                $handler = if ($clear) {$dateClearHandler} else {$dateHandler}
                Assert-Fx (EventGuard $handler) $true "Asset/$dateField clear=$clear explicit event"
                ApplyFieldUpdate ((UpdateRecord $handler).Replace('Self.','testControl.'))
                if ($clear) { Assert-Fx ('IsBlank(testSaved.'+$dateField+')') $true "Asset/$dateField persists native blank" }
                else { Assert-Fx ('testSaved.'+$dateField) ((Eval 'Date(2026,11,30)').ToObject()) "Asset/$dateField explicitly sets a calendar date" }
                AssertOtherAssetFields $dateField "Asset/$dateField clear=$clear"
            }
            $engine.UpdateVariable('testControl',(Eval 'Patch(testControl, {DisplayMode: "Disabled"})'))
            Assert-Fx (EventGuard $dateClearHandler) $false "Asset/$dateField busy/read-only clear blocked"
            $engine.UpdateVariable('testControl',(Eval 'Patch(testControl, {DisplayMode: "Edit", Visible: false})'))
            Assert-Fx (EventGuard $dateClearHandler) $false "Asset/$dateField hidden clear blocked"
            $engine.UpdateVariable('testControl',(Eval 'Patch(testControl, {Visible: true})'))
            $engine.UpdateVariable('ThisItem',(Eval 'Patch(ThisItem, {IsRequired: true})'))
            Assert-Fx (EventGuard $dateClearHandler) $false "Asset/$dateField required clear blocked"
            $engine.UpdateVariable('ThisItem',(Eval 'Patch(ThisItem, {IsRequired: false, ValueDate: If(false,Now(),Blank())})'))
            Assert-Fx (EventGuard $dateClearHandler) $false "Asset/$dateField already blank clear blocked"
        }
        $choiceHandler = Get-Property 'drpEditorChoice' 'OnChange'
        $choiceStart = $choiceHandler.IndexOf('editorInput:') + 'editorInput:'.Length
        $choiceUpdate = Get-Balanced $choiceHandler ($choiceHandler.IndexOf('{',$choiceStart)) '{' '}'
        foreach ($choiceField in @('Criticality','DataClassification','LifecycleStatus','ConfidentialityRequirement','IntegrityRequirement','AvailabilityRequirement')) {
            $set = @($model.ChoiceSets | Where-Object key -eq $choiceCases[$choiceField].Set)[0]
            foreach ($clear in @($false,$true)) {
                $engine.UpdateVariable('colEditorValues',$completeValues)
                $engine.UpdateVariable('ThisItem',(Eval ('LookUp(colEditorValues, FieldInternalName = '+(FxString $choiceField)+')')))
                $selection = if ($clear) {'{ChoiceKey: "", DisplayNameDE: ""}'} else {'{ChoiceKey: '+(FxString ($set.key+':'+$set.values[0][0]))+', DisplayNameDE: '+(FxString $set.values[0][1])+'}'}
                $engine.UpdateVariable('testControl',(Eval ('Patch(testControl, {Visible: true, DisplayMode: "Edit", Selected: '+$selection+'})')))
                Assert-Fx (EventGuard $choiceHandler) $true "Asset/$choiceField clear=$clear explicit event"
                ApplyFieldUpdate ($choiceUpdate.Replace('Self.','testControl.'))
                if ($clear) {
                    Assert-Fx ('IsBlank(testSaved.'+$choiceField+'.Value)') $true "Asset/$choiceField clears connector choice Value"
                    Assert-Fx ('IsBlank(testSaved.'+$choiceField+')') $true "Asset/$choiceField explicit clear sends a blank connector field"
                }
                else { Assert-Fx ('testSaved.'+$choiceField+'.Value') $set.values[0][1] "Asset/$choiceField persists architecture choice label" }
                AssertOtherAssetFields $choiceField "Asset/$choiceField clear=$clear"
            }
        }
        $engine.UpdateVariable('gblAssetRecord',$nonemptyFixture)
        $engine.UpdateVariable('colRecordValues',(Eval $contract.Projection))
        $engine.UpdateVariable('colEditorValues',$completeValues)
    }
    $engine.UpdateVariable('loadedValue',(Eval 'Patch(LookUp(colRecordValues, FieldInternalName = "Criticality"), {ValueText: "UNKNOWN-NATIVE-VALUE"})'))
    $engine.UpdateVariable('testHydrated',(Eval $hydrate))
    Assert-Fx 'testHydrated.IsValid' $false "$key unknown persisted choice invalid"
    Assert-Fx '":__unmapped__:" in testHydrated.ValueChoiceKey' $true "$key unknown choice not silently blanked"
    Assert-Fx '!IsBlank(testHydrated.ErrorMessage)' $true "$key unknown choice explains the block"
    $engine.UpdateVariable('colEditorValues',(Eval 'ForAll(colEditorValues As v, If(v.FieldInternalName = "Criticality", Patch(v, testHydrated), v))'))
    Assert-Fx $saveGuard 'Disabled' "$key unknown persisted choice blocks stale CanSave"
    $engine.UpdateVariable('colEditorValues',$completeValues)
    $engine.UpdateVariable('gblEditorMode','New')
    $engine.UpdateVariable('gblEditorConflict',$true)
    Assert-Fx $saveGuard 'Disabled' "$key uncertain create cannot be retried through stale CanSave"
    $engine.UpdateVariable('gblEditorMode','Edit')
    $engine.UpdateVariable('gblEditorConflict',$false)
    # Explicitly clearing an optional person must be distinguishable from untouched native identity.
    $engine.UpdateVariable('colEditorValues',(Eval 'ForAll(colEditorValues As v, If(v.FieldInternalName = "Owner", Patch(v, {ValuePersonClaims: "", ValuePersonEmail: "", ValueText: "", IsDirty: true}), v))'))
    $engine.UpdateVariable('testSaved',(Eval $contract.Payload))
    Assert-Fx 'IsBlank(testSaved.Owner)' $true "$key explicit person clear persists"
    $engine.UpdateVariable('colEditorValues',$completeValues)
    $engine.UpdateVariable('gblEditorDirty',$false)
    Assert-Fx $loadGuard $true "$key clean list can load an ID"
    foreach($flag in @('gblSaveBusy','gblLoadBusy','gblShowDiscardDialog','gblEditorDirty')) {
        $engine.UpdateVariable($flag,$true);Assert-Fx $loadGuard $false "$key load blocks $flag";$engine.UpdateVariable($flag,$false)
    }
    $engine.UpdateVariable('gblSelectedRecordId',0);Assert-Fx $loadGuard $false "$key cannot load zero ID";$engine.UpdateVariable('gblSelectedRecordId',1001)
    $engine.UpdateVariable('gblCurrentPage','editor');Assert-Fx $loadGuard $false "$key cannot replace editor from stale list event";$engine.UpdateVariable('gblCurrentPage','ObjectList')
    $provider=Eval 'gblActiveProvider'
    $engine.UpdateVariable('gblActiveProvider',(Eval 'Patch(gblActiveProvider, {SupportsEdit: false})'));Assert-Fx $loadGuard $false "$key unsupported edit blocked";$engine.UpdateVariable('gblActiveProvider',$provider)
    $engine.UpdateVariable('gblActiveProvider',(Eval 'Patch(gblActiveProvider, {ObjectTypeKey: "Foreign"})'));Assert-Fx $loadGuard $false "$key stale provider blocked";$engine.UpdateVariable('gblActiveProvider',$provider)
    # The actual gallery query must find a record beyond 2000 locally too; server delegation is a separate host gate.
    $ds=if($key -eq 'Asset'){'Assets'}else{'Systems'}
    $rows=1..3000 | ForEach-Object { '{ID: '+$_+', Title: '+(FxString $(if($_ -eq 3000){'P1-LAST'}else{'OTHER'}))+'}' }
    $engine.UpdateVariable($ds,(Eval ('Table('+($rows -join ',')+')')))
    $engine.UpdateVariable('gblRecordQuery','P1-LAST');$engine.UpdateVariable('gblRecordQueryId',0)
    $items=Get-Property "gal${key}Records" 'Items'
    Assert-Fx ('CountRows('+$items+')') 1 "$key prefix finds final record in 3000-row fixture"
    Assert-Fx ('First('+$items+').ID') 3000 "$key prefix preserves native ID"
    $engine.UpdateVariable('gblRecordQuery','NO-MATCH');$engine.UpdateVariable('gblRecordQueryId',3000)
    Assert-Fx ('First('+$items+').ID') 3000 "$key exact ID is independent of prefix"
    $engine.UpdateVariable('gblRecordQueryId',-1)
    Assert-Fx ('CountRows('+$items+')') 0 "$key invalid ID never falls back to unfiltered list"
    $engine.UpdateVariable('gblRecordQueryId',0)
    Assert-Fx ('CountRows('+$items+')') 0 "$key empty search result distinct from error"
}
# Run the actual App.OnError behavior, including late errors after the button has
# cleared gblSaveBusy. This uses the real interpreter and synthetic error data.
$errorHandler = [regex]::Match($app, '(?ms)^    OnError: \|-\r?\n(?<formula>.*?)(?=^    OnStart:)').Groups['formula'].Value.Trim().TrimStart('=')
if (-not $errorHandler) { throw 'Missing App.OnError formula.' }
$config = [Microsoft.PowerFx.PowerFxConfig]::new()
[Microsoft.PowerFx.PowerFxConfigExtensions]::EnableSetFunction($config)
$engine = [Microsoft.PowerFx.RecalcEngine]::new($config)
$engine.UpdateVariable('lblChangeValidation', $engine.Eval('{Text: ""}', $null, $null))
$engine.UpdateVariable('gblChangeOriginalStatusKey', '')
$engine.UpdateVariable('gblObjectType', 'Asset')
foreach ($case in @(
    @{Name='late edit failure'; Page='editor'; Busy=$false; Mode='Edit'; Blocks=$true},
    @{Name='late create failure'; Page='editor'; Busy=$false; Mode='New'; Blocks=$true},
    @{Name='busy editor failure'; Page='editor'; Busy=$true; Mode='Edit'; Blocks=$true},
    @{Name='busy save outside editor'; Page='ObjectList'; Busy=$true; Mode='Edit'; Blocks=$true},
    @{Name='list read error'; Page='ObjectList'; Busy=$false; Mode='Edit'; Blocks=$false}
)) {
    $engine.UpdateVariable('gblCurrentPage',$case.Page)
    $engine.UpdateVariable('gblEditorMode',$case.Mode)
    $engine.UpdateVariable('gblSaveBusy',$case.Busy)
    $engine.UpdateVariable('gblLoadBusy',$true)
    $engine.UpdateVariable('gblEditorCanSave',$true)
    $engine.UpdateVariable('gblEditorConflict',$false)
    $engine.UpdateVariable('gblRecordError','')
    $engine.UpdateVariable('gblSaveError','')
    $engine.UpdateVariable('gblEditorLoadComplete',$true)
    $engine.UpdateVariable('FirstError',(Eval '{Message: "SYNTHETIC COLUMN READ-ONLY", Source: "lblEditorSave.OnSelect"}'))
    $result = $engine.Eval($errorHandler, $null, $parseOptions)
    if ($result -is [Microsoft.PowerFx.Types.ErrorValue]) { throw "Actual App.OnError execution failed: $($case.Name)" }
    Assert-Fx '!IsBlank(gblRecordError)' $true "$($case.Name) retains source error"
    Assert-Fx 'gblEditorConflict' $case.Blocks "$($case.Name) blocks uncertain save"
    Assert-Fx 'gblEditorCanSave' (-not $case.Blocks) "$($case.Name) invalidates CanSave"
    Assert-Fx 'gblSaveBusy || gblLoadBusy' $false "$($case.Name) releases busy state"
    Assert-Fx '!IsBlank(gblSaveError)' $case.Blocks "$($case.Name) retains editor error after busy flag reset"
    Assert-Fx (Get-Property 'lblEditorSaveError' 'Visible') ($case.Page -eq 'editor') "$($case.Name) displays editor error on editor page"
    if ($case.Blocks) {
        Assert-Fx ('"SYNTHETIC COLUMN READ-ONLY" in '+(Get-Property 'lblEditorSaveError' 'Text')) $true "$($case.Name) displays concrete failure"
        $engine.UpdateVariable('gblEditorLoadComplete',$false)
        Assert-Fx ('"SYNTHETIC COLUMN READ-ONLY" in '+(Get-Property 'lblEditorSaveError' 'Text')) $true "$($case.Name) concrete save error takes precedence over load warning"
    }
}
foreach ($height in @(48,140)) {
    $engine.UpdateVariable('lblEditorSaveError',(Eval ('{Visible: true, Y: 48, Height: '+$height+'}')))
    Assert-Fx (Get-Property 'galEditorFields' 'Y') (52+$height) "Error height $height moves fields below the entire message"
}
$engine.UpdateVariable('lblEditorSaveError',(Eval '{Visible: false, Y: 48, Height: 140}'))
Assert-Fx (Get-Property 'galEditorFields' 'Y') 56 'No error retains the normal form position'
Write-Host "Actual record core Power Fx passed: $checks assertions; $syntax behavior formulas parsed. Connector delegation/ETag/Studio still require DEV acceptance."
