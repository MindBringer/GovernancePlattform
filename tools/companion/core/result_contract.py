from __future__ import annotations

import re
from typing import Sequence


ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
UNITTEST_HEADER_RE = re.compile(r"^(FAIL|ERROR):\s+(.+?)\s*$", re.MULTILINE)
UNITTEST_RAN_RE = re.compile(r"Ran\s+(\d+)\s+tests?\s+in\s+([0-9.]+)s")
UNITTEST_FAILED_RE = re.compile(r"FAILED\s*\(([^)]*)\)")
EXCEPTION_RE = re.compile(r"^(?:[A-Za-z_][\w.]*)(?:Error|Exception):\s*.+$", re.MULTILINE)


def strip_ansi(value: str) -> str:
    return ANSI_RE.sub("", value or "")


def _meaningful_lines(value: str) -> list[str]:
    return [line.rstrip() for line in strip_ansi(value).splitlines() if line.strip()]


def _command_text(command: Sequence[str] | str) -> str:
    if isinstance(command, str):
        return command
    return " ".join(str(part) for part in command)


def _is_unittest(command: Sequence[str] | str) -> bool:
    text = _command_text(command)
    return " -m unittest " in f" {text} " or " unittest discover " in f" {text} "


def _unittest_details(output: str) -> dict[str, object]:
    clean = strip_ansi(output)
    failures = [name.strip() for _, name in UNITTEST_HEADER_RE.findall(clean)]
    ran = UNITTEST_RAN_RE.search(clean)
    failed_summary = UNITTEST_FAILED_RE.search(clean)
    exception_lines = EXCEPTION_RE.findall(clean)
    details: dict[str, object] = {
        "failedTests": failures,
    }
    if ran:
        details["tests"] = int(ran.group(1))
        details["durationSeconds"] = float(ran.group(2))
    if failed_summary:
        details["failedSummary"] = failed_summary.group(1).strip()
    if exception_lines:
        details["assertion"] = exception_lines[-1].strip()
    return details


def _root_cause(output: str, *, unittest: bool) -> str:
    clean = strip_ansi(output)
    exception_lines = EXCEPTION_RE.findall(clean)
    if exception_lines:
        return exception_lines[-1].strip()

    lines = _meaningful_lines(clean)
    if not lines:
        return "Keine weitere Fehlerausgabe vorhanden."

    ignored_prefixes = (
        "Ran ",
        "FAILED (",
        "Process completed with exit code",
        "Error: Process completed with exit code",
    )
    candidates = [line for line in lines if not line.startswith(ignored_prefixes)]
    if unittest:
        candidates = [
            line for line in candidates
            if not line.startswith(("FAIL: ", "ERROR: ", "Traceback (most recent call last):"))
        ]
    selected = candidates[-3:] if candidates else lines[-3:]
    return " | ".join(selected)


def _next_step(
    *,
    gate: str | None,
    failed_tests: list[str],
    worktree_mutation: list[str],
) -> str:
    if worktree_mutation:
        shown = ", ".join(worktree_mutation)
        return (
            f"Die Mutation durch {gate or 'die Aktion'} in {shown} beseitigen oder die Aktion "
            "explizit als mutierend aus dem Required-/Release-Gate herausnehmen; danach denselben Gate erneut ausführen."
        )
    if failed_tests:
        return f"Zuerst den fehlgeschlagenen Test `{failed_tests[0]}` beheben und denselben Gate erneut ausführen."
    if gate:
        return f"Root Cause im Detail-Log von `{gate}` beheben und exakt denselben Gate erneut ausführen."
    return "Root Cause im vollständigen Detail-Log beheben und denselben Command erneut ausführen."


def build_result_contract(
    *,
    command: Sequence[str] | str,
    exit_code: int,
    detail_log: str,
    gate: str | None = None,
    worktree_mutation: list[str] | None = None,
) -> dict[str, object]:
    command_text = _command_text(command)
    ok = exit_code == 0
    mutation = list(worktree_mutation or [])
    unittest = _is_unittest(command)
    unittest_details = _unittest_details(detail_log) if unittest else {"failedTests": []}
    failed_tests = list(unittest_details.get("failedTests") or [])

    if ok:
        tests = unittest_details.get("tests")
        if isinstance(tests, int):
            summary = f"OK · Exit 0 · {tests} Tests"
        else:
            summary = "OK · Exit 0"
        return {
            "ok": True,
            "exitCode": 0,
            "command": command_text,
            "gate": gate,
            "summary": summary,
            "detailLog": detail_log,
            "failure": None,
            "failureBlock": "",
        }

    root_cause = _root_cause(detail_log, unittest=unittest)
    failure: dict[str, object] = {
        "gate": gate,
        "command": command_text,
        "exitCode": exit_code,
        "failedTests": failed_tests,
        "rootCause": root_cause,
        "nextStep": _next_step(
            gate=gate,
            failed_tests=failed_tests,
            worktree_mutation=mutation,
        ),
    }
    for key in ("tests", "durationSeconds", "failedSummary", "assertion"):
        if key in unittest_details:
            failure[key] = unittest_details[key]
    if mutation:
        failure["worktreeMutation"] = mutation

    lines = [
        "FEHLERBLOCK",
        f"Gate/Aktion: {gate or '-'}",
        f"Command: {command_text or '-'}",
        f"Exit-Code: {exit_code}",
    ]
    if failed_tests:
        lines.append("Fehlgeschlagene Tests: " + ", ".join(failed_tests))
    if failure.get("assertion"):
        lines.append("Assertion: " + str(failure["assertion"]))
    if mutation:
        lines.append("Unerwartet geänderte Dateien: " + ", ".join(mutation))
    lines.extend([
        "Root Cause: " + root_cause,
        "Nächster Schritt: " + str(failure["nextStep"]),
    ])
    failure_block = "\n".join(lines)

    return {
        "ok": False,
        "exitCode": exit_code,
        "command": command_text,
        "gate": gate,
        "summary": f"FEHLER · Exit {exit_code}",
        "detailLog": detail_log,
        "failure": failure,
        "failureBlock": failure_block,
    }
