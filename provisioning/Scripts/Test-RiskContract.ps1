[CmdletBinding()]
param([string]$PlanPath, [string]$NativeSnapshotPath)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Import-Module "$root/provisioning/Modules/Model.psm1" -Force
Import-Module "$root/provisioning/Modules/Compiler.psm1" -Force
$model=Get-GPArchitectureModel -Root "$root/provisioning"
Test-GPArchitectureModel $model | Out-Null
$baseline=Get-GPArchitectureModel -Root "$root/provisioning"
$addedNames=@('Title','LinkedAsset','RiskStatus')
$baseline.ObjectFields=@($baseline.ObjectFields|Where-Object {-not ($_.objectTypeKey -eq 'Risk' -and $_.internalName -in $addedNames)})
foreach($f in @($baseline.ObjectFields|Where-Object objectTypeKey -eq 'Risk')){$f.Remove('editorReadOnly')}
$baseline.ChoiceSets=@($baseline.ChoiceSets|Where-Object key -notin @('RiskStatus','RiskSourceChannel'))
$baseline.ObjectFieldOverrides=@()
($baseline.objectTypes|Where-Object key -eq 'Risk').allowVersioning=$false
$schema=Compile-GPArchitecture $model
$oldSchema=Compile-GPArchitecture $baseline
$risk=@($schema.Lists|Where-Object ObjectKey -eq 'Risk')[0]
$oldRisk=@($oldSchema.Lists|Where-Object ObjectKey -eq 'Risk')[0]
if(!$risk.Settings.Versioning -or $risk.Fields.Count -ne $oldRisk.Fields.Count+3){throw 'Risk must add exactly three modeled fields and versioning.'}
$title=@($risk.Fields|Where-Object InternalName -eq 'Title')[0]
$lookup=@($risk.Fields|Where-Object InternalName -eq 'LinkedAsset')[0]
$status=@($risk.Fields|Where-Object InternalName -eq 'RiskStatus')[0]
if($title.Type -ne 'Text' -or !$title.Required -or $title.maxLength -ne 255){throw 'Risk native Title must be required Text/255.'}
if($lookup.Type -ne 'Lookup' -or $lookup.LookupList -ne 'Assets' -or $lookup.Required -or $lookup.Indexed){throw 'Risk asset link must be optional, single and unindexed.'}
if($status.Type -ne 'Choice' -or $status.ChoiceSet -ne 'RiskStatus' -or $status.Required -or $status.Indexed -or $status.default -cne 'RiskStatus:Identified'){throw 'Invalid Risk status field/default.'}
$states=@(($model.StatusModels|Where-Object key -eq 'Risk').states)
$choices=@(($model.ChoiceSets|Where-Object key -eq 'RiskStatus').values)
if($states.Count -ne 5 -or $choices.Count -ne 5){throw 'All five existing Risk states must be preserved.'}
for($i=0;$i -lt $states.Count;$i++){
    if($states[$i][0] -cne $choices[$i][0] -or $states[$i][1] -cne $choices[$i][1] -or $status.Choices[$i] -cne $states[$i][1] -or $choices[$i][2] -ne ($i+1)*10){throw 'Risk status model, stable keys and native labels differ.'}
}
if(@($model.RiskPilot.pilotFields|Sort-Object -Unique).Count -ne 16){throw 'Risk pilot must name 16 distinct fields.'}
foreach($name in $model.RiskPilot.pilotFields){if(@($risk.Fields|Where-Object InternalName -eq $name).Count -ne 1){throw "Risk pilot field absent/duplicate: $name"}}
foreach($old in $oldSchema.Lists){
    $new=@($schema.Lists|Where-Object ObjectKey -eq $old.ObjectKey)[0]
    if($new.Fields.Count -ne $old.Fields.Count+$(if($old.ObjectKey -eq 'Risk'){3}else{0})){throw "Unexpected field delta on $($old.ObjectKey)"}
    foreach($f in $old.Fields){
        $actual=@($new.Fields|Where-Object InternalName -eq $f.InternalName)
        $expected=@{}+$f
        if($old.ObjectKey -ceq 'Risk' -and $f.InternalName -ceq 'SourceChannel'){
            $expected.Type='Choice';$expected.ChoiceSet='RiskSourceChannel';$expected.Choices=@('Canvas App','Power Automate','Import','API','SharePoint','System')
        }
        if($old.ObjectKey -ceq 'Risk' -and $f.InternalName -ceq 'LastValidationAt'){$expected.Indexed=$true}
        if($actual.Count -ne 1 -or $actual[0].Count -ne $expected.Count){throw 'Existing field removed or unexpectedly reshaped.'}
        foreach($k in $expected.Keys){if(($actual[0][$k]|ConvertTo-Json -Depth 20) -cne ($expected[$k]|ConvertTo-Json -Depth 20)){throw "Unexpected native field delta: $($old.ObjectKey).$($f.InternalName).$k"}}
    }
    if($old.ContainsKey('Settings')){foreach($k in $old.Settings.Keys){$expected=if($old.ObjectKey -eq 'Risk' -and $k -eq 'Versioning'){$true}else{$old.Settings[$k]};if($new.Settings[$k] -ne $expected){throw 'Unexpected list setting delta.'}}}
}
# Reject policy regressions in the leading model, independently of Canvas code.
foreach($case in @('duplicate-rating','missing-band','overlap-band','actor','implicit-decision','readonly-string')){
    $bad=Get-GPArchitectureModel -Root "$root/provisioning"
    switch($case){
        'duplicate-rating' {$bad.RiskPilot.ratingScale[1].choiceKey=$bad.RiskPilot.ratingScale[0].choiceKey}
        'missing-band' {$bad.RiskPilot.scoreBands=@($bad.RiskPilot.scoreBands|Select-Object -Skip 1)}
        'overlap-band' {$bad.RiskPilot.scoreBands[1].minimum=4}
        'actor' {$bad.RiskPilot.acceptance.actor='display-name'}
        'implicit-decision' {$bad.RiskPilot.acceptance.requiresExplicitDecision=$false}
        'readonly-string' {($bad.ObjectFields|Where-Object {$_.objectTypeKey -eq 'Risk' -and $_.internalName -eq 'RiskScore'}).editorReadOnly='false'}
    }
    $rejected=$false;try{Test-GPArchitectureModel $bad|Out-Null}catch{$rejected=$true}
    if(!$rejected){throw "Invalid risk policy accepted: $case"}
}
# Resolve into copies, preserving the raw shared base fields and all caller state.
$rawBefore=$model.Fields|ConvertTo-Json -Depth 30
$resolvedRisk=@(Get-GPObjectFields -ObjectTypeKey Risk -Model $model)
$resolvedAsset=@(Get-GPObjectFields -ObjectTypeKey Asset -Model $model)
if(($resolvedRisk|Where-Object internalName -eq SourceChannel).type -cne 'Choice' -or !($resolvedRisk|Where-Object internalName -eq LastValidationAt).indexed -or ($resolvedAsset|Where-Object internalName -eq SourceChannel).type -cne 'Text' -or ($resolvedAsset|Where-Object internalName -eq LastValidationAt).indexed){throw 'Inherited field variant leaked outside Risk.'}
($resolvedRisk|Where-Object internalName -eq SourceChannel).type='Text'
if(($model.Fields|ConvertTo-Json -Depth 30) -cne $rawBefore -or ((Get-GPObjectFields -ObjectTypeKey Risk -Model $model)|Where-Object internalName -eq SourceChannel).type -cne 'Choice'){throw 'Field resolution mutated caller/shared state.'}
$overrideCases=@('unknown-object','unknown-base-field','duplicate','identity-property','string-index','unsupported-type','missing-choice','duplicate-choice','wrong-version')
foreach($case in $overrideCases){
    $bad=Get-GPArchitectureModel -Root "$root/provisioning"
    switch($case){
        'unknown-object' {$bad.ObjectFieldOverrides[0].objectTypeKey='Missing'}
        'unknown-base-field' {$bad.ObjectFieldOverrides[0].internalName='Missing'}
        'duplicate' {$bad.ObjectFieldOverrides+=@($bad.ObjectFieldOverrides[0])}
        'identity-property' {$bad.ObjectFieldOverrides[0].required=$true}
        'string-index' {$bad.ObjectFieldOverrides[1].indexed='true'}
        'unsupported-type' {$bad.ObjectFieldOverrides[0].type='Text'}
        'missing-choice' {$bad.ObjectFieldOverrides[0].choiceSet='Missing'}
        'duplicate-choice' {($bad.ChoiceSets|Where-Object key -eq RiskSourceChannel).values[1][0]='CanvasApp'}
        'wrong-version' {$bad.FieldOverrideSchemaVersion=2}
    }
    $rejected=$false;try{Test-GPArchitectureModel $bad|Out-Null}catch{$rejected=$true}
    if(!$rejected){throw "Invalid inherited field variant accepted: $case"}
    $compilerRejected=$false;try{Compile-GPArchitecture $bad|Out-Null}catch{$compilerRejected=$true}
    if(!$compilerRejected){throw "Invalid inherited field variant reached compilation: $case"}
}
function Test-NativeRiskSnapshot($Native,$RiskSchema){
    if($Native.List -cne 'Risks' -or !$Native.Settings.EnableVersioning){throw 'Native Risk identity/versioning contract differs.'}
    if(@($Native.Schema|Where-Object Indexed).Count -gt 20){throw 'Native Risk index budget exceeded; no index removal authorized.'}
    if((@($Native.Schema|Where-Object Required|ForEach-Object InternalName)|ConvertTo-Json -Compress) -cne (@($RiskSchema.Fields|Where-Object Required|ForEach-Object InternalName)|ConvertTo-Json -Compress)){throw 'Unexpected permanent native Risk required field.'}
    foreach($f in $RiskSchema.Fields){
        $actual=@($Native.Schema|Where-Object InternalName -CEQ $f.InternalName)
        if($actual.Count -eq 0 -and $f.InternalName -cin @('LinkedAsset','RiskStatus')){continue}
        if($actual.Count -ne 1 -or $actual[0].Required -ne $f.Required -or $actual[0].TypeAsString -cne $f.Type -or $actual[0].Indexed -ne $f.Indexed -or ($f.InternalName -cin $model.RiskPilot.pilotFields -and $actual[0].ReadOnlyField)){throw "Native Risk field drift: $($f.InternalName)"}
        [xml]$xml=$actual[0].SchemaXml
        if($xml.Field.GetAttribute('Name') -cne $f.InternalName -or $xml.Field.GetAttribute('Type') -cne $f.Type){throw "Native Risk XML identity/type drift: $($f.InternalName)"}
        if($f.Type -cin @('Choice','MultiChoice')){
            $labels=@($xml.Field.SelectNodes('CHOICES/CHOICE')|ForEach-Object InnerText)
            if(($labels|ConvertTo-Json -Compress) -cne ($f.Choices|ConvertTo-Json -Compress)){throw "Native Risk choices drift: $($f.InternalName)"}
        }
        if($f.Type -ceq 'DateTime'){
            $format=$xml.Field.GetAttribute('Format');if(!$format){$format='DateOnly'}
            $expected=if($f.ContainsKey('DateFormat')){$f.DateFormat}else{'DateOnly'}
            if($format -cne $expected){throw "Native Risk date precision drift: $($f.InternalName)"}
        }
        if($f.InternalName -ceq 'Title'){
            $max=$xml.Field.GetAttribute('MaxLength');if(!$max){$max='255'}
            if($max -cne '255'){throw 'Native Risk Title limit differs.'}
        }
    }
}
$fixture=Get-Content "$root/tests/fixtures/risk-native-contract.json" -Raw|ConvertFrom-Json -Depth 30
Test-NativeRiskSnapshot $fixture $risk
$nativeCases=@('source-type','source-label','source-choice-missing','required-field-missing','duplicate-field','required-flag','existing-index','readonly-score','date-precision','title-limit','versioning','index-budget','extra-required-field')
foreach($case in $nativeCases){
    $bad=$fixture|ConvertTo-Json -Depth 30|ConvertFrom-Json -Depth 30
    $source=$bad.Schema|Where-Object InternalName -eq SourceChannel
    switch($case){
        'source-type' {$source.TypeAsString='Text'}
        'source-label' {$source.SchemaXml=$source.SchemaXml.Replace('Canvas App','Other')}
        'source-choice-missing' {$source.SchemaXml=$source.SchemaXml.Replace('<CHOICE>API</CHOICE>','')}
        'required-field-missing' {$bad.Schema=@($bad.Schema|Where-Object InternalName -ne RiskOwner)}
        'duplicate-field' {$bad.Schema+=@($source)}
        'required-flag' {($bad.Schema|Where-Object InternalName -eq RiskOwner).Required=$true}
        'existing-index' {($bad.Schema|Where-Object InternalName -eq LastValidationAt).Indexed=$false}
        'readonly-score' {($bad.Schema|Where-Object InternalName -eq RiskScore).ReadOnlyField=$true}
        'date-precision' {($bad.Schema|Where-Object InternalName -eq RiskAcceptanceUntil).SchemaXml=($bad.Schema|Where-Object InternalName -eq RiskAcceptanceUntil).SchemaXml.Replace('DateOnly','DateTime')}
        'title-limit' {($bad.Schema|Where-Object InternalName -eq Title).SchemaXml='<Field Name="Title" Type="Text" MaxLength="254" />'}
        'versioning' {$bad.Settings.EnableVersioning=$false}
        'index-budget' {1..21|ForEach-Object {$bad.Schema+=@([pscustomobject]@{InternalName="Extra$_";Indexed=$true})}}
        'extra-required-field' {$bad.Schema+=@([pscustomobject]@{InternalName='Unexpected';Required=$true;Indexed=$false})}
    }
    $rejected=$false;try{Test-NativeRiskSnapshot $bad $risk}catch{$rejected=$true}
    if(!$rejected){throw "Invalid native Risk snapshot accepted: $case"}
}
$unreconciled=Get-GPArchitectureModel -Root "$root/provisioning";$unreconciled.ObjectFieldOverrides=@()
$unreconciledRisk=(Compile-GPArchitecture $unreconciled).Lists|Where-Object ObjectKey -eq Risk
$legacyRejected=$false;try{Test-NativeRiskSnapshot $fixture $unreconciledRisk}catch{$legacyRejected=$_.Exception.Message -match 'SourceChannel'}
if(!$legacyRejected){throw 'The original SourceChannel drift must still be rejected by the same native verifier.'}
$nativeIndexes=$null
if($NativeSnapshotPath){
    $native=Get-Content $NativeSnapshotPath -Raw|ConvertFrom-Json -Depth 35
    Test-NativeRiskSnapshot $native $risk
    $nativeIndexes=@($native.Schema|Where-Object Indexed).Count
}
$metadata=Import-Module "$root/provisioning/Modules/Metadata.psm1" -Force -PassThru
$schemaModule=Import-Module "$root/provisioning/Modules/Schema.psm1" -Force -PassThru
$oldContext=Get-Variable GPContext -Scope Global -ErrorAction SilentlyContinue
try{
    $global:GPContext=@{DryRun=$true;FieldGroup=$model.site.fieldGroup}
    & $metadata {
        function script:Write-GPLog {param($Message,$Level)}
        function script:Set-GPSeedRow {param([string]$List,[string]$KeyField,[hashtable]$Values);$script:Rows.Add([pscustomobject]@{List=$List;KeyField=$KeyField;Values=$Values})}
    }
    function Rows($m){& $metadata {param($m);$script:Rows=[Collections.Generic.List[object]]::new();Publish-GPMetadata -Model $m;$script:Rows.ToArray()} $m}
    $rows=@(Rows $model);$oldRows=@(Rows $baseline);$map=@{};$oldMap=@{}
    foreach($r in $rows){$key=$r.List+'/'+$r.Values[$r.KeyField];if($map.ContainsKey($key)){throw 'Duplicate generated metadata key.'};$map[$key]=$r.Values}
    foreach($r in $oldRows){$oldMap[$r.List+'/'+$r.Values[$r.KeyField]]=$r.Values}
    $added=@($rows|Where-Object {!$oldMap.ContainsKey($_.List+'/'+$_.Values[$_.KeyField])})
    $changes=[Collections.Generic.List[object]]::new()
    foreach($key in $oldMap.Keys){
        $old=$oldMap[$key];$actual=$map[$key]
        if($null -eq $actual -or $actual.Count -ne $old.Count){throw "Existing metadata removed/reshaped: $key"}
        $changed=$false
        foreach($k in $old.Keys){
            if([string]$actual[$k] -cne [string]$old[$k]){$changed=$true}
            $expected=if($key -eq 'ObjectTypes/Risk' -and $k -eq 'AllowVersioning'){$true}elseif($key -in @('FieldDefinitions/Risk:RiskScore','FieldDefinitions/Risk:RiskLevel','FieldDefinitions/Risk:RiskAcceptanceDate') -and $k -eq 'IsReadOnly'){$true}elseif($key -eq 'FieldDefinitions/Risk:SourceChannel' -and $k -in @('SharePointType','ControlType')){'Choice'}elseif($key -eq 'FieldDefinitions/Risk:SourceChannel' -and $k -eq 'ChoiceSetKey'){'RiskSourceChannel'}elseif($key -eq 'FieldDefinitions/Risk:LastValidationAt' -and $k -eq 'IsIndexed'){$true}else{$old[$k]}
            if([string]$actual[$k] -cne [string]$expected){throw "Unexpected existing metadata delta: $key.$k"}
        }
        if($changed){$changes.Add([pscustomobject]@{Key=$key;Values=$actual})}
    }
    if($added.Count -ne 17 -or $rows.Count -ne $oldRows.Count+17 -or $changes.Count -ne 6){throw "Expected 17 new and 6 updated metadata rows, got $($added.Count)/$($changes.Count)."}
    if($map['FormFieldDefinitions/Risk:Edit:Title'].RequiredIf -cne 'true' -or $map['FieldDefinitions/Risk:Title'].SortOrder -ne 0){throw 'Risk Title metadata must be first and required.'}
    foreach($name in $model.RiskPilot.derivedFields){if(!$map["FieldDefinitions/Risk:$name"].IsReadOnly){throw 'Derived Risk fields must be read-only in metadata.'}}
    $lookupXml=& $schemaModule {param($f) New-GPFieldXml -F $f -LookupListId '11111111-1111-1111-1111-111111111111'} $lookup
    $statusXml=& $schemaModule {param($f) New-GPFieldXml -F $f} $status
    [xml]$lx=$lookupXml;[xml]$sx=$statusXml
    if($lx.Field.Type -cne 'Lookup' -or $lx.Field.Indexed -cne 'FALSE' -or $lx.Field.ShowField -cne 'Title' -or $lx.Field.HasAttribute('Mult') -or $sx.Field.Type -cne 'Choice' -or $sx.Field.Indexed -cne 'FALSE' -or @($sx.Field.CHOICES.CHOICE).Count -ne 5){throw 'Invalid Risk prerequisite XML.'}
    $sourceField=$risk.Fields|Where-Object InternalName -eq SourceChannel
    $validationField=$risk.Fields|Where-Object InternalName -eq LastValidationAt
    [xml]$sourceXml=& $schemaModule {param($f) New-GPFieldXml -F $f} $sourceField
    [xml]$validationXml=& $schemaModule {param($f) New-GPFieldXml -F $f} $validationField
    if($sourceXml.Field.Type -cne 'Choice' -or (@($sourceXml.Field.CHOICES.CHOICE)|ConvertTo-Json -Compress) -cne (@('Canvas App','Power Automate','Import','API','SharePoint','System')|ConvertTo-Json -Compress) -or $validationXml.Field.Indexed -cne 'TRUE' -or $validationXml.Field.Format -cne 'DateOnly'){throw 'Inherited native Risk XML contracts differ.'}
    if($PlanPath){[ordered]@{status='prepared-not-authorized';sourceList='Risks';baselineFields=$oldRisk.Fields.Count;candidateFields=$risk.Fields.Count;existingNativeTitle='verify required Text/255; no new Title column';addFields=@(@{InternalName='LinkedAsset';XmlWithSyntheticLookupGuid=$lookupXml},@{InternalName='RiskStatus';Xml=$statusXml});newIndexes=0;nativeExistingIndexes=$nativeIndexes;existingFieldContractReconciliation=@(@{InternalName='SourceChannel';Type='Choice';ChoiceSet='RiskSourceChannel';NativeFieldWriteRequired=$false},@{InternalName='LastValidationAt';Indexed=$true;NativeFieldWriteRequired=$false});enableVersioning=$true;addMetadataRows=$added;updateMetadataRows=$changes;preservedMetadataRows=$oldRows.Count-6;connectorPrerequisite='Risks absent in current native reference: separate native readback, supported Studio connection/export, exact source/reference adoption approval; never synthesize metadata';activation='P4a leaves Risk capabilities false; native list/load/patch adapter follows verified binding'}|ConvertTo-Json -Depth 35|Set-Content $PlanPath -Encoding utf8}
    Write-Host "Risk prerequisite contract passed: 3 modeled fields, 2 unindexed additions, versioning; 17 new/6 updated metadata rows; $($oldRows.Count-6) rows unchanged; six invalid policies, nine invalid field variants and thirteen invalid native snapshots rejected; original SourceChannel drift still rejected. No tenant access."
}finally{
    if($oldContext){$global:GPContext=$oldContext.Value}else{Remove-Variable GPContext -Scope Global -ErrorAction SilentlyContinue}
    Remove-Module $metadata;Remove-Module $schemaModule
}
