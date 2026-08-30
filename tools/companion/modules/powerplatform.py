from __future__ import annotations

from pathlib import Path

from ..core.actions import ActionRegistry, ActionSpec
from ..core.config import ProjectConfig


def _pwsh_script(config: ProjectConfig, relative: str | None, args: list[str] | None = None) -> list[str] | None:
    path = config.path(relative)
    if not path or not path.is_file():
        return None
    return ["pwsh", str(path.relative_to(config.root)), *(args or [])]


def register_powerplatform_actions(registry: ActionRegistry, root: Path, config: ProjectConfig) -> None:
    if not config.enabled("powerPlatform") and not config.data.get("powerPlatform", {}).get("enabled", False):
        return
    pp = config.data.get("powerPlatform", {})
    scripts = pp.get("scripts", {}) if isinstance(pp.get("scripts"), dict) else {}
    script_args = pp.get("scriptArgs", {}) if isinstance(pp.get("scriptArgs"), dict) else {}

    registry.register(ActionSpec(
        id="pac-version", label="PAC prüfen", category="Power Platform",
        description="Prüft, ob die Power Platform CLI verfügbar ist.",
        commands=[["pac", "--version"]], timeout=60,
    ))
    registry.register(ActionSpec(
        id="pac-auth-list", label="PAC Auth-Profile", category="Power Platform",
        description="Zeigt verfügbare PAC-Authentifizierungsprofile.",
        commands=[["pac", "auth", "list"]], timeout=60,
    ))

    for action_id, label, key, description in (
        ("pp-canvas-fix-check", "Canvas-Referenzen prüfen", "canvasFixCheck", "Prüft projektspezifische Canvas-/Connector-Referenzen."),
        ("pp-validate", "Solution/Canvas validieren", "validate", "Führt die projektspezifische Power-Platform-Validierung aus."),
        ("pp-build", "Power Platform Build", "build", "Erzeugt das projektspezifische Solution-/Canvas-Buildartefakt."),
        ("pp-studio-export", "Studio → Git", "studioExport", "Übernimmt den Studio-Stand in den kanonischen Git-SourceTree."),
        ("pp-studio-import", "Git → DEV", "studioImport", "Übernimmt den Git-Stand in die DEV-Power-Platform-Umgebung."),
    ):
        args = [str(x) for x in script_args.get(key, [])] if isinstance(script_args.get(key, []), list) else []
        command = _pwsh_script(config, scripts.get(key), args)
        if command:
            registry.register(ActionSpec(
                id=action_id, label=label, category="Power Platform",
                description=description, commands=[command], timeout=3600,
            ))

    environment = str(pp.get("environmentUrl") or "").strip()
    if environment:
        registry.register(ActionSpec(
            id="pac-publish", label="Publish all customizations", category="Power Platform",
            description="Veröffentlicht Customizations direkt in der konfigurierten DEV-Umgebung.",
            commands=[["pac", "solution", "publish", "--environment", environment]], timeout=3600,
            confirmation="PUBLISH DEV", danger=True,
        ))
