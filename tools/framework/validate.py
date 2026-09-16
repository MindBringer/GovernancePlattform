#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.companion.core.config import ConfigError, load_config
from tools.framework.project_memory import contract as project_memory_contract

REQUIRED_BASE = [
    ".project/project.config.json",
    ".project/framework.manifest.json",
    ".project/framework/AGENT_CONTRACT.md",
    ".project/state/current.json",
    "PROJECT_STATE.md",
    "AGENTS.md",
    "tools/companion/server.py",
    "tools/companion/project_actions.py",
    "tools/companion/core/ui_extensions.py",
    "tools/companion/web/index.html",
    "tools/companion/web/project-ui.css",
    "tools/framework/project_memory.py",
    "tools/framework/technical_debt.py",
    "tools/framework/release_artifacts.py",
    "tools/framework/repository_policy.py",
    "tools/framework/bootstrap_smoke.py",
    "docs/project/Roadmap.md",
    "docs/runbooks/Developer-Companion.md",
]

TEMPLATE_PROJECT_UI = [
    "tools/companion/project_ui.py",
    "tools/companion/project_web/README.md",
]


def main() -> int:
    checks: list[dict[str, object]] = []
    errors: list[str] = []
    try:
        config = load_config(ROOT)
        checks.append({"name": "config", "ok": True, "detail": config.framework_version})
    except ConfigError as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 1

    required = list(REQUIRED_BASE)
    if config.project.get("key") == "project-template":
        required.extend(TEMPLATE_PROJECT_UI)
    for rel in required:
        exists = (ROOT / rel).exists()
        checks.append({"name": f"path:{rel}", "ok": exists})
        if not exists:
            errors.append(f"Pfad fehlt: {rel}")

    manifest_path = ROOT / ".project/framework.manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        manifest = {}
        errors.append(f"Framework-Manifest ungültig: {exc}")
    if manifest.get("frameworkVersion") != config.framework_version:
        errors.append("frameworkVersion in Config und Manifest unterscheiden sich")

    quality = config.data.get("quality", {})
    if not isinstance(quality, dict):
        errors.append("quality muss ein Objekt sein")
    else:
        required_docs = quality.get("requiredDocumentationStatus")
        if not isinstance(required_docs, list) or not required_docs:
            errors.append("quality.requiredDocumentationStatus muss eine nichtleere Liste sein")
        if config.project.get("key") == "project-template":
            supported_python = quality.get("supportedPython")
            platforms = quality.get("ciPlatforms")
            if not isinstance(supported_python, list) or not {"3.12", "3.14"}.issubset(set(supported_python)):
                errors.append("Template muss Python 3.12 und 3.14 als CI-Support deklarieren")
            if not isinstance(platforms, list) or not {"ubuntu", "macos", "windows"}.issubset(set(platforms)):
                errors.append("Template muss Ubuntu, macOS und Windows als CI-Plattformen deklarieren")
            project_ui = config.data.get("ui", {}).get("projectUI", {})
            if not isinstance(project_ui, dict) or not project_ui.get("enabled"):
                errors.append("Template muss ui.projectUI.enabled aktivieren")
            if not isinstance(project_ui, dict) or not project_ui.get("allowCustomAssets"):
                errors.append("Template muss project-owned Custom UI Assets als Erweiterung demonstrieren können")

    repository_policy = config.data.get("repositoryPolicy", {})
    if repository_policy and not isinstance(repository_policy, dict):
        errors.append("repositoryPolicy muss ein Objekt sein")

    release = config.data.get("release", {})
    if config.enabled("release") or release.get("enabled"):
        if not release.get("confirmation"):
            errors.append("Release ist aktiv, aber release.confirmation fehlt")
        gates = release.get("gates", [])
        if not isinstance(gates, list) or not gates:
            errors.append("Release ist aktiv, aber release.gates ist leer")
        if release.get("createGitHubRelease", False) and not isinstance(release.get("tagPrefix", "v"), str):
            errors.append("GitHub Release ist aktiv, aber release.tagPrefix ist ungültig")

    pp = config.data.get("powerPlatform", {})
    if config.enabled("powerPlatform") or pp.get("enabled"):
        scripts = pp.get("scripts", {}) if isinstance(pp.get("scripts"), dict) else {}
        if not scripts.get("validate") and not scripts.get("build"):
            errors.append("Power Platform ist aktiv, aber validate/build-Skripte sind nicht konfiguriert")

    provisioning = config.data.get("provisioning", {})
    if config.enabled("provisioning") or provisioning.get("enabled"):
        script = config.path(str(provisioning.get("modeScript") or ""))
        if not script or not script.is_file():
            errors.append("Provisioning ist aktiv, aber provisioning.modeScript fehlt")

    memory = project_memory_contract(ROOT)
    checks.append({"name": "project-memory-contract", "ok": bool(memory.get("ok"))})
    errors.extend(str(item) for item in memory.get("errors", []))

    result = {"ok": not errors, "frameworkVersion": config.framework_version, "checks": checks, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
