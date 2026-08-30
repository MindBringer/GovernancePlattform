from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from tools.companion.core.config import ProjectConfig
from tools.companion.core.project_runtime import ProjectRuntimeError, ProjectRuntimeRegistry, ProjectRuntimeSpec, load_project_runtimes


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class ProjectRuntimeTests(unittest.TestCase):
    def test_runtime_starts_health_checks_and_stops_owned_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            port = free_port()
            server_source = (
                "import socket, sys\n"
                "server = socket.socket()\n"
                "server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n"
                "server.bind(('127.0.0.1', int(sys.argv[1])))\n"
                "server.listen(5)\n"
                "while True:\n"
                " connection, _ = server.accept()\n"
                " with connection:\n"
                "  connection.recv(4096)\n"
                "  connection.sendall(b'HTTP/1.1 200 OK\\r\\nContent-Length: 2\\r\\nConnection: close\\r\\n\\r\\nOK')\n"
            )
            registry = ProjectRuntimeRegistry(Path(tmp))
            registry.register(ProjectRuntimeSpec(
                id="app", label="App",
                command=[sys.executable, "-c", server_source, str(port)],
                url=f"http://127.0.0.1:{port}/", open_browser=True, start_timeout=15,
            ))
            proxy_env = {
                "HTTP_PROXY": "http://127.0.0.1:9",
                "HTTPS_PROXY": "http://127.0.0.1:9",
                "NO_PROXY": "",
                "http_proxy": "http://127.0.0.1:9",
                "https_proxy": "http://127.0.0.1:9",
                "no_proxy": "",
            }
            with mock.patch.dict(os.environ, proxy_env):
                self.assertTrue(registry.start_all()[0]["ok"])
            self.assertTrue(registry.status()["runtimes"][0]["managed"])
            self.assertEqual(registry.browser_url(), f"http://127.0.0.1:{port}/")
            registry.stop_all()
            self.assertFalse(registry.status()["runtimes"][0]["running"])

    def test_non_success_health_response_is_rejected(self):
        port = free_port()

        class NotFoundHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                body = b"<!doctype html><title>not found</title>"
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", port), NotFoundHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            self.assertFalse(ProjectRuntimeRegistry._healthy(f"http://127.0.0.1:{port}/api/runtime-health"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_remote_url_and_empty_command_are_rejected(self):
        registry = ProjectRuntimeRegistry(Path.cwd())
        with self.assertRaises(ProjectRuntimeError):
            registry.register(ProjectRuntimeSpec(id="remote", label="Remote", command=["x"], url="https://example.com"))
        with self.assertRaises(ProjectRuntimeError):
            registry.register(ProjectRuntimeSpec(id="shell", label="Shell", command=[], url="http://127.0.0.1:9999"))

    def test_public_contract_does_not_expose_command(self):
        spec = ProjectRuntimeSpec(id="app", label="App", command=["secret", "argument"], url="http://localhost:9999")
        self.assertNotIn("command", spec.public())

    def test_missing_adapter_is_optional_and_adapter_can_register(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = ProjectConfig(root, {"project": {"versionFile": "VERSION"}})
            self.assertEqual(load_project_runtimes(root, cfg).all(), [])
            adapter = root / "tools/companion/project_runtime.py"
            adapter.parent.mkdir(parents=True)
            adapter.write_text(
                "from tools.companion.core.project_runtime import ProjectRuntimeSpec\n"
                "def register_project_runtimes(registry, root, config):\n"
                " registry.register(ProjectRuntimeSpec(id='app', label='App', command=['python3'], url='http://127.0.0.1:9999'))\n",
                encoding="utf-8",
            )
            self.assertEqual(load_project_runtimes(root, cfg).all()[0].id, "app")


if __name__ == "__main__":
    unittest.main()
