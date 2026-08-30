#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.companion.core.config import load_config
from tools.companion.core.process import run_command


def main() -> int:
    config = load_config(ROOT)
    policy = config.data.get("repositoryPolicy", {}) if isinstance(config.data.get("repositoryPolicy"), dict) else {}
    base = str(config.data.get("release", {}).get("baseBranch") or "main")
    require_protected = bool(policy.get("requireProtectedBaseBranch", False))

    repo = run_command(ROOT, ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"], 60)
    if not repo.ok or not repo.output.strip():
        print(json.dumps({"ok": False, "error": "GitHub Repository konnte nicht bestimmt werden."}, ensure_ascii=False, indent=2))
        return 1
    name = repo.output.strip()
    branch = run_command(ROOT, ["gh", "api", f"repos/{name}/branches/{base}", "--jq", ".protected"], 60)
    if not branch.ok:
        print(json.dumps({"ok": False, "repository": name, "baseBranch": base, "error": branch.output}, ensure_ascii=False, indent=2))
        return 1
    protected = branch.output.strip().lower() == "true"
    ok = protected or not require_protected
    result = {
        "ok": ok,
        "repository": name,
        "baseBranch": base,
        "protected": protected,
        "required": require_protected,
        "recommendation": None if protected else "Branch Protection oder Repository Ruleset für den Base Branch aktivieren; Engineering Contract als Required Check verwenden.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
