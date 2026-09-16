from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from tools.companion.core.actions import ActionRegistry, ActionSpec, INPUT_TOKEN


class ActionTests(unittest.TestCase):
    def test_duplicate_action_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = ActionRegistry(Path(tmp))
            registry.register(ActionSpec("x", "X", "Test", commands=[["python3", "--version"]]))
            with self.assertRaises(ValueError):
                registry.register(ActionSpec("x", "X2", "Test", commands=[["python3", "--version"]]))

    def test_confirmation_blocks_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = ActionRegistry(Path(tmp))
            registry.register(ActionSpec("danger", "Danger", "Test", commands=[["python3", "--version"]], confirmation="YES"))
            result = registry.execute("danger", "NO")
            self.assertFalse(result["ok"])
            self.assertEqual(result["exitCode"], 409)
            self.assertEqual(result["summary"], "FEHLER · Exit 409")
            self.assertIn("FEHLERBLOCK", result["failureBlock"])

    def test_command_executes_without_shell(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = ActionRegistry(Path(tmp))
            registry.register(ActionSpec("hello", "Hello", "Test", commands=[["python3", "-c", "print('ok')"]]))
            result = registry.execute("hello")
            self.assertTrue(result["ok"])
            self.assertIn("ok", result["output"])
            self.assertEqual(result["summary"], "OK · Exit 0")
            self.assertEqual(result["detailLog"], result["output"])
            self.assertIsNone(result["failure"])

    def test_failed_command_preserves_exit_code_detail_and_final_failure_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = ActionRegistry(Path(tmp))
            registry.register(ActionSpec(
                "fail",
                "Fail",
                "Test",
                commands=[[
                    sys.executable,
                    "-c",
                    "import sys; print('prefix'); print('ValueError: canonical cause'); sys.exit(7)",
                ]],
            ))

            result = registry.execute("fail")

            self.assertFalse(result["ok"])
            self.assertEqual(result["exitCode"], 7)
            self.assertEqual(result["summary"], "FEHLER · Exit 7")
            self.assertEqual(result["detailLog"], result["output"])
            self.assertIn("ValueError: canonical cause", result["detailLog"])
            self.assertIn("ValueError: canonical cause", result["failureBlock"])
            self.assertEqual(result["failure"]["gate"], "fail")
            self.assertEqual(result["failure"]["exitCode"], 7)

    def test_parameterized_action_substitutes_single_argument_without_shell_but_redacts_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = ActionRegistry(Path(tmp))
            registry.register(ActionSpec(
                "echo-input", "Echo", "Test",
                commands=[["python3", "-c", "import sys; print(sys.argv[1])", INPUT_TOKEN]],
                input_label="Token", input_required=True,
            ))
            result = registry.execute("echo-input", user_input="RESET|site|2.0")
            self.assertTrue(result["ok"])
            self.assertNotIn("RESET|site|2.0", result["output"])
            self.assertNotIn("RESET|site|2.0", result["command"])
            self.assertIn("<input>", result["output"])
            self.assertIn("<input>", result["command"])

    def test_required_parameter_blocks_empty_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = ActionRegistry(Path(tmp))
            registry.register(ActionSpec(
                "need-input", "Need", "Test",
                commands=[["python3", "-c", "print('x')", INPUT_TOKEN]],
                input_label="Wert", input_required=True,
            ))
            result = registry.execute("need-input", user_input="")
            self.assertFalse(result["ok"])
            self.assertEqual(result["exitCode"], 409)
            self.assertIn("Eingabe fehlt", result["failureBlock"])

    def test_input_token_requires_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = ActionRegistry(Path(tmp))
            with self.assertRaises(ValueError):
                registry.register(ActionSpec("bad", "Bad", "Test", commands=[["echo", INPUT_TOKEN]]))


if __name__ == "__main__":
    unittest.main()
