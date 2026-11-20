[CmdletBinding()]
param(
    [string]$RepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')),
    [switch]$CheckOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $RepositoryRoot 'provisioning/Modules/Model.psm1') -Force
$model = Get-GPArchitectureModel -Root (Join-Path $RepositoryRoot 'provisioning')
Test-GPArchitectureModel $model | Out-Null
function FxString([string]$Value) { '"' + $Value.Replace('"','""') + '"' }
$ratings = @($model.RiskPilot.ratingScale | ForEach-Object {
    '          {ChoiceKey: ' + (FxString $_.choiceKey) + ', Weight: ' + $_.weight + '}'
})
$bands = @($model.RiskPilot.scoreBands | ForEach-Object {
    '          {LevelKey: ' + (FxString $_.key) + ', DisplayNameDE: ' + (FxString $_.displayNameDE) + ', Minimum: ' + $_.minimum + ', Maximum: ' + $_.maximum + '}'
})
$transitions = @(
    foreach ($state in ($model.StatusModels | Where-Object key -eq 'Risk').states) {
        foreach ($target in $state[4]) {
            '          {FromKey: ' + (FxString "RiskStatus:$($state[0])") + ', ToKey: ' + (FxString "RiskStatus:$target") + '}'
        }
    }
)
$block = @"
      /* BEGIN GENERATED RISK PILOT RUNTIME - DO NOT EDIT */
      Set(gblRiskOriginalStatusKey, "");
      Set(gblRiskOriginalOwnerClaims, "");
      Set(gblRiskDecision, "");
      Set(gblRiskActorClaims, "");
      ClearCollect(colRiskRatingScale,
$($ratings -join ",`n")
      );
      ClearCollect(colRiskScoreBands,
$($bands -join ",`n")
      );
      ClearCollect(colRiskTransitions,
$($transitions -join ",`n")
      );
      /* END GENERATED RISK PILOT RUNTIME */
"@
$path = Join-Path $RepositoryRoot 'powerplatform/canvas/GovernancePortal/Src/App.pa.yaml'
$source = [IO.File]::ReadAllText($path).Replace("`r`n","`n")
$block = $block.Replace("`r`n","`n")
$pattern = '(?s)      /\* BEGIN GENERATED RISK PILOT RUNTIME - DO NOT EDIT \*/.*?      /\* END GENERATED RISK PILOT RUNTIME \*/'
$match = [regex]::Match($source,$pattern)
if ($CheckOnly) {
    if (-not $match.Success -or $match.Value -cne $block) { throw 'Risk pilot runtime differs from leading risk policy/status model. Run Sync-RiskPilotRuntime.ps1.' }
    Write-Host 'Risk pilot runtime matches leading architecture; no native connector or capability is synthesized.'
    return
}
if ($match.Success) { $source = $source.Substring(0,$match.Index) + $block + $source.Substring($match.Index+$match.Length) }
else {
    $anchor = '      /* BEGIN GENERATED OBJECT PROVIDER RUNTIME - DO NOT EDIT */'
    if (-not $source.Contains($anchor)) { throw 'Canonical App runtime anchor missing.' }
    $source = $source.Replace($anchor,$block + "`n`n" + $anchor)
}
[IO.File]::WriteAllText($path,$source,[Text.UTF8Encoding]::new($false))
Write-Host 'Risk pilot runtime generated into the canonical App source. No tenant access.'
