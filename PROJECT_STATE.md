# Projektübergabe – GovernancePlattform

Stand: 2026-10-01 · Arbeitszweig: `codex/stage41-p0` auf Roadmap-Head `964dc6112b618d22b056d468d93d45cfbd423f05` (PR #15). Fachlicher Zielzweig bleibt `feature/canvas-stage-4.1-provider-engine`. Die bestehenden PRs #13/#14/#15 und der ursprüngliche Workspace werden nicht umgeschrieben.

## Aktueller Kandidat

- Provisioning `6.2.5`; Canvas `1.0.0-alpha.4.1.0`; **Solution `1.0.0.30431` in DEV importiert; Canvas 168 Live nach Studio-Verarbeitung und Veröffentlichung.** Branch und Draft-PR sind die dauerhafte Übergabe; das ZIP bleibt lokales, ignoriertes Build-Artefakt.
- Neu verlangt passenden Provider mit Create und Save; Save verlangt den passenden Provider, Save und je nach Modus Create oder Edit mit positiver ID. Busy/ungültiger Editor sperren den Befehl; OnSelect prüft vor Mutationen die aktuelle Sperre. Die Registry bleibt unverändert: Asset/System mit Save, sieben andere registrierte Provider ohne Save.
- Die nicht delegierbare Asset-Gesamtzahl wurde entfernt. Die übrigen Dashboard-Metadatenzähler bleiben bestehen; kein Ersatz durch einen begrenzten Fachdatensatz-Cache.
- Patch-/Personen-/Choice-Mappings und das führende Architekturmodell bleiben erhalten. Liste/Laden/Bearbeiten bestehender Datensätze fehlen weiterhin und gehören zu P1. Schema/Metadaten für Change, Risk, Evidence und Reviews sind keine App-Abnahme.
- Roadmap P0–P7 priorisiert Asset-Pilot, danach Asset/Change/Risk/Evidence mit Verantwortlichen und Reviews. Incident/Problem und weitere Listen folgen.
- Profil 1.2.0 ist adoptiert. Framework-Conformance-PR #6 bleibt isoliert und DO NOT MERGE; keine Framework-Locks/Runtimeversionen ergänzt.

## Belegte DEV-Abnahme vom 01.10.2026

Nach ausdrücklicher Freigabe wurde `30431` per PAC erfolgreich importiert (Exit 0). Die Sicherung vor Import bestätigte unverändert `30430` und das bekannte Artefakt; der Export nach Import bestätigte `30431` und ein bytegleiches msapp (`02e58e6311e2e61a2351814c276f7a5b3673ecf56e3dd5417f54be65902191d5`). Canvas 167 war zunächst Live, führte aber noch alte Neu-Steuerdaten aus. Erst Studio verarbeitete die YAMLs; gespeicherte 168 wurde innerhalb der Freigabe veröffentlicht. **168 ist laut Versionsliste Live**, und auf dem neu geladenen Player funktionieren die Neu-Sperren für Kontakt, Change, Problem und Incident.

Das in Studio kompilierte msapp hat SHA-256 `5c7ff36d4c93417b8c962b6e6561c5bb7c4a48b8e447cdcdc78ba711054a1d77`. Studio lokalisiert SharePoint-Spaltennamen in zwei YAMLs; die tatsächlichen drei Capability-/Revalidierungsformeln stimmen exakt mit Git überein, CountRows(Assets) fehlt. Keine DEV-Quellen oder neue Pack-Baseline wurden automatisch nach Git übernommen. Ein reiner PAC-Import ersetzt diesen Maker-/Veröffentlichungsschritt nicht.

Studio: keine Formelfehler. Die zwei Datenquellenhinweise betreffen ungenutzte TextResources/StatusPresentation. Zwölf Leistungshinweise betreffen zehn nicht aktualisierte Collections und zwei ForAll-Mutationen; Optimierung bei P1. Die 79 Barrierefreiheitsfehler sind konkretisiert (25 Fokus, 31 Tabstopps, 23 Labels) und betreffen auch die interaktiven Asset-Kerncontrols; diese sind vor Pilotfreigabe zu korrigieren.

Direkter DEV-Assets-Zugriff, Einzel-Löschbefehl und normaler SharePoint-Papierkorb sind verfügbar. **Der freigegebene Asset-Save-Test wurde vor dem Write abgebrochen:** 30 aktive Asset-Formularfelder enthalten kein Title, auch die Architektur definiert es nicht als Formularfeld; der Patch würde den generischen Titel Asset verwenden. Das vereinbarte Abbruchkriterium für fehlenden eindeutigen Smoke-Titel bleibt bestehen. Kein neuer Datensatz, kein behaupteter Save-/Quellen-/Bereinigungsnachweis. Alle ungespeicherten Formulare verworfen; Studio geschlossen.

Zusatzbefund: Navigation Risiko & Compliance zeigt eine leere Providerliste. Risk/Control/Measure daher nicht live einzeln geprüft; dieser Navigationsvertrag ist beim Datensatzkern zu klären.

## Paketabschluss lokal

- Semantische Modellklasse `standard-reasoning`: begrenzte Canvas-Capability-Korrektur, keine Schema-/Provider-Neuarchitektur.
- Power-Fx-Engine: **58 Assertions / Exit 0**, direkt auf den tatsächlichen DisplayMode-/Revalidierungsformeln. Positive Asset/System-Pfade und negative Provider-/ID-/Modus-/Busy-/Validierungskontexte bestehen. OnSelect-Guards vor Mutationen geprüft; keine Tenantcalls.
- Vollständiger PAC-Build `30431`, Registry-/Runtime-/Canvas-Prüfungen, vier YAMLs im msapp, PAC-Pack/Unpack, PowerShell-Syntax, Architekturcompiler/Konsistenz, Repository-Audit und Diff: **Exit 0**. Kandidaten-Hashes und Änderungen stehen in [P0-Abnahme](docs/development/Stage-4.1-P0-Abnahme.md).
- Lokales Pester nicht installiert; `pac canvas validate` in PAC 2.9.3 nicht verfügbar. Engine-Test läuft lokal mit explizitem DLL-Verzeichnis, nicht in der bestehenden CI. PAC behält alte interne Controls/SARIF-Snapshots: deren Meldungen werden nicht als aktueller Maker-Check interpretiert und nicht zur Grünfärbung gelöscht.
- CI #14 (`dd406bc`) und #15 (`964dc61`) beim Einstieg erfolgreich. PR #16 am Implementierungs-Head `d8d4f6b0e8f7db443a1681c7a9f883ef69302625`: alle drei CI-Prüfungen erfolgreich. Der aktuelle Dokuabschluss wird erneut am gepushten PR-Head geprüft; lokale Gates ersetzen CI nicht.
- Die Freigabe vom 01.10. galt Import/Veröffentlichung `30431` und genau einem synthetischen DEV-Asset-Test nach gesichertem Bereinigungsweg. Import und Studio-Veröffentlichung ausgeführt; Test vor Write wegen fehlendem Titel abgebrochen. Keine DEV-Übernahme, kein Provisioning/Seed/Reset, kein Datensatz-Write, kein Merge/Release. Der ursprüngliche Branch und seine elf gestagten Dateien bleiben erhalten; keine automatische Synchronisierung dorthin.

## Primäres nächstes Arbeitspaket

**P0-Reparatur des Asset-Neuanlagevertrags:** Title durch Architektur/generierte Formularmetadaten/Canvas/Patch konsistent verfügbar machen und Tastatur/Fokus/Bezeichnungen der interaktiven Kerncontrols korrigieren. Danach genau einen synthetischen Asset speichern, anhand ID und Smoke-Titel verifizieren und bereinigen. [DEV-Evidenz, Checker-Triage und Testablauf](docs/development/Stage-4.1-P0-Abnahme.md). Neue Metadata-/Provisioning-Writes und ein neuer Importkandidat benötigen separate Freigabe. PR #14/#16 bleiben Draft; P1 folgt erst nach P0-Abnahme.
