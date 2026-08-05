#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    ROOT / "README.md",
    ROOT / "CHANGELOG.md",
    ROOT / "powerplatform" / "VERSION",
    ROOT / "powerplatform" / "canvas" / "GovernancePortal" / "Src" / "App.pa.yaml",
    ROOT / "powerplatform" / "canvas" / "GovernancePortal" / "Src" / "scrShell.pa.yaml",
]

FORBIDDEN_TRACKED_PREFIXES = (
    "artifacts/inbound/",
    "artifacts/work/",
    "artifacts/outbound/",
    "generated/",
    "Logs/",
    ".venv/",
)

FORBIDDEN_PATTERNS = (
    re.compile(r"(^|/)canvas-editable(/|$)"),
    re.compile(r"(^|/)Other/Src(/|$)"),
    re.compile(r"\.DS_Store$"),
    re.compile(r"__pycache__"),
    re.compile(r"\.pyc$"),
)


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout.strip())
    return result.stdout


def main() -> int:
    findings: list[str] = []
    notes: list[str] = []

    for path in REQUIRED:
        if not path.exists():
            findings.append(f"Pflichtdatei fehlt: {path.relative_to(ROOT)}")

    tracked = [line for line in git("ls-files").splitlines() if line]
    for path in tracked:
        if path.startswith(FORBIDDEN_TRACKED_PREFIXES):
            findings.append(f"Lokales/erzeugtes Artefakt ist versioniert: {path}")
        if any(pattern.search(path) for pattern in FORBIDDEN_PATTERNS):
            findings.append(f"Veralteter oder lokaler Pfad ist versioniert: {path}")

    canonical = "powerplatform/canvas/GovernancePortal/Src/App.pa.yaml"
    app_sources = [path for path in tracked if path.endswith("/Src/App.pa.yaml")]
    if canonical not in app_sources:
        findings.append("Kanonischer Canvas-App-SourceTree fehlt.")
    extras = [path for path in app_sources if path != canonical]
    for path in extras:
        findings.append(f"Zusätzlicher Canvas-SourceTree gefunden: {path}")

    status = git("status", "--porcelain").strip()
    if status:
        notes.append("Arbeitsverzeichnis enthält lokale Änderungen.")

    branches = git("branch", "-r", "--format=%(refname:short)").splitlines()
    stale_candidates = [
        branch for branch in branches
        if branch.endswith("feature/alpha-3.2-dynamic-form-renderer")
        or branch.endswith("feature/canvas-stage-3.6")
    ]
    for branch in stale_candidates:
        notes.append(f"Remote-Branch als Bereinigungskandidat prüfen: {branch}")

    if findings:
        print("REPOSITORY-AUDIT: FEHLER")
        for item in findings:
            print(f"- {item}")
    else:
        print("REPOSITORY-AUDIT: OK")
        print("- kanonischer Canvas-SourceTree vorhanden")
        print("- keine bekannten Build-/Cache-Altlasten versioniert")
        print("- Pflichtdateien vorhanden")

    if notes:
        print("\nHINWEISE")
        for item in notes:
            print(f"- {item}")

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
