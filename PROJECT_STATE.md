# Projektübergabe – GovernancePlattform

Stand: 2026-10-01 · Branch `codex/stage41-p0` auf Roadmap-Head `964dc6112b618d22b056d468d93d45cfbd423f05` (PR #15). Fachlicher Zielzweig bleibt `feature/canvas-stage-4.1-provider-engine`; Draft-PR #16 enthält das P0-Paket.

## Kandidat und belegter DEV-Stand

- Provisioning `6.2.5`, Canvas `1.0.0-alpha.4.1.0`; lokaler Solution-Kandidat **30435**. Die technische Reparaturschleife bleibt im ausdrücklich freigegebenen P0-DEV-Abnahmeumfang.
- Genau zwei Asset-Title-Metadaten angelegt und gespeicherte Werte geprüft. Bestehende Schlüssel waren leer; kein vollständiges Metadata-Publish, Provisioning, Seed oder Reset.
- 30433 erfolgreich importiert, Export bytegleich, Studio verarbeitet und **Canvas 171 Live** veröffentlicht. Keine Formel-/Laufzeitbefunde im Checker; zwei ungenutzte Quellen, 56 Accessibility-Fehler und zwölf Leistungswarnungen konkret erfasst. Keine pauschale Accessibility- oder Produktivfreigabe.
- Live: Enter/Space-Navigation und Asset/System-Neu funktionieren; Contact gesperrt. Pflicht-Titel erscheint zuerst, leer/Leerzeichen sperren Save. Verwerfen sperrt Hintergrund und gibt beim Weiterbearbeiten den Fokus an Abbrechen zurück. Nach endgültigem Verwerfen landet Tab bei Start; der beabsichtigte Neu-Fokus ist noch nicht belegt.
- **P0 bleibt offen:** Text ist in der Studio-Sammlung gespeichert (diagnostisch `DIAG`), aber IsValid bleibt false und ErrorMessage Pflichtfeld. Null Asset-Save-Versuche, null Asset-Datensatz-Writes. Der einzelne freigegebene Save-/Quellen-/Bereinigungstest bleibt ausstehend.
- 30434 sichert Text-/Validierungswerte vor dem Galerie-Patch und verwendet EditorFieldKey. Import erfolgreich, Canvas 172 Live; keine Studio-/Smoke-Abnahme dieses Zwischenstands. 30435 sperrt zusätzlich alle neun Änderungsereignisse der acht Eingabecontrols, wenn unsichtbar oder nicht bearbeitbar. Die geteilte Galeriezeile darf nicht von einem für ihren Feldtyp unsichtbaren Control verändert werden. Wirksamkeit wird live geprüft; Ursache noch nicht als abschließend bestätigt ausgegeben.
- Personen-/Choice-/Capability-Verträge bleiben erhalten. Personensuche mit dem DEV-Testkonto lieferte im untersuchten Player keinen auswählbaren Treffer; keine fremde Person als Ersatz gewählt. P1 implementiert erst Datensatzliste/Laden/Bearbeiten, P2 den vollständigen Asset-Round-Trip.

## Gates und Git

129 tatsächliche Offline-Power-Fx-Assertions / Exit 0: Guards, Titelgrenzen, Patch-Titel, erfasster Text-Update-Record und sichtbare/bearbeitbare Ereignisse. Metadatendelta: zwei neue Zeilen, 1.012 bestehende unverändert / 0. Accessibility-Quellvertrag: 16 Controls / drei Galerien / 0. Vollständiger PAC-Build, vier YAMLs im msapp, SourceCode-Round-Trip, Syntax/Architektur/Konsistenz/Registry/Runtime/Referenzen, Audit/Diff bestehen. Pester fehlt; PAC 2.9.3 canvas validate nicht verfügbar; Engine-Test lokal, nicht CI. Experimental-Unpack scheiterte mit NullReferenceException; unterstütztes SourceCode-Layout erfolgreich. [Details/Hashes/Live-Nachweise](docs/development/Stage-4.1-P0-Abnahme.md).

CI am Head `e4c9568ee069036980d1644d5c246a24fc51ce61`: drei Checks erfolgreich. Der neue Reparatur-Head wird nach Push geprüft. Ursprünglicher Workspace `codex/stage-4.1-dev-baseline` und elf gestagte Dateien bleiben erhalten. Kein Merge/Release/DEV→Git-Source-Übernahme. PR #14/#16 bleiben Draft; Framework-PR #6 isoliert und DO NOT MERGE, keine Framework-Locks/Runtimeversionen.

## Primäres nächstes Arbeitspaket

**P0-Ereignis- und DEV-Speicherabnahme von 30435:** Studio verarbeiten/prüfen und veröffentlichen, Titelvalidierung und Personenpicker mit Tastatur belegen; erst dann genau ein synthetischer Asset-Save mit Quellenvergleich und reversibler Bereinigung. Modellklasse für die nun über mehrere Controls/Host-Ereignisse gehende Reparatur: `deep-reasoning`. P1 folgt erst nach belegter P0-Abnahme; keine parallele Feature-Erweiterung.
