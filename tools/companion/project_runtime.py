"""Project-owned local runtime adapter.

Register existing product servers here. The framework starts them without shell=True,
checks a loopback health URL and stops only child processes that it owns.
"""
from __future__ import annotations

from pathlib import Path

from tools.companion.core.config import ProjectConfig
from tools.companion.core.project_runtime import ProjectRuntimeRegistry


def register_project_runtimes(
    registry: ProjectRuntimeRegistry,
    root: Path,
    config: ProjectConfig,
) -> None:
    # Beispiel für ein bestehendes lokales Produkt-Cockpit:
    # from tools.companion.core.project_runtime import ProjectRuntimeSpec
    # registry.register(ProjectRuntimeSpec(
    #     id="product-app",
    #     label="Product App",
    #     command=[".venv/bin/python", "app/server.py", "--no-browser"],
    #     url="http://127.0.0.1:8765/",
    #     health_url="http://127.0.0.1:8765/api/health",
    #     auto_start=True,
    #     open_browser=True,
    # ))
    return
