#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
WEB = Path(__file__).resolve().parent
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8770
MAX_PORT_TRIES = 20

ACTIONS: dict[str, list[str]] = {
    "status": ["git", "status", "--short", "--branch"],
    "fetch": ["git", "fetch", "--prune", "origin"],
    "pull": ["git", "pull", "--ff-only"],
    "audit": ["python3", "./tools/companion/audit_repo.py"],
    "canvas-fix-check": ["pwsh", "./powerplatform/scripts/Fix-LocalizedCanvasReferences.ps1", "-CheckOnly"],
    "validate": ["pwsh", "./powerplatform/scripts/Validate-CanvasSource.ps1"],
    "build": ["pwsh", "./powerplatform/scripts/Build.ps1"],
}


def run_process(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=3600,
    )


def run_action(name: str) -> dict[str, object]:
    command = ACTIONS.get(name)
    if command is None:
        return {"ok": False, "exitCode": 404, "output": "Unbekannte Aktion."}

    if name == "pull":
        dirty = run_process(["git", "status", "--porcelain"])
        if dirty.stdout.strip():
            return {
                "ok": False,
                "exitCode": 409,
                "command": "git pull --ff-only",
                "output": "Pull abgebrochen: Arbeitsverzeichnis enthält lokale Änderungen.\n" + dirty.stdout,
            }

    try:
        result = run_process(command)
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "exitCode": 408,
            "command": " ".join(command),
            "output": "Aktion nach 60 Minuten abgebrochen.",
        }

    return {
        "ok": result.returncode == 0,
        "exitCode": result.returncode,
        "command": " ".join(command),
        "output": result.stdout,
    }


def repository_info() -> dict[str, object]:
    branch = run_process(["git", "branch", "--show-current"]).stdout.strip()
    version_file = ROOT / "powerplatform" / "VERSION"
    version = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "unbekannt"
    dirty = bool(run_process(["git", "status", "--porcelain"]).stdout.strip())
    return {"branch": branch, "version": version, "dirty": dirty, "root": str(ROOT)}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, format: str, *args: object) -> None:
        return

    def send_json(self, payload: dict[str, object], status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if urlparse(self.path).path == "/api/info":
            self.send_json(repository_info())
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/action/"):
            self.send_error(404)
            return
        action = parsed.path.rsplit("/", 1)[-1]
        self.send_json(run_action(action))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Governance Developer Companion")
    parser.add_argument("--host", default=os.getenv("GOVERNANCE_COMPANION_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args()


def port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def choose_port(host: str, requested: int | None) -> int:
    if requested is not None:
        if not port_available(host, requested):
            raise SystemExit(f"Port {requested} ist bereits belegt.")
        return requested

    start = int(os.getenv("GOVERNANCE_COMPANION_PORT", str(DEFAULT_PORT)))
    for port in range(start, start + MAX_PORT_TRIES):
        if port_available(host, port):
            return port
    raise SystemExit(f"Kein freier Port im Bereich {start}-{start + MAX_PORT_TRIES - 1} gefunden.")


if __name__ == "__main__":
    args = parse_args()
    port = choose_port(args.host, args.port)
    address = (args.host, port)
    url = f"http://{address[0]}:{address[1]}"
    print(f"Governance Developer Companion: {url}")
    print(f"Repository: {ROOT}")
    server = ThreadingHTTPServer(address, Handler)
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCompanion beendet.")
    finally:
        server.server_close()
