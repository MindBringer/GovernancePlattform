[CmdletBinding()]
param(
    [string]$RepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')),
    [Parameter(Mandatory)][string]$PowerFxDirectory
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$canvas = Join-Path $RepositoryRoot 'powerplatform/canvas/GovernancePortal'
$screen = Get-Content (Join-Path $canvas 'Src/scrAssetEvidence.pa.yaml') -Raw
$upload = Get-Content (Join-Path $canvas 'Src/scrAssetEvidenceUpload.pa.yaml') -Raw
$shell = Get-Content (Join-Path $canvas 'Src/scrShell.pa.yaml') -Raw
$app = Get-Content (Join-Path $canvas 'Src/App.pa.yaml') -Raw
if ($app -notmatch '(?m)^    StartScreen: =scrShell\r?$') {
    throw 'Adding an Evidence screen must retain the normal scrShell launch route.'
}

function Get-ControlFormula([string]$Source, [string]$Control, [string]$Property) {
    $match = [regex]::Match($Source, "(?m)^(?<indent> *)- ${Control}:\r?\n")
    if (!$match.Success) { throw "Missing Canvas control $Control" }
    $remaining = $Source.Substring($match.Index + $match.Length)
    $indent = $match.Groups['indent'].Length
    $next = [regex]::Match($remaining, "(?m)^ {0,$indent}- \w+:")
    if ($next.Success) { $remaining = $remaining.Substring(0, $next.Index) }
    $block = [regex]::Match($remaining, "(?m)^(?<indent> *)${Property}: \|-\r?\n(?<formula>(?:\k<indent> +[^\r\n]*\r?\n|\r?\n)+)")
    if ($block.Success) { return $block.Groups['formula'].Value.Trim().TrimStart('=') }
    $inline = [regex]::Match($remaining, "(?m)^ *${Property}: =(?<formula>[^\r\n]+)")
    if ($inline.Success) { return $inline.Groups['formula'].Value.Trim() }
    throw "Missing Canvas formula $Control.$Property"
}

$items = Get-ControlFormula $screen galAssetEvidence Items
$details = Get-ControlFormula $screen btnEvidenceDetails OnSelect
$canOpen = (Get-ControlFormula $screen btnEvidenceOpen DisplayMode).Replace('DisplayMode.Edit', '"Edit"').Replace('DisplayMode.Disabled', '"Disabled"')
$open = Get-ControlFormula $screen btnEvidenceOpen OnSelect
$readUploadVisible = Get-ControlFormula $screen btnEvidenceUploadOpen Visible
$controlLinkVisible = Get-ControlFormula $screen btnEvidenceLinkControl Visible
$controlLinkOpen = Get-ControlFormula $screen btnEvidenceLinkControl OnSelect
$uploadVisible = Get-ControlFormula $upload frmEvidenceUpload Visible
$entries = foreach ($type in 'Asset','Change','Risk') {
    $entry = Get-ControlFormula $shell "btn${type}Evidence" OnSelect
    if ($entry -notmatch 'Navigate\(scrAssetEvidence, ScreenTransition.None,' -or
        $entry -notmatch ('evidenceTargetType: "' + $type + '", evidenceTargetId: ThisItem.ID')) {
        throw "Evidence entry must use the selected native $type type and ID."
    }
    $entry
}
$lookup = [regex]::Match($details, 'LookUp\(Evidence, ID = sourceId\)').Value

if (!$lookup -or $screen -match '\b(Patch|Collect|SubmitForm|Remove|UpdateIf)\s*\(') {
    throw 'Evidence read must resolve a single native library ID and stay read-only.'
}
if ($open -notmatch 'If\(\s*Self.DisplayMode = DisplayMode.Edit,\s*Launch\(evidenceDocument\.\x27\{Link\}\x27') {
    throw 'Opening a document requires the validated library Link.'
}

foreach ($dll in 'Microsoft.PowerFx.Core.dll', 'Microsoft.PowerFx.Interpreter.dll') {
    [void][Reflection.Assembly]::LoadFrom((Join-Path $PowerFxDirectory $dll))
}
$engine = [Microsoft.PowerFx.RecalcEngine]::new()
$options = [Microsoft.PowerFx.ParserOptions]::new()
$options.Culture = [Globalization.CultureInfo]::InvariantCulture
$options.AllowsSideEffects = $true

function Invoke-Formula([string]$Formula) {
    $value = $engine.Eval($Formula, $null, $options)
    if ($value -is [Microsoft.PowerFx.Types.ErrorValue]) {
        throw "Power Fx failed: $Formula"
    }
    return $value
}
function Assert-Formula([string]$Formula, $Expected, [string]$Scenario) {
    $actual = (Invoke-Formula $Formula).ToObject()
    if ($actual -cne $Expected) {
        throw "${Scenario}: expected '$Expected', got '$actual'."
    }
    $script:assertions++
}
foreach ($formula in ($entries + @($details, $open, $controlLinkOpen, (Get-ControlFormula $upload btnEvidenceUpload OnSelect)))) {
    $parsed = $engine.Parse($formula, $options)
    if (!$parsed.IsSuccess) { throw "Invalid behavior formula: $formula" }
}

$assertions = 0
$engine.UpdateVariable('GovernanceRelations', (Invoke-Formula @'
Table(
    {TargetItemID:3001, TargetObjectTypeKey:"Asset", SourceItemID:7001, SourceObjectTypeKey:"Evidence", RelationTypeKey:"EvidenceSupportsObject", IsActive:true},
    {TargetItemID:3001, TargetObjectTypeKey:"Asset", SourceItemID:7002, SourceObjectTypeKey:"Evidence", RelationTypeKey:"EvidenceSupportsObject", IsActive:true},
    {TargetItemID:3001, TargetObjectTypeKey:"Risk", SourceItemID:7003, SourceObjectTypeKey:"Evidence", RelationTypeKey:"EvidenceSupportsObject", IsActive:true},
    {TargetItemID:3001, TargetObjectTypeKey:"Asset", SourceItemID:7004, SourceObjectTypeKey:"Policy", RelationTypeKey:"EvidenceSupportsObject", IsActive:true},
    {TargetItemID:3001, TargetObjectTypeKey:"Asset", SourceItemID:7005, SourceObjectTypeKey:"Evidence", RelationTypeKey:"DocumentGovernsObject", IsActive:true},
    {TargetItemID:3001, TargetObjectTypeKey:"Asset", SourceItemID:7006, SourceObjectTypeKey:"Evidence", RelationTypeKey:"EvidenceSupportsObject", IsActive:false},
    {TargetItemID:3002, TargetObjectTypeKey:"Asset", SourceItemID:7007, SourceObjectTypeKey:"Evidence", RelationTypeKey:"EvidenceSupportsObject", IsActive:true},
    {TargetItemID:0, TargetObjectTypeKey:"Asset", SourceItemID:7008, SourceObjectTypeKey:"Evidence", RelationTypeKey:"EvidenceSupportsObject", IsActive:true},
    {TargetItemID:3001, TargetObjectTypeKey:"Change", SourceItemID:7009, SourceObjectTypeKey:"Evidence", RelationTypeKey:"EvidenceSupportsObject", IsActive:true},
    {TargetItemID:3001, TargetObjectTypeKey:"System", SourceItemID:7010, SourceObjectTypeKey:"Evidence", RelationTypeKey:"EvidenceSupportsObject", IsActive:true},
    {TargetItemID:3001, TargetObjectTypeKey:"Control", SourceItemID:7011, SourceObjectTypeKey:"Evidence", RelationTypeKey:"EvidenceSupportsObject", IsActive:true},
    {TargetItemID:3001, TargetObjectTypeKey:"Control", SourceItemID:7012, SourceObjectTypeKey:"Risk", RelationTypeKey:"RiskMitigatedByControl", IsActive:true}
)
'@))
$engine.UpdateVariable('evidenceTargetId', 3001)
$engine.UpdateVariable('evidenceTargetType', 'Asset')
Assert-Formula "CountRows($items)" 2 'Matches only active Evidence relations on this Asset'
Assert-Formula "First($items).SourceItemID" 7001 'Keeps native library ID'
foreach ($case in @(
    @{Type='Risk'; FileId=7003},
    @{Type='Change'; FileId=7009},
    @{Type='Control'; FileId=7011}
)) {
    $engine.UpdateVariable('evidenceTargetType', $case.Type)
    Assert-Formula "CountRows($items)" 1 "$($case.Type) with the same native ID has its own relation"
    Assert-Formula "First($items).SourceItemID" $case.FileId "Resolves only the $($case.Type) file"
}
$engine.UpdateVariable('evidenceTargetType', 'System')
Assert-Formula "IsBlank($items)" $true 'No query for an unsupported object type'
$engine.UpdateVariable('evidenceTargetType', 'Asset')
$engine.UpdateVariable('evidenceTargetId', 3002)
Assert-Formula "CountRows($items)" 1 'Switching Asset drops earlier relations'
Assert-Formula "First($items).SourceItemID" 7007 'Shows only the second Asset relation'
$engine.UpdateVariable('evidenceTargetId', 0)
Assert-Formula "IsBlank($items)" $true 'No query for invalid Asset ID'

$engine.UpdateVariable('gblPilotObjectRoutes', (Invoke-Formula 'Table({ObjectTypeKey:"Asset"}, {ObjectTypeKey:"Change"}, {ObjectTypeKey:"Risk"})'))
foreach ($case in @(
    @{Type='Asset'; Id=3001; Writer=$true; Allowed=$true},
    @{Type='Change'; Id=3001; Writer=$true; Allowed=$true},
    @{Type='Risk'; Id=3001; Writer=$true; Allowed=$true},
    @{Type='Change'; Id=3001; Writer=$false; Allowed=$false},
    @{Type='Risk'; Id=3001; Writer=$false; Allowed=$false},
    @{Type='Asset'; Id=3001; Writer=$false; Allowed=$false},
    @{Type='System'; Id=3001; Writer=$true; Allowed=$false},
    @{Type='Risk'; Id=0; Writer=$true; Allowed=$false},
    @{Type='Control'; Id=3001; Writer=$true; Allowed=$false}
)) {
    $engine.UpdateVariable('evidenceTargetType', $case.Type)
    $engine.UpdateVariable('evidenceTargetId', [int]$case.Id)
    $engine.UpdateVariable('evidenceUploadTargetType', $case.Type)
    $engine.UpdateVariable('evidenceUploadTargetId', [int]$case.Id)
    $engine.UpdateVariable('gblAssetPilotCanWrite', $case.Writer)
    Assert-Formula $readUploadVisible $case.Allowed "Upload entry for $($case.Type) ID $($case.Id) writer=$($case.Writer)"
    Assert-Formula $uploadVisible $case.Allowed "Upload form for $($case.Type) ID $($case.Id) writer=$($case.Writer)"
}
$engine.UpdateVariable('evidenceTargetType', 'Control')
$engine.UpdateVariable('evidenceTargetId', 3001)
$engine.UpdateVariable('evidenceControlCanEdit', $true)
$engine.UpdateVariable('evidenceControlRevision', '"5"')
Assert-Formula $controlLinkVisible $true 'Control editor with native permission and revision can link an existing file'
$engine.UpdateVariable('evidenceControlRevision', '')
Assert-Formula $controlLinkVisible $false 'Missing native revision prevents linking an existing file'
$engine.UpdateVariable('evidenceControlRevision', '"5"')
$engine.UpdateVariable('gblAssetPilotCanWrite', $false)
Assert-Formula $controlLinkVisible $false 'Control reader cannot link an existing file'
$engine.UpdateVariable('gblAssetPilotCanWrite', $true)
$engine.UpdateVariable('evidenceTargetType', 'Risk')
$engine.UpdateVariable('evidenceUploadTargetType', 'Risk')
$engine.UpdateVariable('gblPilotObjectRoutes', (Invoke-Formula 'Table({ObjectTypeKey:"Asset"}, {ObjectTypeKey:"Change"})'))
$engine.UpdateVariable('evidenceTargetId', 3001)
$engine.UpdateVariable('evidenceUploadTargetId', 3001)
Assert-Formula $readUploadVisible $false 'Risk upload entry respects the configured routes'
Assert-Formula $uploadVisible $false 'Risk upload form respects the configured routes'

$engine.UpdateVariable('Evidence', (Invoke-Formula @'
Table(
    {ID:7001, '{IsFolder}':false, '{Link}':"https://example.invalid/file", '{VersionNumber}':"2.0"},
    {ID:7002, '{IsFolder}':true, '{Link}':"https://example.invalid/folder", '{VersionNumber}':""},
    {ID:7003, '{IsFolder}':false, '{Link}':"", '{VersionNumber}':"1.0"},
    {ID:7004, '{IsFolder}':false, '{Link}':"http://example.invalid/file", '{VersionNumber}':"1.0"}
)
'@))
$engine.UpdateVariable('evidenceLookupBusy', $false)
$engine.UpdateVariable('evidenceLookupError', '')
$engine.UpdateVariable('gblRecordError', '')
foreach ($case in @(
    @{ID=7001; Mode='Edit'; Note='Readable HTTPS document'},
    @{ID=7002; Mode='Disabled'; Note='Folder'},
    @{ID=7003; Mode='Disabled'; Note='Missing document link'},
    @{ID=7004; Mode='Disabled'; Note='Non-HTTPS link'},
    @{ID=7099; Mode='Disabled'; Note='Missing or invisible native ID'}
)) {
    $engine.UpdateVariable('sourceId', [int]$case.ID)
    $engine.UpdateVariable('evidenceDocument', (Invoke-Formula $lookup))
    Assert-Formula $canOpen $case.Mode $case.Note
}

$engine.UpdateVariable('sourceId', 7001)
$engine.UpdateVariable('evidenceDocument', (Invoke-Formula $lookup))
$engine.UpdateVariable('evidenceLookupBusy', $true)
Assert-Formula $canOpen 'Disabled' 'Pending document lookup'
$engine.UpdateVariable('evidenceLookupBusy', $false)
$engine.UpdateVariable('evidenceLookupError', 'Synthetic denied request')
Assert-Formula $canOpen 'Disabled' 'File lookup failure'
$engine.UpdateVariable('evidenceLookupError', '')
$engine.UpdateVariable('gblRecordError', 'Synthetic query failure')
Assert-Formula $canOpen 'Disabled' 'Relations read failure'

Write-Host "Evidence passed: $assertions assertions on the actual Power Fx filters, upload role checks, native ID lookup and link guards."
