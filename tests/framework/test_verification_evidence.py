from __future__ import annotations

import unittest

from tools.framework.verification_evidence import evaluate


class VerificationEvidenceTests(unittest.TestCase):
    def test_repository_ci_does_not_imply_runtime_acceptance(self):
        result = evaluate({
            "verificationEvidence": [
                {
                    "id": "ci",
                    "class": "repository/ci",
                    "status": "passed",
                    "releasePolicy": "required-pass",
                    "verifiedAt": "2026-08-29T20:30:00+00:00",
                },
                {
                    "id": "runtime",
                    "class": "runtime-readonly",
                    "status": "pending",
                    "releasePolicy": "informational",
                },
            ]
        })
        self.assertTrue(result["ok"])
        by_id = {item["id"]: item for item in result["evidence"]}
        self.assertEqual(by_id["ci"]["status"], "passed")
        self.assertEqual(by_id["runtime"]["status"], "pending")

    def test_required_pass_blocks_release_while_pending(self):
        result = evaluate({
            "verificationEvidence": [
                {
                    "id": "ci",
                    "class": "repository/ci",
                    "status": "pending",
                    "releasePolicy": "required-pass",
                }
            ]
        }, release=True)
        self.assertFalse(result["ok"])
        self.assertFalse(result["releaseReady"])
        self.assertIn("required-pass", result["releaseBlockers"][0])

    def test_allow_deferred_is_explicitly_releaseable(self):
        result = evaluate({
            "verificationEvidence": [
                {
                    "id": "ci",
                    "class": "repository/ci",
                    "status": "passed",
                    "releasePolicy": "required-pass",
                    "verifiedAt": "2026-08-29T20:30:00+00:00",
                },
                {
                    "id": "hardware",
                    "class": "deployment/hardware",
                    "status": "deferred",
                    "releasePolicy": "allow-deferred",
                    "detail": "Hardware acceptance is intentionally deferred.",
                },
            ]
        }, release=True)
        self.assertTrue(result["ok"])
        self.assertTrue(result["releaseReady"])

    def test_deferred_requires_visible_reason(self):
        result = evaluate({
            "verificationEvidence": [
                {
                    "id": "ci",
                    "class": "repository/ci",
                    "status": "passed",
                    "releasePolicy": "required-pass",
                    "verifiedAt": "2026-08-29T20:30:00+00:00",
                },
                {
                    "id": "smoke",
                    "class": "runtime-write-smoke",
                    "status": "deferred",
                    "releasePolicy": "allow-deferred",
                },
            ]
        })
        self.assertFalse(result["ok"])
        self.assertTrue(any("detail fehlt" in error for error in result["errors"]))

    def test_unknown_class_is_rejected(self):
        result = evaluate({
            "verificationEvidence": [
                {
                    "id": "ci",
                    "class": "all-green",
                    "status": "passed",
                    "releasePolicy": "required-pass",
                    "verifiedAt": "2026-08-29T20:30:00+00:00",
                }
            ]
        })
        self.assertFalse(result["ok"])
        self.assertTrue(any("class ist ungültig" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
