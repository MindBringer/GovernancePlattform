#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def digest(path: Path) -> str:
    raw = path.read_bytes()
    # Framework-managed files are primarily text. Canonicalize line endings so
    # the same commit produces the same lock on Linux, macOS and Windows.
    # Binary files keep their original bytes.
    if b"\x00" not in raw:
        try:
            text = raw.decode("utf-8")
            raw = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        except UnicodeDecodeError:
            pass
    return hashlib.sha256(raw).hexdigest()


def portable_key(value: str | Path) -> str:
    """Return one stable repository-relative key format on every OS."""
    return str(value).replace("\\", "/")


def portable_case_key(value: str | Path) -> str:
    """Return a case-insensitive comparison key for cross-platform path safety."""
    return portable_key(value).casefold()


def expand(root: Path, entries: list[str]) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for rel in entries:
        path = root / rel
        if path.is_file():
            files[portable_key(rel)] = path
        elif path.is_dir():
            for item in sorted(path.rglob("*")):
                if item.is_file() and "__pycache__" not in item.parts and not item.name.endswith(".pyc"):
                    files[portable_key(item.relative_to(root))] = item
    return files


def load_manifest(root: Path) -> dict:
    return json.loads((root / ".project/framework.manifest.json").read_text(encoding="utf-8"))


def load_project_config(root: Path) -> dict:
    return json.loads((root / ".project/project.config.json").read_text(encoding="utf-8"))


def project_key(root: Path) -> str:
    try:
        return str(load_project_config(root).get("project", {}).get("key") or "")
    except (OSError, json.JSONDecodeError):
        return ""


def lock_refresh_allowed(root: Path) -> bool:
    """Only the canonical template may bless framework-managed file hashes directly."""
    return project_key(root) == "project-template"


def source_is_template(root: Path) -> bool:
    return project_key(root) == "project-template"


def update_project_state_framework_version(root: Path, framework_version: object) -> bool:
    """Align only the project-owned frameworkVersion marker during controlled adoption."""
    state_path = root / ".project" / "state" / "current.json"
    if not state_path.is_file():
        return False

    version = str(framework_version or "").strip()
    if not version:
        raise ValueError("Framework-Version für Project State fehlt")

    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Project State nicht lesbar: {exc}") from exc
    if not isinstance(state, dict):
        raise ValueError("Project State muss ein JSON-Objekt sein")

    if str(state.get("frameworkVersion") or "") == version:
        return False

    state["frameworkVersion"] = version
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def _manifest_entries(manifest: dict, key: str) -> list[str]:
    raw = manifest.get(key, [])
    if not isinstance(raw, list):
        raise ValueError(f"Framework-Manifest {key} muss eine Liste sein")
    return [portable_key(str(item)) for item in raw]


def merge_manifest_contract(local_manifest: dict, source_manifest: dict) -> dict:
    """Adopt the source ownership contract without dropping consumer-owned additions."""
    source_managed = _manifest_entries(source_manifest, "managed")
    source_owned = _manifest_entries(source_manifest, "projectOwned")
    local_owned = _manifest_entries(local_manifest, "projectOwned")

    source_managed_set = set(source_managed)
    source_owned_set = set(source_owned)
    local_extras = [
        item for item in local_owned
        if item not in source_owned_set and item not in source_managed_set
    ]

    merged = dict(local_manifest)
    merged["schemaVersion"] = source_manifest.get("schemaVersion", local_manifest.get("schemaVersion", 1))
    merged["frameworkVersion"] = source_manifest.get("frameworkVersion")
    merged["managed"] = source_managed
    merged["projectOwned"] = source_owned + local_extras

    overlap = sorted(set(merged["managed"]) & set(merged["projectOwned"]))
    if overlap:
        raise ValueError(f"Framework-Manifest Ownership überschneidet sich: {overlap}")
    return merged


def manifest_contract_changed(local_manifest: dict, source_manifest: dict) -> bool:
    merged = merge_manifest_contract(local_manifest, source_manifest)
    for key in ("schemaVersion", "frameworkVersion", "managed", "projectOwned"):
        if local_manifest.get(key) != merged.get(key):
            return True
    return False


def path_is_project_owned(relative: str, entries: list[str]) -> bool:
    relative_key = portable_case_key(relative).rstrip("/")
    for entry in entries:
        owned = portable_case_key(entry).rstrip("/")
        if relative_key == owned or relative_key.startswith(owned + "/"):
            return True
    return False


def stale_managed_files(
    root: Path,
    local_manifest: dict,
    source_files: dict[str, Path],
    merged_manifest: dict,
) -> list[str]:
    """Return consumer-only files that still live inside framework-managed surfaces."""
    local_files = expand(root, local_manifest.get("managed", []))
    project_owned = _manifest_entries(merged_manifest, "projectOwned")
    return sorted(
        relative
        for relative in local_files
        if relative not in source_files
        and not path_is_project_owned(relative, project_owned)
    )


def build_lock(root: Path) -> dict:
    manifest = load_manifest(root)
    files = expand(root, manifest.get("managed", []))
    return {
        "schemaVersion": 2,
        "digestMode": "sha256-normalized-text-v1",
        "frameworkVersion": manifest.get("frameworkVersion"),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "files": {rel: digest(path) for rel, path in files.items()},
    }


def verify_lock(root: Path) -> tuple[bool, dict[str, object]]:
    lock_path = root / ".project/framework.lock.json"
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, {"error": f"Lock nicht lesbar: {exc}"}
    try:
        manifest = load_manifest(root)
        config = load_project_config(root)
    except (OSError, json.JSONDecodeError) as exc:
        return False, {"error": f"Framework-Metadaten nicht lesbar: {exc}"}
    current = {rel: digest(path) for rel, path in expand(root, manifest.get("managed", [])).items()}
    expected_raw = lock.get("files", {}) if isinstance(lock.get("files"), dict) else {}
    expected = {portable_key(str(rel)): value for rel, value in expected_raw.items()}
    changed = sorted(rel for rel, value in current.items() if expected.get(rel) != value)
    missing = sorted(rel for rel in current if rel not in expected)
    stale = sorted(rel for rel in expected if rel not in current)
    manifest_version = manifest.get("frameworkVersion")
    lock_version = lock.get("frameworkVersion")
    config_version = config.get("frameworkVersion")
    version_ok = lock_version == manifest_version == config_version
    digest_ok = lock.get("digestMode") == "sha256-normalized-text-v1"
    ok = version_ok and digest_ok and not changed and not missing and not stale
    return ok, {
        "ok": ok,
        "frameworkVersion": manifest_version,
        "configVersion": config_version,
        "lockVersion": lock_version,
        "digestMode": lock.get("digestMode"),
        "changed": changed,
        "missing": missing,
        "stale": stale,
        "lockRefreshAllowed": lock_refresh_allowed(root),
        "policy": "version delta is informational; framework-managed drift is blocking",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Controlled local framework sync")
    parser.add_argument("mode", choices=["check", "apply", "lock", "verify-lock", "integrity"])
    parser.add_argument("--source", help="Local clone/path of Project Engineering Template")
    args = parser.parse_args()

    if args.mode == "lock":
        if not lock_refresh_allowed(ROOT):
            print(
                "BLOCKED: Consumer-Repositories dürfen framework-managed Änderungen nicht durch einen neuen Lock legitimieren.\n"
                "Framework-Änderungen zuerst im zentralen Project-Engineering-Template umsetzen und releasen; "
                "danach den Consumer per sync.py apply --source <aktuelles Template> aktualisieren."
            )
            return 3
        payload = build_lock(ROOT)
        (ROOT / ".project/framework.lock.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Lock aktualisiert: {len(payload['files'])} managed files · {payload['digestMode']}")
        return 0

    if args.mode in {"verify-lock", "integrity"}:
        ok, result = verify_lock(ROOT)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if ok else 1

    if not args.source:
        raise SystemExit("check/apply benötigen --source <lokaler Template-Pfad>")
    source = Path(args.source).expanduser().resolve()
    if not source_is_template(source):
        raise SystemExit("Source ist kein Project-Engineering-Template (project.key != project-template).")
    source_ok, source_result = verify_lock(source)
    if not source_ok:
        raise SystemExit("Template-Source hat keinen gültigen Framework-Lock: " + json.dumps(source_result, ensure_ascii=False))

    source_manifest = load_manifest(source)
    source_files = expand(source, source_manifest.get("managed", []))
    changed: list[str] = []
    missing: list[str] = []
    for rel, src in source_files.items():
        dst = ROOT / rel
        if not dst.is_file():
            missing.append(rel)
        elif digest(dst) != digest(src):
            changed.append(rel)

    local_manifest = load_manifest(ROOT)
    try:
        merged_manifest = merge_manifest_contract(local_manifest, source_manifest)
        manifest_changed = manifest_contract_changed(local_manifest, source_manifest)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    stale_managed = stale_managed_files(
        ROOT,
        local_manifest,
        source_files,
        merged_manifest,
    )

    print(f"Installed: {local_manifest.get('frameworkVersion')}\nSource:    {source_manifest.get('frameworkVersion')}")
    print(
        f"Changed: {len(changed)} · Missing: {len(missing)} · "
        f"Stale managed: {len(stale_managed)} · "
        f"Manifest: {'update' if manifest_changed else 'current'}"
    )
    for rel in changed:
        print(f"M {rel}")
    for rel in missing:
        print(f"+ {rel}")
    for rel in stale_managed:
        print(f"- {rel}")

    if args.mode == "check":
        return 2 if changed or missing or stale_managed or manifest_changed else 0

    backup_root = ROOT / ".framework-backup" / datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_candidates = sorted(set(changed + stale_managed))
    for rel in backup_candidates:
        dst = ROOT / rel
        backup = backup_root / rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dst, backup)

    for rel in stale_managed:
        dst = ROOT / rel
        if dst.is_file():
            dst.unlink()
    for rel, src in source_files.items():
        dst = ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    local_manifest = merged_manifest
    (ROOT / ".project/framework.manifest.json").write_text(json.dumps(local_manifest, indent=2) + "\n", encoding="utf-8")
    config_path = ROOT / ".project/project.config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["frameworkVersion"] = source_manifest.get("frameworkVersion")
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_project_state_framework_version(ROOT, source_manifest.get("frameworkVersion"))

    lock = build_lock(ROOT)
    (ROOT / ".project/framework.lock.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(f"Framework angewendet. Backup: {backup_root if backup_candidates else 'nicht erforderlich'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
