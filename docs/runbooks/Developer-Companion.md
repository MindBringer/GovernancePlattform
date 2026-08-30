# Runbook – Developer Companion

## Start

macOS/Linux:

```bash
./start-local.sh
```

Windows:

```powershell
.\start-local.ps1
```

Die Launcher laden optional `.env` und starten den Engineering Companion. Standard: `127.0.0.1:8765`. Ist der Companion-Port belegt, wird innerhalb der nächsten 20 Ports ein freier Port gewählt.

## First Run

Ist `project.key == project-template`, zeigt der Companion den First-Run-Wizard. Er erzeugt Projekt-Config, State, Project Memory, project-owned `AGENTS.md`, Roadmap, Known Issues, Release History und ADR-Basis. Die Adapter `tools/companion/project_actions.py`, `tools/companion/project_runtime.py`, `tools/companion/project_ui.py` und `project_web/` bleiben project-owned.

## Bestehendes Repository adoptieren

Framework 1.3.1 unterstützt die sichere Migration eines bereits existierenden Git-Repositories:

```bash
python3 tools/framework/adopt_existing.py \
  --target ../MeinProjekt \
  --key mein-projekt \
  --name "Mein Projekt" \
  --description "Bestehendes Projekt" \
  --version 2.0.0 \
  --port 8765
```

Optionale Module:

```text
--power-platform
--provisioning
```

Der Target-Workspace muss standardmäßig clean sein. Überschriebene Framework-/Bootstrap-Dateien werden unter `.framework-adoption-backup/<timestamp>/` gesichert. Fachliche Dateien außerhalb des Framework-Contracts werden nicht verändert. Anschließend werden Config, State, Framework Lock sowie project-owned Action-/Runtime-/UI-Adapter für das Zielrepository erzeugt.

Seit Framework 1.3.9 dürfen Consumer ihren Framework-Lock nicht mehr direkt neu erzeugen. Ein Versionsdelta ist für rein project-owned Arbeit zulässig; Drift an framework-managed Dateien blockiert dagegen fail-closed. Framework-Änderungen werden zuerst im aktuellen zentralen Template umgesetzt und released.

Kontrollierter Consumer-Sync:

```bash
python3 tools/framework/sync.py check --source /pfad/zum/Project-Engineering-Template
python3 tools/framework/sync.py apply --source /pfad/zum/Project-Engineering-Template
python3 tools/framework/sync.py integrity
```

Ab Framework 1.3.10 meldet `check` zusätzlich Consumer-only Dateien innerhalb framework-managed Flächen als `stale managed`. `apply` sichert sie zusammen mit geänderten managed Dateien unter `.framework-backup/<timestamp>/`, entfernt sie und kopiert anschließend den kanonischen Template-Stand. Explizit project-owned Dateien bleiben unangetastet.

## UI-Bereiche

- **Dashboard** – generischer Engineering-Status, Produktruntime-Health und optionale project-owned Dashboard-Views.
- **Entwicklung** – alle registrierten Actions nach Capability.
- **Konsole** – vollständige lokale Aktionsausgabe und Live-Status laufender Releases.
- **Project Views** – dynamische Navigationseinträge aus `tools/companion/project_ui.py`.

Seit Framework 1.3.10 zeigt die Shell unter jedem Seitentitel eine kurze Bereichsbeschreibung. Dashboard-Statuskarten und Action-Buttons erklären ihre Bedeutung direkt im UI. Der aufklappbare Orientierungsblock auf dem Dashboard beschreibt den normalen Arbeitsweg; das Runbook bleibt Vertiefung und Recovery-Nachweis, nicht Voraussetzung für Alltagsbedienung.

Der Theme-Schalter speichert Hell-/Dunkelmodus im Browser. Ohne gespeicherte Auswahl wird `prefers-color-scheme` des Betriebssystems verwendet.

## Project Runtime

Lokale Produktserver werden in `tools/companion/project_runtime.py` registriert:

```python
from tools.companion.core.project_runtime import ProjectRuntimeSpec


def register_project_runtimes(registry, root, config):
    registry.register(ProjectRuntimeSpec(
        id="product-app",
        label="Product App",
        command=["python3", "scripts/start_product_runtime.py"],
        url="http://127.0.0.1:8765/",
        health_url="http://127.0.0.1:8765/api/health",
        auto_start=True,
        open_browser=True,
        start_timeout=120,
    ))
```

Vertrag:

- `command` ist immer eine Argumentliste; `shell=True` wird nicht verwendet.
- `url` und `health_url` müssen lokale HTTP(S)-URLs auf `127.0.0.1`, `localhost` oder `::1` sein.
- Eine bereits gesunde Runtime wird als extern erkannt und nicht vom Companion beendet.
- Der Companion stoppt ausschließlich Prozesse, die er selbst gestartet hat.
- `auto_start=false` registriert eine Runtime nur für Status/Link, startet sie aber nicht automatisch.
- `open_browser=true` macht die gesunde Produktruntime zum bevorzugten Browserziel; sonst öffnet der Companion sein Engineering-Dashboard.
- Engineering Companion und Produktserver verwenden getrennte Ports.

Status steht in `GET /api/project-runtimes` und zusätzlich in `GET /api/project` unter `projectRuntimes`.

## Parametrisierte Actions

Actions dürfen genau einen sicheren Texteingabewert deklarieren. Dieser wird als einzelnes `subprocess`-Argument über den Platzhalter `{input}` eingesetzt; es findet keine Shell-Interpolation statt. Das eignet sich z. B. für Reset-Tokens oder explizite IDs.

```python
from tools.companion.core.actions import ActionSpec, INPUT_TOKEN

registry.register(ActionSpec(
    id="reset-apply",
    label="Reset anwenden",
    category="Provisioning",
    commands=[["pwsh", "Provisioning/Reset.ps1", "-ConfirmationToken", INPUT_TOKEN]],
    input_label="Reset-Token aus dem Dry Run",
    input_required=True,
    danger=True,
))
```

## Project View anlegen

In `tools/companion/project_ui.py`:

```python
from tools.companion.core.ui_extensions import ProjectViewSpec


def register_project_ui(registry, root, config):
    registry.register(ProjectViewSpec(
        id="project-health",
        label="Projekt",
        title="Projekt-Cockpit",
        dashboard=True,
        refresh_seconds=30,
        provider=lambda: {
            "status": {"label": "Healthy", "level": "good"},
            "metrics": [{"label": "Services", "value": "8/8", "level": "good"}],
            "actions": ["project-selftest"],
        },
    ))
```

Danach Companion neu starten. `dashboard=True` rendert dieselbe View zusätzlich im generischen Dashboard.

### Generic Renderer

Unterstützte Payload-Bausteine:

- `status`: `{label, level, detail}`;
- `metrics`: Liste aus `{label, value, level?, detail?}`;
- `sections` mit `kind=text|list|table`;
- `actions`: Liste registrierter Action-IDs.

Levels: `good`, `warn`, `danger`, `info`, `neutral`.

### Rich UI

Für komplexe Diagramme, Filter oder projektspezifische Interaktion:

1. `ui.projectUI.allowCustomAssets=true`;
2. JavaScript/CSS unter `tools/companion/project_web/` anlegen;
3. `ProjectViewSpec(renderer="custom", script="...js", stylesheet="...css")` registrieren;
4. Renderer über `window.ProjectCompanion.registerRenderer(viewId, fn)` registrieren.

Custom Assets dürfen das `project_web`-Verzeichnis nicht verlassen. Externe URLs werden nicht als Assets registriert.

## Mutationen aus Project UI

Project-View-Provider und `GET /api/project-view/<id>` sind read-only. Für Änderungen immer eine Action in `project_actions.py` registrieren und aus der UI über `context.runAction('id')` bzw. `actions` im Generic Payload aufrufen. Dadurch bleiben Action-Allowlist, CSRF, Confirmation, Console-Output und Auditierbarkeit erhalten.

## Power Platform / PAC

Der Framework-Core stellt generische PAC-/Power-Platform-Actions bereit. Projektspezifische komplexe Workflows – z. B. Solution Export → Unpack → Canvas Sync oder Validate → Build → Import → Publish – gehören als reviewte Projekt-Action in `project_actions.py` und rufen vorhandene Projektwerkzeuge auf.

## Provisioning

Wenn `provisioning.enabled=true`, registriert der Core je nach Config:

```text
Provisioning  DryRun / Validate / Apply
Reset         DryRun / Apply <Token>
Seed          DryRun / Validate / Apply
```

Reset-Apply verwendet einen dynamischen Input; schreibende Aktionen bleiben confirmation-/tokenpflichtig.

## Kernaktionen

- **Framework Integrity** – nicht mutierender Check auf Config-/Manifest-/Lock-Version und alle framework-managed Datei-Hashes.
- **Framework Lock prüfen** – diagnostischer Integrity-/Lock-Check.
- **Framework Lock aktualisieren** – nur im zentralen `project-template`; in Consumern technisch blockiert.
- **Engineering Contract** – Integrity → Audit → Syntax → Technical Debt → Project Memory → Validate → Integrity → Framework Tests.
- **Engineering Build** – reproduzierbarer nicht mutierender Build/Check.
- **Template Bootstrap Smoke** – nur im Template.
- **Altlasten-Sweep & Review**.
- **Projektgedächtnis prüfen**.
- **Repository Policy prüfen**.
- **Release-Artefakte reparieren**.
- **Vollständiger Release** – Candidate → PR/CI → Final → CI → Merge → Tag/GitHub Release.

Die Auswahl **Vollständiger Release** öffnet sofort die Konsole und rendert sie vor der Bestätigungsabfrage. Nach Freigabe läuft der Release als serverseitiger Job. `GET /api/release-job` liefert redigierte Phasenmetadaten, Fortschritt und Laufzeit; die vollständige Prozessausgabe wird nach Abschluss angezeigt. Ein Browser-Refresh nimmt einen laufenden Monitor wieder auf. Für den finalen Handoff kann `iteration.postReleaseNextStep` in `.project/state/current.json` hinterlegt werden; die Engine setzt damit Stage, Next Step und Memory-Marker vor Tag/GitHub Release konsistent um.

## Sicherheitsmodell

- Loopback-only für Engineering Companion und registrierte Produktruntimes.
- POST nur mit CSRF-Token.
- keine Command-Strings aus Browser/Config.
- Actions und Runtimes verwenden Argumentlisten ohne Shell-Ausführung.
- parametrisierte Actions ersetzen nur explizite `{input}`-Argumente.
- project-owned UI schafft keine freien Custom-POST-Routen.
- Project-UI-Assets nur aus festem Repository-Verzeichnis.
- Content-Security-Policy begrenzt Browser-Ressourcen auf denselben lokalen Origin.
- Destruktive Aktionen bleiben bestätigungs- oder tokenpflichtig.

## Chat-/Agent-Handoff

Bei Wiederaufnahme zuerst `.project/framework/AGENT_CONTRACT.md`, danach `AGENTS.md` und `PROJECT_STATE.md` lesen. Falls Project Runtime oder Project UI vorhanden ist, zusätzlich `tools/companion/project_runtime.py`, `tools/companion/project_ui.py` sowie relevante `project_web`-Assets prüfen. Live-Branch und Live-Commit immer aus Git rekonstruieren.
