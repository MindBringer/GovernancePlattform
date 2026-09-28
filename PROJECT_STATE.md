# Projektübergabe – GovernancePlattform

Stand: 2026-09-28 · Arbeitszweig: `codex/stage-4.1-dev-baseline` auf `codex/stage-4.1-sync` (`0f0070d`); fachlicher Zielzweig: `feature/canvas-stage-4.1-provider-engine`

## Aktueller Kandidat

- Provisioning `6.2.5`; Canvas `1.0.0-alpha.4.1.0`; Solution-Manifest `1.0.0.30430` (neuer lokaler Kandidat). In DEV ist `1.0.0.30429` importiert, aber die zugehörige Canvas-Version 164 ist noch nicht live; Version 163 ist live. DEV-Exportbasis vor dem ersten Import war `1.0.0.30428`.
- Stage 4.1 synchronisiert die neun registrierten Provider in `App.pa.yaml` und bindet `gblActiveProvider` an die Objektauswahl. Asset und System haben Edit/Save; die sieben übrigen Provider melden dafür weiterhin `false`.
- Das Companion-Profil 1.2.0 stammt aus dem Engineering-Template. Ein vollständiger Framework-Consumer-Vertrag ist noch nicht integriert; PR #6 bleibt isolierter Konformitätsnachweis.
- Ein read-only PAC-Export aus DEV bestätigte am 2026-09-28: Die vier Canvas-YAMLs stimmen mit dem fachlichen Reconciliation-Commit `dec366c` im isolierten Conformance-Branch überein. Die DEV-Solution trägt Version `1.0.0.30428`.
- Der neuere DEV-Stand für Personenfelder und Asset-Speichern wurde übernommen. Das diagnostische Label wurde aus dem SourceTree und der Pack-Baseline entfernt; im Kandidaten `30430` fehlen auch die internen Control- und App-Checker-Referenzen. Ein konstantes, warnendes Filter-Prädikat wurde durch eine leere Tabellen-Auswahl ersetzt. Die übrigen umgebungsspezifischen Solution-Dateien wurden nicht pauschal übernommen.
- Die NIS2-Roadmap von `main` ist enthalten und um Stage 4.1/4.2 und die spätere Framework-Adoption ergänzt.

## Verifikation dieses Arbeitspakets

- PowerShell-Syntax, Architekturcompiler und Architektur-Konsistenz: erfolgreich. Die Pester-Suite konnte lokal mangels installiertem Pester-Modul nicht ausgeführt werden; der direkte Skriptaufruf ist kein gültiger Pester-Lauf.
- Canvas-Version/Quellen, Provider-Registry und synchronisierte Runtime: erfolgreich.
- Lokaler vollständiger PAC-Build mit Solution-Inkrement auf `1.0.0.30430`: erfolgreich; Canvas- und Solution-Pakete erzeugt. Der SourceCode-Round-Trip und der Vergleich der vier YAMLs im gepackten `.msapp` waren erfolgreich. Der diagnostische Control-Name und veraltete Literal-Prädikat-Warnungen sind in allen Archivteilen des Kandidaten entfernt.
- Repository-Audit: erfolgreich. `pac canvas validate` ist in PAC `2.9.3` nicht mehr unterstützt; die Projekt-Canvas-Validierung und der vollständige PAC-Pack liefen erfolgreich. Die drei CI-Prüfungen von PR #14 waren am Kandidaten-Head `c1d451f` erfolgreich.
- DEV-Import des Pakets `GovernancePortal_1.0.0.30429_1.0.0-alpha.4.1.0.zip` mit `--publish-changes`: erfolgreich. Der anschließende read-only DEV-Export bestätigt Solution `1.0.0.30429`; das exportierte `.msapp` ist bytegleich mit dem importierten Artefakt (SHA-256 `c9261924e0c01fdd351da6c4759510cd45fb2888c917fea4334731fdd6fd6183`). Die Power-Apps-Versionsliste zeigt jedoch Canvas-Version 164 nur als gespeichert und Version 163 als `Live`: `--publish-changes` hat die Canvas-App nicht live geschaltet.
- Power Apps Studio öffnet die DEV-App und zeigt die DEV-Metadaten. Die laufende App (Version 163) startet, lädt die Navigation und öffnet das Asset-Neuanlageformular. Im Personenfeld `Verantwortlich` liefert die Suche nach dem bestehenden DEV-Konto einen auswählbaren Treffer. Das ungespeicherte Testformular wurde verworfen. Studio zeigte eine Formelwarnung zu einem Literal-Prädikat; der lokale Kandidat `30430` beseitigt deren Quelle, wurde aber noch nicht in Studio geprüft oder nach DEV importiert. Studio ist aktuell schreibgeschützt, da eine andere Bearbeitungssitzung die App kontrolliert. Der direkte Zugriff auf die SharePoint-Asset-Liste endete mit `Access denied`; ein Testdatensatz wurde deshalb mangels verlässlicher Bereinigung nicht angelegt. Provisioning-Apply wurde nicht ausgeführt.

## Primäres nächstes Arbeitspaket

**Stage-4.1-Studio- und DEV-Abnahme:** Die Studio-Bearbeitungssperre klären. Den bereinigten Kandidaten `30430` erst nach separater Freigabe importieren, im Studio auf Control-Freiheit sowie Formelwarnungen prüfen und dann die Canvas-Version ausdrücklich veröffentlichen. Die ältere, noch nicht live geschaltete Version 164 nicht zwischenzeitlich veröffentlichen. Die Asset-Speicherung mit einem kontrollierten DEV-Testdatensatz erst testen, wenn ein Bereinigungsweg gesichert ist. Erst nach der fachlichen Abnahme die Stage-4.1-Integration von PR #5 entscheiden. Framework-Adoption gemäß Issue #7 folgt separat.
