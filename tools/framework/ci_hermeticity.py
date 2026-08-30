#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Mapping


SENSITIVE_ENV_RE = re.compile(r"(?:^|_)(?:TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|APIKEY|PRIVATE_KEY)$", re.IGNORECASE)
PATH_CONTEXT_RE = re.compile(r"(?:WORKSPACE|CONFIG_HOME|PROFILE_ROOT|LOCAL_SETTINGS|DATA_DIR)$", re.IGNORECASE)
SAFE_ENV_PREFIXES = ("GITHUB_", "RUNNER_", "ACTIONS_")
LOCAL_FILE_NAMES = {".env", "local.settings.json"}


def _git_status(root: Path) -> tuple[bool, list[str]]:
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if proc.returncode != 0:
        return False, [proc.stdout.strip() or "git status fehlgeschlagen"]
    return True, [line for line in proc.stdout.splitlines() if line.strip()]


def _allowed_env(environ: Mapping[str, str]) -> set[str]:
    raw = str(environ.get("ENGINEERING_CI_ALLOWED_ENV") or "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def inspect(root: Path, environ: Mapping[str, str] | None = None) -> dict[str, object]:
    env = dict(os.environ if environ is None else environ)
    findings: list[dict[str, str]] = []

    ok_status, status_lines = _git_status(root)
    if not ok_status:
        findings.append({"type": "git-status", "detail": status_lines[0]})
    elif status_lines:
        findings.append({
            "type": "dirty-checkout",
            "detail": "Checkout ist vor den Required Gates nicht sauber: " + " | ".join(status_lines[:20]),
        })

    workspace = Path(env.get("GITHUB_WORKSPACE") or root).resolve()
    try:
        same_workspace = root.resolve() == workspace
    except OSError:
        same_workspace = False
    if env.get("GITHUB_WORKSPACE") and not same_workspace:
        findings.append({
            "type": "workspace-root",
            "detail": f"cwd/root {root.resolve()} stimmt nicht mit GITHUB_WORKSPACE {workspace} überein.",
        })

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.name in LOCAL_FILE_NAMES:
            findings.append({
                "type": "local-config-file",
                "detail": f"Lokale Konfigurationsdatei im CI-Checkout: {path.relative_to(root).as_posix()}",
            })

    allowed = _allowed_env(env)
    runner_temp_raw = env.get("RUNNER_TEMP")
    runner_temp = Path(runner_temp_raw).resolve() if runner_temp_raw else None
    for name, value in sorted(env.items()):
        if name in allowed or name.startswith(SAFE_ENV_PREFIXES):
            continue
        if SENSITIVE_ENV_RE.search(name) and value:
            findings.append({
                "type": "sensitive-environment",
                "detail": f"Sensible Environment-Variable wird implizit an Required CI vererbt: {name}",
            })
            continue
        if not value or not PATH_CONTEXT_RE.search(name):
            continue
        try:
            candidate = Path(value).expanduser().resolve()
        except (OSError, RuntimeError):
            continue
        if not candidate.is_absolute():
            continue
        inside_workspace = candidate == workspace or workspace in candidate.parents
        inside_runner_temp = bool(runner_temp and (candidate == runner_temp or runner_temp in candidate.parents))
        if not inside_workspace and not inside_runner_temp:
            findings.append({
                "type": "external-runtime-context",
                "detail": f"Lokaler Runtime-/Workspace-Pfad wird implizit geerbt: {name}",
            })

    return {
        "ok": not findings,
        "workspace": str(workspace),
        "findings": findings,
        "allowedEnvironment": sorted(allowed),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prüft Self-Hosted Required CI auf lokalen/stalen Kontext.")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    result = inspect(root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
