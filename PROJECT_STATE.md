# Projektübergabe – GovernancePlattform

Stand: 2026-09-28 · Arbeitszweig: `codex/stage-4.1-dev-baseline` auf `codex/stage-4.1-sync` (`0f0070d`); fachlicher Zielzweig: `feature/canvas-stage-4.1-provider-engine`

## Aktueller Kandidat

- Provisioning `6.2.5`; Canvas `1.0.0-alpha.4.1.0`; Solution-Manifest `1.0.0.30428`.
- Stage 4.1 synchronisiert die neun registrierten Provider in `App.pa.yaml` und bindet `gblActiveProvider` an die Objektauswahl. Asset und System haben Edit/Save; die sieben übrigen Provider melden dafür weiterhin `false`.
- Das Companion-Profil 1.2.0 stammt aus dem Engineering-Template. Ein vollständiger Framework-Consumer-Vertrag ist noch nicht integriert; PR #6 bleibt isolierter Konformitätsnachweis.
- Ein read-only PAC-Export aus DEV bestätigte am 2026-09-28: Die vier Canvas-YAMLs stimmen mit dem fachlichen Reconciliation-Commit `dec366c` im isolierten Conformance-Branch überein. Die DEV-Solution trägt Version `1.0.0.30428`.
- Der neuere DEV-Stand für Personenfelder und Asset-Speichern wurde übernommen. Ein diagnostisches Label mit festem Suchwert wurde aus dem SourceTree entfernt; die gepackte App wurde lokal neu erzeugt. Die übrigen umgebungsspezifischen Solution-Dateien wurden nicht pauschal übernommen.
- Die NIS2-Roadmap von `main` ist enthalten und um Stage 4.1/4.2 und die spätere Framework-Adoption ergänzt.

## Verifikation dieses Arbeitspakets

- PowerShell-Syntax, Architekturcompiler und Architektur-Konsistenz: erfolgreich.
- Canvas-Version/Quellen, Provider-Registry und synchronisierte Runtime: erfolgreich.
- Lokaler vollständiger PAC-Build mit `-SkipVersionSync -SkipSolutionIncrement`: erfolgreich; Canvas- und Solution-Pakete erzeugt. Der SourceCode-Round-Trip und der Vergleich der vier YAMLs im gepackten `.msapp` waren erfolgreich.
- Repository-Audit sowie die CI von PR #13 und PR #14: erfolgreich am 2026-09-28. Nach weiteren Änderungen ist der aktuelle PR-Head erneut zu prüfen.
- Power Apps Studio, DEV-Smoke, Tenant-Import und Provisioning-Apply: nicht ausgeführt. PAC weist darauf hin, dass die gepackte YAML-Canvas-App in Power Apps Studio geöffnet und validiert werden muss. Der PAC-Pack kann ältere interne Steuerdaten aus `.msapr` behalten; nur die YAML-Gleichheit belegt noch keine Studio-Abnahme.

## Primäres nächstes Arbeitspaket

**Stage-4.1-Studio- und DEV-Abnahme:** den bereinigten Kandidaten in Power Apps Studio öffnen, die Personen-/Asset-Funktionen prüfen und das diagnostische Label auch aus dem Studio-Binary entfernen; anschließend DEV-Smoke und erneuten DEV→Git-Export dokumentieren. Erst danach die fachliche Stage-4.1-Integration von PR #5 entscheiden. Framework-Adoption gemäß Issue #7 folgt separat.
