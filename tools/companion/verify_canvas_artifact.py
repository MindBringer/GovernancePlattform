#!/usr/bin/env python3
"""Check that the tracked msapp embeds the canonical Canvas YAML sources."""

import json
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "powerplatform/canvas/GovernancePortal/Src"
ARTIFACT = ROOT / "powerplatform/solution/CanvasApps/gp_governanceportal_c93a1_DocumentUri.msapp"


def normalized(data: bytes) -> str:
    return data.decode("utf-8-sig").replace("\r\n", "\n")


def main() -> int:
    if not ARTIFACT.is_file():
        print(f"Canvas artifact is missing: {ARTIFACT.relative_to(ROOT)}")
        return 1

    expected = {f"Src/{path.relative_to(SOURCE).as_posix()}": path for path in SOURCE.rglob("*.pa.yaml")}
    with ZipFile(ARTIFACT) as archive:
        embedded = {
            name.replace("\\", "/"): name
            for name in archive.namelist()
            if name.replace("\\", "/").startswith("Src/") and name.endswith(".pa.yaml")
        }
        missing = sorted(expected.keys() - embedded.keys())
        extra = sorted(embedded.keys() - expected.keys())
        stale = sorted(
            name for name in expected.keys() & embedded.keys()
            if normalized(expected[name].read_bytes()) != normalized(archive.read(embedded[name]))
        )
        diagnostic_references = sorted(
            name for name in archive.namelist()
            if b"lblEnvironment_1" in archive.read(name)
        )
        checker = json.loads(archive.read("AppCheckerResult.sarif"))
        literal_warnings = [
            result for run in checker.get("runs", []) for result in run.get("results", [])
            if result.get("ruleId") == "app-WarnLiteralPredicate"
        ]

    for label, names in (("Missing", missing), ("Unexpected", extra), ("Stale", stale)):
        for name in names:
            print(f"{label} Canvas source in msapp: {name}")
    for name in diagnostic_references:
        print(f"Diagnostic control remains in msapp: {name}")
    if literal_warnings:
        print(f"Stale literal-predicate warnings remain in msapp: {len(literal_warnings)}")
    if missing or extra or stale or diagnostic_references or literal_warnings:
        return 1
    print(f"Canvas artifact source matches {len(expected)} canonical YAML files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
