[CmdletBinding()]
param([string]$PlanPath, [ValidateSet("Asset","System")][string]$ObjectType = "Asset")

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Import-Module "$root/provisioning/Modules/Model.psm1" -Force
Import-Module "$root/provisioning/Modules/Compiler.psm1" -Force
$model = Get-GPArchitectureModel -Root "$root/provisioning"
$schema = Compile-GPArchitecture $model
$title = @(($schema.Lists | Where-Object ObjectKey -eq $ObjectType).Fields | Where-Object InternalName -eq 'Title')
if ($title.Count -ne 1 -or $title[0].Type -ne 'Text' -or -not $title[0].Required -or $title[0].maxLength -ne 255) {
    throw "$ObjectType must resolve exactly one required native Title (Text, maxLength 255)."
}

# Run the actual generator in an isolated module instance, replacing its sole
# metadata-write boundary. No PnP import, auth, remote read or tenant write.
$metadata = Import-Module "$root/provisioning/Modules/Metadata.psm1" -Force -PassThru
try {
    & $metadata {
        function script:Write-GPLog { param($Message, $Level) }
        function script:Set-GPSeedRow {
            param([string]$List, [string]$KeyField, [hashtable]$Values)
            $script:CapturedRows.Add([pscustomobject]@{List=$List; KeyField=$KeyField; Values=$Values})
        }
    }
    function Get-GeneratedRows($Model) {
        & $metadata {
            param($Architecture)
            $script:CapturedRows = [System.Collections.Generic.List[object]]::new()
            Publish-GPMetadata -Model $Architecture
            return $script:CapturedRows.ToArray()
        } $Model
    }
    # The generator's final diagnostics use global context, even with a stubbed
    # write boundary. Keep that environment absent by supplying a temporary value.
    $oldContext = Get-Variable GPContext -Scope Global -ErrorAction SilentlyContinue
    $global:GPContext = @{DryRun=$true}
    $rows = @(Get-GeneratedRows $model)
    $baseline = Get-GPArchitectureModel -Root "$root/provisioning"
    $baseline.ObjectFields = @($baseline.ObjectFields | Where-Object { -not ($_.objectTypeKey -eq $ObjectType -and $_.internalName -eq 'Title') })
    $oldRows = @(Get-GeneratedRows $baseline)
    $delta = @($rows | Where-Object { $_.List -in @('FieldDefinitions','FormFieldDefinitions') -and $_.Values.ObjectTypeKey -eq $ObjectType -and $_.Values.FieldInternalName -eq 'Title' })
    if ($delta.Count -ne 2 -or $rows.Count -ne ($oldRows.Count + 2)) { throw 'Expected exactly two additional metadata rows.' }
    $existing = @{}
    foreach ($row in $rows) { $existing[$row.List + '/' + $row.Values[$row.KeyField]] = $row.Values }
    foreach ($row in $oldRows) {
        $key = $row.List + '/' + $row.Values[$row.KeyField]
        $actual = $existing[$key]
        if ($null -eq $actual -or $actual.Count -ne $row.Values.Count) { throw "Unexpected metadata delta: $key" }
        foreach ($property in $row.Values.Keys) {
            if ([string]$actual[$property] -cne [string]$row.Values[$property]) { throw "Unexpected metadata delta: $key.$property" }
        }
    }
    $field = ($delta | Where-Object List -eq 'FieldDefinitions').Values
    $form = ($delta | Where-Object List -eq 'FormFieldDefinitions').Values
    if (-not $field.IsRequired -or $field.ControlType -ne 'Text' -or $field.SortOrder -ne 0 -or $field.IsReadOnly) { throw 'Invalid Title field metadata.' }
    if ($form.RequiredIf -ne 'true' -or $form.SortOrder -ne 0 -or $form.FormFieldDefinitionKey -ne "${ObjectType}:Edit:Title") { throw 'Invalid Title form metadata.' }
    if ($PlanPath) {
        $delta | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $PlanPath -Encoding utf8
    }
    Write-Host "$ObjectType Title contract passed: native schema, two new metadata rows, $($oldRows.Count) existing rows unchanged; no tenant access."
} finally {
    if ($oldContext) { $global:GPContext = $oldContext.Value }
    else { Remove-Variable GPContext -Scope Global -ErrorAction SilentlyContinue }
    Remove-Module $metadata
}
