from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.companion.core.actions import ActionRegistry, ActionSpec


class ActionMutationGuardTests(unittest.TestCase):
    def _repo(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "framework-test@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Framework Test"], cwd=root, check=True)
        (root / "tracked.txt").write_text("baseline\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "baseline"], cwd=root, check=True)
        return root

    def test_non_mutating_action_rejects_tracked_file_change_and_names_path(self):
        root = self._repo()
        registry = ActionRegistry(root)
        registry.register(ActionSpec(
            id="mutating-gate",
            label="Mutating Gate",
            category="Test",
            commands=[[
                sys.executable,
                "-c",
                "from pathlib import Path; Path('tracked.txt').write_text('changed\\n', encoding='utf-8')",
            ]],
            non_mutating=True,
        ))

        result = registry.execute("mutating-gate")

        self.assertFalse(result["ok"])
        self.assertEqual(result["exitCode"], 409)
        self.assertEqual(result.get("worktreeMutation"), ["tracked.txt"])
        self.assertIn("Non-Mutating-Contract verletzt", result["output"])
        self.assertIn("tracked.txt", result["output"])

    def test_non_mutating_action_allows_preexisting_dirty_state_if_unchanged(self):
        root = self._repo()
        (root / "tracked.txt").write_text("already dirty\n", encoding="utf-8")
        registry = ActionRegistry(root)
        registry.register(ActionSpec(
            id="read-only-gate",
            label="Read-only Gate",
            category="Test",
            commands=[[sys.executable, "-c", "print('ok')"]],
            non_mutating=True,
        ))

        result = registry.execute("read-only-gate")

        self.assertTrue(result["ok"])
        self.assertEqual(result["exitCode"], 0)
        self.assertIn("ok", result["output"])

    def test_non_mutating_guard_does_not_require_head_commit(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        (root / "tracked.txt").write_text("staged baseline\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
        registry = ActionRegistry(root)
        registry.register(ActionSpec(
            id="pre-commit-gate",
            label="Pre-commit Gate",
            category="Test",
            commands=[[sys.executable, "-c", "print('ok')"]],
            non_mutating=True,
        ))

        result = registry.execute("pre-commit-gate")

        self.assertTrue(result["ok"])
        self.assertEqual(result["exitCode"], 0)

    def test_action_public_contract_exposes_non_mutating_flag(self):
        spec = ActionSpec(
            id="gate",
            label="Gate",
            category="Test",
            commands=[[sys.executable, "--version"]],
            non_mutating=True,
        )
        self.assertTrue(spec.public()["nonMutating"])


if __name__ == "__main__":
    unittest.main()
