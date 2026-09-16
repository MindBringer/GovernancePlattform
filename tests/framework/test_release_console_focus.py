from __future__ import annotations

import unittest
from pathlib import Path


class ReleaseConsoleFocusTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.source = root.joinpath("tools/companion/web/input-actions.js").read_text(encoding="utf-8")

    def _run_release_block(self) -> str:
        return self.source.split("async function runRelease()", 1)[1].split("async function resumeReleaseMonitor()", 1)[0]

    def test_full_release_opens_console_before_confirmation_and_button_lock(self):
        block = self._run_release_block()
        show_index = block.index("const output = showConsole();")
        prompt_index = block.index("window.prompt")
        disable_index = block.index("setButtonsDisabled(true)")
        self.assertLess(show_index, prompt_index)
        self.assertLess(show_index, disable_index)
        self.assertIn("await nextPaint();", block)

    def test_cancelled_release_stays_in_console_without_starting_job(self):
        block = self._run_release_block()
        self.assertIn("Release nicht gestartet: Freigabe wurde abgebrochen.", block)
        cancel_index = block.index("if (!confirmation)")
        fetch_index = block.index("fetch('/api/action/release'")
        self.assertLess(cancel_index, fetch_index)

    def test_refresh_monitor_opens_console_before_disabling_navigation(self):
        block = self.source.split("async function resumeReleaseMonitor()", 1)[1]
        show_index = block.index("const output = showConsole();")
        disable_index = block.index("setButtonsDisabled(true)")
        self.assertLess(show_index, disable_index)


if __name__ == "__main__":
    unittest.main()
