
BeforeAll {
 $root=Split-Path $PSScriptRoot -Parent
 Import-Module "$root/provisioning/Modules/Model.psm1" -Force
 Import-Module "$root/provisioning/Modules/Compiler.psm1" -Force
 $model=Get-GPArchitectureModel -Root "$root/provisioning"
 $schema=Compile-GPArchitecture $model
}
Describe 'Governance Platform 6 architecture' {
 It 'validates' { Test-GPArchitectureModel $model | Should -BeTrue }
 It 'uses schema version 6.2.5' { $model.schemaVersion | Should -Be '6.2.5' }
 It 'compiles exactly 50 object and technical lists' { $schema.Lists.Count | Should -Be 50 }
 It 'contains runtime views' { $schema.Runtime.Views.Count | Should -BeGreaterThan 0 }
 It 'contains workflow definitions' { $schema.Runtime.Workflows.Count | Should -BeGreaterThan 0 }
 It 'contains AI skills' { $schema.Runtime.AISkills.Count | Should -BeGreaterThan 0 }
 It 'preserves SystemType as Choice' {
   ($schema.Lists|Where-Object ObjectKey -eq 'System').Fields|Where-Object InternalName -eq 'SystemType'|Select-Object -ExpandProperty Type | Should -Be 'Choice'
 }
 It 'contains Canvas search and timeline stores' {
   ($schema.Lists|Where-Object Title -eq 'SearchIndex').Count | Should -Be 1
   ($schema.Lists|Where-Object Title -eq 'TimelineEvents').Count | Should -Be 1
 }
 It 'defines central relations' { ($schema.Lists|Where-Object Title -eq 'GovernanceRelations').Count | Should -Be 1 }
}
