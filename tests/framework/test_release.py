from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from tools.companion.core.actions import ActionRegistry
from tools.companion.core.base_actions import register_base_actions
from tools.companion.core.config import load_config
from tools.companion.core.process import CommandResult
from tools.companion.core.release import ReleaseEngine


class ReleaseTests(unittest.TestCase):
    def _engine(self) -> tuple[ReleaseEngine, object]:
        root = Path(__file__).resolve().parents[2]
        config = load_config(root)
        registry = ActionRegistry(root)
        register_base_actions(registry, root, config)
        return ReleaseEngine(root, config, registry), config

    def test_release_includes_mandatory_contract_and_configured_gates(self):
        engine, config = self._engine()
        gates = engine._gate_ids(config.data["release"])
        self.assertIn("repo-audit", gates)
        self.assertIn("technical-debt-review", gates)
        self.assertIn("project-memory-contract", gates)
        self.assertIn("framework-validate", gates)
        self.assertIn("syntax-check", gates)
        self.assertIn("tests", gates)
        for configured in config.data["release"].get("gates", []):
            self.assertIn(configured, gates)
        if config.project["key"] == "project-template":
            self.assertIn("bootstrap-smoke", gates)
        self.assertEqual(len(gates), len(set(gates)))

    def test_framework_validate_and_engineering_contract_are_non_mutating(self):
        root = Path(__file__).resolve().parents[2]
        config = load_config(root)
        registry = ActionRegistry(root)
        register_base_actions(registry, root, config)
        validate = registry.get("framework-validate")
        contract = registry.get("engineering-contract")
        integrity = registry.get("framework-integrity")
        self.assertIsNotNone(validate)
        self.assertIsNotNone(contract)
        self.assertIsNotNone(integrity)
        self.assertIn([__import__("sys").executable, "tools/framework/sync.py", "integrity"], validate.commands)
        self.assertNotIn([__import__("sys").executable, "tools/framework/sync.py", "lock"], contract.commands)
        if config.project["key"] == "project-template":
            self.assertIsNotNone(registry.get("framework-lock-refresh"))

    def test_release_artifact_action_follows_config(self):
        root = Path(__file__).resolve().parents[2]
        config = load_config(root)
        registry = ActionRegistry(root)
        register_base_actions(registry, root, config)
        if config.project["key"] == "project-template":
            self.assertIsNotNone(registry.get("bootstrap-smoke"))
        else:
            self.assertIsNone(registry.get("bootstrap-smoke"))
        artifacts = registry.get("release-artifacts")
        if config.data["release"].get("createTag", True) or config.data["release"].get("createGitHubRelease", False):
            self.assertIsNotNone(artifacts)
            self.assertEqual(artifacts.confirmation, "PUBLISH RELEASE")
        else:
            self.assertIsNone(artifacts)

    def test_versioned_release_history_advances_to_current_version(self):
        self.assertEqual(
            ("docs/releases/8.9.6.md", True),
            ReleaseEngine._versioned_release_history_path("docs/releases/8.9.5.md", "8.9.6"),
        )
        self.assertEqual(
            ("docs/releases/1.3.7.md", True),
            ReleaseEngine._versioned_release_history_path("docs/releases/1.3.6.md", "1.3.7"),
        )

    def test_generic_release_history_path_is_not_rewritten(self):
        self.assertEqual(
            ("docs/project/Release-History.md", False),
            ReleaseEngine._versioned_release_history_path("docs/project/Release-History.md", "1.3.7"),
        )

    @patch("tools.companion.core.release.time.sleep", return_value=None)
    @patch("tools.companion.core.release.run_command")
    def test_pr_checks_wait_for_exact_current_head(self, run_mock, _sleep_mock):
        engine, config = self._engine()
        expected = "a" * 40
        old = "b" * 40
        run_mock.side_effect = [
            CommandResult(["git", "rev-parse", "HEAD"], 0, expected + "\n"),
            CommandResult(["gh", "pr", "view"], 0, old + "\n"),
            CommandResult(["gh", "pr", "view"], 0, expected + "\n"),
            CommandResult(["gh", "pr", "checks"], 1, "no checks reported on the 'feature' branch\n"),
            CommandResult(["gh", "pr", "view"], 0, expected + "\n"),
            CommandResult(["gh", "pr", "checks"], 0, "validate-build\tpass\n"),
            CommandResult(["gh", "pr", "checks", "--watch"], 0, "validate-build\tpass\n"),
            CommandResult(["gh", "pr", "view"], 0, expected + "\n"),
        ]
        log: list[str] = []
        result = engine._wait_for_pr_checks(log, config.data["release"], 62)
        self.assertEqual(result, expected)

        commands = [call.args[1] for call in run_mock.call_args_list]
        self.assertEqual(commands[0], ["git", "rev-parse", "HEAD"])
        self.assertEqual(
            commands[1],
            ["gh", "pr", "view", "62", "--json", "headRefOid", "--jq", ".headRefOid"],
        )
        self.assertIn(["gh", "pr", "checks", "62"], commands)
        self.assertIn(["gh", "pr", "checks", "62", "--watch", "--fail-fast"], commands)
        self.assertTrue(any("noch nicht auf lokalem Head" in line for line in log))
        self.assertTrue(any("noch nicht registriert" in line for line in log))

    def test_release_merge_is_pinned_to_validated_head(self):
        source = Path(__file__).resolve().parents[2].joinpath("tools/companion/core/release.py").read_text(encoding="utf-8")
        self.assertIn('"--match-head-commit", final_head', source)
        self.assertIn('"gh", "pr", "merge", str(pr_number)', source)

    def test_release_reports_named_progress_phases_without_command_output(self):
        source = Path(__file__).resolve().parents[2].joinpath("tools/companion/core/release.py").read_text(encoding="utf-8")
        for phase in (
            '"preflight"',
            '"local-gates"',
            '"synchronize"',
            '"candidate-ci"',
            '"final-ci"',
            '"merge"',
            '"artifacts"',
            '"completed"',
        ):
            self.assertIn(phase, source)
        self.assertIn("Callable[[dict[str, object]], None]", source)

    def test_final_release_updates_next_step_and_versioned_history_config(self):
        source = Path(__file__).resolve().parents[2].joinpath("tools/companion/core/release.py").read_text(encoding="utf-8")
        self.assertIn('configured_next = iteration.get("postReleaseNextStep")', source)
        self.assertIn('config_docs["releaseHistory"] = history_rel', source)
        self.assertIn('"next-step": str((state.get("nextStep") or {}).get("id")', source)


if __name__ == "__main__":
    unittest.main()
