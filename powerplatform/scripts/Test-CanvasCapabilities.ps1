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
$config = [Microsoft.PowerFx.PowerFxConfig]::new()
[Microsoft.PowerFx.PowerFxConfigExtensions]::EnableRegExFunctions($config, [TimeSpan]::FromSeconds(2), 100)
$engine = [Microsoft.PowerFx.RecalcEngine]::new($config)
$engine.UpdateVariable('gblAssetPilotEnabled', $false)
$engine.UpdateVariable('gblWorkspaceEnabled', $false)
$engine.UpdateVariable('gblAssetPilotCanWrite', $false)
$engine.UpdateVariable('lblAssetValidation', $engine.Eval('{Text: ""}', $null, $null))
# Provider-only fixture; the real Change invariant is executed in its own gate.
$engine.UpdateVariable('lblChangeValidation', $engine.Eval('{Text: ""}', $null, $null))
# Non-Risk fixtures bind the inactive branch; actual Risk invariants run in Test-CanvasRiskContract.
$riskFixtureOptions=[Microsoft.PowerFx.ParserOptions]::new();$riskFixtureOptions.Culture=[Globalization.CultureInfo]::InvariantCulture
$engine.UpdateVariable('lblRiskValidation', $engine.Eval('{Text: ""}', $null, $riskFixtureOptions))
$engine.UpdateVariable('gblRiskOriginalStatusKey', '')
$engine.UpdateVariable('colRiskTransitions', $engine.Eval('Table({FromKey: "", ToKey: ""})', $null, $riskFixtureOptions))
$engine.UpdateVariable('lblRiskMessage', $engine.Eval('{Visible: false, Y: 56, Height: 44}', $null, $riskFixtureOptions))
$engine.UpdateVariable('btnRiskAccept', $engine.Eval('{Visible: false, Y: 56, Height: 34}', $null, $riskFixtureOptions))
$options = [Microsoft.PowerFx.ParserOptions]::new()
$options.Culture = [System.Globalization.CultureInfo]::InvariantCulture
$engine.UpdateVariable('gblPilotObjectRoutes', $engine.Eval('Table({NavigationKey: "NavGovernance", ObjectTypeKey: "Asset", RequiresExtendedAccess: false})', $null, $options))
$source = Get-Content (Join-Path $RepositoryRoot 'powerplatform/canvas/GovernancePortal/Src/scrShell.pa.yaml') -Raw
$appSource = Get-Content (Join-Path $RepositoryRoot 'powerplatform/canvas/GovernancePortal/Src/App.pa.yaml') -Raw

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
$assetValidation = Get-ControlProperty 'lblAssetValidation' 'Text'
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
$writableTypes = @('Asset', 'System', 'Change', 'Risk')
$checks = 0
function Assert-Formula([string]$Formula, $Expected, [string]$Context) {
    $actual = $engine.Eval($Formula, $null, $options).ToObject()
    if ($actual -ne $Expected) { throw "${Context}: expected '$Expected', got '$actual'." }
    $script:checks++
}

$editorSetting = 'Runtime.AssetPilotEditorEntraObjectId'
$editorId = '01234567-89ab-4cde-8f01-23456789abcd'
$otherId = '12345678-9abc-4def-8012-3456789abcde'
$roleFormula = [regex]::Match($appSource, '(?ms)Set\(\s*gblAssetPilotCanWrite,\s*(?<formula>.*?)\r?\n {6}\);').Groups['formula'].Value
if (!$roleFormula) { throw 'Missing the Asset pilot editor role formula.' }
$engine.UpdateVariable('gblAssetPilotEditorSettingKey', $editorSetting)
$engine.UpdateVariable('gblAssetPilotEnabled', $true)
$engine.UpdateVariable('gblDataError', $false)
$editorRow = '{SettingKey: "' + $editorSetting + '", SettingValue: " ' + $editorId.ToUpperInvariant() + ' "}'
$editorRows = $engine.Eval("Table($editorRow)", $null, $options)
$engine.UpdateVariable('colAppSettings', $editorRows)
$engine.UpdateVariable('gblUser', $engine.Eval('{EntraObjectId: GUID("' + $editorId + '")}', $null, $options))
Assert-Formula $roleFormula $true 'An exact Entra ID and one setting allow the pilot editor'
$engine.UpdateVariable('gblUser', $engine.Eval('{EntraObjectId: GUID("' + $otherId + '")}', $null, $options))
Assert-Formula $roleFormula $false 'A different Entra ID remains read-only'
$engine.UpdateVariable('gblUser', $engine.Eval('{EntraObjectId: GUID("' + $editorId + '")}', $null, $options))
$engine.UpdateVariable('colAppSettings', $engine.Eval("FirstN(Table($editorRow), 0)", $null, $options))
Assert-Formula $roleFormula $false 'A missing setting leaves the pilot read-only'
$engine.UpdateVariable('colAppSettings', $engine.Eval("Table($editorRow, $editorRow)", $null, $options))
Assert-Formula $roleFormula $false 'Duplicate settings leave the pilot read-only'
$engine.UpdateVariable('colAppSettings', $editorRows)
$engine.UpdateVariable('gblDataError', $true)
Assert-Formula $roleFormula $false 'Runtime read errors leave the pilot read-only'
$engine.UpdateVariable('gblDataError', $false)
$engine.UpdateVariable('gblAssetPilotEnabled', $false)

$extendedKey = 'Runtime.ExtendedPilotEntraObjectIds'
$accessFormula = [regex]::Match($appSource, '(?ms)Set\(\s*gblPilotHasExtendedAccess,\s*(?<formula>.*?)\r?\n {6}\);').Groups['formula'].Value
$routeFormula = [regex]::Match($appSource, '(?ms)Set\(\s*gblPilotObjectRoutes,\s*(?<formula>.*?)\r?\n {6}\);').Groups['formula'].Value
$configuredRoutes = [regex]::Match($appSource, '(?ms)Set\(\s*gblPilotConfiguredRoutes,\s*(?<formula>.*?)\r?\n {6}\);').Groups['formula'].Value
if (!$accessFormula -or !$routeFormula -or !$configuredRoutes) { throw 'Missing extended pilot routing expressions.' }
$engine.UpdateVariable('gblPilotExtendedAccessSettingKey', $extendedKey)
$accessRow = '{SettingKey: "' + $extendedKey + '", SettingValue: " ' + $editorId.ToUpperInvariant() + ', ' + $otherId + ' "}'
$engine.UpdateVariable('colAppSettings', $engine.Eval("Table($editorRow, $accessRow)", $null, $options))
Assert-Formula $accessFormula $true 'An explicitly assigned editor sees the extended pilot'
$engine.UpdateVariable('gblUser', $engine.Eval('{EntraObjectId: GUID("' + $otherId + '")}', $null, $options))
Assert-Formula $accessFormula $true 'An explicitly assigned reader sees the extended pilot'
$engine.UpdateVariable('gblAssetPilotEnabled', $true)
Assert-Formula $roleFormula $false 'Extended navigation never grants the editor role'
$engine.UpdateVariable('gblAssetPilotEnabled', $false)
$unassignedId = '01234567-89ab-4cde-8f01-23456789abce'
$engine.UpdateVariable('gblUser', $engine.Eval('{EntraObjectId: GUID("' + $unassignedId + '")}', $null, $options))
Assert-Formula $accessFormula $false 'Assignment requires exact identity'
$engine.UpdateVariable('gblUser', $engine.Eval('{EntraObjectId: GUID("' + $otherId + '")}', $null, $options))
$engine.UpdateVariable('colAppSettings', $editorRows)
Assert-Formula $accessFormula $false 'Missing assignment leaves only the base pilot'
$engine.UpdateVariable('colAppSettings', $engine.Eval("Table($accessRow, $accessRow)", $null, $options))
Assert-Formula $accessFormula $false 'Duplicate settings leave only the base pilot'
$engine.UpdateVariable('colAppSettings', $engine.Eval("Table($accessRow)", $null, $options))
$engine.UpdateVariable('gblDataError', $true)
Assert-Formula $accessFormula $false 'Settings read failure leaves only the base pilot'
$engine.UpdateVariable('gblDataError', $false)
# Workspace navigation is available to authenticated readers without changing save eligibility.
$engine.UpdateVariable('gblWorkspaceEnabled', $true)
$engine.UpdateVariable('colAppSettings', $editorRows)
Assert-Formula $accessFormula $true 'Workspace readers see implemented routes without a pilot allowlist'
$engine.UpdateVariable('gblAssetPilotEnabled', $true)
Assert-Formula $roleFormula $false 'Workspace visibility grants no write role to the reader'
$engine.UpdateVariable('gblDataError', $true)
Assert-Formula $accessFormula $false 'Workspace does not bypass runtime load failures'
$engine.UpdateVariable('gblDataError', $false)
$engine.UpdateVariable('gblUser', $engine.Eval('{EntraObjectId: Blank()}', $null, $options))
Assert-Formula $accessFormula $false 'Workspace does not grant routes to a missing identity'
$engine.UpdateVariable('gblUser', $engine.Eval('{EntraObjectId: GUID("' + $otherId + '")}', $null, $options))
$engine.UpdateVariable('gblWorkspaceEnabled', $false)
$engine.UpdateVariable('gblAssetPilotEnabled', $false)

$siteFormula = [regex]::Match($appSource, '(?ms)Set\(\s*gblWorkspaceSiteUrl,\s*(?<formula>.*?)\r?\n {6}\);').Groups['formula'].Value
if (!$siteFormula) { throw 'Missing workspace site URL validation.' }
$engine.UpdateVariable('gblWorkspaceSiteSettingKey', 'Runtime.SharePointSiteUrl')
foreach ($siteCase in @(
    @{ Value = 'https://example.sharepoint.com/sites/Pilot'; Expected = 'https://example.sharepoint.com/sites/Pilot' },
    @{ Value = 'https://example.sharepoint.com/teams/Pilot/'; Expected = 'https://example.sharepoint.com/teams/Pilot/' },
    @{ Value = 'https://example.sharepoint.com.evil.test/sites/Pilot'; Expected = '' },
    @{ Value = 'javascript:alert(1)'; Expected = '' },
    @{ Value = 'https://example.sharepoint.com/sites/Pilot?redirect=other'; Expected = '' },
    @{ Value = ''; Expected = '' }
)) {
    $siteRow = '{SettingKey: "Runtime.SharePointSiteUrl", SettingValue: "' + $siteCase.Value + '"}'
    $engine.UpdateVariable('colAppSettings', $engine.Eval("Table($siteRow)", $null, $options))
    Assert-Formula $siteFormula $siteCase.Expected 'Workspace links require an exact SharePoint site URL'
}
$engine.UpdateVariable('colAppSettings', $engine.Eval('Table({SettingKey: "Runtime.SharePointSiteUrl", SettingValue: "https://example.sharepoint.com/sites/Pilot"}, {SettingKey: "Runtime.SharePointSiteUrl", SettingValue: "https://example.sharepoint.com/sites/Other"})', $null, $options))
Assert-Formula $siteFormula '' 'Ambiguous site settings disable native links'
$engine.UpdateVariable('colAppSettings', $editorRows)

$engine.UpdateVariable('gblPilotConfiguredRoutes', $engine.Eval($configuredRoutes, $null, $options))
$availableObjects = 'Table({ObjectTypeKey: "Asset"}, {ObjectTypeKey: "System"}, {ObjectTypeKey: "Change"}, {ObjectTypeKey: "Risk"}, {ObjectTypeKey: "Evidence"})'
$engine.UpdateVariable('colObjectTypes', $engine.Eval($availableObjects, $null, $options))
$engine.UpdateVariable('gblPilotHasExtendedAccess', $false)
Assert-Formula ('Concat(' + $routeFormula + ', ObjectTypeKey, ",")') 'Asset' 'Base pilot exposes only Assets'
$engine.UpdateVariable('gblPilotHasExtendedAccess', $true)
Assert-Formula ('Concat(' + $routeFormula + ', ObjectTypeKey, ",")') 'Asset,System,Change,Risk' 'Extended pilot exposes only implemented configured providers'
$engine.UpdateVariable('colObjectTypes', $engine.Eval('Filter(' + $availableObjects + ', ObjectTypeKey <> "Risk")', $null, $options))
Assert-Formula ('Concat(' + $routeFormula + ', ObjectTypeKey, ",")') 'Asset,System,Change' 'A missing object definition suppresses its route'
$engine.UpdateVariable('colObjectTypes', $engine.Eval($availableObjects, $null, $options))

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

$engine.UpdateVariable('gblAssetPilotEnabled', $true)
foreach ($extended in @($false, $true)) {
    $engine.UpdateVariable('gblPilotHasExtendedAccess', $extended)
    $engine.UpdateVariable('gblPilotObjectRoutes', $engine.Eval($routeFormula, $null, $options))
    $items = Get-ControlProperty 'galObjectTypes' 'Items'
    foreach ($route in @(
        @{ Name = 'NavGovernance'; Default = 'Asset'; Extended = 'Asset,System' },
        @{ Name = 'NavOperations'; Default = ''; Extended = 'Change' },
        @{ Name = 'NavRisk'; Default = ''; Extended = 'Risk' }
    )) {
        $engine.UpdateVariable('gblCurrentNavigationKey', $route.Name)
        $expectedItems = if ($extended) { $route.Extended } else { $route.Default }
        Assert-Formula ('Concat(' + $items + ', ObjectTypeKey, ",")') $expectedItems "$($route.Name) object gallery expanded=$extended"
    }
    foreach ($provider in $providers) {
        $key = [string]$provider.objectTypeKey
        $engine.UpdateVariable('gblSelectedObjectTypeKey', $key)
        $engine.UpdateVariable('gblObjectType', $key)
        $engine.UpdateVariable('gblActiveProvider', $engine.Eval(
            '{ObjectTypeKey: "' + $key + '", SupportsCreate: ' + $provider.supportsCreate.ToString().ToLowerInvariant() + ', SupportsEdit: ' + $provider.supportsEdit.ToString().ToLowerInvariant() + ', SupportsSave: ' + $provider.supportsSave.ToString().ToLowerInvariant() + '}',
            $null, $options))
        foreach ($canWrite in @($false, $true)) {
            $engine.UpdateVariable('gblAssetPilotCanWrite', $canWrite)
            $allowed = $canWrite -and ($key -ceq 'Asset' -or ($extended -and $key -in $writableTypes))
            $expected = if ($allowed) { 'Edit' } else { 'Disabled' }
            $engine.UpdateVariable('gblEditorMode', 'New')
            Assert-Formula $newFormula $expected "$key pilot create with editor=$canWrite expanded=$extended"
            Assert-Formula $saveFormula $expected "$key pilot save new with editor=$canWrite expanded=$extended"
            Assert-Formula $validityFormula $allowed "$key pilot revalidate with editor=$canWrite expanded=$extended"
            $engine.UpdateVariable('gblEditorMode', 'Edit')
            $engine.UpdateVariable('gblSelectedRecordId', 42)
            Assert-Formula $saveFormula $expected "$key pilot update with editor=$canWrite expanded=$extended"
        }
    }
}
$engine.UpdateVariable('gblAssetPilotEnabled', $false)
$engine.UpdateVariable('gblAssetPilotCanWrite', $false)
$engine.UpdateVariable('gblSelectedRecordId', 0)

$engine.UpdateVariable('gblAssetPilotEnabled', $true)
$engine.UpdateVariable('gblCurrentPage', 'editor')
$engine.UpdateVariable('gblChangeOriginalStatusKey', 'ChangeStatus:Submitted')
$engine.UpdateVariable('gblRiskOriginalStatusKey', 'RiskStatus:Assessed')
foreach ($item in @(@('Change','btnChangeApprove'), @('Risk','btnRiskAccept'))) {
    $engine.UpdateVariable('gblObjectType', $item[0])
    $visibility = Get-ControlProperty $item[1] 'Visible'
    Assert-Formula $visibility $false "$($item[0]) decision hidden for extended reader"
    $engine.UpdateVariable('gblAssetPilotCanWrite', $true)
    Assert-Formula $visibility $true "$($item[0]) decision visible in extended writer context"
    $engine.UpdateVariable('gblAssetPilotCanWrite', $false)
}
$engine.UpdateVariable('gblAssetPilotEnabled', $false)
$engine.UpdateVariable('gblCurrentPage', 'ObjectList')

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
$fixtureEditor = $engine
# Use a separate engine for the review tests: the provider-only fixtures above
# intentionally omit ValueNumber and the interpreter retains each symbol's type.
$engine = [Microsoft.PowerFx.RecalcEngine]::new()
foreach ($name in @('gblSelectedObjectTypeKey', 'gblObjectType',
        'gblCurrentPage', 'gblEditorLoadComplete', 'gblEditorDirty', 'gblLoadedRecordId', 'gblEditorConflict',
        'gblShowDiscardDialog', 'gblEditorCanSave', 'gblSaveBusy', 'gblLoadBusy', 'colEditorChoiceOptions',
        'lblChangeValidation', 'lblRiskValidation')) {
    $engine.UpdateVariable($name, $fixtureEditor.Eval($name, $null, $options))
}
$engine.UpdateVariable('gblAssetPilotEnabled', $true)
$engine.UpdateVariable('gblAssetPilotCanWrite', $true)
$engine.UpdateVariable('gblPilotObjectRoutes', $engine.Eval('Table({ObjectTypeKey: "Asset"})', $null, $options))
$engine.UpdateVariable('gblActiveProvider', $engine.Eval('{ObjectTypeKey: "Asset", SupportsCreate: true, SupportsEdit: true, SupportsSave: true}', $null, $options))
$cycleBounds = @((Get-Content (Join-Path $RepositoryRoot 'architecture/fields.yaml') -Raw | ConvertFrom-Json).fields |
    Where-Object internalName -CEQ 'ReviewCycleMonths')
if ($cycleBounds.Count -ne 1) { throw 'Expected one canonical Asset review cycle.' }
foreach ($bound in @(@('Min', 'min'), @('Max', 'max'))) {
    $variable = 'gblAssetReviewCycle' + $bound[0]
    $generated = [regex]::Match($appSource, ('Set\(' + $variable + ',\s*(\d+)\);'))
    if (!$generated.Success -or [int]$generated.Groups[1].Value -ne $cycleBounds[0].($bound[1])) {
        throw "Generated Asset review cycle bound differs from architecture: $variable."
    }
    $engine.UpdateVariable($variable, [double]$generated.Groups[1].Value)
}
$cycleMin = $cycleBounds[0].min
$cycleMax = $cycleBounds[0].max
foreach ($mode in @('New', 'Edit')) {
    $engine.UpdateVariable('gblEditorMode', $mode)
    $engine.UpdateVariable('gblSelectedRecordId', $(if ($mode -eq 'Edit') { 42 } else { 0 }))
    foreach ($case in @(
        @{ Value = 'If(false, 0, Blank())'; Allowed = $true },
        @{ Value = [string]($cycleMin - 1); Allowed = $false },
        @{ Value = [string]$cycleMin; Allowed = $true },
        @{ Value = [string]$cycleMax; Allowed = $true },
        @{ Value = [string]($cycleMax + 1); Allowed = $false }
    )) {
        $rows = 'Table({IsValid: true, ControlType: "Text", EditorFieldKey: "Asset:Title", ValueChoiceKey: "", FieldInternalName: "Title", ValueText: "P7-CYCLE", ValueNumber: If(false, 0, Blank())}, {IsValid: true, ControlType: "Number", EditorFieldKey: "Asset:ReviewCycleMonths", ValueChoiceKey: "", FieldInternalName: "ReviewCycleMonths", ValueText: "", ValueNumber: ' + $case.Value + '})'
        $engine.UpdateVariable('colEditorValues', $engine.Eval($rows, $null, $options))
        $engine.UpdateVariable('lblAssetValidation', $engine.Eval('{Text: ' + $assetValidation + '}', $null, $options))
        $expected = if ($case.Allowed) { 'Edit' } else { 'Disabled' }
        Assert-Formula $saveFormula $expected "$mode Asset review cycle $($case.Value) with stale true eligibility"
        Assert-Formula $validityFormula $case.Allowed "$mode Asset review cycle $($case.Value) revalidation"
        if (!$case.Allowed) {
            Assert-Formula 'lblAssetValidation.Text' "Der Reviewzyklus muss zwischen $cycleMin und $cycleMax Monaten liegen." 'Invalid review cycle explains the permitted range'
        }
    }
}
$engine.UpdateVariable('gblObjectType', 'System')
Assert-Formula $assetValidation '' 'Asset review-cycle validation does not affect another provider'
$engine = $fixtureEditor
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
