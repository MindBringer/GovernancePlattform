from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_current_state(root: Path) -> dict[str, Any]:
    path = root / ".project" / "state" / "current.json"
    if not path.is_file():
        return {"schemaVersion": 1, "nextStep": "nicht dokumentiert", "knownIssues": None}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schemaVersion": 1, "nextStep": "nicht lesbar", "error": str(exc)}
    return payload if isinstance(payload, dict) else {"error": "current.json ist kein Objekt"}


def load_project_memory(root: Path, relative_path: str = "PROJECT_STATE.md") -> str:
    path = (root / relative_path).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return "Projektgedächtnis-Pfad ist ungültig."
    if not path.is_file():
        return "Projektgedächtnis fehlt."
    return path.read_text(encoding="utf-8")
