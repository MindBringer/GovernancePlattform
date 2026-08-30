#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(root: Path, args: list[str]) -> None:
    proc = subprocess.run(args, cwd=root, text=True, capture_output=True, timeout=240, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}\n{proc.stdout}\n{proc.stderr}".strip())


def copy_template(destination: Path) -> None:
    ignored = shutil.ignore_patterns(".git", ".framework-backup", "__pycache__", "*.pyc", ".DS_Store")
    shutil.copytree(ROOT, destination, dirs_exist_ok=True, ignore=ignored)


def prepare_module_stubs(root: Path, power_platform: bool, provisioning: bool) -> None:
    if power_platform:
        scripts = root / "powerplatform" / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        (scripts / "Validate-Solution.ps1").write_text("Write-Output 'validate stub'\n", encoding="utf-8")
        (scripts / "Build.ps1").write_text("Write-Output 'build stub'\n", encoding="utf-8")
    if provisioning:
        folder = root / "Provisioning"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "Invoke-ProvisioningLocal.ps1").write_text("param([string]$Mode)\nWrite-Output $Mode\n", encoding="utf-8")


def prepare_project_ui_smoke(root: Path) -> None:
    adapter = root / "tools/companion/project_ui.py"
    adapter.write_text(
        "from tools.companion.core.ui_extensions import ProjectViewSpec\n"
        "def register_project_ui(registry, root, config):\n"
        "    registry.register(ProjectViewSpec(id='smoke-overview', label='Smoke', dashboard=True, provider=lambda: {'metrics':[{'label':'status','value':'ok'}]}))\n",
        encoding="utf-8",
    )


def smoke_variant(base: Path, name: str, *, power_platform: bool = False, provisioning: bool = False) -> dict[str, object]:
    root = base / name
    copy_template(root)
    args = [
        sys.executable, "tools/framework/init_project.py",
        "--key", f"smoke-{name}",
        "--name", f"Smoke {name}",
        "--version", "0.1.0",
        "--port", "8899",
    ]
    if power_platform:
        args.append("--power-platform")
    if provisioning:
        args.append("--provisioning")
    run(root, args)
    prepare_module_stubs(root, power_platform, provisioning)
    prepare_project_ui_smoke(root)
    run(root, [sys.executable, "tools/framework/project_memory.py"])
    run(root, [sys.executable, "tools/framework/validate.py"])
    run(root, [sys.executable, "-m", "compileall", "-q", "tools", "tests"])
    run(root, [sys.executable, "-m", "unittest", "discover", "-s", "tests/framework", "-p", "test_*.py"])
    run(root, [
        sys.executable,
        "-c",
        "from tools.companion.server import project_payload, PROJECT_UI; "
        "p=project_payload(); assert p['ok']; assert p['projectUI']['views'][0]['id']=='smoke-overview'; "
        "assert p['projectRuntimes']['runtimeCount']==0; "
        "assert PROJECT_UI.data('smoke-overview')['metrics'][0]['value']=='ok'",
    ])

    config = json.loads((root / ".project" / "project.config.json").read_text(encoding="utf-8"))
    state = json.loads((root / ".project" / "state" / "current.json").read_text(encoding="utf-8"))
    gates = config.get("release", {}).get("gates", [])
    if "bootstrap-smoke" in gates:
        raise RuntimeError(f"Consumer {name} enthält weiterhin das Template-only Release-Gate bootstrap-smoke")
    runtime_adapter = root / "tools" / "companion" / "project_runtime.py"
    if not runtime_adapter.is_file():
        raise RuntimeError(f"Consumer {name} enthält keinen project-owned Runtime-Adapter")
    return {
        "variant": name,
        "frameworkVersion": config.get("frameworkVersion"),
        "projectKey": config.get("project", {}).get("key"),
        "powerPlatform": config.get("modules", {}).get("powerPlatform"),
        "provisioning": config.get("modules", {}).get("provisioning"),
        "projectUI": config.get("ui", {}).get("projectUI", {}).get("enabled"),
        "projectRuntime": True,
        "releaseGates": gates,
        "nextStep": state.get("nextStep", {}).get("id"),
    }


def main() -> int:
    try:
        config = json.loads((ROOT / ".project" / "project.config.json").read_text(encoding="utf-8"))
        if config.get("project", {}).get("key") != "project-template":
            print(json.dumps({
                "ok": True,
                "skipped": True,
                "reason": "Bootstrap-Smoke ist nur für das Project Engineering Template relevant.",
                "projectKey": config.get("project", {}).get("key"),
            }, ensure_ascii=False, indent=2))
            return 0
        with tempfile.TemporaryDirectory(prefix="engineering-template-smoke-") as tmp:
            base = Path(tmp)
            results = [
                smoke_variant(base, "plain"),
                smoke_variant(base, "powerplatform", power_platform=True),
                smoke_variant(base, "provisioning", provisioning=True),
            ]
        print(json.dumps({"ok": True, "variants": results}, ensure_ascii=False, indent=2))
        return 0
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
