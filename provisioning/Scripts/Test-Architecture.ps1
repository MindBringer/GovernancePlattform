[CmdletBinding()]param()
$root=Split-Path $PSScriptRoot -Parent
foreach($m in @('Model','Compiler')){Import-Module (Join-Path $root "Modules/$m.psm1") -Force}
$model=Get-GPArchitectureModel -Root $root
Test-GPArchitectureModel $model|Out-Null
$schema=Compile-GPArchitecture $model
"Architecture valid. Version=$($model.schemaVersion); Objects=$($model.objectTypes.Count); Compiled lists=$($schema.Lists.Count)"
