"""Project-owned Companion UI adapter.

This file is intentionally NOT framework-managed. Register project-specific read-only
cockpit views here. Mutating operations must stay in project_actions.py so they keep
the ActionRegistry allowlist, POST/CSRF protection and confirmation semantics.

For simple views use the generic JSON component contract. Rich views may opt into a
project-owned renderer from tools/companion/project_web when ui.projectUI.allowCustomAssets
is enabled in .project/project.config.json.
"""
from __future__ import annotations

from pathlib import Path

from tools.companion.core.config import ProjectConfig
from tools.companion.core.ui_extensions import ProjectUIRegistry, ProjectViewSpec


def register_project_ui(registry: ProjectUIRegistry, root: Path, config: ProjectConfig) -> None:
    # Example generic cockpit view:
    # def overview() -> dict:
    #     return {
    #         "status": {"label": "Bereit", "level": "good", "detail": "Projekt-Cockpit aktiv"},
    #         "metrics": [
    #             {"label": "Services", "value": "8/8", "level": "good"},
    #         ],
    #         "sections": [
    #             {
    #                 "kind": "table",
    #                 "title": "Komponenten",
    #                 "columns": [
    #                     {"key": "name", "label": "Komponente"},
    #                     {"key": "status", "label": "Status"},
    #                 ],
    #                 "rows": [
    #                     {"name": "API", "status": "OK"},
    #                 ],
    #             }
    #         ],
    #         "actions": ["project-selftest"],
    #     }
    #
    # registry.register(ProjectViewSpec(
    #     id="project-overview",
    #     label="Projekt",
    #     title="Projekt-Cockpit",
    #     description="Projektbezogener Betriebs- und Anwendungsstatus",
    #     order=20,
    #     dashboard=True,
    #     refresh_seconds=30,
    #     provider=overview,
    # ))
    #
    # Rich UI example (project-owned assets):
    # registry.register(ProjectViewSpec(
    #     id="project-rich",
    #     label="Rich UI",
    #     renderer="custom",
    #     script="rich.js",
    #     stylesheet="rich.css",
    #     provider=overview,
    # ))
    return
