# Governance Portal – Developer Platform 1.0

## Ziel
Reproduzierbarer Git-first-Workflow für macOS/PowerShell 7, PAC CLI, Canvas-App und unmanaged Solution.

## Installation
Den Inhalt dieses Pakets in das Repository-Root kopieren. Bestehende Skripte unter `powerplatform/scripts` werden durch die hier enthaltenen, erweiterten Fassungen ersetzt. `DeveloperPlatform.psd1` anschließend prüfen, insbesondere Solution-Name, MSAPP-Pfad, Version und optional DEV-URL.

## Initialisierung auf macOS
```powershell
pac install latest
pac auth create --environment "<DEV-URL-ODER-ID>"
pac auth list
```

## Standarditeration
```powershell
git switch feature/<iteration>
pwsh ./powerplatform/scripts/Export-Dev.ps1 -Unpack
# Entwicklung und Studio-Test
pwsh ./powerplatform/scripts/Validate.ps1
pwsh ./powerplatform/scripts/Build.ps1
pwsh ./powerplatform/scripts/Import-Dev.ps1 -WhatIf
pwsh ./powerplatform/scripts/Import-Dev.ps1 -Confirm
pwsh ./powerplatform/scripts/Publish-Feature.ps1 -CommitMessage "feat(canvas): ..."
```

## Skripte
- `Export-Dev.ps1`: unmanaged Export nach `artifacts/inbound`, optional direktes Unpack.
- `Unpack-Solution.ps1`: jüngste oder angegebene ZIP in `powerplatform/solution` entpacken.
- `Unpack-Canvas.ps1`: aktualisiert Review- und Editable-Layout.
- `Validate.ps1`: Diff-, Pfad-, PowerShell- und vorhandene Architekturtests.
- `Build.ps1`: Validate, Canvas Pack, SourceCode Refresh, Solution Pack.
- `Import-Dev.ps1`: geschützter DEV-Import mit `-WhatIf`/`-Confirm`.
- `Publish-Feature.ps1`: Build, Commit und Push – nur auf `feature/*`.
- `Release.ps1`: Release nur von sauberem `main`, Version, Build, Commit und Tag.

## Wichtiger Übergangshinweis
Das bestehende Editable-Layout nutzt `pac canvas pack/unpack` mit `Experimental`. Microsoft kennzeichnet diese Befehle und das Experimental-Layout inzwischen als veraltet. Developer Platform 1.0 kapselt diesen Workflow deshalb vollständig in Skripten. Eine spätere Migration auf das unterstützte SourceCode-/Git-Integrationsmodell ist als eigenes Arbeitspaket vorzusehen.

## Branch- und Release-Regeln
- `main`: nur import- und smoke-getestete Stände.
- `feature/*`: Entwicklung.
- Pull Request vor Merge.
- SemVer-Tags, z. B. `v1.0.0-alpha.3.1`.

## Pflicht-Smoke-Test
Appstart, Navigation, Metadatenladen, Objektwahl, Editorstart, geänderte Funktion, schmaler Viewport, keine Regressionen.
