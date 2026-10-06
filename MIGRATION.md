# Governance Portal – Migration to Canvas SourceCode

## P1-Systembeschreibung – begrenzte DEV-Abnahme abgeschlossen

Der lokale Canvas-Quellenkandidat 30445 verwendet `Systems.SystemDescription` (Note, Anzeige Beschreibung). Die bisherige native `Description` ist lesend als versiegelt/schreibgeschützt belegt und bleibt erhalten. Kein Umstellen von ReadOnly/Sealed, keine Umbenennung oder Löschung; vorhandene Werte werden nicht überschrieben. Architektur-/Provisioning-Baseline bleibt 6.2.5, Canvas 1.0.0-alpha.4.1.0; die additive Änderung liegt unter Unreleased und ist nicht global provisioniert.

Die am 04.10.2026 konkret freigegebene Vorbereitung hat ausschließlich die eigene Systems-Spalte und die zwei neuen Runtimezeilen `System:SystemDescription` / `System:Edit:SystemDescription` ergänzt und zurückgelesen. 724 zuvor vorhandene Zeilen in den beiden betroffenen Listen bleiben unverändert. Keine Datenmigration von Description; vor einer späteren fachlichen Migration Bestand und Semantik separat prüfen. Systems wurde in der Vorbereitung einmal unterstützt aktualisiert; dabei entstand Draft 194 bei Live 193/30444. Der danach separat freigegebene Import 30445 ist nun abgeschlossen: Canvas 195 wird vom Import als Live gesetzt, Postexport bytegleich. Nur das erzeugte msapr wurde über Staging übernommen, kanonisches Src bleibt bytegleich. Draft 196 wurde einmal manuell gespeichert und nativ exportgeprüft: 83 Controls semantisch gleich, 45 ausgelassene Defaults kompiliert gleichwertig, alle 19 Quellen-/Metadatensnapshots gleich und 33 Patch-Spalten writable. Formel-/Laufzeitchecker ohne Fehler. Je ein öffentliches Personen-/Lookup-Rebinding regeneriert beide echten Suchregeln; keine private Regel authoriert. Gezieltes Publish abgeschlossen: Canvas 196 Live, veröffentlichte Controls/DataSources bytegleich zum geprüften Host. Die begrenzte P1-DEV-Abnahme ist am 06.10.2026 abgeschlossen: beide Creates, alle fünf System-Edits mit unveränderten übrigen gemappten Feldern und sauberes Wiederöffnen bestehen. Die sichtbare Konfliktsperre erhält Quellenversion 7.0. Beide Testdatensätze sind reversibel bereinigt; Assets 4–7 und sämtliche nativen Vorbestandswerte unverändert, Systems leer. Daraus folgt keine Migration alter Description-Werte oder Produktivfreigabe. Kandidat/Versionen unverändert, kein DEV→Git. Import, Rebindings, manuellen Studio-Save, Publish und Creates nicht wiederholen. [Ausgeführter Scope und Abnahmegrenzen](docs/development/Stage-4.1-P1-SystemDescription.md).

## P2 30446 – lokale Formularänderung ohne Migration

Kandidat 30446 ergänzt ausschließlich die optionale Datum-Leeren-Aktion und die typisierte DateTime-Aktualisierung im gemeinsamen Asset-/System-Editor. Architektur, native Spalten, Runtime-Metadaten, Personen-/Choice-Verträge und die 17/16 Patch-Felder bleiben gleich. Keine Migration, Provisionierung oder DEV→Git-Übernahme erforderlich. 30446 ist noch nicht in DEV übernommen; dort bleibt die abgenommene 30445/196-Baseline. [Separate P2-Abnahme und Grenzen](docs/development/Stage-4.1-P2-Asset-Verantwortliche.md).

## Target structure

```text
powerplatform/
  canvas/
    GovernancePortal/
      Src/
        App.pa.yaml
        scrShell.pa.yaml
        ...
      ...                         # remaining files produced by PAC
  solution/
    canvas/GovernancePortal/
      gp_governanceportal_c93a1_DocumentUri.msapr
  scripts/
    DeveloperPlatform.psd1
    Common.ps1
    Validate-CanvasSource.ps1
    Initialize-CanvasSourceCode.ps1
    Pack-Canvas.ps1
    Pack-Solution.ps1
    Build.ps1
artifacts/
  inbound/                        # ignored
  work/                           # ignored
  outbound/                       # ignored
```

There is exactly one canonical Canvas source tree: `powerplatform/canvas/GovernancePortal` using `Src/*.pa.yaml`.
Do not retain `canvas-editable`, `*.fx.yaml`, or `Other/Src`.

## Clean migration

1. Commit or archive the current repository state.
2. Open the current working app in Power Apps Studio, save and publish it.
3. Download a fresh `.msapp` from Power Apps Studio (`Save as` / `Download a copy`).
4. Put it in `artifacts/inbound/GovernancePortal-current.msapp`.
5. Replace the scripts with this package.
6. Initialize the canonical source:

```powershell
./powerplatform/scripts/Initialize-CanvasSourceCode.ps1 `
  -MsAppPath ./artifacts/inbound/GovernancePortal-current.msapp `
  -Force
```

7. Remove the legacy tree after comparing the result:

```powershell
Remove-Item ./powerplatform/canvas-editable -Recurse -Force
```

8. Ensure `Src/App.pa.yaml` contains the configured version and run:

```powershell
./powerplatform/scripts/Build.ps1
```

9. Import the generated unmanaged solution from `artifacts/outbound`, publish all customizations, and smoke-test in a new browser session.

## Git ignore additions

```gitignore
.DS_Store
artifacts/inbound/
artifacts/work/
artifacts/outbound/
```

## Important operating rule

A fresh Power Apps Studio export is the safest baseline. PAC `canvas pack/unpack` remains preview/deprecated in current Microsoft documentation. Keep the round-trip validation and always validate the resulting app in DEV before merging.
