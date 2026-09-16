from __future__ import annotations

import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

from tools.companion.core.release_jobs import ReleaseJobManager


class ReleaseJobManagerTests(unittest.TestCase):
    @staticmethod
    def _wait_for_job(manager: ReleaseJobManager, timeout: float = 2.0) -> dict[str, object]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            job = manager.current()
            if job and job["status"] != "running":
                return job
            time.sleep(0.01)
        raise AssertionError("Release-Job wurde nicht rechtzeitig abgeschlossen")

    def _git_repo(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "framework-test@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Framework Test"], cwd=root, check=True)
        (root / "tracked.txt").write_text("baseline\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "baseline"], cwd=root, check=True)
        return root

    def test_release_runs_in_background_and_exposes_result(self):
        started = threading.Event()
        finish = threading.Event()

        def runner(confirmation: str | None, progress) -> dict[str, object]:
            self.assertEqual(confirmation, "RELEASE NACH MAIN")
            progress({"phase": "gates", "label": "Gates", "detail": "1/2", "completed": 1, "total": 2})
            started.set()
            self.assertTrue(finish.wait(timeout=2))
            return {"ok": True, "exitCode": 0, "command": "Full release", "output": "done"}

        manager = ReleaseJobManager(runner)
        response = manager.start("RELEASE NACH MAIN")
        self.assertTrue(response["ok"])
        self.assertEqual(response["status"], "running")
        self.assertTrue(started.wait(timeout=1))
        running = manager.current()
        self.assertEqual(running["status"], "running")
        self.assertEqual(running["progress"]["phase"], "gates")
        self.assertEqual(running["progress"]["completed"], 1)

        finish.set()
        job = self._wait_for_job(manager)
        self.assertEqual(job["status"], "success")
        self.assertEqual(job["progress"]["phase"], "completed")
        self.assertEqual(job["progress"]["completed"], job["progress"]["total"])
        self.assertTrue(job["result"]["ok"])
        self.assertEqual(job["result"]["output"], "done")
        self.assertEqual(job["result"]["detailLog"], "done")
        self.assertEqual(job["result"]["summary"], "OK · Exit 0")
        self.assertEqual(job["result"]["failureBlock"], "")

    def test_second_release_is_rejected_while_one_is_running(self):
        started = threading.Event()
        finish = threading.Event()

        def runner(_confirmation: str | None, _progress) -> dict[str, object]:
            started.set()
            finish.wait(timeout=2)
            return {"ok": True, "exitCode": 0}

        manager = ReleaseJobManager(runner)
        first = manager.start("x")
        self.assertTrue(first["ok"])
        self.assertTrue(started.wait(timeout=1))

        second = manager.start("x")
        self.assertFalse(second["ok"])
        self.assertEqual(second["exitCode"], 409)
        self.assertEqual(second["job"]["id"], first["jobId"])
        finish.set()

    def test_worker_exception_becomes_failed_job_with_failure_footer(self):
        def runner(_confirmation: str | None, _progress) -> dict[str, object]:
            raise RuntimeError("boom")

        manager = ReleaseJobManager(runner)
        manager.start("x")
        job = self._wait_for_job(manager)
        self.assertEqual(job["status"], "failed")
        result = job["result"]
        self.assertIn("RuntimeError: boom", result["output"])
        self.assertIn("RuntimeError: boom", result["failureBlock"])
        self.assertIn("RECOVERY", result["failureBlock"])
        self.assertEqual(result["failure"]["gate"], "full-release")
        self.assertEqual(result["summary"], "FEHLER · Exit 1")

    def test_failed_runner_result_preserves_exit_code_and_detail_log(self):
        def runner(_confirmation: str | None, _progress) -> dict[str, object]:
            return {
                "ok": False,
                "exitCode": 9,
                "command": "Full release",
                "output": "RuntimeError: release failed",
            }

        manager = ReleaseJobManager(runner)
        manager.start("x")
        result = self._wait_for_job(manager)["result"]
        self.assertEqual(result["exitCode"], 9)
        self.assertEqual(result["detailLog"], "RuntimeError: release failed")
        self.assertIn("Exit-Code: 9", result["failureBlock"])
        self.assertIn("RuntimeError: release failed", result["failureBlock"])

    def test_failure_recovery_preserves_real_phase_branch_and_dirty_paths(self):
        root = self._git_repo()
        branch = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        (root / "tracked.txt").write_text("release metadata changed\n", encoding="utf-8")

        def runner(_confirmation: str | None, progress) -> dict[str, object]:
            progress({"phase": "preflight", "label": "Preflight", "completed": 0, "total": 10})
            progress({"phase": "local-gates", "label": "Lokale Gates", "completed": 1, "total": 10})
            progress({"phase": "candidate", "label": "Candidate erzeugen", "completed": 2, "total": 10})
            progress({"phase": "failed", "label": "Release abgebrochen", "detail": "boom", "completed": 0, "total": 10})
            return {"ok": False, "exitCode": 1, "command": "Full release", "output": "RuntimeError: candidate failed"}

        manager = ReleaseJobManager(runner, root=root)
        manager.start("x")
        result = self._wait_for_job(manager)["result"]
        recovery = result["recovery"]
        self.assertEqual(recovery["phase"], "candidate")
        self.assertEqual(recovery["branch"], branch)
        self.assertEqual(recovery["dirtyPaths"], ["tracked.txt"])
        self.assertEqual(recovery["lastCompletedPhase"]["label"], "Lokale Gates")
        self.assertIn("git status --short", recovery["nextStep"])
        self.assertIn("tracked.txt", result["failureBlock"])
        self.assertIn("Candidate erzeugen", result["failureBlock"])

    def test_artifact_failure_recovery_never_recommends_remerge(self):
        root = self._git_repo()

        def runner(_confirmation: str | None, progress) -> dict[str, object]:
            progress({"phase": "merge", "label": "Merge", "completed": 9, "total": 10})
            progress({"phase": "artifacts", "label": "Release-Artefakte", "completed": 10, "total": 10})
            progress({"phase": "failed", "label": "Release abgebrochen", "detail": "artifact failed", "completed": 0, "total": 10})
            return {"ok": False, "exitCode": 1, "command": "Full release", "output": "RuntimeError: artifact failed"}

        manager = ReleaseJobManager(runner, root=root)
        manager.start("x")
        recovery = self._wait_for_job(manager)["result"]["recovery"]
        self.assertEqual(recovery["phase"], "artifacts")
        self.assertIn("Nicht erneut mergen", recovery["nextStep"])
        self.assertIn("Release-Artefakte reparieren", recovery["nextStep"])

    def test_companion_routes_and_ui_use_release_jobs(self):
        root = Path(__file__).resolve().parents[2]
        server = (root / "tools/companion/server.py").read_text(encoding="utf-8")
        app = (root / "tools/companion/web/app.js").read_text(encoding="utf-8")
        ui = (root / "tools/companion/web/input-actions.js").read_text(encoding="utf-8")
        index = (root / "tools/companion/web/index.html").read_text(encoding="utf-8")

        self.assertIn('path == "/api/release-job"', server)
        self.assertIn("RELEASE_JOBS.start(confirmation_text)", server)
        self.assertNotIn("self.send_json(RELEASE.execute(confirmation_text))", server)

        self.assertIn("if(id==='release')", app)
        self.assertIn("window.ProjectCompanion?.runRelease", app)
        self.assertNotIn("const action=id==='release'?", app)

        self.assertIn("pollRelease", ui)
        self.assertIn("/api/release-job", ui)
        self.assertIn("Status: RUNNING", ui)
        self.assertIn("progress.label", ui)
        self.assertIn("nextPaint", ui)
        self.assertIn("showView?.('console'", ui)
        self.assertIn("resumeReleaseMonitor", ui)
        self.assertIn("window.ProjectCompanion.runRelease = runRelease", ui)
        self.assertIn("button.dataset.action === 'release'", ui)
        self.assertIn("renderResult(result, output, 'Full release')", ui)

        self.assertIn("app.js?framework=1.3.12", index)
        self.assertIn("input-actions.js?framework=1.3.12", index)
        self.assertIn("no-cache, no-store, must-revalidate", index)
        self.assertIn('id="releaseProgress"', index)
        self.assertIn('id="themeToggle"', index)
        self.assertIn('id="consoleDetailPanel"', index)


if __name__ == "__main__":
    unittest.main()
