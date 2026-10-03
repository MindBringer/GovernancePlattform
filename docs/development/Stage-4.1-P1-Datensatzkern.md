# P1 – Datensatzkern und DEV-Abnahme

Stand: 2026-10-03. **30444 / Canvas 193 Live; Host-Suche, Titeleingabe, Creates und unverändertes Wiederöffnen belegt. Freigegebene Monitor-Diagnose reproduziert den Description-Schreibschutzfehler beim System-Edit; Quelle Version 1.0/unverändert, Testsystem reversibel bereinigt. P1 nicht abgenommen.** Genau ein primäres Folgepaket: lokalen Schreibvertrag für Systems.Description mit Regression reparieren und konkreten DEV-Kandidaten vorbereiten. Diagnose-Create/Edit/Delete je 1/1 verbraucht, keine weiteren Live-Writes. Modellklasse `deep-reasoning` wegen Canvas-/Provider-/SharePoint-Kopplung und Datenintegrität.

## Kandidat und Grenzen

- Branch `codex/stage41-p1`, Basis P0 `5caee00823032b4306f0bdaa900ca9817a53610e`, [Draft-PR #17](https://github.com/MindBringer/GovernancePlattform/pull/17) auf `codex/stage41-p0`.
- Zuvor freigegebener/importierter Kandidat: Solution **1.0.0.30443**, Canvas `1.0.0-alpha.4.1.0`, Provisioning `6.2.5`; Versionsreihen getrennt. Import 188 Live, erster Studio-Schritt 189, öffentliche Personenwiederherstellung in Draft 190 und gezielt publiziert **191 Live**; kanonische Paketquellen unverändert.
- Letzte erfolgreiche begrenzte Paketabnahme: **P0 30440 / Canvas 184**. Vor der 30444-Fortsetzung belegter DEV-Stand: **30443 / Canvas 191 Live laut Maker**, Formelchecker ohne Fehler und Personen-Suchbindung exportbelegt. Der unten dokumentierte 30443-Testumfang ist ausgeführt: zwei Creates, zwei normale Edit-Versuche (einer erfolgreich), ein Konflikt-Quellen-Edit, ein blockierter App-Save und zwei reversible Löschungen. Keine automatische Freigabe für weitere Saves/neue Kandidaten; frühere P0-Save-Freigaben ebenfalls verbraucht. Der gesondert freigegebene 30444-Umfang und sein Verbrauch stehen unten.
- Kanonische Bearbeitungsquelle bleibt `powerplatform/canvas/GovernancePortal/`; SourceCode-Round-Trip nur in ignoriertem Staging. Keine DEV→Git-Übernahme.
- P1 erhält die vorhandenen nativen Save-Verträge. Kein zusätzliches Asset-Fachmapping, neuer Provider, Evidence-/Reviewprozess oder Produktivrollout. Capabilities benennen ausführbare Pfade; Live-/Rollenabnahme bleibt separat.

## Verhalten

Asset und System zeigen native Listen mit Titelanfangssuche oder genauer positiver ID. Ungültige ID liefert einen sichtbaren Fehler und kein ungewollt ungefiltertes Ergebnis. Galeriepfeile und Bildlaufleiste laden weitere Datensätze; kein vorab begrenztes `ClearCollect`, keine ID-Bereichsfilter, keine vermeintliche Gesamtzahl aus `AllItems`.

Öffnen lädt nach `Refresh` den nativen Record mittels ID-Gleichheit. Geladene Werte werden in denselben Editor wie die Neuanlage übernommen. Fehlender/unzugänglicher Datensatz bleibt in der Liste mit Fehlermeldung. Fehlende/falsch typisierte Metadaten und unbekannte gespeicherte Choices sperren Save. Eine unbekannte Choice wird sichtbar als ungültiger Wert erhalten, bis eine gültige Auswahl getroffen wird.

Unveränderte Defaults dürfen keine Felder als geändert markieren. Leere optionale Werte, numerische `0`, `false` und Datum/Uhrzeit bleiben erhalten; Lookup-IDs ohne positives Ziel werden seit 30444 als leer normalisiert; unveränderte Personenobjekte behalten originale Claims, Email und Zusatzattribute. Ein bestehender Lookup wird auch außerhalb des bisherigen Lookup-Caches angezeigt. Die begrenzte Suche nach neuen Lookup-Zielen bleibt der bisherige Vertrag und ist kein Nachweis vollständiger Lookup-Auswahl bei großen Listen.

Bearbeiten setzt eine positive ID, deren Übereinstimmung mit der geladenen ID, vollständige Hydrierung und echte Änderungen voraus. Speichern patcht den original geladenen nativen Record. Eine frische `Modified`-Prüfung sperrt vor dem Patch bei paralleler Änderung oder fehlendem Zeitstempel; fehlende Datensätze und Connectorfehler werden angezeigt. `ErrorKind.Conflict` sperrt erneutes blindes Speichern. Unklarer Save-Ausgang erfordert Quellenprüfung. Der Zeitstempelvergleich allein garantiert keine atomare Konfliktvermeidung zwischen Prüfung und Patch; Connector-/ETag-Verhalten ist ein DEV-Gate.

Load und Save sperren Eingaben, Suche und Navigation. Abbruch oder Navigation bei ungespeicherten Änderungen öffnet den Verwerfen-Dialog; nach Verwerfen bleibt die Objekttypauswahl erhalten bzw. die gewünschte Navigation wird ausgeführt.

## Bestehender Feldumfang

| Typ | Geladene und geschriebene native Felder |
|---|---|
| Asset (17) | Title, AssetType, Owner, DeputyOwner, BusinessOwner, TechnicalOwner, DataSteward, Criticality, DataClassification, LifecycleStatus, ConfidentialityRequirement, IntegrityRequirement, AvailabilityRequirement, LastReviewDate, NextReviewDate, ReviewCycleMonths, IsActive |
| System (16) | Title, Description, Owner, GovernanceStatus, Criticality, SystemType, Environment, LastReviewDate, NextReviewDate, ReviewCycleMonths, IsActive, LinkedAsset, MonitoringStatus, BackupStatus, AuthenticationType, SupportModel |

Das aktuelle Formular zeigt ausschließlich diesen Umfang. Felder außerhalb dieser Payloads werden nicht geschrieben und behalten ihren Quellenwert. Vollständige Asset-Felder/Status, Verantwortliche und Reviewtermin-Abnahme folgen P2. Alle sieben anderen Registry-Typen melden List/Create/Edit/Save als false; Asset/System melden die vier implementierten Fähigkeiten als true.

## System-Title-Metadaten

Native SharePoint-Title-Spalte und bisheriger Patch existierten bereits, die Formulardefinition fehlte. `architecture/object-fields.yaml` ergänzt System-Title (Text, required, maxLength 255, General, SortOrder 0). Der Metadatengenerator behandelt die beiden vorhandenen nativen Asset-/System-Titel entsprechend; bestehende Formularzeilen werden nicht umnummeriert.

Die Offline-Ausführung des tatsächlichen Generators mit abgefangener Schreibgrenze liefert exakt:

| Liste | Schlüssel | Kernwerte |
|---|---|---|
| FieldDefinitions | `System:Title` | Title/Titel, Text, IsRequired/IsVisible/IsActive true, SortOrder 0 |
| FormFieldDefinitions | `System:Edit:Title` | Form `System:Edit`, Title, General, RowNumber/SortOrder 0, RequiredIf `true`, IsActive true |

1.014 andere generierte Zeilen bleiben unverändert. Der vollständige Plan liegt lokal ignoriert unter `artifacts/p1-20261002/system-title-plan.json`. Kein allgemeines Provisioning, Seed/Reset oder erneutes Schreiben der bereits übernommenen Asset-Title-Zeilen.

## Historische Offline-Gates am Kandidaten 30443

| Gate | Ergebnis / Exit-Code |
|---|---|
| Vollständiger `Build.ps1`, PAC 2.9.3 SourceCode-/Solution-Pack | 0; 30443, kein Import/Publish |
| Echter YAML-Parser / Regression | 0 / 0; vier Quellen, vier Regressionstests |
| Canvas-Artefaktvergleich / SourceCode-Unpack | 0; vier kanonische YAMLs unverändert |
| Architecture / ArchitectureConsistency | 0 / 0 |
| PowerShell-Syntax | 0; 35 PS1-/PSM1-Dateien |
| Asset-/System-Title-Vertrag | 0 / 0; je zwei isolierte Zusatzzeilen, andere 1.014 unverändert |
| CanvasSource / Registry / Runtime CheckOnly / References | jeweils 0 |
| Personen-Quellvertrag | 0; vier negative Fixtures verworfen |
| Accessibility-Quellvertrag | 0; 20 Controls / fünf Galerien, Load-/Save-/Modal-Sperren |
| Capability-Engine | 0; 137 tatsächliche Assertions |
| Choice-Quell-/Compiler-/Enginevertrag | 0; zehn Adapter / 42 Werte, 212 tatsächliche Assertions |
| Record-Quell-/Compiler-/Enginevertrag | 0; Asset 17 / System 16 Felder, 281 tatsächliche Assertions, 53 mehrzeilige Formeln geparst |
| Repository-Audit / Diff | 0 / 0 |

**630 tatsächliche Offline-Power-Fx-Assertions.** Die Recordtests werten tatsächliche Projektionen, Hydrierung, Payloads, Guard- und Galerieformeln aus. Voll-/Leerwerte, Datumszeiten, native Personenalias-/Claims-Werte, optionales Leeren, unveränderte Defaults, unbekannte Choices, fehlende Metadaten, falsche Kontrolltypen, Modified-Konflikte und 3.000-Zeilen-Fixtures sind enthalten. Ein lokaler Fixture-Test beweist keine SharePoint-Serverdelegation.

CI enthält Record-Quell-/Compilervertrag, beide Title-Gates, YAML-Parser/Regression und den expliziten Aliasvertrag für den Formularfilter. Der optionale Engine-Test führt nun auch den tatsächlichen Formularfilter mit gemischten Asset-/System-/fremden Metadaten aus (sechs zusätzliche Assertions). Optionale Engine-DLL-Tests laufen lokal. Vor der Reparatur waren alle drei CI-Checks am Head `67a18e0049b75f468c826ca26a1e766206911cfd` erfolgreich; dieser grüne Stand erkannte den später belegten Studio-YAML-Fehler nicht. Der Reparaturhead wird nach Push erneut gegen den tatsächlichen PR-Head geprüft; exakter Head/URLs im Draft und ignorierten Handoff. Alle 18 verfügbaren Abschluss-Gates am 30443-Kandidaten Exit 0. Pester nicht installiert; PAC `canvas validate` in 2.9.3 nicht vorhanden. 30443/191 öffnet ohne Formelfehler, Personenbindung ist exportbelegt; keine vollständige Tenant-Round-Trip-/Rollen-/ETag-/Delegationsabnahme. Die historischen 30442-Formelbefunde und aktuelle 30443-Grenzen stehen unten.

## Historische Kandidaten-Hashes 30443

- `GovernancePortal_1.0.0.30443_1.0.0-alpha.4.1.0.zip`: SHA-256 `e2cea445e8a4e3e2cddb1cf96f21be8ccfda57807eb53cd02d6c815c2c313607`.
- Versioniertes `gp_governanceportal_c93a1_DocumentUri.msapp`: SHA-256 `1d5fa3d1fea7c91f9df1feb2811f6d2611a40d87d7c23ea4c3e62a4a9b46803e`.

Originaler Workspace mit elf gestagten Dateien und P0-Branch erhalten; keine Framework-Locks/-Runtimeversionen, kein Merge/Release. PR #6 bleibt DO NOT MERGE. Neue Logs, ZIPs, Tenantsettings und personenbezogene Daten bleiben außerhalb Git.

## Beobachteter DEV-Versuch mit 30441

Die Freigabe vom 02.10.2026 wurde begrenzt ausgeführt: Vorzustand 30440/184 und dessen Studio-msapp geprüft; genau `System:Title` und `System:Edit:Title` neu geschrieben und nach Reload mit allen Feldern/Boolean-Werten geprüft (je ID 721 in ihrer Liste). Alle-Elemente-Vorstand: vier Assets, IDs 4–7; keine Systems. Kein allgemeines Provisioning/Seed/Reset.

Import 30441 ohne `--publish-changes` und ohne Publish All Exit 0; Postexport Exit 0, Solution 30441 und msapp bytegleich mit dem freigegebenen Kandidaten. Maker zeigt nach Import **185 Live**. Studio meldet vor Öffnen **PA1001 / YamlInvalidSyntax**, ursprünglich `scrShell.pa.yaml(837,57)`: Doppelpunkt mit Leerzeichen in einem ungeschützten YAML-Formelwert. Beide neuen Asset-/System-Öffnen-Beschriftungen wurden lokal als `|-`-Blockskalare geschrieben; die Power-Fx-Formeln bleiben gleich. Der neue Parser verwirft diesen früheren Fehler vor Pack; vier Regressionstests sichern Fehlererkennung und Formelerhalt.

Kein Studio-Rebinding, Checker, gezieltes Save/Publish oder fachlicher Create/Edit/Conflict/Delete ausgeführt. Ein frischer Player erreicht den Startbildschirm, zeigt jedoch den Hinweis auf eine kommende Version; das belegt keinen aktuellen P1-Runtime-Stand und ersetzt die Studio-Prüfung nicht. Test-/Rollen-/Delegationsgates bleiben offen. Lokale Belege und ungenutzte Write-Kontingente in `artifacts/p1-20261002/DEV-ABNAHME.json`; keine persönlichen Daten/Logs in Git.

## Beobachteter DEV-Versuch mit 30442

Die erneute konkrete Freigabe wurde ausgeführt: Vorzustand 30441/185 samt Paketidentität und beide vorhandenen Metadatenschlüssel gelesen, keine Metadaten-Writes. Import 30442 unmanaged ohne Publish All/`--publish-changes` Exit 0; Postexport Exit 0, msapp bytegleich mit freigegebenem Kandidaten. Maker zeigt **186 Live**. Studio öffnet erfolgreich; der YAML-Fehler ist behoben. Studio hat **187 automatisch gespeichert, nicht veröffentlicht**.

App-Checker: genau zwei Formelbefunde in `lblEditorInitialize.OnSelect`: `ObjectTypeKey` wird nicht erkannt, daraus Error/Text-Vergleich inkompatibel. 70 Accessibility-, zwölf Leistungs- und zwei Datenquellenbefunde; keine angezeigten Laufzeitbefunde. Im neuen `Filter(colFormFields As formField, ...)` muss die Spalte als `formField.ObjectTypeKey` referenziert werden. Der ergänzte Offline-Test führte den tatsächlichen Filter aus und reproduzierte vor der Korrektur exakt dieselben zwei Fehler (Exit 1); nach Qualifizierung besteht er mit sechs zusätzlichen Scope-/Feldumfang-Assertions. Aktueller Record-Test 281, insgesamt 630. CI prüft die explizite Referenz auch ohne optionale Engine-DLLs.

Kein Personen-Items-Rebinding, keine fachliche Studioänderung oder gezielte Veröffentlichung, keine Creates/Edits/Conflict/Deletes; P1 bleibt offen. Der neue **30443-Kandidat** korrigiert nur diese Referenz und ist nicht importiert. Vorherige CI am Head `11443eb3135858db4e588abfc05733f0050e522b` war grün, hatte den tatsächlichen Filter jedoch nicht ausgeführt. Screenshots/Befunde und Freigabeverbrauch lokal ignoriert; keine Logs/Personendaten in Git.

## Historische erste DEV-Fortsetzung mit 30443 / 189

Die konkrete Freigabe wurde ausgeführt: alter Studio-187-Editor verlassen, DEV 30442/186 Live und 187 gespeichert sowie beide Metadatenschlüssel je ID 721 lesend bestätigt. Vier Bestandsassets IDs 4–7, Systems leer. Vorabexport Exit 0, 30442-msapp bytegleich mit damaligem Import. 30443 unmanaged ohne Publish All/`--publish-changes` importiert / Exit 0; Postexport / Exit 0, Solution 30443 und msapp bytegleich mit freigegebenem Kandidaten. Maker **188 Live** nach Import.

Studio öffnet, Formelprüfung ausdrücklich „Keine Fehler gefunden“. Personen-Items unterstützt auf temporäre leere `Table()` gesetzt, anschließend exakt die kanonische ForAll/SearchUserV2-Formel im deutschen Studio wiederhergestellt und vollständig aus dem sichtbaren Editor kopiert. Gezieltes Save und Publish ausschließlich dieser App; Maker nach Reload **189 Live**. Checker nach Rebinding: keine Formel-/angezeigten Laufzeitbefunde, 72 Accessibility-, zwölf Leistungs- und zwei Datenquellenbefunde. Keine allgemeine Accessibility- oder Runtime-Freigabe.

Lesender Studio-Export / Exit 0, msapp SHA-256 `c543a40aadad4de4f1a6347e14596c2115971e9e648a5d10a51f3bdf17ce1660`: öffentliche Items sind kanonisch, aber die leere Zwischentabelle hat `DisplayFields`/`SearchFields` auf `[""]`, `IsSearchable` auf false und die generierte `SearchItems`-Regel auf `[]` zurückgesetzt. **Personen-Rebinding nicht erfolgreich abgenommen.** Diese öffentlichen Eigenschaften müssen entsprechend dem bestehenden Source-Vertrag wiederhergestellt werden (`["DisplayName"]`, `["DisplayName"]`, true), danach die generierte V2-Suche vor erneuter gezielter Publikation lesen. Keine privaten Regeln manuell schreiben und keine DEV-Quellenübernahme. Eine leere Zwischentabelle mit unveränderter Personenspalten-Struktur ist als Verfahrensoption erst im Host zu prüfen; kein belegter Fix behauptet.

Während der damaligen Wiederherstellung hatte Studio unerwartet neu geladen und meldete schreibgeschützt, da das bestehende Konto andernorts bereits Bearbeitungssteuerung hat. Keine Überschreibung/Übernahme dieser weiteren Sitzung ausgeführt. Klärung mit dem Nutzer angefragt; der verbleibende freigegebene Umfang und alle fachlichen Write-Kontingente bleiben erhalten. Kein neuer lokaler Quell-/Buildkandidat nötig, solange nur die vorhandenen kanonischen Eigenschaften wiederhergestellt werden.

Ein direkt neu geöffneter Player zeigte zunächst den bisherigen Ablauf. Erst Maker-Wiedergabe und der angebotene Aktualisieren-Versionswechsel zeigten P1. Begrenzte lesende Ergebnisse: Asset-Titelanfang und IDs 4–7 sichtbar; genaue ID 5 liefert nur denselben Datensatz; ungültige ID zeigt die Fehlermeldung und nach abgeschlossener Abfrage keine Datensätze; bestätigte Titelsuche ohne Treffer zeigt den Leerhinweis. DelayOutput/Connector-Zwischenstände unmittelbar nach Eingabe sind keine Endergebnisse. ID 5 öffnet mit Titel Asset, „Keine Änderungen“ und gesperrtem Save; ohne Save abgebrochen. Systems erwartungsgemäß leer; Contact hat kein Neu/keine Liste und den Ausbauhinweis. Keine vollständige Hydrierung aller 17/16 Werte aus dieser Sichtprüfung ableiten.

Ein nur lokaler neuer Asset-Entwurf, nie gespeichert, wurde für den Verwerfen-Dialog benutzt: gültiger Titel markiert Änderung und aktiviert Save; Navigation öffnet Modal, sperrt Hintergrund und fokussiert Weiterbearbeiten. Tastatur-Weiterbearbeiten fokussiert Abbrechen; Abbrechen/Verwerfen per Tastatur schließt den Entwurf und fokussiert Neu. **Kein Create, Edit, Konflikt-Save oder Delete ausgeführt.** Save-Busy, tatsächlicher Personen-Round-Trip, große reale Delegation, Rollen und Connector-/atomare ETag-Konflikte bleiben offen. Screenshots/AX-/Export-/Freigabebelege ausschließlich lokal ignoriert.

Die abschließende SharePoint-Quellenkontrolle fordert erneut Anmeldung. Das bereits freigegebene Servicekonto wurde aus der vorhandenen Kontoliste ausgewählt; danach Kennwortanforderung, keine Zugangsdaten eingegeben. Deshalb kein erneuter finaler Quellen-/Versionsvergleich behauptet. Letzter verifizierter Quellenbestand dieser Fortsetzung bleibt der Vorabstand IDs 4–7/Systems leer; keine fachlichen Writes zur Bereinigung vorhanden. Vor den noch ausstehenden Writes Anmeldung und Quellen-Vorstand erneut prüfen.

## Ausgeführter begrenzter 30443-Testumfang

**Ausführungsstand:** alle nachstehenden fachlichen Versuchskontingente verbraucht; System-Edit fehlgeschlagen, kein Retry. Ergebnisse und genau ein Folgepaket unten.

Die erteilte konkrete Freigabe galt ausschließlich für **30443** und dieselbe DEV-Umgebung; sie wurde für den unveränderten Restumfang nicht erneut angefordert. Die bereits korrekt gespeicherten zwei Metadatenzeilen wurden nicht erneut geschrieben. Ausgeführt wurde folgender begrenzter Testplan:

1. Aktuellen Vorzustand lesen: DEV 30443/189 Live und weitere Studio-Bearbeitungssitzung, beide bestätigten Metadatenschlüssel, fachliche Bestands-IDs und nur nötige redigierte Quellenwerte. Schreibsperre klären und bestehende SharePoint-Anmeldung wiederherstellen, bevor die jeweilige abhängige Arbeit fortgesetzt wird; bei fremden Änderungen erst Kandidatenvergleich. Keine weiteren Metadaten-Writes.
2. 30443 ist bereits importiert und postgeprüft; **kein erneuter Import** nötig. Die vorhandenen kanonischen Personen-Anzeige-/Suchfelder wiederherstellen, kanonische Items erhalten, Checker und lesenden Export der generierten V2-Suchregel prüfen; dann ausschließlich diese App gezielt speichern/veröffentlichen und aktuellen Player laden. Notwendige neue fachliche Formelreparaturen zuerst als neuen prüfbaren lokalen Kandidaten bauen; keine stillen fachlichen Studioänderungen.
3. Lesende Tests: beide Listen, Titelanfang/ID, kein Treffer/ungültige ID, Navigation/Seitenführung, unsupported Provider, vorhandenen Datensatz ohne Save öffnen/abbrechen, Tastatur/Fokus/Dirty-/Busy-Sperren. Studio-Delegationswarnungen und tatsächliche Connector-Ausführung prüfen; große Datensatzmengen nur lesen, keine Massentestdaten erzeugen. Falls echte >2.000-Evidenz fehlt, ausdrücklich als offen festhalten.
4. **Genau ein synthetisches Asset und ein synthetisches System über die App neu anlegen** (zwei Creates). Eindeutige Titel `P1-SMOKE-<UTC>-ASSET` / `P1-SMOKE-<UTC>-SYSTEM`, zugelassenes Testkonto, repräsentative gültige Choices sowie leere optionale Werte; System bei Bedarf an das synthetische Asset koppeln. IDs und tatsächlich gespeicherte Quellenwerte erfassen.
5. Jeden Testdatensatz über Liste/ID erneut öffnen. Default-/Dirty-Zustand prüfen. **Je einmal ausschließlich den Titel ändern und speichern** (zwei Edits), erneut öffnen und Quelle vergleichen. Alle anderen 17/16 gemappten Werte müssen erhalten bleiben, ebenso nicht gemappte Quellenwerte. Benutzerwerte nicht anhand der UI allein als korrekt ausgeben.
6. **Ein kontrollierter zusätzlicher Quellen-Edit am synthetischen Asset** für den Konflikttest: in der App vorab laden, dann den Titel dieses ID-/Marker-bestätigten Testassets über einen zweiten Client ändern. App-Title abweichend bearbeiten und Save versuchen. Der Versuch muss vor Patch blockieren bzw. als echter Connector-Konflikt enden; Titel/Modified/Version nachlesen, keine automatische Wiederholung. Dies belegt die beobachtete Reihenfolge, keine ungetestete atomare ETag-Garantie.
7. Ausschließlich diese zwei bestätigten synthetischen IDs reversibel in den normalen Papierkorb entfernen, System zuerst wegen Lookup. ID-Filter, exakte Papierkorbtitel/Herkunft und alle vorab erfassten Bestandsdatensätze prüfen. Kein Reset, keine Bulk-Löschung, keine produktiven Inhalte anfassen.

Der ausgeführte Plan erlaubte maximal **zwei Creates, zwei normale App-Edits, ein zusätzlicher Konflikt-Quellen-Edit, ein erwartbar blockierter App-Save-Versuch und zwei reversible Testdatensatzlöschungen**, neben der 30443-Kandidatenübernahme. Die zwei Metadaten-Writes aus der vorherigen Freigabe sind bereits verbraucht und bleiben erhalten. Bei unklarem Save-Ausgang zuerst Quellenprüfung, kein erneuter Save. Scheitert ein Round-Trip, bleibt P1 offen; weitere Tenant-Saves benötigen neuen konkreten Scope/Freigabe. Import/Publikation macht P1 nicht automatisch produktionsreif.

## Beobachtete Fortsetzung 30443 / 191 und Abschluss des Testkontingents

Studio wieder schreibbar, keine Sitzungsübernahme/Override nötig. Mit bestehenden öffentlichen Eigenschaften `DisplayFields=["DisplayName"]`, `SearchFields=["DisplayName"]`, `IsSearchable=true` repariert; kanonische Items unverändert. Save 190, Formelchecker ausdrücklich „Keine Fehler gefunden“. Studio-Download des gespeicherten Drafts enthält gegenüber 189 genau vier Regeländerungen am Personencontrol: diese drei öffentlichen Werte plus automatisch generierte SearchItems mit V2-Suche/DisplayName. Keine private Regel manuell geschrieben. Ein Solution-Export vor Publikation enthielt noch 189 und wurde deshalb nicht als Draftnachweis benutzt. Nach gezieltem Publish zeigt Maker **191 Live**; lesender Solution-Export Exit 0, alle drei Controls-JSONs bytegleich zum geprüften Draft. Draft-msapp SHA-256 `3df40c093de42119d1dc44edeb96eba0a80a18f5070339630afe01b29723b8fa`, publiziertes msapp `45edab31fbea72677b1a9f7ea01e1c865cfd7c439e5303ddda6cee36bccb57c6`. Keine DEV→Git-Übernahme; keine neue Paketversion.

Bestehende SharePoint-Anmeldung wieder nutzbar, keine Zugangsdaten eingegeben oder Rechte erweitert. Beide Title-Metadaten je ID 721 erneut nur gelesen. Maker-Wiedergabe im frischen Player gestartet, angebotenen Versionswechsel angenommen. Nur synthetischer Titelmarker und zuvor zugelassenes Testkonto verwendet.

| Prüfung | Tatsächlich beobachtet | Grenze |
|---|---|---|
| Asset Create / ID 10 | Quelle: Titel, Owner, Kritikalität Mittel, aktiv; nach Öffnen keine Änderungen/Save gesperrt | Optionale Werte leer; kein vollständiger nativer Claims-/Hidden-Field-Nachweis |
| Asset Title Edit | Ein Save; neuer Titel in Quelle und Player, Owner/Mittel erhalten; Version 2.0 | Vergleich von 32 sichtbaren Quellfeldbeschreibungen: ausschließlich Title geändert; Beschreibung im Grid leer |
| System Create / ID 2 | Quelle: Titel, Owner, GovernanceStatus Entwurf, Criticality Hoch, aktiv; sauberes Wiederöffnen | Optionale Lookup-Auswahl nicht gesetzt; Quelle zeigt `0;#`, nicht als native Null behauptet |
| System Title Edit | Genau ein Save-Versuch, Editor weiter dirty; Quelle alter Titel, nur Version 1.0 | Fehlgeschlagen, keine zweite Version, kein Retry; genaue Connector-Ursache nicht belegt |
| Lookup-Auswahl | Titelsuche liefert kein Ziel; publizierte interne SearchItems = `Search(ComboBoxSample, Self.SearchText, Value1)` | Öffentliche Items/DisplayFields/SearchFields vorhanden; kein unterstütztes Lookup-Rebinding ausgeführt |
| Asset-Konflikt | App lädt Version 2.0, zweiter Client ändert nur Title zu Version 3.0, ein App-Save wird mit „Der Datensatz wurde inzwischen geändert“ gesperrt; Quelltitel/Version 3.0 unverändert | Sequenzieller Modified-Konflikt bestanden; atomarer ETag-/Connector-Race weiterhin ungetestet |
| Busy / Bereinigung | Während Saves Navigation/Inputs/Abbruch gesperrt; Entwürfe verworfen; System 2 zuerst, Asset 10 danach im normalen Papierkorb | IDs/Marker/Herkunftslisten belegt; Bestand Assets 4–7, Systems leer; kein Purge/Reset |

**Verbrauch:** historische Metadaten 2/2 (diese Fortsetzung 0), Creates 2/2 erfolgreich, normale App-Edit-Versuche 2/2 (Asset bestätigt, System ohne Quelländerung), Konflikt-Quellen-Edit 1/1, erwartbar blockierter App-Save 1/1, reversible Deletes 2/2. Keine weiteren Writes aus diesem Kontingent. Beide synthetischen Datensätze sind bereinigt.

Lokale Diagnose ausschließlich mit synthetischem Fixture und den unveränderten tatsächlichen Projektformeln: `LinkedAsset={Id:0, Value:""}` wird durch Load, Hydrierung und Payload als Id 0 weitergereicht, `IsBlank(Id)` ist false. Diagnose Exit 0 mit zwei zusätzlichen Beobachtungsassertions neben den bestehenden 281 Recordtests; kein neuer kanonischer Test/Kandidat und kein Connector-Aufruf. Die Quellanzeige `0;#` allein beweist nicht, dass dies die tatsächliche Ursache des fehlgeschlagenen Live-Saves ist. Beides muss im Reparaturpaket geklärt werden; kein Ursachenbeweis behauptet.

Unveränderte 30443-Offlinebasis: alle 18 verfügbaren Kandidaten-Gates/Build/Round-Trip Exit 0, 630 Assertions/53 Formeln. Dokumentationsabschluss prüft Audit und Diff; tatsächlicher CI-Head/Exit-Codes im Draft/Handoff. Pester/PAC canvas validate fehlen weiterhin; Rollen, reale große Delegation, vollständige native Werte und atomare ETag-Garantie ungetestet. Historische Checkerzahlen 189 werden nicht als aktueller 191-Accessibility-Check ausgegeben. Screenshots, AX, Exporte, Downloadkopie und Diagnose ausschließlich ignoriert.

## Lokaler Reparaturkandidat 30444

Die unveränderte 30443-Load-Projektion reicht den synthetischen `LinkedAsset={Id:0,Value:""}` als gültig wirkende ID weiter. Der neue tatsächliche Load-Test scheitert daran vor Reparatur / Exit 1. 30444 normalisiert Lookup-ID und Text beim Load, Default und Save: nur positive IDs sind Ziele, 0/negative/Blank werden leere Referenzen. Pflichtreferenz prüft eine positive ID, Cache-Ergänzung und neue Items übernehmen keine ungültigen IDs. Alle 16 System-/17 Asset-Save-Felder und Personen-/Choice-/Capability-Verträge bleiben erhalten. Ein nicht veränderter positiver Lookup bleibt beim Titel-Edit erhalten.

95 neue Assertions verwenden tatsächliche Projektions-, Hydrierungs-, Default-, Event- und Payloadformeln für vier Quellenfälle: Blank, 0, negative ID und positive ID. Sie prüfen sauberes Laden, Pflichtvalidierung, keine Phantomauswahl/Dirty-Events, Titel-Edit und die übrigen 14 Systemfelder sowie zieltyp-/aktiv-/ID-begrenzte Items, bestehende Mehrfachauswahl und stale ID 0 im Payload. Der Interpreter lehnte die alte Tabellenpunktprojektion im Mehrfachdefault ab; dieselbe Auswahl wird jetzt mit `ShowColumns(Filter(...),LookupId)` projiziert und durch tatsächliche Default-Auswertung geprüft. Kein fachlicher Mehrfach-Refactor. Die öffentliche Lookup-Suche verlangt explizit `DisplayFields=["DisplayText"]`, `SearchFields=["DisplayText","SecondaryText"]`, `IsSearchable=true`; CI-Quellgate verbietet eine private SearchItems-Property.

**725 tatsächliche Offline-Assertions / Exit 0** (137 Capability, 212 Choice, 376 Record), 53 Formeln, vier YAML-Regressionstests. PAC 2.9.3 Build 30444 / Exit 0, SourceCode-Pack/-Unpack alle vier YAMLs identisch, Artefakt 4/4; alle 18 verfügbaren Kandidaten-Gates Exit 0. Dokumentationsabschluss: Audit/Diff Exit 0; CI am tatsächlichen PR-Head im Draft/Handoff belegen. Pester/PAC canvas validate fehlen. Im lokalen Reparaturpaket noch keine Live-Reparatur oder neuer Tenant-Save ausgeführt; die danach begonnene freigegebene DEV-Abnahme steht unten. Der vermutete Zusammenhang zwischen ID 0 und dem 191-Live-Savefehler muss weiterhin im DEV-Round-Trip belegt werden.

- Solution **1.0.0.30444**, Canvas `1.0.0-alpha.4.1.0`, Provisioning `6.2.5`, Versionsreihen getrennt.
- ZIP `GovernancePortal_1.0.0.30444_1.0.0-alpha.4.1.0.zip`, SHA-256 `afb99331fc7818a105933bf6de54ce28a361b9c2abba6d9da32d5644fb1406a0`.
- Kanonisches gepacktes msapp SHA-256 `99d1ae433d31c70886e116b65af3e67ddd4edd80921feaede92778031c5bc579`.
- Beim lokalen Build noch nicht importiert; nachfolgend ausdrücklich freigegebener Import und aktueller Maker-/Studio-Stand siehe unten. Paketidentität unverändert, keine DEV→Git-Übernahme.

**Host-Grenze:** Das neue SourceCode-Paket enthält die reparierte kanonische YAML, seine historischen Controls-JSONs aber weiterhin alte öffentliche/generated Bindungen einschließlich ComboBoxSample bei Person/Lookup. Pack-/YAML-Round-Trip ist deshalb kein Nachweis ausgeführter Such-/Payloadregeln. Nach Import muss Studio die Quellen verarbeiten und die beiden ComboBox-Bindungen über öffentliche Eigenschaften mit erhaltener Spaltenstruktur regenerieren. Keine private Regel im Paket oder im Tenant manuell schreiben. Ein gespeicherter Draft ist durch Studio-Download zu prüfen; Solution-Export vor Publish kann noch die alte publizierte Revision liefern.

## Erste 30444-DEV-Abnahme und damaliger Studio-Blocker

Die konkrete Freigabe wurde begonnen. Vorzustand 30443/191 Live, Assets IDs 4–7/Systems leer und beide Title-Metadaten je ID 721 nur gelesen. Vorabexport / Exit 0 enthält bytegleich den zuvor geprüften 191-Stand. Bestehende Anmeldung über das zugelassene Konto erneuert, keine Zugangsdaten eingegeben oder Rechte erweitert.

**Genau ein Kandidatenimport 30444**, unmanaged ohne Publish All/`--publish-changes` und ohne Retry. PAC beendet sich nach 30 Minuten mit Timeout / Exit 1; dieser Exit-Code bleibt erhalten. Der native Solution-Verlauf bestätigt den erfolgreichen 30444-Import. Ein erster Postexport scheitert an DNS/Anmeldung; der lesende Export wird wiederholt und besteht / Exit 0: Solution 30444 und msapp SHA-256 `99d1ae433d31c70886e116b65af3e67ddd4edd80921feaede92778031c5bc579`, bytegleich mit dem freigegebenen Kandidaten. Kein neuer Import aus dem Transportfehler abgeleitet.

Solution-App-Zuordnung und App-ID stimmen. Maker zeigt **192 Live** (importbedingter Stand) und **193 gespeichert, nicht veröffentlicht**. Studio öffnet zunächst im Bearbeitungsmodus. Nur die Strukturansicht-Suche nach `cmbEditorPerson` wurde bedient, keine Formel oder öffentliche Property geändert. Auswahl, App-Checker-Aufruf und Tastatursteuerung scheitern über die verfügbare Browsersteuerung; frische DOM-/AX-/Screenshotprüfung, Neubindung, ein Reload und frischer Tab lösen das Problem nicht. Danach meldet Studio zusätzlich eine bestehende Bearbeitungssitzung: Banner nennt die andernorts vorhandene Steuerung desselben Kontos, Dialog eine andere bearbeitende Person. **Keine Sitzungsüberschreibung/Übernahme.** Native Maker-Details bleiben bedienbar; der Fehler ist damit im Studio beobachtet, seine technische Ursache nicht belegt.

Studio hat beim Aufruf **193 automatisch gespeichert**; kein manuelles Save und keine gezielte Veröffentlichung ausgeführt. Draft 193, Checker und tatsächlich kompilierte Lookup-/Payload-/Personensuchregeln konnten noch nicht exportgeprüft werden. Keine Aussage, dass die reparierte SourceCode-YAML bereits im Player korrekt ausgeführt wird. Kein Rebinding, Create, Edit, Konflikt-Write oder Delete. Abschließende Listenansichten zeigen Assets IDs 4–7 und Systems leer; keine neuen Testdatensätze zu bereinigen.

**Verbrauch der 30444-Freigabe:** Import **1/1**; Personen-/Lookup-Rebinding jeweils **0/1**; manuelles Studio-Save **0/1**, gezieltes App-Publish **0/1**; Creates **0/2**, System-Edit-Versuche **0/5**, reversible Deletes **0/2**. Metadaten-/Bestands-/Konflikt-Writes und Save-Retries jeweils **0**. Automatisches Studio-Save separat als Draft 193 dokumentiert. Der unveränderte Restumfang bleibt ausdrücklich autorisiert; dieselbe Freigabe nicht erneut anfordern.

Kanonische Quellen, Solution-Version, geprüftes lokales msapp und Build bleiben unverändert. Kandidaten-Head `9d7cce25a00513579253469f7cf80287ea500817` hat drei erfolgreiche CI-Checks; 18 lokale Gates/725 Assertions gelten weiter für diesen unveränderten Code. Nur Zustandsdokumentation aktualisiert, Abschluss-Audit/Diff und neue Head-CI im Handoff. Screenshots/AX, Exportkopien, Logs und Freigabeverbrauch ausschließlich lokal ignoriert. Pester/PAC canvas validate und alle offenen Rollen-/Delegations-/ETag-Gates unverändert.

## 30444-Fortsetzung: Host-Suche und 193 Live, Titel-Gate offen

Ein Reload löst die Sitzungssperre ohne Überschreibung. Iframe-Klicks bleiben teilweise gestört; direkter Browser-Tastaturinput mit sichtbarer Fokusprüfung erreicht Controls, Befehle und Dialoge. Der lesende PAC-Canvas-Download / Exit 0 liefert bytegleich die Import-/Live-192-Datei, keinen Draftnachweis. Der unterstützte Studio-Download des gespeicherten Drafts (SHA-256 `77b20318d09fd94c9a474967abbdf2fab3cf7e2ff9e669bce601358a2099e3ab`) zeigt kanonische öffentliche Person-/Lookup-Formeln und reparierte Load-/Payload-/Default-Logik, aber beide privaten Suchregeln noch mit `ComboBoxSample`.

Je **ein öffentlicher Rebinding-Durchlauf**: strukturgleiche leere Items-Tabelle, exakte kanonische Items zurück, Suchaktivierung über die öffentliche IsSearchable-Property kurz aus/ein. DisplayFields/SearchFields bleiben kanonisch. Keine private Suchregel authoriert. Native App-Prüfung: Formeln ausdrücklich „Keine Fehler gefunden“, keine angezeigten Laufzeitbefunde, 72 Accessibility-/zwölf Leistungswarnungen, zwei ungenutzte Datenquellen (TextResources/StatusPresentation). Kein allgemeiner Accessibility-/Runtime-Nachweis.

Ein manueller Save-Versuch bestätigt „Alle Änderungen wurden gespeichert“; Draft 193 wird innerhalb derselben Revision aktualisiert. Studio-Download SHA-256 `11bb45b012d4306892249dd1731a348ce83d715472e5ab999f9c23d43656786e`: beide generierten Suchregeln verwenden die echten Quellen. Gegenüber dem Vor-Draft ändern sich ausschließlich beide generierten SearchItems und eine Änderung ausschließlich der Leerzeichen in Lookup-SearchFields. Load/Payload/Default/Items stimmen nach Auflösung der nativen SharePoint-Anzeigenamen mit den kanonischen Formeln überein; Stringliterale unverändert.

**Genau eine gezielte App-Veröffentlichung**, Maker nach Reload **193 Live** (3.10.2026, 20:49:10). Lesender Solution-Export / Exit 0, publiziertes msapp SHA-256 `cac85b398a345dde2a94a6b3a715544c188c09175f95eb3dae4b06a687ba10dd`: ZIP-Datei nicht bytegleich mit Draftkopie, sämtliche kompilierten Control-Regeln jedoch exakt gleich. Keine neue Build-/Quellversion oder DEV→Git-Übernahme. Frischer Player startet, bestehende Anmeldung fortgesetzt, anschließend sichtbaren Hinweis auf alte Version über „Aktualisieren“ abgearbeitet; neuer Runtime-Stand ohne Versionswarnung bereit.

Vor abhängigen Writes erneut gelesen: Assets IDs 4–7, Systems leer, vorhandene System-Title-/Edit-Title-Metadaten je ID 721. Im neuen Asset-Formular liefert die begrenzte Personensuche das zugelassene Testkonto; tatsächliche Auswahl und Kritikalität Mittel werden angezeigt. **Der sichtbar eingegebene Titel bleibt als fehlendes Pflichtfeld markiert, Speichern gesperrt**, auch nach nativer Tastatur-/Mausbedienung und Fokuswechsel. Kein Save ausgelöst. Die manuelle Gegenprobe wurde angefordert; technische Ursache App-Ereignis versus Eingabesteuerung offen. Kein System-Test begonnen und kein Testdatensatz zu bereinigen. Der ungespeicherte Asset-Entwurf bleibt ausschließlich zur Gegenprobe im Player.

**Verbrauch zum vorherigen Host-Zwischenstand:** Import 1/1, Personen-/Lookup-Rebinding je 1/1, manueller Studio-Save 1/1, gezieltes Publish 1/1; Creates **0/2**, System-Edit-Versuche **0/5**, reversible Deletes **0/2**. Metadaten-/Bestands-/Konflikt-Writes und Save-Retries 0. Der unverändert freigegebene fachliche Rest bleibt autorisiert. Native Such-/Hostabnahme ist belegt; daraus folgt keine fachliche P1- oder Produktivabnahme. Unveränderter Codekandidat behält 18 erfolgreiche Gates/725 Assertions; diese beweisen keine nativen Textänderungsereignisse. Nur sieben Statusdokumente aktualisiert, Abschluss-Audit/Diff und neue Head-CI separat. Exporte, Such-/Formularbelege, Freigabeverbrauch und Screenshots bleiben lokal ignoriert.

## 30444-Fachtest: Creates bestanden, erster System-Edit nicht persistiert

Die bisherige Eingabesperre betrifft die alte getrennte Player-Sitzung. In der aktuell sichtbaren, frisch gestarteten 193-Sitzung wird der Titel nach zeichenweiser Eingabe/Fokuswechsel korrekt übernommen und Save aktiv. Publizierte Textfeld- und Revalidierungsregeln entsprechen den kanonischen Formeln; kein Code-Fix daraus abgeleitet. Eine allgemeine Ursache der alten Sitzung ist nicht bewiesen; die manuelle Gegenprobe ist für diese Fortsetzung nicht mehr erforderlich.

Vor den Writes Maker 193 Live und Quellenbestand Assets IDs 4–7/Systems leer erneut gelesen. Jede fachliche Aktion vor dem einzigen UI-Aufruf im lokalen Freigabejournal reserviert. Asset nach Quellen-ID 11 bestätigt; Player danach neu gestartet, ID-Suche und unverändertes Wiederöffnen mit Testkonto/Mittel belegt. System ID 3 mit Testkonto/Entwurf/Hoch und leerem LinkedAsset bestätigt, Quelle Version 1.0. App zeigt kein Ziel; SharePoint-Feldbeschreibung `0;#` ist ein semantisch leerer Sentinel, kein Raw-Null-Nachweis.

| Schritt | Ergebnis und Evidenz | Grenze |
| --- | --- | --- |
| Asset-Create | Ein Save, ID 11/Marker in Quelle und frischem Player; Owner/Mittel/Aktiv erhalten | Kein Asset-Edit unter 30444 |
| System-Create | Ein Save, ID 3/Marker, Version 1.0; Owner/Entwurf/Hoch/Aktiv und leerer Lookup beim Wiederöffnen | Sichtbare Quellbeschreibungen; native Claims/Hidden-Werte nicht vollständig ausgelesen |
| System-Titel-Edit bei leerem Lookup | Ein UI-Saveversuch; Player bleibt dirty, Quelle alter Titel und nur Version 1.0. Alle sichtbaren Quellfeldbeschreibungen exakt gleich dem Create-Vorstand | Kein belegter Connector-Fehler und kein Nachweis, dass der Speicherhandler startete. Kein Retry; vier abhängige Edits nicht ausgeführt |
| Cleanup | ID-/Marker-bestätigtes System zuerst, dann Asset in Papierkorb; Listenherkunft und ursprünglicher Bestand Assets 4–7/Systems leer belegt | Zwei reversible Löschungen; kein Purge, keine historischen Papierkorbeinträge verändert |

**Verbrauch zum Abschluss:** Import 1/1, Rebindings je 1/1, Studio-Save 1/1, Publish 1/1; Creates **2/2**, System-Edit-Versuche **1/5**, reversible Deletes **2/2**. Metadaten-/Bestands-/Konflikt-Writes und Save-Retries **0**. Das Stop-Kriterium beendet die abhängigen Saves; die vier nicht ausgeführten Edits sind kein zusätzlicher Diagnose-Scope. Kein neuer Import/Publish oder DEV→Git, Quell-/Buildkandidat 30444 unverändert. P1 bleibt fachlich offen.

**Vorbereitungsstand vor der jetzt ausgeführten Diagnose:** Live-Monitor für die veröffentlichte App war verbunden; reine Start-/Formular-/Suchereignisse sind aufgezeichnet. Zum Handoff zeigt er Getrennt; vor jedem neuen Save Verbindung erneuern und Aufnahme tatsächlich prüfen. Nach regulärem Einstieg im sichtbaren Player ist ein ungespeicherter Entwurf `P1-30444-DIAG-20261003-System` mit gültigem Titel/Testkonto/Entwurf/Hoch vorbereitet. Monitor belegt native Textänderung und erfolgreichen `txtEditorText.OnChange`-LookUp. Im neuen Diagnoseumfang wurden noch keine fachlichen Saves ausgeführt. Monitor-Sitzungen/Exporte und vollständige Belege bleiben lokal ignoriert; keine Tokens/Personendaten/Logs committen.

Der anschließend ausdrücklich freigegebene Testscope war auf unverändert 30444/193 und **ein synthetisches System-Create, einen Titel-Edit mit leerem LinkedAsset und ein reversibles System-Cleanup** begrenzt. Monitor vor beiden Saves verbunden, je Schritt ein UI-Aufruf mit reserviertem Verbrauch. Asset-/Metadaten-/Bestands-/Konflikt-Writes, Save-Retries und App-Import/Rebinding/Save/Publish waren ausgeschlossen. Ergebnis und Verbrauch folgen im Diagnoseabschluss.

## 30444-Monitor-Diagnose: Description-Schreibschutz belegt

Die konkret freigegebene Monitor-Diagnose auf unverändert 30444/193 ist abgeschlossen: genau ein System-Create, ein Titel-Edit und ein reversibles Cleanup, je 1/1, kein Retry. Neuanlage ID 4/Version 1.0 und unverändertes Wiederöffnen mit Testkonto/Entwurf/Hoch/Aktiv und leerem LinkedAsset bestehen. Native Return-Aktivierung nach bestätigtem Save-Fokus startet beide Speicherereignisse. Create: Monitor `patchCreateRow` und `createRow`/HTTP 201 Created. Edit: `lblEditorSave.OnSelect` meldet bei `Patch` **„[Systems] Spalte Description ist schreibgeschützt und kann nicht geändert werden“**; kein `updateRow` im aufgezeichneten Monitor, Quelle alter Titel/Version 1.0 und alle sichtbaren Felder unverändert. Lokales 30444-msapp und publizierter 193-Export deklarieren `Systems.Description` als `x-ms-permission: read-only`; der kanonische System-Save enthält das Feld auch beim reinen Titel-Edit, Architekturtyp ist Note. Ursprung des Schreibschutzes in nativer Liste/Connector-Metadaten noch offen. Testsystem ID 4 mit Marker/Herkunft Systems im Papierkorb, Alle Elemente/Systems leer, vier Bestandsassets sichtbar; keine Asset-Writes. Fehler erscheint nach Verwerfen auf der Datensatzliste, während der Editor vorher dirty blieb. Monitor zum Handoff Getrennt; 1.605 aufgezeichnete Ereignisse. P1 bleibt offen.

Die beiden Patch-Fehlereinträge (1.576/1.583) gehören zum einzigen reservierten Edit-Aufruf; kein zweiter Save und kein Retry. Sie sind keine HTTP-Fehlerantwort: der Monitor enthält für diesen Edit keinen updateRow-Aufruf und keine zugehörige HTTP-Antwort. Der Create dagegen hat einen echten Network/createRow/201-Nachweis (881), neben dem DataOperation-Ereignis (880). Aus der erfolgreichen Tastaturaktivierung folgt keine allgemeine Ursache des vorherigen semantischen UI-Clicks. Native Listenrechte wurden in dieser Diagnose nicht geändert oder abschließend ausgelesen; read-only ist in beiden gespeicherten App-Artefakten und im Runtimefehler belegt.

Die 725 bestehenden Offline-Assertions und grüne CI ersetzen diese Connector-Permission-Prüfung nicht. Eine zusätzliche Regression muss den tatsächlichen Schreibvertrag und die Fehleranzeige prüfen. Das fachliche Description-Feld darf nicht entfernt werden, um den Titeltest grün zu machen. Code-/Build-/Versionskandidat bleibt unverändert; Diagnose-/Freigabedaten und Screenshots lokal ignoriert.

## Genau ein primäres nächstes Arbeitspaket

**P1 · lokalen Schreibvertrag für Systems.Description reparieren**, Modellklasse `deep-reasoning`: Architektur, kanonischen System-Save und die Connector-Feldmetadaten gegen den belegten Schreibschutzfehler abgleichen. Minimalen lokalen Reparaturkandidaten mit Regression für diesen Metadatenvertrag und sichtbare Speicherfehler erstellen; Beschreibung, native Record-/Personen-/Choice-/Lookup-Verträge und Konfliktschutz erhalten. Das fachliche Feld nicht entfernen und Tenantrechte nicht ungeprüft ändern. Der Diagnoseumfang ist verbraucht und bereinigt; keine weiteren Live-Writes. Build/Artefaktidentität und vollständige verfügbare Projekt-Gates prüfen, danach einen konkreten DEV-Übernahme-/Abnahmescope vorbereiten. Import, Rebinding, Studio-Save, Publish, Metadatenwrites und DEV→Git bleiben separat zu beauftragen. P2 erst nach P1-Abnahme.

1. Belegte Description-Abweichung zwischen Architektur, gepackten/publizierten Connector-Metadaten und kanonischem System-Save gezielt klären; keine pauschale Feld-/Rechteänderung.
2. Kleinste kohärente lokale Korrektur mit Regression für den tatsächlichen Metadaten-/Save-Vertrag erstellen. Originalen Connector-Record, Personenobjekte, Choices, leere/positive Lookups und Modified-/Conflict-Prüfung erhalten; Fehler im Editor nachvollziehbar anzeigen.
3. Tatsächlichen Kandidaten inklusive Build-/Artefaktidentität mit allen verfügbaren Gates prüfen, dokumentieren und zur konkreten DEV-Übernahme vorbereiten. Diagnoseverbrauch bleibt Create/Edit/Delete je 1/1; ein späterer Live-Retest ist ein eigener konkreter Scope.

Positive Lookup-Auswahl, Titel-Erhalt bei positivem Lookup und Leeren bleiben spätere P1-Abnahmeschritte. P2 nach vollständiger P1-Abnahme; Rollen, große Delegation, native Claims/Hidden-Werte und atomarer ETag bleiben eigene offene Gates.

## Technische Quellen und offene Host-Gates

Die direkte SharePoint-Abfrage verwendet Titelanfang und ID-Gleichheit entsprechend der [Microsoft-Delegationsmatrix](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/connections/connection-sharepoint-online). ID-Bereichsoperatoren werden vermieden. [Galerie-Navigation und AllItems](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/control-gallery) beziehen sich auf geladenen Umfang; P1 zeigt keine Gesamtzahl. Die [Patch-Dokumentation](https://learn.microsoft.com/en-us/power-platform/power-fx/reference/function-patch) beschreibt den nativen Basisrecord; [Errors/Conflict](https://learn.microsoft.com/en-us/power-platform/power-fx/reference/function-errors) hängt von Datenquellenunterstützung ab. Daraus folgt das noch offene Studio-/Delegations-/Connector-Gate, kein vorweggenommener Live-Nachweis.
