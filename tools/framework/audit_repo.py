#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_TRACKED = {".DS_Store", ".env", "settings.local.psd1", "local.settings.json"}


def portable_key(value: str | Path) -> str:
    return str(value).replace("\\", "/")


def portable_case_key(value: str | Path) -> str:
    return portable_key(value).casefold()


def tracked_files(root: Path = ROOT) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "ls-files"], cwd=root, text=True, capture_output=True, timeout=30, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    return proc.stdout.splitlines() if proc.returncode == 0 else []


def case_collision_findings(tracked: list[str]) -> list[str]:
    by_portable_case: dict[str, list[str]] = {}
    for rel in tracked:
        by_portable_case.setdefault(portable_case_key(rel), []).append(portable_key(rel))
    findings: list[str] = []
    for paths in by_portable_case.values():
        unique = sorted(set(paths))
        if len(unique) > 1:
            findings.append(f"Case-only Git-Pfadkollision ist nicht portabel: {', '.join(unique)}")
    return findings


def _actual_case_prefix(declared: str, candidate: str) -> str:
    declared_parts = portable_key(declared).rstrip("/").split("/")
    candidate_parts = portable_key(candidate).split("/")
    return "/".join(candidate_parts[: len(declared_parts)])


def manifest_case_findings(tracked: list[str], manifest: dict) -> list[str]:
    tracked_keys = [portable_key(item) for item in tracked]
    tracked_set = set(tracked_keys)
    findings: list[str] = []
    for section in ("managed", "projectOwned"):
        entries = manifest.get(section, [])
        if not isinstance(entries, list):
            continue
        for raw in entries:
            declared = portable_key(str(raw)).rstrip("/")
            if not declared:
                continue
            exact_prefix = declared + "/"
            if declared in tracked_set or any(item.startswith(exact_prefix) for item in tracked_keys):
                continue

            folded = portable_case_key(declared)
            folded_prefix = folded + "/"
            candidates = [
                item
                for item in tracked_keys
                if portable_case_key(item) == folded or portable_case_key(item).startswith(folded_prefix)
            ]
            if not candidates:
                continue
            actual = _actual_case_prefix(declared, sorted(candidates)[0])
            findings.append(
                f"Manifest-Pfad-Casing weicht von Git ab ({section}): {declared} -> {actual}"
            )
    return findings


def audit(root: Path = ROOT) -> dict[str, object]:
    root = root.resolve()
    tracked = tracked_files(root)
    findings: list[str] = []
    for rel in tracked:
        name = Path(rel).name
        if name in FORBIDDEN_TRACKED or name.endswith(".local.json") or name.endswith(".local.psd1"):
            findings.append(f"Lokale/secret-nahe Datei ist getrackt: {rel}")

    findings.extend(case_collision_findings(tracked))

    manifest_path = root / ".project" / "framework.manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(f"Framework-Manifest nicht lesbar: {exc}")
        else:
            if isinstance(manifest, dict):
                findings.extend(manifest_case_findings(tracked, manifest))

    for rel in ("PROJECT_STATE.md", ".project/project.config.json", ".project/state/current.json", "AGENTS.md"):
        if not (root / rel).is_file():
            findings.append(f"Pflichtdatei fehlt: {rel}")
    return {"ok": not findings, "trackedFiles": len(tracked), "findings": findings}


def main() -> int:
    payload = audit(ROOT)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
