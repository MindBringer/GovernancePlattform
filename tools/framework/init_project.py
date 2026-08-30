#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / ".project/project.config.json"
STATE = ROOT / ".project/state/current.json"
VERSION = ROOT / "VERSION"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a repository created from Project Engineering Template")
    parser.add_argument("--key", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--power-platform", action="store_true")
    parser.add_argument("--provisioning", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    if data.get("project", {}).get("key") != "project-template" and not args.force:
        raise SystemExit("Repository ist bereits initialisiert. Für bewusstes Überschreiben --force verwenden.")
    framework_version = str(data.get("frameworkVersion") or "unknown")

    data["project"].update({"key": args.key, "name": args.name, "description": args.description, "versionFile": "VERSION"})
    data["companion"]["port"] = args.port
    data["modules"]["powerPlatform"] = bool(args.power_platform)
    data["modules"]["provisioning"] = bool(args.provisioning)
    data["powerPlatform"]["enabled"] = bool(args.power_platform)
    data["provisioning"]["enabled"] = bool(args.provisioning)
    ui = data.setdefault("ui", {})
    project_ui = ui.setdefault("projectUI", {})
    project_ui.setdefault("enabled", True)
    project_ui.setdefault("allowCustomAssets", True)
    release = data.get("release", {}) if isinstance(data.get("release"), dict) else {}
    release["gates"] = [str(gate) for gate in release.get("gates", []) if str(gate) != "bootstrap-smoke"]
    data["release"] = release
    CONFIG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    now = datetime.now(timezone.utc)
    next_id = "project-adapters-runtime-cockpit-and-gates"
    next_description = "Projektadapter, lokale Produktruntime, Project Cockpit, Build-/Test-Gates und optionale Module konfigurieren"
    state = {
        "schemaVersion": 2,
        "frameworkVersion": framework_version,
        "projectVersion": args.version,
        "developmentMode": "initialization",
        "currentStage": "Projekt initialisiert",
        "iteration": {
            "goal": next_description,
            "status": "initialization",
            "nonGoals": [],
            "dataRisk": "not-assessed"
        },
        "verification": {"releaseGates": {"status": "pending", "passed": [], "verifiedAt": None}},
        "documentation": {
            "roadmap": "current",
            "runbooks": "current",
            "architecture": "current",
            "knownIssues": "current",
            "releaseHistory": "current"
        },
        "technicalDebt": {
            "status": "reviewed",
            "scannerVersion": framework_version.rsplit(".", 1)[0],
            "findings": 0,
            "blockers": 0,
            "warnings": 0,
            "reviewedAt": now.isoformat(),
            "sample": []
        },
        "nextStep": {"id": next_id, "description": next_description},
        "lastBuild": {"status": "not-run", "timestamp": None},
        "lastRelease": {"status": "not-run", "timestamp": None},
        "releaseProvenance": None,
        "knownIssues": 0,
        "updatedAt": now.isoformat()
    }
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    VERSION.write_text(args.version + "\n", encoding="utf-8")

    write(ROOT / "AGENTS.md", f"""# Agent / Assistant Working Contract – {args.name}

Die framework-weit gültigen Regeln stehen in `.project/framework/AGENT_CONTRACT.md` und werden bei Framework-Updates gepflegt. Dieses Dokument ist project-owned und enthält ausschließlich projektspezifische Ergänzungen.

## Projektspezifische Regeln

- Projekt: **{args.name}** (`{args.key}`)
- Fachliche Architektur-, Daten- und Betriebsregeln hier ergänzen, sobald sie feststehen.
- Projektspezifische Actions gehören in `tools/companion/project_actions.py` oder klar abgegrenzte Projektmodule.
- Lokale Produktserver werden ausschließlich als code-reviewte Argumentlisten in `tools/companion/project_runtime.py` registriert; Engineering Companion und Produkt verwenden getrennte Loopback-Ports.
- Projektspezifische Cockpit-Views gehören in `tools/companion/project_ui.py`; optionale Renderer/CSS liegen ausschließlich unter `tools/companion/project_web/`.
- Read-only Cockpit-Daten können über Project-View-Provider bereitgestellt werden; Mutationen bleiben registrierte Actions.
- Fachliche Tests ergänzen den Framework Engineering Contract.

## Einstieg

`.project/framework/AGENT_CONTRACT.md` → `PROJECT_STATE.md` → Config/State → Live-Git/PR/CI → relevante Runbooks/ADRs → dokumentierter Next Step.
""")

    write(ROOT / "PROJECT_STATE.md", f"""# Projektgedächtnis – {args.name}

<!-- project-memory-schema: 2 -->
<!-- current-version: {args.version} -->
<!-- next-step: {next_id} -->
<!-- updated-at: {now.date().isoformat()} -->
<!-- release-status: not-released -->
<!-- release-source-branch: n/a -->
<!-- release-target-branch: main -->
<!-- release-pr: n/a -->

Dieses Dokument ist die verbindliche Übergabe zwischen Entwicklungsiterationen, Rechnern, ChatGPT- und Codex-Sitzungen.

## Aktueller Stand

- Projekt: **{args.name}**
- Version: **{args.version}**
- Engineering Framework: **{framework_version}**
- Entwicklungsmodus: Initialisierung
- Engineering Companion: Framework-Dashboard plus optionale project-owned Cockpit-Views
- Project Runtime Contract: verfügbar, aber noch ohne registrierte Produktruntime
- Live-Branch und Live-Commit werden immer aus Git ermittelt; Release-Provenienz ist historische Metadaten.

## Aktuelle Iteration

Ziel: {next_description}. Datenrisiko und Nicht-Ziele vor der ersten fachlichen Änderung konkretisieren.

## Umgesetzt

- Repository aus Project Engineering Template initialisiert.
- Config, State, Roadmap, Runbooks, Agent Contract und Projektgedächtnis angelegt.
- Project UI Extension Contract ist verfügbar, aber noch ohne projektspezifische Views.
- Project Runtime Contract ist verfügbar, aber noch ohne projektspezifische Produktruntime.

## Nicht umgesetzt / Nicht-Ziele

- Noch keine fachliche Projektlogik, project-spezifische Cockpit-View oder Produktruntime registriert.

## Qualität und Verifikation

Vor dem ersten Release projektspezifische Tests/Build-Gates ergänzen, Produktruntime per Healthcheck validieren und Engineering Contract ausführen.

## Altlasten und bekannte Probleme

Keine bekannten Altlasten aus der Initialisierung. Nach ersten Projektänderungen Technical-Debt-Review erneut ausführen.

## Nächster geplanter Schritt

**{next_id}** – {next_description}.

## Wiederaufnahme nach Chat-Abbruch

`.project/framework/AGENT_CONTRACT.md` → `AGENTS.md` → `PROJECT_STATE.md` → `.project/project.config.json` → `.project/state/current.json` → Live-Git/PR/CI → Memory Contract.

## Iterationsübergabe

```text
Version: {args.version}
Status: initialisiert
Live-Git: aus Repository ermitteln
Nächster Schritt: {next_id}
```
""")
    write(ROOT / "docs/project/Roadmap.md", f"# Roadmap – {args.name}\n\n## Initialisierung\n\n- [x] Engineering Framework {framework_version} initialisiert\n- [ ] Project Actions, Produktruntime, Project Cockpit und Quality Gates konfigurieren\n- [ ] Architektur und fachliche Roadmap definieren\n")
    write(ROOT / "docs/project/Known-Issues.md", "# Known Issues\n\nKeine bekannten Issues zum Initialisierungszeitpunkt.\n")
    write(ROOT / "docs/project/Release-History.md", f"# Release History – {args.name}\n\nNoch kein Release.\n")
    write(ROOT / "docs/project/Architecture-Decisions.md", f"# Architecture Decisions\n\n## ADR-0001 · Project Engineering Framework {framework_version}\n\nDas Repository verwendet das Project Engineering Framework {framework_version} als Engineering-, Runtime-, Handoff-, Release- und Companion-Cockpit-Basis.\n")

    print(f"Initialisiert: {args.name} ({args.key}) v{args.version} · Framework {framework_version}")
    print("Nächster Schritt: project.config.json, project_actions.py sowie bei Bedarf project_runtime.py und project_ui.py projektspezifisch ergänzen, Datenrisiko festlegen und Engineering Contract ausführen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
