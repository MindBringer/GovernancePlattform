from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class CiRunnerStrategyTests(unittest.TestCase):
    def test_required_engineering_contract_uses_self_hosted_local_ci(self):
        workflow = (ROOT / ".github/workflows/framework-validate.yml").read_text(encoding="utf-8")
        self.assertIn("name: Local CI · required", workflow)
        self.assertIn("runs-on: [self-hosted, local-ci]", workflow)
        self.assertIn("cancel-in-progress: true", workflow)
        self.assertIn("pull_request:", workflow)
        self.assertIn("branches: [ main ]", workflow)
        self.assertNotIn("ubuntu-latest", workflow)
        self.assertNotIn("macos-latest", workflow)
        self.assertNotIn("windows-latest", workflow)

    def test_self_hosted_ci_uses_runner_provided_python(self):
        workflow = (ROOT / ".github/workflows/framework-validate.yml").read_text(encoding="utf-8")
        self.assertNotIn("actions/setup-python", workflow)
        self.assertIn("command -v python3", workflow)
        self.assertIn("python3 --version", workflow)
        self.assertIn("sys.version_info >= (3, 12)", workflow)
        self.assertIn("python3 tools/framework/audit_repo.py", workflow)

    def test_self_hosted_checkout_is_explicitly_clean_and_does_not_persist_github_credentials(self):
        workflow = (ROOT / ".github/workflows/framework-validate.yml").read_text(encoding="utf-8")
        self.assertIn("uses: actions/checkout@v4", workflow)
        self.assertIn("clean: true", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("name: Self-hosted CI hermeticity", workflow)
        self.assertIn("python3 tools/framework/ci_hermeticity.py", workflow)
        self.assertLess(
            workflow.index("Self-hosted CI hermeticity"),
            workflow.index("Repository audit"),
        )

    def test_hosted_compatibility_matrix_is_manual_only(self):
        workflow = (ROOT / ".github/workflows/framework-hosted-matrix.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("ubuntu-latest", workflow)
        self.assertIn("macos-latest", workflow)
        self.assertIn("windows-latest", workflow)
        trigger_prefix = workflow.split("jobs:", 1)[0]
        self.assertNotIn("pull_request:", trigger_prefix)
        self.assertNotIn("push:", trigger_prefix)

    def test_self_hosted_ci_runbook_documents_runner_label_and_offline_behavior(self):
        runbook = (ROOT / "docs/runbooks/Self-Hosted-CI.md").read_text(encoding="utf-8")
        self.assertIn("local-ci", runbook)
        self.assertIn("Queued", runbook)
        self.assertIn("Hosted Compatibility Matrix", runbook)
        self.assertIn("keinen", runbook)
        self.assertIn("Hosted fehlgeschlagen", runbook)
        self.assertIn("Python >= 3.12", runbook)
        self.assertIn("setup-python", runbook)
        self.assertIn("ci_hermeticity.py", runbook)
        self.assertIn("persist-credentials: false", runbook)
        self.assertIn("ENGINEERING_CI_ALLOWED_ENV", runbook)


if __name__ == "__main__":
    unittest.main()
