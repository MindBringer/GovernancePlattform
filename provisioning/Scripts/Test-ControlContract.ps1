[CmdletBinding()]
param([string]$NativeSnapshotPath)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$provisioning = Split-Path $PSScriptRoot -Parent
Import-Module (Join-Path $provisioning 'Modules/Model.psm1') -Force
Import-Module (Join-Path $provisioning 'Modules/Compiler.psm1') -Force
$model = Get-GPArchitectureModel -Root $provisioning
Test-GPArchitectureModel $model | Out-Null
$lists = (Compile-GPArchitecture $model).Lists
$controls = $lists | Where-Object ObjectKey -CEQ 'Control'
if ($controls.Title -cne 'Controls' -or !$controls.Settings.Versioning) {
    throw 'Controls requires the native list and version history.'
}
$types = [ordered]@{ GovernanceID = 'Text'; CorrelationID = 'Text'; Owner = 'User'; ControlType = 'Choice'; ControlStatus = 'Choice'; IsActive = 'Boolean' }
foreach ($name in $types.Keys) {
    $matches = @($controls.Fields | Where-Object InternalName -CEQ $name)
    if ($matches.Count -ne 1 -or $matches[0].Type -cne $types[$name]) {
        throw "Unexpected modeled Controls field type: $name."
    }
}
$status = $controls.Fields | Where-Object InternalName -CEQ 'ControlStatus'
if ($status.ChoiceSet -cne 'ControlStatus' -or 'Konzipiert' -cnotin $status.Choices) {
    throw 'The default native Control status is not in the ControlStatus choice set.'
}
$relationList = $lists | Where-Object Title -CEQ 'GovernanceRelations'
$key = $relationList.Fields | Where-Object InternalName -CEQ 'RelationKey'
if (!$key.Indexed -or !$key.EnforceUnique -or !$key.Required) {
    throw 'GovernanceRelations requires a mandatory indexed unique RelationKey.'
}

if ($NativeSnapshotPath) {
    $snapshot = Get-Content -LiteralPath $NativeSnapshotPath -Raw | ConvertFrom-Json -Depth 20
    if ($snapshot.state -cne 'verified' -or !$snapshot.lists.Controls.versioned) {
        throw 'Native Controls version history was not confirmed.'
    }
    $native = $snapshot.lists.Controls
    foreach ($name in $types.Keys) {
        $matches = @($native.fields | Where-Object name -CEQ $name)
        if ($matches.Count -ne 1 -or $matches[0].type -cne $types[$name] -or $matches[0].readOnly) {
            throw "Unexpected native Controls field type or writability: $name."
        }
    }
    $nativeStatus = $native.fields | Where-Object name -CEQ 'ControlStatus'
    if (($nativeStatus.choices -join '|') -cne ($status.Choices -join '|')) {
        throw 'The native ControlStatus options differ from the architecture.'
    }
    $correlation = $native.fields | Where-Object name -CEQ 'CorrelationID'
    if (!$correlation.indexed) {
        throw 'The native Control receipt lookup requires an indexed CorrelationID.'
    }
    $nativeKey = $snapshot.lists.GovernanceRelations.fields | Where-Object name -CEQ 'RelationKey'
    if ($nativeKey.type -cne 'Text' -or !$nativeKey.indexed -or !$nativeKey.unique -or !$nativeKey.required) {
        throw 'The native relation key is not mandatory, indexed and unique.'
    }
}
Write-Host 'Controls schema, ownership, native choices and unique relation contract verified.'
