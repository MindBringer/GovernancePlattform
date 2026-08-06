[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Join-Path $PSScriptRoot '../..'),
    [switch]$CheckOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = [System.IO.Path]::GetFullPath($RepositoryRoot)
$registryPath = Join-Path $root 'powerplatform/config/ObjectProviderRegistry.json'
$appPath = Join-Path $root 'powerplatform/canvas/GovernancePortal/Src/App.pa.yaml'
$shellPath = Join-Path $root 'powerplatform/canvas/GovernancePortal/Src/scrShell.pa.yaml'
$generatedPath = Join-Path $root 'powerplatform/generated/ObjectProviderRuntime.powerfx'

foreach ($path in @($registryPath, $appPath, $shellPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required file not found: $path"
    }
}

$registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
if (-not $registry.providers -or $registry.providers.Count -eq 0) {
    throw 'ObjectProviderRegistry contains no providers.'
}

function ConvertTo-PowerFxBoolean([object]$Value) {
    if ([bool]$Value) { return 'true' }
    return 'false'
}

$records = foreach ($provider in $registry.providers) {
@"
          {
              ObjectTypeKey: "$($provider.objectTypeKey)",
              DataSourceKey: "$($provider.dataSource)",
              TitleField: "$($provider.titleField)",
              GovernanceIdField: "$($provider.governanceIdField)",
              ActiveField: "$($provider.activeField)",
              SupportsList: $(ConvertTo-PowerFxBoolean $provider.supportsList),
              SupportsCreate: $(ConvertTo-PowerFxBoolean $provider.supportsCreate),
              SupportsEdit: $(ConvertTo-PowerFxBoolean $provider.supportsEdit),
              SupportsSave: $(ConvertTo-PowerFxBoolean $provider.supportsSave)
          }
"@
}

$runtimeBlock = @"
      /* BEGIN GENERATED OBJECT PROVIDER RUNTIME - DO NOT EDIT */
      ClearCollect(
          colObjectProviderRegistry,
          {
              ObjectTypeKey: "",
              DataSourceKey: "",
              TitleField: "",
              GovernanceIdField: "",
              ActiveField: "",
              SupportsList: false,
              SupportsCreate: false,
              SupportsEdit: false,
              SupportsSave: false
          }
      );
      Clear(colObjectProviderRegistry);
      Collect(
          colObjectProviderRegistry,
$($records -join ",`n")
      );
      Set(gblActiveProvider, Blank());
      /* END GENERATED OBJECT PROVIDER RUNTIME */
"@

$generatedContent = @"
// Generated from powerplatform/config/ObjectProviderRegistry.json
// Source of truth remains the JSON registry.
$runtimeBlock
"@

$appContent = [System.IO.File]::ReadAllText($appPath)
$beginMarker = '      /* BEGIN GENERATED OBJECT PROVIDER RUNTIME - DO NOT EDIT */'
$endMarker = '      /* END GENERATED OBJECT PROVIDER RUNTIME */'

if ($appContent.Contains($beginMarker)) {
    $pattern = [regex]::Escape($beginMarker) + '.*?' + [regex]::Escape($endMarker)
    $nextApp = [regex]::Replace($appContent, $pattern, $runtimeBlock.TrimEnd(), [System.Text.RegularExpressions.RegexOptions]::Singleline)
} else {
    $anchor = '      Set(gblShowDiscardDialog, false);'
    if (-not $appContent.Contains($anchor)) {
        throw "App insertion anchor not found: $anchor"
    }
    $nextApp = $appContent.Replace($anchor, $anchor + "`n`n" + $runtimeBlock.TrimEnd())
}

$shellContent = [System.IO.File]::ReadAllText($shellPath)
$nextShell = $shellContent

# Bind the global New command to the active provider capability. The regex is
# intentionally whitespace-tolerant because Power Apps exports can vary line
# indentation and newline style between Studio versions and operating systems.
if (-not $nextShell.Contains('gblActiveProvider.SupportsCreate')) {
    $displayModePattern = '(?ms)(?<indent>\s*)=If\(\s*IsBlank\(gblSelectedObjectTypeKey\),\s*DisplayMode\.Disabled,\s*DisplayMode\.Edit\s*\)'
    $displayModeMatch = [regex]::Match($nextShell, $displayModePattern)
    if (-not $displayModeMatch.Success) {
        throw 'New-button DisplayMode formula not found in scrShell.pa.yaml.'
    }
    $indent = $displayModeMatch.Groups['indent'].Value
    $replacement = @"
${indent}=If(
${indent}    IsBlank(gblSelectedObjectTypeKey)
${indent}        || IsBlank(gblActiveProvider)
${indent}        || !Coalesce(gblActiveProvider.SupportsCreate, false),
${indent}    DisplayMode.Disabled,
${indent}    DisplayMode.Edit
${indent})
"@.TrimEnd()
    $nextShell = [regex]::Replace($nextShell, $displayModePattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $replacement }, 1)
}

$selectionPattern = '(?ms)(?<indent>\s*)=Set\(gblSelectedObjectTypeKey, ThisItem\.ObjectTypeKey\);\s*Set\(gblObjectType, ThisItem\.ObjectTypeKey\);'
if (-not $nextShell.Contains('ObjectTypeKey = ThisItem.ObjectTypeKey')) {
    $selectionMatch = [regex]::Match($nextShell, $selectionPattern)
    if (-not $selectionMatch.Success) {
        throw 'Object-type selection formula not found in scrShell.pa.yaml.'
    }
    $indent = $selectionMatch.Groups['indent'].Value
    $selectionReplacement = @"
${indent}=Set(gblSelectedObjectTypeKey, ThisItem.ObjectTypeKey);
${indent}Set(gblObjectType, ThisItem.ObjectTypeKey);
${indent}Set(
${indent}    gblActiveProvider,
${indent}    LookUp(
${indent}        colObjectProviderRegistry,
${indent}        ObjectTypeKey = ThisItem.ObjectTypeKey
${indent}    )
${indent});
"@.TrimEnd()
    $nextShell = [regex]::Replace($nextShell, $selectionPattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $selectionReplacement }, 1)
}

$requiredShellTokens = @(
    'gblActiveProvider.SupportsCreate',
    'colObjectProviderRegistry',
    'ObjectTypeKey = ThisItem.ObjectTypeKey'
)

if ($CheckOnly) {
    if ($nextApp -ne $appContent -or $nextShell -ne $shellContent) {
        throw 'Provider runtime is not synchronized. Run Sync-ObjectProviderRuntime.ps1 without -CheckOnly.'
    }
    foreach ($token in $requiredShellTokens) {
        if (-not $shellContent.Contains($token)) {
            throw "Provider runtime token missing in scrShell.pa.yaml: $token"
        }
    }
    Write-Host 'Object provider runtime is synchronized.' -ForegroundColor Green
    exit 0
}

$generatedDirectory = Split-Path -Parent $generatedPath
New-Item -ItemType Directory -Path $generatedDirectory -Force | Out-Null
[System.IO.File]::WriteAllText($generatedPath, $generatedContent, [System.Text.UTF8Encoding]::new($false))

if ($nextApp -ne $appContent) {
    [System.IO.File]::WriteAllText($appPath, $nextApp, [System.Text.UTF8Encoding]::new($false))
    Write-Host 'Updated App.pa.yaml provider runtime.' -ForegroundColor Green
}
if ($nextShell -ne $shellContent) {
    [System.IO.File]::WriteAllText($shellPath, $nextShell, [System.Text.UTF8Encoding]::new($false))
    Write-Host 'Updated scrShell.pa.yaml provider capability binding.' -ForegroundColor Green
}

& $PSCommandPath -RepositoryRoot $root -CheckOnly
