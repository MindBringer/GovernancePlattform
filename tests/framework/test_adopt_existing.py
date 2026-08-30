from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class AdoptExistingTests(unittest.TestCase):
    def test_adoption_preserves_legacy_file_and_builds_valid_lock(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "legacy"
            target.mkdir()
            subprocess.run(["git", "init", str(target)], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            subprocess.run(["git", "-C", str(target), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(target), "config", "user.name", "Framework Test"], check=True)
            (target / "start-local.sh").write_text("#!/bin/sh\necho legacy\n", encoding="utf-8")
            (target / "legacy.txt").write_text("fachliche quelle\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(target), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(target), "commit", "-m", "legacy baseline"], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            command = [
                sys.executable,
                str(root / "tools/framework/adopt_existing.py"),
                "--target", str(target),
                "--key", "legacy-project",
                "--name", "Legacy Project",
                "--description", "Existing repository adoption test",
                "--version", "2.0.0",
                "--version-file", "powerplatform/VERSION",
                "--port", "8780",
                "--power-platform",
                "--provisioning",
            ]
            result = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue((target / "legacy.txt").is_file())
            self.assertEqual((target / "powerplatform/VERSION").read_text(encoding="utf-8").strip(), "2.0.0")
            self.assertTrue((target / "tools/companion/project_runtime.py").is_file())

            config = json.loads((target / ".project/project.config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["project"]["key"], "legacy-project")
            self.assertEqual(config["companion"]["port"], 8780)
            self.assertTrue(config["powerPlatform"]["enabled"])
            self.assertTrue(config["provisioning"]["enabled"])
            self.assertNotIn("bootstrap-smoke", config["release"]["gates"])

            state = json.loads((target / ".project/state/current.json").read_text(encoding="utf-8"))
            self.assertIn("Runtime", state["nextStep"]["description"])

            backups = list((target / ".framework-adoption-backup").glob("*/start-local.sh"))
            self.assertEqual(len(backups), 1)
            self.assertIn("echo legacy", backups[0].read_text(encoding="utf-8"))
            self.assertIn(".framework-adoption-backup/", (target / ".gitignore").read_text(encoding="utf-8"))

            verify = subprocess.run(
                [sys.executable, str(target / "tools/framework/sync.py"), "verify-lock"],
                cwd=target,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(verify.returncode, 0, verify.stdout)


if __name__ == "__main__":
    unittest.main()
