# P2 – Asset, Verantwortliche und Reviewtermine

Stand: 2026-10-06 · `codex/stage41-p2` · Basis P1 `a894b386632ed1128a2ff69a4620896d08f77bcd` · Modellklasse `standard-reasoning`.

**Lokal abgeschlossen: Solution 1.0.0.30446. DEV-Abnahme offen; DEV bleibt 30445 / Canvas 196 Live.** P2 bereitet den Asset-Pilot mit dem vorhandenen 17-Felder-Vertrag vor. Es erweitert weder Schema noch Save-Mapping oder Provider-Capabilities. Die P1-Abnahme ist abgeschlossen und wird nicht wiederholt.

## Architektur und Pilotumfang

Führend sind `architecture/platform.yaml`, `fields.yaml`, `object-fields.yaml`, `forms.yaml` und `choices.yaml`. Asset hat 31 deklarierte Felder; davon sind genau 17 in Load, Formular und Save enthalten. Der tatsächliche aliastierte Formularfilter und die NativeControlType-Zuordnung werden gegen den Compiler geprüft.

| Pilotfunktion | Felder | Vertrag |
|---|---|---|
| Identifikation | Title, AssetType | Title verpflichtend/getrimmt; AssetType optionales Textfeld |
| Verantwortliche | Owner, DeputyOwner, BusinessOwner, TechnicalOwner, DataSteward | Einzelperson; Claims-Principal aus UPN. Unveränderte native Objekte mit Email-Alias, Department und JobTitle bleiben erhalten; Wechsel verwendet ausgewählte UPN, Leeren schreibt Blank |
| Einstufung und Status | Criticality, DataClassification, LifecycleStatus | Nur aktive Architektur-Choices, feldbezogene Schlüssel. Status im Pilot ist LifecycleStatus; DataClassification behält bewusst den bestehenden Criticality-ChoiceSet-Vertrag |
| Schutzbedarf | ConfidentialityRequirement, IntegrityRequirement, AvailabilityRequirement | Bestehender Criticality-ChoiceSet; optionale Auswahl kann geleert werden |
| Reviewplanung | LastReviewDate, NextReviewDate, ReviewCycleMonths | Kalenderdatum im Picker; unveränderte native DateTime-Werte behalten Uhrzeit. Geändertes Datum wird DateTime zu 00:00 App-Lokalzeit, explizites Leeren typisiert Blank. Zyklus optional; Architekturgrenzen 1–120 Monate, native Durchsetzung ist in DEV zu prüfen |
| Aktivität | IsActive | Boolean; false bleibt erhalten |

Bewusst außerhalb des Pilotformulars bleiben **14 Felder**: GovernanceID, GovernanceStatus, Description, ComplianceScope, Tags, SourceChannel, CorrelationID, ValidationStatus, LastValidationAt, SearchKeywords, BusinessCritical, RecoveryPriority, RTOHours und RPOHours. Dazu gehören Metadaten/Automationswerte, das native Description-Feld, Mehrfachauswahl und zusätzliche Wiederanlaufplanung. Sie werden nicht in den Patch aufgenommen. Für diesen Pilot gibt es keine automatischen Governance-ID-/Statusregeln, Reviews, Historieneinträge oder Evidence-Bezüge. Das wird erst in den späteren Paketen eingebunden.

## Umsetzung und belegte Lücken

Die fünf Personenfelder und alle 17 Save-/Load-Felder waren bereits implementiert. Die vorhandenen Identitäts- und Choice-Verträge werden erhalten und mit tatsächlichen Formeln geprüft. Neu ist **„Datum leeren“** neben optionalen Datumfeldern: verborgen bei Pflichtfeldern, gesperrt bei leerem Wert, ReadOnly, Load, Save oder Verwerfen-Dialog. Der Handler setzt typisiertes Blank, markiert ausschließlich die betroffene Editorzeile, setzt den Picker zurück und revalidiert.

Die neue Datumsprüfung reproduzierte einen echten Power-Fx-Typfehler: `Patch` in einen DateTime-Editorwert mit `Self.SelectedDate` vom Typ Date wurde abgelehnt. Die Aktualisierung verwendet jetzt `Self.SelectedDate + Time(0, 0, 0)` und einen typisierten leeren DateTime-Wert. Die Initialisierung nutzt ebenfalls DateTimeValue und typisiertes DateTime-Blank; ihre zusätzliche Regression reproduzierte denselben Typfehler und prüft erhaltene Stunden/Minuten/Sekunden eines Metadaten-Defaults. Unveränderte Daten werden weiter direkt hydriert. Der gemeinsame Control gilt auch für System; dessen 16 Save-Felder und bisherige Verträge bleiben unverändert. Keine native Uhrzeit wird allein beim Öffnen oder durch eine andere Feldänderung überschrieben.

## Kandidat und lokale Nachweise

Canvas `1.0.0-alpha.4.1.0`, Provisioning `6.2.5` unverändert; nur die vierteilige Solution-Buildnummer erhöht.

| Artefakt | SHA-256 |
|---|---|
| GovernancePortal_1.0.0.30446_1.0.0-alpha.4.1.0.zip | `596465673942680147b6fba2b8f21932bd08c7b7ef882869ab28efd9fd3ce9e5` |
| gp_governanceportal_c93a1_DocumentUri.msapp | `3b4cc54dfac2870f3211766edf00201b20b78eeb6ea3afabf927915decda0f32` |
| Kanonisches erzeugtes msapr (unverändert) | addc5517a8f8abd5ba74b3b7510b827132eb20b0bdd9c54e2c1fc3f5323a802f |

**Build, Canvas-/Solution-Pack und SourceCode-Unpack Exit 0**, vier Src-YAMLs bytegleich im Round-Trip. ZIP enthält bytegleich das geprüfte msapp. **20/20 verfügbare Projekt-Gates Exit 0**: Architektur/Konsistenz, PowerShell-Syntax, Asset-/System-Title, SystemDescription, YAML/Canvas, Accessibility (21 Controls), Registry/Runtime, Referenzen, Personen, Artefakt, Choice/Capability/Record Power Fx, Audit und Diff. Alle **33 tatsächlichen Patch-Spalten** im kanonischen und gepackten Connector read-write.

**2.349 tatsächliche Power-Fx-Assertions**: 2.000 Record + 212 Choice + 137 Capability, 57 Verhaltensformeln geparst; 13 Python-Regressionen. P2 prüft alle fünf Personenfelder in New/Edit mit Wechsel und Leeren, normalisierte Claims, Erhalt der übrigen Personeneigenschaften/Felder und sauberes lokales Wiederöffnen. Beide Reviewtermine und sechs Choices sind einzeln gesetzt/geleert; andere Werte und genau eine Dirty-Zeile bleiben nachgewiesen. Optionales Number-Blank/0 und Boolean-false bleiben erhalten. Das Harness wertet tatsächliche Guards, Update-Records, Load-, Hydrierungs- und Payloadformeln aus; Gallery-Mutation, Reset/OnChange-Verhalten, Directory-/SharePoint-Connector und Hostkompilierung erfordern DEV.

Toolchain: PAC 2.9.3, PowerShell 7.6.3, Python 3.14/PyYAML 6.0.2. Erster Build Exit 1 durch den Homebrew-Python ohne PyYAML; mit bereits vorhandener validierter Python-Umgebung und ohne erneuten Versionsschritt vollständig Exit 0. Pester nicht installiert, `pac canvas validate` in PAC 2.9.3 nicht unterstützt; keine grünen Gates daraus ableiten. Die vorhandene CI prüft Quelle/Compiler/Artefakt; die optionalen Engine-Tests laufen lokal.

Private Logs, Gate-Befehle/Exit-Codes, Kandidatenhashes und Round-Trip unter `artifacts/p2-local-30446/`; keine Logs, Tenantsettings, Personen oder ZIP-Ausgaben versioniert. Die historischen Controls/SARIF im msapr/Pack sind keine Maker-Abnahme von P2. Das bestehende versionierte msapp ist das geprüfte Solution-Artefakt.

## Genau ein primäres nächstes Paket: begrenzte P2-DEV-Abnahme

Dieser Scope ist **vorbereitet, noch nicht freigegeben**. [AGENTS.md](../../AGENTS.md) verlangt separate Beauftragung für Live-Writes, Import und Veröffentlichung. P1-Write-Kontingente sind verbraucht und werden nicht wiederverwendet. Modellklasse `standard-reasoning`; bei belegter komplexer Host-/Connector-Ursache neu bewerten.

| Aktion | Höchstzahl / Grenze |
|---|---|
| DEV-Import | **1** unmanaged Import ausschließlich des oben gehashten ZIP; ohne Publish All/`--publish-changes`; Timeout durch serverseitigen Verlauf/Postexport klären, kein blinder Retry |
| Unterstützte Studio-Verarbeitung | **1** manueller Draft-Save-Versuch; falls erforderlich je **1** öffentliches Personen-/Lookup-Rebinding bei unveränderten Fachformeln; echte generierte Suchregeln exportprüfen, keine private SearchItems-Regel authorieren |
| Veröffentlichung | **1** gezieltes App-Publish nach Checker und Vergleich des gespeicherten Hostkandidaten; keine andere App/Umgebung |
| Fachlicher Create | **1** synthetisches Asset, Marker `GP-P2-30446-20261006-ASSET`; keine Bestandsdatensätze |
| Fachliche Asset-Edits | **14** App-Save-Versuche gemäß Schrittfolge unten, jeweils Quelle prüfen und sauber wiederöffnen |
| Reversibles Cleanup | **1** ausschließlich diese neue Asset-ID nach Titel/Listenherkunft; Papierkorb und unveränderten Vorbestand prüfen |
| Andere Writes | **0** Schema, Runtime-Metadaten, Rollen, Bestandsdaten, Systems, Seeds, Reset, Papierkorbleerung, Publish All und DEV→Git |

Vor Writes aktuellen App-/Solution-/Quellenstand lesend prüfen. Ein natives Baseline-Snapshot aller Asset-Felder und Versionswerte, Systems-Bestand sowie Checker-/Suchbindungsnachweise lokal sichern. Die zwei bestehenden, für diesen Abnahmescope zulässigen Testidentitäten A/B werden privat per UPN verifiziert; keine Konten anlegen oder Rollen ändern. Fehlt eine zweite zulässige Identität, bleibt der Personenwechsel offen und wird nicht durch dieselbe Person ersetzt.

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
