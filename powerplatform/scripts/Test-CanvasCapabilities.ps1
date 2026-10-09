[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$PowerFxDirectory,
    [string]$RepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# Offline expression tests only. No PAC auth, tenant calls or data writes.
foreach ($library in 'Microsoft.PowerFx.Core.dll', 'Microsoft.PowerFx.Interpreter.dll') {
    [void][System.Reflection.Assembly]::LoadFrom((Join-Path $PowerFxDirectory $library))
}
$engine = [Microsoft.PowerFx.RecalcEngine]::new()
# Provider-only fixture; the real Change invariant is executed in its own gate.
$engine.UpdateVariable('lblChangeValidation', $engine.Eval('{Text: ""}', $null, $null))
$options = [Microsoft.PowerFx.ParserOptions]::new()
$options.Culture = [System.Globalization.CultureInfo]::InvariantCulture
$source = Get-Content (Join-Path $RepositoryRoot 'powerplatform/canvas/GovernancePortal/Src/scrShell.pa.yaml') -Raw

function Get-ControlProperty([string]$Control, [string]$Property) {
    $controlMatch = [regex]::Match($source, "(?m)^(?<indent> *)- ${Control}:\r?`n")
    if (-not $controlMatch.Success) { throw "Missing control: $Control" }
    $indent = $controlMatch.Groups['indent'].Value.Length
    $remainder = $source.Substring($controlMatch.Index + $controlMatch.Length)
    $end = [regex]::Match($remainder, "(?m)^ {0,$indent}- \w+:")
    if ($end.Success) { $remainder = $remainder.Substring(0, $end.Index) }
    $match = [regex]::Match($remainder, "(?m)^(?<indent> *)${Property}: \|-\r?`n(?<formula>(?:\k<indent> +[^\r\n]*\r?`n|\r?`n)+)")
    if (-not $match.Success) { throw "Missing block property: $Control.$Property" }
    return $match.Groups['formula'].Value.Trim().TrimStart('=')
}

$newFormula = Get-ControlProperty 'lblNew' 'DisplayMode'
$saveFormula = Get-ControlProperty 'lblEditorSave' 'DisplayMode'
$revalidate = Get-ControlProperty 'lblEditorRevalidate' 'OnSelect'
$validityMatch = [regex]::Match($revalidate, '(?s)Set\(\s*gblEditorCanSave,\s*(?<formula>.*)\)\s*$')
if (-not $validityMatch.Success) { throw 'Missing editor save eligibility expression.' }
$validityFormula = $validityMatch.Groups['formula'].Value
foreach ($control in 'lblNew', 'lblEditorSave') {
    $action = Get-ControlProperty $control 'OnSelect'
    if ($action -notmatch '^If\(\s*Self\.DisplayMode = DisplayMode\.Edit,') {
        throw "$control.OnSelect must enforce the current DisplayMode before mutations."
    }
}
$newFormula = $newFormula.Replace('DisplayMode.Edit', '"Edit"').Replace('DisplayMode.Disabled', '"Disabled"')
$saveFormula = $saveFormula.Replace('DisplayMode.Edit', '"Edit"').Replace('DisplayMode.Disabled', '"Disabled"')
$providers = (Get-Content (Join-Path $RepositoryRoot 'powerplatform/config/ObjectProviderRegistry.json') -Raw | ConvertFrom-Json).providers
# Independent executable-provider acceptance set; adding a provider requires a real Save implementation and an updated contract.
$writableTypes = @('Asset', 'System', 'Change')
$checks = 0
function Assert-Formula([string]$Formula, $Expected, [string]$Context) {
    $actual = $engine.Eval($Formula, $null, $options).ToObject()
    if ($actual -ne $Expected) { throw "${Context}: expected '$Expected', got '$actual'." }
    $script:checks++
}

$engine.UpdateVariable('gblSelectedObjectTypeKey', 'Asset')
$engine.UpdateVariable('gblObjectType', 'Asset')
$engine.UpdateVariable('gblEditorMode', 'New')
$engine.UpdateVariable('gblSelectedRecordId', 0)
$engine.UpdateVariable('gblSaveBusy', $false)
$engine.UpdateVariable('gblLoadBusy', $false)
$engine.UpdateVariable('gblCurrentPage', 'ObjectList')
$engine.UpdateVariable('gblEditorLoadComplete', $true)
$engine.UpdateVariable('gblEditorDirty', $true)
$engine.UpdateVariable('gblLoadedRecordId', 42)
$engine.UpdateVariable('gblEditorConflict', $false)
$engine.UpdateVariable('gblShowDiscardDialog', $false)
$engine.UpdateVariable('gblEditorCanSave', $true)
$engine.UpdateVariable('colEditorChoiceOptions', $engine.Eval('Table({EditorFieldKey: "Asset:Criticality", ChoiceKey: "Criticality:High", DisplayNameDE: "Hoch"})', $null, $options))
$engine.UpdateVariable('colEditorValues', $engine.Eval('Table({IsValid: true, ControlType: "Text", EditorFieldKey: "Asset:Title", ValueChoiceKey: "", FieldInternalName: "Title", ValueText: "P0-SMOKE"})', $null, $options))

foreach ($provider in $providers) {
    $key = $provider.objectTypeKey
    $record = '{ObjectTypeKey: "' + $key + '", SupportsCreate: ' + $provider.supportsCreate.ToString().ToLowerInvariant() + ', SupportsEdit: ' + $provider.supportsEdit.ToString().ToLowerInvariant() + ', SupportsSave: ' + $provider.supportsSave.ToString().ToLowerInvariant() + '}'
    $engine.UpdateVariable('gblActiveProvider', $engine.Eval($record, $null, $options))
    $engine.UpdateVariable('gblSelectedObjectTypeKey', [string]$key)
    $engine.UpdateVariable('gblObjectType', [string]$key)
    $expected = if ($key -in $writableTypes) { 'Edit' } else { 'Disabled' }
    $engine.UpdateVariable('gblEditorMode', 'New')
    Assert-Formula $newFormula $expected "$key create"
    Assert-Formula $saveFormula $expected "$key save new (including stale true eligibility)"
    Assert-Formula $validityFormula ($key -in $writableTypes) "$key revalidate"
    $engine.UpdateVariable('gblEditorMode', 'Edit')
    $engine.UpdateVariable('gblSelectedRecordId', 42)
    Assert-Formula $saveFormula $expected "$key edit existing"
    $engine.UpdateVariable('gblSelectedRecordId', 0)
    Assert-Formula $saveFormula 'Disabled' "$key edit without ID"
}

$engine.UpdateVariable('gblActiveProvider', $engine.Eval('{ObjectTypeKey: "Asset", SupportsCreate: true, SupportsEdit: true, SupportsSave: true}', $null, $options))
$engine.UpdateVariable('gblSelectedObjectTypeKey', 'Asset')
$engine.UpdateVariable('gblObjectType', 'Asset')
$engine.UpdateVariable('gblEditorMode', 'New')
$engine.UpdateVariable('gblSaveBusy', $true)
Assert-Formula $newFormula 'Disabled' 'Busy create'
Assert-Formula $saveFormula 'Disabled' 'Busy save'
Assert-Formula $validityFormula $false 'Busy revalidate'
$engine.UpdateVariable('gblSaveBusy', $false)
$engine.UpdateVariable('gblSelectedObjectTypeKey', 'Change')
$engine.UpdateVariable('gblObjectType', 'Change')
Assert-Formula $newFormula 'Disabled' 'Stale provider selection'
Assert-Formula $saveFormula 'Disabled' 'Stale editor provider'
Assert-Formula $validityFormula $false 'Stale provider revalidate'
$engine.UpdateVariable('gblSelectedObjectTypeKey', '')
Assert-Formula $newFormula 'Disabled' 'No selection'
$engine.UpdateVariable('gblObjectType', 'Asset')
$engine.UpdateVariable('gblEditorMode', '')
Assert-Formula $saveFormula 'Disabled' 'No editor mode'
$engine.UpdateVariable('gblEditorMode', 'New')
$engine.UpdateVariable('colEditorValues', $engine.Eval('Table({IsValid: false, ControlType: "Text", EditorFieldKey: "Asset:Title", ValueChoiceKey: "", FieldInternalName: "Title", ValueText: "P0-SMOKE"})', $null, $options))
Assert-Formula $validityFormula $false 'Invalid required field'
$engine.UpdateVariable('colEditorValues', $engine.Eval('FirstN(Table({IsValid: true, ControlType: "Text", EditorFieldKey: "Asset:Title", ValueChoiceKey: "", FieldInternalName: "Title", ValueText: "P0-SMOKE"}), 0)', $null, $options))
Assert-Formula $validityFormula $false 'Empty editor'
$engine.UpdateVariable('gblEditorCanSave', $false)
Assert-Formula $saveFormula 'Disabled' 'Failed validation'
$engine.UpdateVariable('gblEditorCanSave', $true)
$engine.UpdateVariable('gblSelectedObjectTypeKey', 'Asset')
foreach ($title in @('', '   ', ('X' * 256))) {
    $engine.UpdateVariable('colEditorValues', $engine.Eval('Table({IsValid: true, ControlType: "Text", EditorFieldKey: "Asset:Title", ValueChoiceKey: "", FieldInternalName: "Title", ValueText: "' + $title + '"})', $null, $options))
    Assert-Formula $saveFormula 'Disabled' 'Invalid Asset Title with stale true eligibility'
    Assert-Formula $validityFormula $false 'Invalid Asset Title revalidation'
}
$engine.UpdateVariable('colEditorValues', $engine.Eval('Table({IsValid: true, ControlType: "Text", EditorFieldKey: "Asset:Title", ValueChoiceKey: "", FieldInternalName: "Description", ValueText: "A description"})', $null, $options))
Assert-Formula $saveFormula 'Disabled' 'Missing Asset Title metadata'
Assert-Formula $validityFormula $false 'Missing Asset Title revalidation'
$engine.UpdateVariable('gblEditorMode', 'Edit')
$engine.UpdateVariable('gblSelectedRecordId', 42)
Assert-Formula $saveFormula 'Disabled' 'Edit Asset must supply Title instead of stored-title fallback'
$engine.UpdateVariable('gblEditorMode', 'New')
$engine.UpdateVariable('gblSelectedRecordId', 0)
$engine.UpdateVariable('gblObjectType', 'System')
$engine.UpdateVariable('gblActiveProvider', $engine.Eval('{ObjectTypeKey: "System", SupportsCreate: true, SupportsEdit: true, SupportsSave: true}', $null, $options))
Assert-Formula $saveFormula 'Disabled' 'Missing System Title metadata also blocks save'
Assert-Formula $validityFormula $false 'Missing System Title revalidation'
$engine.UpdateVariable('colEditorValues', $engine.Eval('Table({IsValid: true, ControlType: "Text", EditorFieldKey: "System:Title", ValueChoiceKey: "", FieldInternalName: "Title", ValueText: "P1-SYSTEM"})', $null, $options))
Assert-Formula $saveFormula 'Edit' 'Valid System Title permits native save'
Assert-Formula $validityFormula $true 'Valid System Title revalidation'
$engine.UpdateVariable('gblObjectType', 'Asset')
$engine.UpdateVariable('gblActiveProvider', $engine.Eval('{ObjectTypeKey: "Asset", SupportsCreate: true, SupportsEdit: true, SupportsSave: true}', $null, $options))
$engine.UpdateVariable('colEditorValues', $engine.Eval('Table({IsValid: true, ControlType: "Text", EditorFieldKey: "Asset:Title", ValueChoiceKey: "", FieldInternalName: "Title", ValueText: "' + ('X' * 255) + '"})', $null, $options))
Assert-Formula $saveFormula 'Edit' 'Native Title accepts 255 characters'
Assert-Formula $validityFormula $true 'Native Title boundary revalidation'
$engine.UpdateVariable('colEditorValues', $engine.Eval('Table({IsValid: true, ControlType: "Text", EditorFieldKey: "Asset:Title", ValueChoiceKey: "", FieldInternalName: "Title", ValueText: "  P0-SMOKE  "})', $null, $options))
Assert-Formula $saveFormula 'Edit' 'Valid Asset Title'
Assert-Formula $validityFormula $true 'Valid Asset Title revalidation'
$titlePatch = [regex]::Match((Get-ControlProperty 'lblEditorSave' 'OnSelect'), '(?m)^\s*Title: (?<formula>Trim\([^\r\n]+)').Groups['formula'].Value.TrimEnd(',')
if (-not $titlePatch) { throw 'Asset Patch must use the validated Title without a fallback.' }
Assert-Formula $titlePatch 'P0-SMOKE' 'Actual Asset Patch trims the input Title'
# The full Save and revalidation expressions must reject unknown nonempty keys
# even when both cached eligibility and the field's IsValid flag are stale true.
foreach ($case in @(@('Criticality:High', 'Edit', $true), @('', 'Edit', $true), @('Criticality:Unknown', 'Disabled', $false))) {
    $rows = 'Table({IsValid: true, ControlType: "Text", EditorFieldKey: "Asset:Title", ValueChoiceKey: "", FieldInternalName: "Title", ValueText: "P0-SMOKE"}, {IsValid: true, ControlType: "Choice", EditorFieldKey: "Asset:Criticality", ValueChoiceKey: "'+$case[0]+'", FieldInternalName: "Criticality", ValueText: ""})'
    $engine.UpdateVariable('colEditorValues', $engine.Eval($rows, $null, $options))
    Assert-Formula $saveFormula $case[1] 'Full Save choice boundary with stale true eligibility'
    Assert-Formula $validityFormula $case[2] 'Full revalidation choice boundary with stale true field validity'
}
$engine.UpdateVariable('colEditorValues', $engine.Eval('Table({IsValid: true, ControlType: "Text", EditorFieldKey: "Asset:Title", ValueChoiceKey: "", FieldInternalName: "Title", ValueText: "P0-SMOKE"})', $null, $options))
$engine.UpdateVariable('gblShowDiscardDialog', $true)
Assert-Formula $newFormula 'Disabled' 'Discard modal prevents New'
Assert-Formula $saveFormula 'Disabled' 'Discard modal prevents Save'
$engine.UpdateVariable('gblShowDiscardDialog', $false)
$engine.UpdateVariable('gblActiveProvider', $engine.Eval('If(false, {ObjectTypeKey: "Asset", SupportsCreate: true, SupportsEdit: true, SupportsSave: true})', $null, $options))
Assert-Formula $newFormula 'Disabled' 'Missing provider'
Assert-Formula $saveFormula 'Disabled' 'Missing save provider'
# Hidden input instances share a gallery record but must never mutate it.
# Evaluate every real handler's guard independently of Canvas event simulation.
$engine.UpdateVariable('ThisItem', $engine.Eval('{EditorFieldKey: "Asset:Title", IsRequired: true, ValueText: "", ValueNumber: If(false, 0, Blank()), ValueDate: If(false, Now(), Blank()), ValueBoolean: false, ValueChoiceKey: "", ValueLookupId: If(false, 0, Blank()), ValuePersonClaims: "", ValuePersonEmail: ""}', $null, $options))
foreach ($control in 'txtEditorText', 'txtEditorMultiline', 'txtEditorNumber', 'datEditorDate', 'togEditorBoolean', 'drpEditorChoice', 'cmbEditorLookup', 'cmbEditorPerson') {
    $events = if ($control -eq 'togEditorBoolean') { @('OnCheck', 'OnUncheck') } else { @('OnChange') }
    foreach ($event in $events) {
        $handler = Get-ControlProperty $control $event
        $guard = [regex]::Match($handler, '^If\(\s*(?<guard>[^\r\n]+),').Groups['guard'].Value
        if (-not $guard) { throw "$control.$event must guard before any mutations." }
        $guard = $guard.Replace('Self.', 'testEditorControl.').Replace('DisplayMode.Edit', '"Edit"')
        foreach ($case in @(
            @{Visible=$true; Mode='Edit'; Expected=$true},
            @{Visible=$false; Mode='Edit'; Expected=$false},
            @{Visible=$true; Mode='Disabled'; Expected=$false},
            @{Visible=$true; Mode='View'; Expected=$false}
        )) {
            $visibleLiteral = ([string]$case.Visible).ToLowerInvariant()
            $engine.UpdateVariable('testEditorControl', $engine.Eval('{Visible: ' + $visibleLiteral + ', DisplayMode: "' + $case.Mode + '", Text: "12", Value: true, SelectedDate: Date(2026,10,2), Selected: {ChoiceKey: "Criticality:High"}, SelectedItems: Table({LookupId: 42, UserPrincipalName: "test@example.invalid", DisplayName: "Synthetic Test"})}', $null, $options))
            Assert-Formula $guard $case.Expected "$control.$event visibility/editability guard"
        }
    }
}
# Evaluate the actual text-input update record before the gallery mutation.
# Canvas host event/collection behavior still requires the DEV acceptance.
$textChange = Get-ControlProperty 'txtEditorText' 'OnChange'
$capturedInput = [regex]::Match($textChange, '(?s)With\(\s*(?<input>\{.*?\})\s*,\s*Patch\(').Groups['input'].Value.Replace('Self.Text', 'testTextInput.Text')
if (-not $capturedInput -or $textChange -notmatch 'LookUp\(colEditorValues, EditorFieldKey = editorKey\)') {
    throw 'Text input must capture its update record before patching the stable editor field key.'
}
$engine.UpdateVariable('ThisItem', $engine.Eval('{EditorFieldKey: "Asset:Title", IsRequired: true}', $null, $options))
foreach ($entry in @(
    @{Text=''; Valid=$false; Error='Pflichtfeld'},
    @{Text='   '; Valid=$false; Error='Pflichtfeld'},
    @{Text='DIAG'; Valid=$true; Error=''},
    @{Text='  P0-SMOKE  '; Valid=$true; Error=''}
)) {
    $engine.UpdateVariable('testTextInput', $engine.Eval('{Text: "' + $entry.Text + '"}', $null, $options))
    $inputFormula = 'With(' + $capturedInput + ', editorInput)'
    Assert-Formula ('(' + $inputFormula + ').ValueText') $entry.Text 'Text event preserves entered value'
    Assert-Formula ('(' + $inputFormula + ').IsValid') $entry.Valid 'Text event computes required validity'
    Assert-Formula ('(' + $inputFormula + ').ErrorMessage') $entry.Error 'Text event clears or sets required error'
    Assert-Formula ('(' + $inputFormula + ').IsDirty') $true 'Text event marks field dirty'
}
$engine.UpdateVariable('ThisItem', $engine.Eval('{EditorFieldKey: "Asset:AssetType", IsRequired: false}', $null, $options))
$engine.UpdateVariable('testTextInput', $engine.Eval('{Text: ""}', $null, $options))
Assert-Formula ('With(' + $capturedInput + ', editorInput.IsValid)') $true 'Optional text stays valid when empty'
Write-Host "Canvas capability expressions passed: $checks assertions; no tenant access."
