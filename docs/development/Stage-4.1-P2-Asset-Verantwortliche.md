# P2 – Asset, Verantwortliche und Reviewtermine

Stand: 2026-10-07 · `codex/stage41-p2` · Basis P1 `a894b386632ed1128a2ff69a4620896d08f77bcd` · Modellklasse `standard-reasoning`.

**P2-DEV-Abnahme abgeschlossen (07.10.2026): Solution 30449 / Canvas 202 Live und gespeichert.** Der separat freigegebene Save am synthetischen Asset 13 leert alle sechs Choices als native null und erhöht die Version von 16.0 auf 17.0; die übrigen 25 deklarierten Felder bleiben erhalten. Sauberes Wiederöffnen zeigt leere Auswahlen, beide Reviewpicker mit leerem DOM-value und placeholder, „Keine Änderungen“ und gesperrtes Save. Asset 13 anschließend genau einmal reversibel bereinigt und nach Marker, Listenherkunft und ID im ersten Papierkorb nachgewiesen. Der vollständige ursprüngliche Bestand ist wiederhergestellt: Assets 4–7 mit sämtlichen nativen Werten/Versionen unverändert, Systems leer. Der erfolgreiche Create und alle fünf Personenwechsel/-Leerungen sowie Review-/Zyklus-/Boolean-Tests unter 30447 bleiben Teil der P2-Evidenz. Gespeicherter und veröffentlichter Host sind in vier Controls-/DataSources-Dateien bytegleich; 84 kanonische/92 kompilierte Controls, beide echten Suchregeln und 19 unveränderte Quellen geprüft. Formel-/Laufzeitchecker ohne Fehler; 72/12/2 Warnungen bleiben. Native ReviewCycleMonths-Min/Max, Produktivrollen und atomarer ETag-Konfliktschutz bleiben für P7 offen; P2 ist keine Produktivfreigabe. P2 bereitet den Asset-Pilot mit dem vorhandenen 17-Felder-Vertrag vor. Es erweitert weder Schema noch Save-Mapping oder Provider-Capabilities. Die P1-Abnahme ist abgeschlossen und wird nicht wiederholt.

## Architektur und Pilotumfang

Führend sind `architecture/platform.yaml`, `fields.yaml`, `object-fields.yaml`, `forms.yaml` und `choices.yaml`. Asset hat 31 deklarierte Felder; davon sind genau 17 in Load, Formular und Save enthalten. Der tatsächliche aliastierte Formularfilter und die NativeControlType-Zuordnung werden gegen den Compiler geprüft.

| Pilotfunktion | Felder | Vertrag |
|---|---|---|
| Identifikation | Title, AssetType | Title verpflichtend/getrimmt; AssetType optionales Textfeld |
| Verantwortliche | Owner, DeputyOwner, BusinessOwner, TechnicalOwner, DataSteward | Einzelperson; Claims-Principal aus UPN. Unveränderte native Objekte mit Email-Alias, Department und JobTitle bleiben erhalten; Wechsel verwendet ausgewählte UPN, Leeren schreibt Blank |
| Einstufung und Status | Criticality, DataClassification, LifecycleStatus | Nur aktive Architektur-Choices, feldbezogene Schlüssel. Status im Pilot ist LifecycleStatus; DataClassification behält bewusst den bestehenden Criticality-ChoiceSet-Vertrag |
| Schutzbedarf | ConfidentialityRequirement, IntegrityRequirement, AvailabilityRequirement | Bestehender Criticality-ChoiceSet; optionale Auswahl kann geleert werden |
| Reviewplanung | LastReviewDate, NextReviewDate, ReviewCycleMonths | Kalenderdatum im Picker; unveränderte native DateTime-Werte behalten Uhrzeit. Geändertes Datum wird DateTime zu 00:00 App-Lokalzeit, explizites Leeren typisiert Blank. Zyklus optional; Architekturgrenzen 1–120 Monate, native Spalte am 06.10.2026 ohne Min-/Max-Attribute; Durchsetzung vor Produktivfreigabe separat klären |
| Aktivität | IsActive | Boolean; false bleibt erhalten |

Bewusst außerhalb des Pilotformulars bleiben **14 Felder**: GovernanceID, GovernanceStatus, Description, ComplianceScope, Tags, SourceChannel, CorrelationID, ValidationStatus, LastValidationAt, SearchKeywords, BusinessCritical, RecoveryPriority, RTOHours und RPOHours. Dazu gehören Metadaten/Automationswerte, das native Description-Feld, Mehrfachauswahl und zusätzliche Wiederanlaufplanung. Sie werden nicht in den Patch aufgenommen. Für diesen Pilot gibt es keine automatischen Governance-ID-/Statusregeln, Reviews, Historieneinträge oder Evidence-Bezüge. Das wird erst in den späteren Paketen eingebunden.

## Umsetzung und belegte Lücken

30447 behebt den in 30446/198 nativ reproduzierten Browserfehler: die Null-Grenze für nicht-Title-Textfelder wird durch 255 ersetzt, entsprechend dem nativen SharePoint-Textvertrag. Note-/Multiline-Control unverändert. Eine Regression wertet die tatsächliche MaxLength-Formel für alle sieben gemappten Textfelder in Asset/System aus: normale Tastatureingabe passt, native Grenze wird eingehalten, beide Title-Felder behalten volle 255 Zeichen. 16 zusätzliche Assertions, vor Fix Exit 1 bei AssetType, danach Exit 0. Die tatsächliche AssetType-Tastatureingabe und Create sind nun unter 30447/200 Live belegt; der noch offene Choice-Leerwertfehler ist davon getrennt.

Die fünf Personenfelder und alle 17 Save-/Load-Felder waren bereits implementiert. Die vorhandenen Identitäts- und Choice-Verträge werden erhalten und mit tatsächlichen Formeln geprüft. Neu ist **„Datum leeren“** neben optionalen Datumfeldern: verborgen bei Pflichtfeldern, gesperrt bei leerem Wert, ReadOnly, Load, Save oder Verwerfen-Dialog. Der Handler setzt typisiertes Blank, markiert ausschließlich die betroffene Editorzeile, setzt den Picker zurück und revalidiert.

Die neue Datumsprüfung reproduzierte einen echten Power-Fx-Typfehler: `Patch` in einen DateTime-Editorwert mit `Self.SelectedDate` vom Typ Date wurde abgelehnt. Die Aktualisierung verwendet jetzt `Self.SelectedDate + Time(0, 0, 0)` und einen typisierten leeren DateTime-Wert. Die Initialisierung nutzt ebenfalls DateTimeValue und typisiertes DateTime-Blank; ihre zusätzliche Regression reproduzierte denselben Typfehler und prüft erhaltene Stunden/Minuten/Sekunden eines Metadaten-Defaults. Unveränderte Daten werden weiter direkt hydriert. Der gemeinsame Control gilt auch für System; dessen 16 Save-Felder und bisherige Verträge bleiben unverändert. Keine native Uhrzeit wird allein beim Öffnen oder durch eine andere Feldänderung überschrieben.

## Historischer Reparaturkandidat 30447 und lokale Nachweise

Canvas `1.0.0-alpha.4.1.0`, Provisioning `6.2.5` unverändert; nur die vierteilige Solution-Buildnummer erhöht.

| Artefakt | SHA-256 |
|---|---|
| GovernancePortal_1.0.0.30447_1.0.0-alpha.4.1.0.zip | `58a1b20bff247d5efcfd60c1c65eb35fcdcbc8bc517539dfa27c882e64e30fd2` |
| gp_governanceportal_c93a1_DocumentUri.msapp | `35f273a9d563189f8e71812caf6a587e7ffe833a3c68eef831ce2d5991365362` |
| Kanonisches erzeugtes msapr (unverändert) | addc5517a8f8abd5ba74b3b7510b827132eb20b0bdd9c54e2c1fc3f5323a802f |

**Build, Canvas-/Solution-Pack und SourceCode-Unpack Exit 0**, vier Src-YAMLs bytegleich im Round-Trip. ZIP enthält bytegleich das geprüfte msapp. **20/20 verfügbare Projekt-Gates Exit 0**: Architektur/Konsistenz, PowerShell-Syntax, Asset-/System-Title, SystemDescription, YAML/Canvas, Accessibility (21 Controls), Registry/Runtime, Referenzen, Personen, Artefakt, Choice/Capability/Record Power Fx, Audit und Diff. Alle **33 tatsächlichen Patch-Spalten** im kanonischen und gepackten Connector read-write.

**2.365 tatsächliche Power-Fx-Assertions**: 2.016 Record + 212 Choice + 137 Capability, 57 Verhaltensformeln geparst; 13 Python-Regressionen. P2 prüft alle fünf Personenfelder in New/Edit mit Wechsel und Leeren, normalisierte Claims, Erhalt der übrigen Personeneigenschaften/Felder und sauberes lokales Wiederöffnen. Beide Reviewtermine und sechs Choices sind einzeln gesetzt/geleert; andere Werte und genau eine Dirty-Zeile bleiben nachgewiesen. Optionales Number-Blank/0 und Boolean-false bleiben erhalten. Das Harness wertet tatsächliche Guards, Update-Records, Load-, Hydrierungs- und Payloadformeln aus; Gallery-Mutation, Reset/OnChange-Verhalten, Directory-/SharePoint-Connector und Hostkompilierung erfordern DEV.

Toolchain: PAC 2.9.3, PowerShell 7.6.3, Python 3.14/PyYAML 6.0.2. Erster Build Exit 1 durch den Homebrew-Python ohne PyYAML; mit bereits vorhandener validierter Python-Umgebung und ohne erneuten Versionsschritt vollständig Exit 0. Pester nicht installiert, `pac canvas validate` in PAC 2.9.3 nicht unterstützt; keine grünen Gates daraus ableiten. Die vorhandene CI prüft Quelle/Compiler/Artefakt; die optionalen Engine-Tests laufen lokal.

Private Logs, Gate-Befehle/Exit-Codes, Kandidatenhashes und Round-Trip unter `artifacts/p2-local-30447/`; keine Logs, Tenantsettings, Personen oder ZIP-Ausgaben versioniert. Die historischen Controls/SARIF im msapr/Pack sind keine Maker-Abnahme von P2. Das bestehende versionierte msapp ist das geprüfte Solution-Artefakt.

## Begrenzte DEV-Abnahme 30447 – beendet am Choice-Blocker

Der freigegebene 30446-Scope endet an einem belegten Eingabefehler vor Create. Verbrauch: Import **1/1**, manueller Studio-Save **1/1**, öffentliche Personen-/Lookup-Rebindings **je 1/1**, gezieltes Publish **1/1**; Asset-Create **0/1**, Edits **0/14**, Cleanup **0/1**. Canvas 198 Live bestätigt; publizierter Host und alle 19 Quellen bytegleich zum geprüften Draft. Der Formularentwurf wurde ohne Save verworfen, native Vollsnapshots bestätigen den unveränderten Bestand. Es gibt keine neue Test-ID oder Cleanup-Aktion. Private Freigabe-/Export-/Browser-/Quellbelege unter `artifacts/p2-20261006/dev-abnahme-30446-20261006/`.

**Die separate menschliche Freigabe für 30447 wurde am 06.10.2026 erteilt und kandidatbezogen erfasst.** [AGENTS.md](../../AGENTS.md) verlangt: „Commit/Push nur im beauftragten Umfang; Merge/Release/Live-Writes separat.“ Der untenstehende ursprüngliche Umfang war ausdrücklich autorisiert und ist nun am Stop-Kriterium beendet; die vorherige 30446-Freigabe bleibt separat verbraucht. Private unveränderliche `artifacts/p2-20261006/dev-abnahme-30447-20261006/APPROVED-SCOPE.json` und fortgeschriebenes `status.json` belegen Grenzen und Verbrauch. Die am 07.10.2026 separat genehmigte Zykluskorrektur erweitert ausschließlich die Edit-Grenze von 14 auf 15; unveränderliche `APPROVED-AMENDMENT-CYCLE-20261007.json` hält diese Freigabe getrennt fest.

**30447-Verbrauch:** Import **1/1**, manueller Studio-Save-Versuch **1/1**, öffentliche Personen-/Lookup-Rebindings **je 1/1 abgeschlossen**, gezieltes Publish **1/1**, Create **1/1**, Asset-Edit-Versuche **15/15** einschließlich separat genehmigter Zykluskorrektur; reversibles Cleanup **0/1** wegen Stop-Regel. Alle anderen Writes **0**. Canvas **200 Live**, gespeicherter und veröffentlichter Host exportgleich. Die Quelle nach Edit 14 ist Asset **13/v16.0** mit weiterhin sechs nichtleeren Choices; dies ist keine erfolgreiche P2-Abnahme. Der native Abschlusslesetest bestätigt unveränderte Assets 4–7 und Systems leer; Lesesitzung Exit 0. Keine weiteren Writes aus dem alten Scope.

| Aktion | Höchstzahl / Grenze |
|---|---|
| DEV-Import | **1** unmanaged Import ausschließlich des historischen 30447-ZIP; ohne Publish All/`--publish-changes`; Timeout durch serverseitigen Verlauf/Postexport klären, kein blinder Retry |
| Unterstützte Studio-Verarbeitung | **1** manueller Draft-Save-Versuch; falls erforderlich je **1** öffentliches Personen-/Lookup-Rebinding bei unveränderten Fachformeln; echte generierte Suchregeln exportprüfen, keine private SearchItems-Regel authorieren |
| Veröffentlichung | **1** gezieltes App-Publish nach Checker und Vergleich des gespeicherten Hostkandidaten; keine andere App/Umgebung |
| Fachlicher Create | **1** synthetisches Asset, Marker `GP-P2-30447-20261006-ASSET`; keine Bestandsdatensätze |
| Fachliche Asset-Edits | **14 + 1** separat genehmigte Zykluskorrektur = **15** verbrauchte App-Save-Versuche |
| Reversibles Cleanup | **1** ausschließlich diese neue Asset-ID nach Titel/Listenherkunft; Papierkorb und unveränderten Vorbestand prüfen |
| Andere Writes | **0** Schema, Runtime-Metadaten, Rollen, Bestandsdaten, Systems, Seeds, Reset, Papierkorbleerung, Publish All und DEV→Git |

Die folgende ursprüngliche Schrittfolge ist historisch ausgeführt; sie autorisiert keine weiteren Saves. Vor den damaligen Writes wurden aktueller App-/Solution-/Quellenstand, beide vollständigen Suchregenerationen und publizierter Host geprüft. Der frische Player bestätigte echte AssetType-Tastatureingabe und DOM-MaxLength 255 vor Create. Ein natives Baseline-Snapshot aller Asset-Felder und Versionswerte, Systems-Bestand sowie Checker-/Suchbindungsnachweise lokal sichern. Die zwei bestehenden, für diesen Abnahmescope zulässigen Testidentitäten A/B werden privat per UPN verifiziert; keine Konten anlegen oder Rollen ändern. Fehlt eine zweite zulässige Identität, bleibt der Personenwechsel offen und wird nicht durch dieselbe Person ersetzt.

1. Asset anlegen: Titelmarker, AssetType, alle fünf Personenfelder mit A, gültige sechs Choice-Werte, beide Reviewtermine, Zyklus 6 und IsActive true. Quelle mit positiver ID prüfen und sauber wiederöffnen.
2. **Edits 1–5:** Owner, DeputyOwner, BusinessOwner, TechnicalOwner und DataSteward einzeln von A auf B wechseln. Native Claims/Person und alle übrigen Felder bleiben jeweils nachvollziehbar.
3. **Edits 6–10:** dieselben fünf Personenfelder einzeln leeren. Native Person null/leer und die übrigen Felder jeweils prüfen; erneutes Öffnen bleibt clean.
4. **Edit 11:** die sechs Choices auf andere gültige Architekturwerte, beide Reviewtermine auf andere Kalendertage und Zyklus 12 setzen. Datum/Uhrzeit nach App-Zeitzone prüfen; übrige Werte erhalten.
5. **Edit 12:** beide Reviewtermine über „Datum leeren“ entfernen. Native Daten bleiben leer, Picker bleibt nach Reset und Wiederöffnen leer; kein Rückfall auf Today/Platzhalter.
6. **Edit 13:** optionalen Zyklus leeren und IsActive false setzen; native null und false unterscheiden.
7. **Edit 14:** die sechs optionalen Choices leeren; nativen leeren Choice-Wert und alle übrigen Daten prüfen.
8. Genau diese Test-ID reversibel bereinigen und vorbestehende Assets/Systems inklusive unveränderter nativer Feldwerte und Versionen belegen.

Jeder Save verlangt vorher die erwartete ID/Version und nachher native Werte/Version sowie „Keine Änderungen“ und gesperrtes Save beim Wiederöffnen. Bei Fehler, unklarem Ausgang, Formelbefund oder abweichendem Versionsstand stoppen und lesend klären; keine Save-/Delete-/Publish-Retries. Keine künstlichen Berechtigungs-/Schemafehler erzeugen. Bestehende P1-Konfliktprüfung nicht wiederholen; atomarer ETag-Schutz, große Datenmengen, Screenreader und reale Produktivrollen sind nicht dadurch abgenommen.

Nach bestandener P2-DEV-Abnahme folgt P3 Change. Erst die getrennte Rollen-/Betriebsfreigabe erlaubt einen produktiven Asset-Pilot; P2 allein ist keine Produktivfreigabe.

## Historischer 30447-Abnahmestand vor der 30449-Freigabe

**Historische P2-DEV-Teilabnahme (07.10.2026): Solution 30447 / Canvas 200 Live und gespeichert.** Beide öffentlichen Suchbindungen sind vollständig regeneriert; gespeicherter und publizierter Host stimmen in Controls und allen 19 Quellen überein (84 kanonische/92 kompilierte Controls, keine abweichende Fachregel). Formel-/Laufzeitchecker ohne Fehler, 72/12/2 Warnungen bleiben. AssetType-Tastatureingabe mit MaxLength 255, ein synthetischer Create (Asset ID 13) und Personenwechsel/-Leeren in allen fünf Feldern bestehen. Edit 11 speichert Choices und Termine, aber zunächst Zyklus 6 statt 12; der separat genehmigte zusätzliche Save mit echter Tastatureingabe korrigiert ausschließlich den Zyklus auf 12. Edits 12/13 belegen beide Termine und Zyklus als native null sowie IsActive false, jeweils sauber wiedergeöffnet. **Edit 14 scheitert:** alle sechs Choices vor Save in der App leer, Quelle bei Version 16.0 weiterhin mit alten Choice-Werten; 25 übrige deklarierte Felder unverändert. Alle 15 genehmigten Edit-Versuche sind verbraucht. Stop-Regel ausgelöst, Cleanup 0/1; Asset 13 bleibt erhalten. Abschließende Vollsnapshots bestätigen Assets 4–7/v1.0 mit allen Ausgangswerten unverändert und Systems leer. Der abschließende Sichtcheck zeigt bei nativ leerem Datum und DOM-value leer noch den Standardplatzhalter „31.12.2001“. **Kandidat 30449 korrigiert Choice-Blank und entfernt diesen Datumsplatzhalter lokal; seine DEV-Abnahme braucht einen neuen begrenzten Scope.** P2 bleibt fachlich offen; native ReviewCycleMonths-Min/Max-Grenzen fehlen weiterhin.

Dieser Stand wurde durch die nachfolgend dokumentierte 30449-Abnahme abgeschlossen; die damaligen Fehlversuche und Stop-Regeln bleiben erhalten.

## Reparaturkandidat 30449 – Choice-Leeren und leere Datumsanzeige

Beim nativen Edit 14 waren alle sechs Auswahlen vor Save leer. SharePoint erhöht die Version auf 16.0, behält aber die vorherigen Choice-Werte. Die damaligen Offline-Tests prüften nur `IsBlank(testSaved.Choice.Value)`: auch ein nichtleerer Datensatz mit leerem Value besteht diese Prüfung. Der neue Test für das ganze Choice-Feld reproduziert den Fehler mit Exit 1. 30449 übergibt bei leerem ValueChoiceKey nun `Blank()` für das ganze Feld, andernfalls weiterhin den feldbezogenen Datensatz mit Architektur-Anzeigewert. Das betrifft alle zehn gleichartigen Asset-/System-Adapter; Pflichtfeld-/Unmapped-Sperren, Personen-, Datums-, Lookup- und Capability-Verträge bleiben bestehen. Die neue Connector-Abnahme bestätigt die Reparatur für alle sechs Asset-Choices; die vier System-Adapter sind durch die tatsächlichen Offline-Round-Trips geprüft, in 30449 gab es keine System-Writes.

Der letzte Sichtcheck unter 30447/200 bestätigt: LastReviewDate ist nativ null, das HTML-Input-value leer und Save gesperrt; der DatePicker zeigt jedoch den Standardplatzhalter „31.12.2001“. Der Platzhalter ist kein gespeichertes Datum. 30449 setzt die öffentliche DatePicker-Eigenschaft `InputTextPlaceholder` auf einen leeren String, damit geleerte Reviewtermine auch sichtbar leer bleiben ([Microsoft: DatePicker-Eigenschaften](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/control-date-picker)). DefaultDate, SelectedDate-/DateTime-Handler und Save-Payload bleiben unverändert; die vollständig leere Anzeige ist für beide Reviewpicker vor Save und nach sauberem Wiederöffnen im frischen Player bestätigt. Keine Abnahmekriterien abgeschwächt.

| Aktueller lokaler Kandidat | SHA-256 |
|---|---|
| GovernancePortal_1.0.0.30449_1.0.0-alpha.4.1.0.zip | `4c41f8e57c9dea79cd8f6622a9f980f7855305489841ba03345a15fc8974695a` |
| gp_governanceportal_c93a1_DocumentUri.msapp | `6c45aa7056d89f5bd615eca2247db178f39510a7cc17f7df9288381f30113f7e` |

Build/Canvas-/Solution-Pack/SourceCode-Unpack Exit 0; vier kanonische YAMLs und ZIP-msapp bytegleich. **20/20 verfügbare Abschluss-Gates Exit 0; 2.381 echte Power-Fx-Assertions (2.032 Record + 212 Choice + 137 Capability), 57 Formeln, 13 Python-Regressionen.** Die 16 zusätzlichen Whole-Choice-Blank-Assertions ergänzen die vorhandenen Value-Prüfungen: zehn optionale native Blank-Round-Trips für Asset/System und sechs explizite Asset-Leeren-Events. Keine Prüfung entfernt oder abgeschwächt. Alle 33 Patch-Spalten writable und 17/16 Load-/Save-Mappings unverändert. Canvas-/Provisioningversion und kanonisches msapr unverändert. Private Build-/Gate-/Hash-/Handoff-Ausgaben unter `artifacts/p2-local-30449/`; Import, gezieltes Publish, ein Datensatz-Save und Cleanup wurden anschließend im separat genehmigten Scope ausgeführt und nativ belegt. Pester/PAC-Validate bleiben nicht verfügbar, historische kompilierte Controls im Pack ersetzen keine neue Maker-Prüfung.

### Genehmigter DEV-Scope 30449 – vollständig verbraucht

[AGENTS.md](../../AGENTS.md) verlangt „Merge/Release/Live-Writes separat.“ Kandidat 30449 und der zusätzliche Save nach dem dokumentierten Stop waren von der alten Freigabe nicht erfasst. Die menschliche „freigabe“ vom 07.10.2026 genehmigte den vorbereiteten neuen Scope. Die unveränderliche `APPROVED-SCOPE.json` und die verbrauchten Zähler liegen privat unter `artifacts/p2-20261006/dev-abnahme-30449-20261007/`; die frühere PREPARED-Datei bleibt historische Vorbereitung.

| Aktion | Genehmigter Höchstumfang |
|---|---|
| Import | **1** unmanaged DEV-Import ausschließlich 30449 mit obigem Hash, ohne `--publish-changes`/Publish All; Postexport und nativen Ausgang klären, kein Retry |
| Studio | **1** manueller Save-Versuch, falls nötig **je 1** öffentliches Personen-/Lookup-Rebinding; kanonische Regeln, echte Suchregeln und alle 19 Quellen exportprüfen |
| Publish | **1** gezieltes App-Publish nach Checker/Hostvergleich, veröffentlichten Export vergleichen |
| Fachlicher Save | **1** App-Edit ausschließlich Asset **13/v16.0**, Marker `GP-P2-30447-20261006-ASSET`: alle sechs Choices leeren; kein Create und kein weiterer Personen-/Datums-/Zyklus-Edit |
| Cleanup | **1** genau dieses synthetische Asset reversibel in den Papierkorb, erst nach bestandener Leerwert-/Wiederöffnen-Prüfung |
| Andere Writes | **0** Schema, Runtime-Metadaten, Bestandsassets 4–7, Systems, Rollen, Seeds/Reset, Papierkorbleerung, Publish All, DEV→Git, Merge, Release, Produktion |

Vor Import/Speichern aktuelle Lösung, App und native Assets/Systems lesend abgleichen: Asset 13 weiterhin v16.0 mit den sechs alten Choice-Werten, alle übrigen Werte exakt zum Abschluss-Snapshot; Bestandsassets und leere Systems unverändert. Vor dem einen Save alle sechs leeren UI-Auswahlen/Dirty-Zustand belegen. Danach alle sechs Werte **native null**, Quelle **v17.0**, übrige 25 deklarierte Felder und weitere native Geschäftsfelder unverändert; vollständiger Vorbestand unverändert. Beide bereits geleerten Reviewpicker müssen DOM-value und placeholder leer zeigen. Sauberes Wiederöffnen zeigt leere Auswahlen, „Keine Änderungen“ und gesperrtes Save. Erst dann Asset 13 mit exakter Marker-/ID-/Versionsprüfung reversibel bereinigen, Papierkorbherkunft und vollständige Ausgangsbestände belegen. Bei abweichendem Ausgang stoppen und nur lesen; keine Retries. Der bereits bestandene Rest von P2 wird erhalten.

## Abschluss der fokussierten DEV-Abnahme 30449

**30449-Verbrauch:** Import **1/1** ohne `--publish-changes`/Publish All, öffentliche Personen-/Lookup-Rebindings **je 1/1**, manueller Studio-Save-Versuch **1/1**, gezieltes App-Publish **1/1**, Asset-Edit **1/1**, reversibles Cleanup **1/1**. Create, Schema-/Runtime-Metadaten-/Bestands-/System-/Rollen-Writes, Seed/Reset, permanente Löschung, DEV→Git und Merge/Release/Produktion **0**. Import, Postimport-/Publikations-Export und native Abschlusslesesitzung jeweils Exit 0. Vorbestand und Assets-/Systems-Schema unverändert. Private Freigabe, Zähler, Quellen-/Host-/Wiederöffnen-/Papierkorb- und Abschlussbelege unter `artifacts/p2-20261006/dev-abnahme-30449-20261007/`; keine Rohbelege oder Personendaten versioniert.

Der alte 30447-Scope bleibt bei 15/15 Edit-Versuchen und 0/1 Cleanup abgeschlossen; dessen fehlgeschlagener Edit 14 wird nicht nachträglich als bestanden markiert. Der neue 30449-Scope enthält genau einen eigenen erfolgreichen Edit. PAC meldet Dienstkonto und Import/Export Exit 0; Studio speichert 202, Maker bestätigt 202 Live. Die private Hostprüfung umfasst jede kanonische Regel und beide tatsächlichen generierten Suchbindungen. Nach Quellen-/Wiederöffnen-Prüfung wurde ausschließlich Asset 13/v17 bereinigt; alle Bestandsfelder/Versionen und beide Listenschemata sind vollständig abgeglichen.

## Genau ein primäres nächstes Arbeitspaket

**P3 · Change – lokale Implementierung und Abnahmevertrag**, Modellklasse `deep-reasoning`. Den führenden Architekturvertrag für Change und die vorhandenen Provider-/Personen-/Choice-/Lookup-Verträge lesen, den ersten nutzbaren Formularumfang mit Asset-Bezug, Verantwortlichen/Genehmiger, Planung, Risiko, Umsetzungs-/Rollback-Plan und Status festlegen. List/Create/Load/Edit/Save samt nachvollziehbarer manueller Genehmigungssemantik lokal umsetzen und tatsächliche Formeln/Mappings prüfen; automatische Freigabe-Flows folgen später. Kandidat bauen, verfügbare Abschluss-Gates ausführen und einen konkreten, begrenzten DEV-Scope vorbereiten. P2 ist im DEV-Scope abgeschlossen; alle Kontingente der 30449-Abnahme sind verbraucht. `weiter` beauftragt dieses lokale P3-Paket. Import, Publikation, fachliche DEV-Writes, Merge/Release und Produktivfreigabe bleiben separat freizugeben.

Die native ReviewCycleMonths-Spalte enthält keine Min-/Max-Grenzen. Es wurde kein Schema-Write oder unzulässiger Live-Grenzwerttest ausgeführt. Diese belegte Abweichung bleibt vor einer Produktivfreigabe zu klären; die begrenzte P2-Abnahme ersetzt diesen Nachweis nicht.
