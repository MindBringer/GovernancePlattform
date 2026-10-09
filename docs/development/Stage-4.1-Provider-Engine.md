# Stage 4.1 – Runtime Provider Engine

## Aktueller Stand (09.10.2026)

**P2-DEV-Abnahme abgeschlossen (07.10.2026): Solution 30449 / Canvas 202 Live und gespeichert.** Der separat freigegebene Save am synthetischen Asset 13 leert alle sechs Choices als native null und erhöht die Version von 16.0 auf 17.0; die übrigen 25 deklarierten Felder bleiben erhalten. Sauberes Wiederöffnen zeigt leere Auswahlen, beide Reviewpicker mit leerem DOM-value und placeholder, „Keine Änderungen“ und gesperrtes Save. Asset 13 anschließend genau einmal reversibel bereinigt und nach Marker, Listenherkunft und ID im ersten Papierkorb nachgewiesen. Der vollständige ursprüngliche Bestand ist wiederhergestellt: Assets 4–7 mit sämtlichen nativen Werten/Versionen unverändert, Systems leer. Der erfolgreiche Create und alle fünf Personenwechsel/-Leerungen sowie Review-/Zyklus-/Boolean-Tests unter 30447 bleiben Teil der P2-Evidenz. Gespeicherter und veröffentlichter Host sind in vier Controls-/DataSources-Dateien bytegleich; 84 kanonische/92 kompilierte Controls, beide echten Suchregeln und 19 unveränderte Quellen geprüft. Formel-/Laufzeitchecker ohne Fehler; 72/12/2 Warnungen bleiben. Native ReviewCycleMonths-Min/Max, Produktivrollen und atomarer ETag-Konfliktschutz bleiben für P7 offen; P2 ist keine Produktivfreigabe. [P2-Vertrag und separate Abnahme](Stage-4.1-P2-Asset-Verantwortliche.md).

**P3b Pflichtfeldkorrektur vollständig belegt (09.10.2026):** Criticality und ChangeType sind in der Changes-Liste jetzt optional; auch ihre beiden Feldverknüpfungen im lokalen Content-Type „Governance Change“ sind optional. Title bleibt das einzige permanente Pflichtfeld, ChangeType bleibt beim Einreichen fachlich erforderlich. Die Content-Type-Ergänzung wurde ausdrücklich zusätzlich freigegeben. Ein Lese-Timeout nach dem erfolgreichen Criticality-Update schloss den ersten Schreibscope; ein vollständiger rein lesender Abschluss bestätigt die Änderung. Nach erneuter ausdrücklicher Freigabe wurde ausschließlich das noch erforderliche ChangeType-Listenflag korrigiert. Kein Write-Retry und keine Wiederholung der bereits erfolgreichen Updates.

Der vollständige native Abschlussvergleich aller sechs Listen bestätigt sämtliche Bestandswerte/Versionen, Metadaten, Listsettings, 20 Indizes, alle übrigen Feldattribute sowie Site Columns und Site Content Types erhalten. Am ersten Titel-only-Draft wurde im svc-Edge-Player genau ein Save ausgelöst; er scheitert weiterhin an **Criticality ist erforderlich**. Die Quelle enthält danach keinen neuen Datensatz und keine neue ID. Die kanonische msapr, das gepackte msapp und der exportgeprüfte veröffentlichte Host deklarieren noch `schema.items.required=[Title,Criticality,ChangeType]`, während die nativen Listen-/Content-Type-Flags bereits nur Title verlangen. Der alte erzeugte Connectorvertrag ist damit konkret belegt; eine unterstützte Studio-Aktualisierung ist noch ausstehend. Sofortiger Stopp ohne Save-Retry; Create-Versuch **1/3**, Edits **0/8**, Cleanups **0/3**, Datenzeilen-Writes 0. Eigener Draft-Player ohne Save geschlossen, ursprüngliche svc-Tabs erhalten; native Lesesitzung Exit 0. Die Restfreigabe ist wegen dieses neuen Fehlers geschlossen.

Das bestehende Schreibvertrags-Gate prüft jetzt zusätzlich die permanenten Change-Pflichtfelder aus der führenden Architektur gegen die tatsächliche erzeugte Connectorliste, auch für nicht gepatchte Felder wie Criticality. Fünf neue synthetische Regressionen prüfen den konkreten schreibbaren, aber veralteten Vertrag, Titel-only, fehlendes Title, einzelne veraltete Flags und ungültige/duplizierte Deklarationen. Die tatsächlichen kanonischen, gepackten und publizierten Referenzen werden mit passendem Fehlergrund abgewiesen. CI führt jetzt auch dieses bestehende Gate am echten Artefakt aus. **22/24 Abschluss-Gates Exit 0; nativer Pflichtfeldvertrag Exit 0, Referenz-/Schreibvertrags-Gates jeweils korrekt Exit 1 mit demselben veralteten Connectorvertrag.** 2.948 Power-Fx-Assertions, 66 Formeln und **29 Python-Regressionen** bestehen. Canvasquellen, msapr/msapp, versiegeltes ZIP und Versionen unverändert; kein neuer Build, Import, Studio-Save, Publish, Export oder DEV→Git in dieser Abnahme. Das svc-Edge-Fenster bestätigt weiterhin **207 Live**. Pester fehlt; PAC 2.9.3 canvas validate unsupported. Private Belege: `dev-pflichtfeldabnahme-30452-contenttype-20261008/` und `dev-pflichtfeldabnahme-30452-rest-20261009/`; keine Rohbelege versioniert.

**P3a Schema-/Referenzbrücke umgesetzt (08.10.2026):** Zwei nicht indizierte Changes-Spalten, 13 neue Metadatenzeilen und ein gezieltes ObjectTypes-Update sind nativ belegt; Geschäftsbestand, 874 andere bestehende Metadatenzeilen, 20 Indizes und Listsettings bleiben erhalten. Die geprüfte Studio-Kopie enthält 20 Quellen und 19 schreibbare Change-Pilotfelder; ausschließlich die erzeugte msapr-Referenz wurde übernommen. Der P3b-Vorcheck bestätigt erstmals gespeichert 203 bei Live 202 und liest Changes direkt im gespeicherten Studio. Beide PAC-Lesewege liefern noch den unveränderten Live-Host 202 als Rückweg. Alle P3a-Kontingente bleiben verbraucht.

**P3b DEV 30450 gestoppt, Reparatur 30451 lokal (08.10.2026):** Der freigegebene einmalige Import von Head `8750c8c56da5a26485e413590ead4264fe247cd0` endet mit PAC Exit 0; Maker zeigt Canvas 204 Live als Plattformfolge. Der Nach-Import-Export ist bytegleich zum freigegebenen msapp, vier Src-YAMLs bytegleich und 20 Quellen erhalten. Studio öffnet die Quelle nicht: PA2108 für `AccessibleLabel` an den beiden neuen `Classic/Button@2.2.0`-Entscheidungsbuttons. Sofortiger Write-Stopp: kein manueller Save, gezieltes Publish oder Change-Save. Vollständiger Nach-/Abschlussvergleich aller sechs Listen erhält sämtliche Werte/Versionen, Spalten und Settings. Die Lesesitzung endet mit Exit 0; Import 1/1, Exporte 3/4, übrige Schreibkontingente 0. Der alte Scope erlaubt keine weiteren Writes oder Retries.

**Lokaler Reparaturkandidat 30451:** Die beiden Zusatzhinweise verwenden das unterstützte `Tooltip`; sichtbarer Text, Tastatur/Fokus und sämtliche Genehmigungs-/Save-Regeln bleiben erhalten. Das vorhandene Accessibility-Gate umfasst jetzt alle drei neuen Change-Buttons und die Change-Galerie; der YAML-Parser weist diese native PA2108-Konstellation für jeden Classic-Button ab. Der alte 30450-Source wird von beiden Prüfungen mit passendem Fehlergrund abgewiesen. 24/24 verfügbare Gates und Pack/Unpack/Solution-Pack Exit 0, 2.948 tatsächliche Power-Fx-Assertions, 66 Formeln und 18 Python-Regressionen; vier YAMLs und eingebettetes msapp bytegleich. 19 Change-Felder und alle 52 Asset-/System-/Change-Patch-Spalten bleiben erhalten. Dieser lokale Stand ging in die unten dokumentierte freigegebene, am Quellen-Laufzeitfehler gestoppte DEV-Abnahme ein; Canvas/Provisioning bleiben `1.0.0-alpha.4.1.0` / `6.2.5`.

**P3b DEV 30451 gestoppt (08.10.2026):** Der erneut ausdrücklich freigegebene Import von Head `d476fcdef88534ebd00ff1aad3e8fe8ba7ff16d8` endet mit PAC Exit 0; Maker bestätigt Canvas **205 Live** als Plattformfolge. Vor-/Nach-Import-Exporte sichern den Rückweg 30450 und das bytegleiche 30451-msapp mit vier identischen Src-YAMLs und 20 Quellen. Studio öffnet die reparierte Quelle; PA2108 tritt beim Öffnen nicht mehr auf. Der echte App-Prüfer zeigt zwei Formel-Delegationswarnungen und **einen Laufzeitfehler an der Datenquelle Changes**. Sofortiger Write-Stopp, kein manueller Save, gezieltes Publish oder Change-Save. Sämtliche Werte/Versionen, Schema und Settings aller sechs Listen bleiben im Abschluss exakt erhalten; Leser Exit 0. Verbrauch: Import 1/1, lesende Exporte 2/4, übrige Schreibkontingente 0. Diese Freigabe ist geschlossen; keine automatische Fortsetzung oder Source-Rebinding.

**Historischer lokaler Reparaturkandidat 30452 vor DEV-Abnahme:** Das unveränderte generierte msapr und msapp verbinden Changes vollständig; die Solution-App-Metadaten registrieren diese Quelle und ihre Tabelle jedoch noch nicht. Der native 30451-Export bestätigt dieselbe Abweichung. Ausschließlich diese zwei Registrierungseinträge werden aus dem bereits kanonischen msapr ergänzt; alle bisherigen Verbindungen, Dataset-/Alias-/Override-Bindungen und Canvas-/Fachformeln bleiben erhalten. Das vorhandene Schreibvertrags-Gate vergleicht jetzt auch die vollständigen Quellen-/Dataset-/API-Registrierungen zwischen kanonischem msapr, gepacktem msapp und Solution. Der echte eingefrorene 30451-Metadatensatz wird mit dem passenden Fehlergrund abgewiesen; sechs synthetische Regressionen decken fehlende Registrierung, falsche Tabellen/API, Dataset-Alias, Servicequelle und Paketpfade ab. **24/24 verfügbare Gates Exit 0**, 2.948 Power-Fx-Assertions, 66 Formeln und 24 Python-Regressionen; Pack/Unpack/Solution-Pack Exit 0, vier YAMLs und msapp bytegleich zum freigegebenen 30451. Solution **1.0.0.30452**; Canvas/Provisioning bleiben `1.0.0-alpha.4.1.0` / `6.2.5`. Kein neuer DEV-Import, keine native Referenz-/Quellübernahme oder funktionale Abnahme; private Belege unter `artifacts/p3-local-30452/` und `dev-abnahme-30451-20261008/`.

**P3b DEV 30452 – Quellenfehler behoben, Suchabnahme gestoppt (08.10.2026):** Der ausdrücklich freigegebene Import von Head `25b2c5cd8e559761c100b45ef0fc144036924be1` endet mit PAC Exit 0; der native Nach-Export bestätigt das unveränderte msapp, vier bytegleiche Src-YAMLs, 20 Quellen und vollständige Solution-Quellen-/Dataset-/API-Registrierungen einschließlich Changes. Studio öffnet; Laufzeitchecker ausdrücklich „Keine Fehler gefunden“, zwei Formel-Delegationswarnungen, 81 Accessibility-, zwölf Leistungs- und zwei Hinweise auf ungenutzte Quellen. Ein manueller Studio-Save und eine echte Studio-Kopie belegen **gespeichert 207 / Live 206**; Live 206 ist die Importfolge, gezieltes Publish 0. Alle 92 kanonischen Controls/Formeln stimmen mit 101 kompilierten Controls überein, keine abweichenden oder ungeprüften Defaults; der native Schreibvertrag für 52 Patch-Felder besteht. Beide generierten Personen-/Lookup-`SearchItems` verwenden jedoch `ComboBoxSample`. Sofortiger Write-Stopp vor Publish und Change-Saves; Rebindings waren auf 0 begrenzt. Alle sechs Listen bleiben mit sämtlichen Werten/Versionen, Schema und Settings exakt erhalten, Leser Exit 0. Verbrauch: Import 1/1, manueller Save 1/1, lesende Exporte 3/4; Publish, Change-Creates/-Edits/Cleanups 0. Der Scope ist geschlossen; kein Retry oder DEV→Git. Private Belege: `dev-abnahme-30452-20261008/`.

**P3b Suchkorrektur 30452 abgeschlossen, Draft-Abnahme gestoppt (08.10.2026):** Die neue ausdrückliche Freigabe umfasst keinen Import. Je ein öffentlicher Personen-/Lookup-Rebinding-Durchlauf, ein zusätzlicher manueller Studio-Save und zwei lesende Exportaufnahmen sind erfolgreich. Beide tatsächlichen generierten Suchregeln verwenden Office365-V2 beziehungsweise colLookupValues und die kanonischen Suchfelder; kein ComboBoxSample. Alle 92 kanonischen/101 kompilierten Controls, Formeln/Defaults, 20 Quellen und der 52-Feld-Schreibvertrag bleiben erhalten. Gezieltes Publish genau einmal; Maker bestätigt **207 Live und gespeichert**, die bestehenden Revisionen wurden aktualisiert. Publizierte Controls und DataSources sind bytegleich zur geprüften Studio-Kopie. Laufzeitchecker ohne Fehler, zwei Delegationswarnungen und 81/12/2 weitere Hinweise bleiben.

Der erste unvollständige synthetische Draft-Create scheitert nativ an **Changes.Criticality ist erforderlich**. Readback bestätigt zusätzlich **ChangeType.Required=true**; Architektur und Runtime-FieldDefinitions definieren beide Felder als optional. Title bleibt das einzige permanente Pflichtfeld; ChangeType ist beim Einreichen fachlich erforderlich. Sofortiger Stopp ohne Retry: kein neuer Datensatz/keine ID, keine Edits oder Cleanups. Alle Werte/Versionen, Schema und Settings der sechs Listen bleiben exakt zum Vorcheck erhalten; Lesesitzung Exit 0. Verbrauch dieses geschlossenen Scopes: Import 0, Rebindings je 1/1, Save 1/1, Publish 1/1, Exporte 2/2, Create-Versuch 1/3, Edits 0/8, Cleanups 0/3. Übrige Live-Writes 0; alte Restkontingente werden nicht übertragen.

Das vorhandene Test-ChangeContract-Gate vergleicht bei nativer Voraufnahme jetzt auch die Pflichtflags mit dem führenden Schema. **23/24 Abschluss-Gates Exit 0; der native Pflichtfeldvertrag blockiert korrekt mit Exit 1 für Criticality und ChangeType.** Vier synthetische Gegenproben: passender Vertrag Exit 0, Criticality-/ChangeType-/beide Abweichungen jeweils Exit 1 mit passendem Grund. Die tatsächlichen gespeicherten und publizierten Schreibverträge bestehen. 2.948 Power-Fx-Assertions, 66 Formeln und 24 Python-Regressionen bleiben bestanden; keine Tests abgeschwächt. Kanonischer Canvas, Architektur, msapr/msapp, versiegeltes ZIP und Versionen unverändert; kein erneuter Build oder DEV→Git. Pester fehlt; PAC 2.9.3 canvas validate unsupported. Private Belege und der konkrete Folgescope unter `dev-suchabnahme-30452-20261008/`; keine Rohbelege versioniert.


**P3b · Changes-Connectorvertrag aktualisieren und lokalen Reparaturkandidaten vorbereiten**, Modellklasse `deep-reasoning`, neue konkrete Freigabe erforderlich. Nach frischem lesendem Vorcheck auf 30452 / gespeichert und Live 207 die vorhandene Changes-Quelle im svc-Studio genau einmal unterstützt aktualisieren, höchstens einen manuellen Studio-Save und eine echte App-Kopie aufnehmen. Alle kanonischen Formeln/Defaults, bisherigen Quellen/Bindungen, beide echten Suchregeln und sämtliche 52 Schreibfelder erhalten; der erzeugte Changes-Pflichtvertrag muss ausschließlich die bereits führende Architektur abbilden. Nur die geprüfte generierte msapr darf ausdrücklich über DEV→Git übernommen werden, kein zweiter Canvas-SourceTree oder handgeänderter Connectorcache. Anschließend lokalen Kandidaten 30453 bauen und vollständig prüfen, altes versiegeltes 30452-Artefakt erhalten. Keine erneuten Schema-/Content-Type-Writes, Imports, Publishes, Rebindings, weiteren Quellen-/Referenzübernahmen oder Datenzeilen-Writes. Bei Fehler/abweichendem Vertrag Rücklesen und Stopp ohne Write-Retry. Die danach nötige Veröffentlichung beziehungsweise Funktionsabnahme erhält erst am geprüften Kandidaten ihren eigenen konkreten Scope; P4 folgt nach bestandener P3b-Abnahme. Siehe [P3-Vertrag und Freigabegrenzen](Stage-4.1-P3-Change.md).

Die folgenden Versionsberichte sind historische Evidenz; die aktuelle Arbeitsgrenze steht oben und in PROJECT_STATE.md.

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
- Der Datensatzkern (Roadmap P1) ergänzt Liste, Laden und Bearbeiten für Asset/System. DEV 30444/193 Live, beide generierten Suchbindungen und native Formelprüfung belegt; Titeleingabe, beide Creates und unverändertes Wiederöffnen bestanden. Erster System-Edit nicht persistiert, Quelle Version 1.0/unverändert, Folge-Edits gestoppt und beide Testdatensätze reversibel bereinigt. 725 Assertions/Build/Round-Trip/18 Gates gelten für unveränderten Quellkandidaten; System-/Lookup-Round-Trip offen. Die anschließende freigegebene Monitor-Diagnose belegt den Description-Schreibschutzfehler im Edit; Testsystem ID 4 bereinigt, Diagnoseverbrauch je 1/1. Der damals offene Schreibvertrag wurde in P1/30445 repariert und abgenommen; der aktuelle P3-Scope steht oben. Incident/Problem folgen später.

## Abnahmekriterien

- `pwsh ./powerplatform/scripts/Validate-ObjectProviderRegistry.ps1` läuft erfolgreich.
- `pwsh ./powerplatform/scripts/Sync-ObjectProviderRuntime.ps1` erzeugt bzw. aktualisiert die Runtime idempotent.
- `pwsh ./powerplatform/scripts/Sync-ObjectProviderRuntime.ps1 -CheckOnly` läuft danach erfolgreich.
- `colObjectProviderRegistry` ist in `App.pa.yaml` vorhanden.
- `gblActiveProvider` wird bei Objekttypauswahl gesetzt.
- **Neu** ist ohne passende Create-/Save-Capabilities deaktiviert; Save prüft Provider, Modus und ID.
- `Test-CanvasCapabilities.ps1 -PowerFxDirectory <PAC-Library-Verzeichnis>` prüft die tatsächlichen Guard-/Revalidierungsformeln offline mit der Power-Fx-Engine (137 Assertions; ergänzend Choice 212, Record Core 2.032 und Change 567 am lokalen Kandidaten 30450). Die Engine-DLLs stammen aus der lokal installierten PAC-Toolchain; die bestehende CI führt diesen optionalen Engine-Test nicht aus.
- Abschlusskriterium: vollständiger Build und DEV-Speicher-/Quellen-/Bereinigungstest müssen erfolgreich sein. Build und begrenzte P0-Choice-Quellenabnahme von 30440 sind erfolgreich; keine vollständige Asset-/Produktivabnahme.

## Historische P0-Baseline und Title-Reparatur

30431 / Canvas 168 belegte den erforderlichen Studio-Verarbeitungsschritt nach SourceCode-Import; die direkte Importversion führte noch alte interne Regeln aus. Die `.msapr`-Pack-Baseline behält historische Controls/SARIF und ist keine aktuelle Maker-Abnahme. 30432 ergänzte den nativen verpflichtenden Asset-Title und genau zwei Metadatenzeilen. Seine unzulässigen Classic-Button-Properties wurden in 30433 korrigiert; 30434/35 reparierten Galerieereignisse. Details und Versionen stehen historisch in der [P0-Abnahme](Stage-4.1-P0-Abnahme.md); aktueller Stand und einziges Folgepaket folgen unten.

## Historische P0-Host-/Choice-Abnahme 30440

**DEV 30440 / Canvas 184 Live, P0 technisch abgeschlossen (02.10.2026).** Import ohne Publish All Exit 0, Postimport-msapp bytegleich mit Kandidat. Unterstütztes Studio-Items-Rebinding erhält die kanonische Formel; lesender Export bestätigt die generierte V2-Personensuche, feldbezogenen Choice-Default, AllowEmptySelection, zehn native Choice-Adapter und beide Save-Guards. Kein privater YAML-/Pack-Hack und kein Source-Takeover.

Genau ein zusätzlicher ausdrücklich freigegebener Save ID 9 im frischen Player: Title getrimmt, Owner korrekt und Kritikalität stabil angezeigt/Quelle **Hoch**. Busy sperrte Save/Abbruch/Navigation. Ausschließlich ID 9 mit passendem synthetischem Titel reversibel bereinigt; ID-gefilterte Liste leer, Papierkorb/Herkunft Assets belegt, vier Bestandsassets erhalten. Historisch scheiterte ID 8 unter 30439 und wurde bereinigt; alter Player vor aktuellem Test ohne Save verworfen.

Studio-184-Checker vor Veröffentlichung: keine Formel-/Laufzeitbefunde; zwei ungenutzte Quellen, 56 Accessibility-Befunde und zwölf Leistungswarnungen. 347 Offline-Power-Fx-Assertions, Quell-/Compiler-/Personenverträge, Build und verfügbare Projekt-Gates bestehen. Reine Tastatur-Persistenz der Personenauswahl und vollständige Asset-/Rollen-/Reviewabnahme bleiben offen; Neu-Fokus nach Verwerfen nun beobachtet. Details: [P0-Abnahme](Stage-4.1-P0-Abnahme.md).

## Historischer P1-Datensatzkern und DEV-Fehler 30444

Native Asset-/System-Galerien verwenden direkte Titelanfangsfilter oder ID-Gleichheit und ID-Sortierung; die Galerie lädt weitere Datensätze beim Blättern. Keine lokale Gesamtzahl oder vorgeschaltete begrenzte Datensatzcollection. Load speichert den originalen nativen Record und hydriert genau den vorhandenen Patch-Vertrag (Asset 17 / System 16 Felder). Metadatentyp/-vollständigkeit und unbekannte Choices sperren Save; unveränderte Personenobjekte bleiben erhalten. Edit benötigt geladene ID, vollständigen Load, echte Änderung und konfliktfreien Stand. Frische Modified-Prüfung und `ErrorKind.Conflict` geben sichtbare Fehler; der atomare Connector-Konfliktschutz ist in DEV zu prüfen.

Die sieben bisher nicht ausführbaren Registry-Typen melden nun auch List/Create als false; Asset/System behalten alle vier Fähigkeiten. Genau zwei System-Title-Metadaten wurden freigegeben in DEV gespeichert und nach Reload geprüft; keine erneuten Writes. Import 30441 ohne Publish All/`--publish-changes` und bytegleicher Postexport bestehen, Maker zeigt 185 Live; Studio scheitert an PA1001/YamlInvalidSyntax in der Öffnen-Beschriftung. Beide Beschriftungen sind im lokalen Kandidaten 30442 als Blockskalare korrigiert, Formeln unverändert. Echter YAML-Parser vor Pack/in CI und vier Regressionstests ergänzt; CI prüft weiter `Test-CanvasRecordCore.ps1`, lokal 281 Record-Assertions, zusammen 630/53 geparste Formeln. Nach freigegebenem 30442-Import (bytegleicher Postexport, 186 Live) öffnet Studio erfolgreich, speichert 187 automatisch und meldet zwei Formelbefunde im aliasten Formularfilter. `formField.ObjectTypeKey` ist im 30443-Kandidaten explizit qualifiziert. Neuer Engine-Test des tatsächlichen Filters reproduziert beide früheren Hostfehler und besteht nach Korrektur mit sechs zusätzlichen Assertions; CI-Aliasvertrag ergänzt. Keine fachlichen Writes oder gezielte Publikation. Alle 18 verfügbaren Gates und Build bestehen. Diese Tests ersetzen keine Maker-/Connector-Abnahme.

30443 wurde anschließend ausdrücklich freigegeben importiert und zunächst als 189 veröffentlicht. Die zurückgesetzten öffentlichen Personenfelder sind inzwischen kanonisch wiederhergestellt; gespeicherter Draft 190 und publizierter Export 191 enthalten identische Controls-JSONs und die korrekte generierte V2-Suche. Formelchecker ohne Fehler, keine neue Fachformel/Quellübernahme. Beide synthetischen Creates und sauberes Laden bestehen, Asset-Titel-Edit ist quellenbestätigt; System-Titel-Edit einmal versucht, Quelle unverändert bei Version 1.0. Lookup-Suchregel verwendet noch `ComboBoxSample`. Asset-Modified-Konflikt sichtbar blockiert, Quellversion 3.0 erhalten; kein atomarer ETag-Nachweis. Beide Testdatensätze reversibel bereinigt. P1 bleibt offen, fachliche Write-Kontingente verbraucht.

30444 wurde genau einmal ohne Publish All/`--publish-changes` importiert: PAC Timeout / Exit 1, serverseitiger Erfolg und bytegleicher Postexport / Exit 0. Studio-Sperre inzwischen ohne Überschreibung gelöst; beide öffentlichen Suchbindungen je einmal regeneriert. Gespeicherter Draft und publizierter Export enthalten kanonische Load-/Payload-/Default-/Items-Formeln und echte generierte Suchquellen statt `ComboBoxSample`. Native Formelprüfung fehlerfrei, ein manueller Save-Versuch und eine gezielte App-Veröffentlichung, Maker **193 Live**. Im publizierten Export sind sämtliche kompilierten Control-Regeln exakt gleich dem akzeptierten Draft; Paketdateien bei identischen Control-Regeln nicht bytegleich. Keine DEV→Git-Übernahme.

**Vorheriger Fachtest vor Monitor-Diagnose:** Die vorherige Titelblockade wurde im getrennten sichtbaren Player aufgelöst: Zeichenweise Eingabe mit Fokuswechsel übernimmt den Titel korrekt. Titel-/Revalidierungsregeln im publizierten Artefakt entsprechen kanonischen Quellen; keine Formeländerung. Asset ID 11 und System ID 3 angelegt und unverändert wieder geöffnet, Player nach Asset-Create frisch gestartet. System-Lookup bleibt semantisch leer (`0;#` in der Quelle). Erster System-Titel-Edit nach einem UI-Saveversuch nicht persistiert; alter Titel/Version 1.0 und sämtliche sichtbaren Quellfeldbeschreibungen unverändert, Player dirty. Kein Connector-Fehler als Ursache belegt. Vier Folge-Edits gestoppt; System und Asset reversibel gelöscht, Papierkorb/Herkunft und Vorbestand Assets 4–7/Systems leer belegt. Verbrauch Creates 2/2, System-Edit-Versuche 1/5, Deletes 2/2; Save-Retries und übrige fachliche Writes 0. P1 nicht abgenommen. Live-Monitor eingerichtet, native Textänderung/OnChange-LookUp erfolgreich aufgezeichnet; zum Handoff Getrennt, Verbindung vor Saves erneuern. Keine zusätzlichen Saves.

Die konkret freigegebene Monitor-Diagnose auf unverändert 30444/193 ist abgeschlossen: genau ein System-Create, ein Titel-Edit und ein reversibles Cleanup, je 1/1, kein Retry. Neuanlage ID 4/Version 1.0 und unverändertes Wiederöffnen mit Testkonto/Entwurf/Hoch/Aktiv und leerem LinkedAsset bestehen. Native Return-Aktivierung nach bestätigtem Save-Fokus startet beide Speicherereignisse. Create: Monitor `patchCreateRow` und `createRow`/HTTP 201 Created. Edit: `lblEditorSave.OnSelect` meldet bei `Patch` **„[Systems] Spalte Description ist schreibgeschützt und kann nicht geändert werden“**; kein `updateRow` im aufgezeichneten Monitor, Quelle alter Titel/Version 1.0 und alle sichtbaren Felder unverändert. Lokales 30444-msapp und publizierter 193-Export deklarieren `Systems.Description` als `x-ms-permission: read-only`; der kanonische System-Save enthält das Feld auch beim reinen Titel-Edit, Architekturtyp ist Note. Ursprung des Schreibschutzes in nativer Liste/Connector-Metadaten noch offen. Testsystem ID 4 mit Marker/Herkunft Systems im Papierkorb, Alle Elemente/Systems leer, vier Bestandsassets sichtbar; keine Asset-Writes. Fehler erscheint nach Verwerfen auf der Datensatzliste, während der Editor vorher dirty blieb. Monitor zum Handoff Getrennt; 1.605 aufgezeichnete Ereignisse. P1 bleibt offen.

Der damalige Description-Blocker wurde in P1/30445 behoben und begrenzt in DEV abgenommen. Dieser historische Reparaturauftrag ist abgeschlossen; aktueller P3-Kandidat und einziges nächstes Paket stehen oben.
