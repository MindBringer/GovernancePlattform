# Projektübergabe – GovernancePlattform

Stand: 2026-09-28 · Arbeitszweig: `codex/stage-4.1-dev-baseline` auf `codex/stage-4.1-sync` (`0f0070d`); fachlicher Zielzweig: `feature/canvas-stage-4.1-provider-engine`

## Aktueller Kandidat

- Provisioning `6.2.5`; Canvas `1.0.0-alpha.4.1.0`; Solution-Manifest `1.0.0.30430`. Dieses Paket ist mit Freigabe in DEV importiert; Canvas-Version 165 ist laut Power-Apps-Versionsliste `Live`. Version 164 aus dem vorherigen Import blieb gespeichert, aber nicht live. DEV-Exportbasis vor dem ersten Import war `1.0.0.30428`.
- Stage 4.1 synchronisiert die neun registrierten Provider in `App.pa.yaml` und bindet `gblActiveProvider` an die Objektauswahl. Asset und System haben Edit/Save; die sieben übrigen Provider melden dafür weiterhin `false`.
- Das Companion-Profil 1.2.0 stammt aus dem Engineering-Template. Ein vollständiger Framework-Consumer-Vertrag ist noch nicht integriert; PR #6 bleibt isolierter Konformitätsnachweis.
- Ein read-only PAC-Export aus DEV bestätigte am 2026-09-28: Die vier Canvas-YAMLs stimmen mit dem fachlichen Reconciliation-Commit `dec366c` im isolierten Conformance-Branch überein. Die DEV-Solution trägt Version `1.0.0.30428`.
- Der neuere DEV-Stand für Personenfelder und Asset-Speichern wurde übernommen. Das diagnostische Label wurde aus dem SourceTree und der Pack-Baseline entfernt; im Kandidaten `30430` fehlen auch die internen Control- und App-Checker-Referenzen. Ein konstantes, warnendes Filter-Prädikat wurde durch eine leere Tabellen-Auswahl ersetzt. Die übrigen umgebungsspezifischen Solution-Dateien wurden nicht pauschal übernommen.
- Die NIS2-Roadmap von `main` ist enthalten und um Stage 4.1/4.2 und die spätere Framework-Adoption ergänzt.

## Verifikation dieses Arbeitspakets

- PowerShell-Syntax, Architekturcompiler und Architektur-Konsistenz: erfolgreich. Die Pester-Suite konnte lokal mangels installiertem Pester-Modul nicht ausgeführt werden; der direkte Skriptaufruf ist kein gültiger Pester-Lauf.
- Canvas-Version/Quellen, Provider-Registry und synchronisierte Runtime: erfolgreich.
- Lokaler vollständiger PAC-Build mit Solution-Inkrement auf `1.0.0.30430`: erfolgreich; Canvas- und Solution-Pakete erzeugt. Der SourceCode-Round-Trip und der Vergleich der vier YAMLs im gepackten `.msapp` waren erfolgreich. Der diagnostische Control-Name und veraltete Literal-Prädikat-Warnungen sind in allen Archivteilen des Kandidaten entfernt.
- Repository-Audit: erfolgreich. `pac canvas validate` ist in PAC `2.9.3` nicht mehr unterstützt; die Projekt-Canvas-Validierung und der vollständige PAC-Pack liefen erfolgreich. Die drei CI-Prüfungen von PR #14 waren am Kandidaten-Head `a73560b` erfolgreich.
- DEV-Import des Pakets `GovernancePortal_1.0.0.30429_1.0.0-alpha.4.1.0.zip` mit `--publish-changes`: erfolgreich. Der anschließende read-only DEV-Export bestätigt Solution `1.0.0.30429`; das exportierte `.msapp` ist bytegleich mit dem importierten Artefakt (SHA-256 `c9261924e0c01fdd351da6c4759510cd45fb2888c917fea4334731fdd6fd6183`). Die Power-Apps-Versionsliste zeigt jedoch Canvas-Version 164 nur als gespeichert und Version 163 als `Live`: `--publish-changes` hat die Canvas-App nicht live geschaltet.
- Nach separater Freigabe wurde `GovernancePortal_1.0.0.30430_1.0.0-alpha.4.1.0.zip` mit `--publish-changes` erfolgreich nach DEV importiert. Der anschließende read-only DEV-Export bestätigt Solution `1.0.0.30430` und ein bytegleiches `.msapp` (SHA-256 `2edcdb3de5942a5fcd0022c372162143866dcd453d9b6798fa6106c3a36c75b1`). Die Versionsliste markiert die neue Canvas-Version 165 als `Live`; eine weitere Studio-Veröffentlichung war daher nicht nötig.
- Power Apps Studio öffnet Version 165 im Bearbeitungsmodus. Auf dem gewählten Bildschirm meldet die Formelleiste `Keine Formelfehler vorhanden`; die App-Überprüfung selbst ließ sich über die Browsersteuerung nicht öffnen und ist daher nicht live abgenommen. Der gepackte Kandidat enthält weder das diagnostische Control noch die veraltete Literal-Prädikat-Warnung. Die laufende Version 165 startet, lädt Navigation, 16 Objekttypen und 12 Seiten und zeigt im Bereich Governance die Asset-, System- und Kontakt-Kacheln. Das Asset-Neuanlageformular wurde auf Version 165 nicht erreicht; der frühere Personenfeld-Smoke bezog sich ausschließlich auf Version 163. Der direkte Zugriff auf die SharePoint-Asset-Liste endete mit `Access denied`; ein Testdatensatz wurde deshalb mangels verlässlicher Bereinigung nicht angelegt. Provisioning-Apply wurde nicht ausgeführt.

## Primäres nächstes Arbeitspaket

**Stage-4.1-DEV-Funktionsabnahme:** In Studio die vollständige App-Überprüfung für die nun live geschaltete Version 165 sichten. Danach das Asset-Neuanlageformular und den Personenfeld-Picker auf Version 165 prüfen und die Asset-Speicherung mit einem kontrollierten DEV-Testdatensatz erst testen, wenn ein Bereinigungsweg gesichert ist. PR #14 bleibt bis dahin Draft; erst nach fachlicher Abnahme die Stage-4.1-Integration von PR #5 entscheiden. Framework-Adoption gemäß Issue #7 folgt separat.
