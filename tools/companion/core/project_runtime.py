from __future__ import annotations

import importlib.util
import http.client
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import urlparse

from tools.companion.core.config import ProjectConfig

RUNTIME_ID_RE = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
PROJECT_RUNTIME_MODULE = "tools/companion/project_runtime.py"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class ProjectRuntimeError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProjectRuntimeSpec:
    id: str
    label: str
    command: list[str]
    url: str
    health_url: str | None = None
    auto_start: bool = True
    open_browser: bool = False
    start_timeout: int = 20

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "url": self.url,
            "healthUrl": self.health_url or self.url,
            "autoStart": self.auto_start,
            "openBrowser": self.open_browser,
        }


def _validate_loopback_url(value: str, field: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in LOOPBACK_HOSTS:
        raise ProjectRuntimeError(f"{field} muss eine lokale HTTP(S)-URL sein: {value}")
    if parsed.username or parsed.password:
        raise ProjectRuntimeError(f"{field} darf keine Zugangsdaten enthalten")
    return value


class ProjectRuntimeRegistry:
    """Supervises project-owned local product servers without shell execution."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self._specs: dict[str, ProjectRuntimeSpec] = {}
        self._processes: dict[str, subprocess.Popen] = {}
        self._external: set[str] = set()
        self._errors: dict[str, str] = {}

    def register(self, spec: ProjectRuntimeSpec) -> None:
        if not isinstance(spec, ProjectRuntimeSpec):
            raise ProjectRuntimeError("Project Runtime Registry akzeptiert nur ProjectRuntimeSpec")
        if not RUNTIME_ID_RE.fullmatch(spec.id) or spec.id in self._specs:
            raise ProjectRuntimeError(f"Doppelte oder ungültige Project-Runtime-ID: {spec.id!r}")
        if not spec.label.strip():
            raise ProjectRuntimeError(f"Project Runtime {spec.id} benötigt ein Label")
        if not spec.command or any(not isinstance(item, str) or not item.strip() for item in spec.command):
            raise ProjectRuntimeError(f"Project Runtime {spec.id} benötigt eine Argumentliste")
        _validate_loopback_url(spec.url, "url")
        _validate_loopback_url(spec.health_url or spec.url, "health_url")
        if not isinstance(spec.start_timeout, int) or not 1 <= spec.start_timeout <= 120:
            raise ProjectRuntimeError(f"Project Runtime {spec.id}: start_timeout muss 1..120 sein")
        self._specs[spec.id] = spec

    def all(self) -> list[ProjectRuntimeSpec]:
        return list(self._specs.values())

    @staticmethod
    def _healthy(url: str) -> bool:
        connection: http.client.HTTPConnection | None = None
        try:
            parsed = urlparse(url)
            connection_type = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
            connection = connection_type(parsed.hostname, parsed.port, timeout=0.75)
            path = parsed.path or "/"
            if parsed.query:
                path = f"{path}?{parsed.query}"
            connection.request("GET", path, headers={"User-Agent": "Project-Engineering-Companion/1"})
            response = connection.getresponse()
            return 200 <= int(response.status) < 300
        except Exception:
            return False
        finally:
            if connection is not None:
                connection.close()

    def start(self, runtime_id: str) -> dict[str, Any]:
        spec = self._specs.get(runtime_id)
        if spec is None:
            raise ProjectRuntimeError(f"Unbekannte Project Runtime: {runtime_id}")
        health_url = spec.health_url or spec.url
        if self._healthy(health_url):
            self._external.add(runtime_id)
            self._errors.pop(runtime_id, None)
            return {"ok": True, "id": runtime_id, "running": True, "managed": False, "url": spec.url}

        current = self._processes.get(runtime_id)
        if current is None or current.poll() is not None:
            try:
                self._processes[runtime_id] = subprocess.Popen(
                    spec.command,
                    cwd=self.root,
                    stdin=subprocess.DEVNULL,
                    shell=False,
                )
            except OSError as exc:
                self._errors[runtime_id] = str(exc)
                return {"ok": False, "id": runtime_id, "running": False, "managed": True, "error": str(exc)}

        deadline = time.monotonic() + spec.start_timeout
        process = self._processes[runtime_id]
        while time.monotonic() < deadline:
            if process.poll() is not None:
                error = f"Prozess endete mit Exit {process.returncode}"
                self._errors[runtime_id] = error
                return {"ok": False, "id": runtime_id, "running": False, "managed": True, "error": error}
            if self._healthy(health_url):
                self._errors.pop(runtime_id, None)
                return {"ok": True, "id": runtime_id, "running": True, "managed": True, "url": spec.url}
            time.sleep(0.1)

        self._stop_process(runtime_id)
        error = f"Health-Check nach {spec.start_timeout}s nicht grün: {health_url}"
        self._errors[runtime_id] = error
        return {"ok": False, "id": runtime_id, "running": False, "managed": True, "error": error}

    def start_all(self) -> list[dict[str, Any]]:
        return [self.start(spec.id) for spec in self.all() if spec.auto_start]

    def _stop_process(self, runtime_id: str) -> None:
        process = self._processes.pop(runtime_id, None)
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    def stop_all(self) -> None:
        for runtime_id in list(self._processes):
            self._stop_process(runtime_id)
        self._external.clear()

    def status(self) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for spec in self.all():
            process = self._processes.get(spec.id)
            process_running = process is not None and process.poll() is None
            healthy = self._healthy(spec.health_url or spec.url)
            rows.append({
                **spec.public(),
                "running": bool(healthy or process_running),
                "healthy": healthy,
                "managed": process_running,
                "external": spec.id in self._external,
                "error": self._errors.get(spec.id, ""),
            })
        return {
            "ok": all(row["healthy"] or not row["autoStart"] for row in rows),
            "runtimeCount": len(rows),
            "healthyCount": sum(1 for row in rows if row["healthy"]),
            "runtimes": rows,
        }

    def browser_url(self) -> str:
        return next((spec.url for spec in self.all() if spec.open_browser and self._healthy(spec.health_url or spec.url)), "")


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("project_companion_runtime", path)
    if spec is None or spec.loader is None:
        raise ProjectRuntimeError(f"Project-Runtime-Modul kann nicht geladen werden: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_project_runtimes(root: Path, config: ProjectConfig) -> ProjectRuntimeRegistry:
    registry = ProjectRuntimeRegistry(root)
    module_path = (root / PROJECT_RUNTIME_MODULE).resolve()
    if not module_path.is_file():
        return registry
    try:
        module_path.relative_to(root.resolve())
    except ValueError as exc:
        raise ProjectRuntimeError("Project-Runtime-Modul liegt außerhalb des Repositories") from exc
    module = _load_module(module_path)
    register = getattr(module, "register_project_runtimes", None)
    if not callable(register):
        raise ProjectRuntimeError(
            f"{PROJECT_RUNTIME_MODULE} benötigt register_project_runtimes(registry, root, config)"
        )
    register(registry, root.resolve(), config)
    return registry
