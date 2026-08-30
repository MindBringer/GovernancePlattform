from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.companion.core.config import ProjectConfig
from tools.companion.core.ui_extensions import ProjectUIError, ProjectUIRegistry, ProjectViewSpec, load_project_ui


class ProjectUITests(unittest.TestCase):
    def test_generic_view_registration_and_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = ProjectUIRegistry(root)
            registry.register(ProjectViewSpec(
                id="overview",
                label="Overview",
                dashboard=True,
                refresh_seconds=30,
                provider=lambda: {"metrics": [{"label": "Health", "value": "OK"}]},
            ))
            self.assertEqual([item["id"] for item in registry.public()], ["overview"])
            self.assertEqual(registry.data("overview")["metrics"][0]["value"], "OK")

    def test_duplicate_view_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = ProjectUIRegistry(Path(tmp))
            registry.register(ProjectViewSpec(id="overview", label="One"))
            with self.assertRaises(ProjectUIError):
                registry.register(ProjectViewSpec(id="overview", label="Two"))

    def test_invalid_view_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = ProjectUIRegistry(Path(tmp))
            with self.assertRaises(ProjectUIError):
                registry.register(ProjectViewSpec(id="../escape", label="Bad"))

    def test_provider_must_return_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = ProjectUIRegistry(Path(tmp))
            registry.register(ProjectViewSpec(id="overview", label="Overview", provider=lambda: [1, 2, 3]))
            with self.assertRaises(ProjectUIError):
                registry.data("overview")

    def test_custom_assets_need_opt_in_and_stay_in_project_web(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            web = root / "tools/companion/project_web"
            web.mkdir(parents=True)
            (web / "rich.js").write_text("window.x=1;", encoding="utf-8")
            with self.assertRaises(ProjectUIError):
                ProjectUIRegistry(root).register(ProjectViewSpec(id="rich", label="Rich", renderer="custom", script="rich.js"))

            registry = ProjectUIRegistry(root, allow_custom_assets=True)
            registry.register(ProjectViewSpec(id="rich", label="Rich", renderer="custom", script="rich.js"))
            self.assertEqual(registry.public()[0]["script"], "/project-ui/assets/rich.js")
            self.assertEqual(registry.asset_paths(), {"rich.js"})

            with self.assertRaises(ProjectUIError):
                registry.register(ProjectViewSpec(id="escape", label="Escape", renderer="custom", script="../../outside.js"))

    def test_refresh_interval_is_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = ProjectUIRegistry(Path(tmp))
            with self.assertRaises(ProjectUIError):
                registry.register(ProjectViewSpec(id="fast", label="Fast", refresh_seconds=1))
            with self.assertRaises(ProjectUIError):
                registry.register(ProjectViewSpec(id="slow", label="Slow", refresh_seconds=3601))

    def test_missing_project_ui_adapter_is_optional(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = ProjectConfig(root, {"project": {"versionFile": "VERSION"}, "ui": {"projectUI": {"enabled": True}}})
            registry = load_project_ui(root, cfg)
            self.assertEqual(registry.public(), [])

    def test_project_ui_adapter_can_register_view(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter = root / "tools/companion/project_ui.py"
            adapter.parent.mkdir(parents=True)
            adapter.write_text(
                "from tools.companion.core.ui_extensions import ProjectViewSpec\n"
                "def register_project_ui(registry, root, config):\n"
                "    registry.register(ProjectViewSpec(id='project', label='Project'))\n",
                encoding="utf-8",
            )
            cfg = ProjectConfig(root, {"project": {"versionFile": "VERSION"}, "ui": {"projectUI": {"enabled": True}}})
            registry = load_project_ui(root, cfg)
            self.assertEqual(registry.public()[0]["id"], "project")


if __name__ == "__main__":
    unittest.main()
