# Stage 3.5.2a – Referenzprüfung nach dem Canvas-Pack

## Korrektur

Die Datenquellenprüfung aus Stage 3.5.2 lief zu früh:

```text
Source validieren
→ Datenquellen im alten Referenzpaket prüfen
→ Canvas packen
```

Stage 3.5.2a verwendet die korrekte Reihenfolge:

```text
Source validieren
→ Canvas packen
→ neu gepackte .msapp prüfen
→ Solution packen
```

## Dateien

- `Build.ps1`
- `Validate-CanvasSource.ps1`
- `Validate-CanvasReferences.ps1`

## Wichtig

Die Studio-gespeicherte `.msapp` wird **nicht manuell** nach
`powerplatform/solution/CanvasApps` kopiert. Dieser Ordner ist das Buildziel von
`Pack-Canvas.ps1` und wird automatisch aktualisiert.

Falls die neue Post-Pack-Prüfung weiterhin `Systems` oder `Office365Users` als
fehlend meldet, enthält der kanonische SourceCode-Ordner noch ein altes `.msapr`.
Dann einmalig:

```powershell
pac canvas unpack `
  --msapp ./artifacts/inbound/GovernancePortal-3.5.1-studio-baseline.msapp `
  --sources ./artifacts/work/GovernancePortal-reference-refresh `
  --layout SourceCode `
  --overwrite
```

Anschließend nur die erzeugte `*.msapr` aus dem temporären Quellordner nach

```text
powerplatform/canvas/GovernancePortal/
```

kopieren. Die aktuellen Dateien unter `Src/` dürfen dabei nicht überschrieben
werden.

## Build

```powershell
./powerplatform/scripts/Build.ps1
```
