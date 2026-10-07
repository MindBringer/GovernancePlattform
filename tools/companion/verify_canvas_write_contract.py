#!/usr/bin/env python3
"""Reject Patch fields that the canonical or packed connector cannot write.

Read-only validation: never modify connector permissions or infer them from the
architecture. A new architecture field still needs a native field and a generated
connector reference before this deployment gate can pass.
"""

import argparse
import json
import re
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
CANVAS = Path("powerplatform/canvas/GovernancePortal")
ARTIFACT = Path("powerplatform/solution/CanvasApps/gp_governanceportal_c93a1_DocumentUri.msapp")


def patch_fields(source: str) -> dict[str, list[str]]:
    contracts = {}
    for match in re.finditer(r"\bPatch\(\s*(Assets|Systems|Changes)\s*,", source):
        name = match[1]
        start = source.index("{", match.end())
        depth = 0
        quoted = False
        pos = start
        while pos < len(source):
            ch = source[pos]
            if ch == '"':
                if quoted and source[pos:pos + 2] == '""':
                    pos += 2
                    continue
                quoted = not quoted
            if not quoted:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        break
            pos += 1
        if depth:
            raise ValueError(f"Unbalanced {name} Patch payload")
        lines = re.findall(r"(?m)^( +)(\w+):", source[start + 1:pos])
        if not lines:
            raise ValueError(f"Missing {name} Patch fields")
        indent = min(len(spaces) for spaces, _ in lines)
        fields = [key for spaces, key in lines if len(spaces) == indent]
        if name in contracts:
            raise ValueError(f"Ambiguous {name} Patch contract")
        contracts[name] = fields
    if not {"Assets", "Systems"}.issubset(contracts):
        raise ValueError("Required native Asset/System Patch providers are missing")
    return contracts


def read_sources(path: Path) -> list[dict]:
    with ZipFile(path) as archive:
        entries = {name.replace("\\", "/"): name for name in archive.namelist()}
        candidates = [name for name in entries if name in (
            "References/DataSources.json", "msapp/References/DataSources.json")]
        if len(candidates) != 1:
            raise ValueError("Expected one connector reference entry")
        return json.loads(archive.read(entries[candidates[0]]))["DataSources"]


def validate(sources: list[dict], contracts: dict[str, list[str]]) -> list[str]:
    errors = []
    for name, fields in contracts.items():
        matches = [source for source in sources if source.get("Name") == name]
        if len(matches) != 1:
            errors.append(f"{name}: expected one native data source")
            continue
        source = matches[0]
        if source.get("IsWritable") is not True:
            errors.append(f"{name}: connector is not writable")
        raw = source.get("DataEntityMetadataJson", {}).get(source.get("TableName"))
        if raw is None:
            errors.append(f"{name}: missing metadata for the bound native table")
            continue
        metadata = json.loads(raw) if isinstance(raw, str) else raw
        properties = metadata.get("schema", {}).get("items", {}).get("properties", {})
        for field in fields:
            prop = properties.get(field)
            if prop is None:
                errors.append(f"{name}.{field}: missing generated connector field")
            elif prop.get("x-ms-permission") != "read-write":
                errors.append(f"{name}.{field}: connector permission {prop.get('x-ms-permission', 'missing')}, expected read-write")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--artifact", type=Path, default=ARTIFACT)
    args = parser.parse_args()
    root = args.root.resolve()
    source = (root / CANVAS / "Src/scrShell.pa.yaml").read_text(encoding="utf-8-sig")
    contracts = patch_fields(source)
    references = list((root / CANVAS).glob("*.msapr"))
    if len(references) != 1:
        raise ValueError("Expected one canonical generated reference package")
    paths = [references[0], root / args.artifact]
    failed = False
    for path in paths:
        errors = validate(read_sources(path), contracts)
        for error in errors:
            print(f"{path.name}: {error}")
        failed |= bool(errors)
    if failed:
        print("Write contract blocked. Inspect native schema, then refresh the generated canonical reference through the approved DEV workflow; do not override permissions.")
        return 1
    print(f"Canvas write contract passed: {sum(map(len, contracts.values()))} Patch fields in canonical and packed connector references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
