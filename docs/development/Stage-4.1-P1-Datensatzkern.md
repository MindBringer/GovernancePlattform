# P1 – Datensatzkern und DEV-Abnahme

Stand: 2026-10-02. **DEV 30441/Canvas 185 mit Studio-Blocker; Reparatur 30442 lokal bereit, P1 nicht abgenommen.** Primäres Folgepaket ist ausschließlich die hier beschriebene P1-DEV-Fortsetzung mit dem neuen Kandidaten. Modellklasse `deep-reasoning` wegen Canvas-/Provider-/SharePoint-Kopplung und Datenintegrität.

## Kandidat und Grenzen

- Branch `codex/stage41-p1`, Basis P0 `5caee00823032b4306f0bdaa900ca9817a53610e`, [Draft-PR #17](https://github.com/MindBringer/GovernancePlattform/pull/17) auf `codex/stage41-p0`.
- Lokaler Reparaturkandidat: Solution **1.0.0.30442**, Canvas `1.0.0-alpha.4.1.0`, Provisioning `6.2.5`; Versionsreihen getrennt. Noch nicht importiert.
- Letzte erfolgreiche fachliche Abnahme: **P0 30440 / Canvas 184**. Aktueller DEV-Import: **30441 / Canvas 185 Live laut Maker**, Studio-Öffnen gescheitert. Die konkrete Freigabe für 30441 deckte zwei Metadatenzeilen und Import ab; fachliche Save-Kontingente sind ungenutzt. Sie autorisiert keinen automatischen Import des neuen 30442-Kandidaten. Frühere P0-Save-Freigaben bleiben verbraucht.
- Kanonische Bearbeitungsquelle bleibt `powerplatform/canvas/GovernancePortal/`; SourceCode-Round-Trip nur in ignoriertem Staging. Keine DEV→Git-Übernahme.
- P1 erhält die vorhandenen nativen Save-Verträge. Kein zusätzliches Asset-Fachmapping, neuer Provider, Evidence-/Reviewprozess oder Produktivrollout. Capabilities benennen ausführbare Pfade; Live-/Rollenabnahme bleibt separat.

## Verhalten

Asset und System zeigen native Listen mit Titelanfangssuche oder genauer positiver ID. Ungültige ID liefert einen sichtbaren Fehler und kein ungewollt ungefiltertes Ergebnis. Galeriepfeile und Bildlaufleiste laden weitere Datensätze; kein vorab begrenztes `ClearCollect`, keine ID-Bereichsfilter, keine vermeintliche Gesamtzahl aus `AllItems`.

Öffnen lädt nach `Refresh` den nativen Record mittels ID-Gleichheit. Geladene Werte werden in denselben Editor wie die Neuanlage übernommen. Fehlender/unzugänglicher Datensatz bleibt in der Liste mit Fehlermeldung. Fehlende/falsch typisierte Metadaten und unbekannte gespeicherte Choices sperren Save. Eine unbekannte Choice wird sichtbar als ungültiger Wert erhalten, bis eine gültige Auswahl getroffen wird.

Unveränderte Defaults dürfen keine Felder als geändert markieren. Leere optionale Werte, `0`, `false` und Datum/Uhrzeit bleiben erhalten; unveränderte Personenobjekte behalten originale Claims, Email und Zusatzattribute. Ein bestehender Lookup wird auch außerhalb des bisherigen Lookup-Caches angezeigt. Die begrenzte Suche nach neuen Lookup-Zielen bleibt der bisherige Vertrag und ist kein Nachweis vollständiger Lookup-Auswahl bei großen Listen.

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

## Offline-Gates am Kandidaten

| Gate | Ergebnis / Exit-Code |
|---|---|
| Vollständiger `Build.ps1`, PAC 2.9.3 SourceCode-/Solution-Pack | 0; 30442, kein Import/Publish |
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
| Record-Quell-/Compiler-/Enginevertrag | 0; Asset 17 / System 16 Felder, 275 tatsächliche Assertions, 53 mehrzeilige Formeln geparst |
| Repository-Audit / Diff | 0 / 0 |

**624 tatsächliche Offline-Power-Fx-Assertions.** Die Recordtests werten tatsächliche Projektionen, Hydrierung, Payloads, Guard- und Galerieformeln aus. Voll-/Leerwerte, Datumszeiten, native Personenalias-/Claims-Werte, optionales Leeren, unveränderte Defaults, unbekannte Choices, fehlende Metadaten, falsche Kontrolltypen, Modified-Konflikte und 3.000-Zeilen-Fixtures sind enthalten. Ein lokaler Fixture-Test beweist keine SharePoint-Serverdelegation.

CI enthält Record-Quell-/Compilervertrag, beide Title-Gates und nun den YAML-Parser samt Regression. Optionale Engine-DLL-Tests laufen lokal. Vor der Reparatur waren alle drei CI-Checks am Head `67a18e0049b75f468c826ca26a1e766206911cfd` erfolgreich; dieser grüne Stand erkannte den später belegten Studio-YAML-Fehler nicht. Der Reparaturhead wird nach Push erneut gegen den tatsächlichen PR-Head geprüft; exakter Head/URLs im Draft und ignorierten Handoff. Alle 18 verfügbaren Abschluss-Gates am 30442-Kandidaten Exit 0. Pester nicht installiert; PAC `canvas validate` in 2.9.3 nicht vorhanden. Kein P1-Studio-Checker, Tenant-Round-Trip oder realer Rollen-/ETag-/Delegationsnachweis.

## Kandidaten-Hashes

- `GovernancePortal_1.0.0.30442_1.0.0-alpha.4.1.0.zip`: SHA-256 `558e6e9e63f6cd339b664df68968f5ccd063e50c79972307fac9bf43b771da12`.
- Versioniertes `gp_governanceportal_c93a1_DocumentUri.msapp`: SHA-256 `911f4615521601353e78b13b545dc5071051e9ee703d2293bfea3369305340dc`.

Originaler Workspace mit elf gestagten Dateien und P0-Branch erhalten; keine Framework-Locks/-Runtimeversionen, kein Merge/Release. PR #6 bleibt DO NOT MERGE. Neue Logs, ZIPs, Tenantsettings und personenbezogene Daten bleiben außerhalb Git.

## Beobachteter DEV-Versuch mit 30441

Die Freigabe vom 02.10.2026 wurde begrenzt ausgeführt: Vorzustand 30440/184 und dessen Studio-msapp geprüft; genau `System:Title` und `System:Edit:Title` neu geschrieben und nach Reload mit allen Feldern/Boolean-Werten geprüft (je ID 721 in ihrer Liste). Alle-Elemente-Vorstand: vier Assets, IDs 4–7; keine Systems. Kein allgemeines Provisioning/Seed/Reset.

Import 30441 ohne `--publish-changes` und ohne Publish All Exit 0; Postexport Exit 0, Solution 30441 und msapp bytegleich mit dem freigegebenen Kandidaten. Maker zeigt nach Import **185 Live**. Studio meldet vor Öffnen **PA1001 / YamlInvalidSyntax**, ursprünglich `scrShell.pa.yaml(837,57)`: Doppelpunkt mit Leerzeichen in einem ungeschützten YAML-Formelwert. Beide neuen Asset-/System-Öffnen-Beschriftungen wurden lokal als `|-`-Blockskalare geschrieben; die Power-Fx-Formeln bleiben gleich. Der neue Parser verwirft diesen früheren Fehler vor Pack; vier Regressionstests sichern Fehlererkennung und Formelerhalt.

Kein Studio-Rebinding, Checker, gezieltes Save/Publish oder fachlicher Create/Edit/Conflict/Delete ausgeführt. Ein frischer Player erreicht den Startbildschirm, zeigt jedoch den Hinweis auf eine kommende Version; das belegt keinen aktuellen P1-Runtime-Stand und ersetzt die Studio-Prüfung nicht. Test-/Rollen-/Delegationsgates bleiben offen. Lokale Belege und ungenutzte Write-Kontingente in `artifacts/p1-20261002/DEV-ABNAHME.json`; keine persönlichen Daten/Logs in Git.

## Konkreter Freigabeumfang für die P1-DEV-Fortsetzung

Eine neue Freigabe gilt ausschließlich für **30442** und dieselbe DEV-Umgebung. Die bereits korrekt gespeicherten zwei Metadatenzeilen werden nicht erneut geschrieben. Der übrige Testumfang bleibt begrenzt:

1. Vorzustand lesen: DEV 30441/185, beide bestätigten Metadatenschlüssel, fachliche Bestands-IDs und nur nötige redigierte Quellenwerte. Bei abweichendem Stand stoppen; keine weiteren Metadaten-Writes.
2. 30442 unmanaged importieren, **ohne Publish All**. Postimport lesend gegen Kandidat prüfen. In Studio öffnen, kanonische Personen-Items unterstützt neu binden, Formel exakt wiederherstellen und Checker ausführen. Notwendige lokale Formelreparaturen zuerst als neuen prüfbaren Kandidaten bauen; keine stillen fachlichen Studioänderungen. Gezielt diese App speichern/veröffentlichen, frischen Player öffnen.
3. Lesende Tests: beide Listen, Titelanfang/ID, kein Treffer/ungültige ID, Navigation/Seitenführung, unsupported Provider, vorhandenen Datensatz ohne Save öffnen/abbrechen, Tastatur/Fokus/Dirty-/Busy-Sperren. Studio-Delegationswarnungen und tatsächliche Connector-Ausführung prüfen; große Datensatzmengen nur lesen, keine Massentestdaten erzeugen. Falls echte >2.000-Evidenz fehlt, ausdrücklich als offen festhalten.
4. **Genau ein synthetisches Asset und ein synthetisches System über die App neu anlegen** (zwei Creates). Eindeutige Titel `P1-SMOKE-<UTC>-ASSET` / `P1-SMOKE-<UTC>-SYSTEM`, zugelassenes Testkonto, repräsentative gültige Choices sowie leere optionale Werte; System bei Bedarf an das synthetische Asset koppeln. IDs und tatsächlich gespeicherte Quellenwerte erfassen.
5. Jeden Testdatensatz über Liste/ID erneut öffnen. Default-/Dirty-Zustand prüfen. **Je einmal ausschließlich den Titel ändern und speichern** (zwei Edits), erneut öffnen und Quelle vergleichen. Alle anderen 17/16 gemappten Werte müssen erhalten bleiben, ebenso nicht gemappte Quellenwerte. Benutzerwerte nicht anhand der UI allein als korrekt ausgeben.
6. **Ein kontrollierter zusätzlicher Quellen-Edit am synthetischen Asset** für den Konflikttest: in der App vorab laden, dann den Titel dieses ID-/Marker-bestätigten Testassets über einen zweiten Client ändern. App-Title abweichend bearbeiten und Save versuchen. Der Versuch muss vor Patch blockieren bzw. als echter Connector-Konflikt enden; Titel/Modified/Version nachlesen, keine automatische Wiederholung. Dies belegt die beobachtete Reihenfolge, keine ungetestete atomare ETag-Garantie.
7. Ausschließlich diese zwei bestätigten synthetischen IDs reversibel in den normalen Papierkorb entfernen, System zuerst wegen Lookup. ID-Filter, exakte Papierkorbtitel/Herkunft und alle vorab erfassten Bestandsdatensätze prüfen. Kein Reset, keine Bulk-Löschung, keine produktiven Inhalte anfassen.

Erlaubt wären damit maximal **zwei Creates, zwei normale App-Edits, ein zusätzlicher Konflikt-Quellen-Edit, ein erwartbar blockierter App-Save-Versuch und zwei reversible Testdatensatzlöschungen**, neben der 30442-Kandidatenübernahme. Die zwei Metadaten-Writes aus der vorherigen Freigabe sind bereits verbraucht und bleiben erhalten. Bei unklarem Save-Ausgang zuerst Quellenprüfung, kein erneuter Save. Scheitert ein Round-Trip, bleibt P1 offen; weitere Tenant-Saves benötigen neuen konkreten Scope/Freigabe. Import/Publikation macht P1 nicht automatisch produktionsreif.

## Technische Quellen und offene Host-Gates

Die direkte SharePoint-Abfrage verwendet Titelanfang und ID-Gleichheit entsprechend der [Microsoft-Delegationsmatrix](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/connections/connection-sharepoint-online). ID-Bereichsoperatoren werden vermieden. [Galerie-Navigation und AllItems](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/control-gallery) beziehen sich auf geladenen Umfang; P1 zeigt keine Gesamtzahl. Die [Patch-Dokumentation](https://learn.microsoft.com/en-us/power-platform/power-fx/reference/function-patch) beschreibt den nativen Basisrecord; [Errors/Conflict](https://learn.microsoft.com/en-us/power-platform/power-fx/reference/function-errors) hängt von Datenquellenunterstützung ab. Daraus folgt das noch offene Studio-/Delegations-/Connector-Gate, kein vorweggenommener Live-Nachweis.
