#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = ROOT / "tools" / "companion" / "local.settings.json"
VERSION_FILE = ROOT / "powerplatform" / "VERSION"
SOLUTION_XML = ROOT / "powerplatform" / "solution" / "Other" / "Solution.xml"
SOLUTION_DIR = ROOT / "powerplatform" / "solution"
CANVAS_DIR = ROOT / "powerplatform" / "canvas" / "GovernancePortal"
MSAPP_NAME = "gp_governanceportal_c93a1_DocumentUri.msapp"


def run(command: list[str], timeout: int = 3600) -> int:
    print(f"$ {' '.join(command)}", flush=True)
    result = subprocess.run(command, cwd=ROOT, text=True, check=False, timeout=timeout)
    return result.returncode


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
    code = run(["pac", "--version"], 60)
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
        "--managed", "false",
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
    command = [
        "pac", "solution", "unpack",
        "--zipfile", str(source),
        "--folder", str(SOLUTION_DIR),
        "--packagetype", "Unmanaged",
        "--allowDelete", "true",
        "--allowWrite", "true",
    ]
    return run(command, 3600)


def canvas_sync() -> int:
    require_command("pac")
    msapp = SOLUTION_DIR / "CanvasApps" / MSAPP_NAME
    if not msapp.exists():
        raise RuntimeError(f"Canvas-App fehlt in entpackter Solution: {msapp.relative_to(ROOT)}")
    CANVAS_DIR.mkdir(parents=True, exist_ok=True)
    command = [
        "pac", "canvas", "unpack",
        "--msapp", str(msapp),
        "--sources", str(CANVAS_DIR),
        "--layout", "SourceCode",
    ]
    code = run(command, 3600)
    if code == 0:
        app_yaml = CANVAS_DIR / "Src" / "App.pa.yaml"
        if not app_yaml.exists():
            raise RuntimeError("Canvas-Unpack meldete Erfolg, App.pa.yaml fehlt.")
        print("Canvas-SourceTree wurde aus dem DEV-Export synchronisiert.")
        print("Jetzt Git-Diff prüfen, danach Build ausführen.")
    return code


def git_diff() -> int:
    return run(["git", "status", "--short", "--branch"], 60) or run(
        ["git", "diff", "--stat"], 60
    )


def pac_import() -> int:
    require_command("pac")
    settings = load_settings()
    candidates = sorted((ROOT / "artifacts" / "outbound").glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise RuntimeError("Keine gepackte Solution unter artifacts/outbound gefunden. Zuerst Build ausführen.")
    package = candidates[0]
    print(f"Importpaket: {package.relative_to(ROOT)}")
    command = [
        "pac", "solution", "import",
        "--path", str(package),
        "--environment", settings["environmentUrl"],
        "--publish-changes",
        "--force-overwrite",
        "--skip-dependency-check", "false",
    ]
    return run(command, 3600)


def publish_all() -> int:
    require_command("pac")
    settings = load_settings()
    return run(["pac", "solution", "publish", "--environment", settings["environmentUrl"]], 3600)


def main() -> int:
    parser = argparse.ArgumentParser(description="Governance Portal PAC workflow")
    parser.add_argument("action", choices=[
        "check", "auth-list", "select-dev", "export", "unpack", "canvas-sync", "git-diff", "import", "publish"
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
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
