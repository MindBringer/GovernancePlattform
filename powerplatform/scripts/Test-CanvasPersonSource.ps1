[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$gate = Join-Path $PSScriptRoot 'Fix-LocalizedCanvasReferences.ps1'
$sourcePath = Join-Path $PSScriptRoot '../canvas/GovernancePortal/Src/scrShell.pa.yaml'
$source = Get-Content $sourcePath -Raw
$temp = Join-Path ([System.IO.Path]::GetTempPath()) ('gp-person-source-' + [guid]::NewGuid() + '.yaml')
try {
    & $gate -CanvasSource $sourcePath -CheckOnly
    $cases = @(
        @{Name='observed unsupported SearchItems property'; Pattern='SearchFields: =\["DisplayName"\]'; Replacement="SearchFields: =[`"DisplayName`"]`n                                                SearchItems: =Self.Items"},
        @{Name='unbounded search'; Pattern='top: 20'; Replacement='top: 2000'},
        @{Name='empty directory search'; Pattern='isSearchTermRequired: true'; Replacement='isSearchTermRequired: false'},
        @{Name='missing selected UPN'; Pattern='selectedPerson\.UserPrincipalName'; Replacement='selectedPerson.Mail'}
    )
    foreach ($case in $cases) {
        $fixture = [regex]::Replace($source, $case.Pattern, $case.Replacement)
        if ($fixture -ceq $source) { throw "Fixture did not change source: $($case.Name)." }
        [System.IO.File]::WriteAllText($temp, $fixture)
        $rejected = $false
        try { & $gate -CanvasSource $temp -CheckOnly } catch {
            if ($_.Exception.Message -notmatch 'SearchItems is private|Person search requires|Erforderliche Personenfeld-Referenzen') { throw }
            $rejected = $true
        }
        if (-not $rejected) { throw "Person source gate accepted invalid contract: $($case.Name)." }
    }
    Write-Host 'Person source contract passed: bounded server search and UPN; four invalid fixtures rejected, including Studio PA2108. Generated Studio binding still requires live acceptance.'
}
finally { if (Test-Path $temp) { [System.IO.File]::Delete($temp) } }
