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
    'selectedPerson.displayName' = 'selectedPerson.DisplayName'
    'selectedPerson.mail' = 'selectedPerson.Mail'
    'selectedPerson.userPrincipalName' = 'selectedPerson.UserPrincipalName'
    'selectedPerson.id' = 'selectedPerson.Id'
    'selectedPerson.givenName' = 'selectedPerson.GivenName'
    'selectedPerson.surname' = 'selectedPerson.Surname'
    'selectedPerson.department' = 'selectedPerson.Department'
    'selectedPerson.jobTitle' = 'selectedPerson.JobTitle'
    'selectedPerson.city' = 'selectedPerson.City'
}

foreach ($entry in $replacements.GetEnumerator()) {
    $content = $content.Replace($entry.Key, $entry.Value)
}

# Items formula: normalize unqualified SearchUserV2 fields to the schema exposed
# by the localized connector in the current Power Apps tenant.
$content = $content.Replace("                                                              displayName,`n                                                              mail,`n                                                              userPrincipalName", "                                                              DisplayName,`n                                                              Mail,`n                                                              UserPrincipalName")
$content = $content.Replace("                                                              mail,`n                                                              userPrincipalName,`n                                                              jobTitle", "                                                              Mail,`n                                                              UserPrincipalName,`n                                                              JobTitle")

$invalidPatterns = @(
    'Office365Users.SearchUserV2',
    'selectedPerson.displayName',
    'selectedPerson.mail',
    'selectedPerson.userPrincipalName',
    'selectedPerson.department',
    'selectedPerson.jobTitle'
)

$requiredPatterns = @(
    "'Office365-Benutzer'.SearchUserV2",
    'DisplayFields: =["DisplayName"]',
    'SearchFields: =["DisplayName"]',
    'UserPrincipalName: usr.UserPrincipalName',
    'UserPrincipalName: ThisItem.ValuePersonEmail',
    'selectedPerson: First(Self.SelectedItems)',
    'selectedPerson.UserPrincipalName',
    'SelectMultiple: =false'
)

if ($CheckOnly) {
    $person = [regex]::Match($content, '(?ms)^ *- cmbEditorPerson:\r?\n(?<control>.*?)(?=^ {0,42}- \w+:|\z)').Groups['control'].Value
    if ($person -match '(?m)^ +SearchItems:') {
        throw 'SearchItems is private and unsupported in ComboBox SourceCode YAML (Studio PA2108); rebind Items in Studio and verify its generated rule.'
    }
    if ($person -notmatch 'searchTerm:\s*Self\.SearchText' -or
        $person -notmatch 'top:\s*20\s*,' -or
        $person -notmatch 'isSearchTermRequired:\s*true') {
        throw 'Person search requires bounded, required server-filtered Items.'
    }
    $invalid = $invalidPatterns | Where-Object { $content.Contains($_) }
    if ($invalid) {
        throw "Ungültige Canvas-Referenzen gefunden: $($invalid -join ', ')"
    }

    $missing = $requiredPatterns | Where-Object { -not $content.Contains($_) }
    if ($missing) {
        throw "Erforderliche Personenfeld-Referenzen fehlen: $($missing -join ', ')"
    }

    Write-Host 'Lokalisierte Canvas-Referenzen und Personenfeld-Bindung sind konsistent.' -ForegroundColor Green
    exit 0
}

if ($content -ne $original) {
    [System.IO.File]::WriteAllText($resolvedPath, $content, [System.Text.UTF8Encoding]::new($false))
    Write-Host "Canvas-Referenzen korrigiert: $resolvedPath" -ForegroundColor Green
} else {
    Write-Host 'Keine Korrekturen erforderlich.' -ForegroundColor DarkGreen
}

& $PSCommandPath -CanvasSource $resolvedPath -CheckOnly
