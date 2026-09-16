#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EVIDENCE_CLASSES = {
    "repository/ci",
    "runtime-readonly",
    "runtime-write-smoke",
    "deployment/hardware",
    "operator-waiver/deferred",
}
EVIDENCE_STATUSES = {
    "passed",
    "failed",
    "pending",
    "deferred",
    "waived",
    "not-applicable",
}
RELEASE_POLICIES = {
    "required-pass",
    "allow-deferred",
    "informational",
}


def _state(root: Path) -> dict[str, object]:
    path = root / ".project" / "state" / "current.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("current.json muss ein JSON-Objekt sein")
    return payload


def evaluate(state: dict[str, object], *, release: bool = False) -> dict[str, object]:
    raw = state.get("verificationEvidence", [])
    errors: list[str] = []
    blockers: list[str] = []
    normalized: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    class_counts = {key: 0 for key in sorted(EVIDENCE_CLASSES)}

    if not isinstance(raw, list):
        return {
            "ok": False,
            "releaseReady": False,
            "errors": ["verificationEvidence muss eine Liste sein"],
            "releaseBlockers": [],
            "evidence": [],
            "classCounts": class_counts,
        }

    for index, item in enumerate(raw):
        prefix = f"verificationEvidence[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} muss ein Objekt sein")
            continue

        evidence_id = str(item.get("id") or "").strip()
        evidence_class = str(item.get("class") or "").strip()
        status = str(item.get("status") or "").strip()
        policy = str(item.get("releasePolicy") or "").strip()
        detail = str(item.get("detail") or "").strip()
        verified_at = str(item.get("verifiedAt") or "").strip()

        if not evidence_id:
            errors.append(f"{prefix}.id fehlt")
        elif evidence_id in seen_ids:
            errors.append(f"Doppelte Evidence-ID: {evidence_id}")
        else:
            seen_ids.add(evidence_id)

        if evidence_class not in EVIDENCE_CLASSES:
            errors.append(f"{prefix}.class ist ungültig: {evidence_class or '<leer>'}")
        else:
            class_counts[evidence_class] += 1
        if status not in EVIDENCE_STATUSES:
            errors.append(f"{prefix}.status ist ungültig: {status or '<leer>'}")
        if policy not in RELEASE_POLICIES:
            errors.append(f"{prefix}.releasePolicy ist ungültig: {policy or '<leer>'}")
        if status == "passed" and not verified_at:
            errors.append(f"{prefix}.verifiedAt fehlt bei status=passed")
        if status in {"deferred", "waived", "not-applicable"} and not detail:
            errors.append(f"{prefix}.detail fehlt bei status={status}")

        if release and status in EVIDENCE_STATUSES and policy in RELEASE_POLICIES:
            if policy == "required-pass" and status != "passed":
                blockers.append(f"{evidence_id or prefix}: required-pass erfordert passed, aktuell {status}")
            elif policy == "allow-deferred" and status not in {"passed", "deferred", "waived", "not-applicable"}:
                blockers.append(f"{evidence_id or prefix}: allow-deferred erlaubt aktuellen Status {status} nicht")

        normalized.append({
            "id": evidence_id,
            "class": evidence_class,
            "status": status,
            "releasePolicy": policy,
            "detail": detail,
            "verifiedAt": verified_at or None,
        })

    if raw and class_counts["repository/ci"] == 0:
        errors.append("verificationEvidence benötigt mindestens eine repository/ci-Evidenz")

    release_ready = not errors and not blockers
    return {
        "ok": not errors and (not release or not blockers),
        "releaseReady": release_ready,
        "errors": errors,
        "releaseBlockers": blockers,
        "evidence": normalized,
        "classCounts": class_counts,
    }


def contract(root: Path = ROOT, *, release: bool = False) -> dict[str, object]:
    try:
        state = _state(root.resolve())
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {
            "ok": False,
            "releaseReady": False,
            "errors": [f"Project State nicht lesbar: {exc}"],
            "releaseBlockers": [],
            "evidence": [],
            "classCounts": {key: 0 for key in sorted(EVIDENCE_CLASSES)},
        }
    return evaluate(state, release=release)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verification Evidence Contract")
    parser.add_argument("--release", action="store_true", help="Release-Readiness gemäß releasePolicy prüfen")
    args = parser.parse_args()
    result = contract(ROOT, release=args.release)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
