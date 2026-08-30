from __future__ import annotations

import json
import unittest
from pathlib import Path


class InitProjectTests(unittest.TestCase):
    def test_template_release_gate_contains_bootstrap_only_in_template(self):
        root = Path(__file__).resolve().parents[2]
        config = json.loads((root / ".project/project.config.json").read_text(encoding="utf-8"))
        gates = config.get("release", {}).get("gates", [])
        if config.get("project", {}).get("key") == "project-template":
            self.assertIn("bootstrap-smoke", gates)


if __name__ == "__main__":
    unittest.main()
