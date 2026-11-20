#!/usr/bin/env python3
"""Check embedded Canvas sources and, for a Studio export, compiled screens."""

import argparse
import json
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "powerplatform/canvas/GovernancePortal/Src"
ARTIFACT = ROOT / "powerplatform/solution/CanvasApps/gp_governanceportal_c93a1_DocumentUri.msapp"


def normalized(data: bytes) -> str:
    return data.decode("utf-8-sig").replace("\r\n", "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, default=ARTIFACT)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--compiled-screens", action="store_true",
                        help="Require Studio-compiled screens for each screen in the source tree")
    args = parser.parse_args()
    if not args.artifact.is_file():
        print(f"Canvas artifact is missing: {args.artifact}")
        return 1

    expected = {
        f"Src/{path.relative_to(args.source).as_posix()}": path
        for path in args.source.rglob("*.pa.yaml")
    }
    if not expected:
        print(f"Canvas source files are missing: {args.source}")
        return 1

    missing_screens = []
    with ZipFile(args.artifact) as archive:
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
        if args.compiled_screens:
            import yaml

            expected_screens = {
                screen
                for source in expected.values()
                for screen in yaml.load(source.read_text(encoding="utf-8-sig"), Loader=yaml.BaseLoader).get("Screens", {})
            }
            compiled_screens = set()
            for name in archive.namelist():
                path = name.replace("\\", "/")
                if path.startswith("Controls/") and path.endswith(".json"):
                    control = json.loads(archive.read(name)).get("TopParent", {})
                    if control.get("Template", {}).get("Name") == "screen":
                        compiled_screens.add(control["Name"])
            missing_screens = sorted(expected_screens - compiled_screens)

    for label, names in (("Missing", missing), ("Unexpected", extra), ("Stale", stale)):
        for name in names:
            print(f"{label} Canvas source in msapp: {name}")
    for name in missing_screens:
        print(f"Screen missing from compiled Canvas runtime: {name}")
    for name in diagnostic_references:
        print(f"Diagnostic control remains in msapp: {name}")
    if literal_warnings:
        print(f"Stale literal-predicate warnings remain in msapp: {len(literal_warnings)}")
    if missing or extra or stale or missing_screens or diagnostic_references or literal_warnings:
        return 1
    print(f"Canvas artifact source matches {len(expected)} canonical YAML files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
