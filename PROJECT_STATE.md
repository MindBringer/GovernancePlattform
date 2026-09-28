# Projektübergabe – GovernancePlattform

Stand: 2026-09-28 · Produktzweig: `feature/canvas-stage-4.1-provider-engine` · Ausgangs-HEAD: `ff74201a6ac6039942e0f6915702531f0ff1db57`

## Aktueller Kandidat

- Provisioning `6.2.5`; Canvas `1.0.0-alpha.4.1.0`; Solution-Manifest `1.0.0.30409`.
- Stage 4.1 synchronisiert die neun registrierten Provider in `App.pa.yaml` und bindet `gblActiveProvider` an die Objektauswahl. Asset und System haben Edit/Save; die sieben übrigen Provider melden dafür weiterhin `false`.
- Das Companion-Profil 1.2.0 stammt aus dem Engineering-Template. Ein vollständiger Framework-Consumer-Vertrag ist noch nicht integriert; PR #6 bleibt isolierter Konformitätsnachweis.
- Die NIS2-Roadmap von `main` ist in diesem Zweig enthalten und um Stage 4.1/4.2 und die spätere Framework-Adoption ergänzt.

## Verifikation dieses Arbeitspakets

- PowerShell-Syntax, Architekturcompiler und Architektur-Konsistenz: erfolgreich.
- Canvas-Version/Quellen, Provider-Registry und synchronisierte Runtime: erfolgreich.
- Lokaler vollständiger PAC-Build mit `-SkipVersionSync -SkipSolutionIncrement`: erfolgreich; Canvas- und Solution-Pakete erzeugt.
- Repository-Audit: erfolgreich. Die GitHub-CI enthält nun nicht mutierende Canvas-/Provider-Prüfungen; der neue CI-Kandidat braucht nach Push einen erfolgreichen Lauf.
- Power Apps Studio, DEV-Smoke, Tenant-Import und Provisioning-Apply: nicht ausgeführt. PAC weist darauf hin, dass die gepackte YAML-Canvas-App vor der Verwendung in Power Apps Studio geöffnet und validiert werden muss.

## Primäres nächstes Arbeitspaket

**Stage-4.1-DEV-Baseline und Abnahme:** aktuellen Studio-/DEV-Stand mit dem Git-Kandidaten abgleichen, Änderungen als überprüften Diff übernehmen, vollständigen Build und Studio-/DEV-Smoke dokumentieren. Erst danach die fachliche Stage-4.1-Integration von PR #5 entscheiden. Framework-Adoption gemäß Issue #7 folgt separat.
