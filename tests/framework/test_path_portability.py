from __future__ import annotations

import unittest

from tools.framework.audit_repo import case_collision_findings, manifest_case_findings
from tools.framework.sync import path_is_project_owned


class PathPortabilityTests(unittest.TestCase):
    def test_case_only_git_collision_is_rejected(self):
        findings = case_collision_findings(["README.md", "README.MD", "tools/app.py"])
        self.assertEqual(len(findings), 1)
        self.assertIn("README.MD", findings[0])
        self.assertIn("README.md", findings[0])

    def test_manifest_case_mismatch_is_visible(self):
        findings = manifest_case_findings(
            ["README.MD", "tools/framework/sync.py"],
            {
                "managed": ["tools/framework"],
                "projectOwned": ["README.md"],
            },
        )
        self.assertEqual(
            findings,
            ["Manifest-Pfad-Casing weicht von Git ab (projectOwned): README.md -> README.MD"],
        )

    def test_manifest_exact_case_is_green(self):
        findings = manifest_case_findings(
            ["README.md", "tools/framework/sync.py"],
            {
                "managed": ["tools/framework"],
                "projectOwned": ["README.md"],
            },
        )
        self.assertEqual(findings, [])

    def test_project_owned_protection_is_case_insensitive(self):
        self.assertTrue(path_is_project_owned("README.MD", ["README.md"]))
        self.assertTrue(
            path_is_project_owned(
                "Tools/Companion/Project_Web/index.html",
                ["tools/companion/project_web"],
            )
        )
        self.assertFalse(path_is_project_owned("tools/companion/core/actions.py", ["tools/companion/project_web"]))


if __name__ == "__main__":
    unittest.main()
