# Governance Portal – Migration to Canvas SourceCode

## P3a Change – additive Migration vorbereitet, nicht ausgeführt

Zwei neue Changes-Spalten (LinkedAsset→Assets.Title und ChangeStatus mit den sieben bestehenden Lifecycle-Labels), Versionierung aktivieren, nativen Title Text/required/255 prüfen. Der reale Compiler-/Metadatentest belegt 13 neue Runtimezeilen (sechs Field-/FormFieldDefinitions, sieben ChoiceValues) und genau ObjectTypes/Change.AllowVersioning als Update; 31 bestehende Felder und 1.017 andere Zeilen erhalten. Kein Backfill, keine Description-Umdeutung, keine Datenmigration.

Changes fehlt im kanonischen Connectorpaket. Native Ergänzung, unterstützte Studio-Verbindung und geprüfte DEV→Git-Übernahme allein des erzeugten msapr brauchen eine neue Freigabe. Keine unaufgelösten Canvas-Formeln oder erfundenen Connectorrechte; Change-Capabilities bleiben false. `VERSION`, Canvas- und Solutionversion unverändert. [Konkreter Scope und Stop-Regeln](docs/development/Stage-4.1-P3-Change.md).

## P1-Systembeschreibung – begrenzte DEV-Abnahme abgeschlossen

Der lokale Canvas-Quellenkandidat 30445 verwendet `Systems.SystemDescription` (Note, Anzeige Beschreibung). Die bisherige native `Description` ist lesend als versiegelt/schreibgeschützt belegt und bleibt erhalten. Kein Umstellen von ReadOnly/Sealed, keine Umbenennung oder Löschung; vorhandene Werte werden nicht überschrieben. Architektur-/Provisioning-Baseline bleibt 6.2.5, Canvas 1.0.0-alpha.4.1.0; die additive Änderung liegt unter Unreleased und ist nicht global provisioniert.

Die am 04.10.2026 konkret freigegebene Vorbereitung hat ausschließlich die eigene Systems-Spalte und die zwei neuen Runtimezeilen `System:SystemDescription` / `System:Edit:SystemDescription` ergänzt und zurückgelesen. 724 zuvor vorhandene Zeilen in den beiden betroffenen Listen bleiben unverändert. Keine Datenmigration von Description; vor einer späteren fachlichen Migration Bestand und Semantik separat prüfen. Systems wurde in der Vorbereitung einmal unterstützt aktualisiert; dabei entstand Draft 194 bei Live 193/30444. Der danach separat freigegebene Import 30445 ist nun abgeschlossen: Canvas 195 wird vom Import als Live gesetzt, Postexport bytegleich. Nur das erzeugte msapr wurde über Staging übernommen, kanonisches Src bleibt bytegleich. Draft 196 wurde einmal manuell gespeichert und nativ exportgeprüft: 83 Controls semantisch gleich, 45 ausgelassene Defaults kompiliert gleichwertig, alle 19 Quellen-/Metadatensnapshots gleich und 33 Patch-Spalten writable. Formel-/Laufzeitchecker ohne Fehler. Je ein öffentliches Personen-/Lookup-Rebinding regeneriert beide echten Suchregeln; keine private Regel authoriert. Gezieltes Publish abgeschlossen: Canvas 196 Live, veröffentlichte Controls/DataSources bytegleich zum geprüften Host. Die begrenzte P1-DEV-Abnahme ist am 06.10.2026 abgeschlossen: beide Creates, alle fünf System-Edits mit unveränderten übrigen gemappten Feldern und sauberes Wiederöffnen bestehen. Die sichtbare Konfliktsperre erhält Quellenversion 7.0. Beide Testdatensätze sind reversibel bereinigt; Assets 4–7 und sämtliche nativen Vorbestandswerte unverändert, Systems leer. Daraus folgt keine Migration alter Description-Werte oder Produktivfreigabe. Kandidat/Versionen unverändert, kein DEV→Git. Import, Rebindings, manuellen Studio-Save, Publish und Creates nicht wiederholen. [Ausgeführter Scope und Abnahmegrenzen](docs/development/Stage-4.1-P1-SystemDescription.md).

## P2 30446–30449 – ohne Migration

30446 ergänzt die optionale Datum-Leeren-Aktion und typisierte DateTime-Aktualisierung. Es wurde einmal importiert, unterstützt gespeichert und als Canvas 198 gezielt veröffentlicht; der Host-Export stimmt mit dem geprüften Draft überein. Seine Asset-Abnahme stoppt vor Create: der gemeinsame einzeilige Text-Control erzeugt für AssetType `maxlength="0"` und verhindert echte Tastatureingabe. Der ungespeicherte Entwurf wurde verworfen; alle nativen Bestandswerte bleiben unverändert.

30447 korrigiert lokal genau diese Control-Grenze auf 255, erhält Title, Note-Control und sämtliche 17/16 Load-/Patch-Felder. Architektur, Spalten, Runtime-Metadaten und Connectorbindungen bleiben gleich; keine Migration, Provisionierung oder DEV→Git-Übernahme erforderlich. Build/Pack/Unpack und Red-/Green-Regression sind geprüft. **P2-DEV-Abnahme abgeschlossen (07.10.2026): Solution 30449 / Canvas 202 Live und gespeichert.** Der separat freigegebene Save am synthetischen Asset 13 leert alle sechs Choices als native null und erhöht die Version von 16.0 auf 17.0; die übrigen 25 deklarierten Felder bleiben erhalten. Sauberes Wiederöffnen zeigt leere Auswahlen, beide Reviewpicker mit leerem DOM-value und placeholder, „Keine Änderungen“ und gesperrtes Save. Asset 13 anschließend genau einmal reversibel bereinigt und nach Marker, Listenherkunft und ID im ersten Papierkorb nachgewiesen. Der vollständige ursprüngliche Bestand ist wiederhergestellt: Assets 4–7 mit sämtlichen nativen Werten/Versionen unverändert, Systems leer. Der erfolgreiche Create und alle fünf Personenwechsel/-Leerungen sowie Review-/Zyklus-/Boolean-Tests unter 30447 bleiben Teil der P2-Evidenz. Gespeicherter und veröffentlichter Host sind in vier Controls-/DataSources-Dateien bytegleich; 84 kanonische/92 kompilierte Controls, beide echten Suchregeln und 19 unveränderte Quellen geprüft. Formel-/Laufzeitchecker ohne Fehler; 72/12/2 Warnungen bleiben. Native ReviewCycleMonths-Min/Max, Produktivrollen und atomarer ETag-Konfliktschutz bleiben für P7 offen; P2 ist keine Produktivfreigabe. [P2-Kandidat, Umfang und Stop-Regeln](docs/development/Stage-4.1-P2-Asset-Verantwortliche.md).

30449 korrigiert die zehn Choice-Blank-Payloads in Asset/System und entfernt den missverständlichen DatePicker-Platzhalter bei leerem Datum; kein Schema-/Datenmigrations- oder Provisionierungsschritt. Leerer Choice-Schlüssel sendet das gesamte Feld als Blank, gültige Labels bleiben unverändert. Der Kandidat ist lokal und im separat freigegebenen DEV-Scope abgenommen: sechs Choices native null/v17, sichtbar leere Reviewpicker, sauberes Wiederöffnen und reversibles Cleanup von Asset 13. Vorbestand und Schema bleiben unverändert; alle Kontingente sind verbraucht. Keine DEV→Git-Übernahme.

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
