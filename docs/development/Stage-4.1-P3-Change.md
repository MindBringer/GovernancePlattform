# Stage 4.1 P3 – Change

Stand 07.10.2026, Branch `codex/stage41-p3`, Basis `d3ed7105969f58941ebdef799b758bfa12f1695e` aus P2-Draft #18. Modellklasse `deep-reasoning` wegen Schema-/Connector-/Canvas-Kopplung und Genehmigungssemantik. P2 bleibt 30449 / Canvas 202 Live; P3 ist nicht in DEV abgenommen.

## P3a: lokale Voraussetzungen

Die Repository-Prüfung zeigt eine zusätzliche Abhängigkeit vor der Canvas-Implementierung: Das kanonische msapr und das gepackte msapp enthalten 19 Quellen, darunter Assets und Systems sowie vier Beispielquellen. **Changes ist nicht verbunden.** Ein Registry-Eintrag `DataSourceKey: "Changes"` erzeugt keine Connectorverbindung. Die Architektur hatte 31 Change-Felder, aber keine Asset-Lookup-Spalte und keine native Spalte für das vorhandene siebenstufige Statusmodell; `ApprovalStatus` hat nur vier Werte. `GovernanceStatus` bleibt der allgemeine Lifecycle und wird nicht umgedeutet.

Der lokale Kandidat ergänzt:

- `Changes.LinkedAsset`: optionaler, nicht indizierter Einzel-Lookup auf `Assets.Title`; keine zusätzliche Relations-Liste oder zweite Speicherung.
- `Changes.ChangeStatus`: optionale, nicht indizierte Choice mit den sieben Schlüsseln/Labels aus `status-models.yaml`; Metadaten-Default `ChangeStatus:Draft`. Native Choice-Labels und interne Schlüssel bleiben getrennt.
- Den bestehenden nativen `Changes.Title` als erforderliches Textfeld mit maximal 255 Zeichen in Architektur und Formularmetadaten. Keine zweite Title-Spalte. Title ist Zeile 0; alle vorhandenen Formularzeilen behalten ihre Position.
- `Change.allowVersioning=true`, damit fachliche Status- und Planänderungen nach Aktivierung eine native Historie erhalten. Alte Versionen werden nicht rekonstruiert.

Der Compiler erzeugt 34 deklarierte Felder einschließlich des nativen Title. Die bestehenden 31 Felder bleiben unverändert. Der echte Metadatengenerator liefert genau **13 neue Zeilen**: sechs Field-/FormFieldDefinitions für Title/LinkedAsset/ChangeStatus und sieben ChoiceValues. Genau **eine vorhandene Zeile** wird geändert: `ObjectTypes/Change.AllowVersioning=false→true`. Die übrigen **1.017 generierten Zeilen** sind unverändert. Keine Umsortierung bestehender Felder, kein Backfill, kein Umstellen der versiegelten Basis-Description.

`Test-ChangeContract.ps1` prüft den Compiler, XML-Generator, Status-/Choice-Übereinstimmung und den tatsächlichen Metadaten-Delta am isolierten Write-Boundary ohne PnP/Auth/Tenantzugriff. Der exportierte Plan verwendet einen ausdrücklich synthetischen Assets-GUID; der spätere native Schritt muss ihn anhand der gelesenen Assets-Listenidentität ersetzen. Der Title-Vertrag und der Change-Vertrag laufen auch in CI.

## P3a: erster DEV-Versuch gestoppt, Indexvertrag korrigiert

Die ausdrückliche Freigabe auf Kandidat `0ede226bb150eda2c74aba0289e80a28610877c7` wurde am 07.10.2026 begonnen. Die native Leseaufnahme bestätigt Solution 30449, gespeichert/Live 202, erforderliches schreibbares Title Text/255 und bereits eingeschaltete Changes-Versionierung mit 50 Hauptversionen. LinkedAsset und ChangeStatus sowie die 13 neuen Metadatenzeilen fehlen. Eine vorhandene Change-Zeile, vier Assets und 875 Zeilen in den vier betroffenen Metadatenlisten wurden vollständig gesichert.

Der erste Add von LinkedAsset mit `Indexed=TRUE` scheitert am nativen Indexlimit: Changes enthält bereits **20 indizierte Spalten**. SharePoint erlaubt [höchstens 20 Indizes pro Liste](https://support.microsoft.com/de-de/sharepoint/data-and-lists/add-an-index-to-a-list-or-library-column). Verbrauch: **ein Spalten-Add-Versuch von zwei**, tatsächlich **keine neue Spalte**. Alle weiteren Kontingente bleiben 0; kein Retry, Metadaten-/Studio-/Export-/Fachdatensatz-Write, Import oder Publish. Der vollständige Nachvergleich aller sechs Listen bestätigt unveränderte Spalten/Settings, Datensatzwerte und Versionen. Die native Lesesitzung ist mit Exit 0 beendet. Private Freigabe, Vor-/Nachzustand und Stoppbeleg bleiben unter `artifacts/p3-20261007/dev-bruecke-20261007/`; diese ursprüngliche Freigabe ist abgeschlossen und berechtigt keinen neuen Versuch.

Die lokale Korrektur setzt ausschließlich die **beiden neuen** Architekturfelder auf `indexed:false`. Der echte XML-Generator muss für beide ausdrücklich `Indexed=FALSE` liefern. Alle bisherigen Architekturfelder/Indexflags und alle 20 nativen Indizes bleiben erhalten; keine Indexlöschung oder Änderung bestehender Spalten. Der Pilot sucht per Title/ID und verwendet Asset-Bezug/ChangeStatus im geladenen Record und Payload, ohne serverseitigen Filter auf diesen neuen Spalten. Status-/Asset-Ansichten und Indizes für größere Datenmengen brauchen später eine eigene belegte Strategie in P7. Ein indizierter Lookup allein löst die SharePoint-Listenschwelle nicht.

Das Gate prüft jetzt zusätzlich das native Indexbudget, wenn ein lokaler Changes-Snapshot angegeben wird. Der alte Kandidat ist mit dem tatsächlichen 20-Index-Snapshot rot (**20+2>20**, Exit 1); der korrigierte Vertrag ist grün mit **20+0**. Auch ohne Snapshot verlangt CI beide neuen Felder nicht indiziert. Vorhandene Indexabweichungen zwischen Gesamtarchitektur und Tenant werden in diesem additiven Scope weder überschrieben noch pauschal angeglichen.

Die Provider-Capabilities bleiben alle vier `false`; es wurden keine unaufgelösten Changes-Formeln in den kanonischen SourceTree geschrieben und keine Connector-Metadaten erfunden. Canvas-/Solution-/Provisioningversion bleiben unverändert. Der Pack-Nachweis der bestehenden App ist keine Change-Abnahme und kein neu zu importierender App-Kandidat.

## Erster Formularumfang nach der Connector-Brücke

19 geplante Load-/Write-Felder, jeweils gegen echte generierte Connector-Metadaten zu prüfen:

| Bereich | Felder |
|---|---|
| Identität und Bezug | Title, LinkedAsset, IsActive |
| Zuständigkeit | Owner, Approver |
| Einordnung und Status | ChangeType, ChangeStatus, ApprovalStatus, ChangeRisk |
| Planung und Durchführung | PlannedStart, PlannedEnd, ImplementationPlan, RollbackPlan, ActualEnd |
| Entscheidung und Auswirkung | ApprovedDate, EmergencyChange, DowntimeExpected, DowntimeMinutes, RollbackValidated |

Die übrigen 15 deklarierten Felder bleiben außerhalb dieses ersten Formulars und werden nicht gepatcht. `Description` bleibt außerhalb, bis ein eigener belegter Schreibvertrag vorliegt. Die vorhandenen P1/P2-Verträge gelten auch für Change: vollständige Hydrierung, originaler nativer Patch-Record, Claims-Identität, feldbezogene Choice-Schlüssel, echte Blank-Werte, positives Lookup-Ziel, delegierbare Titel-/ID-Suche, Dirty-/Modal-/Load-/Save-Sperren sowie frischer Modified-Vergleich. Keine atomare ETag-Garantie ohne native Evidenz.

## Manueller Ablauf für P3b

Die folgende Semantik ist der Implementierungs- und Testvertrag; sie ist noch nicht als App-Funktion verfügbar. Ein neuer Entwurf startet explizit mit ChangeStatus/ApprovalStatus `Draft`. Alte Datensätze ohne ChangeStatus verlangen vor Änderung eine bewusste Statuszuordnung; kein stiller Backfill oder Auto-Approval.

| ChangeStatus | Erlaubter nächster Status | ApprovalStatus |
|---|---|---|
| Draft | Submitted | Draft |
| Submitted | Approved oder Rejected | Submitted |
| Approved | Scheduled | Approved |
| Scheduled | Implemented | Approved |
| Implemented | Closed | Approved |
| Rejected | keiner | Rejected |
| Closed | keiner | Approved |

Entwürfe dürfen unvollständig gespeichert werden. Einreichen verlangt Asset, Owner, Approver, Change-Typ, Risiko, Umsetzungs- und Rollback-Plan sowie Start/Ende mit Ende ≥ Start. Derselbe Status ist für normale Edits zulässig; Statuswechsel müssen genau dem führenden Modell folgen. Der Genehmigungsstatus wird aus dem Ablaufstatus abgeleitet und nicht unabhängig frei verändert.

Genehmigen/Ablehnen muss eine explizite Entscheidung des zugeordneten Genehmigers sein. Dafür braucht die Implementierung eine nachgewiesene aktuelle Connector-Personenidentität; ein frei auswählbarer DisplayName oder eine E-Mail-Alias-Gleichheit reicht nicht. `ApprovedDate` wird nur beim ersten genehmigenden Übergang gesetzt und danach erhalten; bei Ablehnung bleibt es leer. Native Modified/Editor und die eingeschaltete Listenhistorie belegen den tatsächlich schreibenden Akteur. Diese UI-Regel allein ersetzt keine SharePoint-Rollenprüfung: direkte Listenrechte und die Produktivrollen bleiben P7.

Nach Einreichen sind Asset, Owner/Genehmiger, Change-Typ, Risiko und die beiden Pläne gegen beiläufige Edits zu sperren; ein größerer Planwechsel braucht später einen ausdrücklich definierten Revisionsprozess. Geplant/Umgesetzt/Geschlossen verlangt erhaltene Genehmigung; Umgesetzt zusätzlich ActualEnd. Rejected/Closed sind im Pilot schreibgeschützt. Termine sind zunächst Kalendertage; eine Bedienung mit Stunden/Minuten ist ein späterer Ausbau. Native unveränderte DateTime-Werte dürfen beim Laden oder einem anderen Feld-Edit keine Uhrzeit verlieren. DowntimeMinutes darf nicht negativ sein; ein DowntimeExpected=false darf vorhandene Zahlen nicht still löschen.

Die P3b-Tests müssen tatsächliche Load-/Payload-/Guard-Formeln mit synthetischen vollständigen Records ausführen: New/Edit/Blank-Personen und Choices, Lookup/Termine/0/false, Fremdfeld-Erhalt, Draft→Submitted→Approved→Scheduled→Implemented→Closed, Submitted→Rejected, ungültige Sprünge, fremder Genehmiger, fehlende Entscheidungsvoraussetzungen und stale Modified. Capabilities werden erst nach ausführbaren geprüften List/Create/Load/Edit/Save-Pfaden aktiviert. Automatische Flows, weitere Listen, Evidence und Reviews folgen ihren eigenen Paketen.

## Primäres nächstes Arbeitspaket: P3a DEV-Schema-/Connector-Brücke

**Korrigierter Scope vorbereitet, neu freizugeben.** Die vorherige P3a-Freigabe wurde nach dem Indexfehler gemäß ihrer Stoppregel beendet. Der neue Versuch ändert den zuvor freigegebenen Indexvertrag und braucht daher eine neue ausdrückliche Freigabe des geprüften Kandidaten und Planhashs. `weiter` beauftragt lokale Repoarbeit; die anschließende P3-Canvas-Implementierung bleibt beauftragt. Gemäß [AGENTS.md](../../AGENTS.md) ist „DEV→Git ebenfalls nur ausdrücklich beauftragt“.

Der konkrete Freigabeumfang ist ausschließlich:

1. Neue native Leseaufnahme von Changes, Assets und den vier betroffenen Metadatenlisten; alle vorhandenen Datensatzwerte/Versionen und Spalten/Settings sichern. App/Solution 30449 mit gespeichertem und Live-Host 202 als Vorzustand gegen die erhaltenen P2-Exporte bestätigen. Vorbestand, Listenidentität, native Title Text/required/255, eingeschaltete Versionierung, 20 vorhandene Indizes und etwaige bereits vorhandene neue Spalten prüfen. Bei Abweichung stoppen und den Plan vor einem Write abgleichen; keine pauschale Provisionierung. Den neuen Planhash und Kandidaten getrennt von der abgeschlossenen Freigabe binden.
2. Höchstens zwei neue Spalten auf Changes, genau nach diesem Vertrag und ausdrücklich **ohne zusätzliche Indizes**. Bestehende Spalten/Indizes, Listsettings und Versionshistorie erhalten. Versionierung ist bereits true und wird nur geprüft; **kein Listsetting-Write**. Kein fachlicher Datensatz-Edit oder Default-Backfill.
3. Höchstens 13 neue Metadatenzeilen und eine gezielte Aktualisierung `ObjectTypes/Change.AllowVersioning`; nur die vier Listen FieldDefinitions, FormFieldDefinitions, ChoiceValues und ObjectTypes. Bereits exakt passende Zeilen lesen statt neu schreiben; abweichende bestehende Zeilen nicht automatisch überschreiben. Alle übrigen Zeilen müssen unverändert bleiben. Keine vollständige Seed-/Metadata-Publish-Aktion.
4. In der bestehenden DEV-App genau eine echte Changes-Verbindung über Studio hinzufügen; bestehende Verbindungen erhalten. Höchstens ein manueller Studio-Save, kein gezieltes Publish, kein Import und kein Publish All. Autosave-Versionsänderungen protokollieren; P2 Live unverändert prüfen.
5. Genau eine lesende App-/Solution-Exportaufnahme und PAC-Unpack über ignoriertes Staging. Nach Quell-/Identitäts-/DataSources-Diff ausschließlich die erzeugte kanonische msapr-Referenz übernehmen. Vier kanonische Src-YAMLs bleiben bytegleich; bestehende native Regeln/Controls werden gegen den erhaltenen gespeicherten P2-202-Host geprüft. Personen-/Lookupregeln, Asset/System-Schreibrechte und Solutionidentität müssen erhalten bleiben. Neue fachliche Src-/Controlformeln oder weitere Bindungsänderungen stoppen vor Übernahme. Keine Erfindung/Anpassung von `x-ms-permission`.
6. Native Rückleseprüfung der neuen Felder, Lookup-Zielidentität, sieben Choices, Metadaten und Versionierung; vorhandene Inhalte/Versionen unverändert. Die echte Changes-Verbindung muss sämtliche geplanten 19 Felder writable zeigen. Wenn etwaige Typen/Rechte abweichen, zuerst gezielte lokale Reparatur; kein Daten-Save als Probe.

Neue Maximalbudgets: Schemaadds **2** (beide nicht indiziert), Listsetting/Indexänderungen **0**, neue Metadatazeilen **13**, Metadataupdate **1**, Studio-Quellenaddition **1**, manueller Studio-Save **1**, Export-/Unpack-/Referenzübernahme **1**. Keine automatischen Write-Retries nach Fehlermeldung oder Wertabweichung; zunächst readback und Stopp vor weiterem Write. Dieser Scope enthält keine fachlichen Creates/Edits/Deletes, Rollenänderungen, Imports, Publishes, Seed/Reset, Merge, Release oder Produktion.

Nach erfolgreicher Brücke wird innerhalb P3 lokal der oben definierte Canvas-Vertrag umgesetzt, ein neuer App-Kandidat gebaut und anschließend erst ein eigener begrenzter DEV-Funktionstest vorbereitet. P4 ist kein Teil dieses Arbeitspakets.

## Lokale Prüfung und Handoff

Der Kandidat umfasst Architektur, den bestehenden Title-Metadatengenerator, Vertragstests einschließlich Indexbudget, die Erweiterung des Schreibvertragsprüfers auf tatsächliche Changes-Patches, CI und Zustandsdokumentation. **23/23 verfügbare Abschluss-Gates Exit 0**, 15 Python-Regressionen und die unveränderten **2.381 tatsächlichen Power-Fx-Assertions** (2.032 Record / 212 Choice / 137 Capability), 57 Formeln. Die neue Changes-Patch-Regression scheitert vor der Prüfererweiterung mit Exit 1 und besteht danach. Vier isolierte Negativproben (fehlendes Lookup, falsches Choice-Label, abgeschaltete Versionierung, neuer Index bei ausgeschöpftem nativen Budget) werden vom tatsächlichen Change-Gate jeweils mit erwartetem Exit 1 abgewiesen. PAC-SourceCode-Pack/-Unpack und Solution-Pack der unveränderten P2-App jeweils Exit 0; vier YAMLs bytegleich, Solution-msapp bytegleich. Kein neuer Canvas-/Solution-Releasekandidat.

Komplette Gate-/Pack-/Round-Trip-Exit-Codes und SHA-256 der Korrektur stehen im privaten Handoff unter `artifacts/p3-local-index/`; die ursprünglichen lokalen Belege unter `artifacts/p3-local-schema/` und die verbrauchte Freigabe bleiben erhalten. Keine Logs, Personen-/Tenantsettings oder Buildausgaben werden versioniert. Pester fehlt; `pac canvas validate` wird von PAC 2.9.3 nicht unterstützt. Offlineprüfungen liefern keine erfolgreiche native Schema-/Connector-Brücke. CI am tatsächlichen finalen Head wird im Draft-PR/Handoff dokumentiert.

Originalworkspace mit elf gestagten Dateien, abgeschlossene P1-/P2-Branches und ihre Drafts bleiben erhalten; kein Merge/Release, Framework-PR #6 bleibt DO NOT MERGE.
