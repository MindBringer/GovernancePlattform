[CmdletBinding()]
param(
    [string]$CanvasSource = (Join-Path $PSScriptRoot '../canvas/GovernancePortal/Src/scrShell.pa.yaml'),
    [switch]$CheckOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$resolvedPath = (Resolve-Path -LiteralPath $CanvasSource).Path
$content = [System.IO.File]::ReadAllText($resolvedPath)
$original = $content

$replacements = [ordered]@{
    'Office365Users.SearchUserV2' = "'Office365-Benutzer'.SearchUserV2"
    'selectedPerson.DisplayName' = 'selectedPerson.displayName'
    'selectedPerson.Mail' = 'selectedPerson.mail'
    'selectedPerson.UserPrincipalName' = 'selectedPerson.userPrincipalName'
    'selectedPerson.Id' = 'selectedPerson.id'
    'selectedPerson.GivenName' = 'selectedPerson.givenName'
    'selectedPerson.Surname' = 'selectedPerson.surname'
    'selectedPerson.Department' = 'selectedPerson.department'
    'selectedPerson.JobTitle' = 'selectedPerson.jobTitle'
    'selectedPerson.City' = 'selectedPerson.city'
}

foreach ($entry in $replacements.GetEnumerator()) {
    $content = $content.Replace($entry.Key, $entry.Value)
}

# Items-Formel: unqualifizierte Connectorfelder auf das V2-camelCase-Schema umstellen.
$content = $content.Replace("                                                              DisplayName,`n                                                              Mail,`n                                                              UserPrincipalName", "                                                              displayName,`n                                                              mail,`n                                                              userPrincipalName")
$content = $content.Replace("                                                              Mail,`n                                                              UserPrincipalName,`n                                                              JobTitle", "                                                              mail,`n                                                              userPrincipalName,`n                                                              jobTitle")

$invalidPatterns = @(
    'Office365Users.SearchUserV2',
    'selectedPerson.DisplayName',
    'selectedPerson.Mail',
    'selectedPerson.UserPrincipalName'
)

if ($CheckOnly) {
    $invalid = $invalidPatterns | Where-Object { $content.Contains($_) }
    if ($invalid) {
        throw "Ungültige Canvas-Referenzen gefunden: $($invalid -join ', ')"
    }
    Write-Host 'Lokalisierte Canvas-Referenzen sind konsistent.' -ForegroundColor Green
    exit 0
}

if ($content -ne $original) {
    [System.IO.File]::WriteAllText($resolvedPath, $content, [System.Text.UTF8Encoding]::new($false))
    Write-Host "Canvas-Referenzen korrigiert: $resolvedPath" -ForegroundColor Green
} else {
    Write-Host 'Keine Korrekturen erforderlich.' -ForegroundColor DarkGreen
}

& $PSCommandPath -CanvasSource $resolvedPath -CheckOnly
