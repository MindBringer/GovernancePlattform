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
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
CANVAS = Path("powerplatform/canvas/GovernancePortal")
ARTIFACT = Path("powerplatform/solution/CanvasApps/gp_governanceportal_c93a1_DocumentUri.msapp")
APP_METADATA = Path("powerplatform/solution/CanvasApps/gp_governanceportal_c93a1.meta.xml")


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


def change_required_fields(root: Path) -> set[str]:
    """Read permanent requirements from architecture, including omitted fields."""
    base = json.loads((root / "architecture/fields.yaml").read_text())["fields"]
    specific = json.loads((root / "architecture/object-fields.yaml").read_text())["objectFields"]
    fields = {field["internalName"]: field for field in base if field.get("scope") == "base"}
    fields.update({field["internalName"]: field for field in specific
                   if field.get("objectTypeKey") == "Change"})
    return {name for name, field in fields.items() if field.get("required") is True}


def validate_change_required(sources: list[dict], expected: set[str]) -> list[str]:
    """A writable cached connector can still reject an incomplete Draft."""
    matches = [source for source in sources if source.get("Name") == "Changes"]
    if len(matches) != 1:
        return ["Changes: expected one native data source for required-field validation"]
    source = matches[0]
    raw = source.get("DataEntityMetadataJson", {}).get(source.get("TableName"))
    if raw is None:
        return ["Changes: missing bound-table metadata for required-field validation"]
    metadata = json.loads(raw) if isinstance(raw, str) else raw
    required = metadata.get("schema", {}).get("items", {}).get("required")
    if (not isinstance(required, list) or any(not isinstance(field, str) for field in required)
            or len(required) != len(set(required))):
        return ["Changes: missing, malformed or duplicate connector required-field declaration"]
    if set(required) != expected:
        return ["Changes: cached connector required-field drift: "
                f"unexpected={sorted(set(required) - expected)}, "
                f"missing={sorted(expected - set(required))}; incomplete Draft is blocked"]
    return []


def change_datetime_fields(root: Path) -> set[str]:
    """Explicit instants require generated date-time metadata, never a date."""
    fields = json.loads((root / "architecture/object-fields.yaml").read_text())["objectFields"]
    return {field["internalName"] for field in fields
            if field.get("objectTypeKey") == "Change"
            and field.get("type") == "DateTime" and field.get("dateFormat") == "DateTime"}


def validate_change_datetime(sources: list[dict], expected: set[str]) -> list[str]:
    if not expected:
        return []
    matches = [source for source in sources if source.get("Name") == "Changes"]
    if len(matches) != 1:
        return ["Changes: expected one native data source for date-time validation"]
    source = matches[0]
    raw = source.get("DataEntityMetadataJson", {}).get(source.get("TableName"))
    if raw is None:
        return ["Changes: missing bound-table metadata for date-time validation"]
    metadata = json.loads(raw) if isinstance(raw, str) else raw
    properties = metadata.get("schema", {}).get("items", {}).get("properties", {})
    errors = []
    for name in sorted(expected):
        prop = properties.get(name)
        if not isinstance(prop, dict) or prop.get("type") != "string" or prop.get("format") != "date-time":
            errors.append(f"Changes.{name}: connector must declare string/date-time; "
                          "date-only or missing timestamp precision blocks approval")
    return errors


def read_connections(path: Path) -> dict:
    with ZipFile(path) as archive:
        entries = {name.replace("\\", "/"): name for name in archive.namelist()}
        candidates = [name for name in entries if name in (
            "Properties.json", "msapp/Properties.json")]
        if len(candidates) != 1:
            raise ValueError("Expected one Canvas properties entry")
        raw = json.loads(archive.read(entries[candidates[0]]))["LocalConnectionReferences"]
        return json.loads(raw) if isinstance(raw, str) else raw


def validate_connections(sources: list[dict], local: dict, solution: dict) -> list[str]:
    """Check both registrations; writable msapp metadata alone is insufficient."""
    errors = []
    if local.keys() != solution.keys():
        errors.append("Solution connection identities differ from Canvas references")
    registered = []
    for key, connection in local.items():
        native = solution.get(key, {})
        names = connection.get("dataSources", [])
        registered.extend(names)
        if len(names) != len(set(names)):
            errors.append("Duplicate Canvas source registration")
        if native.get("id") != connection.get("connectionRef", {}).get("id"):
            errors.append("Solution connector API differs from Canvas references")
        declared = native.get("dataSources", [])
        for name in sorted(set(names) - set(declared)):
            errors.append(f"{name}: missing Solution source registration")
        if set(declared) - set(names) or len(declared) != len(set(declared)):
            errors.append("Unexpected or duplicate Solution source registration")
        datasets = connection.get("datasets", {})
        if datasets != native.get("dataSets", {}):
            errors.append("Solution dataset/table bindings differ from Canvas references")
        for name in names:
            matches = [source for source in sources if source.get("Name") == name]
            if len(matches) != 1:
                errors.append(f"{name}: expected one registered Canvas data source")
                continue
            source = matches[0]
            if source.get("ApiId") != connection.get("connectionRef", {}).get("id"):
                errors.append(f"{name}: Canvas source uses a different connector API")
            if source.get("DatasetName"):
                # Existing generated sources can use dataset aliases. Preserve
                # their complete dataset/override maps above and resolve the
                # unique registered source name within this connection.
                bindings = [dataset.get("dataSources", {}).get(name)
                            for dataset in datasets.values()
                            if name in dataset.get("dataSources", {})]
                if len(bindings) != 1 or bindings[0].get("tableName") != source.get("TableName"):
                    errors.append(f"{name}: Canvas dataset does not bind its native table")
    connected = [source["Name"] for source in sources if source.get("ApiId") and not source.get("IsSampleData")]
    if set(registered) != set(connected) or len(registered) != len(set(registered)):
        errors.append("Connected Canvas sources and registrations differ")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--artifact", type=Path, default=ARTIFACT)
    parser.add_argument("--solution-metadata", type=Path, default=APP_METADATA)
    args = parser.parse_args()
    root = args.root.resolve()
    source = (root / CANVAS / "Src/scrShell.pa.yaml").read_text(encoding="utf-8-sig")
    contracts = patch_fields(source)
    references = list((root / CANVAS).glob("*.msapr"))
    if len(references) != 1:
        raise ValueError("Expected one canonical generated reference package")
    paths = [references[0], root / args.artifact]
    raw = ElementTree.parse(root / args.solution_metadata).getroot().findtext("ConnectionReferences")
    solution_connections = json.loads(raw)
    failed = False
    for path in paths:
        sources = read_sources(path)
        errors = validate(sources, contracts)
        if "Changes" in contracts:
            errors += validate_change_required(sources, change_required_fields(root))
            errors += validate_change_datetime(sources, change_datetime_fields(root))
        errors += validate_connections(sources, read_connections(path), solution_connections)
        for error in errors:
            print(f"{path.name}: {error}")
        failed |= bool(errors)
    if failed:
        print("Write contract blocked. Inspect native schema and Solution registrations; preserve generated bindings and use the approved workflow for any native refresh.")
        return 1
    print(f"Canvas write contract passed: {sum(map(len, contracts.values()))} Patch fields, Change permanent requirements/date-time precision and complete Solution source/dataset registrations in canonical and packed connector references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
