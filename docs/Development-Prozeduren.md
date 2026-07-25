# Entwicklungs-, Build- und Git-Prozeduren

## 1. Lokalen Stand aktualisieren

```powershell
git switch feature/canvas-stage-3.5
git pull --ff-only
```

Vor Änderungen muss das Arbeitsverzeichnis sauber sein:

```powershell
git status
```

## 2. Architektur und Provisioning prüfen

```powershell
pwsh ./provisioning/Scripts/Test-PowerShellSyntax.ps1
pwsh ./provisioning/Scripts/Test-Architecture.ps1
pwsh ./provisioning/Scripts/Test-ArchitectureConsistency.ps1
```

Für eine Umgebungsprüfung wird anschließend ein Provisioning-DryRun mit Export der Assessment-Artefakte ausgeführt. Produktive Änderungen erst nach Prüfung des DryRuns starten.

## 3. Canvas/Solution aus Power Platform übernehmen

1. Aktuelle unmanaged Solution aus der Entwicklungsumgebung exportieren.
2. ZIP unter `artifacts/inbound/` ablegen.
3. Solution entpacken:

```powershell
pac solution unpack `
  --zipfile ./artifacts/inbound/GovernancePortal.zip `
  --folder ./powerplatform/solution `
  --packagetype Unmanaged `
  --allowDelete true `
  --allowWrite true
```

4. Canvas-App in den kanonischen SourceTree entpacken:

```powershell
pac canvas unpack `
  --msapp ./powerplatform/solution/CanvasApps/gp_governanceportal_c93a1_DocumentUri.msapp `
  --sources ./powerplatform/canvas/GovernancePortal `
  --layout SourceCode `
  --overwrite
```

5. Prüfen, dass kein zweiter SourceTree erzeugt oder committed wurde.

## 4. Version synchronisieren

Die Canvas-Version steht in `powerplatform/VERSION`. Beispiel:

```powershell
pwsh ./powerplatform/scripts/Set-BuildVersion.ps1 -Version 1.0.0-alpha.3.5.0
```

Das Skript synchronisiert Canvas `gblAppVersion`, `powerplatform/VERSION` und die numerische Solution-Version. `DeveloperPlatform.psd1` muss bei einer dauerhaften Baseline ebenfalls angepasst werden.

## 5. Validieren und bauen

```powershell
pwsh ./powerplatform/scripts/Validate-CanvasSource.ps1
pwsh ./powerplatform/scripts/Build.ps1
```

Optional mit expliziter Version:

```powershell
pwsh ./powerplatform/scripts/Build.ps1 -Version 1.0.0-alpha.3.5.0
```

Erwartete Ausgabe: Canvas- und Solution-Pakete unter `artifacts/outbound/`. Diese Ausgaben werden nicht committed.

## 6. Smoke-Test

1. erzeugte unmanaged Solution in DEV importieren
2. alle Anpassungen veröffentlichen
3. App in neuer Browser-Sitzung starten
4. Initialisierung, Navigation, Choice-, Lookup- und Person-Provider prüfen
5. New/Edit/Save für alle von der Iteration betroffenen Objekte prüfen
6. Fehlermeldungen und Browser-Konsole dokumentieren

## 7. Commit und Pull Request

```powershell
git status
git diff --check
git add architecture docs powerplatform provisioning tests migration
git commit -m "feat(canvas): implement stage 3.5 editor lifecycle"
git push -u origin feature/canvas-stage-3.5
```

Commit-Typen: `feat`, `fix`, `refactor`, `docs`, `test`, `build`, `chore`.

Ein Pull Request enthält mindestens:

- Ziel und Umfang
- betroffene Architektur-/Runtime-Definitionen
- Validierungs- und Build-Ergebnis
- durchgeführte Smoke-Tests
- bekannte Einschränkungen

## 8. Nicht committen

- `artifacts/inbound`, `artifacts/work`, `artifacts/outbound`
- Logs und exportierte Assessment-/Schema-Berichte
- lokale ZIP-Pakete und Hashdateien
- alternative Canvas-SourceTrees
- temporäre Copy-Dateien wie `*(1).*`, `*-fixed`, `*-final`
