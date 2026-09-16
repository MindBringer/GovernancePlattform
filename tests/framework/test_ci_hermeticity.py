from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.framework.ci_hermeticity import inspect


class CiHermeticityTests(unittest.TestCase):
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

    def test_clean_checkout_without_sensitive_context_is_accepted(self):
        root = self._repo()
        result = inspect(root, {
            "GITHUB_WORKSPACE": str(root),
            "RUNNER_TEMP": str(root / ".runner-temp"),
            "PATH": "/usr/bin:/bin",
            "GITHUB_TOKEN": "platform-managed",
        })
        self.assertTrue(result["ok"], result)

    def test_dirty_checkout_is_rejected(self):
        root = self._repo()
        (root / "untracked.tmp").write_text("stale\n", encoding="utf-8")
        result = inspect(root, {"GITHUB_WORKSPACE": str(root)})
        self.assertFalse(result["ok"])
        self.assertIn("dirty-checkout", [item["type"] for item in result["findings"]])

    def test_local_env_file_is_rejected_even_when_ignored(self):
        root = self._repo()
        (root / ".gitignore").write_text(".env\n", encoding="utf-8")
        subprocess.run(["git", "add", ".gitignore"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "ignore env"], cwd=root, check=True)
        (root / ".env").write_text("SECRET=value\n", encoding="utf-8")
        result = inspect(root, {"GITHUB_WORKSPACE": str(root)})
        self.assertFalse(result["ok"])
        self.assertIn("local-config-file", [item["type"] for item in result["findings"]])

    def test_inherited_sensitive_environment_is_rejected_but_explicit_allowlist_works(self):
        root = self._repo()
        env = {
            "GITHUB_WORKSPACE": str(root),
            "FOODLAB_API_KEY": "secret",
        }
        blocked = inspect(root, env)
        self.assertFalse(blocked["ok"])
        self.assertIn("sensitive-environment", [item["type"] for item in blocked["findings"]])

        env["ENGINEERING_CI_ALLOWED_ENV"] = "FOODLAB_API_KEY"
        allowed = inspect(root, env)
        self.assertTrue(allowed["ok"], allowed)

    def test_external_workspace_context_is_rejected(self):
        root = self._repo()
        result = inspect(root, {
            "GITHUB_WORKSPACE": str(root),
            "CASHFLOW_WORKSPACE": "/Users/example/private-workspace",
        })
        self.assertFalse(result["ok"])
        self.assertIn("external-runtime-context", [item["type"] for item in result["findings"]])


if __name__ == "__main__":
    unittest.main()
