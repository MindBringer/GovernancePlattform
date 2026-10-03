[CmdletBinding()]
param([string]$RepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# Button schema/name contract: https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/control-button
$source = Get-Content (Join-Path $RepositoryRoot 'powerplatform/canvas/GovernancePortal/Src/scrShell.pa.yaml') -Raw
$buttons = @('lblRefresh','lblNew','lblEditorCancel','lblEditorSave','lblDiscardStay','lblDiscardConfirm','lblNavigationItem','lblObjectTypeTitle','btnAssetRecordOpen','btnSystemRecordOpen')
$inputs = @('txtEditorText','txtEditorMultiline','txtEditorNumber','datEditorDate','togEditorBoolean','drpEditorChoice','cmbEditorLookup','cmbEditorPerson','txtRecordSearch','txtRecordId')
foreach ($control in $buttons + $inputs) {
    $match = [regex]::Match($source, "(?m)^(?<indent> *)- ${control}:\r?`n")
    if (-not $match.Success) { throw "Missing core control: $control" }
    $indent = $match.Groups['indent'].Value.Length
    $block = $source.Substring($match.Index + $match.Length)
    $end = [regex]::Match($block, "(?m)^ {0,$indent}- \w+:")
    if ($end.Success) { $block = $block.Substring(0, $end.Index) }
    if ($control -in $buttons -and $block -notmatch 'Control: Classic/Button@') { throw "$control needs button semantics for keyboard activation." }
    # Classic buttons expose Text as their screenreader name; AccessibleLabel
    # is rejected by Studio's SourceCode schema (PA2108). Input controls need it.
    if ($control -in $buttons) {
        if ($block -match '(?m)^ *AccessibleLabel:') { throw "$control has an unsupported Classic Button property: AccessibleLabel." }
        if ($block -notmatch '(?m)^ *Text: (?:=.+|\|-\r?\n +=.+)') { throw "$control needs a visible Text name." }
    } elseif ($block -notmatch '(?m)^ *AccessibleLabel: =.+') {
        throw "$control needs a descriptive AccessibleLabel."
    }
    foreach ($property in @('TabIndex: =0\r?$', 'FocusedBorderThickness: =3\r?$', 'FocusedBorderColor: =gblTheme.ColorText\r?$')) {
        if ($block -notmatch "(?m)^ *$property") { throw "Missing core accessibility contract: $control/$property" }
    }
    if ($control -in $inputs) {
        $busyPattern = if ($control -in @('txtRecordSearch','txtRecordId')) {
            'DisplayMode: =If\(gblSaveBusy \|\| gblLoadBusy \|\| gblShowDiscardDialog, DisplayMode.Disabled,'
        } else {
            'DisplayMode: =If\(gblShowDiscardDialog \|\| gblSaveBusy \|\| gblLoadBusy, DisplayMode.Disabled,'
        }
        if ($block -notmatch $busyPattern) { throw "$control must not accept edits under the modal or during Load/Save." }
    }
}
foreach ($control in @('galNavigation','galObjectTypes','galEditorFields','galAssetRecords','galSystemRecords')) {
    $match = [regex]::Match($source, "(?ms)- ${control}:\r?`n.*?Properties:\r?`n(?<properties>.*?)Children:")
    if (-not $match.Success -or $match.Groups['properties'].Value -notmatch 'AccessibleLabel:' -or $match.Groups['properties'].Value -notmatch 'ItemAccessibleLabel:') { throw "Missing gallery context: $control" }
}
Write-Host 'Asset editor source accessibility contract passed: 20 core controls / 5 galleries. Studio and keyboard acceptance still required.'
