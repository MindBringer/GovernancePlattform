from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from tools.framework.project_memory import contract


class ProjectMemoryTests(unittest.TestCase):
    def test_template_project_memory_contract_is_green(self):
        root = Path(__file__).resolve().parents[2]
        result = contract(root)
        self.assertTrue(result["ok"], result.get("errors"))

    def _copy_contract_fixture(self, root: Path, target: Path) -> None:
        config = json.loads((root / ".project/project.config.json").read_text(encoding="utf-8"))
        version_file = str(config["project"]["versionFile"])
        version = (root / version_file).read_text(encoding="utf-8").strip()
        for rel in [
            ".project/project.config.json",
            ".project/state/current.json",
            ".project/framework/AGENT_CONTRACT.md",
            "AGENTS.md",
            "PROJECT_STATE.md",
            version_file,
        ]:
            src = root / rel
            dst = target / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        docs = config["documentation"]
        for key in ("roadmap", "knownIssues", "architectureDecisions"):
            dst = target / docs[key]
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text("# placeholder\n", encoding="utf-8")
        release_history = target / docs["releaseHistory"]
        release_history.parent.mkdir(parents=True, exist_ok=True)
        release_history.write_text(f"# placeholder\n\n## {version}\n", encoding="utf-8")
        (target / docs["runbooksRoot"]).mkdir(parents=True, exist_ok=True)

    def _force_released_state(self, target: Path) -> str:
        config = json.loads((target / ".project/project.config.json").read_text(encoding="utf-8"))
        version_file = str(config["project"]["versionFile"])
        version = (target / version_file).read_text(encoding="utf-8").strip()
        state_path = target / ".project/state/current.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        iteration = state.setdefault("iteration", {})
        iteration["status"] = "released"
        state["lastRelease"] = {
            "status": "released",
            "version": version,
            "targetBranch": "main",
        }
        state["releaseProvenance"] = {
            "sourceBranch": "test-release-branch",
            "targetBranch": "main",
            "pr": 1,
            "phase": "final",
        }
        state_path.write_text(json.dumps(state), encoding="utf-8")

        memory_path = target / str(config["documentation"]["projectState"])
        memory = memory_path.read_text(encoding="utf-8")
        memory = re.sub(
            r"<!--\s*release-status:\s*.*?\s*-->",
            "<!-- release-status: released -->",
            memory,
            count=1,
            flags=re.IGNORECASE,
        )
        memory_path.write_text(memory, encoding="utf-8")
        return version

    def test_missing_single_next_step_is_rejected(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self._copy_contract_fixture(root, target)
            state_path = target / ".project/state/current.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["nextStep"] = {"id": "", "description": ""}
            state_path.write_text(json.dumps(state), encoding="utf-8")
            result = contract(target)
            self.assertFalse(result["ok"])
            self.assertTrue(any("nextStep" in err for err in result["errors"]))

    def test_persisted_live_branch_is_rejected(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self._copy_contract_fixture(root, target)
            state_path = target / ".project/state/current.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["git"] = {"branch": "test-stale", "commit": "deadbeef"}
            state_path.write_text(json.dumps(state), encoding="utf-8")
            result = contract(target)
            self.assertFalse(result["ok"])
            self.assertTrue(any("Live-Branch" in err for err in result["errors"]))

    def test_invalid_verification_evidence_class_is_rejected(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self._copy_contract_fixture(root, target)
            state_path = target / ".project/state/current.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["verificationEvidence"] = [
                {
                    "id": "invalid-class",
                    "class": "invalid-evidence-class",
                    "status": "pending",
                    "releasePolicy": "required-pass",
                }
            ]
            state_path.write_text(json.dumps(state), encoding="utf-8")
            result = contract(target)
            self.assertFalse(result["ok"])
            self.assertTrue(any("class ist ungültig" in err for err in result["errors"]))

    def test_released_state_requires_release_history_for_current_version(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self._copy_contract_fixture(root, target)
            self._force_released_state(target)
            config = json.loads((target / ".project/project.config.json").read_text(encoding="utf-8"))
            history = target / config["documentation"]["releaseHistory"]
            history.write_text("# Release History\n\n## 0.0.1\n", encoding="utf-8")
            result = contract(target)
            self.assertFalse(result["ok"])
            self.assertTrue(any("Release-History-Eintrag" in err for err in result["errors"]))


if __name__ == "__main__":
    unittest.main()
