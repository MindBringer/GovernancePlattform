from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path

from tools.companion.core.action_jobs import ActionJobManager
from tools.companion.core.actions import ActionRegistry, ActionSpec


class ActionJobManagerTests(unittest.TestCase):
    def _registry(self, root: Path) -> ActionRegistry:
        registry = ActionRegistry(root)
        registry.register(ActionSpec(
            id="long-task",
            label="Long Task",
            category="Test",
            commands=[
                [sys.executable, "-c", "import time; time.sleep(0.05); print('one')"],
                [sys.executable, "-c", "import time; time.sleep(0.05); print('two')"],
            ],
            background=True,
            progress_labels=["Prepare", "Execute"],
        ))
        registry.register(ActionSpec(
            id="sync-task",
            label="Sync Task",
            category="Test",
            commands=[[sys.executable, "-c", "print('sync')"]],
        ))
        return registry

    def test_background_action_runs_and_exposes_progress_and_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self._registry(root)
            manager = ActionJobManager(lambda: registry)

            started = manager.start("long-task")
            self.assertTrue(started["ok"])
            self.assertEqual(started["actionId"], "long-task")

            deadline = time.time() + 3
            saw_named_progress = False
            while time.time() < deadline:
                job = manager.current()
                if job and job["progress"]["label"] in {"Prepare", "Execute"}:
                    saw_named_progress = True
                if job and job["status"] != "running":
                    break
                time.sleep(0.01)

            job = manager.current()
            self.assertTrue(saw_named_progress)
            self.assertEqual(job["status"], "success")
            self.assertEqual(job["progress"]["phase"], "completed")
            self.assertEqual(job["progress"]["completed"], 2)
            self.assertEqual(job["result"]["summary"], "OK · Exit 0")
            self.assertIn("one", job["result"]["detailLog"])
            self.assertIn("two", job["result"]["detailLog"])

    def test_synchronous_action_cannot_be_started_as_background_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = self._registry(Path(tmp))
            manager = ActionJobManager(lambda: registry)
            result = manager.start("sync-task")
            self.assertFalse(result["ok"])
            self.assertEqual(result["exitCode"], 409)

    def test_second_background_action_is_rejected_while_running(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = self._registry(Path(tmp))
            manager = ActionJobManager(lambda: registry)
            first = manager.start("long-task")
            self.assertTrue(first["ok"])
            second = manager.start("long-task")
            self.assertFalse(second["ok"])
            self.assertEqual(second["exitCode"], 409)
            self.assertEqual(second["job"]["id"], first["jobId"])

    def test_public_job_payload_never_contains_confirmation_or_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = ActionRegistry(root)
            registry.register(ActionSpec(
                id="secret-task",
                label="Secret Task",
                category="Test",
                commands=[[sys.executable, "-c", "import sys; print('done')", "{input}"]],
                confirmation="CONFIRM-SECRET",
                input_label="Secret input",
                input_required=True,
                background=True,
            ))
            manager = ActionJobManager(lambda: registry)
            manager.start("secret-task", "CONFIRM-SECRET", "INPUT-SECRET")
            deadline = time.time() + 2
            while time.time() < deadline and manager.current()["status"] == "running":
                time.sleep(0.01)
            payload = repr(manager.current())
            self.assertNotIn("CONFIRM-SECRET", payload)
            self.assertNotIn("INPUT-SECRET", payload)


if __name__ == "__main__":
    unittest.main()
