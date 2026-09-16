#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / ".project" / "state" / "current.json"
FORBIDDEN_TRACKED = {".DS_Store", ".env", "settings.local.psd1", "local.settings.json"}
TEXT_SUFFIXES = {".py", ".ps1", ".psm1", ".js", ".ts", ".tsx", ".jsx", ".json", ".md", ".yml", ".yaml", ".html", ".css", ".sh"}
SOURCE_SUFFIXES = {".py", ".ps1", ".psm1", ".js", ".ts", ".tsx", ".jsx", ".sh"}
CONFLICT_START_RE = re.compile(r"(?m)^\s*<<<<<<<\s+.+$")
CONFLICT_END_RE = re.compile(r"(?m)^\s*>>>>>>>\s+.+$")
COMMENT_MARKER_RE = re.compile(r"(?mi)^\s*(?:#|//|/\*)\s*.*\b(?:TODO|FIXME|XXX)\b")
VERSIONED_IMPL_RE = re.compile(r"(?:^|[-_.])(v|version)?\d{2,}(?:[-_.]|$)", re.IGNORECASE)
LEGACY_RE = re.compile(r"(?:^|[-_.])(legacy|deprecated|obsolete|old)(?:[-_.]|$)", re.IGNORECASE)


def _tracked_files(root: Path) -> list[str]:
    proc = subprocess.run(["git", "ls-files"], cwd=root, text=True, capture_output=True, timeout=30, check=False)
    return proc.stdout.splitlines() if proc.returncode == 0 else []


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def scan(root: Path = ROOT) -> dict[str, object]:
    tracked = _tracked_files(root)
    blockers: list[str] = []
    warnings: list[str] = []
    duplicate_buckets: dict[str, list[str]] = {}
    marker_count = 0

    for rel in tracked:
        path = root / rel
        name = path.name
        if name in FORBIDDEN_TRACKED or name.endswith(".local.json") or name.endswith(".local.psd1"):
            blockers.append(f"Lokale/secret-nahe Datei ist getrackt: {rel}")
        if not path.is_file():
            continue
        if path.stat().st_size > 5 * 1024 * 1024:
            warnings.append(f"Große getrackte Datei >5 MiB: {rel}")
        text = ""
        if path.suffix.lower() in TEXT_SUFFIXES:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = ""
            if CONFLICT_START_RE.search(text) or CONFLICT_END_RE.search(text):
                blockers.append(f"Unaufgelöster Merge-Konfliktmarker: {rel}")
        if path.suffix.lower() in SOURCE_SUFFIXES:
            hits = len(COMMENT_MARKER_RE.findall(text))
            marker_count += hits
            if hits:
                warnings.append(f"{hits} TODO/FIXME/XXX-Kommentar(e): {rel}")
            stem = path.stem
            if LEGACY_RE.search(stem):
                warnings.append(f"Legacy-/Deprecated-Dateiname prüfen: {rel}")
            if VERSIONED_IMPL_RE.search(stem):
                warnings.append(f"Versionierte Implementierungsdatei prüfen: {rel}")
            if path.stat().st_size > 0:
                duplicate_buckets.setdefault(_digest(path), []).append(rel)

    for paths in duplicate_buckets.values():
        if len(paths) > 1:
            warnings.append("Inhaltsgleiche Source-Dateien prüfen: " + ", ".join(sorted(paths)))

    findings = blockers + warnings
    return {
        "ok": not blockers,
        "scannerVersion": "1.1",
        "trackedFiles": len(tracked),
        "findings": len(findings),
        "blockers": blockers,
        "warnings": warnings,
        "markerCount": marker_count,
        "sample": findings[:20],
    }


def record_review(result: dict[str, object], root: Path = ROOT) -> None:
    state_path = root / ".project" / "state" / "current.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()
    state["technicalDebt"] = {
        "status": "reviewed" if result.get("ok") else "blocked",
        "scannerVersion": result.get("scannerVersion"),
        "findings": int(result.get("findings") or 0),
        "blockers": len(result.get("blockers") or []),
        "warnings": len(result.get("warnings") or []),
        "reviewedAt": now,
        "sample": result.get("sample") or [],
    }
    state["updatedAt"] = now
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Technical-debt and repository legacy sweep")
    parser.add_argument("--review", action="store_true", help="Review-Ergebnis in current.json festhalten")
    args = parser.parse_args()
    result = scan(ROOT)
    if args.review:
        record_review(result, ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
