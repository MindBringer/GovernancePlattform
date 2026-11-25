[CmdletBinding()]
param([string]$NativeSnapshotPath)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$provisioning = Split-Path $PSScriptRoot -Parent
Import-Module (Join-Path $provisioning 'Modules/Model.psm1') -Force
Import-Module (Join-Path $provisioning 'Modules/Compiler.psm1') -Force
$model = Get-GPArchitectureModel -Root $provisioning
Test-GPArchitectureModel $model | Out-Null
$incident = (Compile-GPArchitecture $model).Lists | Where-Object ObjectKey -CEQ 'Incident'

$expectedTransitions = [ordered]@{
    New = 'InProgress'
    InProgress = 'Resolved'
    Resolved = 'Closed'
    Closed = ''
}
$states = @(($model.StatusModels | Where-Object key -CEQ 'Incident').states)
if ($states.Count -ne $expectedTransitions.Count) { throw 'Incident status model is incomplete.' }
foreach ($key in $expectedTransitions.Keys) {
    $matching = @($states | Where-Object { $_[0] -ceq $key })
    if ($matching.Count -ne 1) { throw "Missing or duplicate Incident status: $key." }
    $state = $matching[0]
    if (($state[4] -join ',') -cne $expectedTransitions[$key] -or
        $state[2] -ne ($key -ceq 'New') -or $state[3] -ne ($key -ceq 'Closed')) {
        throw "Unexpected Incident transition or status boundary: $key."
    }
}
if ($incident.Title -cne 'Incidents' -or !$incident.Settings.Versioning) {
    throw 'Incident pilot requires the Incidents list and version history.'
}

$requiredTypes = [ordered]@{
    Owner = 'User'
    LinkedSystem = 'Lookup'
    PortalStatus = 'Text'
    Impact = 'Text'
    Urgency = 'Text'
    Priority = 'Choice'
    ResolvedDate = 'DateTime'
    BusinessImpact = 'Note'
    SecurityIncident = 'Boolean'
}
foreach ($name in $requiredTypes.Keys) {
    $matching = @($incident.Fields | Where-Object InternalName -CEQ $name)
    if ($matching.Count -ne 1 -or $matching[0].Type -cne $requiredTypes[$name]) {
        throw "Unexpected modeled Incident field type: $name."
    }
}
$linkedSystem = $incident.Fields | Where-Object InternalName -CEQ 'LinkedSystem'
$priority = $incident.Fields | Where-Object InternalName -CEQ 'Priority'
if ($linkedSystem.LookupList -cne 'Systems' -or $priority.ChoiceSet -cne 'Priority') {
    throw 'Incident lookup or choice-set binding has changed.'
}

if ($NativeSnapshotPath) {
    $native = Get-Content -LiteralPath $NativeSnapshotPath -Raw | ConvertFrom-Json -Depth 20
    if ($native.state -cne 'verified' -or $native.incidents.settings.title -cne $incident.Title -or
        $native.systems.settings.title -cne $linkedSystem.LookupList -or !$native.incidents.settings.versioning) {
        throw 'Native list identities or version history could not be verified.'
    }
    $nativeTypes = [ordered]@{ Title = 'Text' } + $requiredTypes
    foreach ($name in $nativeTypes.Keys) {
        $matching = @($native.incidents.fields | Where-Object internalName -CEQ $name)
        if ($matching.Count -ne 1 -or $matching[0].type -cne $nativeTypes[$name] -or $matching[0].readOnly) {
            throw "Unexpected native Incident field type or write capability: $name."
        }
    }
    $nativeTitle = $native.incidents.fields | Where-Object internalName -CEQ 'Title'
    $nativeSystem = $native.incidents.fields | Where-Object internalName -CEQ 'LinkedSystem'
    $nativePriority = $native.incidents.fields | Where-Object internalName -CEQ 'Priority'
    if (!$nativeTitle.required -or [guid]$nativeSystem.lookup -ne [guid]$native.systems.settings.id -or
        ($nativePriority.choices -join '|') -cne ($priority.Choices -join '|')) {
        throw 'Native Incident title, choice labels or Systems lookup differ.'
    }
    Write-Host 'Incident field types, version history, Systems lookup and native choice labels verified.'
}
else {
    Write-Host 'Incident schema and lifecycle verified locally.'
}
