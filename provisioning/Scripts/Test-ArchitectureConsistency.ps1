[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
function Read-JsonFile([string]$RelativePath){
  Get-Content (Join-Path $root $RelativePath) -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 100
}
$platform=Read-JsonFile 'architecture/platform.yaml'
$permissions=Read-JsonFile 'architecture/permissions.yaml'
$runtime=Read-JsonFile 'architecture/canvas-runtime.yaml'
$views=Read-JsonFile 'architecture/views.yaml'
$objectFields=Read-JsonFile 'architecture/object-fields.yaml'
$choices=Read-JsonFile 'architecture/choices.yaml'

$errors=[System.Collections.Generic.List[string]]::new()
$roleKeys=@($permissions.permissions.key)
$roleReferences=@()
foreach($collectionName in @('pages','navigation','dashboards','commands')){
  $collection=$runtime.$collectionName
  foreach($item in @($collection)){
    if($item.requiresRole){$roleReferences+=$item.requiresRole}
  }
}
foreach($role in ($roleReferences|Sort-Object -Unique)){
  if($role -notin $roleKeys){$errors.Add("Unknown role reference: $role")}
}

$fieldMap=@{}
foreach($f in $objectFields.objectFields){
  if(-not $fieldMap.ContainsKey($f.objectTypeKey)){$fieldMap[$f.objectTypeKey]=@()}
  $fieldMap[$f.objectTypeKey]+=$f.internalName
}
foreach($rule in $runtime.businessRules){
  if($rule.objectTypeKey -eq '*' -or -not $rule.targetField){continue}
  foreach($target in ($rule.targetField -split ';')){
    if($target -and $target -notin $fieldMap[$rule.objectTypeKey]){$errors.Add("Business rule '$($rule.key)' references missing field '$target' on '$($rule.objectTypeKey)'.")}
  }
}

$documentStatusSet = $choices.choiceSets |
    Where-Object key -eq 'DocumentStatus'

if (-not $documentStatusSet) {
    throw "ChoiceSet 'DocumentStatus' wurde in architecture/choices.yaml nicht gefunden."
}

$documentStatus = @(
    foreach ($value in $documentStatusSet.values) {
        if ($null -eq $value -or $value.Count -lt 2) {
            throw "Ungültiger Eintrag im ChoiceSet 'DocumentStatus'. Erwartet wird mindestens [Key, DisplayNameDE]."
        }

        [string]$value[1]
    }
)
$published=($views.views|Where-Object key -eq 'PublishedDocuments').filter
if($published -notmatch 'DocumentStatus eq ([^ ]+)'){$errors.Add('PublishedDocuments filter does not specify DocumentStatus.')}
elseif($Matches[1] -notin $documentStatus){$errors.Add("PublishedDocuments uses unknown stored choice value '$($Matches[1])'.")}

foreach($nav in $platform.navigation){
  foreach($child in @($nav.children)){
    if($child.url -and $child.url -notmatch '^\{SiteUrl\}/'){$errors.Add("Navigation child '$($child.title)' is not site-relative via {SiteUrl}: $($child.url)")}
  }
}
if($errors.Count){$errors|ForEach-Object{Write-Error $_};throw "Architecture consistency validation failed with $($errors.Count) error(s)."}
Write-Host 'Architecture consistency validation passed.'
