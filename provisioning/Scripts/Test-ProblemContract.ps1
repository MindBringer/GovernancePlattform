[CmdletBinding()]
param([string]$NativeSnapshotPath, [switch]$RequireNativeFields)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$provisioning = Split-Path $PSScriptRoot -Parent
Import-Module (Join-Path $provisioning 'Modules/Model.psm1') -Force
Import-Module (Join-Path $provisioning 'Modules/Compiler.psm1') -Force
Import-Module (Join-Path $provisioning 'Modules/Schema.psm1') -Force
$model = Get-GPArchitectureModel -Root $provisioning
Test-GPArchitectureModel $model | Out-Null
$problem = (Compile-GPArchitecture $model).Lists | Where-Object ObjectKey -CEQ 'Problem'
if ($problem.Title -cne 'Problems' -or !$problem.Settings.Versioning) {
    throw 'Problems requires a versioned native list.'
}

$notes = @('RootCause', 'Workaround', 'KnownError')
$targets = [ordered]@{ RelatedIncidents = 'Incidents'; ResolvingChanges = 'Changes' }
$typeNames = @{ Incidents = 'Incident'; Changes = 'Change' }
foreach ($name in ($notes + @($targets.Keys))) {
    $fields = @($problem.Fields | Where-Object InternalName -CEQ $name)
    if ($fields.Count -ne 1 -or $fields[0].Required -or $fields[0].Indexed -or $fields[0].EnforceUnique -or
        $fields[0]['searchable'] -ne $false -or $fields[0]['exportable'] -ne $false -or $fields[0]['aiVisible'] -ne $false) {
        throw "Expected one optional, unindexed Problems field $name with restricted metadata."
    }
    $field = $fields[0]
    if ($name -cin $notes) {
        if ($field.Type -cne 'Note') { throw "Expected a plain Note for $name." }
        continue
    }
    if ($field.Type -cne 'Lookup' -or !$field.allowMultiple -or $field.LookupList -cne $targets[$name]) {
        throw "Missing typed, multi-value list mapping for $name."
    }
    $guid = '00000000-0000-0000-0000-000000000001'
    $xmlText = & (Get-Module Schema) {
        param($Definition, $Target)
        $global:GPContext = @{ FieldGroup = 'Governance' }
        New-GPFieldXml $Definition $Target
    } $field $guid
    $xml = ([xml]$xmlText).Field
    if ($xml.Type -cne 'LookupMulti' -or $xml.Mult -cne 'TRUE' -or $xml.List -cne "{$guid}" -or $xml.ShowField -cne 'Title') {
        throw "Generated $name field XML differs from the native LookupMulti contract."
    }
}

if ($RequireNativeFields -and !$NativeSnapshotPath) { throw 'A native snapshot is required for the field readback.' }
if ($NativeSnapshotPath) {
    $snapshot = Get-Content -LiteralPath $NativeSnapshotPath -Raw | ConvertFrom-Json -AsHashtable -Depth 20
    if ($snapshot.state -cne 'verified') { throw 'The native Problems inventory is unavailable.' }
    foreach ($name in @('Problems', 'Incidents')) {
        $list = $snapshot.lists[$name]
        if (!$list.versioned -or !$list.uniquePermissions -or $list.reader.read -or $list.reader.add -or $list.reader.edit -or
            !$list.editor.read -or !$list.editor.add -or !$list.editor.edit) {
            throw "The native pilot roles or versioning differ for $name."
        }
    }
    $native = $snapshot.lists.Problems
    $incidents = $snapshot.lists.Incidents
    if (!$native.acl -or !$incidents.acl -or $incidents.uniqueItems -ne 0 -or
        @($native.acl.roles + $incidents.acl.roles | Where-Object { $null -eq $_.contentAccess }).Count -ne 0) {
        throw 'The effective ACL inventories or Incident item inheritance were not confirmed.'
    }
    if ($RequireNativeFields) {
        $contentRoles = {
            param($Assignments)
            foreach ($assignment in $Assignments) {
                foreach ($role in ($assignment.roles | Where-Object contentAccess)) { "$($assignment.principal)/$($role.id)" }
            }
        }
        $problemAcl = @(& $contentRoles $native.acl) -join '|'
        $incidentAcl = @(& $contentRoles $incidents.acl) -join '|'
        $it = @($native.acl | Where-Object { $_.it -and @($_.roles | Where-Object kind -in @(3, 6)).Count -gt 0 })
        if ($problemAcl -cne $incidentAcl -or $it.Count -ne 1) {
            throw 'Problems and Incidents must grant item access to the same IT and administrator principals.'
        }
    }
    foreach ($name in ($notes + @($targets.Keys))) {
        $fields = @($native.fields | Where-Object name -CEQ $name)
        if ($fields.Count -eq 0 -and !$RequireNativeFields -and $name -cin @('Workaround', 'RelatedIncidents', 'ResolvingChanges')) {
            continue
        }
        if ($fields.Count -ne 1 -or $fields[0].readOnly -or $fields[0].required -or $fields[0].indexed -or $fields[0].unique) {
            throw "Unexpected native field flags for $name."
        }
        $field = $fields[0]
        if ($name -cin $notes) {
            if ($field.type -cne 'Note' -or $field.richText -or $field.appendOnly) { throw "Unexpected native Note format for $name." }
            continue
        }
        $target = $snapshot.lists[$targets[$name]]
        if ($field.type -cne 'LookupMulti' -or !$field.multi -or $field.showField -cne 'Title' -or [guid]$field.list -ne [guid]$target.listId) {
            throw "Unexpected native multi-value lookup contract for $($typeNames[$targets[$name]]) in $name."
        }
    }
}
Write-Host 'Problems versioning, plain analysis fields and typed multi-value lookups verified.'
