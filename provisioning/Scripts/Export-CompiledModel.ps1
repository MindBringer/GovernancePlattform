[CmdletBinding()]param()
$root=Split-Path $PSScriptRoot -Parent
foreach($m in @('Logging','Model','Compiler','Reporting')){Import-Module (Join-Path $root "Modules/$m.psm1") -Force}
$global:GPContext=@{Root=$root;LogFile=(Join-Path $root '../Logs/compile.log');DryRun=$false}
$model=Get-GPArchitectureModel -Root $root
Test-GPArchitectureModel $model|Out-Null
$schema=Compile-GPArchitecture $model
Export-GPCompiledSchema $schema
Export-GPDataDictionary $schema
