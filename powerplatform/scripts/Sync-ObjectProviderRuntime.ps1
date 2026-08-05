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

$oldDisplayMode = @"
                                      =If(
                                          IsBlank(gblSelectedObjectTypeKey),
                                          DisplayMode.Disabled,
                                          DisplayMode.Edit
                                      )
"@
$newDisplayMode = @"
                                      =If(
                                          IsBlank(gblSelectedObjectTypeKey)
                                              || IsBlank(gblActiveProvider)
                                              || !Coalesce(gblActiveProvider.SupportsCreate, false),
                                          DisplayMode.Disabled,
                                          DisplayMode.Edit
                                      )
"@
if ($nextShell.Contains($oldDisplayMode.TrimEnd())) {
    $nextShell = $nextShell.Replace($oldDisplayMode.TrimEnd(), $newDisplayMode.TrimEnd())
}

$selectionAnchor = '                                      =Set(gblSelectedObjectTypeKey, ThisItem.ObjectTypeKey);' + "`n" +
                   '                                      Set(gblObjectType, ThisItem.ObjectTypeKey);'
$selectionReplacement = '                                      =Set(gblSelectedObjectTypeKey, ThisItem.ObjectTypeKey);' + "`n" +
                        '                                      Set(gblObjectType, ThisItem.ObjectTypeKey);' + "`n" +
                        '                                      Set(' + "`n" +
                        '                                          gblActiveProvider,' + "`n" +
                        '                                          LookUp(' + "`n" +
                        '                                              colObjectProviderRegistry,' + "`n" +
                        '                                              ObjectTypeKey = ThisItem.ObjectTypeKey' + "`n" +
                        '                                          )' + "`n" +
                        '                                      );'
if ($nextShell.Contains($selectionAnchor) -and -not $nextShell.Contains('ObjectTypeKey = ThisItem.ObjectTypeKey' + "`n" + '                                          )')) {
    $nextShell = $nextShell.Replace($selectionAnchor, $selectionReplacement)
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
