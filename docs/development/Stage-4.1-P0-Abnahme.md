# P0 – Stage 4.1: Choice-Reparatur vor erneuter DEV-Abnahme

Stand: 2026-10-01 · Modellklasse: `deep-reasoning` · **P0 bleibt offen**

## Aktueller Kandidat und Live-Ergebnis

Lokaler Kandidat **Solution 1.0.0.30440**, Canvas `1.0.0-alpha.4.1.0`, Provisioning `6.2.5`. Noch nicht in DEV importiert. Letzter belegter DEV-Stand: **Solution 30439 / Canvas 181 Live**. Draft [PR #16](https://github.com/MindBringer/GovernancePlattform/pull/16) basiert auf dem Roadmap-Branch; keine Stage-4.1-Integration oder Produktivfreigabe.

Der ausdrücklich freigegebene **einzelne Asset-Speichertest ist verbraucht**: genau ein Save, Erfolgsmeldung und ID 8. Synthetischer Titel `P0-SMOKE-20261001T203143Z-C439`. Der Quellenvergleich bestätigt den getrimmten Titel und das ausgewählte freigegebene DEV-Testkonto als Owner. Die Kritikalität ist jedoch inkonsistent: „Hoch“ gewählt, Player danach „Niedrig“, Quelle `Criticality:High`. Dieser Datenintegritätsfehler blockiert P0; er wird nicht allein nach P2 verschoben.

Ausschließlich dieser anhand ID und Titel bestätigte Datensatz wurde reversibel in den normalen SharePoint-Papierkorb verschoben. ID-gefilterte aktive Liste leer, exakt dieser Titel im Papierkorb mit Herkunft Assets, danach alle vier vorhandenen Assets weiterhin sichtbar. Kein Purge, Reset, anderer Datensatz-Write oder zweite Neuanlage. Personen-/Tenantdaten und Voll-Logs bleiben außerhalb Git.

## Reparatur 30440

- `drpEditorChoice.Default` löst den qualifizierten `ValueChoiceKey` über die feldbezogenen `colEditorChoiceOptions` zu `DisplayNameDE` auf. `Items.Value` bleibt `DisplayNameDE`. `AllowEmptySelection=true` verhindert einen scheinbar ausgewählten ersten Eintrag bei leerem optionalem Wert; [Microsofts Dropdown-Vertrag](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/control-drop-down).
- Choice-OnChange erfasst Schlüssel, Bezeichnung und Validierung vor dem Galerie-Patch und adressiert den stabilen `EditorFieldKey`. Die Sichtbarkeits-/Edit-Guards bleiben erhalten.
- Zehn vorhandene native Choice-Mappings übersetzen erst an der SharePoint-Patch-Grenze in den durch den Architekturcompiler erzeugten deutschen Wert: sechs Asset-Felder; System GovernanceStatus, Criticality, SystemType und Environment. Qualifizierte Schlüssel bleiben im Editor und im generischen Payload erhalten. Keine neue fachliche Feldzuordnung, kein Schema-/Choice-Metadaten-Write.
- Save-DisplayMode und Revalidierung sperren unabhängig von veraltetem IsValid/Eligibility jeden nicht leeren Choice-Schlüssel ohne feldbezogene Bezeichnung. Leere optionale Werte bleiben leer; Pflichtfeldvalidierung bleibt separat wirksam.
- Personensuche bleibt die begrenzte V2-Suche mit `Self.SearchText`, top 20, isSearchTermRequired=true und DisplayName/UPN. CI verwirft vier ungültige Fixtures, darunter das in Studio tatsächlich unzulässige öffentliche `SearchItems`-Property.

## Personenpicker: erforderlicher Studio-Schritt

SourceCode-PAC-Pack übernimmt auch interne historische Control-Regeln. Nach dem Import wurde trotz korrekter öffentlicher Items-Formel die private Suchregel `Search(ComboBoxSample, Self.SearchText, Value1)` ausgeführt. Ein unterstütztes **Studio-Rebinding von Items** (temporäre leere Tabelle, anschließend exakt die kanonische ForAll/SearchUserV2-Formel wiederherstellen), Speichern und gezielte App-Veröffentlichung erzeugte Canvas 181 mit funktionierender Suche.

Der lesende Export von Canvas 181 bestätigt die generierte Suchregel über den V2-Aufruf und DisplayName; der Player zeigte einen benannten Treffer, direkte Auswahl blieb bestehen, der Owner war in der Datenquelle korrekt. Tastatur-Erreichbarkeit und Suche sind beobachtet; eine ausschließlich per Tastatur persistierte Personenauswahl wird nicht behauptet. Kein DEV→Git-Source-Takeover, keine zweite authorbare Quelle und kein manuell gepflegter privater SearchItems-Hack.

**Nach jedem weiteren SourceCode-Import**: Items im Studio neu binden, kanonische Formel erhalten, Checker prüfen, gezielt veröffentlichen, frischen Player laden und benannten Treffer/Auswahl verifizieren. Lesender Export muss die erzeugte Suchregel belegen. Importerfolg oder Paketbytegleichheit allein genügt nicht.

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
| 30440 lokal | Choice-Anzeige/Adapter/Guards korrigiert, Offline-Gates bestanden. DEV-/Studio-/Quellenabnahme ausstehend; dafür erneute konkrete Freigabe erforderlich. |

Frühere Importaufrufe verwendeten `--publish-changes`; das ist historische Evidenz, keine künftige Standardfreigabe für Publish All. Neue Importe erfolgen ohne diesen Schalter; nur die benannte Canvas-App wird nach Studio-Prüfung gezielt veröffentlicht.

## Checker, Tastatur und verbleibende Grenzen

Checker 171: keine Formel-/Laufzeitbefunde, zwei ungenutzte Quellen (TextResources/StatusPresentation), 56 Accessibility-Fehler (19 Fokus, 25 Tabstopp, zwölf Labels), zwölf Leistungswarnungen (zehn initialisierte Collections, zwei ForAll-Mutationshinweise). Diese Counts sind **historisch**, kein neu berechneter Bericht für 181 oder 30440. Alte AppCheckerResult.sarif-Snapshots im Pack-Artefakt bleiben historische Daten, keine aktuelle Maker-Abnahme.

Buttons haben Text-Namen, Inputs Labels/Fokus/Tabvertrag, Dialog sperrt Hintergrund und gibt bei Weiterbearbeiten Fokus an Abbrechen zurück. Nach endgültigem Verwerfen ist Neu-Fokus nicht belegt (Tab landet bei Start); vor Asset-Pilot in P2 schließen. Keine allgemeine Accessibility-Freigabe. Kontakte öffnen nach Neu keinen Editor; Asset/System-Neu positiv beobachtet. Risk/Control/Measure nicht live einzeln positiv geprüft: Navigation Risiko & Compliance war leer. Keine Vollabnahme aller Provider behauptet.

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
| DEV-Abnahme 30440 | **nicht ausgeführt**, Live bleibt 30439 / 181; Offline-Grün ist keine Live-Abnahme |

Engine-Gates laden lokal Core-/Interpreter-DLLs aus der expliziten PAC-Installation. CI führt Quell-/Compiler-/Syntax-/Architektur-/Artefaktprüfungen aus, die 347 Engine-Assertions lokal. Keine Tests abgeschwächt.

30440 ZIP SHA-256: `6d7a661ccf1e2c5f304cb637e9b297ffcf1eb9a214e7b649de89170187b1c029`.
30440 msapp SHA-256: `a3b8eb928f0153acd7c3454d2576ca2ef3f354905aaff247f26cdb65cd9a2564`.
30439 ZIP SHA-256: `298d25acc205a21257a8307e2fd297a665a44cf87eca18dccf5b7165643b75ce`.
Lesender Studio-181-Export msapp SHA-256: `6614cb1491fc8b1a4bb06287fbb45af9b7b1923a2b43f1322efac2bde5799c6e`.
Builds/Exports/Logs/Screenshots bleiben lokal, nicht in Git.

## Freigaben, Git und genau ein nächstes Paket

Die frühere konkrete Freigabe deckte zwei Title-Metadaten, DEV-Import/Studio-Veröffentlichung und **einen** Asset-Speichertest mit Quellenvergleich/Bereinigung. Diese Writes sind erledigt. Die lokale notwendige Choice-Reparatur ist vorbereitet; ein **zweiter** Save wird daraus nicht abgeleitet. Keine automatische Provisionierung, DEV-Übernahme, Publish All, Deployment, Release oder Merge.

Branch `codex/stage41-p0`, Draft PR #16 auf `codex/first-use-roadmap`; tatsächlicher Commit/CI-Head und Exit-Ergebnisse werden im PR-Handoff am Paketabschluss dokumentiert. Ursprünglicher Workspace `codex/stage-4.1-dev-baseline` mit elf gestagten Dateien bleibt erhalten. PR #14 bleibt Draft, Framework-PR #6 isoliert/DO NOT MERGE; keine Framework-Locks/Runtimeversionen.

**Einziger primärer nächster Schritt: P0-Choice-DEV-Abnahme von 30440**, nach konkreter Freigabe für Import ohne Publish All, Studio-Rebinding/Checker/gezielte App-Veröffentlichung und genau **einen zusätzlichen** synthetischen Asset-Save mit Title, zugelassenem DEV-Testkonto und stabil angezeigter Kritikalität „Hoch“. Vor Save müssen Anzeige und gewählter Schlüssel übereinstimmen; bei Rücksprung abbrechen. Danach genau ID und Titel in der Quelle prüfen: Title getrimmt, Owner korrekt, Criticality **Hoch**. Testdatensatz reversibel entfernen und Abwesenheit/Papierkorb belegen. Bei unklarer Save-Antwort zuerst lesen, kein blindes Wiederholen. P1 beginnt erst nach erfolgreicher P0-Abnahme.
