from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class CompanionUXTests(unittest.TestCase):
    def test_release_selection_switches_console_before_confirmation(self):
        source = (ROOT / "tools/companion/web/input-actions.js").read_text(encoding="utf-8")
        run_release = source[source.index("async function runRelease()") : source.index("async function resumeReleaseMonitor()")]
        self.assertLess(run_release.index("const output = showConsole()"), run_release.index("window.prompt"))
        self.assertLess(run_release.index("await nextPaint()"), run_release.index("window.prompt"))
        self.assertIn("progress.label", source)
        self.assertIn("progress.detail", source)

    def test_all_registered_actions_use_structured_console_result_layer(self):
        source = (ROOT / "tools/companion/web/input-actions.js").read_text(encoding="utf-8")
        self.assertIn("function renderResult(data, output", source)
        self.assertIn("data?.summary", source)
        self.assertIn("data?.failureBlock", source)
        self.assertIn("data?.detailLog", source)
        self.assertIn("event.stopImmediatePropagation()", source)
        self.assertIn("void runRegisteredAction(actionSpec(button.dataset.action))", source)
        self.assertIn("window.ProjectCompanion.runAction = id => runRegisteredAction(actionSpec(id))", source)

    def test_console_keeps_full_detail_log_separate_from_compact_result(self):
        index = (ROOT / "tools/companion/web/index.html").read_text(encoding="utf-8")
        self.assertIn('id="output"', index)
        self.assertIn('id="consoleDetailPanel"', index)
        self.assertIn('id="outputDetails"', index)
        self.assertIn("Vollständiges Detail-Log", index)
        self.assertIn("Root Cause", index)

    def test_verification_evidence_is_rendered_as_separate_classes(self):
        index = (ROOT / "tools/companion/web/index.html").read_text(encoding="utf-8")
        source = (ROOT / "tools/companion/web/verification-evidence.js").read_text(encoding="utf-8")
        self.assertIn('id="verificationEvidenceCard"', index)
        self.assertIn('id="verificationEvidenceList"', index)
        self.assertIn("Repository-/CI-Erfolg ist kein Ersatz", index)
        for evidence_class in (
            "repository/ci",
            "runtime-readonly",
            "runtime-write-smoke",
            "deployment/hardware",
            "operator-waiver/deferred",
        ):
            self.assertIn(evidence_class, source)
        self.assertIn("releasePolicy", source)
        self.assertIn("verification-evidence.js", index)

    def test_companion_has_persisted_dark_mode_and_system_fallback(self):
        app = (ROOT / "tools/companion/web/app.js").read_text(encoding="utf-8")
        styles = (ROOT / "tools/companion/web/styles.css").read_text(encoding="utf-8")
        index = (ROOT / "tools/companion/web/index.html").read_text(encoding="utf-8")
        self.assertIn("companion-theme", app)
        self.assertIn("prefers-color-scheme: dark", app)
        self.assertIn(':root[data-theme="dark"]', styles)
        self.assertIn("@media (prefers-color-scheme: dark)", styles)
        self.assertIn('id="themeToggle"', index)

    def test_inline_guidance_explains_primary_views_and_metrics(self):
        app = (ROOT / "tools/companion/web/app.js").read_text(encoding="utf-8")
        index = (ROOT / "tools/companion/web/index.html").read_text(encoding="utf-8")
        for label in ("Dashboard", "Entwicklung", "Konsole"):
            self.assertIn(label, index + app)
        self.assertIn('id="pageDescription"', index)
        self.assertIn("Orientierung: Was zeigt der Companion?", index)
        self.assertIn("statusHelp", app)
        self.assertIn("a.description", app)


if __name__ == "__main__":
    unittest.main()
