[CmdletBinding()]
param([string]$PlanPath)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Import-Module "$root/provisioning/Modules/Model.psm1" -Force
Import-Module "$root/provisioning/Modules/Compiler.psm1" -Force
$model = Get-GPArchitectureModel -Root "$root/provisioning"
$baseline = Get-GPArchitectureModel -Root "$root/provisioning"
$addedNames = @('Title','LinkedAsset','ChangeStatus')
$baseline.ObjectFields = @($baseline.ObjectFields | Where-Object { -not ($_.objectTypeKey -eq 'Change' -and $_.internalName -in $addedNames) })
$baseline.ChoiceSets = @($baseline.ChoiceSets | Where-Object key -ne 'ChangeStatus')
($baseline.objectTypes | Where-Object key -eq 'Change').allowVersioning = $false
$schema = Compile-GPArchitecture $model
$oldSchema = Compile-GPArchitecture $baseline
$change = @($schema.Lists | Where-Object ObjectKey -eq 'Change')[0]
$fields = @($change.Fields | Where-Object InternalName -in $addedNames)
if ($fields.Count -ne 3 -or $change.Fields.Count -ne 34 -or -not $change.Settings.Versioning) {
    throw 'Change requires its native Title contract, two additional fields and version history.'
}
$title = @($fields | Where-Object InternalName -eq 'Title')[0]
$lookup = @($fields | Where-Object InternalName -eq 'LinkedAsset')[0]
$status = @($fields | Where-Object InternalName -eq 'ChangeStatus')[0]
if ($title.Type -ne 'Text' -or -not $title.Required -or $title.maxLength -ne 255) { throw 'Invalid Change Title contract.' }
if ($lookup.Type -ne 'Lookup' -or $lookup.LookupList -ne 'Assets' -or $lookup.Required -or -not $lookup.Indexed) { throw 'Change asset reference must be an optional indexed native Assets lookup.' }
if ($status.Type -ne 'Choice' -or $status.ChoiceSet -ne 'ChangeStatus' -or $status.default -ne 'ChangeStatus:Draft' -or $status.Required -or -not $status.Indexed) { throw 'Invalid Change lifecycle field/default.' }
$states = @(($model.StatusModels | Where-Object key -eq 'Change').states)
$choices = @(($model.ChoiceSets | Where-Object key -eq 'ChangeStatus').values)
if ($states.Count -ne 7 -or $choices.Count -ne 7) { throw 'The complete Change lifecycle must be retained.' }
for ($i=0; $i -lt $states.Count; $i++) {
    if ($choices[$i][0] -cne $states[$i][0] -or $choices[$i][1] -cne $states[$i][1] -or $choices[$i][2] -ne (($i+1)*10) -or $status.Choices[$i] -cne $states[$i][1]) { throw 'Change choice keys, native labels and lifecycle model diverge.' }
}
$approval = @($change.Fields | Where-Object InternalName -eq 'ApprovalStatus')[0]
if ($approval.ChoiceSet -ne 'ApprovalStatus' -or $approval.Choices.Count -ne 4) { throw 'Approval and implementation lifecycle must remain separate.' }
foreach ($oldList in $oldSchema.Lists) {
    $current = @($schema.Lists | Where-Object ObjectKey -eq $oldList.ObjectKey)[0]
    $expectedCount = $oldList.Fields.Count + $(if ($oldList.ObjectKey -eq 'Change') {3} else {0})
    if ($current.Fields.Count -ne $expectedCount) { throw "Unexpected field delta: $($oldList.Title)" }
    foreach ($oldField in $oldList.Fields) {
        $actual = @($current.Fields | Where-Object InternalName -eq $oldField.InternalName)
        if ($actual.Count -ne 1 -or ($actual[0] | ConvertTo-Json -Depth 20) -cne ($oldField | ConvertTo-Json -Depth 20)) { throw "Existing field changed: $($oldList.Title).$($oldField.InternalName)" }
    }
    if ($oldList.ContainsKey('Settings')) {
        foreach ($property in $oldList.Settings.Keys) {
            $expected = if ($oldList.ObjectKey -eq 'Change' -and $property -eq 'Versioning') {$true} else {$oldList.Settings[$property]}
            if ($current.Settings[$property] -ne $expected) { throw "Unexpected list setting delta: $($oldList.Title).$property" }
        }
    }
}
# Capture the actual generators at their write boundary. This test never imports
# PnP, authenticates, calls a connector or executes provisioning.
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
    $oldMap = @{}; $currentMap = @{}
    foreach ($row in $oldRows) { $oldMap[$row.List+'/'+$row.Values[$row.KeyField]] = $row.Values }
    foreach ($row in $rows) {
        $key = $row.List+'/'+$row.Values[$row.KeyField]
        if ($currentMap.ContainsKey($key)) { throw "Duplicate generated metadata key: $key" }
        $currentMap[$key] = $row.Values
    }
    $added = @($rows | Where-Object { -not $oldMap.ContainsKey($_.List+'/'+$_.Values[$_.KeyField]) })
    $changed = @($rows | Where-Object { $_.List -eq 'ObjectTypes' -and $_.Values.ObjectTypeKey -eq 'Change' })
    if ($added.Count -ne 13 -or $rows.Count -ne $oldRows.Count+13 -or $changed.Count -ne 1) { throw 'Expected 13 new metadata rows and one Change object-type update.' }
    foreach ($key in $oldMap.Keys) {
        $actual = $currentMap[$key]; $old = $oldMap[$key]
        if ($null -eq $actual -or $actual.Count -ne $old.Count) { throw "Existing metadata removed or reshaped: $key" }
        foreach ($property in $old.Keys) {
            $expected = if ($key -eq 'ObjectTypes/Change' -and $property -eq 'AllowVersioning') {$true} else {$old[$property]}
            if ([string]$actual[$property] -cne [string]$expected) { throw "Unplanned metadata change: $key.$property" }
        }
    }
    foreach ($name in $addedNames) {
        $definition = $currentMap["FieldDefinitions/Change:$name"]
        $form = $currentMap["FormFieldDefinitions/Change:Edit:$name"]
        if ($definition.IsReadOnly -or -not $definition.IsVisible -or $form.FormDefinitionKey -ne 'Change:Edit' -or $form.SectionKey -ne $definition.SectionKey) { throw "Invalid Change field/form linkage: $name" }
    }
    if ($currentMap['FormFieldDefinitions/Change:Edit:Title'].RequiredIf -ne 'true' -or $currentMap['FormFieldDefinitions/Change:Edit:Title'].SortOrder -ne 0) { throw 'Native Change Title must be required and first without moving existing rows.' }
    if ($currentMap['FieldDefinitions/Change:LinkedAsset'].LookupObjectTypeKey -ne 'Asset' -or $currentMap['FieldDefinitions/Change:ChangeStatus'].DefaultValue -ne 'ChangeStatus:Draft') { throw 'Metadata lookup/default differs from architecture.' }
    # Substitute only a synthetic GUID into the real field XML generator.
    $lookupXml = & $schemaModule { param($Field) New-GPFieldXml -F $Field -LookupListId '11111111-1111-1111-1111-111111111111' } $lookup
    $statusXml = & $schemaModule { param($Field) New-GPFieldXml -F $Field } $status
    [xml]$lx = $lookupXml; [xml]$sx = $statusXml
    if ($lx.Field.Type -ne 'Lookup' -or $lx.Field.ShowField -ne 'Title' -or $lx.Field.List -ne '{11111111-1111-1111-1111-111111111111}' -or $lx.Field.HasAttribute('Mult')) { throw 'Invalid native single-asset lookup XML.' }
    if ($sx.Field.Type -ne 'Choice' -or @($sx.Field.CHOICES.CHOICE).Count -ne 7 -or $sx.Field.HasAttribute('FillInChoice') -or $sx.Field.HasAttribute('ReadOnly')) { throw 'Invalid native Change lifecycle XML.' }
    if ($PlanPath) {
        [ordered]@{
            status='prepared-not-authorized'; sourceList='Changes'
            baselineFields=31; candidateFields=34
            existingNativeTitle='verify required Text/255; no additional Title column'
            addFields=@(
                [ordered]@{InternalName='LinkedAsset'; Type='Lookup'; LookupList='Assets'; XmlWithSyntheticLookupGuid=$lookupXml},
                [ordered]@{InternalName='ChangeStatus'; Type='Choice'; Xml=$statusXml}
            )
            listSettings=[ordered]@{EnableVersioning=$true; existingVersions='preserve'; existingItems='preserve; no backfill'}
            addMetadataRows=$added; updateMetadataRows=$changed
            existingMetadataRowsUnchanged=$oldRows.Count-1
            connectorPrerequisite='explicit Changes connection, native schema readback, generated reference export and separate DEV-to-Git approval; never synthesize connector metadata'
        } | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $PlanPath -Encoding utf8
    }
    Write-Host "Change prerequisite contract passed: native Title; two new fields; versioning; 13 new/1 updated metadata rows; $($oldRows.Count-1) existing rows and all existing fields preserved; no tenant access."
} finally {
    if ($oldContext) { $global:GPContext = $oldContext.Value }
    else { Remove-Variable GPContext -Scope Global -ErrorAction SilentlyContinue }
    Remove-Module $metadata
    Remove-Module $schemaModule
}
