[CmdletBinding()]
param([string]$NativeSnapshotPath)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$provisioning = Split-Path $PSScriptRoot -Parent
Import-Module (Join-Path $provisioning 'Modules/Model.psm1') -Force
Import-Module (Join-Path $provisioning 'Modules/Compiler.psm1') -Force
$model = Get-GPArchitectureModel -Root $provisioning
Test-GPArchitectureModel $model | Out-Null
$measures = (Compile-GPArchitecture $model).Lists | Where-Object ObjectKey -CEQ 'Measure'
if ($measures.Title -cne 'Measures' -or !$measures.Settings.Versioning) {
    throw 'Measures requires the native list and version history.'
}
$types = [ordered]@{
    Title = 'Text'; Owner = 'User'; DueDate = 'DateTime'; MeasureStatus = 'Choice'
    CorrelationID = 'Text'; IsActive = 'Boolean'
    EffectivenessValidationDate = 'DateTime'; EffectivenessValidationResult = 'Note'
}
foreach ($name in ($types.Keys | Where-Object { $_ -cne 'Title' })) {
    $matches = @($measures.Fields | Where-Object InternalName -CEQ $name)
    if ($matches.Count -ne 1 -or $matches[0].Type -cne $types[$name]) {
        throw "Unexpected modeled Measures field: $name."
    }
}
$root = Split-Path $provisioning -Parent
$statusModels = (Get-Content (Join-Path $root 'architecture/status-models.yaml') -Raw | ConvertFrom-Json -Depth 12).statusModels
$states = ($statusModels | Where-Object key -CEQ 'Measure').states
$labels = $states | ForEach-Object { $_[1] }
$status = $measures.Fields | Where-Object InternalName -CEQ 'MeasureStatus'
if ($status.ChoiceSet -cne 'MeasureStatus' -or !$status.Indexed -or $status.Required -or
    ($status.Choices -join '|') -cne ($labels -join '|')) {
    throw 'The optional indexed SharePoint MeasureStatus choices must match the lifecycle.'
}

if ($NativeSnapshotPath) {
    $snapshot = Get-Content -LiteralPath $NativeSnapshotPath -Raw | ConvertFrom-Json -Depth 20
    if ($snapshot.state -cne 'verified' -or !$snapshot.lists.Measures.versioned) {
        throw 'Native Measures version history was not confirmed.'
    }
    $native = $snapshot.lists.Measures
    foreach ($name in $types.Keys) {
        $matches = @($native.fields | Where-Object name -CEQ $name)
        if ($matches.Count -ne 1 -or $matches[0].type -cne $types[$name] -or $matches[0].readOnly) {
            throw "Unexpected native Measures field type or writability: $name."
        }
    }
    foreach ($name in @('DueDate', 'EffectivenessValidationDate')) {
        $dateField = $native.fields | Where-Object name -CEQ $name
        if ($dateField.format -cne 'DateOnly') { throw "Native $name must be DateOnly." }
    }
    $nativeStatus = $native.fields | Where-Object name -CEQ 'MeasureStatus'
    $requestCode = $native.fields | Where-Object name -CEQ 'CorrelationID'
    if ($nativeStatus.Required -or !$nativeStatus.Indexed -or $nativeStatus.Unique -or !$requestCode.Indexed -or
        ($nativeStatus.choices -join '|') -cne ($labels -join '|')) {
        throw 'Native status options or request-code index differ from the measure contract.'
    }
    $relationKey = $snapshot.lists.GovernanceRelations.fields | Where-Object name -CEQ 'RelationKey'
    if (!$relationKey.Indexed -or !$relationKey.Unique -or !$relationKey.Required) {
        throw 'Native relations require the mandatory indexed unique key.'
    }
    foreach ($listName in @('Measures', 'Controls', 'Evidence', 'GovernanceRelations')) {
        $list = $snapshot.lists.$listName
        if (!$list.reader.read -or $list.reader.add -or $list.reader.edit -or !$list.editor.read) {
            throw "Native reader or editor permissions differ on $listName."
        }
    }
    if (!$native.editor.add -or !$native.editor.edit -or !$snapshot.lists.GovernanceRelations.editor.add) {
        throw 'The pilot editor requires create and edit on Measures and create on GovernanceRelations.'
    }
}
Write-Host 'Measures schema, version history, lifecycle choices and relation contract verified.'
