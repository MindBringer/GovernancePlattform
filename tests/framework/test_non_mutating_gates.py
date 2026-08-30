from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.companion.core.actions import ActionRegistry
from tools.companion.core.base_actions import register_base_actions
from tools.companion.core.config import ProjectConfig
from tools.companion.core.release import ReleaseEngine


class NonMutatingGateContractTests(unittest.TestCase):
    def _registry(self) -> tuple[ActionRegistry, ProjectConfig]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "VERSION").write_text("1.3.11\n", encoding="utf-8")
        config = ProjectConfig(
            root=root,
            data={
                "frameworkVersion": "1.3.11",
                "project": {
                    "key": "test-consumer",
                    "name": "Test Consumer",
                    "versionFile": "VERSION",
                },
                "modules": {
                    "git": False,
                    "audit": True,
                    "build": True,
                    "release": True,
                },
                "quality": {
                    "projectMemoryContract": True,
                    "technicalDebtReview": True,
                },
                "release": {
                    "createTag": False,
                    "createGitHubRelease": False,
                    "gates": ["engineering-contract", "build"],
                },
            },
        )
        registry = ActionRegistry(root)
        register_base_actions(registry, root, config)
        return registry, config

    @staticmethod
    def _flatten_commands(registry: ActionRegistry, action_id: str) -> list[str]:
        spec = registry.get(action_id)
        if spec is None:
            raise AssertionError(f"Action fehlt: {action_id}")
        return [arg for command in spec.commands for arg in command]

    def test_backward_compatible_release_review_gate_is_non_mutating(self):
        registry, config = self._registry()
        engine = ReleaseEngine(registry.root, config, registry)

        gate_ids = engine._gate_ids(config.data["release"])
        self.assertIn("technical-debt-review", gate_ids)
        self.assertNotIn("--review", self._flatten_commands(registry, "technical-debt-review"))
        self.assertTrue(registry.get("technical-debt-review").non_mutating)

    def test_all_registered_base_release_gates_declare_non_mutating_contract(self):
        registry, config = self._registry()
        engine = ReleaseEngine(registry.root, config, registry)

        for gate_id in engine._gate_ids(config.data["release"]):
            spec = registry.get(gate_id)
            self.assertIsNotNone(spec, gate_id)
            self.assertTrue(spec.non_mutating, gate_id)

    def test_engineering_contract_never_records_technical_debt_review(self):
        registry, _ = self._registry()
        self.assertNotIn("--review", self._flatten_commands(registry, "engineering-contract"))
        self.assertNotIn("--review", self._flatten_commands(registry, "build"))
        self.assertNotIn("--review", self._flatten_commands(registry, "technical-debt-check"))

    def test_review_recording_is_explicit_separate_mutating_action(self):
        registry, _ = self._registry()
        record = registry.get("technical-debt-record")
        self.assertIsNotNone(record)
        self.assertFalse(record.non_mutating)
        args = self._flatten_commands(registry, "technical-debt-record")
        self.assertIn("tools/framework/technical_debt.py", args)
        self.assertIn("--review", args)


if __name__ == "__main__":
    unittest.main()
