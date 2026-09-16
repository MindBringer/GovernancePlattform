# GovernancePlattform project-owned Companion actions.

from __future__ import annotations

import sys
from pathlib import Path

from tools.companion.core.actions import ActionRegistry, ActionSpec
from tools.companion.core.config import ProjectConfig


def register_project_actions(
    registry: ActionRegistry,
    root: Path,
    config: ProjectConfig,
) -> None:
    python = sys.executable
    pac = "tools/companion/pac_workflow.py"

    registry.register(ActionSpec(
        id="governance-repository-audit",
        label="Governance Repository Audit",
        category="Governance · Qualität",
        description="Prüft den bestehenden Governance-Repository-Vertrag read-only.",
        commands=[[python, "tools/companion/audit_repo.py"]],
        non_mutating=True,
        timeout=120,
    ))

    registry.register(ActionSpec(
        id="governance-provider-registry-check",
        label="Provider Registry prüfen",
        category="Governance · Qualität",
        description="Validiert die Stage-4.1 Object-Provider-Registry ohne Änderungen.",
        commands=[["pwsh", "powerplatform/scripts/Validate-ObjectProviderRegistry.ps1"]],
        non_mutating=True,
        timeout=120,
    ))

    registry.register(ActionSpec(
        id="governance-pac-check",
        label="Governance PAC prüfen",
        category="Governance · ALM",
        description="Prüft PAC-Verfügbarkeit und Auth-Profile ohne Repository-Write.",
        commands=[[python, pac, "check"]],
        non_mutating=True,
        timeout=180,
    ))

    registry.register(ActionSpec(
        id="governance-git-diff",
        label="Governance Git-Diff",
        category="Governance · ALM",
        description="Zeigt Repository-Status und Diff ohne Änderungen.",
        commands=[[python, pac, "git-diff"]],
        non_mutating=True,
        timeout=120,
    ))

    registry.register(ActionSpec(
        id="governance-pac-select-dev",
        label="PAC DEV-Profil auswählen",
        category="Governance · ALM",
        description="Wählt das konfigurierte PAC-DEV-Profil aus.",
        commands=[[python, pac, "select-dev"]],
        confirmation="PAC DEV AUSWÄHLEN",
        danger=True,
        timeout=180,
    ))

    registry.register(ActionSpec(
        id="governance-pac-export",
        label="Solution aus DEV exportieren",
        category="Governance · ALM",
        description="Exportiert die konfigurierte DEV-Solution in den lokalen Workspace.",
        commands=[[python, pac, "export"]],
        confirmation="DEV EXPORTIEREN",
        danger=True,
        background=True,
        timeout=3600,
    ))

    registry.register(ActionSpec(
        id="governance-pac-unpack",
        label="DEV-Export entpacken",
        category="Governance · ALM",
        description="Entpackt einen vorhandenen DEV-Export in die lokale Solution.",
        commands=[[python, pac, "unpack"]],
        confirmation="EXPORT ENTPACKEN",
        danger=True,
        background=True,
        timeout=3600,
    ))

    registry.register(ActionSpec(
        id="governance-canvas-sync",
        label="Canvas nach Git-SourceTree übernehmen",
        category="Governance · ALM",
        description="Synchronisiert den entpackten Canvas-Stand in den Git-SourceTree.",
        commands=[[python, pac, "canvas-sync"]],
        confirmation="CANVAS NACH GIT ÜBERNEHMEN",
        danger=True,
        background=True,
        timeout=3600,
    ))

    registry.register(ActionSpec(
        id="governance-studio-sync",
        label="Studio Sync · DEV → Git",
        category="Governance · ALM",
        description="Exportiert DEV, entpackt die Solution, synchronisiert Canvas und zeigt den Git-Diff.",
        commands=[[python, pac, "studio-sync"]],
        confirmation="DEV NACH GIT ÜBERNEHMEN",
        danger=True,
        background=True,
        timeout=3600,
    ))

    registry.register(ActionSpec(
        id="governance-pac-import",
        label="Solution nach DEV importieren",
        category="Governance · Deployment",
        description="Importiert das passende Solution-Paket nach DEV und veröffentlicht Änderungen.",
        commands=[[python, pac, "import"]],
        confirmation="NACH DEV IMPORTIEREN",
        danger=True,
        background=True,
        timeout=3600,
    ))

    registry.register(ActionSpec(
        id="governance-publish-all",
        label="Publish All · DEV",
        category="Governance · Deployment",
        description="Veröffentlicht umgebungsweit alle ausstehenden DEV-Customizations.",
        commands=[[python, pac, "publish"]],
        confirmation="PUBLISH ALL DEV",
        danger=True,
        background=True,
        timeout=3600,
    ))

    registry.register(ActionSpec(
        id="governance-deploy-dev",
        label="Build + Import + Publish · DEV",
        category="Governance · Deployment",
        description="Führt den Governance Deploy-to-DEV-Workflow aus und verändert die DEV-Umgebung.",
        commands=[[python, pac, "deploy-dev"]],
        confirmation="NACH DEV DEPLOYEN",
        danger=True,
        background=True,
        timeout=3600,
    ))
