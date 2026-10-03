# Stage 4.1 – Runtime Provider Engine

## Ziel

Stage 4.1 überführt die statische `ObjectProviderRegistry.json` in eine typisierte Canvas-Laufzeitcollection. Die Registry wird damit nicht nur dokumentiert und validiert, sondern steuert sichtbare Fähigkeiten der App.

## Führende Quelle

```text
powerplatform/config/ObjectProviderRegistry.json
```

Aus dieser Datei erzeugt `Sync-ObjectProviderRuntime.ps1` den Laufzeitblock in `App.pa.yaml` sowie eine lesbare Zwischenrepräsentation unter:

```text
powerplatform/generated/ObjectProviderRuntime.powerfx
```

Die JSON-Registry bleibt die einzige manuell gepflegte Quelle.

## Laufzeitmodell

`colObjectProviderRegistry` enthält pro Objekttyp:

- `ObjectTypeKey`
- `DataSourceKey`
- `TitleField`
- `GovernanceIdField`
- `ActiveField`
- `SupportsList`
- `SupportsCreate`
- `SupportsEdit`
- `SupportsSave`

Beim Auswählen eines Objekttyps wird der passende Datensatz in `gblActiveProvider` aufgelöst.

## Erste capability-gesteuerte Funktion

Der globale **Neu**-Befehl ist nicht mehr nur vom ausgewählten Objekttyp abhängig. Er wird nur aktiviert, wenn der aktive Provider zur Auswahl passt und sowohl `SupportsCreate = true` als auch `SupportsSave = true` meldet. Während eines Speichervorgangs bleibt er deaktiviert. `OnSelect` prüft den aktuellen `DisplayMode` vor jeder Editor-Mutation.

Die Save-Schaltfläche und die Editor-Revalidierung prüfen ebenfalls den passenden Provider und `SupportsSave`. Im Modus `New` ist zusätzlich `SupportsCreate` nötig; `Edit` erfordert `SupportsEdit`, eine positive und übereinstimmende geladene ID, vollständige Hydrierung, echte Änderungen und keinen Konflikt. Load/Save sperren Eingaben und Navigation. Unbekannte Modi und fehlende Provider bleiben gesperrt. Auch ein veraltetes `gblEditorCanSave = true` kann die Save-Sperre nicht umgehen. Das ist eine UI-/Ausführungsgrenze, keine zusätzliche SharePoint-Berechtigung.

Die nicht delegierbare Asset-Gesamtzahl wurde aus dem lokalen Dashboard entfernt. Verlässliche Fachkennzahlen folgen nach dem Datensatzkern; die übrigen Metadatenzähler bleiben unverändert.

## Build-Integration

Der Build führt in dieser Reihenfolge aus:

1. Versionsabgleich
2. Registry-Validierung
3. Synchronisierung der Provider-Runtime
4. Korrektur lokalisierter Connectorreferenzen
5. Canvas-Validierung
6. Provider-Runtime-Prüfung im Check-Only-Modus
7. Canvas- und Solution-Pack

Der Synchronisierer ist idempotent. Bei unveränderter Registry entstehen keine zusätzlichen Änderungen.
Die Repository-CI führt Canvas-Validierung, Registry-Validierung und Runtime-Prüfung im Check-Only-Modus aus. Eine fehlende Synchronisierung stoppt die CI, statt dort automatisch Quellcode zu verändern.
Zusätzlich prüft sie, dass das versionierte `.msapp` die vier kanonischen Canvas-YAMLs enthält.

## DEV-Baseline vom 28.09.2026

Ein read-only PAC-Export aus DEV zeigte denselben Canvas-SourceCode wie der fachliche Reconciliation-Commit `dec366c` des isolierten Konformitätszweigs. Gegenüber dem älteren Stage-4.1-Branch enthält DEV Änderungen an Personenfeld-Bindungen und der Asset-Speicherung. Die DEV-Solution hat die Paketversion `1.0.0.30428`.

Für den Git-Kandidaten wurde ein diagnostisches Label mit festem Suchwert aus dem Canvas-YAML entfernt und das Paket lokal neu gebaut. Der PAC-SourceCode-Pack kann interne Steuerdaten aus der älteren `.msapr`-Ausgangsressource behalten. Deshalb müssen die bereinigte App und ihre Personen-/Asset-Funktionen in Power Apps Studio geprüft werden; ein erfolgreicher Pack und der YAML-Vergleich sind dafür noch kein Ersatz. Import und Publish sind keine Repository-CI-Schritte.

## Sicherheitsgrenzen

- Datenquellen werden weiterhin statisch in Power Fx adressiert; Power Apps erlaubt keine dynamische Dereferenzierung aus Textwerten.
- Die Registry steuert Fähigkeiten und Providerauflösung, ersetzt aber noch nicht die statischen Save-Zweige.
- Der Datensatzkern (Roadmap P1) ergänzt Liste, Laden und Bearbeiten für Asset/System. DEV 30444/193 Live, beide generierten Suchbindungen und native Formelprüfung belegt; Titeleingabe, beide Creates und unverändertes Wiederöffnen bestanden. Erster System-Edit nicht persistiert, Quelle Version 1.0/unverändert, Folge-Edits gestoppt und beide Testdatensätze reversibel bereinigt. 725 Assertions/Build/Round-Trip/18 Gates gelten für unveränderten Quellkandidaten; System-/Lookup-Round-Trip offen. Nächstes Paket: verbundener Live-Monitor mit einem konkret begrenzten neuen System-Test zur Freigabe; keine neue App-Version oder vermutete Code-Reparatur. Change folgt P3, Incident/Problem später.

## Abnahmekriterien

- `pwsh ./powerplatform/scripts/Validate-ObjectProviderRegistry.ps1` läuft erfolgreich.
- `pwsh ./powerplatform/scripts/Sync-ObjectProviderRuntime.ps1` erzeugt bzw. aktualisiert die Runtime idempotent.
- `pwsh ./powerplatform/scripts/Sync-ObjectProviderRuntime.ps1 -CheckOnly` läuft danach erfolgreich.
- `colObjectProviderRegistry` ist in `App.pa.yaml` vorhanden.
- `gblActiveProvider` wird bei Objekttypauswahl gesetzt.
- **Neu** ist ohne passende Create-/Save-Capabilities deaktiviert; Save prüft Provider, Modus und ID.
- `Test-CanvasCapabilities.ps1 -PowerFxDirectory <PAC-Library-Verzeichnis>` prüft die tatsächlichen Guard-/Revalidierungsformeln offline mit der Power-Fx-Engine (137 Assertions; ergänzend Choice 212 und Record Core 376 am Kandidaten 30444). Die Engine-DLLs stammen aus der lokal installierten PAC-Toolchain; die bestehende CI führt diesen optionalen Engine-Test nicht aus.
- Abschlusskriterium: vollständiger Build und DEV-Speicher-/Quellen-/Bereinigungstest müssen erfolgreich sein. Build und begrenzte P0-Choice-Quellenabnahme von 30440 sind erfolgreich; keine vollständige Asset-/Produktivabnahme.

## Historische P0-Baseline und Title-Reparatur

30431 / Canvas 168 belegte den erforderlichen Studio-Verarbeitungsschritt nach SourceCode-Import; die direkte Importversion führte noch alte interne Regeln aus. Die `.msapr`-Pack-Baseline behält historische Controls/SARIF und ist keine aktuelle Maker-Abnahme. 30432 ergänzte den nativen verpflichtenden Asset-Title und genau zwei Metadatenzeilen. Seine unzulässigen Classic-Button-Properties wurden in 30433 korrigiert; 30434/35 reparierten Galerieereignisse. Details und Versionen stehen historisch in der [P0-Abnahme](Stage-4.1-P0-Abnahme.md); aktueller Stand und einziges Folgepaket folgen unten.

## P0-Host-/Choice-Abnahme: aktueller Kandidat 30440

**DEV 30440 / Canvas 184 Live, P0 technisch abgeschlossen (02.10.2026).** Import ohne Publish All Exit 0, Postimport-msapp bytegleich mit Kandidat. Unterstütztes Studio-Items-Rebinding erhält die kanonische Formel; lesender Export bestätigt die generierte V2-Personensuche, feldbezogenen Choice-Default, AllowEmptySelection, zehn native Choice-Adapter und beide Save-Guards. Kein privater YAML-/Pack-Hack und kein Source-Takeover.

Genau ein zusätzlicher ausdrücklich freigegebener Save ID 9 im frischen Player: Title getrimmt, Owner korrekt und Kritikalität stabil angezeigt/Quelle **Hoch**. Busy sperrte Save/Abbruch/Navigation. Ausschließlich ID 9 mit passendem synthetischem Titel reversibel bereinigt; ID-gefilterte Liste leer, Papierkorb/Herkunft Assets belegt, vier Bestandsassets erhalten. Historisch scheiterte ID 8 unter 30439 und wurde bereinigt; alter Player vor aktuellem Test ohne Save verworfen.

Studio-184-Checker vor Veröffentlichung: keine Formel-/Laufzeitbefunde; zwei ungenutzte Quellen, 56 Accessibility-Befunde und zwölf Leistungswarnungen. 347 Offline-Power-Fx-Assertions, Quell-/Compiler-/Personenverträge, Build und verfügbare Projekt-Gates bestehen. Reine Tastatur-Persistenz der Personenauswahl und vollständige Asset-/Rollen-/Reviewabnahme bleiben offen; Neu-Fokus nach Verwerfen nun beobachtet. Details: [P0-Abnahme](Stage-4.1-P0-Abnahme.md).

## P1: Datensatzkern, DEV 30444 und offene Abnahme

Native Asset-/System-Galerien verwenden direkte Titelanfangsfilter oder ID-Gleichheit und ID-Sortierung; die Galerie lädt weitere Datensätze beim Blättern. Keine lokale Gesamtzahl oder vorgeschaltete begrenzte Datensatzcollection. Load speichert den originalen nativen Record und hydriert genau den vorhandenen Patch-Vertrag (Asset 17 / System 16 Felder). Metadatentyp/-vollständigkeit und unbekannte Choices sperren Save; unveränderte Personenobjekte bleiben erhalten. Edit benötigt geladene ID, vollständigen Load, echte Änderung und konfliktfreien Stand. Frische Modified-Prüfung und `ErrorKind.Conflict` geben sichtbare Fehler; der atomare Connector-Konfliktschutz ist in DEV zu prüfen.

Die sieben bisher nicht ausführbaren Registry-Typen melden nun auch List/Create als false; Asset/System behalten alle vier Fähigkeiten. Genau zwei System-Title-Metadaten wurden freigegeben in DEV gespeichert und nach Reload geprüft; keine erneuten Writes. Import 30441 ohne Publish All/`--publish-changes` und bytegleicher Postexport bestehen, Maker zeigt 185 Live; Studio scheitert an PA1001/YamlInvalidSyntax in der Öffnen-Beschriftung. Beide Beschriftungen sind im lokalen Kandidaten 30442 als Blockskalare korrigiert, Formeln unverändert. Echter YAML-Parser vor Pack/in CI und vier Regressionstests ergänzt; CI prüft weiter `Test-CanvasRecordCore.ps1`, lokal 281 Record-Assertions, zusammen 630/53 geparste Formeln. Nach freigegebenem 30442-Import (bytegleicher Postexport, 186 Live) öffnet Studio erfolgreich, speichert 187 automatisch und meldet zwei Formelbefunde im aliasten Formularfilter. `formField.ObjectTypeKey` ist im 30443-Kandidaten explizit qualifiziert. Neuer Engine-Test des tatsächlichen Filters reproduziert beide früheren Hostfehler und besteht nach Korrektur mit sechs zusätzlichen Assertions; CI-Aliasvertrag ergänzt. Keine fachlichen Writes oder gezielte Publikation. Alle 18 verfügbaren Gates und Build bestehen. Diese Tests ersetzen keine Maker-/Connector-Abnahme.

30443 wurde anschließend ausdrücklich freigegeben importiert und zunächst als 189 veröffentlicht. Die zurückgesetzten öffentlichen Personenfelder sind inzwischen kanonisch wiederhergestellt; gespeicherter Draft 190 und publizierter Export 191 enthalten identische Controls-JSONs und die korrekte generierte V2-Suche. Formelchecker ohne Fehler, keine neue Fachformel/Quellübernahme. Beide synthetischen Creates und sauberes Laden bestehen, Asset-Titel-Edit ist quellenbestätigt; System-Titel-Edit einmal versucht, Quelle unverändert bei Version 1.0. Lookup-Suchregel verwendet noch `ComboBoxSample`. Asset-Modified-Konflikt sichtbar blockiert, Quellversion 3.0 erhalten; kein atomarer ETag-Nachweis. Beide Testdatensätze reversibel bereinigt. P1 bleibt offen, fachliche Write-Kontingente verbraucht.

30444 wurde genau einmal ohne Publish All/`--publish-changes` importiert: PAC Timeout / Exit 1, serverseitiger Erfolg und bytegleicher Postexport / Exit 0. Studio-Sperre inzwischen ohne Überschreibung gelöst; beide öffentlichen Suchbindungen je einmal regeneriert. Gespeicherter Draft und publizierter Export enthalten kanonische Load-/Payload-/Default-/Items-Formeln und echte generierte Suchquellen statt `ComboBoxSample`. Native Formelprüfung fehlerfrei, ein manueller Save-Versuch und eine gezielte App-Veröffentlichung, Maker **193 Live**. Im publizierten Export sind sämtliche kompilierten Control-Regeln exakt gleich dem akzeptierten Draft; Paketdateien bei identischen Control-Regeln nicht bytegleich. Keine DEV→Git-Übernahme.

Die vorherige Titelblockade wurde im getrennten sichtbaren Player aufgelöst: Zeichenweise Eingabe mit Fokuswechsel übernimmt den Titel korrekt. Titel-/Revalidierungsregeln im publizierten Artefakt entsprechen kanonischen Quellen; keine Formeländerung. Asset ID 11 und System ID 3 angelegt und unverändert wieder geöffnet, Player nach Asset-Create frisch gestartet. System-Lookup bleibt semantisch leer (`0;#` in der Quelle). Erster System-Titel-Edit nach einem UI-Saveversuch nicht persistiert; alter Titel/Version 1.0 und sämtliche sichtbaren Quellfeldbeschreibungen unverändert, Player dirty. Kein Connector-Fehler als Ursache belegt. Vier Folge-Edits gestoppt; System und Asset reversibel gelöscht, Papierkorb/Herkunft und Vorbestand Assets 4–7/Systems leer belegt. Verbrauch Creates 2/2, System-Edit-Versuche 1/5, Deletes 2/2; Save-Retries und übrige fachliche Writes 0. P1 nicht abgenommen. Live-Monitor eingerichtet, native Textänderung/OnChange-LookUp erfolgreich aufgezeichnet; zum Handoff Getrennt, Verbindung vor Saves erneuern. Keine zusätzlichen Saves.

**P1 · überwachte System-Save-Diagnose auf 30444/193**, Modellklasse `deep-reasoning`: im eingerichteten Live-Monitor nach erneuter Verbindung den Beginn des Speicherereignisses und eine mögliche SharePoint-Anfrage unterscheiden. Ein ungespeicherter synthetischer System-Entwurf mit gültigem Titel, zugelassenem Testkonto, Entwurf/Hoch und leerem Lookup ist vorbereitet. Neuer konkreter DEV-Scope zur Freigabe: höchstens ein System-Create, ein Titel-Edit bei leerem Lookup und eine reversible Löschung ausschließlich dieses ID-/Marker-bestätigten Systems; kein Asset-Write. Genau ein Speicheraufruf je Schritt, vorab Verbrauch reservieren, Monitor/Quellenversion/Felder/Wiederöffnen belegen; bei unklarem oder fehlgeschlagenem Ergebnis keine Wiederholung oder abhängigen Writes, anschließend begrenztes Cleanup. Die bisherige 30444-Folge ist nach dem nicht persistierten ersten System-Edit gestoppt und bereinigt; ihre vier nicht ausgeführten Folge-Edits autorisieren keine neue Reproduktion. Kein Import, Rebinding, Studio-Save, Publish, Metadaten-/Bestands-/Konflikt-Write oder DEV→Git. Erst belegte Ursache rechtfertigt einen lokalen Reparaturkandidaten; P2 nach P1-Abnahme. [P1-Plan und Grenzen](Stage-4.1-P1-Datensatzkern.md). Vollständige Asset-Mappings/Verantwortliche/Reviewtermin folgen P2; keine Produktivfreigabe oder implizite Integration.
