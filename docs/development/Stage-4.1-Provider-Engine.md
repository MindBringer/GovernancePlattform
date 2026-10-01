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

Die Save-Schaltfläche und die Editor-Revalidierung prüfen ebenfalls den passenden Provider und `SupportsSave`. Im Modus `New` ist zusätzlich `SupportsCreate` nötig; `Edit` erfordert `SupportsEdit` und eine positive Datensatz-ID. Unbekannte Modi und fehlende Provider bleiben gesperrt. Auch ein veraltetes `gblEditorCanSave = true` kann die Save-Sperre nicht umgehen. Das ist eine UI-/Ausführungsgrenze, keine zusätzliche SharePoint-Berechtigung.

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
- Der Datensatzkern (Roadmap P1) ergänzt Liste, Laden und Bearbeiten. Change folgt im ersten Produktivumfang (P3); Incident/Problem werden nachfolgend eingebunden.

## Abnahmekriterien

- `pwsh ./powerplatform/scripts/Validate-ObjectProviderRegistry.ps1` läuft erfolgreich.
- `pwsh ./powerplatform/scripts/Sync-ObjectProviderRuntime.ps1` erzeugt bzw. aktualisiert die Runtime idempotent.
- `pwsh ./powerplatform/scripts/Sync-ObjectProviderRuntime.ps1 -CheckOnly` läuft danach erfolgreich.
- `colObjectProviderRegistry` ist in `App.pa.yaml` vorhanden.
- `gblActiveProvider` wird bei Objekttypauswahl gesetzt.
- **Neu** ist ohne passende Create-/Save-Capabilities deaktiviert; Save prüft Provider, Modus und ID.
- `Test-CanvasCapabilities.ps1 -PowerFxDirectory <PAC-Library-Verzeichnis>` prüft die tatsächlichen Guard-/Revalidierungsformeln offline mit der Power-Fx-Engine (76 Assertions am Reparaturkandidaten 30432). Die Engine-DLLs stammen aus der lokal installierten PAC-Toolchain; die bestehende CI führt diesen optionalen Engine-Test nicht aus.
- Abschlusskriterium: vollständiger Build und DEV-Speicher-/Quellen-/Bereinigungstest müssen erfolgreich sein. Der Build ist belegt; die Live-Speicherabnahme von 30432 steht noch aus.

## P0-Kandidat vom 01.10.2026

Solution `1.0.0.30431` wurde nach ausdrücklicher Freigabe am 01.10.2026 in DEV importiert. Nach dem erforderlichen Studio-Verarbeitungsschritt wurde Canvas 168 veröffentlicht und als Live geprüft. SourceCode-Pack/Unpack und Capability-Tests sind keine Maker-Abnahme. Die `.msapr`-Pack-Baseline behält alte interne Controls und SARIF-Meldungen, einschließlich der früheren CountRows-Warnung; sie wurde nicht manuell als zweite Quelle bearbeitet. Die direkte Importversion 167 führte noch alte Neu-Regeln aus; erst das Öffnen/Verarbeiten in Studio und Veröffentlichen der 168 aktivierten die geprüften YAML-Regeln. Dieser Maker-Schritt ist deshalb ein verbindliches Abnahmegate nach SourceCode-Pack und Import; Import/Publish allein genügt nicht. Die verbleibenden Prüfungen und der kontrollierte Asset-Smoke stehen in [Stage-4.1-P0-Abnahme.md](Stage-4.1-P0-Abnahme.md).

## P0-Reparaturkandidat 30432 (lokal)

Asset-Title wird aus der führenden Architektur als verpflichtender Text erzeugt; zwei zusätzliche Title-Metadatenzeilen erhalten SortOrder 0, vorhandene Zeilen bleiben unverändert. Initialisierung liest auch FieldDefinitions.IsRequired. Save und Revalidierung verlangen für Asset einen nicht leeren, maximal 255 Zeichen langen Titel; der Patch trimmt ohne generischen Fallback. Acht Aktionen/Auswahlen sind Classic-Buttons, Eingaben/Galerien haben expliziten Tastatur-/Fokus-/Labelvertrag und der Verwerfen-Dialog sperrt den Hintergrund. 76 Offline-Power-Fx-Assertions, neue Metadaten-/Accessibility-Gates und PAC-Build/Round-Trip bestehen. DEV bleibt 30431 / Canvas 168; neue Metadatenübernahme und Import/Studio-Veröffentlichung brauchen konkrete Freigabe. Nächstes Paket ist allein die P0-DEV-Abnahme von 30432 gemäß [P0-Abnahme](Stage-4.1-P0-Abnahme.md).
