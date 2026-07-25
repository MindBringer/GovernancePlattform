# Repository-Bereinigung

## Durchgeführte Bereinigung

| Pfad | Entscheidung | Begründung |
|---|---|---|
| `gp_governanceportal_c93a1/` | entfernt | zweiter, abweichender Canvas-SourceTree; kanonisch ist `powerplatform/canvas/GovernancePortal` |
| `.gitignore.additions` | entfernt | Integrationsrest; Regeln gehören direkt in `.gitignore` |
| `README-APPLY-alpha.2.2.md` | entfernt | historische Paket-Anweisung |
| `README-APPLY-alpha.3.0.md` | entfernt | historische Paket-Anweisung |
| `docs/CHANGELOG.md` | entfernt | konkurrierender Changelog; Root-`CHANGELOG.md` ist kanonisch |
| `docs/PACKAGE-INVENTORY.txt` | entfernt | veraltetes Paketinventar statt dauerhafter Projektdokumentation |
| `docs/V6-ARCHITECTURE.md` | entfernt | identisch zu altem `docs/README.md`; Inhalte in `Architecture.md` konsolidiert |
| `docs/Development-Iteration.md` | archiviert | historischer Prozessstand |
| `docs/iterations/*` | archiviert | abgeschlossene Iterationsprotokolle |
| `docs/MIGRATION-v4-v5.md` | archiviert | historische Migration |
| `migration/ARCHIVE-v4-to-v5.yaml` | archiviert | alte, nicht aktive Regel |

## Kanonische Pfade

- Architekturdefinitionen: `architecture/`
- Canvas SourceCode: `powerplatform/canvas/GovernancePortal/`
- Solution Source: `powerplatform/solution/`
- aktuelle Dokumentation: `docs/`
- historische Dokumentation: `docs/archive/`
- aktive Migrationen: `migration/`
- historische Migrationen: `migration/archive/`

## Noch manuell zu prüfen

1. Ob `powerplatform/solution/CanvasApps/*DocumentUri.msapp` als reproduzierbares Build-Input dauerhaft versioniert werden soll. Der aktuelle Build ersetzt diese Datei; für einen vollständig sourcebasierten Workflow könnte sie aus Git entfernt werden, sofern der Pack-Prozess ohne Baseline-Binary zuverlässig funktioniert.
2. Ob sämtliche Environment-Variable-Definitionen in der Solution tatsächlich verwendet werden. Die vielen SharePoint-Definitionen können legitim aus Connector-Bindings stammen; nicht ohne Solution-Importtest löschen.
3. Ob `architecture/cleanup.yaml` noch aktive Reset-Regeln enthält oder nur eine historische Zwischenstufe darstellt.
4. Ob `MIGRATION.md` nach erfolgreicher Umstellung auf SourceCode langfristig in `docs/archive/migrations/` verschoben werden kann.

## Dauerhafte Regeln

- Keine Release-ZIPs, Logs, Screenshots oder exportierten CSV/JSON-Berichte im Repository-Root.
- Keine nummerierten Kopien (`Datei(1)`, `Datei(2)`) committen.
- Abgeschlossene Iterationsprotokolle vierteljährlich nach `docs/archive/iterations/` verschieben.
- Löschungen an Solution-Komponenten nur nach erfolgreichem Pack-, Import- und Smoke-Test.
