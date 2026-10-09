# IT Governance Portal

Metadatengetriebene Governance-Plattform auf Basis von SharePoint Online, Power Apps Canvas, Power Automate und PowerShell-Provisioning.

## Aktueller Stand

| Teilprodukt | Version | Status |
|---|---:|---|
| SharePoint-Provisioning und Architekturmodell | `6.2.5` | stabile Git-Baseline |
| Canvas App | `1.0.0-alpha.4.1.0` | P0/P1/P2 abgenommen; DEV 30452 / gespeichert und Live 207; Quelle/Suche/native Pflichtfelder behoben; Connector-Pflichtvertrag veraltet, P3b offen, Produktion P7 |
| Developer Workflow | `Stage 4.1` | lokales Profil 1.2.0; Framework-PR #6 bleibt isoliert |

Die Versionsreihen bleiben getrennt: `VERSION` beschreibt das Provisioning-Paket, `powerplatform/VERSION` die Canvas-Version. `powerplatform/solution/VERSION` spiegelt die Canvas-Version; die vierteilige Solution-Paketversion steht im Solution-Manifest. Die Stage-4.1-Änderungen sind noch nicht nach `main` integriert; `main` enthält Canvas `1.0.0-alpha.4.0.0`.

**P2-DEV-Abnahme abgeschlossen (07.10.2026): Solution 30449 / Canvas 202 Live und gespeichert.** Der separat freigegebene Save am synthetischen Asset 13 leert alle sechs Choices als native null und erhöht die Version von 16.0 auf 17.0; die übrigen 25 deklarierten Felder bleiben erhalten. Sauberes Wiederöffnen zeigt leere Auswahlen, beide Reviewpicker mit leerem DOM-value und placeholder, „Keine Änderungen“ und gesperrtes Save. Asset 13 anschließend genau einmal reversibel bereinigt und nach Marker, Listenherkunft und ID im ersten Papierkorb nachgewiesen. Der vollständige ursprüngliche Bestand ist wiederhergestellt: Assets 4–7 mit sämtlichen nativen Werten/Versionen unverändert, Systems leer. Der erfolgreiche Create und alle fünf Personenwechsel/-Leerungen sowie Review-/Zyklus-/Boolean-Tests unter 30447 bleiben Teil der P2-Evidenz. Gespeicherter und veröffentlichter Host sind in vier Controls-/DataSources-Dateien bytegleich; 84 kanonische/92 kompilierte Controls, beide echten Suchregeln und 19 unveränderte Quellen geprüft. Formel-/Laufzeitchecker ohne Fehler; 72/12/2 Warnungen bleiben. Native ReviewCycleMonths-Min/Max, Produktivrollen und atomarer ETag-Konfliktschutz bleiben für P7 offen; P2 ist keine Produktivfreigabe. [P2-Vertrag und separate Abnahme](docs/development/Stage-4.1-P2-Asset-Verantwortliche.md).

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


**P3b · Changes-Connectorvertrag aktualisieren und lokalen Reparaturkandidaten vorbereiten**, Modellklasse `deep-reasoning`, neue konkrete Freigabe erforderlich. Nach frischem lesendem Vorcheck auf 30452 / gespeichert und Live 207 die vorhandene Changes-Quelle im svc-Studio genau einmal unterstützt aktualisieren, höchstens einen manuellen Studio-Save und eine echte App-Kopie aufnehmen. Alle kanonischen Formeln/Defaults, bisherigen Quellen/Bindungen, beide echten Suchregeln und sämtliche 52 Schreibfelder erhalten; der erzeugte Changes-Pflichtvertrag muss ausschließlich die bereits führende Architektur abbilden. Nur die geprüfte generierte msapr darf ausdrücklich über DEV→Git übernommen werden, kein zweiter Canvas-SourceTree oder handgeänderter Connectorcache. Anschließend lokalen Kandidaten 30453 bauen und vollständig prüfen, altes versiegeltes 30452-Artefakt erhalten. Keine erneuten Schema-/Content-Type-Writes, Imports, Publishes, Rebindings, weiteren Quellen-/Referenzübernahmen oder Datenzeilen-Writes. Bei Fehler/abweichendem Vertrag Rücklesen und Stopp ohne Write-Retry. Die danach nötige Veröffentlichung beziehungsweise Funktionsabnahme erhält erst am geprüften Kandidaten ihren eigenen konkreten Scope; P4 folgt nach bestandener P3b-Abnahme. Siehe [P3-Vertrag und Freigabegrenzen](docs/development/Stage-4.1-P3-Change.md).

## Architektur in Kürze

`architecture/*.yaml` ist die führende Quelle für SharePoint-Schema und Runtime-Metadaten. Das Provisioning kompiliert und validiert dieses Modell. Die Canvas-App nutzt die bereitgestellten Runtime-Listen für Navigation, Formulare, Felder, Choices, Lookups und Berechtigungen.

```text
architecture/*.yaml
        │
        ├── provisioning/            SharePoint-Schema, Seed-Daten, Prüfung
        └── powerplatform/
             ├── canvas/             kanonischer Canvas-SourceCode
             ├── solution/           entpackte unmanaged Solution
             ├── config/             Object-Provider-Registry
             └── scripts/            Validierung, Versionierung und Build
```

## Repository-Struktur

| Pfad | Zweck |
|---|---|
| `architecture/` | kanonisches Architektur- und Metadatenmodell |
| `provisioning/` | idempotentes Provisioning, Reset, Export und Tests |
| `powerplatform/canvas/GovernancePortal/` | einziger gültiger Canvas-SourceTree |
| `powerplatform/solution/` | entpackte Power-Platform-Solution |
| `powerplatform/scripts/` | Build-, Pack- und Validierungsskripte |
| `docs/development/` | aktuelle Entwicklungs- und Testdokumentation |
| `docs/archive/` | historische, nicht mehr normative Dokumente |
| `migration/` | aktive Migrationsregeln; ältere Regeln unter `migration/archive/` |
| `tests/` | Pester- und Architekturtests |
| `tools/companion/` | lokale, eingeschränkte Web-GUI für Git-, Audit- und Testaktionen |
| `artifacts/`, `generated/`, `Logs/` | lokale oder reproduzierbare Ausgaben |

## Voraussetzungen

- Git
- PowerShell 7
- Power Platform CLI (`pac`)
- PnP.PowerShell für Provisioning gegen SharePoint Online
- Python 3 für den lokalen Companion und PyYAML aus `tools/companion/requirements-validation.txt` für die Canvas-YAML-Prüfung
- Berechtigungen für die Zielumgebung und die Governance-Portal-Site

## Lokaler Testablauf

Neue Änderungen werden per Git-Branch bereitgestellt:

```bash
git fetch origin
git switch <branch>
git pull --ff-only
bash ./start-local.sh
```

Der Companion sucht automatisch einen freien Port ab `8770`, öffnet den Browser und stellt Status, Fetch, Pull, Repository-Audit, Connectorprüfung, Canvas-Validierung und Build bereit. Freie Shell-Kommandos sind nicht möglich.

Ohne Companion:

```powershell
pwsh ./provisioning/Scripts/Test-PowerShellSyntax.ps1
pwsh ./provisioning/Scripts/Test-Architecture.ps1
pwsh ./provisioning/Scripts/Test-ArchitectureConsistency.ps1
pwsh ./powerplatform/scripts/Build.ps1
```

Build-Ausgaben entstehen unter `artifacts/` und gehören nicht in Git.

## Verbindliche Dokumente

- [Canvas Stage 3.6](docs/development/Stage-3.6.md)
- [Developer Companion Stage 3.7](docs/development/Stage-3.7-Developer-Companion.md)
- [Runtime Provider Engine Stage 4.1](docs/development/Stage-4.1-Provider-Engine.md)
- [P1-Datensatzkern und konkrete DEV-Abnahme](docs/development/Stage-4.1-P1-Datensatzkern.md)
- [P2 Asset, Verantwortliche und konkrete DEV-Abnahme](docs/development/Stage-4.1-P2-Asset-Verantwortliche.md)
- [PAC-Workflow](docs/development/PAC-Companion-Workflow.md)
- [Roadmap](docs/ROADMAP.md)
- [Aktuelle Projektübergabe](PROJECT_STATE.md)
- [Lokaler Git-/Test-Workflow](docs/development/Local-Companion-Workflow.md)
- [Canvas-SourceCode-Migration](MIGRATION.md)
- [Änderungshistorie](CHANGELOG.md)

## Arbeitsregeln

1. Änderungen erfolgen in Feature- oder Fix-Branches und werden über Pull Requests nach `main` übernommen.
2. Es gibt genau einen Canvas-SourceTree: `powerplatform/canvas/GovernancePortal`.
3. Maker-Portal-Änderungen werden exportiert, entpackt, validiert und gegen Git geprüft.
4. Lokale Tests beginnen mit `git fetch` und `git pull --ff-only`; ZIP-basierte Quellcodeübernahmen entfallen.
5. `start-local.sh` wird über `bash` gestartet; ein lokales `chmod` ist nicht erforderlich.
6. Provisioning bleibt idempotent; produktive Bibliotheksinhalte dürfen nicht unbeabsichtigt gelöscht werden.
7. Historische Pakete, Logs und Zwischenstände werden nicht im aktiven Quellbaum abgelegt.
