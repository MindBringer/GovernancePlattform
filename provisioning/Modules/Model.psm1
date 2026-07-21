
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
    $model.Migration=Read-GPJsonYaml (Join-Path $Root '../migration/v5-to-v6.yaml')
    return $model
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
        if($f.choiceSet -and $choices -notcontains $f.choiceSet){$errors.Add("Field '$($f.internalName)' references unknown choice set '$($f.choiceSet)'.")}
    }
    $statusKeys=@($Model.StatusModels|ForEach-Object{$_.key})
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
Export-ModuleMember -Function Read-GPJsonYaml,Get-GPArchitectureModel,Test-GPArchitectureModel
