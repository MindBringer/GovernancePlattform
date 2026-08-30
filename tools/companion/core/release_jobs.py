from __future__ import annotations

import threading
import time
import uuid
from pathlib import Path
from typing import Callable

from .git_status import repository_status
from .result_contract import build_result_contract


ProgressReporter = Callable[[dict[str, object]], None]
ReleaseRunner = Callable[[str | None, ProgressReporter], dict[str, object]]


class ReleaseJobManager:
    """Run one long-lived release outside the HTTP request thread."""

    def __init__(self, runner: ReleaseRunner, root: Path | None = None) -> None:
        self._runner = runner
        self._root = (root or Path(__file__).resolve().parents[3]).resolve()
        self._lock = threading.Lock()
        self._job: dict[str, object] | None = None

    def start(self, confirmation: str | None) -> dict[str, object]:
        with self._lock:
            if self._job and self._job.get("status") == "running":
                return {
                    "ok": False,
                    "exitCode": 409,
                    "error": "Ein Release läuft bereits.",
                    "job": self._public(self._job),
                }

            job: dict[str, object] = {
                "id": uuid.uuid4().hex,
                "status": "running",
                "startedAt": time.time(),
                "finishedAt": None,
                "result": None,
                "lastCompletedPhase": None,
                "progress": {
                    "phase": "queued",
                    "label": "Release wird vorbereitet",
                    "detail": "Der serverseitige Release-Job wurde angelegt.",
                    "completed": 0,
                    "total": 10,
                    "updatedAt": time.time(),
                },
            }
            self._job = job
            thread = threading.Thread(
                target=self._run,
                args=(job, confirmation),
                name=f"release-job-{str(job['id'])[:8]}",
                daemon=True,
            )
            thread.start()
            return {
                "ok": True,
                "exitCode": 0,
                "jobId": job["id"],
                "status": "running",
            }

    @staticmethod
    def _normalize_result(result: dict[str, object]) -> dict[str, object]:
        if "summary" in result and "detailLog" in result and "failureBlock" in result:
            return result

        ok = bool(result.get("ok"))
        exit_code_raw = result.get("exitCode", 0 if ok else 1)
        try:
            exit_code = int(exit_code_raw)
        except (TypeError, ValueError):
            exit_code = 0 if ok else 1
        if not ok and exit_code == 0:
            exit_code = 1

        detail_log = str(result.get("detailLog") or result.get("output") or "")
        command = str(result.get("command") or "Full release")
        normalized = build_result_contract(
            command=command,
            exit_code=exit_code,
            detail_log=detail_log,
            gate="full-release",
            worktree_mutation=[str(item) for item in (result.get("worktreeMutation") or [])],
        )
        # Keep the historical release-job field for older Companion consumers.
        normalized["output"] = detail_log
        for key, value in result.items():
            if key not in normalized:
                normalized[key] = value
        return normalized

    @staticmethod
    def _recovery_next_step(phase: str, dirty_paths: list[str]) -> str:
        if phase == "artifacts":
            return (
                "Der PR-Merge ist bereits abgeschlossen. Nicht erneut mergen; main synchronisieren und die "
                "idempotente Companion-Aktion 'Release-Artefakte reparieren' ausführen."
            )
        if phase == "merge":
            return (
                "Den PR-Merge-Status auf GitHub prüfen. Wenn der PR ungemerged ist, Ursache auf dem Feature-Branch "
                "beheben und Full Release erneut starten; wenn er bereits gemerged ist, main synchronisieren und "
                "Release-Artefakte reparieren. Nicht blind erneut mergen."
            )
        if phase in {"candidate-ci", "final-ci"}:
            return (
                "Den fehlgeschlagenen Check auf dem aktuellen Feature-Branch beheben und den Full Release erneut "
                "starten. Den PR nicht manuell mergen und den geprüften Head nicht umgehen."
            )
        if dirty_paths:
            return (
                "Zuerst 'git status --short' prüfen und die genannten Änderungen gezielt einordnen; keine pauschalen "
                "Resets verwenden. Danach Ursache beheben und den Full Release auf dem Feature-Branch erneut starten."
            )
        return (
            "Ursache auf dem aktuellen Feature-Branch beheben und den Full Release erneut starten; PR/Tag/Release "
            "nicht manuell vorziehen."
        )

    def _attach_recovery(self, result: dict[str, object], job: dict[str, object]) -> dict[str, object]:
        if bool(result.get("ok")):
            return result

        failure_progress = job.get("failureProgress")
        progress = dict(failure_progress) if isinstance(failure_progress, dict) else dict(job.get("progress") or {})
        last_completed = job.get("lastCompletedPhase")
        last_completed_payload = dict(last_completed) if isinstance(last_completed, dict) else {}
        repo = repository_status(self._root)
        dirty_paths = [str(item) for item in (repo.get("dirtyPaths") or [])]
        phase = str(progress.get("phase") or "unknown")
        completed = int(progress.get("completed") or 0)
        total = max(1, int(progress.get("total") or 10))
        next_step = self._recovery_next_step(phase, dirty_paths)

        recovery = {
            "phase": phase,
            "phaseLabel": str(progress.get("label") or phase),
            "completed": completed,
            "total": total,
            "lastCompletedPhase": {
                "phase": str(last_completed_payload.get("phase") or ""),
                "label": str(last_completed_payload.get("label") or ""),
                "completed": int(last_completed_payload.get("completed") or 0),
            } if last_completed_payload else None,
            "branch": str(repo.get("branch") or "unbekannt"),
            "dirtyPaths": dirty_paths,
            "nextStep": next_step,
        }
        result["recovery"] = recovery

        existing_mutation = [str(item) for item in (result.get("worktreeMutation") or [])]
        combined_mutation = sorted(set(existing_mutation + dirty_paths))
        if combined_mutation:
            result["worktreeMutation"] = combined_mutation

        failure = result.get("failure")
        if isinstance(failure, dict):
            failure["recovery"] = recovery
            failure["nextStep"] = next_step
            if combined_mutation:
                failure["worktreeMutation"] = combined_mutation

        last_label = str(last_completed_payload.get("label") or "keine abgeschlossene Phase dokumentiert")
        dirty_text = ", ".join(dirty_paths) if dirty_paths else "keine"
        recovery_block = (
            "RECOVERY\n"
            f"Phase: {recovery['phaseLabel']} ({phase}) · {completed}/{total}\n"
            f"Zuletzt abgeschlossen: {last_label}\n"
            f"Branch: {recovery['branch']}\n"
            f"Dirty Paths: {dirty_text}\n"
            f"Nächster Schritt: {next_step}"
        )
        failure_block = str(result.get("failureBlock") or "").rstrip()
        result["failureBlock"] = f"{failure_block}\n\n{recovery_block}" if failure_block else recovery_block
        return result

    def _run(self, job: dict[str, object], confirmation: str | None) -> None:
        def report(progress: dict[str, object]) -> None:
            with self._lock:
                if self._job is not job or job.get("status") != "running":
                    return
                previous = dict(job.get("progress") or {})
                normalized = self._normalize_progress(progress)
                if normalized.get("phase") == "failed":
                    job["failureProgress"] = previous
                elif int(normalized.get("completed") or 0) > int(previous.get("completed") or 0):
                    job["lastCompletedPhase"] = {
                        "phase": str(previous.get("phase") or ""),
                        "label": str(previous.get("label") or ""),
                        "completed": int(previous.get("completed") or 0),
                    }
                job["progress"] = normalized

        try:
            result = self._normalize_result(self._runner(confirmation, report))
        except Exception as exc:  # defensive boundary around the release worker
            detail = f"ABBRUCH: {type(exc).__name__}: {exc}"
            result = self._normalize_result({
                "ok": False,
                "exitCode": 1,
                "command": "Full release",
                "output": detail,
            })
        result = self._attach_recovery(result, job)
        with self._lock:
            job["result"] = result
            job["status"] = "success" if bool(result.get("ok")) else "failed"
            job["finishedAt"] = time.time()
            progress = dict(job.get("progress") or {})
            progress.update({
                "phase": "completed" if bool(result.get("ok")) else "failed",
                "label": "Release abgeschlossen" if bool(result.get("ok")) else "Release abgebrochen",
                "detail": "Alle Release-Schritte sind abgeschlossen." if bool(result.get("ok")) else "Root Cause und Recovery-Hinweis stehen im Fehlerblock; das vollständige Log bleibt separat verfügbar.",
                "completed": int(progress.get("total") or 10) if bool(result.get("ok")) else int(progress.get("completed") or 0),
                "updatedAt": time.time(),
            })
            job["progress"] = self._normalize_progress(progress)

    def current(self) -> dict[str, object] | None:
        with self._lock:
            return self._public(self._job) if self._job else None

    def status(self) -> dict[str, object]:
        return {"ok": True, "job": self.current()}

    @staticmethod
    def _public(job: dict[str, object]) -> dict[str, object]:
        payload = {
            "id": job.get("id"),
            "status": job.get("status"),
            "startedAt": job.get("startedAt"),
            "finishedAt": job.get("finishedAt"),
            "progress": dict(job.get("progress") or {}),
        }
        if job.get("status") != "running":
            payload["result"] = job.get("result")
        return payload

    @staticmethod
    def _normalize_progress(progress: dict[str, object]) -> dict[str, object]:
        total = max(1, int(progress.get("total") or 10))
        completed = min(total, max(0, int(progress.get("completed") or 0)))
        return {
            "phase": str(progress.get("phase") or "running")[:80],
            "label": str(progress.get("label") or "Release läuft")[:160],
            "detail": str(progress.get("detail") or "")[:500],
            "completed": completed,
            "total": total,
            "updatedAt": float(progress.get("updatedAt") or time.time()),
        }
