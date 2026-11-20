#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = ROOT / "tools" / "companion" / "local.settings.json"
VERSION_FILE = ROOT / "powerplatform" / "VERSION"
SOLUTION_XML = ROOT / "powerplatform" / "solution" / "Other" / "Solution.xml"
SOLUTION_DIR = ROOT / "powerplatform" / "solution"
CANVAS_DIR = ROOT / "powerplatform" / "canvas" / "GovernancePortal"
MSAPP_NAME = "gp_governanceportal_c93a1_DocumentUri.msapp"
OUTBOUND_DIR = ROOT / "artifacts" / "outbound"


def run(command: list[str], timeout: int = 3600) -> int:
    print(f"$ {' '.join(command)}", flush=True)
    result = subprocess.run(command, cwd=ROOT, text=True, check=False, timeout=timeout)
    return result.returncode


def checked(command: list[str], timeout: int = 3600) -> None:
    code = run(command, timeout)
    if code != 0:
        raise RuntimeError(f"Schritt fehlgeschlagen (Exit {code}): {' '.join(command)}")


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Erforderlicher Befehl fehlt im PATH: {name}")


def load_settings(required: bool = True) -> dict[str, str]:
    if not SETTINGS.exists():
        if required:
            raise RuntimeError(
                "Lokale PAC-Konfiguration fehlt: tools/companion/local.settings.json. "
                "Vorlage local.settings.example.json kopieren und anpassen."
            )
        return {}
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    for key in ("environmentUrl", "solutionUniqueName"):
        if required and not str(data.get(key, "")).strip():
            raise RuntimeError(f"PAC-Konfiguration unvollständig: {key}")
    return {key: str(value) for key, value in data.items() if value is not None}


def solution_unique_name() -> str:
    settings = load_settings(False)
    if settings.get("solutionUniqueName"):
        return settings["solutionUniqueName"]
    if SOLUTION_XML.exists():
        root = ET.parse(SOLUTION_XML).getroot()
        value = root.findtext("./SolutionManifest/UniqueName")
        if value:
            return value
    return "GovernancePortal"


def version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else "unknown"


def export_path() -> Path:
    return ROOT / "artifacts" / "inbound" / f"{solution_unique_name()}-{version()}-DEV.zip"


def select_auth() -> int:
    settings = load_settings()
    profile = settings.get("authProfileName", "").strip()
    if profile:
        return run(["pac", "auth", "select", "--name", profile], 120)
    print("Kein authProfileName konfiguriert; aktuell ausgewähltes PAC-Profil bleibt aktiv.")
    return run(["pac", "auth", "list"], 120)


def pac_check() -> int:
    require_command("pac")
    code = run(["pac", "help"], 60)
    if code != 0:
        return code
    return run(["pac", "auth", "list"], 120)


def pac_export() -> int:
    require_command("pac")
    settings = load_settings()
    target = export_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "pac", "solution", "export",
        "--name", settings["solutionUniqueName"],
        "--path", str(target),
        "--overwrite",
        "--environment", settings["environmentUrl"],
    ]
    code = run(command, 3600)
    if code == 0 and not target.exists():
        raise RuntimeError(f"PAC meldete Erfolg, Exportdatei fehlt: {target}")
    if code == 0:
        print(f"Export erstellt: {target.relative_to(ROOT)}")
    return code


def pac_unpack() -> int:
    require_command("pac")
    source = export_path()
    if not source.exists():
        raise RuntimeError(f"Exportdatei fehlt: {source.relative_to(ROOT)}")
    return run([
        "pac", "solution", "unpack",
        "--zipfile", str(source),
        "--folder", str(SOLUTION_DIR),
        "--packagetype", "Unmanaged",
        "--allowDelete", "--allowWrite", "--clobber",
    ], 3600)


def canvas_sync() -> int:
    require_command("pac")
    msapp = SOLUTION_DIR / "CanvasApps" / MSAPP_NAME
    if not msapp.exists():
        raise RuntimeError(f"Canvas-App fehlt in entpackter Solution: {msapp.relative_to(ROOT)}")
    CANVAS_DIR.mkdir(parents=True, exist_ok=True)
    code = run([
        "pac", "canvas", "unpack",
        "--msapp", str(msapp),
        "--sources", str(CANVAS_DIR),
        "--layout", "SourceCode",
        "--overwrite",
    ], 3600)
    if code == 0 and not (CANVAS_DIR / "Src" / "App.pa.yaml").exists():
        raise RuntimeError("Canvas-Unpack meldete Erfolg, App.pa.yaml fehlt.")
    if code == 0:
        print("Canvas-SourceTree wurde aus dem DEV-Export synchronisiert.")
    return code


def git_diff() -> int:
    code = run(["git", "status", "--short", "--branch"], 60)
    return code if code != 0 else run(["git", "diff", "--stat"], 60)


def current_package() -> Path:
    candidates = sorted(OUTBOUND_DIR.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise RuntimeError("Keine gepackte Solution unter artifacts/outbound gefunden. Zuerst Build ausführen.")
    expected_version = version()
    matching = [item for item in candidates if expected_version in item.name]
    if not matching:
        found = "\n".join(f"- {item.name}" for item in candidates[:5])
        raise RuntimeError(
            f"Kein Importpaket für Canvas-Version {expected_version} gefunden. Vorhanden:\n{found}\n"
            "Vollständigen Build erneut ausführen."
        )
    return matching[0]


def print_package(package: Path) -> None:
    stat = package.stat()
    modified = datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds")
    print(f"Importpaket: {package.relative_to(ROOT)}")
    print(f"Canvas-Version: {version()}")
    print(f"Größe: {stat.st_size / 1024:.1f} KiB")
    print(f"Geändert: {modified}")


def pac_import() -> int:
    require_command("pac")
    settings = load_settings()
    package = current_package()
    print_package(package)
    command = [
        "pac", "solution", "import",
        "--path", str(package),
        "--environment", settings["environmentUrl"],
        "--publish-changes",
        "--force-overwrite",
    ]
    settings_file = settings.get("deploymentSettingsFile", "").strip()
    if settings_file:
        resolved = ROOT / settings_file
        if not resolved.exists():
            raise RuntimeError(f"Deployment-Settings-Datei fehlt: {settings_file}")
        command.extend(["--settings-file", str(resolved)])
    code = run(command, 3600)
    if code == 0:
        print("\nIMPORT UND VERÖFFENTLICHUNG ABGESCHLOSSEN")
        print("Die Canvas-App ist jetzt in DEV testbar; ein manueller Solution-Import ist nicht erforderlich.")
    return code


def publish_all() -> int:
    require_command("pac")
    settings = load_settings()
    print("HINWEIS: Publish All veröffentlicht umgebungsweit alle ausstehenden Anpassungen.")
    return run(["pac", "solution", "publish", "--environment", settings["environmentUrl"]], 3600)


def studio_sync() -> int:
    print("=== Studio Sync: DEV -> Git-Arbeitsverzeichnis ===")
    checked(["python3", "./tools/companion/pac_workflow.py", "check"], 180)
    checked(["python3", "./tools/companion/pac_workflow.py", "select-dev"], 180)
    checked(["python3", "./tools/companion/pac_workflow.py", "export"])
    checked(["python3", "./tools/companion/pac_workflow.py", "unpack"])
    checked(["python3", "./tools/companion/pac_workflow.py", "canvas-sync"])
    checked(["python3", "./tools/companion/pac_workflow.py", "git-diff"], 180)
    print("\nSTUDIO SYNC ABGESCHLOSSEN")
    print("Git-Diff prüfen. Erst danach Build oder Deploy to DEV ausführen.")
    return 0


def deploy_dev() -> int:
    settings = load_settings()
    print("=== Deploy to DEV: Validate -> Build -> Import -> Publish ===")
    print(f"Zielumgebung: {settings['environmentUrl']}")
    checked(["python3", "./tools/companion/audit_repo.py"])
    checked(["pwsh", "./powerplatform/scripts/Build.ps1"])
    package = current_package()
    print_package(package)
    checked(["python3", "./tools/companion/pac_workflow.py", "import"])
    print("\nDEPLOYMENT ERFOLGREICH")
    print(f"Governance Portal {version()} ist in DEV importiert, veröffentlicht und testbereit.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Governance Portal PAC workflow")
    parser.add_argument("action", choices=[
        "check", "auth-list", "select-dev", "export", "unpack", "canvas-sync", "git-diff",
        "import", "publish", "studio-sync", "deploy-dev"
    ])
    args = parser.parse_args()
    try:
        if args.action == "check": return pac_check()
        if args.action == "auth-list": return run(["pac", "auth", "list"], 120)
        if args.action == "select-dev": return select_auth()
        if args.action == "export": return pac_export()
        if args.action == "unpack": return pac_unpack()
        if args.action == "canvas-sync": return canvas_sync()
        if args.action == "git-diff": return git_diff()
        if args.action == "import": return pac_import()
        if args.action == "publish": return publish_all()
        if args.action == "studio-sync": return studio_sync()
        if args.action == "deploy-dev": return deploy_dev()
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
