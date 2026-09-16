from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.framework.version_truth import evaluate


class VersionTruthTests(unittest.TestCase):
    def test_current_project_and_framework_markers_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                "Aktueller Release: **9.2.0**.\nEngineering Framework **1.3.12** startet lokal.\n",
                encoding="utf-8",
            )
            result = evaluate(
                root,
                {
                    "versionTruth": [
                        {
                            "path": "README.md",
                            "contains": [
                                "Aktueller Release: **{projectVersion}**",
                                "Engineering Framework **{frameworkVersion}** startet lokal",
                            ],
                        }
                    ]
                },
                project_version="9.2.0",
                framework_version="1.3.12",
            )
            self.assertTrue(result["ok"], result["errors"])

    def test_stale_framework_marker_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                "Aktueller Release: **9.2.0**.\nEngineering Framework **1.3.10** startet lokal.\n",
                encoding="utf-8",
            )
            result = evaluate(
                root,
                {
                    "versionTruth": [
                        {
                            "path": "README.md",
                            "contains": ["Engineering Framework **{frameworkVersion}** startet lokal"],
                        }
                    ]
                },
                project_version="9.2.0",
                framework_version="1.3.12",
            )
            self.assertFalse(result["ok"])
            self.assertIn("Engineering Framework **1.3.12** startet lokal", result["errors"][0])

    def test_stale_project_release_marker_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("Aktueller Release: **9.0.3**.\n", encoding="utf-8")
            result = evaluate(
                root,
                {
                    "versionTruth": [
                        {
                            "path": "README.md",
                            "contains": ["Aktueller Release: **{projectVersion}**"],
                        }
                    ]
                },
                project_version="9.2.0",
                framework_version="1.3.12",
            )
            self.assertFalse(result["ok"])
            self.assertIn("Aktueller Release: **9.2.0**", result["errors"][0])

    def test_repository_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = evaluate(
                root,
                {
                    "versionTruth": [
                        {
                            "path": "../outside.md",
                            "contains": ["{projectVersion}"],
                        }
                    ]
                },
                project_version="9.2.0",
                framework_version="1.3.12",
            )
            self.assertFalse(result["ok"])
            self.assertIn("verlässt den Repository-Root", result["errors"][0])

    def test_empty_contract_is_backwards_compatible(self):
        result = evaluate(
            Path.cwd(),
            {},
            project_version="1.0.0",
            framework_version="1.3.12",
        )
        self.assertTrue(result["ok"])
        self.assertEqual([], result["checks"])


if __name__ == "__main__":
    unittest.main()
