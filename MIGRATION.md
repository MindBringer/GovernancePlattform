# Governance Portal – Migration to Canvas SourceCode

## P1-Systembeschreibung – begrenzte DEV-Abnahme abgeschlossen

Der lokale Canvas-Quellenkandidat 30445 verwendet `Systems.SystemDescription` (Note, Anzeige Beschreibung). Die bisherige native `Description` ist lesend als versiegelt/schreibgeschützt belegt und bleibt erhalten. Kein Umstellen von ReadOnly/Sealed, keine Umbenennung oder Löschung; vorhandene Werte werden nicht überschrieben. Architektur-/Provisioning-Baseline bleibt 6.2.5, Canvas 1.0.0-alpha.4.1.0; die additive Änderung liegt unter Unreleased und ist nicht global provisioniert.

Die am 04.10.2026 konkret freigegebene Vorbereitung hat ausschließlich die eigene Systems-Spalte und die zwei neuen Runtimezeilen `System:SystemDescription` / `System:Edit:SystemDescription` ergänzt und zurückgelesen. 724 zuvor vorhandene Zeilen in den beiden betroffenen Listen bleiben unverändert. Keine Datenmigration von Description; vor einer späteren fachlichen Migration Bestand und Semantik separat prüfen. Systems wurde in der Vorbereitung einmal unterstützt aktualisiert; dabei entstand Draft 194 bei Live 193/30444. Der danach separat freigegebene Import 30445 ist nun abgeschlossen: Canvas 195 wird vom Import als Live gesetzt, Postexport bytegleich. Nur das erzeugte msapr wurde über Staging übernommen, kanonisches Src bleibt bytegleich. Draft 196 wurde einmal manuell gespeichert und nativ exportgeprüft: 83 Controls semantisch gleich, 45 ausgelassene Defaults kompiliert gleichwertig, alle 19 Quellen-/Metadatensnapshots gleich und 33 Patch-Spalten writable. Formel-/Laufzeitchecker ohne Fehler. Je ein öffentliches Personen-/Lookup-Rebinding regeneriert beide echten Suchregeln; keine private Regel authoriert. Gezieltes Publish abgeschlossen: Canvas 196 Live, veröffentlichte Controls/DataSources bytegleich zum geprüften Host. Die begrenzte P1-DEV-Abnahme ist am 06.10.2026 abgeschlossen: beide Creates, alle fünf System-Edits mit unveränderten übrigen gemappten Feldern und sauberes Wiederöffnen bestehen. Die sichtbare Konfliktsperre erhält Quellenversion 7.0. Beide Testdatensätze sind reversibel bereinigt; Assets 4–7 und sämtliche nativen Vorbestandswerte unverändert, Systems leer. Daraus folgt keine Migration alter Description-Werte oder Produktivfreigabe. Kandidat/Versionen unverändert, kein DEV→Git. Import, Rebindings, manuellen Studio-Save, Publish und Creates nicht wiederholen. [Ausgeführter Scope und Abnahmegrenzen](docs/development/Stage-4.1-P1-SystemDescription.md).

## P2 30446–30449 – ohne Migration

30446 ergänzt die optionale Datum-Leeren-Aktion und typisierte DateTime-Aktualisierung. Es wurde einmal importiert, unterstützt gespeichert und als Canvas 198 gezielt veröffentlicht; der Host-Export stimmt mit dem geprüften Draft überein. Seine Asset-Abnahme stoppt vor Create: der gemeinsame einzeilige Text-Control erzeugt für AssetType `maxlength="0"` und verhindert echte Tastatureingabe. Der ungespeicherte Entwurf wurde verworfen; alle nativen Bestandswerte bleiben unverändert.

30447 korrigiert lokal genau diese Control-Grenze auf 255, erhält Title, Note-Control und sämtliche 17/16 Load-/Patch-Felder. Architektur, Spalten, Runtime-Metadaten und Connectorbindungen bleiben gleich; keine Migration, Provisionierung oder DEV→Git-Übernahme erforderlich. Build/Pack/Unpack und Red-/Green-Regression sind geprüft. **P2-DEV-Teilabnahme (07.10.2026): Solution 30447 / Canvas 200 Live und gespeichert.** Beide öffentlichen Suchbindungen sind vollständig regeneriert; gespeicherter und publizierter Host stimmen in Controls und allen 19 Quellen überein (84 kanonische/92 kompilierte Controls, keine abweichende Fachregel). Formel-/Laufzeitchecker ohne Fehler, 72/12/2 Warnungen bleiben. AssetType-Tastatureingabe mit MaxLength 255, ein synthetischer Create (Asset ID 13) und Personenwechsel/-Leeren in allen fünf Feldern bestehen. Edit 11 speichert Choices und Termine, aber zunächst Zyklus 6 statt 12; der separat genehmigte zusätzliche Save mit echter Tastatureingabe korrigiert ausschließlich den Zyklus auf 12. Edits 12/13 belegen beide Termine und Zyklus als native null sowie IsActive false, jeweils sauber wiedergeöffnet. **Edit 14 scheitert:** alle sechs Choices vor Save in der App leer, Quelle bei Version 16.0 weiterhin mit alten Choice-Werten; 25 übrige deklarierte Felder unverändert. Alle 15 genehmigten Edit-Versuche sind verbraucht. Stop-Regel ausgelöst, Cleanup 0/1; Asset 13 bleibt erhalten. Abschließende Vollsnapshots bestätigen Assets 4–7/v1.0 mit allen Ausgangswerten unverändert und Systems leer. Der abschließende Sichtcheck zeigt bei nativ leerem Datum und DOM-value leer noch den Standardplatzhalter „31.12.2001“. **Kandidat 30449 korrigiert Choice-Blank und entfernt diesen Datumsplatzhalter lokal; seine DEV-Abnahme braucht einen neuen begrenzten Scope.** P2 bleibt fachlich offen; native ReviewCycleMonths-Min/Max-Grenzen fehlen weiterhin. [P2-Kandidat, Umfang und Stop-Regeln](docs/development/Stage-4.1-P2-Asset-Verantwortliche.md).

30449 korrigiert die zehn Choice-Blank-Payloads in Asset/System und entfernt den missverständlichen DatePicker-Platzhalter bei leerem Datum; kein Schema-/Datenmigrations- oder Provisionierungsschritt. Leerer Choice-Schlüssel sendet das gesamte Feld als Blank, gültige Labels bleiben unverändert. Der neue Kandidat ist lokal gebaut und geprüft; eine fokussierte DEV-Abnahme am bestehenden synthetischen Asset 13 sowie sein reversibles Cleanup sind separat freizugeben. Keine DEV→Git-Übernahme.

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
