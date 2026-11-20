[CmdletBinding()]
param(
    [string]$RepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')),
    [string]$PowerFxDirectory
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# Compile the actual architecture; no auth, connector or metadata-write boundary.
Import-Module (Join-Path $RepositoryRoot 'provisioning/Modules/Model.psm1') -Force
Import-Module (Join-Path $RepositoryRoot 'provisioning/Modules/Compiler.psm1') -Force
$model = Get-GPArchitectureModel -Root (Join-Path $RepositoryRoot 'provisioning')
$schema = Compile-GPArchitecture $model
$source = Get-Content (Join-Path $RepositoryRoot 'powerplatform/canvas/GovernancePortal/Src/scrShell.pa.yaml') -Raw
$dropdown = [regex]::Match($source, '(?ms)- drpEditorChoice:.*?(?=^ *- cmbEditorLookup:)').Value
if ($dropdown -notmatch '(?m)^ *AllowEmptySelection: =true\r?$' -or $dropdown -notmatch '(?m)^ *Items.Value: =DisplayNameDE\r?$') {
    throw 'Choice display must use DisplayNameDE and preserve an empty optional selection.'
}
$default = [regex]::Match($dropdown, '(?ms)^ *(?<indent>Default): \|-\r?\n(?<formula>.*?)(?=^ *DisplayMode:)').Groups['formula'].Value.Trim().TrimStart('=')
if (-not $default -or $default -notmatch 'choiceOption.EditorFieldKey = ThisItem.EditorFieldKey' -or $default -notmatch 'choiceOption.ChoiceKey = ThisItem.ValueChoiceKey' -or $default -notmatch 'choiceOption.DisplayNameDE') {
    throw 'Choice Default must resolve the field-scoped qualified key to its displayed label.'
}
if ($dropdown -notmatch 'editorKey: ThisItem.EditorFieldKey' -or $dropdown -notmatch 'LookUp\(colEditorValues, EditorFieldKey = editorKey\)' -or $dropdown -notmatch 'ValueChoiceKey: Self.Selected.ChoiceKey') {
    throw 'Choice OnChange must capture the internal key before patching the stable field record.'
}
$patches = @([regex]::Matches($source, '(?m)^\s*Value: (?<formula>With\(\{choiceField: LookUp\(colEditorValues, FieldInternalName = "(?<field>[^"]+)"\)[^\r\n]+)'))
$expected = @('Criticality','DataClassification','LifecycleStatus','ConfidentialityRequirement','IntegrityRequirement','AvailabilityRequirement','GovernanceStatus','Criticality','SystemType','Environment')
if ($patches.Count -ne $expected.Count) { throw "Expected ten native Asset/System choice adapters, got $($patches.Count)." }
if ($source -match 'Value: LookUp\(colEditorValues,[^\r\n]+ValueChoiceKey\)') { throw 'Qualified metadata keys must not reach native SharePoint Choice.Value.' }
$guards = @([regex]::Matches($source, '(?m)CountRows\(Filter\(colEditorValues As choiceField,[^\r\n]+\)\) = 0'))
if ($guards.Count -ne 2 -or $guards[0].Value -cne $guards[1].Value) { throw 'Save and revalidation must independently reject nonempty unmapped choice keys.' }
foreach ($fragment in @('choiceField.ControlType = "Choice"','!IsBlank(choiceField.ValueChoiceKey)','IsBlank(LookUp(colEditorChoiceOptions','choiceOption.EditorFieldKey = choiceField.EditorFieldKey','choiceOption.ChoiceKey = choiceField.ValueChoiceKey','choiceOption.DisplayNameDE')) {
    if (-not $guards[0].Value.Contains($fragment)) { throw "Missing choice eligibility guard: $fragment" }
}
if ($PowerFxDirectory) {
    foreach ($library in 'Microsoft.PowerFx.Core.dll','Microsoft.PowerFx.Interpreter.dll') {
        [void][System.Reflection.Assembly]::LoadFrom((Join-Path $PowerFxDirectory $library))
    }
    $engine = [Microsoft.PowerFx.RecalcEngine]::new()
    $options = [Microsoft.PowerFx.ParserOptions]::new()
    $options.Culture = [System.Globalization.CultureInfo]::InvariantCulture
    $checks = 0
    function FxString([string]$Value) { return '"' + $Value.Replace('"','""') + '"' }
    function Assert-Formula([string]$Formula, $Expected, [string]$Context) {
        $result = $engine.Eval($Formula, $null, $options)
        if ($result -is [Microsoft.PowerFx.Types.ErrorValue]) { throw "${Context}: $($result.ToObject())" }
        $actual = $result.ToObject()
        if ($actual -cne $Expected) { throw "${Context}: expected '$Expected', got '$actual'." }
        $script:checks++
    }
}
$valueCount = 0
for ($i=0; $i -lt $patches.Count; $i++) {
    $field = $patches[$i].Groups['field'].Value
    $object = if ($i -lt 6) { 'Asset' } else { 'System' }
    if ($field -cne $expected[$i]) { throw "Unexpected native choice adapter $i/$field." }
    $native = @(($schema.Lists | Where-Object ObjectKey -eq $object).Fields | Where-Object InternalName -eq $field)
    if ($native.Count -ne 1 -or $native[0].Type -ne 'Choice') { throw "Missing native Choice schema: $object/$field" }
    $set = @($model.ChoiceSets | Where-Object key -eq $native[0].ChoiceSet)[0]
    if (($native[0].Choices -join '|') -cne (($set.values | ForEach-Object { $_[1] }) -join '|')) { throw "Compiler labels differ: $object/$field" }
    $valueCount += $set.values.Count
    if (-not $PowerFxDirectory) { continue }
    $editorKey = "${object}:$field"
    $records = @($set.values | ForEach-Object {
        '{EditorFieldKey: '+(FxString $editorKey)+', ChoiceKey: '+(FxString "$($set.key):$($_[0])")+', DisplayNameDE: '+(FxString $_[1])+'}'
    })
    # A foreign field with the same key must never supply this field's label.
    $records = @('{EditorFieldKey: "Foreign:Choice", ChoiceKey: '+(FxString "$($set.key):$($set.values[0][0])")+', DisplayNameDE: "WRONG FIELD"}') + $records
    $engine.UpdateVariable('colEditorChoiceOptions', $engine.Eval('Table('+($records -join ',')+')', $null, $options))
    foreach ($value in $set.values) {
        $key = "$($set.key):$($value[0])"
        $row = '{EditorFieldKey: '+(FxString $editorKey)+', ControlType: "Choice", FieldInternalName: '+(FxString $field)+', ValueChoiceKey: '+(FxString $key)+'}'
        $engine.UpdateVariable('ThisItem', $engine.Eval($row, $null, $options))
        $engine.UpdateVariable('colEditorValues', $engine.Eval('Table('+$row+')', $null, $options))
        Assert-Formula $default $value[1] "$object/$field/$key display"
        Assert-Formula $patches[$i].Groups['formula'].Value $value[1] "$object/$field/$key native Patch"
        Assert-Formula $guards[0].Value $true "$object/$field/$key eligible"
    }
    foreach ($case in @(@('', $true), @('Criticality:Unknown', $false))) {
        $row = '{EditorFieldKey: '+(FxString $editorKey)+', ControlType: "Choice", FieldInternalName: '+(FxString $field)+', ValueChoiceKey: '+(FxString $case[0])+'}'
        $engine.UpdateVariable('ThisItem', $engine.Eval($row, $null, $options))
        $engine.UpdateVariable('colEditorValues', $engine.Eval('Table('+$row+')', $null, $options))
        Assert-Formula $default $null "$object/$field/empty-or-unknown display"
        Assert-Formula $patches[$i].Groups['formula'].Value $null "$object/$field/empty-or-unknown native Patch"
        Assert-Formula $guards[0].Value $case[1] "$object/$field/empty-or-unknown eligibility"
    }
    $row = '{EditorFieldKey: "Foreign:Missing", ControlType: "Choice", FieldInternalName: '+(FxString $field)+', ValueChoiceKey: '+(FxString "$($set.key):$($set.values[0][0])")+'}'
    $engine.UpdateVariable('colEditorValues', $engine.Eval('Table('+$row+')', $null, $options))
    Assert-Formula $guards[0].Value $false "$object/$field rejects another field's option"
}
if ($PowerFxDirectory) {
    $capture = [regex]::Match($dropdown, '(?s)With\(\s*(?<record>\{\s*editorKey:.*?\})\s*,\s*Patch\(').Groups['record'].Value.Replace('Self.Selected', 'testChoiceInput.Selected').Replace('ThisItem', 'testChoiceItem')
    if (-not $capture) { throw 'Missing captured Choice update record.' }
    foreach ($required in @($true, $false)) {
        $engine.UpdateVariable('testChoiceItem', $engine.Eval('{EditorFieldKey: "Asset:Criticality", IsRequired: '+$required.ToString().ToLowerInvariant()+'}', $null, $options))
        foreach ($selected in @(@('Criticality:High','Hoch'), @('',''))) {
            $engine.UpdateVariable('testChoiceInput', $engine.Eval('{Selected: {ChoiceKey: '+(FxString $selected[0])+', DisplayNameDE: '+(FxString $selected[1])+'}}', $null, $options))
            Assert-Formula ('('+ $capture +').editorInput.ValueChoiceKey') $selected[0] 'Choice event keeps qualified key'
            Assert-Formula ('('+ $capture +').editorInput.ValueText') $selected[1] 'Choice event captures displayed label'
            Assert-Formula ('('+ $capture +').editorInput.IsValid') (-not $required -or $selected[0] -ne '') 'Choice event required validity'
            Assert-Formula ('('+ $capture +').editorInput.IsDirty') $true 'Choice event dirty flag'
        }
    }
}
Write-Host "Canvas choice source/compiler contract passed: ten adapters / $valueCount declared values; no tenant access."
if ($PowerFxDirectory) { Write-Host "Actual choice Power Fx passed: $checks assertions." }
else { Write-Host 'Power Fx execution not run: supply -PowerFxDirectory for the local engine gate.' }
