#!/usr/bin/env python3
"""Parse Canvas YAML and known native regressions; this is not a full Studio schema check."""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode

ROOT = Path(__file__).resolve().parents[2]


def validate_text(text: str) -> None:
    # BaseLoader avoids YAML 1.1 coercion of Power Fx strings such as on/off.
    documents = list(yaml.compose_all(text, Loader=yaml.BaseLoader))
    if len(documents) != 1 or not isinstance(documents[0], MappingNode):
        raise ValueError("Expected one Canvas YAML mapping document")

    def fail(node: yaml.Node, message: str) -> None:
        mark = node.start_mark
        raise ValueError(f"line {mark.line + 1}, column {mark.column + 1}: {message}")

    def visit(node: yaml.Node) -> None:
        if isinstance(node, MappingNode):
            fields = {key.value: value for key, value in node.value if isinstance(key, ScalarNode)}
            control = fields.get("Control")
            properties = fields.get("Properties")
            # Native PA2108 on 30450: Classic buttons use Text for their
            # screenreader name; AccessibleLabel is not in this control schema.
            if (isinstance(control, ScalarNode)
                    and control.value.startswith("Classic/Button@")
                    and isinstance(properties, MappingNode)):
                for property_key, _ in properties.value:
                    if isinstance(property_key, ScalarNode) and property_key.value == "AccessibleLabel":
                        fail(property_key, "PA2108: Classic/Button does not support AccessibleLabel; use Text for its name")
            keys: set[str] = set()
            for key, value in node.value:
                if not isinstance(key, ScalarNode):
                    fail(key, "Canvas mapping key must be a scalar")
                if key.value in keys:
                    fail(key, f"Duplicate Canvas key: {key.value}")
                keys.add(key.value)
                if key.value == "Properties":
                    if not isinstance(value, MappingNode):
                        fail(value, "Properties must be a mapping")
                    for _, formula in value.value:
                        if not isinstance(formula, ScalarNode):
                            fail(formula, "Canvas property must be a scalar formula; use |- for colon-space")
                visit(value)
        elif isinstance(node, SequenceNode):
            for child in node.value:
                visit(child)

    visit(documents[0])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "powerplatform/canvas/GovernancePortal/Src")
    args = parser.parse_args()
    files = sorted(args.source.rglob("*.pa.yaml"))
    if not files:
        parser.error(f"No *.pa.yaml files in {args.source}")
    failures = 0
    for path in files:
        try:
            validate_text(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, ValueError) as error:
            failures += 1
            print(f"CANVAS-YAML: FAIL {path}: {error}")
    if failures:
        return 1
    print(f"CANVAS-YAML: OK; {len(files)} files parsed; property scalar and duplicate-key checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
