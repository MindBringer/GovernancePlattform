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
$list = @($compiled.Lists | Where-Object ObjectKey -CEQ 'BusinessProcess')
if ($list.Count -ne 1 -or $list[0].Title -cne 'BusinessProcesses' -or $list[0].Template -cne 'GenericList' -or
    !$list[0].Settings.Versioning -or $list[0].Settings.Attachments) {
    throw 'Unexpected process register settings.'
}

$types = [ordered]@{
    GovernanceID = 'Text'; Description = 'Note'; Owner = 'User'; IsActive = 'Boolean'
    BiaStatus = 'Choice'; BiaAssetItemID = 'Number'; BiaSystemItemID = 'Number'
    BiaMtpdMinutes = 'Number'; BiaRtoMinutes = 'Number'; BiaRpoMinutes = 'Number'
    BiaMinimumService = 'Note'; BiaAssessedAt = 'DateTime'; BiaAssessedBy = 'User'
    BcmExerciseDate = 'DateTime'; BcmExerciseResult = 'Note'
    BcmEvidenceItemID = 'Number'; BcmEvidenceVersion = 'Text'
}
if ($list[0].Fields.Count -ne $types.Count) { throw 'Unexpected number of process fields.' }
foreach ($name in $types.Keys) {
    $field = @($list[0].Fields | Where-Object InternalName -CEQ $name)
    if ($field.Count -ne 1 -or $field[0].Type -cne $types[$name]) {
        throw "Unexpected process field $name."
    }
}
$byName = @{}
foreach ($field in $list[0].Fields) { $byName[$field.InternalName] = $field }
if (!$byName.GovernanceID.Indexed -or !$byName.GovernanceID.EnforceUnique -or !$byName.BiaStatus.Required -or
    !$byName.BiaStatus.Indexed -or ($byName.BiaStatus.Choices -join '|') -cne 'Entwurf|Bewertet' -or
    $byName.BiaMtpdMinutes.min -ne 1 -or $byName.BiaRtoMinutes.min -ne 1 -or $byName.BiaRpoMinutes.min -ne 0 -or
    $byName.BiaAssessedAt.DateFormat -cne 'DateTime' -or $byName.BcmExerciseDate.DateFormat -cne 'DateOnly') {
    throw 'Unexpected process request key, lifecycle, minutes or date contract.'
}

if ($NativeSnapshotPath) {
    $snapshot = Get-Content -LiteralPath $NativeSnapshotPath -Raw | ConvertFrom-Json -Depth 20
    if ($snapshot.state -cne 'verified') { throw 'Process register provisioning was not verified.' }
    $native = $snapshot.lists.BusinessProcesses
    if (!$native.versioned -or !$native.uniquePermissions -or !$native.editor.read -or
        !$native.editor.add -or !$native.editor.edit -or !$native.reader.read -or
        $native.reader.add -or $native.reader.edit -or $native.reader.delete -or
        $native.fields.Count -ne $types.Count) {
        throw 'Unexpected native process roles, versioning or schema.'
    }
    foreach ($name in $types.Keys) {
        $expected = $byName[$name]
        $actual = @($native.fields | Where-Object name -CEQ $name)
        if ($actual.Count -ne 1 -or $actual[0].type -cne $expected.Type -or
            $actual[0].required -ne $expected.Required -or $actual[0].indexed -ne $expected.Indexed -or
            $actual[0].unique -ne $expected.EnforceUnique -or
            ($expected.ContainsKey('DateFormat') -and $actual[0].format -cne $expected.DateFormat) -or
            ($expected.ContainsKey('Choices') -and ($actual[0].choices -join '|') -cne ($expected.Choices -join '|'))) {
            throw "Unexpected native process field $name."
        }
    }
}
Write-Host 'Business continuity register, lifecycle, minute bounds, date formats and unique request key verified.'
