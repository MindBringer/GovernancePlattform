from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.companion.core.config import ConfigError, ProjectConfig, load_config, validate_config


class ConfigTests(unittest.TestCase):
    def test_repository_config_is_valid(self):
        root = Path(__file__).resolve().parents[2]
        config = load_config(root)
        self.assertNotEqual(config.framework_version, "unknown")
        self.assertTrue(config.project["key"])
        self.assertNotEqual(config.version(), "unknown")
        self.assertTrue(config.data["quality"]["projectMemoryContract"])
        self.assertTrue(config.data["quality"]["technicalDebtReview"])
        self.assertTrue(config.companion_url().startswith("http://"))
        if config.project["key"] == "project-template":
            expected_version = (root / "VERSION").read_text(encoding="utf-8").strip()
            self.assertEqual(config.framework_version, expected_version)
            self.assertEqual(config.version(), expected_version)
            self.assertEqual(config.data["quality"]["supportedPython"], ["3.12", "3.14"])
            self.assertEqual(config.data["quality"]["ciPlatforms"], ["ubuntu", "macos", "windows"])
            self.assertTrue(config.data["release"]["createTag"])
            self.assertTrue(config.data["release"]["createGitHubRelease"])
            self.assertTrue(config.data["ui"]["projectUI"]["enabled"])
            self.assertTrue(config.data["ui"]["projectUI"]["allowCustomAssets"])

    def test_reference_configs_track_framework_version(self):
        root = Path(__file__).resolve().parents[2]
        repository_config = json.loads((root / ".project/project.config.json").read_text(encoding="utf-8"))
        if repository_config.get("project", {}).get("key") != "project-template":
            self.skipTest("Template reference configs are not part of consumer repositories")
        framework_version = str(repository_config["frameworkVersion"])
        examples = root / "examples"
        for name in (
            "project.config.governance.json",
            "project.config.userlifecycle.json",
            "project.config.portfolio.json",
        ):
            payload = json.loads((examples / name).read_text(encoding="utf-8"))
            self.assertEqual(payload["frameworkVersion"], framework_version, name)
            self.assertEqual(validate_config(payload), [], name)
        lifecycle = json.loads((examples / "project.config.userlifecycle.json").read_text(encoding="utf-8"))
        self.assertEqual(lifecycle["provisioning"]["resetScript"], "Provisioning/Invoke-ResetLocal.ps1")
        self.assertEqual(lifecycle["provisioning"]["seedScript"], "Provisioning/Invoke-SeedLocal.ps1")
        portfolio = json.loads((examples / "project.config.portfolio.json").read_text(encoding="utf-8"))
        self.assertEqual(portfolio["companion"]["port"], 8775)
        self.assertEqual(
            ProjectConfig(root, portfolio).companion_url(),
            "http://127.0.0.1:8775/",
        )
        self.assertTrue((examples / "project_runtime.portfolio.py").is_file())
        self.assertTrue((examples / "project_actions.governance.py").is_file())

    def test_project_root_is_canonicalized(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = ProjectConfig(root, {"project": {"versionFile": "VERSION"}})
            self.assertEqual(cfg.root, root.resolve())

    def test_companion_url_uses_configured_loopback_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = ProjectConfig(
                Path(tmp),
                {
                    "project": {"versionFile": "VERSION"},
                    "companion": {"host": "127.0.0.1", "port": 8775},
                },
            )
            self.assertEqual(cfg.companion_url(), "http://127.0.0.1:8775/")

    def test_json_version_file_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config/version.json").write_text('{"version":"8.8.19"}', encoding="utf-8")
            cfg = ProjectConfig(root, {"project": {"versionFile": "config/version.json", "versionJsonKey": "version"}})
            self.assertEqual(cfg.version(), "8.8.19")

    def test_path_cannot_escape_repo(self):
        root = Path(__file__).resolve().parents[2]
        config = load_config(root)
        with self.assertRaises(ConfigError):
            config.path("../../outside")

    def test_invalid_schema_version_is_rejected(self):
        root = Path(__file__).resolve().parents[2]
        payload = json.loads((root / ".project/project.config.json").read_text(encoding="utf-8"))
        payload["schemaVersion"] = 99
        self.assertIn("schemaVersion muss 1 sein", validate_config(payload))

    def test_quality_contract_is_required(self):
        root = Path(__file__).resolve().parents[2]
        payload = json.loads((root / ".project/project.config.json").read_text(encoding="utf-8"))
        payload.pop("quality")
        self.assertIn("quality muss ein Objekt sein", validate_config(payload))

    def test_invalid_ci_platform_is_rejected(self):
        root = Path(__file__).resolve().parents[2]
        payload = json.loads((root / ".project/project.config.json").read_text(encoding="utf-8"))
        payload["quality"]["ciPlatforms"] = ["ubuntu", "solaris"]
        self.assertIn("quality.ciPlatforms enthält ungültige Plattformen", validate_config(payload))

    def test_release_artifact_flags_must_be_boolean(self):
        root = Path(__file__).resolve().parents[2]
        payload = json.loads((root / ".project/project.config.json").read_text(encoding="utf-8"))
        payload["release"]["createTag"] = "yes"
        self.assertIn("release.createTag muss bool sein", validate_config(payload))

    def test_project_ui_flags_must_be_boolean(self):
        root = Path(__file__).resolve().parents[2]
        payload = json.loads((root / ".project/project.config.json").read_text(encoding="utf-8"))
        payload["ui"]["projectUI"]["enabled"] = "yes"
        payload["ui"]["projectUI"]["allowCustomAssets"] = 1
        errors = validate_config(payload)
        self.assertIn("ui.projectUI.enabled muss bool sein", errors)
        self.assertIn("ui.projectUI.allowCustomAssets muss bool sein", errors)


if __name__ == "__main__":
    unittest.main()
