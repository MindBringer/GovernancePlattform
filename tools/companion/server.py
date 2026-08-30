#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import secrets
import socket
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
WEB = Path(__file__).resolve().parent / "web"
PROJECT_WEB = ROOT / "tools/companion/project_web"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.companion.core.action_jobs import ActionJobManager
from tools.companion.core.actions import ActionRegistry
from tools.companion.core.base_actions import register_base_actions
from tools.companion.core.config import ConfigError, load_config
from tools.companion.core.git_status import repository_status
from tools.companion.core.process import run_command
from tools.companion.core.project_runtime import ProjectRuntimeError, load_project_runtimes
from tools.companion.core.release import ReleaseEngine
from tools.companion.core.release_jobs import ReleaseJobManager
from tools.companion.core.state import load_current_state, load_project_memory
from tools.companion.core.ui_extensions import ProjectUIError, load_project_ui
from tools.companion.modules.powerplatform import register_powerplatform_actions
from tools.companion.modules.provisioning import register_provisioning_actions
from tools.companion.project_actions import register_project_actions

MAX_PORT_TRIES = 20
CSRF_TOKEN = secrets.token_urlsafe(32)
KEY_RE = re.compile(r"^[A-Za-z0-9._-]+$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def build_runtime():
    config = load_config(ROOT)
    registry = ActionRegistry(ROOT)
    register_base_actions(registry, ROOT, config)
    register_powerplatform_actions(registry, ROOT, config)
    register_provisioning_actions(registry, ROOT, config)
    register_project_actions(registry, ROOT, config)
    project_ui = load_project_ui(ROOT, config)
    project_runtimes = load_project_runtimes(ROOT, config)
    release = ReleaseEngine(ROOT, config, registry)
    return config, registry, project_ui, project_runtimes, release


CONFIG, REGISTRY, PROJECT_UI, PROJECT_RUNTIMES, RELEASE = build_runtime()
RELEASE_JOBS = ReleaseJobManager(
    lambda confirmation, progress: RELEASE.execute(confirmation, progress)
)
ACTION_JOBS = ActionJobManager(lambda: REGISTRY)


def reload_runtime() -> None:
    global CONFIG, REGISTRY, PROJECT_UI, PROJECT_RUNTIMES, RELEASE
    PROJECT_RUNTIMES.stop_all()
    CONFIG, REGISTRY, PROJECT_UI, PROJECT_RUNTIMES, RELEASE = build_runtime()


def release_tag() -> str:
    release = CONFIG.data.get("release", {})
    if not release.get("createTag", True) and not release.get("createGitHubRelease", False):
        return ""
    prefix = str(release.get("tagPrefix") if release.get("tagPrefix") is not None else "v")
    return f"{prefix}{CONFIG.version()}"


def project_payload() -> dict[str, object]:
    docs = CONFIG.data.get("documentation", {})
    state = load_current_state(ROOT)
    status = repository_status(ROOT)
    actions = [spec.public() for spec in REGISTRY.all()]
    categories: list[str] = []
    for action in actions:
        category = str(action["category"])
        if category not in categories:
            categories.append(category)
    ui = CONFIG.data.get("ui", {}) if isinstance(CONFIG.data.get("ui"), dict) else {}
    project_ui_config = ui.get("projectUI", {}) if isinstance(ui.get("projectUI"), dict) else {}
    return {
        "ok": True,
        "csrf": CSRF_TOKEN,
        "frameworkVersion": CONFIG.framework_version,
        "project": {
            **CONFIG.project,
            "version": CONFIG.version(),
        },
        "modules": CONFIG.modules,
        "ui": ui,
        "projectUI": {
            "enabled": bool(project_ui_config.get("enabled", True)),
            "allowCustomAssets": bool(project_ui_config.get("allowCustomAssets", False)),
            "views": PROJECT_UI.public(),
        },
        "projectRuntimes": PROJECT_RUNTIMES.status(),
        "actionJob": ACTION_JOBS.current(),
        "release": {
            "enabled": bool(CONFIG.data.get("release", {}).get("enabled", False)),
            "confirmation": str(CONFIG.data.get("release", {}).get("confirmation") or ""),
            "tag": release_tag(),
            "createTag": bool(CONFIG.data.get("release", {}).get("createTag", True)),
            "createGitHubRelease": bool(CONFIG.data.get("release", {}).get("createGitHubRelease", False)),
            "job": RELEASE_JOBS.current(),
        },
        "actions": actions,
        "categories": categories,
        "repository": status,
        "state": state,
        "docs": docs,
    }


def initialize_project(payload: dict[str, object]) -> dict[str, object]:
    if CONFIG.project.get("key") != "project-template":
        return {"ok": False, "exitCode": 409, "error": "Repository ist bereits initialisiert."}
    name = str(payload.get("name") or "").strip()
    key = str(payload.get("key") or "").strip()
    description = str(payload.get("description") or "").strip()
    version = str(payload.get("version") or "0.1.0").strip()
    try:
        port = int(payload.get("port") or 8765)
    except (TypeError, ValueError):
        port = 0
    if not name or len(name) > 120:
        return {"ok": False, "exitCode": 400, "error": "Projektname fehlt oder ist zu lang."}
    if not KEY_RE.fullmatch(key):
        return {"ok": False, "exitCode": 400, "error": "Projekt-Key darf nur Buchstaben, Zahlen, Punkt, Unterstrich und Bindestrich enthalten."}
    if not VERSION_RE.fullmatch(version):
        return {"ok": False, "exitCode": 400, "error": "Startversion muss SemVer im Format X.Y.Z sein."}
    if not 1024 <= port <= 65535:
        return {"ok": False, "exitCode": 400, "error": "Companion-Port muss zwischen 1024 und 65535 liegen."}

    command = [
        sys.executable, "tools/framework/init_project.py",
        "--key", key,
        "--name", name,
        "--description", description,
        "--version", version,
        "--port", str(port),
    ]
    if bool(payload.get("powerPlatform")):
        command.append("--power-platform")
    if bool(payload.get("provisioning")):
        command.append("--provisioning")
    result = run_command(ROOT, command, 300)
    if not result.ok:
        return {"ok": False, "exitCode": result.returncode, "error": result.output or "Initialisierung fehlgeschlagen."}
    try:
        reload_runtime()
    except (ConfigError, ProjectUIError, ProjectRuntimeError) as exc:
        return {"ok": False, "exitCode": 500, "error": f"Initialisiert, aber neue Runtime ist ungültig: {exc}"}
    return {"ok": True, "exitCode": 0, "output": result.output or f"{name} wurde initialisiert."}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, format: str, *args: object) -> None:
        return

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; font-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        super().end_headers()

    def send_json(self, payload: dict[str, object], status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def read_payload(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        body = self.rfile.read(min(length, 65536)) if length else b"{}"
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def check_csrf(self) -> bool:
        if self.headers.get("X-CSRF-Token") != CSRF_TOKEN:
            self.send_json({"ok": False, "exitCode": 403, "output": "CSRF-Token ungültig."}, 403)
            return False
        return True

    def serve_project_asset(self, request_path: str) -> None:
        relative = unquote(request_path.removeprefix("/project-ui/assets/")).lstrip("/")
        if not relative or not PROJECT_UI.allow_custom_assets or relative not in PROJECT_UI.asset_paths():
            self.send_error(404)
            return
        root = PROJECT_WEB.resolve()
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            self.send_error(404)
            return
        if not candidate.is_file():
            self.send_error(404)
            return
        mime, _ = mimetypes.guess_type(candidate.name)
        data = candidate.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/project":
            self.send_json(project_payload())
            return
        if path == "/api/status":
            self.send_json({
                "ok": True,
                "repository": repository_status(ROOT),
                "state": load_current_state(ROOT),
                "version": CONFIG.version(),
                "frameworkVersion": CONFIG.framework_version,
            })
            return
        if path == "/api/project-memory":
            relative = str(CONFIG.data.get("documentation", {}).get("projectState") or "PROJECT_STATE.md")
            self.send_json({"ok": True, "content": load_project_memory(ROOT, relative)})
            return
        if path == "/api/project-runtimes":
            self.send_json(PROJECT_RUNTIMES.status())
            return
        if path == "/api/action-job":
            self.send_json(ACTION_JOBS.status())
            return
        if path == "/api/release-job":
            self.send_json(RELEASE_JOBS.status())
            return
        if path.startswith("/api/project-view/"):
            view_id = unquote(path.removeprefix("/api/project-view/")).strip()
            try:
                payload = PROJECT_UI.data(view_id)
            except ProjectUIError as exc:
                self.send_json({"ok": False, "error": str(exc)}, 404)
                return
            except Exception as exc:
                self.send_json({"ok": False, "error": f"Project-View-Provider fehlgeschlagen: {type(exc).__name__}: {exc}"}, 500)
                return
            self.send_json({"ok": True, "viewId": view_id, "data": payload})
            return
        if path.startswith("/project-ui/assets/"):
            self.serve_project_asset(path)
            return
        super().do_GET()

    def do_POST(self) -> None:
        if not self.check_csrf():
            return
        path = urlparse(self.path).path
        payload = self.read_payload()
        if path == "/api/init":
            result = initialize_project(payload)
            status = 200 if result.get("ok") else int(result.get("exitCode") or 400)
            self.send_json(result, status if status in {400, 403, 409, 500} else 200)
            return
        if not path.startswith("/api/action/"):
            self.send_json({"ok": False, "exitCode": 404, "output": "Unbekannter Endpunkt."}, 404)
            return
        action_id = path.rsplit("/", 1)[-1]
        confirmation = payload.get("confirmation")
        confirmation_text = str(confirmation) if confirmation is not None else None
        if action_id == "release":
            active_action = ACTION_JOBS.current()
            if active_action and active_action.get("status") == "running":
                self.send_json({
                    "ok": False,
                    "exitCode": 409,
                    "error": "Full Release ist blockiert, solange eine Background-Action läuft.",
                    "job": active_action,
                }, 409)
                return
            result = RELEASE_JOBS.start(confirmation_text)
            self.send_json(result, 202 if result.get("ok") else 409)
            return
        raw_input = payload.get("input")
        input_text = str(raw_input) if raw_input is not None else None
        spec = REGISTRY.get(action_id)
        if spec and spec.background:
            active_release = RELEASE_JOBS.current()
            if active_release and active_release.get("status") == "running":
                self.send_json({
                    "ok": False,
                    "exitCode": 409,
                    "error": "Background-Action ist blockiert, solange ein Full Release läuft.",
                    "job": active_release,
                }, 409)
                return
            result = ACTION_JOBS.start(action_id, confirmation_text, input_text)
            self.send_json(result, 202 if result.get("ok") else 409 if result.get("exitCode") == 409 else 404)
            return
        result = REGISTRY.execute(action_id, confirmation_text, input_text)
        code = int(result.get("exitCode") or 500)
        self.send_json(result, 200 if result.get("ok") else code if code in {403, 404, 408, 409} else 200)


def available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def choose_port(host: str, requested: int | None, default_port: int) -> int:
    if requested is not None:
        if not available(host, requested):
            raise SystemExit(f"Port {requested} ist bereits belegt.")
        return requested
    for port in range(default_port, default_port + MAX_PORT_TRIES):
        if available(host, port):
            return port
    raise SystemExit(f"Kein freier Port im Bereich {default_port}-{default_port + MAX_PORT_TRIES - 1} gefunden.")


def main() -> None:
    companion = CONFIG.data.get("companion", {})
    parser = argparse.ArgumentParser(description="Project Engineering Framework Companion")
    parser.add_argument("--host", default=os.getenv("ENGINEERING_COMPANION_HOST", str(companion.get("host") or "127.0.0.1")))
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Aus Sicherheitsgründen bindet das Engineering Framework nur an Loopback-Adressen.")
    default_port = int(os.getenv("ENGINEERING_COMPANION_PORT", str(companion.get("port") or 8765)))
    port = choose_port(args.host, args.port, default_port)
    url = f"http://{args.host}:{port}/"
    print(f"{CONFIG.project['name']} Engineering Companion: {url}")
    print(f"Repository: {ROOT}")
    print(f"Framework: {CONFIG.framework_version} · Projekt: {CONFIG.version()}")
    if PROJECT_UI.all():
        print(f"Project UI: {len(PROJECT_UI.all())} View(s)")

    server = ThreadingHTTPServer((args.host, port), Handler)
    for result in PROJECT_RUNTIMES.start_all():
        state = "OK" if result.get("ok") else "FEHLER"
        print(f"Project Runtime {result.get('id')}: {state} · {result.get('url') or result.get('error') or ''}")
    open_browser = bool(companion.get("openBrowser", True)) and not args.no_browser
    if open_browser:
        browser_url = PROJECT_RUNTIMES.browser_url() or url
        threading.Timer(0.5, lambda: webbrowser.open(browser_url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCompanion beendet.")
    finally:
        PROJECT_RUNTIMES.stop_all()
        server.server_close()


if __name__ == "__main__":
    try:
        main()
    except (ConfigError, ProjectUIError, ProjectRuntimeError) as exc:
        raise SystemExit(f"Konfigurationsfehler: {exc}") from exc
