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
- Der Datensatzkern (Roadmap P1) ergänzt im lokalen Kandidaten 30441 Liste, Laden und Bearbeiten für Asset/System; die DEV-Abnahme ist offen. Change folgt im ersten Produktivumfang (P3); Incident/Problem werden nachfolgend eingebunden.

## Abnahmekriterien

- `pwsh ./powerplatform/scripts/Validate-ObjectProviderRegistry.ps1` läuft erfolgreich.
- `pwsh ./powerplatform/scripts/Sync-ObjectProviderRuntime.ps1` erzeugt bzw. aktualisiert die Runtime idempotent.
- `pwsh ./powerplatform/scripts/Sync-ObjectProviderRuntime.ps1 -CheckOnly` läuft danach erfolgreich.
- `colObjectProviderRegistry` ist in `App.pa.yaml` vorhanden.
- `gblActiveProvider` wird bei Objekttypauswahl gesetzt.
- **Neu** ist ohne passende Create-/Save-Capabilities deaktiviert; Save prüft Provider, Modus und ID.
- `Test-CanvasCapabilities.ps1 -PowerFxDirectory <PAC-Library-Verzeichnis>` prüft die tatsächlichen Guard-/Revalidierungsformeln offline mit der Power-Fx-Engine (137 Assertions; ergänzend Choice 212 und Record Core 275 am Kandidaten 30441). Die Engine-DLLs stammen aus der lokal installierten PAC-Toolchain; die bestehende CI führt diesen optionalen Engine-Test nicht aus.
- Abschlusskriterium: vollständiger Build und DEV-Speicher-/Quellen-/Bereinigungstest müssen erfolgreich sein. Build und begrenzte P0-Choice-Quellenabnahme von 30440 sind erfolgreich; keine vollständige Asset-/Produktivabnahme.

## Historische P0-Baseline und Title-Reparatur

30431 / Canvas 168 belegte den erforderlichen Studio-Verarbeitungsschritt nach SourceCode-Import; die direkte Importversion führte noch alte interne Regeln aus. Die `.msapr`-Pack-Baseline behält historische Controls/SARIF und ist keine aktuelle Maker-Abnahme. 30432 ergänzte den nativen verpflichtenden Asset-Title und genau zwei Metadatenzeilen. Seine unzulässigen Classic-Button-Properties wurden in 30433 korrigiert; 30434/35 reparierten Galerieereignisse. Details und Versionen stehen historisch in der [P0-Abnahme](Stage-4.1-P0-Abnahme.md); aktueller Stand und einziges Folgepaket folgen unten.

## P0-Host-/Choice-Abnahme: aktueller Kandidat 30440

**DEV 30440 / Canvas 184 Live, P0 technisch abgeschlossen (02.10.2026).** Import ohne Publish All Exit 0, Postimport-msapp bytegleich mit Kandidat. Unterstütztes Studio-Items-Rebinding erhält die kanonische Formel; lesender Export bestätigt die generierte V2-Personensuche, feldbezogenen Choice-Default, AllowEmptySelection, zehn native Choice-Adapter und beide Save-Guards. Kein privater YAML-/Pack-Hack und kein Source-Takeover.

Genau ein zusätzlicher ausdrücklich freigegebener Save ID 9 im frischen Player: Title getrimmt, Owner korrekt und Kritikalität stabil angezeigt/Quelle **Hoch**. Busy sperrte Save/Abbruch/Navigation. Ausschließlich ID 9 mit passendem synthetischem Titel reversibel bereinigt; ID-gefilterte Liste leer, Papierkorb/Herkunft Assets belegt, vier Bestandsassets erhalten. Historisch scheiterte ID 8 unter 30439 und wurde bereinigt; alter Player vor aktuellem Test ohne Save verworfen.

Studio-184-Checker vor Veröffentlichung: keine Formel-/Laufzeitbefunde; zwei ungenutzte Quellen, 56 Accessibility-Befunde und zwölf Leistungswarnungen. 347 Offline-Power-Fx-Assertions, Quell-/Compiler-/Personenverträge, Build und verfügbare Projekt-Gates bestehen. Reine Tastatur-Persistenz der Personenauswahl und vollständige Asset-/Rollen-/Reviewabnahme bleiben offen; Neu-Fokus nach Verwerfen nun beobachtet. Details: [P0-Abnahme](Stage-4.1-P0-Abnahme.md).

## P1: lokaler Datensatzkern 30441

Native Asset-/System-Galerien verwenden direkte Titelanfangsfilter oder ID-Gleichheit und ID-Sortierung; die Galerie lädt weitere Datensätze beim Blättern. Keine lokale Gesamtzahl oder vorgeschaltete begrenzte Datensatzcollection. Load speichert den originalen nativen Record und hydriert genau den vorhandenen Patch-Vertrag (Asset 17 / System 16 Felder). Metadatentyp/-vollständigkeit und unbekannte Choices sperren Save; unveränderte Personenobjekte bleiben erhalten. Edit benötigt geladene ID, vollständigen Load, echte Änderung und konfliktfreien Stand. Frische Modified-Prüfung und `ErrorKind.Conflict` geben sichtbare Fehler; der atomare Connector-Konfliktschutz ist in DEV zu prüfen.

Die sieben bisher nicht ausführbaren Registry-Typen melden nun auch List/Create als false; Asset/System behalten alle vier Fähigkeiten. System-Title benötigt genau zwei neue Metadatenzeilen; bestehende Asset-Title-Metadaten und alle anderen Zeilen bleiben erhalten. Zusätzlich prüft die CI `Test-CanvasRecordCore.ps1`; lokal prüft die tatsächliche Power-Fx-Engine 275 Record-Assertions, zusammen 624. Diese Tests ersetzen keine Maker-/Connector-Abnahme.

**Einziger primärer nächster Schritt: P1 · DEV-Abnahme des Datensatzkerns**, Modellklasse `deep-reasoning`, mit dem konkret begrenzten [Test-/Freigabeplan](Stage-4.1-P1-Datensatzkern.md). Keine neue DEV-Aktion in der lokalen P1-Umsetzung. Vollständige Asset-Mappings/Verantwortliche/Reviewtermin folgen P2 nach erfolgreichem P1-Round-Trip; keine Produktivfreigabe oder implizite Stage-4.1-Integration.
