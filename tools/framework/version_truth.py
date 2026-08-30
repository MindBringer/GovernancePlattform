#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def _render_marker(value: str, *, project_version: str, framework_version: str) -> str:
    return (
        value.replace("{projectVersion}", project_version)
        .replace("{frameworkVersion}", framework_version)
    )


def evaluate(
    root: Path,
    documentation: dict[str, object],
    *,
    project_version: str,
    framework_version: str,
) -> dict[str, object]:
    raw = documentation.get("versionTruth", [])
    errors: list[str] = []
    checks: list[dict[str, object]] = []

    if raw is None:
        raw = []
    if not isinstance(raw, list):
        return {
            "ok": False,
            "errors": ["documentation.versionTruth muss eine Liste sein"],
            "checks": [],
        }

    resolved_root = root.resolve()
    for index, item in enumerate(raw):
        prefix = f"documentation.versionTruth[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} muss ein Objekt sein")
            continue

        relative = str(item.get("path") or "").strip()
        contains = item.get("contains", [])
        if not relative:
            errors.append(f"{prefix}.path fehlt")
            continue
        if not isinstance(contains, list) or not contains:
            errors.append(f"{prefix}.contains muss eine nichtleere Liste sein")
            continue

        path = (resolved_root / relative).resolve()
        try:
            path.relative_to(resolved_root)
        except ValueError:
            errors.append(f"{prefix}.path verlässt den Repository-Root: {relative}")
            continue
        if not path.is_file():
            errors.append(f"Version-Truth-Dokument fehlt: {relative}")
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"Version-Truth-Dokument nicht lesbar: {relative}: {exc}")
            continue

        for marker_index, marker_raw in enumerate(contains):
            if not isinstance(marker_raw, str) or not marker_raw:
                errors.append(f"{prefix}.contains[{marker_index}] muss ein nichtleerer String sein")
                continue
            marker = _render_marker(
                marker_raw,
                project_version=project_version,
                framework_version=framework_version,
            )
            ok = marker in text
            checks.append({
                "path": relative,
                "marker": marker,
                "ok": ok,
            })
            if not ok:
                errors.append(f"Aktive Dokumentationswahrheit fehlt in {relative}: {marker}")

    return {
        "ok": not errors,
        "errors": errors,
        "checks": checks,
    }
