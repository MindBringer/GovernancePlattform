from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProjectConfig:
    root: Path
    data: dict[str, Any]

    def __post_init__(self) -> None:
        # macOS can expose the same temporary/repository path as both /var/... and
        # /private/var/.... Keep one canonical root so relative_to() remains
        # portable across macOS, Linux and Windows.
        object.__setattr__(self, "root", self.root.resolve())

    @property
    def project(self) -> dict[str, Any]:
        return self.data["project"]

    @property
    def modules(self) -> dict[str, bool]:
        return {str(k): bool(v) for k, v in self.data.get("modules", {}).items()}

    @property
    def framework_version(self) -> str:
        return str(self.data.get("frameworkVersion", "unknown"))

    def companion_url(self) -> str:
        companion = self.data.get("companion", {})
        if not isinstance(companion, dict):
            return ""
        host = str(companion.get("host") or "127.0.0.1").strip()
        port = companion.get("port")
        if not host or not isinstance(port, int):
            return ""
        display_host = f"[{host}]" if ":" in host and not host.startswith("[") else host
        return f"http://{display_host}:{port}/"

    def enabled(self, module: str) -> bool:
        return bool(self.modules.get(module, False))

    def path(self, value: str | None) -> Path | None:
        if not value:
            return None
        candidate = (self.root / value).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ConfigError(f"Pfad verlässt das Repository: {value}") from exc
        return candidate

    def version(self) -> str:
        version_file = self.path(str(self.project.get("versionFile") or "VERSION"))
        if not version_file or not version_file.is_file():
            return "unknown"
        raw = version_file.read_text(encoding="utf-8").strip()
        json_key = str(self.project.get("versionJsonKey") or "").strip()
        if json_key:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                return "unknown"
            value = payload.get(json_key) if isinstance(payload, dict) else None
            return str(value) if value is not None else "unknown"
        return raw


def validate_config(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schemaVersion") != 1:
        errors.append("schemaVersion muss 1 sein")
    framework = data.get("frameworkVersion")
    if not isinstance(framework, str) or not framework.strip():
        errors.append("frameworkVersion fehlt")
    project = data.get("project")
    if not isinstance(project, dict):
        errors.append("project muss ein Objekt sein")
    else:
        for key in ("key", "name", "versionFile"):
            if not isinstance(project.get(key), str) or not project.get(key, "").strip():
                errors.append(f"project.{key} fehlt")
    companion = data.get("companion")
    if not isinstance(companion, dict):
        errors.append("companion muss ein Objekt sein")
    else:
        port = companion.get("port")
        if not isinstance(port, int) or not 1024 <= port <= 65535:
            errors.append("companion.port muss zwischen 1024 und 65535 liegen")

    ui = data.get("ui", {})
    if ui and not isinstance(ui, dict):
        errors.append("ui muss ein Objekt sein")
    elif isinstance(ui, dict):
        project_ui = ui.get("projectUI", {})
        if project_ui and not isinstance(project_ui, dict):
            errors.append("ui.projectUI muss ein Objekt sein")
        elif isinstance(project_ui, dict):
            for key in ("enabled", "allowCustomAssets"):
                if key in project_ui and not isinstance(project_ui.get(key), bool):
                    errors.append(f"ui.projectUI.{key} muss bool sein")

    if not isinstance(data.get("modules"), dict):
        errors.append("modules muss ein Objekt sein")
    quality = data.get("quality")
    if not isinstance(quality, dict):
        errors.append("quality muss ein Objekt sein")
    else:
        for key in ("projectMemoryContract", "technicalDebtReview"):
            if not isinstance(quality.get(key), bool):
                errors.append(f"quality.{key} muss bool sein")
        if "verificationEvidence" in quality and not isinstance(quality.get("verificationEvidence"), bool):
            errors.append("quality.verificationEvidence muss bool sein")
        docs = quality.get("requiredDocumentationStatus")
        if not isinstance(docs, list) or not docs or any(not isinstance(item, str) or not item.strip() for item in docs):
            errors.append("quality.requiredDocumentationStatus muss eine nichtleere String-Liste sein")
        supported_python = quality.get("supportedPython", [])
        if supported_python and (not isinstance(supported_python, list) or any(not isinstance(item, str) or not item.strip() for item in supported_python)):
            errors.append("quality.supportedPython muss eine String-Liste sein")
        ci_platforms = quality.get("ciPlatforms", [])
        if ci_platforms and (not isinstance(ci_platforms, list) or any(item not in {"ubuntu", "macos", "windows"} for item in ci_platforms)):
            errors.append("quality.ciPlatforms enthält ungültige Plattformen")
    repository_policy = data.get("repositoryPolicy", {})
    if repository_policy and not isinstance(repository_policy, dict):
        errors.append("repositoryPolicy muss ein Objekt sein")
    elif isinstance(repository_policy, dict) and "requireProtectedBaseBranch" in repository_policy and not isinstance(repository_policy.get("requireProtectedBaseBranch"), bool):
        errors.append("repositoryPolicy.requireProtectedBaseBranch muss bool sein")
    release = data.get("release")
    if not isinstance(release, dict):
        errors.append("release muss ein Objekt sein")
    else:
        if release.get("mergeMethod") not in {"squash", "merge", "rebase"}:
            errors.append("release.mergeMethod muss squash, merge oder rebase sein")
        if not isinstance(release.get("gates"), list):
            errors.append("release.gates muss eine Liste sein")
        for key in ("createTag", "createGitHubRelease"):
            if key in release and not isinstance(release.get(key), bool):
                errors.append(f"release.{key} muss bool sein")
        if "tagPrefix" in release and not isinstance(release.get("tagPrefix"), str):
            errors.append("release.tagPrefix muss String sein")
    if not isinstance(data.get("documentation"), dict):
        errors.append("documentation muss ein Objekt sein")
    return errors


def load_config(root: Path) -> ProjectConfig:
    root = root.resolve()
    path = root / ".project" / "project.config.json"
    if not path.is_file():
        raise ConfigError(f"Konfiguration fehlt: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Konfiguration ist kein gültiges JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("Konfiguration muss ein JSON-Objekt sein")
    errors = validate_config(data)
    if errors:
        raise ConfigError("; ".join(errors))
    return ProjectConfig(root=root, data=data)
