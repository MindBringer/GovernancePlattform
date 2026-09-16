from __future__ import annotations

import unittest

from tools.companion.core.result_contract import build_result_contract


class ResultContractTests(unittest.TestCase):
    def test_unittest_failure_extracts_test_assertion_and_root_cause(self):
        output = """
FAIL: test_release_gate (tests.test_release.ReleaseTests.test_release_gate)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/test_release.py", line 42, in test_release_gate
    self.assertEqual(actual, expected)
AssertionError: 'dirty' != 'clean'

Ran 12 tests in 0.123s

FAILED (failures=1)
""".strip()

        result = build_result_contract(
            command=["python3", "-m", "unittest", "discover"],
            exit_code=1,
            detail_log=output,
            gate="tests",
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["exitCode"], 1)
        failure = result["failure"]
        self.assertEqual(failure["tests"], 12)
        self.assertEqual(
            failure["failedTests"],
            ["test_release_gate (tests.test_release.ReleaseTests.test_release_gate)"],
        )
        self.assertIn("AssertionError", failure["assertion"])
        self.assertIn("AssertionError", failure["rootCause"])
        self.assertIn("FEHLERBLOCK", result["failureBlock"])
        self.assertIn("Exit-Code: 1", result["failureBlock"])

    def test_failure_block_survives_large_preceding_output(self):
        output = "\n".join([f"successful step {index}" for index in range(2000)])
        output += "\nRuntimeError: canonical root cause"

        result = build_result_contract(
            command="python3 scripts/quality_gate.py",
            exit_code=7,
            detail_log=output,
            gate="quality-gate",
        )

        self.assertEqual(result["summary"], "FEHLER · Exit 7")
        self.assertIn("canonical root cause", result["failure"]["rootCause"])
        self.assertIn("canonical root cause", result["failureBlock"])
        self.assertNotIn("successful step 0", result["failureBlock"])

    def test_ansi_sequences_are_removed_from_summary_fields(self):
        result = build_result_contract(
            command="tool",
            exit_code=2,
            detail_log="\x1b[31mValueError: bad value\x1b[0m",
            gate="doctor",
        )
        self.assertEqual(result["failure"]["rootCause"], "ValueError: bad value")
        self.assertNotIn("\x1b", result["failureBlock"])

    def test_worktree_mutation_gets_deterministic_next_step(self):
        result = build_result_contract(
            command="gate",
            exit_code=409,
            detail_log="mutation",
            gate="engineering-contract",
            worktree_mutation=[".project/state/current.json"],
        )
        self.assertEqual(
            result["failure"]["worktreeMutation"],
            [".project/state/current.json"],
        )
        self.assertIn("explizit als mutierend", result["failure"]["nextStep"])
        self.assertIn(".project/state/current.json", result["failureBlock"])

    def test_success_contract_is_compact_but_keeps_detail_log(self):
        detail = "line one\nline two"
        result = build_result_contract(
            command="python3 tool.py",
            exit_code=0,
            detail_log=detail,
            gate="tool",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["summary"], "OK · Exit 0")
        self.assertEqual(result["detailLog"], detail)
        self.assertIsNone(result["failure"])
        self.assertEqual(result["failureBlock"], "")


if __name__ == "__main__":
    unittest.main()
