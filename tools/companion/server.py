#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
WEB = Path(__file__).resolve().parent

ACTIONS: dict[str, list[str]] = {
    "status": ["git", "status", "--short", "--branch"],
    "fetch": ["git", "fetch", "--prune", "origin"],
    "pull": ["git", "pull", "--ff-only"],
    "canvas-fix-check": ["pwsh", "./powerplatform/scripts/Fix-LocalizedCanvasReferences.ps1", "-CheckOnly"],
    "validate": ["pwsh", "./powerplatform/scripts/Validate-CanvasSource.ps1"],
    "build": ["pwsh", "./powerplatform/scripts/Build.ps1"],
}


def run_action(name: str) -> dict[str, object]:
    command = ACTIONS.get(name)
    if command is None:
        return {"ok": False, "exitCode": 404, "output": "Unbekannte Aktion."}

    if name == "pull":
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
        )
        if dirty.stdout.strip():
            return {
                "ok": False,
                "exitCode": 409,
                "output": "Pull abgebrochen: Arbeitsverzeichnis enthält lokale Änderungen.\n" + dirty.stdout,
            }

    result = subprocess.run(
        command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=False,
    )
    return {
        "ok": result.returncode == 0,
        "exitCode": result.returncode,
        "command": " ".join(command),
        "output": result.stdout,
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/action/"):
            self.send_error(404)
            return
        action = parsed.path.rsplit("/", 1)[-1]
        payload = json.dumps(run_action(action), ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    address = ("127.0.0.1", 8765)
    print(f"Governance Companion: http://{address[0]}:{address[1]}")
    print(f"Repository: {ROOT}")
    ThreadingHTTPServer(address, Handler).serve_forever()
