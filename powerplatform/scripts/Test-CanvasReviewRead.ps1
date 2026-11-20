[CmdletBinding()]
param(
    [string]$RepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')),
    [Parameter(Mandatory)][string]$PowerFxDirectory,
    [string]$PythonCommand = 'python3'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$source = Join-Path $RepositoryRoot 'powerplatform/canvas/GovernancePortal/Src'
if ((Get-Content (Join-Path $source 'scrReviews.pa.yaml') -Raw) -match '\b(Patch|SubmitForm|Collect|Remove|UpdateIf)\s*\(') {
    throw 'The review reader must neither write a decision nor update the schedule.'
}

$extract = @'
import json, sys
from pathlib import Path
import yaml

def formulas(node, name, result):
    result.update({f"{name}.{key}": value[1:] for key, value in node.get("Properties", {}).items()
                   if isinstance(value, str) and value.startswith("=")})
    for child in node.get("Children", []):
        for child_name, child_node in child.items():
            formulas(child_node, child_name, result)

source = Path(sys.argv[1])
result = {}
for screen in ("scrReviews", "scrReviewDecision", "scrWorkspace", "scrShell"):
    doc = yaml.safe_load((source / f"{screen}.pa.yaml").read_text(encoding="utf-8-sig"))
    formulas(doc["Screens"][screen], screen, result)
print(json.dumps(result))
'@
$formulas = $extract | & $PythonCommand - $source | ConvertFrom-Json -AsHashtable
if ($LASTEXITCODE -ne 0) { throw 'Canvas review formulas could not be extracted.' }

foreach ($dll in 'Microsoft.PowerFx.Core.dll', 'Microsoft.PowerFx.Interpreter.dll') {
    [void][Reflection.Assembly]::LoadFrom((Join-Path $PowerFxDirectory $dll))
}
$engine = [Microsoft.PowerFx.RecalcEngine]::new()
$options = [Microsoft.PowerFx.ParserOptions]::new()
$options.Culture = [Globalization.CultureInfo]::InvariantCulture
$options.AllowsSideEffects = $true
function Read-Formula([string]$Formula) {
    $result = $engine.Eval($Formula, $null, $options)
    if ($result -is [Microsoft.PowerFx.Types.ErrorValue]) { throw "Invalid formula: $Formula" }
    $result
}
function Assert-Formula([string]$Formula, $Expected) {
    $actual = (Read-Formula $Formula).ToObject()
    if ($actual -cne $Expected) { throw "$Formula returned '$actual', expected '$Expected'." }
    $script:assertions++
}

$assertions = 0
foreach ($key in $formulas.Keys) {
    if ($key -match '^((scrReview|btnReview|lblReview|galReview|txtReview|galDue|btnDue|drpReview|datReview)\w*\.|(btnWorkspaceSource|lblWorkspaceSource)\.|scrShell\.OnVisible$)') {
        if (!$engine.Parse($formulas[$key], $options).IsSuccess) { throw "Invalid Canvas formula at $key." }
        $assertions++
    }
}
if ($formulas['btnReviewObject.OnSelect'] -notmatch 'Set\(gblSelectedRecordId, reviewTarget.ID\)' -or
    $formulas['scrShell.OnVisible'] -notmatch 'Select\(lblRecordLoad\)' -or
    $formulas['btnReviewEvidence.OnSelect'] -notmatch 'evidenceTargetType: reviewType, evidenceTargetId: reviewTarget.ID') {
    throw 'Review links must reuse the native record loader and the typed Evidence route.'
}
$assertions += 3

$objects = Read-Formula @'
Table(
  {ID:1, IsActive:true, NextReviewDate:Date(2026,11,1)},
  {ID:2, IsActive:true, NextReviewDate:Date(2026,12,19)},
  {ID:3, IsActive:false, NextReviewDate:Date(2026,11,19)},
  {ID:4, IsActive:true, NextReviewDate:Date(2026,12,20)},
  {ID:5, IsActive:true, NextReviewDate:If(false, Date(2026,11,19), Blank())},
  {ID:6, IsActive:true, NextReviewDate:Date(1900,1,1)}
)
'@
$dueStart = [regex]::Match($formulas['btnWorkspaceSource.OnSelect'], 'reviewDueFrom:\s*(Date\([\d, ]+\))')
if (!$dueStart.Success) { throw 'The delegated query requires a date-only lower bound.' }
$engine.UpdateVariable('reviewDueFrom', (Read-Formula $dueStart.Groups[1].Value))
$engine.UpdateVariable('reviewDueBefore', (Read-Formula 'Date(2026,12,20)'))
$engine.UpdateVariable('gblPilotObjectRoutes', (Read-Formula 'Table({ObjectTypeKey:"Asset"}, {ObjectTypeKey:"Change"}, {ObjectTypeKey:"Risk"})'))
foreach ($type in @('Asset', 'Change', 'Risk')) {
    $list = $type + 's'
    $items = $formulas["galDue$list.Items"].Replace('Self.Visible', 'reviewGalleryVisible')
    $engine.UpdateVariable($list, $objects)
    $engine.UpdateVariable('reviewGalleryVisible', $true)
    $engine.UpdateVariable('reviewLookupId', 0)
    Assert-Formula "CountRows($items)" 2
    Assert-Formula "First($items).ID" 1
    Assert-Formula "Last($items).ID" 2
    $engine.UpdateVariable('reviewLookupId', 4)
    Assert-Formula "First($items).ID" 4
    $engine.UpdateVariable('reviewLookupId', 5)
    Assert-Formula "First($items).ID" 5
    $engine.UpdateVariable('reviewGalleryVisible', $false)
    Assert-Formula "CountRows($items)" 0
}

$history = $formulas['galReviewHistory.Items'].Replace('Self.Visible', 'reviewGalleryVisible')
$engine.UpdateVariable('reviewGalleryVisible', $true)
$engine.UpdateVariable('reviewTarget', (Read-Formula '{ID:7}'))
$engine.UpdateVariable('Reviews', (Read-Formula @'
Table(
  {ID:31, ReviewedItemID:7, ReviewedObjectType:{Value:"Risiko"}, ReviewDate:Date(2026,10,1)},
  {ID:32, ReviewedItemID:7, ReviewedObjectType:{Value:"Asset"}, ReviewDate:Date(2026,10,2)},
  {ID:33, ReviewedItemID:7, ReviewedObjectType:{Value:"Change"}, ReviewDate:Date(2026,10,3)},
  {ID:34, ReviewedItemID:7, ReviewedObjectType:{Value:"Risiko"}, ReviewDate:Date(2026,10,4)},
  {ID:35, ReviewedItemID:8, ReviewedObjectType:{Value:"Risiko"}, ReviewDate:Date(2026,10,5)}
)
'@))
foreach ($case in @(@('Asset', 1, 32), @('Change', 1, 33), @('Risk', 2, 34), @('System', 0, 0))) {
    $engine.UpdateVariable('reviewType', $case[0])
    Assert-Formula "CountRows($history)" $case[1]
    if ($case[1] -gt 0) { Assert-Formula "First($history).ID" $case[2] }
}
$engine.UpdateVariable('reviewType', 'Risk')
$engine.UpdateVariable('gblPilotObjectRoutes', (Read-Formula 'Table({ObjectTypeKey:"Asset"})'))
Assert-Formula "CountRows($history)" 0
$engine.UpdateVariable('gblPilotObjectRoutes', (Read-Formula 'Table({ObjectTypeKey:"Asset"}, {ObjectTypeKey:"Change"}, {ObjectTypeKey:"Risk"})'))
$engine.UpdateVariable('decisionActionVisible', $true)
$engine.UpdateVariable('decisionBusy', $false)
$engine.UpdateVariable('gblAssetPilotCanWrite', $true)
$engine.UpdateVariable('decisionTargetId', 7)
$engine.UpdateVariable('decisionTargetType', 'Asset')
$engine.UpdateVariable('decisionStage', 'editing')
$engine.UpdateVariable('decisionDue', '2099-05-14')
$engine.UpdateVariable('drpReviewDecision', (Read-Formula '{Selected:{ChoiceKey:"ReviewResult:Updated"}}'))
$displayMode = $formulas['btnReviewSubmit.DisplayMode'].Replace('Self.Visible', 'decisionActionVisible').
    Replace('DisplayMode.Disabled', '"Disabled"').Replace('DisplayMode.Edit', '"Edit"')
foreach ($case in @(@(13, 'Disabled'), @(14, 'Disabled'), @(15, 'Edit'))) {
    $engine.UpdateVariable('datReviewNextDue', (Read-Formula "{SelectedDate:Date(2099,5,$($case[0]))}"))
    Assert-Formula $displayMode $case[1]
}
$engine.UpdateVariable('gblAssetPilotCanWrite', $false)
Assert-Formula $displayMode 'Disabled'
$engine.UpdateVariable('gblAssetPilotCanWrite', $true)
$engine.UpdateVariable('decisionBusy', $true)
Assert-Formula $displayMode 'Disabled'

$submit = $formulas['btnReviewSubmit.OnSelect']
$requestStart = $submit.IndexOf('With(')
$requestEnd = $submit.IndexOf('UpdateContext(', $requestStart)
$requestExpression = $submit.Substring($requestStart, $requestEnd - $requestStart) +
    'requestMode & "|" & requestDue & "|" & requestETag & "|" & requestOutcome & "|" & requestNextDue)'
if ($submit -notmatch 'GPCompleteReview\.Run\(decisionTargetId, decisionTargetType, requestMode,\s*requestDue, requestETag, requestOutcome, requestNextDue\)' -or
    $submit -notmatch 'retryMode: requestMode, retryDue: requestDue,\s*retryETag: requestETag, retryOutcome: requestOutcome, retryNextDue: requestNextDue') {
    throw 'The Flow call and the saved retry must use the same typed inputs.'
}
$assertions += 2
$engine.UpdateVariable('decisionRevision', '"item-42,3"')
$engine.UpdateVariable('datReviewNextDue', (Read-Formula '{SelectedDate:Date(2099,5,15)}'))
$engine.UpdateVariable('retryMode', 'save')
$engine.UpdateVariable('retryDue', '2099-05-14')
$engine.UpdateVariable('retryETag', '"item-42,3"')
$engine.UpdateVariable('retryOutcome', 'Updated')
$engine.UpdateVariable('retryNextDue', '2099-05-15')
foreach ($case in @(
    @('prepare', 'prepare|-|-|-|-'),
    @('editing', 'save|2099-05-14|"item-42,3"|Updated|2099-05-15'),
    @('resume', 'resume|2099-05-14|-|-|-'),
    @('uncertain', 'save|2099-05-14|"item-42,3"|Updated|2099-05-15')
)) {
    $engine.UpdateVariable('decisionStage', $case[0])
    Assert-Formula $requestExpression $case[1]
}
Write-Host "Canvas review read contract passed ($assertions assertions)."
