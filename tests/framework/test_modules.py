from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.companion.core.actions import ActionRegistry, INPUT_TOKEN
from tools.companion.core.config import ProjectConfig, load_config
from tools.companion.modules.powerplatform import register_powerplatform_actions
from tools.companion.modules.provisioning import register_provisioning_actions


class ModuleTests(unittest.TestCase):
    def test_optional_modules_match_repository_config(self):
        root = Path(__file__).resolve().parents[2]
        config = load_config(root)
        registry = ActionRegistry(root)
        register_powerplatform_actions(registry, root, config)
        register_provisioning_actions(registry, root, config)
        action_ids = {spec.id for spec in registry.all()}
        if config.enabled("powerPlatform") or config.data.get("powerPlatform", {}).get("enabled", False):
            self.assertIn("pac-version", action_ids)
        else:
            self.assertNotIn("pac-version", action_ids)
        if config.enabled("provisioning") or config.data.get("provisioning", {}).get("enabled", False):
            mode_script = config.path(str(config.data.get("provisioning", {}).get("modeScript") or ""))
            if mode_script and mode_script.is_file():
                self.assertIn("provision-dryrun", action_ids)
        else:
            self.assertNotIn("provision-dryrun", action_ids)

    def test_powerplatform_script_args_are_applied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "powerplatform/scripts/Fix.ps1"
            script.parent.mkdir(parents=True)
            script.write_text("# test", encoding="utf-8")
            config = ProjectConfig(root, {
                "modules": {"powerPlatform": True},
                "powerPlatform": {
                    "enabled": True,
                    "environmentUrl": "",
                    "scripts": {"canvasFixCheck": "powerplatform/scripts/Fix.ps1"},
                    "scriptArgs": {"canvasFixCheck": ["-CheckOnly"]},
                },
            })
            registry = ActionRegistry(root)
            register_powerplatform_actions(registry, root, config)
            spec = registry.get("pp-canvas-fix-check")
            self.assertIsNotNone(spec)
            self.assertEqual(spec.commands[0][-1], "-CheckOnly")
            self.assertIsNotNone(registry.get("pac-version"))

    def test_provisioning_registers_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "Provisioning/Invoke.ps1"
            script.parent.mkdir(parents=True)
            script.write_text("# test", encoding="utf-8")
            config = ProjectConfig(root, {
                "modules": {"provisioning": True},
                "provisioning": {"enabled": True, "modeScript": "Provisioning/Invoke.ps1", "applyConfirmation": "APPLY SCHEMA"},
            })
            registry = ActionRegistry(root)
            register_provisioning_actions(registry, root, config)
            self.assertEqual(registry.get("provision-apply").confirmation, "APPLY SCHEMA")

    def test_provisioning_registers_reset_and_seed_extensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("Invoke.ps1", "Reset.ps1", "Seed.ps1"):
                path = root / "Provisioning" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# test", encoding="utf-8")
            config = ProjectConfig(root, {
                "modules": {"provisioning": True},
                "provisioning": {
                    "enabled": True,
                    "modeScript": "Provisioning/Invoke.ps1",
                    "resetScript": "Provisioning/Reset.ps1",
                    "seedScript": "Provisioning/Seed.ps1",
                    "seedApplyConfirmation": "APPLY SEED",
                },
            })
            registry = ActionRegistry(root)
            register_provisioning_actions(registry, root, config)
            reset = registry.get("reset-apply")
            self.assertIsNotNone(reset)
            self.assertTrue(reset.input_required)
            self.assertIn(INPUT_TOKEN, reset.commands[0])
            self.assertIsNotNone(registry.get("reset-dryrun"))
            self.assertIsNotNone(registry.get("seed-dryrun"))
            self.assertIsNotNone(registry.get("seed-validate"))
            self.assertEqual(registry.get("seed-apply").confirmation, "APPLY SEED")


if __name__ == "__main__":
    unittest.main()
