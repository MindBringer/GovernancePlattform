from __future__ import annotations

import shutil
from pathlib import Path

from .process import run_command


def _text(root: Path, *command: str, timeout: int = 10) -> tuple[int, str]:
    result = run_command(root, command, timeout)
    return result.returncode, result.output.strip()


def _dirty_paths(lines: list[str]) -> list[str]:
    paths: list[str] = []
    for line in lines:
        if len(line) < 3 or line.startswith("##"):
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        if path and path not in paths:
            paths.append(path)
    return paths


def repository_status(root: Path) -> dict[str, object]:
    branch_rc, branch = _text(root, "git", "symbolic-ref", "--quiet", "--short", "HEAD")
    detached = branch_rc != 0
    if detached:
        branch = "(detached)"
    head_rc, head = _text(root, "git", "rev-parse", "--short", "HEAD")
    status_rc, status = _text(root, "git", "status", "--porcelain=v1", "--branch")
    lines = status.splitlines() if status_rc == 0 else []
    body = [line for line in lines if not line.startswith("##")]
    dirty = bool(body)
    dirty_paths = _dirty_paths(body)
    conflicts = [
        line[3:] for line in body
        if len(line) >= 3 and line[:2] in {"UU", "AA", "DD", "AU", "UA", "DU", "UD"}
    ]
    ahead = behind = 0
    count_rc, counts = _text(root, "git", "rev-list", "--left-right", "--count", "HEAD...@{upstream}")
    if count_rc == 0:
        parts = counts.split()
        if len(parts) == 2 and all(p.isdigit() for p in parts):
            ahead, behind = int(parts[0]), int(parts[1])
    origin_rc, origin = _text(root, "git", "remote", "get-url", "origin")
    gh_available = shutil.which("gh") is not None
    gh_authenticated = gh_available and _text(root, "gh", "auth", "status", timeout=20)[0] == 0
    ok = head_rc == 0 and status_rc == 0
    return {
        "ok": ok,
        "branch": branch,
        "detached": detached,
        "head": head if head_rc == 0 else "",
        "dirty": dirty,
        "dirtyPaths": dirty_paths,
        "state": "dirty" if dirty else "clean",
        "conflicts": conflicts,
        "ahead": ahead,
        "behind": behind,
        "origin": origin if origin_rc == 0 else "",
        "ghAvailable": gh_available,
        "ghAuthenticated": gh_authenticated,
    }


def guard_clean_worktree(root: Path) -> tuple[bool, str]:
    status = repository_status(root)
    if not status.get("ok"):
        return False, "Git-Status konnte nicht ermittelt werden."
    if status.get("dirty"):
        return False, "Aktion abgebrochen: Arbeitsverzeichnis enthält lokale Änderungen."
    return True, ""
