function Export-GPCompiledSchema {
 [CmdletBinding()]
 param([hashtable]$Schema)
 $json=Join-Path $global:GPContext.Root '../generated/compiled-schema.json'
 $Schema|ConvertTo-Json -Depth 100|Set-Content $json -Encoding utf8
 $csv=Join-Path $global:GPContext.Root ("../generated/SchemaReport-{0}.csv" -f (Get-Date -Format yyyyMMdd-HHmmss))
 $rows=@(foreach($l in $Schema.Lists){foreach($f in $l.Fields){[pscustomobject]@{ObjectKey=$l.ObjectKey;List=$l.Title;BaseClass=$l.BaseClass;Field=$f.InternalName;DisplayName=$f.DisplayName;Type=$f.Type;Required=$f.Required;Indexed=$f.Indexed}}})
 $rows|Export-Csv $csv -NoTypeInformation -Encoding utf8
 Write-GPLog "Compiled schema exported: $json" SUCCESS
 Write-GPLog "Schema report exported: $csv" SUCCESS
}
function Export-GPDataDictionary {
 [CmdletBinding()]
 param([hashtable]$Schema)
 $path=Join-Path $global:GPContext.Root '../generated/Data-Dictionary.md'
 $lines=[System.Collections.Generic.List[string]]::new()
 $lines.Add('# Data Dictionary – Governance Platform 6.2.5')
 foreach($l in $Schema.Lists){
   $lines.Add("`n## $($l.Title)");$lines.Add("Basisklasse: **$($l.BaseClass)**`n")
   $lines.Add('| Interner Name | Anzeige | Typ | Pflicht | Index |');$lines.Add('|---|---|---:|:---:|:---:|')
   foreach($f in $l.Fields){$lines.Add("| $($f.InternalName) | $($f.DisplayName) | $($f.Type) | $($f.Required) | $($f.Indexed) |")}
 }
 $lines|Set-Content $path -Encoding utf8
 Write-GPLog "Data dictionary exported: $path" SUCCESS
}
Export-ModuleMember -Function Export-GPCompiledSchema,Export-GPDataDictionary
