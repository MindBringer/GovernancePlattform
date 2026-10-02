# P1 – Datensatzkern und DEV-Abnahme

Stand: 2026-10-02. **Lokale Umsetzung bereit; keine P1-Live-Abnahme.** Primäres Folgepaket ist ausschließlich die hier beschriebene P1-DEV-Abnahme. Modellklasse `deep-reasoning` wegen Canvas-/Provider-/SharePoint-Kopplung und Datenintegrität.

## Kandidat und Grenzen

- Branch `codex/stage41-p1`, Basis P0 `5caee00823032b4306f0bdaa900ca9817a53610e`, eigener Draft auf `codex/stage41-p0`.
- Solution **1.0.0.30441**, Canvas `1.0.0-alpha.4.1.0`, Provisioning `6.2.5`; Versionsreihen getrennt.
- Letzter belegter Live-Stand: **P0 30440 / Canvas 184**. Frühere P0-Neuanlage-/Save-Freigaben sind verbraucht. `weiter P1` beauftragt die lokale Umsetzung, Tests, Kandidat und Draft; kein neuer Import/Publish oder Tenant-Save.
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
| Vollständiger `Build.ps1`, PAC 2.9.3 SourceCode-/Solution-Pack | 0; 30441, kein Import/Publish |
| Canvas-Artefaktvergleich / SourceCode-Unpack | 0; vier kanonische YAMLs unverändert |
| Architecture / ArchitectureConsistency | 0 / 0 |
| PowerShell-Syntax | 0; 35 PS1-/PSM1-Dateien |
| Asset-/System-Title-Vertrag | 0 / 0; je zwei isolierte Zusatzzeilen, andere 1.014 unverändert |
| CanvasSource / Registry / Runtime CheckOnly / References | jeweils 0 |
| Personen-Quellvertrag | 0; vier negative Fixtures verworfen |
| Accessibility-Quellvertrag | 0; 20 Controls / fünf Galerien, Load-/Save-/Modal-Sperren |
| Capability-Engine | 0; 137 tatsächliche Assertions |
| Choice-Quell-/Compiler-/Enginevertrag | 0; zehn Adapter / 42 Werte, 212 tatsächliche Assertions |
| Record-Quell-/Compiler-/Enginevertrag | 0; Asset 17 / System 16 Felder, 275 tatsächliche Assertions, 51 mehrzeilige Formeln geparst |
| Repository-Audit / Diff | 0 / 0 |

**624 tatsächliche Offline-Power-Fx-Assertions.** Die Recordtests werten tatsächliche Projektionen, Hydrierung, Payloads, Guard- und Galerieformeln aus. Voll-/Leerwerte, Datumszeiten, native Personenalias-/Claims-Werte, optionales Leeren, unveränderte Defaults, unbekannte Choices, fehlende Metadaten, falsche Kontrolltypen, Modified-Konflikte und 3.000-Zeilen-Fixtures sind enthalten. Ein lokaler Fixture-Test beweist keine SharePoint-Serverdelegation.

CI enthält Record-Quell-/Compilervertrag und beide Title-Gates; optionale Engine-DLL-Tests laufen lokal. Exakter Git-/CI-Head und URLs werden im Draft und ignorierten lokalen Handoff festgehalten, nach Push gegen den tatsächlichen Head geprüft. Pester nicht installiert; PAC `canvas validate` in 2.9.3 nicht vorhanden. Kein aktueller P1-Studio-Checker, Tenant-Round-Trip oder realer Rollen-/ETag-/Delegationsnachweis.

## Kandidaten-Hashes

- `GovernancePortal_1.0.0.30441_1.0.0-alpha.4.1.0.zip`: SHA-256 `7f40b2ede2a1cbd43555e4c4f306bd751a8287cb396a9c43cf52a2d42a85c799`.
- Versioniertes `gp_governanceportal_c93a1_DocumentUri.msapp`: SHA-256 `7610a5177eab92eb400a9c4dfa254d7d3e87d9c02d7febff0123585834ffe719`.

Originaler Workspace mit elf gestagten Dateien und P0-Branch erhalten; keine Framework-Locks/-Runtimeversionen, kein Merge/Release. PR #6 bleibt DO NOT MERGE. Neue Logs, ZIPs, Tenantsettings und personenbezogene Daten bleiben außerhalb Git.

## Konkreter Freigabeumfang für P1 DEV

Eine folgende Freigabe gilt ausschließlich für diesen Kandidaten und die DEV-Umgebung:

1. Vorzustand lesen und sichern: aktuelle App-/Solution-Version, Metadatenschlüssel, fachliche Test-/Bestands-IDs und nur nötige redigierte Quellenwerte. Abweichung vom belegten Stand zunächst klären. Genau die zwei System-Title-Zeilen aus dem Plan ergänzen; falls sie bereits identisch vorhanden sind, kein Write. Bei abweichenden existierenden Zeilen stoppen.
2. 30441 unmanaged importieren, **ohne Publish All**. Postimport lesend gegen Kandidat prüfen. In Studio öffnen, kanonische Personen-Items unterstützt neu binden, Formel exakt wiederherstellen und Checker ausführen. Notwendige lokale Formelreparaturen zuerst als neuen prüfbaren Kandidaten bauen; keine stillen fachlichen Studioänderungen. Gezielt diese App speichern/veröffentlichen, frischen Player öffnen.
3. Lesende Tests: beide Listen, Titelanfang/ID, kein Treffer/ungültige ID, Navigation/Seitenführung, unsupported Provider, vorhandenen Datensatz ohne Save öffnen/abbrechen, Tastatur/Fokus/Dirty-/Busy-Sperren. Studio-Delegationswarnungen und tatsächliche Connector-Ausführung prüfen; große Datensatzmengen nur lesen, keine Massentestdaten erzeugen. Falls echte >2.000-Evidenz fehlt, ausdrücklich als offen festhalten.
4. **Genau ein synthetisches Asset und ein synthetisches System über die App neu anlegen** (zwei Creates). Eindeutige Titel `P1-SMOKE-<UTC>-ASSET` / `P1-SMOKE-<UTC>-SYSTEM`, zugelassenes Testkonto, repräsentative gültige Choices sowie leere optionale Werte; System bei Bedarf an das synthetische Asset koppeln. IDs und tatsächlich gespeicherte Quellenwerte erfassen.
5. Jeden Testdatensatz über Liste/ID erneut öffnen. Default-/Dirty-Zustand prüfen. **Je einmal ausschließlich den Titel ändern und speichern** (zwei Edits), erneut öffnen und Quelle vergleichen. Alle anderen 17/16 gemappten Werte müssen erhalten bleiben, ebenso nicht gemappte Quellenwerte. Benutzerwerte nicht anhand der UI allein als korrekt ausgeben.
6. **Ein kontrollierter zusätzlicher Quellen-Edit am synthetischen Asset** für den Konflikttest: in der App vorab laden, dann den Titel dieses ID-/Marker-bestätigten Testassets über einen zweiten Client ändern. App-Title abweichend bearbeiten und Save versuchen. Der Versuch muss vor Patch blockieren bzw. als echter Connector-Konflikt enden; Titel/Modified/Version nachlesen, keine automatische Wiederholung. Dies belegt die beobachtete Reihenfolge, keine ungetestete atomare ETag-Garantie.
7. Ausschließlich diese zwei bestätigten synthetischen IDs reversibel in den normalen Papierkorb entfernen, System zuerst wegen Lookup. ID-Filter, exakte Papierkorbtitel/Herkunft und alle vorab erfassten Bestandsdatensätze prüfen. Kein Reset, keine Bulk-Löschung, keine produktiven Inhalte anfassen.

Erlaubt wären damit maximal **zwei Creates, zwei normale App-Edits, ein zusätzlicher Konflikt-Quellen-Edit, ein erwartbar blockierter App-Save-Versuch und zwei reversible Testdatensatzlöschungen**, neben den zwei begrenzten Metadatenzeilen und der Kandidatenübernahme. Bei unklarem Save-Ausgang zuerst Quellenprüfung, kein erneuter Save. Scheitert ein Round-Trip, bleibt P1 offen; weitere Tenant-Saves benötigen neuen konkreten Scope/Freigabe. Import/Publikation macht P1 nicht automatisch produktionsreif.

## Technische Quellen und offene Host-Gates

Die direkte SharePoint-Abfrage verwendet Titelanfang und ID-Gleichheit entsprechend der [Microsoft-Delegationsmatrix](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/connections/connection-sharepoint-online). ID-Bereichsoperatoren werden vermieden. [Galerie-Navigation und AllItems](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/control-gallery) beziehen sich auf geladenen Umfang; P1 zeigt keine Gesamtzahl. Die [Patch-Dokumentation](https://learn.microsoft.com/en-us/power-platform/power-fx/reference/function-patch) beschreibt den nativen Basisrecord; [Errors/Conflict](https://learn.microsoft.com/en-us/power-platform/power-fx/reference/function-errors) hängt von Datenquellenunterstützung ab. Daraus folgt das noch offene Studio-/Delegations-/Connector-Gate, kein vorweggenommener Live-Nachweis.
