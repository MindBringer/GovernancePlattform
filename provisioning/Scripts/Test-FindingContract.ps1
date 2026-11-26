[CmdletBinding()]
param([string]$NativeSnapshotPath)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$provisioning = Split-Path $PSScriptRoot -Parent
Import-Module (Join-Path $provisioning 'Modules/Model.psm1') -Force
Import-Module (Join-Path $provisioning 'Modules/Compiler.psm1') -Force
$model = Get-GPArchitectureModel -Root $provisioning
Test-GPArchitectureModel $model | Out-Null
$compiled = Compile-GPArchitecture $model
$types = [ordered]@{
    GovernanceID = 'Text'; Description = 'Note'; Owner = 'User'; IsActive = 'Boolean'
    FindingStatus = 'Choice'; FindingDueDate = 'DateTime'; FindingSourceItemID = 'Number'
    FindingMeasureItemID = 'Number'; FindingEvidenceItemID = 'Number'; FindingClosureNote = 'Note'
    FindingClosedBy = 'User'; FindingClosedAt = 'DateTime'; FindingEvidenceVersion = 'Text'
}
$statusLabels = 'Offen|In Bearbeitung|Abgeschlossen'
foreach ($name in 'Findings', 'AuditFindings') {
    $list = @($compiled.Lists | Where-Object Title -CEQ $name)
    if ($list.Count -ne 1 -or $list[0].Template -cne 'GenericList' -or
        !$list[0].Settings.Versioning -or $list[0].Settings.Attachments -or $list[0].Fields.Count -ne $types.Count) {
        throw "Unexpected schema for $name."
    }
    foreach ($field in $types.Keys) {
        $definition = @($list[0].Fields | Where-Object InternalName -CEQ $field)
        if ($definition.Count -ne 1 -or $definition[0].Type -cne $types[$field]) {
            throw "Unexpected field $name.$field."
        }
    }
    $key = $list[0].Fields | Where-Object InternalName -CEQ 'GovernanceID'
    $status = $list[0].Fields | Where-Object InternalName -CEQ 'FindingStatus'
    $due = $list[0].Fields | Where-Object InternalName -CEQ 'FindingDueDate'
    if (!$key.Indexed -or !$key.EnforceUnique -or !$status.Indexed -or !$status.Required -or
        ($status.Choices -join '|') -cne $statusLabels -or !$due.Required -or $due.DateFormat -cne 'DateOnly') {
        throw "Unexpected request key, status or deadline in $name."
    }
}
if ($NativeSnapshotPath) {
    $snapshot = Get-Content -LiteralPath $NativeSnapshotPath -Raw | ConvertFrom-Json -Depth 20
    if ($snapshot.state -cne 'verified' -or $snapshot.lists.Findings.id -eq $snapshot.lists.AuditFindings.id) {
        throw 'The two separate native lists were not confirmed.'
    }
    foreach ($name in 'Findings', 'AuditFindings') {
        $native = $snapshot.lists.$name
        if (!$native.versioned -or !$native.uniquePermissions -or
            !$native.editor.read -or !$native.editor.add -or !$native.editor.edit -or
            $native.reader.read -ne ($name -ceq 'Findings') -or $native.reader.add -or $native.reader.edit) {
            throw "Unexpected versioning or pilot roles in $name."
        }
        foreach ($field in $types.Keys) {
            $definition = @($native.fields | Where-Object name -CEQ $field)
            if ($definition.Count -ne 1 -or $definition[0].type -cne $types[$field]) {
                throw "Unexpected native field $name.$field."
            }
        }
        $key = $native.fields | Where-Object name -CEQ 'GovernanceID'
        $status = $native.fields | Where-Object name -CEQ 'FindingStatus'
        $due = $native.fields | Where-Object name -CEQ 'FindingDueDate'
        if (!$key.indexed -or !$key.unique -or !$status.indexed -or !$status.required -or
            ($status.choices -join '|') -cne $statusLabels -or !$due.required -or $due.format -cne 'DateOnly') {
            throw "Unexpected native key, status or deadline in $name."
        }
    }
}
Write-Host 'Finding lists, lifecycle, unique request keys and role boundary verified.'
