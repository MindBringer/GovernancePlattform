from __future__ import annotations

import importlib.util
import re
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from tools.companion.core.config import ProjectConfig

VIEW_ID_RE = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
ALLOWED_LEVELS = {"good", "warn", "danger", "info", "neutral"}
ALLOWED_RENDERERS = {"generic", "custom"}
PROJECT_UI_MODULE = "tools/companion/project_ui.py"
PROJECT_WEB_ROOT = "tools/companion/project_web"


class ProjectUIError(RuntimeError):
    pass


Provider = Callable[[], dict[str, Any]]


@dataclass(frozen=True)
class ProjectViewSpec:
    id: str
    label: str
    title: str | None = None
    description: str = ""
    order: int = 100
    dashboard: bool = False
    renderer: str = "generic"
    script: str | None = None
    stylesheet: str | None = None
    refresh_seconds: int = 0
    provider: Provider | None = None

    def public(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "label": self.label,
            "title": self.title or self.label,
            "description": self.description,
            "order": self.order,
            "dashboard": self.dashboard,
            "renderer": self.renderer,
            "refreshSeconds": self.refresh_seconds,
        }
        if self.script:
            payload["script"] = f"/project-ui/assets/{self.script}"
        if self.stylesheet:
            payload["stylesheet"] = f"/project-ui/assets/{self.stylesheet}"
        return payload


class ProjectUIRegistry:
    def __init__(self, root: Path, *, allow_custom_assets: bool = False) -> None:
        self.root = root.resolve()
        self.project_web_root = (self.root / PROJECT_WEB_ROOT).resolve()
        self.allow_custom_assets = allow_custom_assets
        self._views: dict[str, ProjectViewSpec] = {}

    def _validate_asset(self, value: str | None, suffix: str) -> str | None:
        if not value:
            return None
        if not self.allow_custom_assets:
            raise ProjectUIError("Custom Project-UI-Assets sind in project.config.json nicht freigegeben")
        relative = Path(value)
        if relative.is_absolute():
            raise ProjectUIError(f"Project-UI-Asset muss relativ sein: {value}")
        candidate = (self.project_web_root / relative).resolve()
        try:
            candidate.relative_to(self.project_web_root)
        except ValueError as exc:
            raise ProjectUIError(f"Project-UI-Asset verlässt tools/companion/project_web: {value}") from exc
        if candidate.suffix.lower() != suffix:
            raise ProjectUIError(f"Project-UI-Asset benötigt Endung {suffix}: {value}")
        if not candidate.is_file():
            raise ProjectUIError(f"Project-UI-Asset fehlt: {value}")
        return relative.as_posix()

    def register(self, spec: ProjectViewSpec) -> None:
        if not isinstance(spec, ProjectViewSpec):
            raise ProjectUIError("Project UI Registry akzeptiert nur ProjectViewSpec")
        if not VIEW_ID_RE.fullmatch(spec.id):
            raise ProjectUIError(f"Ungültige Project-View-ID: {spec.id}")
        if spec.id in self._views:
            raise ProjectUIError(f"Doppelte Project-View-ID: {spec.id}")
        if not spec.label.strip():
            raise ProjectUIError(f"Project View {spec.id} benötigt ein Label")
        if spec.renderer not in ALLOWED_RENDERERS:
            raise ProjectUIError(f"Project View {spec.id}: renderer muss generic oder custom sein")
        if not isinstance(spec.order, int):
            raise ProjectUIError(f"Project View {spec.id}: order muss Integer sein")
        if not isinstance(spec.refresh_seconds, int) or spec.refresh_seconds < 0 or spec.refresh_seconds > 3600:
            raise ProjectUIError(f"Project View {spec.id}: refresh_seconds muss 0..3600 sein")
        if 0 < spec.refresh_seconds < 5:
            raise ProjectUIError(f"Project View {spec.id}: automatischer Refresh mindestens 5 Sekunden")
        if spec.provider is not None and not callable(spec.provider):
            raise ProjectUIError(f"Project View {spec.id}: provider muss callable sein")

        script = self._validate_asset(spec.script, ".js")
        stylesheet = self._validate_asset(spec.stylesheet, ".css")
        if spec.renderer == "custom" and not script:
            raise ProjectUIError(f"Project View {spec.id}: custom renderer benötigt script")

        self._views[spec.id] = ProjectViewSpec(
            id=spec.id,
            label=spec.label.strip(),
            title=(spec.title or spec.label).strip(),
            description=spec.description.strip(),
            order=spec.order,
            dashboard=bool(spec.dashboard),
            renderer=spec.renderer,
            script=script,
            stylesheet=stylesheet,
            refresh_seconds=spec.refresh_seconds,
            provider=spec.provider,
        )

    def all(self) -> list[ProjectViewSpec]:
        return sorted(self._views.values(), key=lambda item: (item.order, item.label.lower(), item.id))

    def public(self) -> list[dict[str, Any]]:
        return [item.public() for item in self.all()]

    def get(self, view_id: str) -> ProjectViewSpec | None:
        return self._views.get(view_id)

    def asset_paths(self) -> set[str]:
        paths: set[str] = set()
        for spec in self._views.values():
            if spec.script:
                paths.add(spec.script)
            if spec.stylesheet:
                paths.add(spec.stylesheet)
        return paths

    def data(self, view_id: str) -> dict[str, Any]:
        spec = self.get(view_id)
        if spec is None:
            raise ProjectUIError(f"Unbekannte Project View: {view_id}")
        if spec.provider is None:
            return {}
        payload = spec.provider()
        if payload is None:
            return {}
        if not isinstance(payload, dict):
            raise ProjectUIError(f"Project View {view_id}: provider muss ein JSON-Objekt liefern")
        return payload


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("project_companion_ui", path)
    if spec is None or spec.loader is None:
        raise ProjectUIError(f"Project-UI-Modul kann nicht geladen werden: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_project_ui(root: Path, config: ProjectConfig) -> ProjectUIRegistry:
    ui = config.data.get("ui", {}) if isinstance(config.data.get("ui"), dict) else {}
    project_ui = ui.get("projectUI", {}) if isinstance(ui.get("projectUI"), dict) else {}
    enabled = bool(project_ui.get("enabled", True))
    allow_custom_assets = bool(project_ui.get("allowCustomAssets", False))
    registry = ProjectUIRegistry(root, allow_custom_assets=allow_custom_assets)
    if not enabled:
        return registry

    module_path = (root / PROJECT_UI_MODULE).resolve()
    if not module_path.is_file():
        return registry
    try:
        module_path.relative_to(root.resolve())
    except ValueError as exc:
        raise ProjectUIError("Project-UI-Modul liegt außerhalb des Repositories") from exc

    module = _load_module(module_path)
    register = getattr(module, "register_project_ui", None)
    if register is None:
        raise ProjectUIError(f"{PROJECT_UI_MODULE} benötigt register_project_ui(registry, root, config)")
    if not callable(register):
        raise ProjectUIError(f"{PROJECT_UI_MODULE}: register_project_ui ist nicht callable")
    register(registry, root.resolve(), config)
    return registry
