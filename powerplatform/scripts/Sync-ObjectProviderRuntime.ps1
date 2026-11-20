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

$canvasRuntime = Get-Content -LiteralPath (Join-Path $root 'architecture/canvas-runtime.yaml') -Raw | ConvertFrom-Json
$assetPilot = $canvasRuntime.assetPilot
$assetReviewCycle = @((Get-Content -LiteralPath (Join-Path $root 'architecture/fields.yaml') -Raw | ConvertFrom-Json).fields |
    Where-Object internalName -CEQ 'ReviewCycleMonths')
if ($assetReviewCycle.Count -ne 1 -or $assetReviewCycle[0].type -cne 'Number' -or
    $assetReviewCycle[0].min -isnot [long] -or $assetReviewCycle[0].max -isnot [long] -or
    $assetReviewCycle[0].min -lt 1 -or $assetReviewCycle[0].max -lt $assetReviewCycle[0].min) {
    throw 'The canonical Asset review cycle requires positive integer bounds in architecture/fields.yaml.'
}
$assetNavigation = @($canvasRuntime.navigation | Where-Object {
    $_.objectTypeKey -ceq 'Asset' -and $_.pageKey -ceq 'ObjectList'
})
$homeNavigation = @($canvasRuntime.navigation | Where-Object pageKey -CEQ 'Home')
if ($assetPilot.enabled -isnot [bool] -or $assetPilot.objectTypeKey -cne 'Asset' -or
    $assetPilot.editorSettingKey -cnotmatch '^[A-Za-z]+(?:\.[A-Za-z]+)+$' -or
    $assetPilot.extendedAccessSettingKey -cnotmatch '^[A-Za-z]+(?:\.[A-Za-z]+)+$' -or
    $assetPilot.extendedAccessSettingKey -eq $assetPilot.editorSettingKey -or
    $assetNavigation.Count -ne 1 -or $homeNavigation.Count -ne 1 -or
    ($assetPilot.navigationKeys -join ',') -cne "$($homeNavigation[0].key),$($assetNavigation[0].key)") {
    throw 'The Asset pilot requires the canonical Home and Asset navigation keys and a runtime editor setting.'
}
$pilotNavigationKeys = ($assetPilot.navigationKeys | ForEach-Object { '"' + $_ + '"' }) -join ', '
$extendedRoutes = @($assetPilot.extendedObjectRoutes)
$extendedTypes = @($extendedRoutes | ForEach-Object objectTypeKey)
if ($extendedTypes -icontains 'Asset' -or @($extendedTypes | Sort-Object -Unique).Count -ne $extendedTypes.Count) {
    throw 'Extended pilot routes must have distinct non-Asset object types.'
}
$extendedRouteRecords = foreach ($route in $extendedRoutes) {
    $navigation = @($canvasRuntime.navigation | Where-Object {
        $_.key -ceq $route.navigationKey -and $_.pageKey -ceq 'ObjectList' -and $_.visible
    })
    $provider = @($registry.providers | Where-Object {
        $_.objectTypeKey -ceq $route.objectTypeKey -and $_.supportsList
    })
    if ($navigation.Count -ne 1 -or $provider.Count -ne 1) {
        throw "Extended pilot route requires a visible ObjectList and a list provider: $($route.objectTypeKey)."
    }
    '              {NavigationKey: "' + $route.navigationKey + '", ObjectTypeKey: "' + $route.objectTypeKey + '", RequiresExtendedAccess: true}'
}
$pilotRouteRecords = @(
    '              {NavigationKey: "' + $assetNavigation[0].key + '", ObjectTypeKey: "Asset", RequiresExtendedAccess: false}'
) + @($extendedRouteRecords)

$workspace = $canvasRuntime.workspace
if ($workspace.enabled -isnot [bool] -or $workspace.siteSettingKey -cnotmatch '^[A-Za-z]+(?:\.[A-Za-z]+)+$') {
    throw 'The workspace requires an explicit mode and site setting key.'
}
$platformModel = Get-Content -LiteralPath (Join-Path $root 'architecture/platform.yaml') -Raw | ConvertFrom-Json
$workspaceEntries = foreach ($module in $workspace.modules) {
    if (@($canvasRuntime.navigation | Where-Object { $_.key -ceq $module.navigationKey -and $_.visible }).Count -ne 1) {
        throw "Unknown workspace navigation $($module.navigationKey)."
    }
    foreach ($sourceKey in $module.sources) {
        $objectType = @($platformModel.objectTypes | Where-Object key -CEQ $sourceKey)
        $technical = @($workspace.technicalSources | Where-Object key -CEQ $sourceKey)
        if ($objectType.Count + $technical.Count -ne 1) { throw "Ambiguous workspace source $sourceKey." }
        $sourceName = if ($objectType.Count) { $objectType[0].source } else { $technical[0].source }
        $title = if ($objectType.Count) { $objectType[0].pluralNameDE } else { $technical[0].label }
        $isLibrary = $objectType.Count -eq 1 -and $objectType[0].kind -ceq 'Library'
        $path = if ($isLibrary) { "/$sourceName/Forms/AllItems.aspx" } else { "/Lists/$sourceName/AllItems.aspx" }
        $canvasProvider = if (@($registry.providers | Where-Object { $_.objectTypeKey -ceq $sourceKey -and $_.supportsList }).Count) { $sourceKey } else { '' }
        if ($sourceName -cnotmatch '^[A-Za-z][A-Za-z0-9_]*$' -or $title -match '["\r\n]') { throw 'Invalid workspace source.' }
        '          {NavigationKey: "' + $module.navigationKey + '", ObjectTypeKey: "' + $sourceKey + '", Title: "' + $title +
            '", RelativePath: "' + $path + '", CanvasProvider: "' + $canvasProvider + '"}'
    }
}
$workspaceBlock = @"
      Set(gblWorkspaceEnabled, $(if ($workspace.enabled) { 'true' } else { 'false' }));
      Set(gblWorkspaceSiteSettingKey, "$($workspace.siteSettingKey)");
      Set(
          gblWorkspaceSources,
          Table(
$($workspaceEntries -join ("," + [Environment]::NewLine))
          )
      );
"@

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
$workspaceBlock
      Set(gblAssetPilotEnabled, $(ConvertTo-PowerFxBoolean $assetPilot.enabled));
      Set(gblAssetPilotEditorSettingKey, "$($assetPilot.editorSettingKey)");
      Set(gblPilotExtendedAccessSettingKey, "$($assetPilot.extendedAccessSettingKey)");
      Set(gblAssetPilotNavigationKeys, [$pilotNavigationKeys]);
      Set(gblAssetPilotAssetNavigation, "$($assetNavigation[0].key)");
      Set(
          gblPilotConfiguredRoutes,
          Table(
$($pilotRouteRecords -join ",`n")
          )
      );
      Set(gblAssetReviewCycleMin, $($assetReviewCycle[0].min));
      Set(gblAssetReviewCycleMax, $($assetReviewCycle[0].max));
      /* END GENERATED OBJECT PROVIDER RUNTIME */
"@
$runtimeBlock = $runtimeBlock.Replace("`r`n", "`n")

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
    $displayModePattern = '(?ms)(?<indent>[ \t]*)=If\(\s*IsBlank\(gblSelectedObjectTypeKey\),\s*DisplayMode\.Disabled,\s*DisplayMode\.Edit\s*\)'
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
"@.TrimEnd().Replace("`r`n", "`n")
    $nextShell = [regex]::Replace($nextShell, $displayModePattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $replacement }, 1)
}

$selectionPattern = '(?ms)(?<indent>[ \t]*)=Set\(gblSelectedObjectTypeKey, ThisItem\.ObjectTypeKey\);\s*Set\(gblObjectType, ThisItem\.ObjectTypeKey\);'
if ($nextShell -notmatch 'Set\(\s*gblActiveProvider\s*,\s*LookUp\(\s*colObjectProviderRegistry') {
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
"@.TrimEnd().Replace("`r`n", "`n")
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
    if ($shellContent -notmatch 'Set\(\s*gblActiveProvider\s*,\s*LookUp\(\s*colObjectProviderRegistry') {
        throw 'Active provider selection is missing in scrShell.pa.yaml.'
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
