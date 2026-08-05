# IT Governance Portal

Metadatengetriebene Governance-Plattform auf Basis von SharePoint Online, Power Apps Canvas, Power Automate und PowerShell-Provisioning.

## Aktueller Stand

| Teilprodukt | Version | Status |
|---|---:|---|
| SharePoint-Provisioning und Architekturmodell | `6.2.5` | stabile Git-Baseline |
| Canvas App | `1.0.0-alpha.3.6.0` | Stage 3.6 integriert; Person- und Choice-Provider im Test |
| Developer Workflow | `Stage 3.7` | Companion-, Audit- und Git-Pull-Zwischenstufe |

Die Versionsreihen bleiben getrennt: `VERSION` beschreibt das Provisioning-Paket, `powerplatform/VERSION` die Canvas-/Solution-Version. Stage 3.7 verändert den Entwicklungsworkflow, nicht die Canvas-Laufzeitversion.

## Architektur in Kürze

`architecture/*.yaml` ist die führende Quelle für SharePoint-Schema und Runtime-Metadaten. Das Provisioning kompiliert und validiert dieses Modell. Die Canvas-App nutzt die bereitgestellten Runtime-Listen für Navigation, Formulare, Felder, Choices, Lookups und Berechtigungen.

```text
architecture/*.yaml
        │
        ├── provisioning/            SharePoint-Schema, Seed-Daten, Prüfung
        └── powerplatform/
             ├── canvas/             kanonischer Canvas-SourceCode
             ├── solution/           entpackte unmanaged Solution
             └── scripts/            Validierung, Versionierung und Build
```

## Repository-Struktur

| Pfad | Zweck |
|---|---|
| `architecture/` | kanonisches Architektur- und Metadatenmodell |
| `provisioning/` | idempotentes Provisioning, Reset, Export und Tests |
| `powerplatform/canvas/GovernancePortal/` | einziger gültiger Canvas-SourceTree |
| `powerplatform/solution/` | entpackte Power-Platform-Solution |
| `powerplatform/scripts/` | Build-, Pack- und Validierungsskripte |
| `docs/development/` | aktuelle Entwicklungs- und Testdokumentation |
| `docs/archive/` | historische, nicht mehr normative Dokumente |
| `migration/` | aktive Migrationsregeln; ältere Regeln unter `migration/archive/` |
| `tests/` | Pester- und Architekturtests |
| `tools/companion/` | lokale, eingeschränkte Web-GUI für Git-, Audit- und Testaktionen |
| `artifacts/`, `generated/`, `Logs/` | lokale oder reproduzierbare Ausgaben |

## Voraussetzungen

- Git
- PowerShell 7
- Power Platform CLI (`pac`)
- PnP.PowerShell für Provisioning gegen SharePoint Online
- Python 3 für den lokalen Companion
- Berechtigungen für die Zielumgebung und die Governance-Portal-Site

## Lokaler Testablauf

Neue Änderungen werden per Git-Branch bereitgestellt:

```bash
git fetch origin
git switch <branch>
git pull --ff-only
bash ./start-local.sh
```

Der Companion sucht automatisch einen freien Port ab `8770`, öffnet den Browser und stellt Status, Fetch, Pull, Repository-Audit, Connectorprüfung, Canvas-Validierung und Build bereit. Freie Shell-Kommandos sind nicht möglich.

Ohne Companion:

```powershell
pwsh ./provisioning/Scripts/Test-PowerShellSyntax.ps1
pwsh ./provisioning/Scripts/Test-Architecture.ps1
pwsh ./provisioning/Scripts/Test-ArchitectureConsistency.ps1
pwsh ./powerplatform/scripts/Build.ps1
```

Build-Ausgaben entstehen unter `artifacts/` und gehören nicht in Git.

## Verbindliche Dokumente

- [Canvas Stage 3.6](docs/development/Stage-3.6.md)
- [Developer Companion Stage 3.7](docs/development/Stage-3.7-Developer-Companion.md)
- [Lokaler Git-/Test-Workflow](docs/development/Local-Companion-Workflow.md)
- [Canvas-SourceCode-Migration](MIGRATION.md)
- [Änderungshistorie](CHANGELOG.md)

## Arbeitsregeln

1. Änderungen erfolgen in Feature- oder Fix-Branches und werden über Pull Requests nach `main` übernommen.
2. Es gibt genau einen Canvas-SourceTree: `powerplatform/canvas/GovernancePortal`.
3. Maker-Portal-Änderungen werden exportiert, entpackt, validiert und gegen Git geprüft.
4. Lokale Tests beginnen mit `git fetch` und `git pull --ff-only`; ZIP-basierte Quellcodeübernahmen entfallen.
5. `start-local.sh` wird über `bash` gestartet; ein lokales `chmod` ist nicht erforderlich.
6. Provisioning bleibt idempotent; produktive Bibliotheksinhalte dürfen nicht unbeabsichtigt gelöscht werden.
7. Historische Pakete, Logs und Zwischenstände werden nicht im aktiven Quellbaum abgelegt.
