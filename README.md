# IT Governance Portal

Metadatengetriebene Governance-Plattform auf Basis von SharePoint Online, Power Apps Canvas, Power Automate und PowerShell-Provisioning.

## Aktueller Stand

| Teilprodukt | Version | Status |
|---|---:|---|
| SharePoint-Provisioning und Architekturmodell | `6.2.5` | stabile Git-Baseline |
| Canvas App | `1.0.0-alpha.4.1.0` | P0/P1/P2 in DEV abgenommen; 30449 / Canvas 202 Live. P3b 30450 lokal geprüft, DEV-Abnahme offen; Produktion P7 |
| Developer Workflow | `Stage 4.1` | lokales Profil 1.2.0; Framework-PR #6 bleibt isoliert |

Die Versionsreihen bleiben getrennt: `VERSION` beschreibt das Provisioning-Paket, `powerplatform/VERSION` die Canvas-Version. `powerplatform/solution/VERSION` spiegelt die Canvas-Version; die vierteilige Solution-Paketversion steht im Solution-Manifest. Die Stage-4.1-Änderungen sind noch nicht nach `main` integriert; `main` enthält Canvas `1.0.0-alpha.4.0.0`.

**P2-DEV-Abnahme abgeschlossen (07.10.2026): Solution 30449 / Canvas 202 Live und gespeichert.** Der separat freigegebene Save am synthetischen Asset 13 leert alle sechs Choices als native null und erhöht die Version von 16.0 auf 17.0; die übrigen 25 deklarierten Felder bleiben erhalten. Sauberes Wiederöffnen zeigt leere Auswahlen, beide Reviewpicker mit leerem DOM-value und placeholder, „Keine Änderungen“ und gesperrtes Save. Asset 13 anschließend genau einmal reversibel bereinigt und nach Marker, Listenherkunft und ID im ersten Papierkorb nachgewiesen. Der vollständige ursprüngliche Bestand ist wiederhergestellt: Assets 4–7 mit sämtlichen nativen Werten/Versionen unverändert, Systems leer. Der erfolgreiche Create und alle fünf Personenwechsel/-Leerungen sowie Review-/Zyklus-/Boolean-Tests unter 30447 bleiben Teil der P2-Evidenz. Gespeicherter und veröffentlichter Host sind in vier Controls-/DataSources-Dateien bytegleich; 84 kanonische/92 kompilierte Controls, beide echten Suchregeln und 19 unveränderte Quellen geprüft. Formel-/Laufzeitchecker ohne Fehler; 72/12/2 Warnungen bleiben. Native ReviewCycleMonths-Min/Max, Produktivrollen und atomarer ETag-Konfliktschutz bleiben für P7 offen; P2 ist keine Produktivfreigabe. [P2-Vertrag und separate Abnahme](docs/development/Stage-4.1-P2-Asset-Verantwortliche.md).

**P3a Schema-/Referenzbrücke umgesetzt, P3b lokal geprüft (08.10.2026):** Zwei nicht indizierte Changes-Spalten, 13 neue Metadatenzeilen und ein gezieltes ObjectTypes-Update sind nativ zurückgelesen. Alle bisherigen Geschäftswerte/Versionen, 874 andere bestehende Metadatenzeilen, 20 Indizes und Listsettings bleiben erhalten. Studio hat Changes über die bestehende Verbindung hinzugefügt; der einmalige App-Kopie-Export enthält 20 Quellen und 19 schreibbare Change-Pilotfelder. Ausschließlich die erzeugte msapr-Referenz wurde übernommen; alle 19 bisherigen Quellen und Bindungen sowie die bisherigen Regeln bleiben erhalten. Ein manueller Save wurde ausgelöst und Studio meldete „Alle Änderungen wurden gespeichert“; Maker zeigt weiterhin gespeichert/Live 202. Eine neue gespeicherte Hostversion ist daher nicht belegt.

**Lokaler App-Kandidat 30450:** Change-Liste, Titel-/ID-Suche, Laden, New/Edit/Save für genau 19 Felder und explizites Genehmigen/Ablehnen sind implementiert; die vier Change-Capabilities sind nach Offline-Prüfung aktiviert. 24/24 verfügbare Gates und Pack/Unpack/Solution-Pack Exit 0, 2.948 tatsächliche Power-Fx-Assertions (2.032 Record / 212 Choice / 137 Capability / 567 Change), 66 Formeln und 15 Python-Regressionen. Vier YAMLs sowie eingebettetes Solution-msapp bytegleich. Der lokale Kandidat wurde noch nicht importiert oder fachlich in DEV abgenommen. Canvas-/Provisioningversion bleiben `1.0.0-alpha.4.1.0` / `6.2.5`.

**P3b · begrenzte DEV-Funktionsabnahme von Solution 30450**, Modellklasse `deep-reasoning`, separat freizugeben. Ein DEV-Import ohne Publish All/`--publish-changes`, ein manueller Studio-Save und ein gezieltes App-Publish; bis zu vier lesende Exportaufnahmen über ignoriertes Staging. Anschließend höchstens drei synthetische Change-Creates und acht Change-Edits: vollständiger genehmigter Lifecycle, gesperrte Entscheidung bei fremdem Genehmiger und Ablehnung. Nach jedem Save native Feld-/Versionsprüfung und sauberes Wiederöffnen; anschließend bis zu drei reversible Papierkorb-Cleanups nur dieser neu erzeugten Changes. Keine Bestands-, Asset-, Schema-, Metadaten-, Index-, Rollen- oder Produktionsänderung. Bei Fehler/Wertabweichung readback und Stopp ohne Write-Retry. Die P3a-Kontingente sind verbraucht. Der Import kann als Plattformfolge den DEV-App-Host umstellen; sein tatsächlicher gespeicherter/Live-Stand wird geprüft. P4 folgt nach diesem Paket. Siehe [P3-Vertrag und Freigabegrenzen](docs/development/Stage-4.1-P3-Change.md).

## Architektur in Kürze

`architecture/*.yaml` ist die führende Quelle für SharePoint-Schema und Runtime-Metadaten. Das Provisioning kompiliert und validiert dieses Modell. Die Canvas-App nutzt die bereitgestellten Runtime-Listen für Navigation, Formulare, Felder, Choices, Lookups und Berechtigungen.

```text
architecture/*.yaml
        │
        ├── provisioning/            SharePoint-Schema, Seed-Daten, Prüfung
        └── powerplatform/
             ├── canvas/             kanonischer Canvas-SourceCode
             ├── solution/           entpackte unmanaged Solution
             ├── config/             Object-Provider-Registry
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
- Python 3 für den lokalen Companion und PyYAML aus `tools/companion/requirements-validation.txt` für die Canvas-YAML-Prüfung
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
- [Runtime Provider Engine Stage 4.1](docs/development/Stage-4.1-Provider-Engine.md)
- [P1-Datensatzkern und konkrete DEV-Abnahme](docs/development/Stage-4.1-P1-Datensatzkern.md)
- [P2 Asset, Verantwortliche und konkrete DEV-Abnahme](docs/development/Stage-4.1-P2-Asset-Verantwortliche.md)
- [PAC-Workflow](docs/development/PAC-Companion-Workflow.md)
- [Roadmap](docs/ROADMAP.md)
- [Aktuelle Projektübergabe](PROJECT_STATE.md)
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
