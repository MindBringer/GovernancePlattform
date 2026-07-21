[CmdletBinding()]param([string]$Path=(Split-Path (Split-Path $PSScriptRoot -Parent) -Parent))
$allErrors=@()
foreach($file in Get-ChildItem -Path $Path -Recurse -File -Include *.ps1,*.psm1){
 $tokens=$null;$errors=$null
 [void][System.Management.Automation.Language.Parser]::ParseFile($file.FullName,[ref]$tokens,[ref]$errors)
 foreach($error in $errors){$allErrors+=[pscustomobject]@{File=$file.FullName;Line=$error.Extent.StartLineNumber;Column=$error.Extent.StartColumnNumber;Text=$error.Extent.Text;Message=$error.Message}}
}
if($allErrors.Count){$allErrors|Format-Table -AutoSize;throw "PowerShell syntax validation failed with $($allErrors.Count) error(s)."}
Write-Host 'PowerShell syntax validation completed successfully.'
