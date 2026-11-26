[CmdletBinding()]
param([Parameter(Mandatory)][string]$PowerFxDirectory)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot '../canvas/GovernancePortal/Src'
foreach ($library in 'Microsoft.PowerFx.Core.dll', 'Microsoft.PowerFx.Interpreter.dll') {
    [void][Reflection.Assembly]::LoadFrom((Join-Path $PowerFxDirectory $library))
}
$engine = [Microsoft.PowerFx.RecalcEngine]::new()
$options = [Microsoft.PowerFx.ParserOptions]::new()
$options.Culture = [Globalization.CultureInfo]::InvariantCulture

function Get-ItemsFormula([string]$Screen, [string]$Control) {
    $yaml = Get-Content (Join-Path $source "$Screen.pa.yaml") -Raw
    $controlStart = [regex]::Match($yaml, "(?m)^(?<indent> +)- ${Control}:\r?$")
    if (!$controlStart.Success) { throw "Missing gallery $Screen.$Control" }
    $tail = $yaml.Substring($controlStart.Index + $controlStart.Length)
    $end = [regex]::Match($tail, "(?m)^ {0,$($controlStart.Groups['indent'].Length)}- \w+:")
    if ($end.Success) { $tail = $tail.Substring(0, $end.Index) }
    $items = [regex]::Match($tail, '(?m)^(?<indent> +)Items: \|-\r?\n(?<formula>(?:\k<indent> +[^\r\n]*\r?\n)+)')
    if (!$items.Success) { throw "Missing Items on $Screen.$Control" }
    $formula = $items.Groups['formula'].Value.Trim().TrimStart('=')
    if ($formula -match '\b(Collect|FirstN|LastN|ForAll|ClearCollect)\s*\(') { throw "$Control truncates locally" }
    return $formula.Replace('Self.Visible', 'statusTestControl.Visible')
}

function Invoke-Fx([string]$Expression) {
    $value = $engine.Eval($Expression, $null, $options)
    if ($value -is [Microsoft.PowerFx.Types.ErrorValue]) {
        throw "Power Fx error for $Expression. $($value.Errors.Message -join ', ')"
    }
    return $value
}
function Set-Fx([string]$Name, [string]$Expression) {
    $engine.UpdateVariable($Name, (Invoke-Fx $Expression))
}
function Set-Filter([string]$Name, [string]$Status) {
    Set-Fx $Name ('{Selected: {Value: "' + $Status + '"}}')
}
function Assert-StatusOptions([string]$Screen, [string]$Control, [string]$Expected) {
    $items = Get-ItemsFormula $Screen $Control
    $actual = (Invoke-Fx ('Concat(' + $items + ', Value, "|")')).ToObject()
    if ($actual -cne $Expected) { throw "$Screen.$Control displays <$actual> instead of <$Expected>" }
}
function Assert-Rows([string]$Formula, [string]$Expected, [string]$Case) {
    $expression = 'Concat(' + $Formula + ', Text(ID), ",")'
    $actual = [string](Invoke-Fx $expression).ToObject()
    if ($actual -cne $Expected) { throw "$Case expected <$Expected> and returned <$actual>" }
}
function Set-Rows([string]$List, [string]$Field, [string[]]$Statuses, [switch]$TextStatus, [switch]$Document) {
    $records = for ($index = 0; $index -lt $Statuses.Count; $index++) {
        $id = $index + 1
        $native = if ($Statuses[$index] -eq '@blank') { 'Blank()' } else { '"' + $Statuses[$index] + '"' }
        $value = if ($TextStatus) { $native } else { "{Value: $native}" }
        $extra = if ($Document) { ", Modified: Date(2026, 1, $id)" } else { '' }
        '{ID:' + $id + ', Title:"Zeile ' + $id + '", CorrelationID:"GP-PRB-REQ-' + $id +
            '", ' + $Field + ': ' + $value + $extra + '}'
    }
    Set-Fx $List ('Table(' + ($records -join ',') + ')')
}

Assert-StatusOptions scrIncidents drpIncidentBrowseStatus 'Alle Status|Offen und in Arbeit|Nur offen|Neu|In Bearbeitung|Gelöst|Geschlossen|Ohne Status'
Assert-StatusOptions scrProblems drpProblemBrowseStatus 'Alle Status|Entwurf|Aktiv|In Review|Außer Betrieb|Archiviert|Ohne Status'
Assert-StatusOptions scrControls drpControlBrowseStatus 'Alle Status|Konzipiert|Implementiert|Wirksam|Unwirksam|Ohne Status'
Assert-StatusOptions scrMeasures drpMeasureBrowseStatus 'Alle Status|Offen und in Arbeit|Geplant|In Umsetzung|In Prüfung|Wirksam|Geschlossen|Ohne Status'
Assert-StatusOptions scrDocumentLibrary drpDocumentBrowseStatus 'Alle Status|Entwurf|In Prüfung|Veröffentlicht|Außer Kraft|Ohne Status (inkl. Ordner)'
Set-Fx gblObjectType '"Change"'
Assert-StatusOptions scrShell drpRecordBrowseStatus 'Alle Status|Offen und in Arbeit|Entwurf|Eingereicht|Genehmigt|Geplant|Umgesetzt|Abgelehnt|Geschlossen|Ohne Status'
Set-Fx gblObjectType '"Risk"'
Assert-StatusOptions scrShell drpRecordBrowseStatus 'Alle Status|Offen und in Arbeit|Identifiziert|Bewertet|In Bearbeitung|Akzeptiert|Geschlossen|Ohne Status'
Set-Fx gblObjectType '"Asset"'
Assert-StatusOptions scrShell drpRecordBrowseStatus 'Alle Status|Entwurf|Aktiv|In Review|Außer Betrieb|Archiviert|Ohne Status'

$incident = Get-ItemsFormula scrIncidents galIncidents
Set-Rows Incidents PortalStatus @('New','InProgress','Resolved','Closed','@blank','') -TextStatus
Set-Fx txtIncidentSearch '{Visible:true, Text:""}'
Set-Filter drpIncidentBrowseStatus 'Offen und in Arbeit'
Assert-Rows $incident '6,5,2,1' 'Unresolved incidents include unclassified legacy cases'
Set-Filter drpIncidentBrowseStatus 'In Bearbeitung'
Assert-Rows $incident '2' 'Only incident work in progress'
Set-Filter drpIncidentBrowseStatus 'Neu'
Assert-Rows $incident '1' 'Only new incidents'
Set-Filter drpIncidentBrowseStatus 'Nur offen'
Assert-Rows $incident '6,5,1' 'Only open incidents, prior to work in progress'
Set-Filter drpIncidentBrowseStatus 'Gelöst'
Assert-Rows $incident '3' 'Resolved incidents are separate from closed'
Set-Fx txtIncidentSearch '{Visible:false, Text:""}'
Assert-Rows $incident '' 'Denied incident gallery'

$problem = Get-ItemsFormula scrProblems galProblems
Set-Rows Problems GovernanceStatus @('Aktiv','In Review','Archiviert','@blank')
Set-Fx txtProblemSearch '{Visible:true, Text:""}'
Set-Filter drpProblemBrowseStatus 'Alle Status'
Assert-Rows $problem '4,3,2,1' 'Problems browse without a title'
Set-Filter drpProblemBrowseStatus 'Ohne Status'
Assert-Rows $problem '4' 'Unclassified Problems'
Set-Fx txtProblemSearch '{Visible:true, Text:"GP-PRB-REQ-1"}'
Assert-Rows $problem '1' 'Exact request code remains independent of status'
Set-Fx txtProblemSearch '{Visible:false, Text:""}'
Assert-Rows $problem '' 'Denied Problems gallery'

$control = Get-ItemsFormula scrControls galControls
Set-Rows Controls ControlStatus @('Wirksam','Unwirksam','Konzipiert')
Set-Fx txtControlSearch '{Visible:true, Text:""}'
Set-Filter drpControlBrowseStatus 'Unwirksam'
Assert-Rows $control '2' 'Exact control status'

$measure = Get-ItemsFormula scrMeasures galMeasures
Set-Rows Measures MeasureStatus @('Geplant','In Umsetzung','In Prüfung','Wirksam','Geschlossen','@blank')
Set-Fx txtMeasureSearch '{Visible:true, Text:""}'
Set-Filter drpMeasureBrowseStatus 'Offen und in Arbeit'
Assert-Rows $measure '6,3,2,1' 'Measures still needing work'

Set-Fx statusTestControl '{Visible:true}'
Set-Fx gblRecordQuery '""'
Set-Fx gblRecordQueryId '0'
foreach ($case in @(
    @{List='Changes'; Key='Change'; Field='ChangeStatus'; Statuses=@('Entwurf','Eingereicht','Genehmigt','Geplant','Umgesetzt','Abgelehnt','Geschlossen','@blank'); Pending='1,2,3,4,8'; Exact='Umgesetzt'; ExactResult='5'},
    @{List='Risks'; Key='Risk'; Field='RiskStatus'; Statuses=@('Identifiziert','Bewertet','In Bearbeitung','Akzeptiert','Geschlossen','@blank'); Pending='1,2,3,6'; Exact='In Bearbeitung'; ExactResult='3'},
    @{List='Systems'; Key='System'; Field='GovernanceStatus'; Statuses=@('Aktiv','Archiviert','@blank'); Exact='Archiviert'; ExactResult='2'},
    @{List='Assets'; Key='Asset'; Field='LifecycleStatus'; Statuses=@('Aktiv','In Review','@blank'); Exact='In Review'; ExactResult='2'}
)) {
    $items = Get-ItemsFormula scrShell ("gal" + $case.Key + "Records")
    Set-Rows $case.List $case.Field $case.Statuses
    if ($case.ContainsKey('Pending')) {
        Set-Filter drpRecordBrowseStatus 'Offen und in Arbeit'
        Assert-Rows $items $case.Pending "$($case.Key) unfinished"
    }
    Set-Filter drpRecordBrowseStatus $case.Exact
    Assert-Rows $items $case.ExactResult "$($case.Key) exact status"
    Set-Fx gblRecordQuery '"Kein Treffer"'
    Assert-Rows $items '' "$($case.Key) composes status and title"
    Set-Fx gblRecordQueryId '1'
    Assert-Rows $items '1' "$($case.Key) exact ID still wins"
    Set-Fx gblRecordQueryId '0'
    Set-Fx gblRecordQuery '""'
}

foreach ($library in 'Policies','Procedures','Runbooks') {
    $items = Get-ItemsFormula scrDocumentLibrary ("gal" + $library)
    Set-Rows $library DocumentStatus @('Entwurf','In Prüfung','Veröffentlicht','Außer Kraft','@blank') -Document
    Set-Fx documentItemId '0'
    Set-Filter drpDocumentBrowseStatus 'Alle Status'
    Assert-Rows $items '5,4,3,2,1' "$library browses without ID"
    Set-Filter drpDocumentBrowseStatus 'In Prüfung'
    Assert-Rows $items '2' "$library publication status"
    Set-Filter drpDocumentBrowseStatus 'Ohne Status (inkl. Ordner)'
    Assert-Rows $items '5' "$library without status"
    Set-Fx documentItemId '3'
    Assert-Rows $items '3' "$library exact ID wins over the status filter"
}
Write-Host 'Canvas status views verified across eleven galleries.'
