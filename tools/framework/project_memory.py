#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.companion.core.config import load_config
from tools.framework.verification_evidence import evaluate as evaluate_evidence
from tools.framework.version_truth import evaluate as evaluate_version_truth

META_RE = re.compile(r"<!--\s*([a-z0-9-]+):\s*(.*?)\s*-->", re.IGNORECASE)
REQUIRED_SECTIONS = [
    "## Aktueller Stand",
    "## Aktuelle Iteration",
    "## Umgesetzt",
    "## Nicht umgesetzt / Nicht-Ziele",
    "## Qualität und Verifikation",
    "## Altlasten und bekannte Probleme",
    "## Nächster geplanter Schritt",
    "## Wiederaufnahme nach Chat-Abbruch",
    "## Iterationsübergabe",
]
RELEASE_MARKERS = [
    "release-status",
    "release-source-branch",
    "release-target-branch",
    "release-pr",
]


def _metadata(text: str) -> dict[str, str]:
    return {key.lower(): value.strip() for key, value in META_RE.findall(text)}


def contract(root: Path = ROOT) -> dict[str, object]:
    root = root.resolve()
    config = load_config(root)
    errors: list[str] = []
    checks: list[dict[str, object]] = []

    state_path = root / ".project" / "state" / "current.json"
    memory_path = root / str(config.data.get("documentation", {}).get("projectState") or "PROJECT_STATE.md")
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "errors": [f"current.json nicht lesbar: {exc}"], "checks": []}
    try:
        memory = memory_path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"ok": False, "errors": [f"PROJECT_STATE nicht lesbar: {exc}"], "checks": []}

    meta = _metadata(memory)
    version = config.version()
    framework = config.framework_version

    def require(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            errors.append(detail or name)

    require("memory-schema", meta.get("project-memory-schema") == "2", "PROJECT_STATE project-memory-schema muss 2 sein")
    require("memory-updated-at", bool(meta.get("updated-at")), "PROJECT_STATE updated-at fehlt")
    require("state-schema", int(state.get("schemaVersion") or 0) >= 2, "current.json schemaVersion muss >= 2 sein")
    require("project-version-state", str(state.get("projectVersion") or "") == version, f"projectVersion in current.json muss {version} sein")
    require("project-version-memory", meta.get("current-version") == version, f"PROJECT_STATE current-version muss {version} sein")
    require("framework-version-state", str(state.get("frameworkVersion") or "") == framework, f"frameworkVersion in current.json muss {framework} sein")

    require("framework-agent-contract", (root / ".project/framework/AGENT_CONTRACT.md").is_file(), "Framework Agent Contract fehlt: .project/framework/AGENT_CONTRACT.md")
    require("project-agent-contract", (root / "AGENTS.md").is_file(), "Project-owned AGENTS.md fehlt")
    legacy_git = state.get("git")
    stale_live_git = isinstance(legacy_git, dict) and any(key in legacy_git for key in ("branch", "commit"))
    require("no-persisted-live-git", not stale_live_git, "current.json darf Live-Branch/Live-Commit nicht persistent als git.branch/git.commit speichern; releaseProvenance verwenden")

    for marker in RELEASE_MARKERS:
        require(f"memory-marker:{marker}", bool(meta.get(marker)), f"PROJECT_STATE Marker fehlt: {marker}")

    next_step = state.get("nextStep")
    valid_next = isinstance(next_step, dict) and bool(str(next_step.get("id") or "").strip()) and bool(str(next_step.get("description") or "").strip())
    require("single-next-step", valid_next, "current.json benötigt genau einen nextStep mit id und description")
    if valid_next:
        require("next-step-memory", meta.get("next-step") == str(next_step["id"]), "PROJECT_STATE next-step stimmt nicht mit current.json überein")

    iteration = state.get("iteration")
    valid_iteration = isinstance(iteration, dict) and bool(str(iteration.get("goal") or "").strip()) and bool(str(iteration.get("status") or "").strip()) and bool(str(iteration.get("dataRisk") or "").strip()) and isinstance(iteration.get("nonGoals"), list)
    require("iteration-handoff", valid_iteration, "current.json benötigt iteration.goal/status/dataRisk/nonGoals")

    if isinstance(iteration, dict) and iteration.get("status") == "released":
        last_release = state.get("lastRelease") if isinstance(state.get("lastRelease"), dict) else {}
        provenance = state.get("releaseProvenance") if isinstance(state.get("releaseProvenance"), dict) else {}
        require("released-state", last_release.get("status") == "released", "iteration.status=released erfordert lastRelease.status=released")
        require("released-version", str(last_release.get("version") or "") == version, "Released State erfordert lastRelease.version == projectVersion")
        require("released-provenance", provenance.get("phase") == "final" and bool(provenance.get("targetBranch")), "Released State erfordert finale releaseProvenance mit Target Branch")
        require("released-memory-marker", meta.get("release-status") == "released", "Released State erfordert PROJECT_STATE release-status=released")

    debt = state.get("technicalDebt")
    debt_ok = isinstance(debt, dict) and debt.get("status") == "reviewed" and int(debt.get("blockers") or 0) == 0 and bool(debt.get("reviewedAt"))
    require("technical-debt-review", debt_ok, "Technical-Debt-Review fehlt, ist blockiert oder enthält Blocker")

    quality = config.data.get("quality", {}) if isinstance(config.data.get("quality"), dict) else {}
    if bool(quality.get("verificationEvidence")) or "verificationEvidence" in state:
        evidence = evaluate_evidence(state, release=False)
        evidence_detail = "; ".join(str(item) for item in evidence.get("errors", [])) or "Verification Evidence ist strukturell gültig"
        require("verification-evidence-structure", bool(evidence.get("ok")), evidence_detail)

    documentation = state.get("documentation") if isinstance(state.get("documentation"), dict) else {}
    required_doc_keys = quality.get("requiredDocumentationStatus", [])
    for key in required_doc_keys:
        status = str(documentation.get(str(key)) or "")
        require(f"documentation:{key}", status in {"current", "n/a"}, f"Dokumentationsstatus {key} muss current oder n/a sein")

    docs = config.data.get("documentation", {}) if isinstance(config.data.get("documentation"), dict) else {}
    version_truth = evaluate_version_truth(
        root,
        docs,
        project_version=version,
        framework_version=framework,
    )
    truth_detail = "; ".join(str(item) for item in version_truth.get("errors", [])) or "Aktive Dokumentationswahrheit ist konsistent"
    require("documentation-version-truth", bool(version_truth.get("ok")), truth_detail)

    for key in ("roadmap", "knownIssues", "releaseHistory", "architectureDecisions"):
        rel = str(docs.get(key) or "")
        if rel:
            require(f"doc-path:{key}", (root / rel).is_file(), f"Dokument fehlt: {rel}")
    runbooks_root = str(docs.get("runbooksRoot") or "")
    if runbooks_root:
        require("doc-path:runbooks", (root / runbooks_root).is_dir(), f"Runbook-Verzeichnis fehlt: {runbooks_root}")

    if isinstance(iteration, dict) and iteration.get("status") == "released":
        history_rel = str(docs.get("releaseHistory") or "")
        history_path = root / history_rel if history_rel else None
        history = ""
        if history_path and history_path.is_file():
            try:
                history = history_path.read_text(encoding="utf-8")
            except OSError:
                history = ""
        current_history = bool(re.search(rf"^##\s+{re.escape(version)}(?:\s|$)", history, re.MULTILINE))
        require("released-history-version", current_history, f"Released State erfordert Release-History-Eintrag für {version}")

    for section in REQUIRED_SECTIONS:
        require(f"section:{section}", section in memory, f"PROJECT_STATE Abschnitt fehlt: {section}")

    require("known-issues-type", isinstance(state.get("knownIssues"), int) and int(state.get("knownIssues") or 0) >= 0, "knownIssues muss eine nichtnegative Ganzzahl sein")

    return {
        "ok": not errors,
        "projectVersion": version,
        "frameworkVersion": framework,
        "checks": checks,
        "errors": errors,
    }


def main() -> int:
    result = contract(ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
