# Projektübergabe – GovernancePlattform

Stand: 2026-09-28 · Arbeitszweig: `codex/stage-4.1-dev-baseline` auf `codex/stage-4.1-sync` (`0f0070d`); fachlicher Zielzweig: `feature/canvas-stage-4.1-provider-engine`

## Aktueller Kandidat

- Provisioning `6.2.5`; Canvas `1.0.0-alpha.4.1.0`; Solution-Manifest `1.0.0.30429` (DEV-Importkandidat; DEV-Exportbasis `1.0.0.30428`).
- Stage 4.1 synchronisiert die neun registrierten Provider in `App.pa.yaml` und bindet `gblActiveProvider` an die Objektauswahl. Asset und System haben Edit/Save; die sieben übrigen Provider melden dafür weiterhin `false`.
- Das Companion-Profil 1.2.0 stammt aus dem Engineering-Template. Ein vollständiger Framework-Consumer-Vertrag ist noch nicht integriert; PR #6 bleibt isolierter Konformitätsnachweis.
- Ein read-only PAC-Export aus DEV bestätigte am 2026-09-28: Die vier Canvas-YAMLs stimmen mit dem fachlichen Reconciliation-Commit `dec366c` im isolierten Conformance-Branch überein. Die DEV-Solution trägt Version `1.0.0.30428`.
- Der neuere DEV-Stand für Personenfelder und Asset-Speichern wurde übernommen. Ein diagnostisches Label mit festem Suchwert wurde aus dem SourceTree entfernt; die gepackte App wurde lokal neu erzeugt. Die übrigen umgebungsspezifischen Solution-Dateien wurden nicht pauschal übernommen.
- Die NIS2-Roadmap von `main` ist enthalten und um Stage 4.1/4.2 und die spätere Framework-Adoption ergänzt.

## Verifikation dieses Arbeitspakets

- PowerShell-Syntax, Architekturcompiler und Architektur-Konsistenz: erfolgreich.
- Canvas-Version/Quellen, Provider-Registry und synchronisierte Runtime: erfolgreich.
- Lokaler vollständiger PAC-Build mit Solution-Inkrement auf `1.0.0.30429`: erfolgreich; Canvas- und Solution-Pakete erzeugt. Der SourceCode-Round-Trip und der Vergleich der vier YAMLs im gepackten `.msapp` waren erfolgreich. Der feste diagnostische Suchwert ist im neu gepackten `.msapp` nicht enthalten.
- Repository-Audit sowie die CI von PR #13 und PR #14: erfolgreich am 2026-09-28. Nach weiteren Änderungen ist der aktuelle PR-Head erneut zu prüfen.
- DEV-Import des Pakets `GovernancePortal_1.0.0.30429_1.0.0-alpha.4.1.0.zip` mit `--publish-changes`: erfolgreich. Der anschließende read-only DEV-Export bestätigt Solution `1.0.0.30429`; das exportierte `.msapp` ist bytegleich mit dem importierten Artefakt (SHA-256 `c9261924e0c01fdd351da6c4759510cd45fb2888c917fea4334731fdd6fd6183`).
- Power Apps Studio öffnet den importierten Kandidaten und zeigt die DEV-Metadaten. Die veröffentlichte App startet, lädt die Navigation und öffnet das Asset-Neuanlageformular. Im Personenfeld `Verantwortlich` liefert die Suche nach dem bestehenden DEV-Konto einen auswählbaren Treffer. Das ungespeicherte Testformular wurde verworfen; ein Asset-Save mit Datensatzänderung wurde nicht geprüft. Der Player meldete kurz eine bald verfügbare neue App-Version; nach dem Neuladen startete die App ohne diesen Hinweis. Studio zeigte eine Formelwarnung zu einem Literal-Prädikat. Die vollständige Studio-Abnahme ist noch offen. Provisioning-Apply wurde nicht ausgeführt.

## Primäres nächstes Arbeitspaket

**Stage-4.1-Studio- und DEV-Abnahme:** Studio-Formelwarnung einordnen, die Asset-Speicherung mit einem kontrollierten DEV-Testdatensatz prüfen und bestätigen, dass das diagnostische Label auch im Studio nicht mehr erscheint. Der DEV-Rückexport des importierten Artefakts und ein lesender App-/Personenfeld-Smoke sind abgeschlossen. Erst nach der fachlichen Abnahme die Stage-4.1-Integration von PR #5 entscheiden. Framework-Adoption gemäß Issue #7 folgt separat.
