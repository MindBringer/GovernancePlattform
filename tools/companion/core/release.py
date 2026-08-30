from __future__ import annotations

import json
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .actions import ActionRegistry
from .config import ProjectConfig
from .git_status import repository_status
from .process import run_command


class ReleaseEngine:
    def __init__(self, root: Path, config: ProjectConfig, registry: ActionRegistry):
        self.root = root
        self.config = config
        self.registry = registry

    def _run(self, log: list[str], command: list[str], timeout: int = 3600) -> None:
        log.append("$ " + " ".join(command))
        result = run_command(self.root, command, timeout)
        if result.output:
            log.append(result.output.rstrip())
        if not result.ok:
            raise RuntimeError(f"Schritt fehlgeschlagen (Exit {result.returncode}): {' '.join(command)}")

    def _run_gate(self, log: list[str], action_id: str) -> None:
        spec = self.registry.get(action_id)
        if spec is None:
            raise RuntimeError(f"Release-Gate ist nicht registriert: {action_id}")
        result = self.registry.execute(action_id)
        log.append(f"\n# Gate: {action_id}")
        if result.get("output"):
            log.append(str(result["output"]))
        if not result.get("ok"):
            raise RuntimeError(f"Release-Gate fehlgeschlagen: {action_id}")

    @staticmethod
    def _emit_progress(
        reporter: Callable[[dict[str, object]], None] | None,
        phase: str,
        label: str,
        detail: str,
        completed: int,
        total: int = 10,
    ) -> None:
        if reporter is None:
            return
        reporter({
            "phase": phase,
            "label": label,
            "detail": detail,
            "completed": completed,
            "total": total,
        })

    def _gate_ids(self, release: dict[str, Any]) -> list[str]:
        ids: list[str] = []
        quality = self.config.data.get("quality", {})
        if self.config.enabled("audit"):
            ids.append("repo-audit")
        if quality.get("technicalDebtReview", True):
            ids.append("technical-debt-review")
        if quality.get("projectMemoryContract", True):
            ids.extend(["project-memory-contract", "framework-validate"])
        if self.config.enabled("build"):
            ids.extend(["syntax-check", "tests"])
        ids.extend(str(item) for item in release.get("gates", []))
        result: list[str] = []
        for item in ids:
            if item and item not in result:
                result.append(item)
        return result

    def _replace_memory_marker(self, memory: str, key: str, value: str) -> str:
        pattern = re.compile(rf"<!--\s*{re.escape(key)}:\s*.*?\s*-->", re.IGNORECASE)
        line = f"<!-- {key}: {value} -->"
        if pattern.search(memory):
            return pattern.sub(line, memory, count=1)
        return line + "\n" + memory

    @staticmethod
    def _versioned_release_history_path(configured: str, version: str) -> tuple[str, bool]:
        configured_path = Path(configured)
        is_versioned = bool(re.fullmatch(r"\d+(?:\.\d+){2,3}", configured_path.stem))
        if not is_versioned:
            return configured_path.as_posix(), False
        return (configured_path.parent / f"{version}{configured_path.suffix or '.md'}").as_posix(), True

    def _write_release_metadata(
        self,
        source_branch: str,
        target_branch: str,
        gate_ids: list[str],
        *,
        phase: str,
        pr_number: int | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        version = self.config.version()

        state_path = self.root / ".project" / "state" / "current.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["frameworkVersion"] = self.config.framework_version
        state["projectVersion"] = version
        state["developmentMode"] = "release" if phase == "candidate" else "released"
        state["updatedAt"] = now_iso
        state.pop("git", None)
        state["releaseProvenance"] = {
            "sourceBranch": source_branch,
            "targetBranch": target_branch,
            "pr": pr_number,
            "phase": phase,
        }
        iteration = state.get("iteration")
        if isinstance(iteration, dict):
            iteration["status"] = "release-candidate" if phase == "candidate" else "released"
        if phase == "candidate":
            state["currentStage"] = f"{version} · Release-Kandidat"
        else:
            state["currentStage"] = f"{version} · veröffentlicht"
            configured_next = iteration.get("postReleaseNextStep") if isinstance(iteration, dict) else None
            if (
                isinstance(configured_next, dict)
                and str(configured_next.get("id") or "").strip()
                and str(configured_next.get("description") or "").strip()
            ):
                state["nextStep"] = {
                    "id": str(configured_next["id"]).strip(),
                    "description": str(configured_next["description"]).strip(),
                }
            else:
                state["nextStep"] = {
                    "id": f"{version}-post-release-review",
                    "description": (
                        f"Den veröffentlichten Stand {version} lokal prüfen und die nächste "
                        "Iteration aus der Produkt-Roadmap starten."
                    ),
                }
        verification = state.setdefault("verification", {})
        verification["releaseGates"] = {"status": "success", "passed": gate_ids, "verifiedAt": now_iso}
        state["lastBuild"] = {
            "status": "success",
            "timestamp": now_iso,
            "sourceBranch": source_branch,
        }
        state["lastRelease"] = {
            "status": "pending-merge" if phase == "candidate" else "released",
            "version": version,
            "timestamp": now_iso,
            "sourceBranch": source_branch,
            "targetBranch": target_branch,
            "pr": pr_number,
        }
        documentation = state.setdefault("documentation", {})
        documentation["releaseHistory"] = "current"
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        docs = self.config.data.get("documentation", {})
        memory_path = self.root / str(docs.get("projectState") or "PROJECT_STATE.md")
        memory = memory_path.read_text(encoding="utf-8")
        marker_values = {
            "current-version": version,
            "next-step": str((state.get("nextStep") or {}).get("id") or f"{version}-post-release-review"),
            "updated-at": now.date().isoformat(),
            "release-status": "candidate" if phase == "candidate" else "released",
            "release-source-branch": source_branch,
            "release-target-branch": target_branch,
            "release-pr": str(pr_number or "pending"),
        }
        for key, value in marker_values.items():
            memory = self._replace_memory_marker(memory, key, value)
        memory_path.write_text(memory, encoding="utf-8")

        if phase != "final":
            return

        configured_history_rel = str(docs.get("releaseHistory") or "docs/project/Release-History.md")
        history_rel, versioned_history = self._versioned_release_history_path(configured_history_rel, version)
        history_path = self.root / history_rel
        history_path.parent.mkdir(parents=True, exist_ok=True)
        history = (
            history_path.read_text(encoding="utf-8")
            if history_path.is_file()
            else f"# {self.config.project['name']} {version}\n"
        )
        if not re.search(rf"^##\s+{re.escape(version)}(?:\s|$)", history, re.MULTILINE):
            goal = ""
            if isinstance(iteration, dict):
                goal = str(iteration.get("goal") or "")
            next_step = state.get("nextStep") if isinstance(state.get("nextStep"), dict) else {}
            next_desc = str(next_step.get("description") or "")
            entry = (
                f"\n## {version} · {now.date().isoformat()}\n\n"
                f"- Status: Release über Engineering Companion\n"
                f"- Source Branch: `{source_branch}`\n"
                f"- Target Branch: `{target_branch}`\n"
                f"- Pull Request: #{pr_number if pr_number is not None else 'n/a'}\n"
                f"- Iterationsziel: {goal or 'nicht dokumentiert'}\n"
                f"- Release-Gates: {', '.join(gate_ids)}\n"
                f"- Nächster Schritt: {next_desc or 'nicht dokumentiert'}\n"
            )
            history_path.write_text(history.rstrip() + "\n" + entry, encoding="utf-8")

        if versioned_history and history_rel != configured_history_rel:
            config_path = self.root / ".project" / "project.config.json"
            config_data = json.loads(config_path.read_text(encoding="utf-8"))
            config_docs = config_data.setdefault("documentation", {})
            config_docs["releaseHistory"] = history_rel
            config_path.write_text(
                json.dumps(config_data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    def _commit_if_dirty(self, log: list[str], message: str) -> None:
        status = repository_status(self.root)
        if not status.get("dirty"):
            return
        self._run(log, ["git", "add", "-A"], 60)
        self._run(log, ["git", "commit", "-m", message], 120)

    def _wait_for_pr_checks(self, log: list[str], release: dict[str, Any], pr_number: int) -> str:
        head = run_command(self.root, ["git", "rev-parse", "HEAD"], 60)
        expected_head = head.output.strip().lower() if head.ok else ""
        if not re.fullmatch(r"[0-9a-f]{40}", expected_head):
            raise RuntimeError("Aktueller Git-Head konnte für die PR-Check-Verifikation nicht bestimmt werden.")

        probe = None
        head_seen = False
        for attempt in range(1, 25):
            pr_head = run_command(
                self.root,
                ["gh", "pr", "view", str(pr_number), "--json", "headRefOid", "--jq", ".headRefOid"],
                60,
            )
            observed_head = pr_head.output.strip().lower() if pr_head.ok else ""
            if observed_head != expected_head:
                shown = observed_head[:12] if observed_head else "unbekannt"
                log.append(
                    f"PR-Head noch nicht auf lokalem Head · Versuch {attempt}/24 · "
                    f"erwartet {expected_head[:12]} · gesehen {shown}"
                )
                time.sleep(5)
                continue

            head_seen = True
            probe = run_command(self.root, ["gh", "pr", "checks", str(pr_number)], 60)
            text = (probe.output or "").lower()
            if "no checks reported" not in text:
                break
            log.append(
                f"PR-Checks für Head {expected_head[:12]} noch nicht registriert · Versuch {attempt}/24"
            )
            time.sleep(5)

        if not head_seen:
            raise RuntimeError(
                f"GitHub-PR #{pr_number} meldet nach 120 Sekunden nicht den erwarteten Head {expected_head[:12]}."
            )
        no_checks = probe is None or "no checks reported" in (probe.output or "").lower()
        if no_checks:
            if release.get("allowNoChecks", False):
                log.append(f"Keine PR-Checks für Head {expected_head[:12]} registriert; laut Config zulässig.")
                return expected_head
            raise RuntimeError(
                f"Nach 120 Sekunden wurden für PR-Head {expected_head[:12]} keine Checks registriert."
            )

        checks = run_command(
            self.root,
            ["gh", "pr", "checks", str(pr_number), "--watch", "--fail-fast"],
            1800,
        )
        log.append(f"$ gh pr checks {pr_number} --watch --fail-fast · Head {expected_head[:12]}")
        if checks.output:
            log.append(checks.output.rstrip())
        if not checks.ok:
            raise RuntimeError("Mindestens ein PR-Check ist fehlgeschlagen oder konnte nicht ausgewertet werden.")

        final_pr_head = run_command(
            self.root,
            ["gh", "pr", "view", str(pr_number), "--json", "headRefOid", "--jq", ".headRefOid"],
            60,
        )
        if not final_pr_head.ok or final_pr_head.output.strip().lower() != expected_head:
            raise RuntimeError("PR-Head hat sich während der Check-Auswertung verändert; Release wird nicht gemerged.")
        return expected_head

    def _ensure_pr(self, log: list[str], base: str, branch: str) -> int:
        pr = run_command(self.root, ["gh", "pr", "view", "--json", "number", "--jq", ".number"], 60)
        if not pr.ok or not pr.output.strip():
            self._run(log, [
                "gh", "pr", "create", "--base", base, "--head", branch,
                "--title", f"Release {self.config.version()}",
                "--body", f"Automatisch durch den {self.config.project['name']} Engineering Companion erstellt. Engineering Contract und Release-Gates wurden lokal ausgeführt.",
            ], 120)
            pr = run_command(self.root, ["gh", "pr", "view", "--json", "number", "--jq", ".number"], 60)
        if not pr.ok or not pr.output.strip().isdigit():
            raise RuntimeError("Pull-Request-Nummer konnte nicht bestimmt werden.")
        return int(pr.output.strip())

    def _publish_release_artifacts(self, log: list[str]) -> None:
        result = run_command(self.root, [sys.executable, "tools/framework/release_artifacts.py"], 600)
        log.append(f"$ {sys.executable} tools/framework/release_artifacts.py")
        if result.output:
            log.append(result.output.rstrip())
        if not result.ok:
            raise RuntimeError("Merge ist abgeschlossen, aber Tag/GitHub-Release konnten nicht vollständig erzeugt werden. Aktion 'Release-Artefakte reparieren' erneut ausführen.")

    def execute(
        self,
        confirmation: str | None,
        progress: Callable[[dict[str, object]], None] | None = None,
    ) -> dict[str, object]:
        release = self.config.data.get("release", {})
        log: list[str] = []
        try:
            self._emit_progress(progress, "preflight", "Release-Preflight", "Konfiguration, Freigabe und GitHub-Zugang werden geprüft.", 0)
            if not release.get("enabled", False):
                raise RuntimeError("Release-Modul ist deaktiviert.")
            expected = str(release.get("confirmation") or "")
            if not expected or confirmation != expected:
                raise RuntimeError(f"Bestätigung fehlt. Erwartet: {expected}")
            if shutil.which("gh") is None:
                raise RuntimeError("GitHub CLI fehlt. Installation und 'gh auth login' erforderlich.")
            self._run(log, ["gh", "auth", "status"], 60)

            base = str(release.get("baseBranch") or "main")
            merge_method = str(release.get("mergeMethod") or "squash")
            status = repository_status(self.root)
            branch = str(status.get("branch") or "")
            if not status.get("ok") or status.get("detached"):
                raise RuntimeError("Repository befindet sich nicht auf einem normalen Branch.")
            if branch == base:
                raise RuntimeError(f"Release ist nur aus einem Feature-/Fix-Branch zulässig, nicht aus {base}.")
            if status.get("conflicts"):
                raise RuntimeError("Release ist bei Git-Konflikten gesperrt.")

            gate_ids = self._gate_ids(release)
            for index, gate in enumerate(gate_ids, start=1):
                self._emit_progress(progress, "local-gates", "Lokale Release-Gates", f"Gate {index}/{len(gate_ids)}: {gate}", 1)
                self._run_gate(log, gate)

            self._emit_progress(progress, "candidate", "Release-Kandidat vorbereiten", "Projektgedächtnis und Release-Metadaten werden erzeugt und committed.", 2)
            self._write_release_metadata(branch, base, gate_ids, phase="candidate")
            self._run_gate(log, "project-memory-contract")
            if repository_status(self.root).get("dirty") and not release.get("commitDirty", True):
                raise RuntimeError("Release-Metadaten erzeugen Änderungen, aber commitDirty=false.")
            self._commit_if_dirty(log, f"chore(release): prepare {self.config.version()}")

            self._emit_progress(progress, "synchronize", "Mit main synchronisieren", f"{branch} wird auf origin/{base} rebased.", 3)
            self._run(log, ["git", "fetch", "--prune", "origin"], 300)
            self._run(log, ["git", "rebase", f"origin/{base}"], 600)
            for index, gate in enumerate(gate_ids, start=1):
                self._emit_progress(progress, "synchronized-gates", "Gates nach Rebase", f"Gate {index}/{len(gate_ids)}: {gate}", 4)
                self._run_gate(log, gate)
            self._write_release_metadata(branch, base, gate_ids, phase="candidate")
            self._run_gate(log, "project-memory-contract")
            self._commit_if_dirty(log, f"chore(release): refresh verification {self.config.version()}")

            self._emit_progress(progress, "pull-request", "Pull Request aktualisieren", "Branch wird sicher gepusht und der Pull Request ermittelt.", 5)
            self._run(log, ["git", "push", "--force-with-lease", "-u", "origin", branch], 600)
            pr_number = self._ensure_pr(log, base, branch)
            self._emit_progress(progress, "candidate-ci", "Candidate-CI überwachen", f"Checks für PR #{pr_number} und den exakten Candidate-Head laufen.", 6)
            self._wait_for_pr_checks(log, release, pr_number)

            # Final state is committed only after all candidate checks are green.
            # It therefore reaches main atomically with the successful merge.
            self._emit_progress(progress, "finalize", "Finalen Release-Stand erzeugen", f"Finale Metadaten für PR #{pr_number} werden committed.", 7)
            self._write_release_metadata(branch, base, gate_ids, phase="final", pr_number=pr_number)
            self._run_gate(log, "project-memory-contract")
            self._commit_if_dirty(log, f"chore(release): finalize {self.config.version()}")
            self._run(log, ["git", "push", "--force-with-lease", "origin", branch], 600)
            self._emit_progress(progress, "final-ci", "Finale CI überwachen", f"Checks für den finalen Head von PR #{pr_number} laufen.", 8)
            final_head = self._wait_for_pr_checks(log, release, pr_number)

            self._emit_progress(progress, "merge", "PR nach main mergen", f"PR #{pr_number} wird mit geprüftem Head gemergt; main wird anschließend synchronisiert.", 9)
            self._run(
                log,
                [
                    "gh", "pr", "merge", str(pr_number), f"--{merge_method}", "--delete-branch",
                    "--match-head-commit", final_head,
                ],
                300,
            )
            self._run(log, ["git", "switch", base], 120)
            self._run(log, ["git", "pull", "--ff-only", "origin", base], 300)
            if release.get("createTag", True) or release.get("createGitHubRelease", False):
                self._emit_progress(progress, "artifacts", "Release-Artefakte veröffentlichen", "Tag und GitHub Release werden aus dem synchronisierten main erzeugt.", 10)
                self._publish_release_artifacts(log)
            self._emit_progress(progress, "completed", "Release abgeschlossen", f"{self.config.version()} wurde nach {base} veröffentlicht.", 10)
            return {"ok": True, "exitCode": 0, "command": "Full release", "output": "\n".join(log)}
        except (RuntimeError, OSError, json.JSONDecodeError) as exc:
            self._emit_progress(progress, "failed", "Release abgebrochen", str(exc), 0)
            log.append(f"\nABBRUCH: {exc}")
            return {"ok": False, "exitCode": 1, "command": "Full release", "output": "\n".join(log)}
