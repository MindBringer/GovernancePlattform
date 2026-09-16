from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.framework.sync import (
    digest,
    expand,
    lock_refresh_allowed,
    merge_manifest_contract,
    portable_key,
    stale_managed_files,
    update_project_state_framework_version,
    verify_lock,
)


class SyncTests(unittest.TestCase):
    def test_text_digest_is_line_ending_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lf = root / "lf.txt"
            crlf = root / "crlf.txt"
            lf.write_bytes(b"one\ntwo\n")
            crlf.write_bytes(b"one\r\ntwo\r\n")
            self.assertEqual(digest(lf), digest(crlf))

    def test_binary_digest_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.bin"
            b = root / "b.bin"
            a.write_bytes(b"\x00one\r\ntwo")
            b.write_bytes(b"\x00one\ntwo")
            self.assertNotEqual(digest(a), digest(b))

    def test_portable_key_normalizes_windows_separators(self):
        self.assertEqual(portable_key(r"tools\framework\sync.py"), "tools/framework/sync.py")
        self.assertEqual(portable_key("tools/framework/sync.py"), "tools/framework/sync.py")

    def test_manifest_upgrade_adopts_framework_contract_and_preserves_consumer_owned_additions(self):
        local = {
            "schemaVersion": 1,
            "frameworkVersion": "1.1.1",
            "managed": ["tools/companion/core"],
            "projectOwned": ["AGENTS.md", "docs/local-only"],
            "consumerMeta": {"keep": True},
        }
        source = {
            "schemaVersion": 1,
            "frameworkVersion": "1.2.0",
            "managed": ["tools/companion/core", "tools/companion/web"],
            "projectOwned": ["AGENTS.md", "tools/companion/project_ui.py", "tools/companion/project_web"],
        }
        merged = merge_manifest_contract(local, source)
        self.assertEqual(merged["frameworkVersion"], "1.2.0")
        self.assertEqual(merged["managed"], source["managed"])
        self.assertEqual(
            merged["projectOwned"],
            ["AGENTS.md", "tools/companion/project_ui.py", "tools/companion/project_web", "docs/local-only"],
        )
        self.assertEqual(merged["consumerMeta"], {"keep": True})

    def test_manifest_upgrade_drops_local_owned_entry_when_framework_now_manages_it(self):
        local = {
            "managed": [],
            "projectOwned": ["tools/new-core", "docs/local-only"],
        }
        source = {
            "frameworkVersion": "1.2.0",
            "managed": ["tools/new-core"],
            "projectOwned": [],
        }
        merged = merge_manifest_contract(local, source)
        self.assertEqual(merged["managed"], ["tools/new-core"])
        self.assertEqual(merged["projectOwned"], ["docs/local-only"])

    def test_stale_managed_files_detects_consumer_only_framework_files(self):
        with tempfile.TemporaryDirectory() as local_tmp, tempfile.TemporaryDirectory() as source_tmp:
            local = Path(local_tmp)
            source = Path(source_tmp)
            (local / "managed").mkdir()
            (source / "managed").mkdir()

            (local / "managed/current.txt").write_text("current\n", encoding="utf-8")
            (local / "managed/stale.txt").write_text("stale\n", encoding="utf-8")
            (local / "managed/local-owned.txt").write_text("owned\n", encoding="utf-8")
            (source / "managed/current.txt").write_text("current\n", encoding="utf-8")

            local_manifest = {
                "schemaVersion": 1,
                "frameworkVersion": "1.3.9",
                "managed": ["managed"],
                "projectOwned": ["managed/local-owned.txt"],
            }
            source_manifest = {
                "schemaVersion": 1,
                "frameworkVersion": "1.3.10",
                "managed": ["managed"],
                "projectOwned": [],
            }

            merged = merge_manifest_contract(local_manifest, source_manifest)
            source_files = expand(source, source_manifest["managed"])
            stale = stale_managed_files(local, local_manifest, source_files, merged)

            self.assertEqual(["managed/stale.txt"], stale)

    def test_framework_adoption_updates_only_framework_version_in_project_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / ".project" / "state"
            state_dir.mkdir(parents=True)
            original = {
                "schemaVersion": 2,
                "frameworkVersion": "1.3.10",
                "projectVersion": "9.2.0",
                "nextStep": {"id": "keep", "description": "keep"},
                "verification": {"consumer": {"status": "keep"}},
                "lastRelease": {"version": "9.2.0", "status": "released"},
                "consumerData": {"nested": [1, 2, 3]},
            }
            state_path = state_dir / "current.json"
            state_path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")

            self.assertTrue(update_project_state_framework_version(root, "1.3.12"))
            updated = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(updated["frameworkVersion"], "1.3.12")

            expected = dict(original)
            expected["frameworkVersion"] = "1.3.12"
            self.assertEqual(updated, expected)
            self.assertFalse(update_project_state_framework_version(root, "1.3.12"))

    def test_framework_adoption_leaves_missing_project_state_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(update_project_state_framework_version(Path(tmp), "1.3.12"))

    def test_managed_text_files_have_no_blank_line_at_eof(self):
        root = Path(__file__).resolve().parents[2]
        manifest = json.loads((root / ".project/framework.manifest.json").read_text(encoding="utf-8"))
        findings = []
        for relative, path in expand(root, manifest.get("managed", [])).items():
            raw = path.read_bytes()
            if b"\x00" in raw:
                continue
            try:
                text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
            except UnicodeDecodeError:
                continue
            if text.endswith("\n\n"):
                findings.append(relative)
        self.assertEqual([], findings, f"framework-managed text files with blank line at EOF: {findings}")

    def test_only_template_may_refresh_framework_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".project").mkdir()
            (root / ".project/project.config.json").write_text(
                json.dumps({"project": {"key": "consumer"}}), encoding="utf-8"
            )
            self.assertFalse(lock_refresh_allowed(root))
            (root / ".project/project.config.json").write_text(
                json.dumps({"project": {"key": "project-template"}}), encoding="utf-8"
            )
            self.assertTrue(lock_refresh_allowed(root))

    def test_verify_lock_requires_config_manifest_and_lock_version_consistency(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".project").mkdir()
            (root / "managed.txt").write_text("ok\n", encoding="utf-8")
            (root / ".project/framework.manifest.json").write_text(
                json.dumps({"frameworkVersion": "1.3.9", "managed": ["managed.txt"]}), encoding="utf-8"
            )
            (root / ".project/project.config.json").write_text(
                json.dumps({"frameworkVersion": "1.3.8", "project": {"key": "consumer"}}), encoding="utf-8"
            )
            (root / ".project/framework.lock.json").write_text(
                json.dumps({
                    "digestMode": "sha256-normalized-text-v1",
                    "frameworkVersion": "1.3.9",
                    "files": {"managed.txt": digest(root / "managed.txt")},
                }),
                encoding="utf-8",
            )
            ok, result = verify_lock(root)
            self.assertFalse(ok)
            self.assertEqual(result["configVersion"], "1.3.8")
            self.assertEqual(result["frameworkVersion"], "1.3.9")


if __name__ == "__main__":
    unittest.main()
