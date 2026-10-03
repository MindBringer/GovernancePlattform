# P0 – Stage 4.1: technische DEV-Abnahme abgeschlossen

Stand: 2026-10-02 · Modellklasse: `deep-reasoning` · **P0 technisch in DEV abgeschlossen**

## Aktueller Kandidat und Live-Ergebnis

**Solution 1.0.0.30440 / Canvas 184 Live**, Canvas `1.0.0-alpha.4.1.0`, Provisioning `6.2.5`. Import ohne `--publish-changes` Exit 0, Postimport-Export Exit 0 mit bytegleichem msapp. Unterstütztes Studio-Rebinding, Speichern und gezielte Veröffentlichung der benannten App; Maker bestätigt 184 Live. Draft [PR #16](https://github.com/MindBringer/GovernancePlattform/pull/16) basiert auf dem Roadmap-Branch; keine Stage-4.1-Integration oder Produktivfreigabe.

Nach erneuter ausdrücklicher Freigabe erfolgte **genau ein zusätzlicher Asset-Save**, ID **9**, synthetischer Titel `P0-SMOKE-20261002T052051Z-C440`. Leer-/Leerzeichentitel sperrten Save, gültiger Titel aktivierte ihn. Personensuche lieferte den benannten zugelassenen DEV-Testtreffer; direkte Auswahl blieb erhalten. Kritikalität **Hoch** blieb nach Auswahl und Fokuswechsel sichtbar. Genau eine Save-Aktion; „Speichert …“ sperrte Navigation/Save/Abbruch, danach schloss der Editor. Eine flüchtige Erfolgsmeldung wurde nicht gesondert erfasst; der maßgebliche Erfolg ist der Quellenbeleg.

Direkte SharePoint-Prüfung: **Title getrimmt**, **Owner korrekt**, **Criticality Hoch**. DOM-Zeilenidentität und anschließend sichtbarer ID-Filter 9 bestätigen denselben synthetischen Titel. Unausgefüllte optionale Choice-Felder bleiben leer. Ausschließlich dieser ID-/Titel-bestätigte Datensatz wurde reversibel in den normalen Papierkorb verschoben. ID-gefilterte aktive Liste leer, exakter Titel im Papierkorb mit Herkunft Assets; danach alle vier vorhandenen Assets erhalten. Kein Purge, Reset oder weiterer Datensatz-Write. Personen-/Tenantdaten, Voll-Logs und Screenshots bleiben außerhalb Git.

Der vor der Veröffentlichung geöffnete alte Player zeigte weiterhin einen Rücksprung auf Niedrig; **kein Save**, Formular verworfen. Erst ein frisch geöffneter Player zeigte die neuen leeren Choice-Defaults und stabile Auswahl. Alte Sitzungen nach Veröffentlichung nicht als aktuellen Kandidaten abnehmen; App-Player-Version ist kein Nachweis der Canvas-Revision. Historischer ID-8-Test unter 30439: Title/Owner korrekt, Hoch gewählt/UI Niedrig/Quelle `Criticality:High`; bereits reversibel bereinigt. Dieser frühere Fehler bleibt als Reparaturgrund dokumentiert.

## Reparatur 30440

- `drpEditorChoice.Default` löst den qualifizierten `ValueChoiceKey` über die feldbezogenen `colEditorChoiceOptions` zu `DisplayNameDE` auf. `Items.Value` bleibt `DisplayNameDE`. `AllowEmptySelection=true` verhindert einen scheinbar ausgewählten ersten Eintrag bei leerem optionalem Wert; [Microsofts Dropdown-Vertrag](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/control-drop-down).
- Choice-OnChange erfasst Schlüssel, Bezeichnung und Validierung vor dem Galerie-Patch und adressiert den stabilen `EditorFieldKey`. Die Sichtbarkeits-/Edit-Guards bleiben erhalten.
- Zehn vorhandene native Choice-Mappings übersetzen erst an der SharePoint-Patch-Grenze in den durch den Architekturcompiler erzeugten deutschen Wert: sechs Asset-Felder; System GovernanceStatus, Criticality, SystemType und Environment. Qualifizierte Schlüssel bleiben im Editor und im generischen Payload erhalten. Keine neue fachliche Feldzuordnung, kein Schema-/Choice-Metadaten-Write.
- Save-DisplayMode und Revalidierung sperren unabhängig von veraltetem IsValid/Eligibility jeden nicht leeren Choice-Schlüssel ohne feldbezogene Bezeichnung. Leere optionale Werte bleiben leer; Pflichtfeldvalidierung bleibt separat wirksam.
- Personensuche bleibt die begrenzte V2-Suche mit `Self.SearchText`, top 20, isSearchTermRequired=true und DisplayName/UPN. CI verwirft vier ungültige Fixtures, darunter das in Studio tatsächlich unzulässige öffentliche `SearchItems`-Property.

## Personenpicker: erforderlicher Studio-Schritt

SourceCode-PAC-Pack übernimmt auch interne historische Control-Regeln. Nach dem Import wurde trotz korrekter öffentlicher Items-Formel die private Suchregel `Search(ComboBoxSample, Self.SearchText, Value1)` ausgeführt. Ein unterstütztes **Studio-Rebinding von Items** (temporäre leere Tabelle, anschließend exakt die kanonische ForAll/SearchUserV2-Formel wiederherstellen), Speichern und gezielte App-Veröffentlichung erzeugte historisch Canvas 181 mit funktionierender Suche; für 30440 wiederholt und als Canvas 184 gezielt veröffentlicht.

Der lesende Export von Canvas 184 bestätigt die generierte Suchregel über den V2-Aufruf und DisplayName; der Player zeigte einen benannten Treffer, direkte Auswahl blieb bestehen, der Owner war in der Datenquelle korrekt. Tastatur-Erreichbarkeit und Suche sind beobachtet; eine ausschließlich per Tastatur persistierte Personenauswahl wird nicht behauptet. Kein DEV→Git-Source-Takeover, keine zweite authorbare Quelle und kein manuell gepflegter privater SearchItems-Hack.

**Nach jedem weiteren SourceCode-Import**: Items im Studio neu binden, kanonische Formel erhalten, Checker prüfen, gezielt veröffentlichen, frischen Player laden und benannten Treffer/Auswahl verifizieren. Lesender Export muss die erzeugte Suchregel belegen. Importerfolg oder Paketbytegleichheit allein genügt nicht.

**Ergänzung aus P1/30443:** Eine leere `Table()` setzte im aktuellen Studio auch `DisplayFields`, `SearchFields` und `IsSearchable` zurück, obwohl die kanonische Items-Formel danach wieder vorhanden und der Checker ohne Formelfehler war. Deshalb vor künftiger gezielter Publikation alle drei öffentlichen Eigenschaften gegen den bestehenden Source-Vertrag prüfen/wiederherstellen (`["DisplayName"]`, `["DisplayName"]`, true) und die generierte V2-Suchregel lesend belegen. Ein bloßes Items-Rebinding ist kein Erfolgsnachweis. Die historische P0-Abnahme bleibt unverändert; erfolgreiche P1-Personenwiederherstellung unter 191 und die offenen System-/Lookup-Befunde stehen im [P1-Abnahmeplan](Stage-4.1-P1-Datensatzkern.md).

## Belegte Reparaturhistorie

| Stand | Beobachtung und Grenze |
|---|---|
| 30431 / Canvas 168 Live | Provider-/Busy-Guards und entfernte nicht delegierbare Asset-Gesamtzahl geprüft. Save vor Write gestoppt: Title-Metadaten fehlten. |
| 30432 | Genau zwei Title-Metadaten nach Freigabe angelegt; kein Voll-Publish/Provisioning/Seed/Reset. Studio PA2108 für acht unzulässige Classic-Button-AccessibleLabel-Properties. |
| 30433 / Canvas 171 Live | Button-Text-Namen statt unzulässigem Property. Navigation/Neu/Abbruch/Dialog per Tastatur; Titel leer sperrt, nicht leer blieb fälschlich ungültig. Kein Save. |
| 30434 / Canvas 172 | Text-Update-Record vor Patch erfasst, stabiler EditorFieldKey. Import Exit 0; keine eigenständige Studio-Abnahme dieses Zwischenstands. |
| 30435 / Canvas 174 Live | Neun Ereignisse von acht Inputs gegen unsichtbar/nicht bearbeitbar geschützt. Nicht leerer Titel aktiviert Save, Pflichtfehler wird gelöscht. Personenpicker weiter ohne benannten Treffer. |
| 30436 / Canvas 176 Live | Diagnostische Änderung einer privaten gepackten Suchregel hielt Studio-Regenerierung nicht stand. Nicht als Source-Lösung übernommen. |
| 30437 / Canvas 178 Saved | Direkter V2-Items-Diagnoseversuch ohne ForAll erfolglos; Studio-Version nicht veröffentlicht, kanonische Formel wiederhergestellt. |
| 30438 / Canvas 179 | Öffentliche YAML-Eigenschaft SearchItems erzeugte Studio PA2108. PAC-Client nach anhaltendem Import-Warten beendet (Signal TERM, Wrapper Exit 241); **kein erfolgreicher CLI-Exit** behauptet. Unzulässige Eigenschaft entfernt und negative Fixture ergänzt. |
| 30439 / Canvas 181 Live | Import **ohne `--publish-changes`** Exit 0; Studio-Rebinding, Speichern und gezielte Veröffentlichung erfolgreich. Genau ein Save ID 8; Title/Owner korrekt, Choice-Round-Trip fehlgeschlagen, Bereinigung belegt. |
| 30440 / Canvas 184 Live | Import ohne Publish All Exit 0, Studio-Rebinding/Checker/gezielte Veröffentlichung, lesender Export. Genau ein zusätzlich freigegebener Save ID 9 im frischen Player: Title/Owner/Hoch korrekt; reversible Bereinigung/Bestandsassets verifiziert. P0 technisch abgeschlossen. |

Frühere Importaufrufe verwendeten `--publish-changes`; das ist historische Evidenz, keine künftige Standardfreigabe für Publish All. Neue Importe erfolgen ohne diesen Schalter; nur die benannte Canvas-App wird nach Studio-Prüfung gezielt veröffentlicht.

## Checker, Tastatur und verbleibende Grenzen

**Aktueller Studio-184-Checker vor Veröffentlichung:** keine Formel-/Laufzeitbefunde, zwei ungenutzte Quellen (TextResources/StatusPresentation), 56 Accessibility-Befunde (19 Fokus, 25 Tabstopp, zwölf Labels), zwölf Leistungswarnungen (zehn initialisierte Collections, zwei ForAll-Mutationshinweise). Die gleichen historischen Counts von 171 sind damit für 184 neu im Maker geprüft. Kein erneuter Checker nach dem Player-Save behauptet. Alte AppCheckerResult.sarif-Snapshots im Pack-Artefakt sind keine aktuelle Maker-Abnahme.

Buttons haben Text-Namen, Inputs Labels/Fokus/Tabvertrag, Dialog sperrt Hintergrund und gibt bei Weiterbearbeiten Fokus an Abbrechen zurück. Nach endgültigem Verwerfen wurde **Neu-Fokus** im aktuellen Host positiv beobachtet; frühere ungeklärte Beobachtung damit geschlossen. Reine Tastatur-Persistenz der Personenauswahl nicht belegt. Keine allgemeine Accessibility-Freigabe; verbleibende Befunde vor Asset-Pilot im betroffenen Ablauf schließen oder begründet bewerten. Kontakte öffnen nach Neu keinen Editor; Asset/System-Neu positiv beobachtet. Risk/Control/Measure nicht live einzeln positiv geprüft: Navigation Risiko & Compliance war leer. Keine Vollabnahme aller Provider behauptet.

P1 implementiert erst Datensatzliste/Laden/Bearbeiten. P2 prüft den vollständigen Asset-Round-Trip einschließlich GovernanceStatus, weiterer Verantwortlicher und Reviewtermin; nicht ausgefüllte/nicht gemappte Felder wurden in P0 nicht als gespeichert ausgegeben. Insbesondere Asset-GovernanceStatus bleibt im vorhandenen Patch ungemappt; ein sichtbarer Standard ist kein Quellenbeleg. Der Speichertest belegt keinen Reviewablauf.

## Gates des lokalen Kandidaten 30440

| Gate | Ergebnis / Exit-Code |
|---|---|
| Tatsächliche Power-Fx-Capabilities/Ereignisse | 135 Assertions / 0; Provider, Title-Grenzen, Busy, Stale Eligibility, Text-Record und alle Eingabeereignis-Guards |
| Tatsächliche Power-Fx-Choice-Formeln | 212 Assertions / 0; zehn native Adapter, alle 42 deklarierten Werte, feldbezogene Defaults/Patches, leere/unbekannte/fremde Schlüssel, erfasster OnChange-Record |
| Choice-Quell-/Compilervertrag | zehn Adapter / 42 Werte / 0; auch CI ohne PAC-DLLs |
| Asset-Title-Schema/Metadatengenerator | zwei zusätzliche Zeilen, 1.012 bestehende unverändert / 0 |
| Accessibility-Quellvertrag | 16 Controls / drei Galerien / 0; kein Ersatz für Host-Abnahme |
| Personen-Quellvertrag | aktueller Quellcode akzeptiert, vier ungültige Fixtures verworfen / 0; private generierte Bindung bleibt Studio-Gate |
| Vollständiger Build | Registry, Runtime-Sync, Source/Version, Referenzen, PAC Canvas-Pack und Solution-Pack / 0 |
| PAC SourceCode-Unpack/Vergleich | vier YAMLs identisch nach BOM/Newline-Normalisierung / 0 |
| PowerShell-Syntax | 33 Dateien / 0 |
| Architektur/Konsistenz | 16 Objekttypen, 50 Listen / 0 |
| Artefaktvergleich / Repository-Audit / Diff | bestanden / 0 |
| Pester | nicht ausgeführt: Modul fehlt |
| `pac canvas validate` | PAC 2.9.3 bietet diesen Befehl nicht; Maker-Prüfung erforderlich |
| DEV-Abnahme 30440 | Import/Export Exit 0, Studio 184 Live und begrenzter Asset-Save-/Quellen-/Bereinigungstest bestanden; keine vollständige Asset-/Produktivabnahme |

Engine-Gates laden lokal Core-/Interpreter-DLLs aus der expliziten PAC-Installation. CI führt Quell-/Compiler-/Syntax-/Architektur-/Artefaktprüfungen aus, die 347 Engine-Assertions lokal. Keine Tests abgeschwächt.

30440 ZIP SHA-256: `6d7a661ccf1e2c5f304cb637e9b297ffcf1eb9a214e7b649de89170187b1c029`.
30440 msapp SHA-256: `a3b8eb928f0153acd7c3454d2576ca2ef3f354905aaff247f26cdb65cd9a2564`.
30439 ZIP SHA-256: `298d25acc205a21257a8307e2fd297a665a44cf87eca18dccf5b7165643b75ce`.
Lesender Studio-181-Export msapp SHA-256: `6614cb1491fc8b1a4bb06287fbb45af9b7b1923a2b43f1322efac2bde5799c6e`.
Lesender Studio-184-Export msapp SHA-256: `d5d6bf9ee663dc03801c38da45021996d92b1440ae74c24d7e30a27c70bfb501`. Generierte Suchregel, Choice-Default/AllowEmptySelection, zehn native Adapter und beide Save-Guards read-only bestätigt. Studio-Regenerierung erklärt die Abweichung zum SourceCode-Pack; keine DEV-Quellenübernahme.
Builds/Exports/Logs/Screenshots bleiben lokal, nicht in Git.

## Freigaben, Git und genau ein nächstes Paket

Die frühere konkrete Freigabe deckte zwei Title-Metadaten, DEV-Import/Studio-Veröffentlichung und einen Asset-Speichertest (ID 8). Die erneute Freigabe deckte **30440 Import ohne Publish All, Studio-Rebinding/Checker/gezielte Veröffentlichung und genau einen zusätzlichen synthetischen Save mit Quellenvergleich/reversibler Bereinigung (ID 9)**. Beide Save-Freigaben sind verbraucht. Keine automatische Provisionierung, DEV-Übernahme, Publish All, Deployment, Release oder Merge.

Branch `codex/stage41-p0`, Draft PR #16 auf `codex/first-use-roadmap`. Code-/Doku-Head `2f229d4334501ed7ab595145989d5df49c3fa7a5` mit drei erfolgreichen CI-Checks geprüft; abschließender Dokumentations-Head/CI im PR-Handoff. Ursprünglicher Workspace `codex/stage-4.1-dev-baseline` mit elf gestagten Dateien bleibt erhalten. PR #14 bleibt Draft, Framework-PR #6 isoliert/DO NOT MERGE; keine Framework-Locks/Runtimeversionen.

**Aktueller primärer nächster Schritt: P1 · verbleibende DEV-Abnahme von 30444 unter bestehender Freigabe**, Modellklasse `deep-reasoning`; [aktueller Stand und begrenzter Restumfang](Stage-4.1-P1-Datensatzkern.md). DEV 30444/192 Live, automatisch gespeicherter Draft 193; Studio-Bedienung/Sitzung blockiert, keine gezielte Veröffentlichung oder fachlichen Testwrites. Import ist verbraucht und wird nicht wiederholt. Personenbindung und Asset-Konflikt unter 30443/191 bleiben historische Belege, System-Edit/Lookup offen. P2 nach P1-Abnahme; P0-Abschluss bedeutet keine Stage-4.1-Integration oder Produktivfreigabe.
