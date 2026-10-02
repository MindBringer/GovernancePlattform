# Projektübergabe – GovernancePlattform

Stand: 2026-10-02 · Branch `codex/stage41-p0` auf Roadmap-Head `964dc6112b618d22b056d468d93d45cfbd423f05` (PR #15). Fachlicher Zielzweig bleibt `feature/canvas-stage-4.1-provider-engine`; Draft [PR #16](https://github.com/MindBringer/GovernancePlattform/pull/16) enthält P0.

## Kandidat und belegter DEV-Stand

- Provisioning `6.2.5`, Canvas `1.0.0-alpha.4.1.0`, Solution **30440 / Canvas 184 Live**. DEV-Import ohne Publish All Exit 0; Postimport-msapp bytegleich mit dem Kandidaten.
- **P0 technisch in DEV abgeschlossen:** genau ein zusätzlich ausdrücklich freigegebener Asset-Save, ID 9. Synthetischer Titel nach Trim, zugelassenes Testkonto als Owner und Kritikalität **Hoch** direkt in SharePoint bestätigt. Anzeige blieb vor Save nach Fokuswechsel Hoch; Busy sperrte Navigation/Abbruch/Save. Danach ausschließlich diesen ID-/Titel-bestätigten Testdatensatz reversibel entfernt: ID-Filter leer, exakter Titel im normalen Papierkorb mit Herkunft Assets, alle vier Bestandsassets erhalten.
- Frühere 30439-Abnahme ID 8 scheiterte an inkonsistenter Choice-Anzeige/Quelle; ebenfalls bereinigt. Der alte Player zeigte vor dem aktuellen Test weiterhin Rücksprünge; ohne Save verworfen. Der erfolgreiche Test erfolgte in einem frisch geöffneten Player. Frischer Player ist verbindliches Host-Gate nach Veröffentlichung.
- Zwei Asset-Title-Metadaten bleiben erhalten. Leer-/Leerzeichentitel sperren, gültiger Titel aktiviert Save. 30440 löst Choice-Default und zehn native Adapter über feldbezogene Anzeigenamen auf; leere optionale Werte bleiben leer, unbekannte Schlüssel sperren Save/Revalidierung. Architektur und interne ChoiceKey-/Capability-Verträge unverändert.
- Personenpicker nach SourceCode-Import im Studio unterstützt neu gebunden, exakt kanonische Items-Formel wiederhergestellt. Lesender Studio-184-Export bestätigt generierte V2-Suchregel, Choice-Default/AllowEmptySelection, zehn Adapter und beide Save-Guards. Kein DEV→Git-Source-Takeover.
- Aktueller Studio-184-Checker vor Veröffentlichung: keine Formel-/Laufzeitbefunde; zwei ungenutzte Quellen, 56 Accessibility-Befunde und zwölf Leistungswarnungen. Vollständige Accessibility-/Rollen-/Produktivabnahme bleibt offen. Reine Tastatur-Persistenz der Personenauswahl nicht belegt; Neu-Fokus nach endgültigem Verwerfen nun positiv beobachtet.
- P0 belegt nur die getestete Neuanlage mit Titel/Owner/Kritikalität. Datensatzliste, Laden/Bearbeiten, vollständige Asset-Feldmappings (insbesondere GovernanceStatus), weitere Verantwortliche und Reviewablauf folgen P1/P2; keine Produktivfreigabe.

## Gates und Git

**347 tatsächliche Offline-Power-Fx-Assertions / Exit 0** (135 Capability-/Ereignisprüfungen + 212 Choice); zehn native Adapter / 42 deklarierte Werte. Title-Metadatendelta: zwei neue Zeilen, 1.012 bestehende unverändert / 0. Accessibility-Quellvertrag 16 Controls / drei Galerien / 0. Personen-Quellvertrag mit vier verworfenen negativen Fixtures / 0. Vollständiger PAC-Build, vier YAMLs im msapp, SourceCode-Round-Trip, 33 PowerShell-Syntaxdateien, Architektur/Konsistenz/Registry/Runtime/Referenzen, Audit/Diff bestehen. Pester fehlt; PAC 2.9.3 canvas validate nicht verfügbar; Engine lokal, Quell-/Compilervertrag auch CI. [Hashes, Grenzen und Freigaben](docs/development/Stage-4.1-P0-Abnahme.md).

CI am geprüften Code-/Doku-Head `2f229d4334501ed7ab595145989d5df49c3fa7a5`: drei Checks erfolgreich. Neuer Kandidat und Dokumentation werden am Paketabschluss gegen den tatsächlichen PR-Head geprüft; Ergebnis im PR-Handoff. Ursprünglicher Workspace `codex/stage-4.1-dev-baseline` mit elf gestagten Dateien erhalten. Kein Merge/Release/DEV→Git-Source-Takeover. PR #14/#16 Draft; Framework-PR #6 isoliert/DO NOT MERGE, keine Framework-Locks/Runtimeversionen.

## Primäres nächstes Arbeitspaket

**P1 · Datensatzkern:** echte Datensatzliste mit Suche/Seitenführung, Laden nach ID, Bearbeiten/Speichern für tatsächlich unterstützte Typen; Capabilities müssen den ausführbaren Load-/Save-Pfaden entsprechen. Leere Werte, Fehler und parallele Änderungen sichtbar behandeln; Round-Trip eines bestehenden Datensatzes nachweisen. Modellklasse `deep-reasoning` wegen Canvas-/SharePoint-/Provider-/Datenintegritätskopplung. Implementierung lokal-first; neue Tenant-Writes bleiben separat freigabepflichtig.
