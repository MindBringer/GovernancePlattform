[CmdletBinding()]
param([string]$PlanPath)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Import-Module "$root/provisioning/Modules/Model.psm1" -Force
Import-Module "$root/provisioning/Modules/Compiler.psm1" -Force
$model = Get-GPArchitectureModel -Root "$root/provisioning"
$baseline = Get-GPArchitectureModel -Root "$root/provisioning"
$baseline.ObjectFields = @($baseline.ObjectFields | Where-Object { -not ($_.objectTypeKey -eq 'System' -and $_.internalName -eq 'SystemDescription') })
$schema = Compile-GPArchitecture $model
$oldSchema = Compile-GPArchitecture $baseline
$system = @($schema.Lists | Where-Object ObjectKey -eq 'System')[0]
$field = @($system.Fields | Where-Object InternalName -eq 'SystemDescription')
if ($field.Count -ne 1 -or $field[0].Type -ne 'Note' -or $field[0].DisplayName -ne 'Beschreibung' -or $field[0].Required -or $field[0].Indexed) {
    throw 'Expected one optional plain SystemDescription Note field, displayed as Beschreibung.'
}
foreach ($oldList in $oldSchema.Lists) {
    $current = @($schema.Lists | Where-Object ObjectKey -eq $oldList.ObjectKey)[0]
    $expectedCount = $oldList.Fields.Count + $(if ($oldList.ObjectKey -eq 'System') { 1 } else { 0 })
    if ($current.Fields.Count -ne $expectedCount) { throw "Unexpected schema delta: $($oldList.Title)" }
    foreach ($oldField in $oldList.Fields) {
        $actual = @($current.Fields | Where-Object InternalName -eq $oldField.InternalName)
        if ($actual.Count -ne 1 -or ($actual[0] | ConvertTo-Json -Depth 20) -cne ($oldField | ConvertTo-Json -Depth 20)) { throw "Existing field changed: $($oldList.Title).$($oldField.InternalName)" }
    }
}
# Exercise the real metadata/XML generators with the write boundary replaced.
# No PnP import, authentication, remote read, provisioning or metadata write.
$metadata = Import-Module "$root/provisioning/Modules/Metadata.psm1" -Force -PassThru
$schemaModule = Import-Module "$root/provisioning/Modules/Schema.psm1" -Force -PassThru
$oldContext = Get-Variable GPContext -Scope Global -ErrorAction SilentlyContinue
try {
    $global:GPContext = @{DryRun=$true; FieldGroup=$model.site.fieldGroup}
    & $metadata {
        function script:Write-GPLog { param($Message, $Level) }
        function script:Set-GPSeedRow {
            param([string]$List, [string]$KeyField, [hashtable]$Values)
            $script:CapturedRows.Add([pscustomobject]@{List=$List; KeyField=$KeyField; Values=$Values})
        }
    }
    function Get-GeneratedRows($Architecture) {
        & $metadata {
            param($Architecture)
            $script:CapturedRows = [System.Collections.Generic.List[object]]::new()
            Publish-GPMetadata -Model $Architecture
            $script:CapturedRows.ToArray()
        } $Architecture
    }
    $rows = @(Get-GeneratedRows $model)
    $oldRows = @(Get-GeneratedRows $baseline)
    $delta = @($rows | Where-Object { $_.List -in @('FieldDefinitions','FormFieldDefinitions') -and $_.Values.ObjectTypeKey -eq 'System' -and $_.Values.FieldInternalName -eq 'SystemDescription' })
    if ($delta.Count -ne 2 -or $rows.Count -ne $oldRows.Count + 2) { throw 'Expected exactly two additional SystemDescription metadata rows.' }
    $existing = @{}
    foreach ($row in $rows) { $existing[$row.List + '/' + $row.Values[$row.KeyField]] = $row.Values }
    foreach ($row in $oldRows) {
        $key = $row.List + '/' + $row.Values[$row.KeyField]
        $actual = $existing[$key]
        if ($null -eq $actual -or $actual.Count -ne $row.Values.Count) { throw "Unexpected metadata delta: $key" }
        foreach ($property in $row.Values.Keys) {
            if ([string]$actual[$property] -cne [string]$row.Values[$property]) { throw "Existing metadata changed: $key.$property" }
        }
    }
    $definition = ($delta | Where-Object List -eq 'FieldDefinitions').Values
    $form = ($delta | Where-Object List -eq 'FormFieldDefinitions').Values
    if ($definition.IsReadOnly -or $definition.IsRequired -or $definition.ControlType -ne 'Note' -or $definition.FieldDefinitionKey -ne 'System:SystemDescription' -or $form.FormFieldDefinitionKey -ne 'System:Edit:SystemDescription') { throw 'Invalid writable description metadata contract.' }
    $xml = & $schemaModule { param($Field) New-GPFieldXml -F $Field } $field[0]
    [xml]$parsed = $xml
    if ($parsed.Field.Name -ne 'SystemDescription' -or $parsed.Field.Type -ne 'Note' -or $parsed.Field.RichText -ne 'FALSE' -or $parsed.Field.HasAttribute('ReadOnly') -or $parsed.Field.HasAttribute('Sealed')) { throw 'New description XML must not reuse or unseal the native Description field.' }
    if ($PlanPath) {
        [ordered]@{
            status='prepared-not-authorized'; sourceList=$system.Title
            addField=[ordered]@{InternalName=$field[0].InternalName; Type=$field[0].Type; DisplayName=$field[0].DisplayName; Xml=$xml}
            metadataRows=$delta
            existingMetadataRowsUnchanged=$oldRows.Count
            existingNativeDescription='retain sealed/read-only; no permission change, rename, deletion or data overwrite'
            connectorPrerequisite='native field readback and generated Systems connector reference refresh; separate DEV-to-Git approval'
        } | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $PlanPath -Encoding utf8
    }
    Write-Host "System description contract passed: one additional Systems Note column / two metadata rows; $($oldRows.Count) existing metadata rows and every existing schema field unchanged; no tenant access."
} finally {
    if ($oldContext) { $global:GPContext = $oldContext.Value }
    else { Remove-Variable GPContext -Scope Global -ErrorAction SilentlyContinue }
    Remove-Module $metadata
    Remove-Module $schemaModule
}
