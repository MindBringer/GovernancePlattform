# IT Governance Portal

Metadatengetriebene Governance-Plattform auf Basis von SharePoint Online, Power Apps Canvas, Power Automate und PowerShell-Provisioning.

## Aktueller Stand

| Teilprodukt | Version | Status |
|---|---:|---|
| SharePoint-Provisioning und Architekturmodell | `6.2.5` | stabile Git-Baseline |
| Canvas App | `1.0.0-alpha.4.1.0` | P0/P1/P2 abgenommen; DEV 30450 / Canvas 204 Live, Studio PA2108. Reparatur 30451 lokal geprüft; P3b offen, Produktion P7 |
| Developer Workflow | `Stage 4.1` | lokales Profil 1.2.0; Framework-PR #6 bleibt isoliert |

Die Versionsreihen bleiben getrennt: `VERSION` beschreibt das Provisioning-Paket, `powerplatform/VERSION` die Canvas-Version. `powerplatform/solution/VERSION` spiegelt die Canvas-Version; die vierteilige Solution-Paketversion steht im Solution-Manifest. Die Stage-4.1-Änderungen sind noch nicht nach `main` integriert; `main` enthält Canvas `1.0.0-alpha.4.0.0`.

**P2-DEV-Abnahme abgeschlossen (07.10.2026): Solution 30449 / Canvas 202 Live und gespeichert.** Der separat freigegebene Save am synthetischen Asset 13 leert alle sechs Choices als native null und erhöht die Version von 16.0 auf 17.0; die übrigen 25 deklarierten Felder bleiben erhalten. Sauberes Wiederöffnen zeigt leere Auswahlen, beide Reviewpicker mit leerem DOM-value und placeholder, „Keine Änderungen“ und gesperrtes Save. Asset 13 anschließend genau einmal reversibel bereinigt und nach Marker, Listenherkunft und ID im ersten Papierkorb nachgewiesen. Der vollständige ursprüngliche Bestand ist wiederhergestellt: Assets 4–7 mit sämtlichen nativen Werten/Versionen unverändert, Systems leer. Der erfolgreiche Create und alle fünf Personenwechsel/-Leerungen sowie Review-/Zyklus-/Boolean-Tests unter 30447 bleiben Teil der P2-Evidenz. Gespeicherter und veröffentlichter Host sind in vier Controls-/DataSources-Dateien bytegleich; 84 kanonische/92 kompilierte Controls, beide echten Suchregeln und 19 unveränderte Quellen geprüft. Formel-/Laufzeitchecker ohne Fehler; 72/12/2 Warnungen bleiben. Native ReviewCycleMonths-Min/Max, Produktivrollen und atomarer ETag-Konfliktschutz bleiben für P7 offen; P2 ist keine Produktivfreigabe. [P2-Vertrag und separate Abnahme](docs/development/Stage-4.1-P2-Asset-Verantwortliche.md).

**P3a Schema-/Referenzbrücke umgesetzt (08.10.2026):** Zwei nicht indizierte Changes-Spalten, 13 neue Metadatenzeilen und ein gezieltes ObjectTypes-Update sind nativ belegt; Geschäftsbestand, 874 andere bestehende Metadatenzeilen, 20 Indizes und Listsettings bleiben erhalten. Die geprüfte Studio-Kopie enthält 20 Quellen und 19 schreibbare Change-Pilotfelder; ausschließlich die erzeugte msapr-Referenz wurde übernommen. Der P3b-Vorcheck bestätigt erstmals gespeichert 203 bei Live 202 und liest Changes direkt im gespeicherten Studio. Beide PAC-Lesewege liefern noch den unveränderten Live-Host 202 als Rückweg. Alle P3a-Kontingente bleiben verbraucht.

**P3b DEV 30450 gestoppt, Reparatur 30451 lokal (08.10.2026):** Der freigegebene einmalige Import von Head `8750c8c56da5a26485e413590ead4264fe247cd0` endet mit PAC Exit 0; Maker zeigt Canvas 204 Live als Plattformfolge. Der Nach-Import-Export ist bytegleich zum freigegebenen msapp, vier Src-YAMLs bytegleich und 20 Quellen erhalten. Studio öffnet die Quelle nicht: PA2108 für `AccessibleLabel` an den beiden neuen `Classic/Button@2.2.0`-Entscheidungsbuttons. Sofortiger Write-Stopp: kein manueller Save, gezieltes Publish oder Change-Save. Vollständiger Nach-/Abschlussvergleich aller sechs Listen erhält sämtliche Werte/Versionen, Spalten und Settings. Die Lesesitzung endet mit Exit 0; Import 1/1, Exporte 3/4, übrige Schreibkontingente 0. Der alte Scope erlaubt keine weiteren Writes oder Retries.

**Lokaler Reparaturkandidat 30451:** Die beiden Zusatzhinweise verwenden das unterstützte `Tooltip`; sichtbarer Text, Tastatur/Fokus und sämtliche Genehmigungs-/Save-Regeln bleiben erhalten. Das vorhandene Accessibility-Gate umfasst jetzt alle drei neuen Change-Buttons und die Change-Galerie; der YAML-Parser weist diese native PA2108-Konstellation für jeden Classic-Button ab. Der alte 30450-Source wird von beiden Prüfungen mit passendem Fehlergrund abgewiesen. 24/24 verfügbare Gates und Pack/Unpack/Solution-Pack Exit 0, 2.948 tatsächliche Power-Fx-Assertions, 66 Formeln und 18 Python-Regressionen; vier YAMLs und eingebettetes msapp bytegleich. 19 Change-Felder und alle 52 Asset-/System-/Change-Patch-Spalten bleiben erhalten. 30451 ist noch nicht importiert oder fachlich nativ abgenommen; Canvas/Provisioning bleiben `1.0.0-alpha.4.1.0` / `6.2.5`.

**P3b · begrenzte DEV-Funktionsabnahme von Reparatur 30451**, Modellklasse `deep-reasoning`, neu konkret freizugeben. Ein zusätzlicher DEV-Import genau dieses geprüften ZIPs ohne Publish All/`--publish-changes`; maximal ein manueller Studio-Save und ein gezieltes App-Publish erst nach erfolgreicher Maker-/Connectorprüfung. Bis zu vier lesende Exportaufnahmen, höchstens drei neue synthetische Changes und acht Edit-Saves für vollständigen genehmigten Lifecycle, fremden Genehmiger ohne Entscheidungs-Save und ausdrückliche Ablehnung; nach jedem Save natives Readback und sauberes Wiederöffnen, danach bis zu drei reversible Papierkorb-Cleanups nur dieser Tests. Bei Fehler/Wertabweichung Readback und Stopp ohne Write-Retry. Keine Bestands-, Asset-, Schema-, Metadaten-, Index-, Rollen- oder Produktionsänderung; kein DEV→Git, Merge oder Release. 30450 bleibt mit seinem tatsächlichen Fehler abgeschlossen; keine automatische Übertragung seiner Restkontingente. P4 folgt nach P3b. Siehe [P3-Vertrag und Freigabegrenzen](docs/development/Stage-4.1-P3-Change.md).

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
