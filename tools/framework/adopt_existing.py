#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.framework.sync import build_lock, digest, expand, load_manifest


ADOPTION_OWNED_PATHS = [
    "AGENTS.md",
    "PROJECT_STATE.md",
    "docs/project/Roadmap.md",
    "docs/project/Known-Issues.md",
    "docs/project/Release-History.md",
    "docs/project/Architecture-Decisions.md",
    "tools/companion/project_actions.py",
    "tools/companion/project_runtime.py",
    "tools/companion/project_ui.py",
]


def git(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(target), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def backup_file(target: Path, rel: str, backup_root: Path) -> None:
    src = target / rel
    if not src.is_file():
        return
    dst = backup_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def write_text(target: Path, rel: str, content: str, backup_root: Path) -> None:
    backup_file(target, rel, backup_root)
    path = target / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_managed(target: Path, backup_root: Path) -> tuple[int, int]:
    manifest = load_manifest(ROOT)
    files = expand(ROOT, manifest.get("managed", []))
    copied = 0
    replaced = 0
    for rel, src in files.items():
        dst = target / rel
        if dst.is_file() and digest(dst) != digest(src):
            backup_file(target, rel, backup_root)
            replaced += 1
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    return copied, replaced


def write_initial_config(target: Path, args: argparse.Namespace) -> None:
    source_config = json.loads((ROOT / ".project/project.config.json").read_text(encoding="utf-8"))
    framework_version = str(load_manifest(ROOT).get("frameworkVersion") or source_config.get("frameworkVersion") or "unknown")
    source_config["frameworkVersion"] = framework_version
    source_config["project"].update({
        "key": args.key,
        "name": args.name,
        "description": args.description,
        "versionFile": args.version_file,
    })
    source_config["companion"]["port"] = args.port
    source_config["modules"]["powerPlatform"] = bool(args.power_platform)
    source_config["modules"]["provisioning"] = bool(args.provisioning)
    source_config["powerPlatform"]["enabled"] = bool(args.power_platform)
    source_config["provisioning"]["enabled"] = bool(args.provisioning)
    source_config["release"]["gates"] = [
        gate for gate in source_config.get("release", {}).get("gates", [])
        if gate != "bootstrap-smoke"
    ]
    path = target / ".project/project.config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(source_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_manifest(target: Path) -> None:
    manifest = load_manifest(ROOT)
    (target / ".project").mkdir(parents=True, exist_ok=True)
    (target / ".project/framework.manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def ensure_version_file(target: Path, args: argparse.Namespace) -> None:
    path = target / args.version_file
    if path.is_file():
        existing = path.read_text(encoding="utf-8").strip()
        if existing and existing != args.version:
            print(f"HINWEIS: Versionsfile bleibt unverändert ({existing}); Adoption-State startet mit {args.version}.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(args.version + "\n", encoding="utf-8")


def state_payload(args: argparse.Namespace) -> dict:
    now = datetime.now(timezone.utc)
    framework_version = str(load_manifest(ROOT).get("frameworkVersion") or "unknown")
    return {
        "schemaVersion": 2,
        "frameworkVersion": framework_version,
        "projectVersion": args.version,
        "developmentMode": "framework-migration",
        "currentStage": "Engineering Framework Migration",
        "iteration": {
            "goal": "Bestehendes Repository auf das Project Engineering Framework migrieren",
            "status": "in-progress",
            "nonGoals": ["fachliche Refactorings während der Framework-Migration"],
            "dataRisk": "low",
        },
        "verification": {"releaseGates": {"status": "pending", "passed": [], "verifiedAt": None}},
        "documentation": {
            "roadmap": "migration-pending",
            "runbooks": "migration-pending",
            "architecture": "migration-pending",
            "knownIssues": "migration-pending",
            "releaseHistory": "migration-pending",
        },
        "technicalDebt": {
            "status": "pending",
            "scannerVersion": framework_version.rsplit(".", 1)[0],
            "findings": 0,
            "blockers": 0,
            "warnings": 0,
            "reviewedAt": None,
            "sample": [],
        },
        "nextStep": {
            "id": "framework-migration-adapters",
            "description": "Project Config, Actions, Runtime, Cockpit, Doku und Release-Gates auf das bestehende Projekt abbilden",
        },
        "lastBuild": {"status": "not-run", "timestamp": None},
        "lastRelease": {"status": "not-run", "timestamp": None},
        "releaseProvenance": None,
        "knownIssues": 0,
        "updatedAt": now.isoformat(),
    }


def write_state(target: Path, args: argparse.Namespace) -> None:
    path = target / ".project/state/current.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state_payload(args), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_project_scaffold(target: Path, args: argparse.Namespace, backup_root: Path) -> None:
    now = datetime.now(timezone.utc)
    framework_version = str(load_manifest(ROOT).get("frameworkVersion") or "unknown")
    write_text(target, "AGENTS.md", f"""# Agent / Assistant Working Contract – {args.name}

Die framework-weit gültigen Regeln stehen in `.project/framework/AGENT_CONTRACT.md`. Dieses Dokument ist project-owned und enthält projektspezifische Ergänzungen.

## Migration

- Projekt: **{args.name}** (`{args.key}`)
- Engineering Framework: **{framework_version}**
- Bestehende fachliche Architektur und Projektdateien bleiben erhalten.
- Framework-managed Dateien werden ausschließlich über Framework-Sync aktualisiert.
- Projektspezifische Actions gehören in `tools/companion/project_actions.py`.
- Lokale Produktserver gehören als code-reviewte Argumentlisten in `tools/companion/project_runtime.py`.
- Projektspezifische Cockpit-Views gehören in `tools/companion/project_ui.py`.

## Einstieg

`.project/framework/AGENT_CONTRACT.md` → `PROJECT_STATE.md` → `.project/project.config.json` → Live-Git/PR/CI → relevante Projekt-Doku.
""", backup_root)
    write_text(target, "PROJECT_STATE.md", f"""# Projektgedächtnis – {args.name}

<!-- project-memory-schema: 2 -->
<!-- current-version: {args.version} -->
<!-- next-step: framework-migration-adapters -->
<!-- updated-at: {now.date().isoformat()} -->
<!-- release-status: migration -->
<!-- release-source-branch: n/a -->
<!-- release-target-branch: main -->
<!-- release-pr: n/a -->

## Aktueller Stand

Das bestehende Repository wird auf **Project Engineering Framework {framework_version}** migriert. Fachliche Quellen und bestehende Projekt-Dokumentation bleiben erhalten; die neue Engineering-Schicht wird getrennt darüber gelegt.

## Aktuelle Iteration

Ziel: Framework-Config, Actions, lokale Produktruntime, Cockpit, Power-Platform-/Provisioning-Hooks und Release-Gates auf den vorhandenen Projektstand abbilden.

## Nicht-Ziele

- Keine fachlichen Refactorings während der Framework-Migration.
- Keine Löschung bestehender Fachquellen.

## Qualität und Verifikation

Nach der Adapter-Migration: Framework Validate → projektspezifische Gates → Build → Runtime-Health → Release aus Feature-Branch.

## Nächster geplanter Schritt

**framework-migration-adapters** – Project Config, Actions, Runtime, Cockpit, Doku und Release-Gates auf das bestehende Projekt abbilden.
""", backup_root)
    write_text(target, "docs/project/Roadmap.md", f"# Roadmap – {args.name}\n\n## Engineering Framework Migration\n\n- [x] Framework {framework_version} adoptieren\n- [ ] Project Actions, Runtime und optionale Module konfigurieren\n- [ ] Bestehende Roadmap/Doku in den Framework-Dokumentationsvertrag einordnen\n- [ ] Engineering Contract, Runtime-Health und Projekt-Build grün ausführen\n- [ ] Migration nach main releasen\n", backup_root)
    write_text(target, "docs/project/Known-Issues.md", "# Known Issues\n\n- Framework-Migration läuft; projektspezifische Adapter sind noch nicht vollständig konfiguriert.\n", backup_root)
    write_text(target, "docs/project/Release-History.md", f"# Release History – {args.name}\n\nFramework-Migration noch nicht released.\n", backup_root)
    write_text(target, "docs/project/Architecture-Decisions.md", f"# Architecture Decisions\n\n## ADR-0001 · Project Engineering Framework {framework_version}\n\nDas bestehende Repository übernimmt das Project Engineering Framework als gemeinsame Engineering-, Companion-, Runtime-, Handoff- und Release-Basis. Fachliche Quellen bleiben project-owned.\n", backup_root)
    for rel in ("tools/companion/project_actions.py", "tools/companion/project_runtime.py", "tools/companion/project_ui.py"):
        src = ROOT / rel
        if src.is_file():
            backup_file(target, rel, backup_root)
            dst = target / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def ensure_gitignore(target: Path) -> None:
    path = target / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    entry = ".framework-adoption-backup/"
    lines = text.splitlines()
    if entry not in lines:
        path.write_text(text.rstrip() + ("\n" if text.strip() else "") + entry + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Adopt Project Engineering Framework into an existing Git repository")
    parser.add_argument("--target", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--version", required=True)
    parser.add_argument("--version-file", default="VERSION")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--power-platform", action="store_true")
    parser.add_argument("--provisioning", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if target == ROOT:
        raise SystemExit("Target darf nicht das Template-Repository selbst sein.")
    if not (target / ".git").exists():
        raise SystemExit(f"Target ist kein Git-Repository: {target}")
    status = git(target, "status", "--porcelain")
    if status.returncode != 0:
        raise SystemExit(status.stdout.strip() or "git status fehlgeschlagen")
    if status.stdout.strip() and not args.allow_dirty:
        raise SystemExit("Target enthält lokale Änderungen. Erst committen/stashen oder bewusst --allow-dirty verwenden.")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = target / ".framework-adoption-backup" / stamp
    copied, replaced = copy_managed(target, backup_root)
    write_manifest(target)
    write_initial_config(target, args)
    write_state(target, args)
    write_project_scaffold(target, args, backup_root)
    ensure_version_file(target, args)
    ensure_gitignore(target)

    lock = build_lock(target)
    (target / ".project/framework.lock.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")

    print(f"FRAMEWORK ADOPTION: OK · {args.name} · Framework {lock.get('frameworkVersion')}")
    print(f"Managed files: {copied} · ersetzt: {replaced}")
    print(f"Backup: {backup_root}")
    print("Nächster Schritt: project.config.json, project_actions.py, project_runtime.py, project_ui.py und Projektdokumentation auf den Ist-Stand abbilden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
