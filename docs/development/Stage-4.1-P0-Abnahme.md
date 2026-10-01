# P0 – Stage 4.1: Kandidat und ausstehende DEV-Abnahme

Stand: 2026-10-01 · Modellklasse: `standard-reasoning` · P0 bleibt offen

## Kandidat und Umfang

Branch `codex/stage41-p0` auf Roadmap-Head `964dc6112b618d22b056d468d93d45cfbd423f05` (PR #15), damit Zustandsquelle und Arbeitspaket übereinstimmen. Der ursprüngliche Workspace auf `codex/stage-4.1-dev-baseline` und seine gestagten Änderungen bleiben erhalten. Provisioning `6.2.5` und Canvas `1.0.0-alpha.4.1.0` bleiben gleich; die lokale Solution trägt `1.0.0.30431`.

- **Neu:** passende Auswahl, vorhandener Provider, Create und Save erforderlich; Busy sperrt den Befehl. `OnSelect` prüft den aktuellen DisplayMode vor der Initialisierung.
- **Save:** passende Provideridentität und Save erforderlich. New prüft Create; Edit prüft Edit und positive ID. Unbekannter Modus, fehlender Provider, Busy oder fehlgeschlagene Validierung sperren Save. Auch programmatische Auswahl und veraltete Eligibility umgehen die Sperre nicht.
- **Dashboard:** Asset-Gesamtzahl entfernt, weil `CountRows(Assets)` beim SharePoint-Connector keine verlässliche Gesamtzahl liefert. Keine Ersatzkennzahl aus einer ebenfalls begrenzten Sammlung.
- Registry, Schema, Personen-/Choice-Mappings und bestehende Patch-Zweige bleiben unverändert. P1 implementiert erst den Load-/Edit-Einstieg. `SupportsSave` ist keine produktive Freigabe.

Lokales Artefakt: `artifacts/outbound/GovernancePortal_1.0.0.30431_1.0.0-alpha.4.1.0.zip` (ignoriert, nicht versioniert). SHA-256 ZIP: `11d575e2dfd6dfba64f3de0512cdcde14aa6f04ccec70877e7228b28bd1da4b4`; msapp: `02e58e6311e2e61a2351814c276f7a5b3673ecf56e3dd5417f54be65902191d5`.

## Verifikation und Grenzen

| Gate | Ergebnis / Exit-Code |
|---|---|
| Offline-Power-Fx-Capabilities | 58 Assertions erfolgreich / 0; tatsächliche DisplayMode-/Revalidierungsformeln mit allen neun Providern, invaliden IDs/Modi, fehlendem/veraltetem Provider, Busy, leeren/invaliden Feldern und veralteter Eligibility. Kein Tenantzugriff. |
| Vollständiger Build | erfolgreich / 0; Version, Registry, Runtime-Sync, Canvas-Quellen/Referenzen, PAC Canvas-Pack und Solution-Pack |
| PAC SourceCode-Pack/Unpack | vier kanonische YAMLs bytegleich nach Newline-/BOM-Normalisierung / 0 |
| PowerShell-Syntax | erfolgreich / 0 |
| Architekturcompiler / Konsistenz | erfolgreich / 0; 16 Objekttypen, 50 kompilierte Listen |
| Canvas-Artefaktvergleich / Repository-Audit / Diff | erfolgreich / 0 |
| Pester | nicht ausgeführt: Modul lokal nicht installiert; keine Pester-Abnahme behauptet |
| `pac canvas validate` | nicht verfügbar in PAC 2.9.3; SourceCode-Pack verlangt zusätzlich Maker-Validierung |
| DEV `30431`, Studio-Checker und Asset-Save | nicht ausgeführt; separate Freigabe sowie funktionierender Zugang/Bereinigungsweg erforderlich |

`Test-CanvasCapabilities.ps1` lädt die Core-/Interpreter-DLLs aus einer explizit angegebenen lokalen Power-Fx-Installation. Die bestehende CI validiert Syntax, Architektur, Registry/Runtime und gepackte YAMLs; sie führt diesen Engine-Test mangels PAC-DLLs nicht aus. Der Test ersetzt keinen Canvas-Host, SharePoint-Connector oder Maker-Compiler.

## App-Checker-Triage

Letzter belegter Live-Stand: DEV-Solution `30430`, Canvas 165 Live am 28.09.2026. Studio erzeugte dabei gespeicherte, unveröffentlichte Version 166. Am 01.10.2026 scheiterte die erneute lesende Versionsprüfung zunächst an `refresh_token_expired`, danach an der Microsoft-Anmeldeweiterleitung. Nach dem angebotenen Wiederholungsweg fordert Power Apps erneut Anmeldung. Kein aktueller DEV-Head wird daraus abgeleitet.

| Kategorie aus Studio am 28.09. | Entscheidung / Abnahme |
|---|---|
| 1 Formelwarnung: `CountRows(Assets)` | Genauigkeitsproblem im Dashboard; Ausdruck im kanonischen P0-Quellcode entfernt. Nach DEV-Import in Studio prüfen, dass die Warnung tatsächlich weg ist. |
| 2 Datenquellenhinweise | Offen und abnahmerelevant: Details/IDs und betroffene Connections lesen; Verbindung und erforderliche Rechte mit dem DEV-Testkonto belegen. Keine pauschale Freigabe aus bloßen Counts. |
| 79 Barrierefreiheitshinweise | Offen: Neu, Speichern, Abbrechen und Personenpicker mit Tastatur/Fokus/verständlichen Labels prüfen; Blocker im Asset-Neuanlagepfad vor P0-Abnahme beheben. Weitere Detailbefunde mit Zielpaket vor Pilotfreigabe erfassen. |
| 12 Leistungshinweise | Offen: konkrete Regeln/Controls erfassen und Start/Formular/Pickersuche/Save beobachten. Hinweise auf unnötige Loads gehen gezielt in P1; ohne Details keine Entwarnung. |

PAC übernimmt alte interne Controls und `AppCheckerResult.sarif` aus der Pack-Baseline. Dort stehen weiter `CountRows(Assets)` und historische Formelbefunde. Dieser Snapshot ist weder neu berechnet noch ein aktueller Studio-Bericht. Er wird nicht gelöscht, um eine vermeintlich grüne Abnahme zu erzeugen. Maßgeblich ist die erneute Maker-Prüfung des freigegebenen Kandidaten.

## Kontrollierter Asset-Speichertest

1. Bestehende Microsoft-Anmeldung erneuern. DEV-App/Umgebung und tatsächliche Live-/Saved-Version lesen; bei neueren fachlichen Änderungen stoppen und Delta klären, keine automatische DEV-Übernahme.
2. **Vor jeder Neuanlage** direkten Zugriff auf die richtige DEV-Assets-Liste nachweisen. Testverantwortlicher muss den einzelnen synthetischen Datensatz lesen und über den SharePoint-Papierkorb reversibel entfernen können. Asset hat im Architekturmodell `allowDelete = false`; hierfür wird kein App-Delete-Provider oder pauschales Löschrecht ergänzt. Bei `Access denied` oder unklarem Rückweg bleibt der Save-Test gesperrt.
3. Kandidat `30431` nach separater DEV-Import-/Veröffentlichungsfreigabe einspielen und im Studio prüfen. Prüfen: Asset/System erlauben Neu; Contact, Incident, Problem, Change, Risk, Control, Measure nicht. Asset-Abbruch ohne Speichern funktioniert. Save ist bei fehlenden Pflichtwerten gesperrt. App-Checker-Details protokollieren.
4. Genau einen synthetischen Asset anlegen: eindeutiger Titel `P0-SMOKE-<UTC-Zeit>-<Kurzkennung>`, ausschließlich synthetischer fachlicher Inhalt, ein ausdrücklich zugelassenes vorhandenes DEV-Testkonto als Verantwortlicher, gültige Metadaten-Choicewerte. Ist kein eindeutiger Titel im Formular verfügbar oder würde der Fallback `Asset` greifen, vor Save stoppen. Nicht unterstützte Felder nicht als geprüft ausgeben.
5. Nach dem einzigen Save Erfolg und zurückgegebene ID festhalten. **Nicht blind erneut speichern**, falls Antwort/Fehler unklar ist: zuerst anhand Titel/ID in der Datenquelle auf möglichen bereits angelegten Datensatz prüfen.
6. In der DEV-Assets-Liste genau diese ID öffnen und Titel, Owner, ausgewählte Choicewerte und weitere tatsächlich ausgefüllte gemappte Felder vergleichen. Quellen-Nachweis mit App-Erfolg abgleichen. App-Wiederöffnen/Ändern gehört zum noch fehlenden P1-Datensatzkern.
7. Ausschließlich den anhand ID **und** Smoke-Titel bestätigten Testdatensatz reversibel in den Papierkorb verschieben; keine Suche-und-Massenlöschung, kein Purge/Reset. Abwesenheit in der aktiven Liste belegen. Bei fehlgeschlagener Bereinigung ID intern für den Testverantwortlichen halten und P0 offen lassen.
8. Redigierte Abnahmeevidenz eintragen (Versionen, Datum, Erfolg/Fehler, Feldvergleich, Bereinigung, relevante Checker-Regeln). Keine Personen-, Tenant-, Credential- oder Voll-Logs committen.

## Freigaben und nächster Schritt

`weiter` autorisiert dieses lokale P0-Paket einschließlich Commit/Push und Draft-PR. Die frühere DEV-Freigabe bezog sich auf `30430`; sie gilt nicht automatisch für `30431`. Keine neuen DEV-Imports, Studio-Veröffentlichungen, Provisioning-, Seed-, Reset- oder Datensatz-Writes wurden ausgeführt. PR #14 bleibt Draft; PR #6 bleibt isoliert/DO NOT MERGE.

**Primäres nächstes Arbeitspaket: P0-DEV-Abnahme dieses Kandidaten.** Anmeldung und Bereinigung nachweisen, dann den separat freigegebenen Import/Studio-Check und genau einen freigegebenen synthetischen Asset-Save samt Quellenprüfung/Bereinigung durchführen. Erst nach dieser Evidenz ist P0 geschlossen und P1 der Default-Scope.
