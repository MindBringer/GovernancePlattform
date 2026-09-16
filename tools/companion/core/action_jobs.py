from __future__ import annotations

import threading
import time
import uuid

from .actions import ActionRegistry
from .result_contract import build_result_contract


class ActionJobManager:
    """Run one opt-in project action outside the HTTP request thread.

    Synchronous actions stay untouched. Only ActionSpec.background=true is accepted.
    The job payload intentionally contains no confirmation text or action input.
    """

    def __init__(self, registry_provider) -> None:
        self._registry_provider = registry_provider
        self._lock = threading.Lock()
        self._job: dict[str, object] | None = None

    def start(
        self,
        action_id: str,
        confirmation: str | None = None,
        user_input: str | None = None,
    ) -> dict[str, object]:
        registry: ActionRegistry = self._registry_provider()
        spec = registry.get(action_id)
        if spec is None:
            return {
                "ok": False,
                "exitCode": 404,
                "error": "Unbekannte Aktion.",
            }
        if not spec.background:
            return {
                "ok": False,
                "exitCode": 409,
                "error": "Aktion ist nicht als Background-Action registriert.",
            }

        with self._lock:
            if self._job and self._job.get("status") == "running":
                return {
                    "ok": False,
                    "exitCode": 409,
                    "error": "Eine Background-Action läuft bereits.",
                    "job": self._public(self._job),
                }

            total = max(1, len(spec.commands))
            job: dict[str, object] = {
                "id": uuid.uuid4().hex,
                "actionId": action_id,
                "label": spec.label,
                "status": "running",
                "startedAt": time.time(),
                "finishedAt": None,
                "result": None,
                "progress": {
                    "phase": "queued",
                    "label": spec.label,
                    "detail": "Background-Action wurde angelegt.",
                    "completed": 0,
                    "total": total,
                    "updatedAt": time.time(),
                },
            }
            self._job = job
            thread = threading.Thread(
                target=self._run,
                args=(job, action_id, confirmation, user_input),
                name=f"action-job-{action_id[:24]}-{str(job['id'])[:8]}",
                daemon=True,
            )
            thread.start()
            return {
                "ok": True,
                "exitCode": 0,
                "jobId": job["id"],
                "actionId": action_id,
                "status": "running",
            }

    def _run(
        self,
        job: dict[str, object],
        action_id: str,
        confirmation: str | None,
        user_input: str | None,
    ) -> None:
        def report(progress: dict[str, object]) -> None:
            with self._lock:
                if self._job is not job or job.get("status") != "running":
                    return
                job["progress"] = self._normalize_progress(progress, str(job.get("label") or action_id))

        try:
            registry: ActionRegistry = self._registry_provider()
            result = registry.execute(action_id, confirmation, user_input, progress=report)
        except Exception as exc:  # defensive boundary around project-owned worker execution
            detail = f"ABBRUCH: {type(exc).__name__}: {exc}"
            result = build_result_contract(
                command=action_id,
                exit_code=1,
                detail_log=detail,
                gate=action_id,
            )
            result["output"] = detail

        with self._lock:
            job["result"] = result
            ok = bool(result.get("ok"))
            job["status"] = "success" if ok else "failed"
            job["finishedAt"] = time.time()
            progress = dict(job.get("progress") or {})
            total = max(1, int(progress.get("total") or 1))
            progress.update({
                "phase": "completed" if ok else "failed",
                "label": str(job.get("label") or action_id),
                "detail": "Background-Action abgeschlossen." if ok else "Background-Action fehlgeschlagen; Fehlerblock und Detail-Log sind verfügbar.",
                "completed": total if ok else int(progress.get("completed") or 0),
                "total": total,
                "updatedAt": time.time(),
            })
            job["progress"] = self._normalize_progress(progress, str(job.get("label") or action_id))

    def current(self) -> dict[str, object] | None:
        with self._lock:
            return self._public(self._job) if self._job else None

    def status(self) -> dict[str, object]:
        return {"ok": True, "job": self.current()}

    @staticmethod
    def _public(job: dict[str, object]) -> dict[str, object]:
        payload = {
            "id": job.get("id"),
            "actionId": job.get("actionId"),
            "label": job.get("label"),
            "status": job.get("status"),
            "startedAt": job.get("startedAt"),
            "finishedAt": job.get("finishedAt"),
            "progress": dict(job.get("progress") or {}),
        }
        if job.get("status") != "running":
            payload["result"] = job.get("result")
        return payload

    @staticmethod
    def _normalize_progress(progress: dict[str, object], fallback_label: str) -> dict[str, object]:
        total = max(1, int(progress.get("total") or 1))
        completed = min(total, max(0, int(progress.get("completed") or 0)))
        return {
            "phase": str(progress.get("phase") or "running")[:80],
            "label": str(progress.get("label") or fallback_label)[:160],
            "detail": str(progress.get("detail") or "")[:500],
            "completed": completed,
            "total": total,
            "updatedAt": float(progress.get("updatedAt") or time.time()),
        }
