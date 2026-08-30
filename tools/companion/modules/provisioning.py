from __future__ import annotations

from pathlib import Path

from ..core.actions import ActionRegistry, ActionSpec, INPUT_TOKEN
from ..core.config import ProjectConfig


def _script(config: ProjectConfig, value: object) -> str | None:
    path = config.path(str(value or ""))
    if not path or not path.is_file():
        return None
    return str(path.relative_to(config.root))


def register_provisioning_actions(registry: ActionRegistry, root: Path, config: ProjectConfig) -> None:
    provisioning = config.data.get("provisioning", {})
    if not config.enabled("provisioning") and not provisioning.get("enabled", False):
        return

    relative = _script(config, provisioning.get("modeScript"))
    if relative:
        registry.register(ActionSpec(
            id="provision-dryrun", label="Provisioning Dry Run", category="Provisioning",
            description="Ermittelt Änderungen ohne Schreibzugriff.",
            commands=[["pwsh", relative, "-Mode", "DryRun"]], timeout=3600,
        ))
        registry.register(ActionSpec(
            id="provision-validate", label="Provisioning validieren", category="Provisioning",
            description="Validiert den Ist-/Soll-Zustand.",
            commands=[["pwsh", relative, "-Mode", "Validate"]], timeout=3600,
        ))
        registry.register(ActionSpec(
            id="provision-apply", label="Provisioning anwenden", category="Provisioning",
            description="Wendet deklarative Änderungen auf das Zielsystem an.",
            commands=[["pwsh", relative, "-Mode", "Apply"]], timeout=3600,
            confirmation=str(provisioning.get("applyConfirmation") or "APPLY SCHEMA"), danger=True,
        ))

    reset_relative = _script(config, provisioning.get("resetScript"))
    if reset_relative:
        token_arg = str(provisioning.get("resetTokenArgument") or "-ConfirmationToken")
        registry.register(ActionSpec(
            id="reset-dryrun", label="Reset Dry Run", category="Provisioning",
            description="Zeigt kontrollierte Löschziele und erzeugt das Reset-Bestätigungstoken.",
            commands=[["pwsh", reset_relative, "-Mode", "DryRun"]], timeout=3600,
        ))
        registry.register(ActionSpec(
            id="reset-apply", label="Kontrollierten Reset anwenden", category="Provisioning",
            description="Wendet den Reset mit dem Token aus dem Dry Run an.",
            commands=[["pwsh", reset_relative, "-Mode", "Apply", token_arg, INPUT_TOKEN]], timeout=3600,
            input_label=str(provisioning.get("resetInputLabel") or "Reset-Token aus dem Dry Run"),
            input_placeholder=str(provisioning.get("resetInputPlaceholder") or "RESET|https://...|schemaVersion"),
            input_required=True,
            danger=True,
        ))

    seed_relative = _script(config, provisioning.get("seedScript"))
    if seed_relative:
        registry.register(ActionSpec(
            id="seed-dryrun", label="Seed Dry Run", category="Provisioning",
            description="Prüft deklarative Seed-Daten ohne Schreibzugriff.",
            commands=[["pwsh", seed_relative, "-Mode", "DryRun"]], timeout=3600,
        ))
        registry.register(ActionSpec(
            id="seed-validate", label="Seed validieren", category="Provisioning",
            description="Validiert den aktuellen Seed-Zustand.",
            commands=[["pwsh", seed_relative, "-Mode", "Validate"]], timeout=3600,
        ))
        registry.register(ActionSpec(
            id="seed-apply", label="Seed anwenden", category="Provisioning",
            description="Wendet deklarative Seed-Daten idempotent an.",
            commands=[["pwsh", seed_relative, "-Mode", "Apply"]], timeout=3600,
            confirmation=str(provisioning.get("seedApplyConfirmation") or "APPLY SEED"), danger=True,
        ))
