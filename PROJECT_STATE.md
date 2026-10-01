# Projektübergabe – GovernancePlattform

Stand: 2026-10-01 · Branch `codex/stage41-p0` auf Roadmap-Head `964dc6112b618d22b056d468d93d45cfbd423f05` (PR #15). Fachlicher Zielzweig bleibt `feature/canvas-stage-4.1-provider-engine`; Draft [PR #16](https://github.com/MindBringer/GovernancePlattform/pull/16) enthält P0.

## Kandidat und belegter DEV-Stand

- Provisioning `6.2.5`, Canvas `1.0.0-alpha.4.1.0`, lokaler Solution-Kandidat **30440**; noch nicht importiert. DEV **30439 / Canvas 181 Live**.
- Genau zwei Asset-Title-Metadaten angelegt/verifiziert. Title-Validierung funktioniert im veröffentlichten Player: leer/Leerzeichen sperren, nicht leer aktiviert Save. Die neun Ereignis-Guards und der erfasste Text-Update-Record sind wirksam.
- Personenpicker braucht nach SourceCode-Import ein unterstütztes Studio-Rebinding der kanonischen Items-Formel. Für 181: benannter Treffer, stabile direkte Auswahl, Owner korrekt in der Quelle; lesender Export bestätigt die generierte V2-Suchregel. Private SearchItems-YAML ist unzulässig (PA2108), keine gepackte zweite Bearbeitungsquelle.
- **Genau ein freigegebener Asset-Save** erfolgreich (ID 8). Getrimmter synthetischer Titel/zugelassenes Testkonto korrekt. Kritikalität fehlerhaft: Hoch gewählt, UI Niedrig, Quelle `Criticality:High`. **P0 bleibt wegen Datenintegrität offen.**
- Ausschließlich ID 8 mit passendem Smoke-Titel reversibel bereinigt. ID-gefilterte Liste leer, Papierkorb/Herkunft Assets belegt; vier vorhandene Assets weiterhin sichtbar. Kein zweiter Save, Purge, Seed oder Reset.
- 30440 übersetzt interne qualifizierte Choice-Schlüssel in feldbezogene deutsche Anzeigenamen für Default und zehn bestehende native SharePoint-Patches; leere Auswahl bleibt leer, unbekannte nicht leere Schlüssel sperren Save/Revalidierung. Interne Schlüssel, Architektur und Provider-Capabilities bleiben erhalten. Diese Reparatur ist offline geprüft, noch nicht live abgenommen.
- Nicht vollständig belegt: reine Tastatur-Persistenz der Personenauswahl, Neu-Fokus nach endgültigem Verwerfen, aktueller vollständiger App-Checker für den neuen Kandidaten. Historische Checker-Counts und gescheiterte Diagnoseversuche sind in der [P0-Abnahme](docs/development/Stage-4.1-P0-Abnahme.md) getrennt dokumentiert. Keine Produktiv-/Accessibility-Freigabe.

## Gates und Git

**347 tatsächliche Offline-Power-Fx-Assertions / Exit 0** (135 Capability-/Ereignisprüfungen + 212 Choice); zehn native Adapter / 42 deklarierte Werte. Title-Metadatendelta: zwei neue Zeilen, 1.012 bestehende unverändert / 0. Accessibility-Quellvertrag 16 Controls / drei Galerien / 0. Personen-Quellvertrag mit vier verworfenen negativen Fixtures / 0. Vollständiger PAC-Build, vier YAMLs im msapp, SourceCode-Round-Trip, 33 PowerShell-Syntaxdateien, Architektur/Konsistenz/Registry/Runtime/Referenzen, Audit/Diff bestehen. Pester fehlt; PAC 2.9.3 canvas validate nicht verfügbar; Engine lokal, Quell-/Compilervertrag auch CI. [Hashes, Grenzen und Freigaben](docs/development/Stage-4.1-P0-Abnahme.md).

CI am vorherigen Head `a69ccd032feb34530033ced8c8d51d14354a5ce5`: drei Checks erfolgreich. Neuer Kandidat und Dokumentation werden am Paketabschluss gegen den tatsächlichen PR-Head geprüft; Ergebnis im PR-Handoff. Ursprünglicher Workspace `codex/stage-4.1-dev-baseline` mit elf gestagten Dateien erhalten. Kein Merge/Release/DEV→Git-Source-Takeover. PR #14/#16 Draft; Framework-PR #6 isoliert/DO NOT MERGE, keine Framework-Locks/Runtimeversionen.

## Primäres nächstes Arbeitspaket

**P0-Choice-DEV-Abnahme von 30440:** konkrete neue Freigabe für Import ohne Publish All, Studio-Items-Rebinding/Checker/gezielte App-Veröffentlichung und **genau einen zusätzlichen** synthetischen Asset-Save mit Title, Testkonto und Kritikalität Hoch; Quelle muss Hoch enthalten, anschließend reversible Bereinigung verifizieren. Die ursprüngliche Einzel-Save-Freigabe ist verbraucht. Modellklasse `deep-reasoning` wegen belegter Galerie-/Host-/Compiler-/Connector-Kopplung und Datenintegritätsfehler. P1 erst nach erfolgreicher P0-Abnahme.
