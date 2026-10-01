[CmdletBinding()]
param([string]$RepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$source = Get-Content (Join-Path $RepositoryRoot 'powerplatform/canvas/GovernancePortal/Src/scrShell.pa.yaml') -Raw
$buttons = @('lblRefresh','lblNew','lblEditorCancel','lblEditorSave','lblDiscardStay','lblDiscardConfirm','lblNavigationItem','lblObjectTypeTitle')
$inputs = @('txtEditorText','txtEditorMultiline','txtEditorNumber','datEditorDate','togEditorBoolean','drpEditorChoice','cmbEditorLookup','cmbEditorPerson')
foreach ($control in $buttons + $inputs) {
    $match = [regex]::Match($source, "(?m)^(?<indent> *)- ${control}:\r?`n")
    if (-not $match.Success) { throw "Missing core control: $control" }
    $indent = $match.Groups['indent'].Value.Length
    $block = $source.Substring($match.Index + $match.Length)
    $end = [regex]::Match($block, "(?m)^ {0,$indent}- \w+:")
    if ($end.Success) { $block = $block.Substring(0, $end.Index) }
    if ($control -in $buttons -and $block -notmatch 'Control: Classic/Button@') { throw "$control needs button semantics for keyboard activation." }
    foreach ($property in @('AccessibleLabel: =.+', 'TabIndex: =0\r?$', 'FocusedBorderThickness: =3\r?$', 'FocusedBorderColor: =gblTheme.ColorText\r?$')) {
        if ($block -notmatch "(?m)^ *$property") { throw "Missing core accessibility contract: $control/$property" }
    }
    if ($control -in $inputs -and $block -notmatch 'DisplayMode: =If\(gblShowDiscardDialog \|\| gblSaveBusy, DisplayMode.Disabled,') { throw "$control must not accept edits under the modal or during Save." }
}
foreach ($control in @('galNavigation','galObjectTypes','galEditorFields')) {
    $match = [regex]::Match($source, "(?ms)- ${control}:\r?`n.*?Properties:\r?`n(?<properties>.*?)Children:")
    if (-not $match.Success -or $match.Groups['properties'].Value -notmatch 'AccessibleLabel:' -or $match.Groups['properties'].Value -notmatch 'ItemAccessibleLabel:') { throw "Missing gallery context: $control" }
}
Write-Host 'Asset editor source accessibility contract passed: 16 core controls / 3 galleries. Studio and keyboard acceptance still required.'
