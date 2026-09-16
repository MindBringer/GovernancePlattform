from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.companion.core.config import validate_config


class RepositoryPolicyTests(unittest.TestCase):
    def test_repository_policy_flag_is_boolean(self):
        root = Path(__file__).resolve().parents[2]
        payload = json.loads((root / ".project/project.config.json").read_text(encoding="utf-8"))
        payload["repositoryPolicy"]["requireProtectedBaseBranch"] = "yes"
        self.assertIn("repositoryPolicy.requireProtectedBaseBranch muss bool sein", validate_config(payload))


if __name__ == "__main__":
    unittest.main()
