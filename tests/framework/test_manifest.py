from __future__ import annotations

import json
import unittest
from pathlib import Path


class ManifestTests(unittest.TestCase):
    def test_owned_paths_are_not_managed(self):
        root = Path(__file__).resolve().parents[2]
        manifest = json.loads((root / ".project/framework.manifest.json").read_text(encoding="utf-8"))
        managed = set(manifest["managed"])
        project_owned = set(manifest["projectOwned"])
        self.assertTrue(managed.isdisjoint(project_owned))
        self.assertIn("tools/companion/project_actions.py", project_owned)
        self.assertNotIn("tools/companion/project_actions.py", managed)
        self.assertIn("tools/companion/project_runtime.py", project_owned)
        self.assertNotIn("tools/companion/project_runtime.py", managed)
        self.assertIn("tools/companion/project_ui.py", project_owned)
        self.assertIn("tools/companion/project_web", project_owned)
        self.assertNotIn("tools/companion/project_ui.py", managed)
        self.assertNotIn("tools/companion/project_web", managed)
        self.assertIn("AGENTS.md", project_owned)
        self.assertIn(".project/framework/AGENT_CONTRACT.md", managed)

    def test_framework_version_matches_project_config(self):
        root = Path(__file__).resolve().parents[2]
        manifest = json.loads((root / ".project/framework.manifest.json").read_text(encoding="utf-8"))
        config = json.loads((root / ".project/project.config.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["frameworkVersion"], config["frameworkVersion"])

    def test_template_version_file_matches_framework_version_only_for_template_repo(self):
        root = Path(__file__).resolve().parents[2]
        config = json.loads((root / ".project/project.config.json").read_text(encoding="utf-8"))
        if config.get("project", {}).get("key") == "project-template":
            self.assertEqual(config["frameworkVersion"], (root / "VERSION").read_text().strip())


if __name__ == "__main__":
    unittest.main()
