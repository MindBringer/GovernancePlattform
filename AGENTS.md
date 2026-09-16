# Agent / Assistant Working Contract – GovernancePlattform

Die framework-weit gültigen Regeln stehen in `.project/framework/AGENT_CONTRACT.md`. Dieses Dokument ist project-owned und enthält projektspezifische Ergänzungen.

## Migration

- Projekt: **GovernancePlattform** (`governance-platform`)
- Engineering Framework: **1.3.12**
- Bestehende fachliche Architektur und Projektdateien bleiben erhalten.
- Framework-managed Dateien werden ausschließlich über Framework-Sync aktualisiert.
- Projektspezifische Actions gehören in `tools/companion/project_actions.py`.
- Lokale Produktserver gehören als code-reviewte Argumentlisten in `tools/companion/project_runtime.py`.
- Projektspezifische Cockpit-Views gehören in `tools/companion/project_ui.py`.

## Einstieg

`.project/framework/AGENT_CONTRACT.md` → `PROJECT_STATE.md` → `.project/project.config.json` → Live-Git/PR/CI → relevante Projekt-Doku.
