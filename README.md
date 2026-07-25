# IT Governance Portal

Metadatengetriebene Governance-Plattform auf Basis von SharePoint Online, Power Apps Canvas, Power Automate und PowerShell-Provisioning.

## Aktueller Stand

| Teilprodukt | Version | Status |
|---|---:|---|
| SharePoint-Provisioning und Architekturmodell | `6.2.5` | stabile Git-Baseline |
| Canvas App | `1.0.0-alpha.3.4.1` | Stage 3.4.1 abgeschlossen; Stage 3.5 in Arbeit |

Die beiden Versionsreihen sind bewusst getrennt: `VERSION` beschreibt das Provisioning-Paket, `powerplatform/VERSION` die Canvas-/Solution-Version.

## Architektur in Kürze

`architecture/*.yaml` ist die führende Quelle für das physische SharePoint-Schema und die Runtime-Metadaten. Das Provisioning kompiliert und validiert dieses Modell. Die Canvas-App verwendet die bereitgestellten Runtime-Listen für Navigation, Formulare, Felder, Choices, Lookups und Berechtigungen.

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
| `docs/` | aktuelle Architektur-, Entwicklungs- und Betriebsdokumentation |
| `docs/archive/` | historische, nicht mehr normative Dokumente |
| `migration/` | aktive Migrationsregeln; ältere Regeln unter `migration/archive/` |
| `tests/` | Pester- und Architekturtests |
| `artifacts/`, `generated/`, `Logs/` | reproduzierbare beziehungsweise lokale Ausgaben |

## Voraussetzungen

- PowerShell 7
- Power Platform CLI (`pac`)
- PnP.PowerShell für Provisioning gegen SharePoint Online
- Berechtigungen für die Zielumgebung und die Governance-Portal-Site

## Validierung und Build

```powershell
# Architektur und Provisioning prüfen
pwsh ./provisioning/Scripts/Test-PowerShellSyntax.ps1
pwsh ./provisioning/Scripts/Test-Architecture.ps1
pwsh ./provisioning/Scripts/Test-ArchitectureConsistency.ps1

# Canvas SourceCode und Solution bauen
pwsh ./powerplatform/scripts/Build.ps1
```

Build-Ausgaben entstehen unter `artifacts/` und gehören nicht in Git.

## Verbindliche Dokumente

- [Architektur](docs/Architecture.md)
- [Roadmap](docs/Roadmap.md)
- [Entwicklungs- und Build-Prozeduren](docs/Development-Prozeduren.md)
- [Coding Standards](docs/CodingStandards.md)
- [Repository-Bereinigung und Archivregeln](docs/Repository-Cleanup.md)
- [Canvas-SourceCode-Migration](MIGRATION.md)
- [Änderungshistorie](CHANGELOG.md)

## Arbeitsregeln

1. Änderungen erfolgen in Feature-Branches und werden über Pull Requests nach `main` übernommen.
2. Es gibt genau einen Canvas-SourceTree: `powerplatform/canvas/GovernancePortal`.
3. Maker-Portal-Änderungen werden vor dem Merge exportiert, entpackt, validiert und gegen Git geprüft.
4. Provisioning bleibt idempotent; produktive Bibliotheksinhalte dürfen durch Reset oder Migration nicht unbeabsichtigt gelöscht werden.
5. Historische Pakete, Logs und Zwischenstände werden nicht im aktiven Quellbaum abgelegt.
