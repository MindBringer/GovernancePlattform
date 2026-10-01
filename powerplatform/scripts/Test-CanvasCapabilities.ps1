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
$writableTypes = @('Asset', 'System')
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
$engine.UpdateVariable('gblEditorCanSave', $true)
$engine.UpdateVariable('colEditorValues', $engine.Eval('Table({IsValid: true})', $null, $options))

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
$engine.UpdateVariable('colEditorValues', $engine.Eval('Table({IsValid: false})', $null, $options))
Assert-Formula $validityFormula $false 'Invalid required field'
$engine.UpdateVariable('colEditorValues', $engine.Eval('FirstN(Table({IsValid: true}), 0)', $null, $options))
Assert-Formula $validityFormula $false 'Empty editor'
$engine.UpdateVariable('gblEditorCanSave', $false)
Assert-Formula $saveFormula 'Disabled' 'Failed validation'
$engine.UpdateVariable('gblEditorCanSave', $true)
$engine.UpdateVariable('gblSelectedObjectTypeKey', 'Asset')
$engine.UpdateVariable('gblActiveProvider', $engine.Eval('If(false, {ObjectTypeKey: "Asset", SupportsCreate: true, SupportsEdit: true, SupportsSave: true})', $null, $options))
Assert-Formula $newFormula 'Disabled' 'Missing provider'
Assert-Formula $saveFormula 'Disabled' 'Missing save provider'
Write-Host "Canvas capability expressions passed: $checks assertions; no tenant access."
