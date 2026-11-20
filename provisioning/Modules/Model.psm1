
function Read-GPJsonYaml {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path)
    if(-not(Test-Path $Path)){throw "Architecture file not found: $Path"}
    try { return (Get-Content -Path $Path -Raw -Encoding utf8 | ConvertFrom-Json -Depth 100 -AsHashtable) }
    catch { throw "Architecture file '$Path' must be valid JSON-compatible YAML: $($_.Exception.Message)" }
}
function Get-GPArchitectureModel {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Root)
    $a=Join-Path $Root '../architecture'
    $model=Read-GPJsonYaml "$a/platform.yaml"
    $model.Fields=(Read-GPJsonYaml "$a/fields.yaml").fields
    $model.ObjectFields=(Read-GPJsonYaml "$a/object-fields.yaml").objectFields
    $fieldOverrides=Read-GPJsonYaml "$a/field-overrides.yaml"
    $model.FieldOverrideSchemaVersion=$fieldOverrides.schemaVersion
    $model.ObjectFieldOverrides=$fieldOverrides.objectFieldOverrides
    $model.ChoiceSets=(Read-GPJsonYaml "$a/choices.yaml").choiceSets
    $model.StatusModels=(Read-GPJsonYaml "$a/status-models.yaml").statusModels
    $model.RelationTypes=(Read-GPJsonYaml "$a/relations.yaml").relationTypes
    $model.Forms=(Read-GPJsonYaml "$a/forms.yaml").forms
    $model.Views=(Read-GPJsonYaml "$a/views.yaml").views
    $model.Workflows=(Read-GPJsonYaml "$a/workflows.yaml").workflows
    $ai=Read-GPJsonYaml "$a/ai.yaml"
    $model.AIPrompts=$ai.prompts
    $model.AISkills=$ai.skills
    $model.Permissions=(Read-GPJsonYaml "$a/permissions.yaml").permissions
    $canvas=Read-GPJsonYaml "$a/canvas-runtime.yaml"
    $model.Pages=$canvas.pages
    $model.NavigationDefinitions=$canvas.navigation
    $model.Dashboards=$canvas.dashboards
    $model.Widgets=$canvas.widgets
    $model.Commands=$canvas.commands
    $model.Validations=$canvas.validations
    $model.BusinessRules=$canvas.businessRules
    $model.TextResources=$canvas.textResources
    $model.Cleanup=Read-GPJsonYaml "$a/cleanup.yaml"
    $model.RiskPilot=Read-GPJsonYaml "$a/risk-pilot.yaml"
    $model.Migration=Read-GPJsonYaml (Join-Path $Root '../migration/v5-to-v6.yaml')
    return $model
}
# Resolve inherited field variants once for both schema compilation and runtime metadata.
# Copies preserve the raw base model and the established order of every form field.
function Get-GPObjectFields {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$ObjectTypeKey,[Parameter(Mandatory)][hashtable]$Model)
    if($Model.FieldOverrideSchemaVersion -ne 1){throw 'Invalid inherited field-override schema version.'}
    foreach($variant in @($Model.ObjectFieldOverrides)){
        if(@($Model.objectTypes|Where-Object key -CEQ $variant.objectTypeKey).Count -ne 1){throw "Unknown inherited field-override object '$($variant.objectTypeKey)'."}
    }
    $objects=@($Model.objectTypes|Where-Object key -CEQ $ObjectTypeKey)
    if($objects.Count -ne 1){throw "Unknown/duplicate field-override object '$ObjectTypeKey'."}
    $baseKeys=@($Model.baseClasses[$objects[0].baseClass].fields)
    $baseFields=@($Model.Fields|Where-Object {$baseKeys -contains $_.key})
    $fields=@($baseFields)+@($Model.ObjectFields|Where-Object objectTypeKey -CEQ $ObjectTypeKey)
    $resolved=[Collections.Generic.List[hashtable]]::new()
    foreach($f in $fields){$copy=@{};foreach($k in $f.Keys){$copy[$k]=$f[$k]};$resolved.Add($copy)}
    $seen=@{}
    foreach($variant in @($Model.ObjectFieldOverrides|Where-Object objectTypeKey -CEQ $ObjectTypeKey)){
        $name=$variant.internalName
        if($seen.ContainsKey($name)){throw "Duplicate inherited field override '$ObjectTypeKey.$name'."}
        $seen[$name]=$true
        $unknown=@($variant.Keys|Where-Object {$_ -cnotin @('objectTypeKey','internalName','type','choiceSet','indexed')})
        $base=@($baseFields|Where-Object internalName -CEQ $name)
        $target=@($resolved|Where-Object internalName -CEQ $name)
        if($unknown.Count -or $base.Count -ne 1 -or $target.Count -ne 1 -or $variant.Count -le 2){throw "Invalid inherited field override '$ObjectTypeKey.$name'."}
        if($variant.ContainsKey('indexed') -and $variant.indexed -isnot [bool]){throw "Non-Boolean inherited index flag '$ObjectTypeKey.$name'."}
        if($variant.ContainsKey('type') -and $variant.type -cne 'Choice'){throw "Only explicit Choice field variants are supported: '$ObjectTypeKey.$name'."}
        foreach($k in @('type','choiceSet','indexed')){if($variant.ContainsKey($k)){$target[0][$k]=$variant[$k]}}
        if($target[0].type -ceq 'Choice'){
            $sets=@($Model.ChoiceSets|Where-Object key -CEQ $target[0].choiceSet)
            if($sets.Count -ne 1 -or @($sets[0].values).Count -eq 0){throw "Unknown/empty inherited choice set '$ObjectTypeKey.$name'."}
            $values=@($sets[0].values)
            if(@($values|ForEach-Object {$_[0]}|Sort-Object -Unique).Count -ne $values.Count -or @($values|ForEach-Object {$_[1]}|Sort-Object -Unique).Count -ne $values.Count -or @($values|Where-Object {$_.Count -lt 3 -or [string]::IsNullOrWhiteSpace($_[0]) -or [string]::IsNullOrWhiteSpace($_[1])}).Count){throw "Invalid inherited choice values '$ObjectTypeKey.$name'."}
        }elseif($variant.ContainsKey('choiceSet')){throw "Choice set on non-Choice inherited field '$ObjectTypeKey.$name'."}
    }
    return $resolved.ToArray()
}
function Test-GPArchitectureModel {
    [CmdletBinding()]
    param([Parameter(Mandatory)][hashtable]$Model)
    $errors=[System.Collections.Generic.List[string]]::new()
    foreach($p in @('schemaVersion','platformName','baseClasses','objectTypes','technicalObjects')){
        if(-not $Model.ContainsKey($p)){ $errors.Add("Missing required model property '$p'.") }
    }
    $keys=@($Model.objectTypes|ForEach-Object{$_.key})
    foreach($d in ($keys|Group-Object|Where-Object Count -gt 1)){$errors.Add("Duplicate object type key '$($d.Name)'.")}
    $fieldKeys=@($Model.Fields|ForEach-Object{$_.key})
    foreach($bc in $Model.baseClasses.Keys){
        foreach($fk in $Model.baseClasses[$bc].fields){
            if($fieldKeys -notcontains $fk){$errors.Add("Base class '$bc' references unknown field '$fk'.")}
        }
    }
    $objectKeys=@($Model.objectTypes|ForEach-Object{$_.key})
    $objectSources=@($Model.objectTypes|ForEach-Object{$_.source})
    foreach($f in $Model.ObjectFields){
        if($objectKeys -notcontains $f.objectTypeKey){$errors.Add("Field '$($f.internalName)' references unknown object type '$($f.objectTypeKey)'.")}
        if($f.lookupObject -and $objectKeys -notcontains $f.lookupObject -and $objectSources -notcontains $f.lookupObject){
            $errors.Add("Field '$($f.objectTypeKey).$($f.internalName)' references unknown lookup object '$($f.lookupObject)'.")
        }
    }
    $choices=@($Model.ChoiceSets|ForEach-Object{$_.key})
    foreach($f in @($Model.Fields)+@($Model.ObjectFields)){
        if($f.ContainsKey('editorReadOnly') -and $f.editorReadOnly -isnot [bool]){$errors.Add("Field '$($f.internalName)' has non-Boolean editorReadOnly.")}
        if($f.choiceSet -and $choices -notcontains $f.choiceSet){$errors.Add("Field '$($f.internalName)' references unknown choice set '$($f.choiceSet)'.")}
        if($f.ContainsKey('dateFormat') -and ($f.type -cne 'DateTime' -or $f.dateFormat -isnot [string] -or $f.dateFormat -cnotin @('DateOnly','DateTime'))){
            $errors.Add("Field '$($f.internalName)' has invalid dateFormat; only DateOnly/DateTime on DateTime are supported.")
        }
    }
    if($Model.FieldOverrideSchemaVersion -ne 1){$errors.Add('Invalid inherited field-override schema version.')}
    foreach($variant in @($Model.ObjectFieldOverrides)){
        if(@($Model.objectTypes|Where-Object key -CEQ $variant.objectTypeKey).Count -ne 1){$errors.Add("Unknown inherited field-override object '$($variant.objectTypeKey)'.")}
    }
    foreach($o in $Model.objectTypes){try{Get-GPObjectFields -ObjectTypeKey $o.key -Model $Model|Out-Null}catch{$errors.Add($_.Exception.Message)}}
    $statusKeys=@($Model.StatusModels|ForEach-Object{$_.key})
    if($Model.RiskPilot){
        $risk=$Model.RiskPilot
        if($risk.schemaVersion -ne 1 -or $risk.objectTypeKey -cne 'Risk'){$errors.Add('Invalid RiskPilot identity/version.')}
        foreach($setKey in @('RiskLikelihood','RiskImpact')){
            $set=@($Model.ChoiceSets|Where-Object key -eq $setKey)
            $scale=@($risk.ratingScale|Where-Object {$_.choiceKey -like "$($setKey):*"})
            $expected=@($set.values|ForEach-Object {"$($setKey):$($_[0])"})
            if($set.Count -ne 1 -or $scale.Count -ne 5 -or @($scale.choiceKey|Sort-Object -Unique).Count -ne 5 -or (Compare-Object ($expected|Sort-Object) ($scale.choiceKey|Sort-Object)) -or (Compare-Object @(1,2,3,4,5) @($scale.weight|Sort-Object))){$errors.Add("Invalid RiskPilot rating scale: $setKey")}
        }
        $next=1
        foreach($band in $risk.scoreBands){
            if($band.minimum -ne $next -or $band.maximum -lt $band.minimum -or [string]::IsNullOrWhiteSpace($band.key)){$errors.Add('RiskPilot score bands must cover 1..25 exactly once.')}
            $next=$band.maximum+1
        }
        if($next -ne 26 -or @($risk.scoreBands.key|Sort-Object -Unique).Count -ne 4 -or @($risk.ratingScale).Count -ne 10){$errors.Add('Invalid RiskPilot score bands/scale cardinality.')}
        if($risk.acceptance.actor -cne 'persisted-RiskOwner' -or !$risk.acceptance.requiresExplicitDecision -or $risk.acceptance.dateFormat -cne 'DateOnly' -or !$risk.acceptance.untilInclusive -or !$risk.acceptance.coreLockedAfterAcceptance -or $risk.acceptance.expiredAcceptance -cne 'block-edits-except-close'){$errors.Add('Invalid RiskPilot acceptance contract.')}
    }
    foreach($o in $Model.objectTypes){if($o.statusModel -and $statusKeys -notcontains $o.statusModel){$errors.Add("Object '$($o.key)' references unknown status model '$($o.statusModel)'.")}}
    $promptKeys=@($Model.AIPrompts|ForEach-Object{$_.key})
    foreach($s in $Model.AISkills){if($promptKeys -notcontains $s.promptKey){$errors.Add("AI skill '$($s.key)' references unknown prompt '$($s.promptKey)'.")}}
    foreach($v in $Model.Views){
        if($v.objectTypeKey -ne '*' -and -not $Model.baseClasses.ContainsKey($v.objectTypeKey) -and $objectKeys -notcontains $v.objectTypeKey){
            $errors.Add("View '$($v.key)' references unknown object type '$($v.objectTypeKey)'.")
        }
    }

    # Every provisioned object type must resolve to exactly one default view.
    foreach($o in $Model.objectTypes){
        $applicable=@($Model.Views|Where-Object{ $_.objectTypeKey -eq '*' -or $_.objectTypeKey -eq $o.key -or $_.objectTypeKey -eq $o.baseClass })
        $defaults=@($applicable|Where-Object{[bool]$_.isDefault})
        if($defaults.Count -ne 1){$errors.Add("Object '$($o.key)' resolves to $($defaults.Count) default views; exactly one is required.")}
        foreach($v in $applicable){
            if(-not $v.key){$errors.Add("Object '$($o.key)' has a view without key.")}
        }
    }
    $pageKeys=@($Model.Pages|ForEach-Object{$_.key})
    foreach($n in $Model.NavigationDefinitions){if($pageKeys -notcontains $n.pageKey){$errors.Add("Navigation '$($n.key)' references unknown page '$($n.pageKey)'.")}}
    $dashboardKeys=@($Model.Dashboards|ForEach-Object{$_.key})
    foreach($w in $Model.Widgets){if($dashboardKeys -notcontains $w.dashboardKey){$errors.Add("Widget '$($w.key)' references unknown dashboard '$($w.dashboardKey)'.")}}
    foreach($c in $Model.Commands){if($c.targetPageKey -and $pageKeys -notcontains $c.targetPageKey){$errors.Add("Command '$($c.key)' references unknown page '$($c.targetPageKey)'.")}}
    if($errors.Count){throw ("Architecture model validation failed:`n - "+($errors -join "`n - "))}
    return $true
}
Export-ModuleMember -Function Read-GPJsonYaml,Get-GPArchitectureModel,Test-GPArchitectureModel,Get-GPObjectFields
