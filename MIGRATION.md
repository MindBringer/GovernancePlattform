# Governance Portal – Migration to Canvas SourceCode

## P3 Change – DEV 30451 gestoppt, Reparatur 30452 lokal

Der ursprüngliche indizierte LinkedAsset-Add wurde am nativen 20-Index-Limit ohne weitere Writes gestoppt; seine Freigabe bleibt abgeschlossen. Die separat freigegebene Korrektur auf Head `b81f017b2ca7f83c34e9dea13a4b45e5ea46afa1` und Planhash `2266546dc0323ff2119ca6a3429c57dbc4b69c3656fdc2914037f950f7d9b8c4` ist ausgeführt: LinkedAsset→Assets.Title und siebenstufiger ChangeStatus ohne neue Indizes, genau 13 neue Runtimezeilen und ein ObjectTypes/Change.AllowVersioning-Update. Versionierung war bereits aktiv; Listsetting-/Index-Writes 0. Alle bisherigen Werte/Versionen und 874 anderen bestehenden Metadatenzeilen bleiben nativ erhalten. Der isolierte Generatorvertrag erhält 31 alte Architekturfelder und 1.017 andere generierte Zeilen.

**P3a Schema-/Referenzbrücke umgesetzt (08.10.2026):** Zwei nicht indizierte Changes-Spalten, 13 neue Metadatenzeilen und ein gezieltes ObjectTypes-Update sind nativ belegt; Geschäftsbestand, 874 andere bestehende Metadatenzeilen, 20 Indizes und Listsettings bleiben erhalten. Die geprüfte Studio-Kopie enthält 20 Quellen und 19 schreibbare Change-Pilotfelder; ausschließlich die erzeugte msapr-Referenz wurde übernommen. Der P3b-Vorcheck bestätigt erstmals gespeichert 203 bei Live 202 und liest Changes direkt im gespeicherten Studio. Beide PAC-Lesewege liefern noch den unveränderten Live-Host 202 als Rückweg. Alle P3a-Kontingente bleiben verbraucht.

**P3b DEV 30450 gestoppt, Reparatur 30451 lokal (08.10.2026):** Der freigegebene einmalige Import von Head `8750c8c56da5a26485e413590ead4264fe247cd0` endet mit PAC Exit 0; Maker zeigt Canvas 204 Live als Plattformfolge. Der Nach-Import-Export ist bytegleich zum freigegebenen msapp, vier Src-YAMLs bytegleich und 20 Quellen erhalten. Studio öffnet die Quelle nicht: PA2108 für `AccessibleLabel` an den beiden neuen `Classic/Button@2.2.0`-Entscheidungsbuttons. Sofortiger Write-Stopp: kein manueller Save, gezieltes Publish oder Change-Save. Vollständiger Nach-/Abschlussvergleich aller sechs Listen erhält sämtliche Werte/Versionen, Spalten und Settings. Die Lesesitzung endet mit Exit 0; Import 1/1, Exporte 3/4, übrige Schreibkontingente 0. Der alte Scope erlaubt keine weiteren Writes oder Retries.

**Lokaler Reparaturkandidat 30451:** Die beiden Zusatzhinweise verwenden das unterstützte `Tooltip`; sichtbarer Text, Tastatur/Fokus und sämtliche Genehmigungs-/Save-Regeln bleiben erhalten. Das vorhandene Accessibility-Gate umfasst jetzt alle drei neuen Change-Buttons und die Change-Galerie; der YAML-Parser weist diese native PA2108-Konstellation für jeden Classic-Button ab. Der alte 30450-Source wird von beiden Prüfungen mit passendem Fehlergrund abgewiesen. 24/24 verfügbare Gates und Pack/Unpack/Solution-Pack Exit 0, 2.948 tatsächliche Power-Fx-Assertions, 66 Formeln und 18 Python-Regressionen; vier YAMLs und eingebettetes msapp bytegleich. 19 Change-Felder und alle 52 Asset-/System-/Change-Patch-Spalten bleiben erhalten. Dieser lokale Stand ging in die unten dokumentierte freigegebene, am Quellen-Laufzeitfehler gestoppte DEV-Abnahme ein; Canvas/Provisioning bleiben `1.0.0-alpha.4.1.0` / `6.2.5`.

**P3b DEV 30451 gestoppt (08.10.2026):** Der erneut ausdrücklich freigegebene Import von Head `d476fcdef88534ebd00ff1aad3e8fe8ba7ff16d8` endet mit PAC Exit 0; Maker bestätigt Canvas **205 Live** als Plattformfolge. Vor-/Nach-Import-Exporte sichern den Rückweg 30450 und das bytegleiche 30451-msapp mit vier identischen Src-YAMLs und 20 Quellen. Studio öffnet die reparierte Quelle; PA2108 tritt beim Öffnen nicht mehr auf. Der echte App-Prüfer zeigt zwei Formel-Delegationswarnungen und **einen Laufzeitfehler an der Datenquelle Changes**. Sofortiger Write-Stopp, kein manueller Save, gezieltes Publish oder Change-Save. Sämtliche Werte/Versionen, Schema und Settings aller sechs Listen bleiben im Abschluss exakt erhalten; Leser Exit 0. Verbrauch: Import 1/1, lesende Exporte 2/4, übrige Schreibkontingente 0. Diese Freigabe ist geschlossen; keine automatische Fortsetzung oder Source-Rebinding.

**Lokaler Reparaturkandidat 30452:** Das unveränderte generierte msapr und msapp verbinden Changes vollständig; die Solution-App-Metadaten registrieren diese Quelle und ihre Tabelle jedoch noch nicht. Der native 30451-Export bestätigt dieselbe Abweichung. Ausschließlich diese zwei Registrierungseinträge werden aus dem bereits kanonischen msapr ergänzt; alle bisherigen Verbindungen, Dataset-/Alias-/Override-Bindungen und Canvas-/Fachformeln bleiben erhalten. Das vorhandene Schreibvertrags-Gate vergleicht jetzt auch die vollständigen Quellen-/Dataset-/API-Registrierungen zwischen kanonischem msapr, gepacktem msapp und Solution. Der echte eingefrorene 30451-Metadatensatz wird mit dem passenden Fehlergrund abgewiesen; sechs synthetische Regressionen decken fehlende Registrierung, falsche Tabellen/API, Dataset-Alias, Servicequelle und Paketpfade ab. **24/24 verfügbare Gates Exit 0**, 2.948 Power-Fx-Assertions, 66 Formeln und 24 Python-Regressionen; Pack/Unpack/Solution-Pack Exit 0, vier YAMLs und msapp bytegleich zum freigegebenen 30451. Solution **1.0.0.30452**; Canvas/Provisioning bleiben `1.0.0-alpha.4.1.0` / `6.2.5`. Kein neuer DEV-Import, keine native Referenz-/Quellübernahme oder funktionale Abnahme; private Belege unter `artifacts/p3-local-30452/` und `dev-abnahme-30451-20261008/`.


Die Korrektur verlangt keine weitere Schema-/Datenmigration, keinen Backfill oder Description-Write. Der neue 30452-Import und die verbleibende Maker-/Funktionsabnahme benötigen eine neue konkrete Freigabe; keine automatische DEV→Git-Quellübernahme. [Kandidat, Grenzen und primärer Abnahmescope](docs/development/Stage-4.1-P3-Change.md).

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
