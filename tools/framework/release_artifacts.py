#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.companion.core.config import ProjectConfig, load_config
from tools.companion.core.git_status import repository_status
from tools.companion.core.process import run_command


def _run(root: Path, command: list[str], timeout: int = 300) -> str:
    result = run_command(root, command, timeout)
    if not result.ok:
        raise RuntimeError(result.output or f"Exit {result.returncode}: {' '.join(command)}")
    return result.output.strip()


def publish_release_artifacts(root: Path, config: ProjectConfig) -> dict[str, Any]:
    release = config.data.get("release", {})
    version = config.version()
    base = str(release.get("baseBranch") or "main")
    prefix = str(release.get("tagPrefix") if release.get("tagPrefix") is not None else "v")
    tag = f"{prefix}{version}"
    status = repository_status(root)
    if status.get("branch") != base:
        raise RuntimeError(f"Release-Artefakte dürfen nur auf {base} erzeugt werden; aktuell: {status.get('branch')}")
    if status.get("dirty"):
        raise RuntimeError("Release-Artefakte erfordern ein sauberes Arbeitsverzeichnis.")

    _run(root, ["git", "fetch", "--tags", "--prune", "origin"], 300)
    head = _run(root, ["git", "rev-parse", "HEAD"], 30)
    tag_commit = run_command(root, ["git", "rev-list", "-n", "1", tag], 30)
    tag_created = False
    if tag_commit.ok and tag_commit.output.strip():
        if tag_commit.output.strip() != head:
            raise RuntimeError(f"Tag {tag} existiert bereits auf anderem Commit: {tag_commit.output.strip()}")
    elif release.get("createTag", True):
        _run(root, ["git", "tag", "-a", tag, "-m", f"{config.project['name']} {version}"], 60)
        _run(root, ["git", "push", "origin", tag], 300)
        tag_created = True

    github_release_created = False
    if release.get("createGitHubRelease", False):
        existing = run_command(root, ["gh", "release", "view", tag, "--json", "tagName"], 60)
        if not existing.ok:
            next_step = ""
            state_path = root / ".project" / "state" / "current.json"
            if state_path.is_file():
                try:
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                    if isinstance(state.get("nextStep"), dict):
                        next_step = str(state["nextStep"].get("description") or "")
                except (OSError, json.JSONDecodeError):
                    pass
            notes = f"Release {version} über Project Engineering Companion."
            if next_step:
                notes += f"\n\nNächster Schritt: {next_step}"
            _run(root, [
                "gh", "release", "create", tag,
                "--target", base,
                "--title", f"{config.project['name']} {version}",
                "--notes", notes,
            ], 300)
            github_release_created = True

    return {
        "ok": True,
        "version": version,
        "tag": tag,
        "commit": head,
        "tagCreated": tag_created,
        "githubReleaseCreated": github_release_created,
    }


def main() -> int:
    try:
        result = publish_release_artifacts(ROOT, load_config(ROOT))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
