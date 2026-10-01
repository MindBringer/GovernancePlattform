# Projektübergabe – GovernancePlattform

Stand: 2026-10-01 · Arbeitszweig: `codex/stage41-p0` auf Roadmap-Head `964dc6112b618d22b056d468d93d45cfbd423f05` (PR #15). Fachlicher Zielzweig bleibt `feature/canvas-stage-4.1-provider-engine`. Die bestehenden PRs #13/#14/#15 und der ursprüngliche Workspace werden nicht umgeschrieben.

## Aktueller Kandidat

- Provisioning `6.2.5`; Canvas `1.0.0-alpha.4.1.0`; **lokale Solution `1.0.0.30431`**, noch nicht in DEV importiert. Branch und Draft-PR sind die dauerhafte Übergabe; das ZIP bleibt lokales, ignoriertes Build-Artefakt.
- Neu verlangt passenden Provider mit Create und Save; Save verlangt den passenden Provider, Save und je nach Modus Create oder Edit mit positiver ID. Busy/ungültiger Editor sperren den Befehl; OnSelect prüft vor Mutationen die aktuelle Sperre. Die Registry bleibt unverändert: Asset/System mit Save, sieben andere registrierte Provider ohne Save.
- Die nicht delegierbare Asset-Gesamtzahl wurde entfernt. Die übrigen Dashboard-Metadatenzähler bleiben bestehen; kein Ersatz durch einen begrenzten Fachdatensatz-Cache.
- Patch-/Personen-/Choice-Mappings und das führende Architekturmodell bleiben erhalten. Liste/Laden/Bearbeiten bestehender Datensätze fehlen weiterhin und gehören zu P1. Schema/Metadaten für Change, Risk, Evidence und Reviews sind keine App-Abnahme.
- Roadmap P0–P7 priorisiert Asset-Pilot, danach Asset/Change/Risk/Evidence mit Verantwortlichen und Reviews. Incident/Problem und weitere Listen folgen.
- Profil 1.2.0 ist adoptiert. Framework-Conformance-PR #6 bleibt isoliert und DO NOT MERGE; keine Framework-Locks/Runtimeversionen ergänzt.

## Belegte DEV-Baseline und aktuelle Grenzen

Am 28.09.2026 wurde nach separater Freigabe Solution `30430` importiert; ein read-only Export bestätigte ein bytegleiches msapp (SHA-256 `2edcdb3de5942a5fcd0022c372162143866dcd453d9b6798fa6106c3a36c75b1`). Canvas 165 war laut Versionsliste Live. Anschließendes Studio-Öffnen erzeugte gespeicherte, unveröffentlichte 166. Navigation, 16 Objekttypen, 12 Seiten, Asset-Formular und Personensuche wurden geprüft; kein Datensatz wurde gespeichert. Direkter SharePoint-Zugriff endete mit Access denied, damit fehlte der sichere Bereinigungsweg.

Der Studio-Checker meldete eine CountRows-Delegierungswarnung sowie 79 Barrierefreiheits-, 12 Leistungs- und 2 Datenquellenhinweise. CountRows ist im neuen Quellcode entfernt; die übrigen Kategorien bleiben nach konkreten Regeln zu bewerten. Am 01.10.2026 war die Microsoft-Sitzung abgelaufen und die Anmeldeweiterleitung schlug fehl; die Versionsliste konnte nicht erneut gelesen werden. Der Stand vom 28.09. ist daher keine aktuelle Live-Verifikation.

## Paketabschluss lokal

- Semantische Modellklasse `standard-reasoning`: begrenzte Canvas-Capability-Korrektur, keine Schema-/Provider-Neuarchitektur.
- Power-Fx-Engine: **58 Assertions / Exit 0**, direkt auf den tatsächlichen DisplayMode-/Revalidierungsformeln. Positive Asset/System-Pfade und negative Provider-/ID-/Modus-/Busy-/Validierungskontexte bestehen. OnSelect-Guards vor Mutationen geprüft; keine Tenantcalls.
- Vollständiger PAC-Build `30431`, Registry-/Runtime-/Canvas-Prüfungen, vier YAMLs im msapp, PAC-Pack/Unpack, PowerShell-Syntax, Architekturcompiler/Konsistenz, Repository-Audit und Diff: **Exit 0**. Kandidaten-Hashes und Änderungen stehen in [P0-Abnahme](docs/development/Stage-4.1-P0-Abnahme.md).
- Lokales Pester nicht installiert; `pac canvas validate` in PAC 2.9.3 nicht verfügbar. Engine-Test läuft lokal mit explizitem DLL-Verzeichnis, nicht in der bestehenden CI. PAC behält alte interne Controls/SARIF-Snapshots: deren Meldungen werden nicht als aktueller Maker-Check interpretiert und nicht zur Grünfärbung gelöscht.
- CI #14 (`dd406bc`) und #15 (`964dc61`) beim Einstieg erfolgreich. Der CI-Nachweis für den neuen Kandidaten wird am gepushten Draft-PR-Head festgehalten; lokale Gates ersetzen ihn nicht.
- Keine DEV-Übernahme, kein Import/Publish, kein Provisioning/Seed/Reset, kein Live-Datensatz-Write, kein Merge/Release. Die frühere Importfreigabe galt `30430`. Der ursprüngliche Branch und seine elf gestagten Dateien bleiben erhalten; keine automatische Synchronisierung dorthin.

## Primäres nächstes Arbeitspaket

**P0-DEV-Abnahme von `30431`:** Microsoft-Anmeldung und direkten DEV-Assets-Zugriff mit reversibler Einzel-Bereinigung nachweisen. Dann nach separater Freigabe Kandidat importieren/Studio prüfen und genau einen synthetischen Asset speichern, anhand ID in der Datenquelle verifizieren und bereinigen. [Testablauf und Checker-Triage](docs/development/Stage-4.1-P0-Abnahme.md) sind vorbereitet. PR #14 bleibt bis zur fachlichen Abnahme Draft. Erst mit dieser Evidenz ist P0 geschlossen und P1 der Default-Scope.
