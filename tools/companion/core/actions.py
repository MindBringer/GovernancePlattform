from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from .process import run_command
from .result_contract import build_result_contract


INPUT_TOKEN = "{input}"
REDACTED_INPUT = "<input>"
ActionProgressReporter = Callable[[dict[str, object]], None]


def _tracked_worktree_state(root: Path) -> dict[str, str] | None:
    indexed = run_command(root, ["git", "ls-files", "-s", "-z"], 60)
    if not indexed.ok:
        return None

    state: dict[str, str] = {}
    for record in indexed.output.split("\0"):
        if not record:
            continue
        metadata, separator, rel = record.partition("\t")
        if not separator or not rel:
            return None
        path = root / rel
        payload = hashlib.sha256()
        payload.update(metadata.encode("utf-8", errors="replace"))
        payload.update(b"\0")
        try:
            if path.is_symlink():
                payload.update(b"symlink\0")
                payload.update(str(path.readlink()).encode("utf-8", errors="replace"))
            elif path.is_file():
                payload.update(b"file\0")
                with path.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        payload.update(chunk)
            elif path.exists():
                payload.update(b"other\0")
            else:
                payload.update(b"missing\0")
        except OSError:
            return None
        state[rel] = payload.hexdigest()
    return state


def _display_command(raw_command: list[str]) -> list[str]:
    return [arg.replace(INPUT_TOKEN, REDACTED_INPUT) for arg in raw_command]


def _redact_output(value: str, input_value: str) -> str:
    if not input_value:
        return value
    return value.replace(input_value, REDACTED_INPUT)


def _payload(
    *,
    action_id: str,
    command: list[str] | str,
    exit_code: int,
    detail_log: str,
    worktree_mutation: list[str] | None = None,
) -> dict[str, object]:
    payload = build_result_contract(
        command=command,
        exit_code=exit_code,
        detail_log=detail_log,
        gate=action_id,
        worktree_mutation=worktree_mutation,
    )
    # Backward compatibility: existing Companion/project-owned consumers read `output`.
    # 1.3.12 adds summary/detailLog/failure fields without removing the historical field.
    payload["output"] = detail_log
    if worktree_mutation:
        payload["worktreeMutation"] = list(worktree_mutation)
    return payload


@dataclass
class ActionSpec:
    id: str
    label: str
    category: str
    description: str = ""
    commands: list[list[str]] = field(default_factory=list)
    confirmation: str | None = None
    danger: bool = False
    timeout: int = 3600
    guard: Callable[[Path], tuple[bool, str]] | None = None
    input_label: str | None = None
    input_placeholder: str | None = None
    input_required: bool = False
    non_mutating: bool = False
    background: bool = False
    progress_labels: list[str] = field(default_factory=list)

    def public(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "id": self.id,
            "label": self.label,
            "category": self.category,
            "description": self.description,
            "requiresConfirmation": self.confirmation is not None,
            "danger": self.danger,
            "nonMutating": self.non_mutating,
            "background": self.background,
        }
        if self.input_label is not None:
            payload["input"] = {
                "label": self.input_label,
                "placeholder": self.input_placeholder or "",
                "required": self.input_required,
            }
        return payload

    def progress_label(self, index: int) -> str:
        if 0 <= index < len(self.progress_labels) and self.progress_labels[index].strip():
            return self.progress_labels[index].strip()
        if len(self.commands) <= 1:
            return self.label
        return f"{self.label} · Schritt {index + 1}/{len(self.commands)}"


class ActionRegistry:
    def __init__(self, root: Path):
        self.root = root
        self._actions: dict[str, ActionSpec] = {}

    def register(self, spec: ActionSpec) -> None:
        if not spec.id or spec.id in self._actions:
            raise ValueError(f"Doppelte oder leere Action-ID: {spec.id!r}")
        if any(not isinstance(cmd, list) or not cmd for cmd in spec.commands):
            raise ValueError(f"Ungültige Command-Liste in Action {spec.id}")
        if any(not isinstance(label, str) or not label.strip() for label in spec.progress_labels):
            raise ValueError(f"Ungültige Progress-Labels in Action {spec.id}")
        if len(spec.progress_labels) > len(spec.commands):
            raise ValueError(f"Action {spec.id} definiert mehr Progress-Labels als Commands")
        uses_input = any(INPUT_TOKEN in arg for cmd in spec.commands for arg in cmd)
        if uses_input and spec.input_label is None:
            raise ValueError(f"Action {spec.id} verwendet {INPUT_TOKEN}, definiert aber kein input_label")
        if spec.input_label is not None and not uses_input:
            raise ValueError(f"Action {spec.id} definiert Eingabe, verwendet aber {INPUT_TOKEN} in keinem Command")
        self._actions[spec.id] = spec

    def get(self, action_id: str) -> ActionSpec | None:
        return self._actions.get(action_id)

    def all(self) -> list[ActionSpec]:
        return list(self._actions.values())

    def execute(
        self,
        action_id: str,
        confirmation: str | None = None,
        user_input: str | None = None,
        progress: ActionProgressReporter | None = None,
    ) -> dict[str, object]:
        spec = self.get(action_id)
        if spec is None:
            return _payload(
                action_id=action_id,
                command=action_id,
                exit_code=404,
                detail_log="Unbekannte Aktion.",
            )
        if spec.confirmation is not None and confirmation != spec.confirmation:
            return _payload(
                action_id=action_id,
                command=action_id,
                exit_code=409,
                detail_log=f"Bestätigung fehlt. Erwartet: {spec.confirmation}",
            )
        input_value = "" if user_input is None else str(user_input)
        if spec.input_required and not input_value.strip():
            return _payload(
                action_id=action_id,
                command=action_id,
                exit_code=409,
                detail_log=f"Eingabe fehlt: {spec.input_label or 'Wert'}",
            )
        if spec.guard:
            allowed, reason = spec.guard(self.root)
            if not allowed:
                return _payload(
                    action_id=action_id,
                    command=action_id,
                    exit_code=409,
                    detail_log=reason,
                )

        baseline_state: dict[str, str] | None = None
        if spec.non_mutating:
            baseline_state = _tracked_worktree_state(self.root)
            if baseline_state is None:
                return _payload(
                    action_id=action_id,
                    command=action_id,
                    exit_code=409,
                    detail_log="Non-Mutating-Contract konnte den getrackten Git-Working-Tree nicht bestimmen.",
                )

        total = max(1, len(spec.commands))
        log: list[str] = []
        for index, raw_command in enumerate(spec.commands):
            command = [arg.replace(INPUT_TOKEN, input_value) for arg in raw_command]
            display_command = _display_command(raw_command)
            if progress:
                progress({
                    "phase": "action-command",
                    "label": spec.progress_label(index),
                    "detail": f"Schritt {index + 1}/{total} läuft.",
                    "completed": index,
                    "total": total,
                })
            log.append("$ " + " ".join(display_command))
            result = run_command(self.root, command, spec.timeout)
            if result.output:
                log.append(_redact_output(result.output.rstrip(), input_value))

            if spec.non_mutating:
                current_state = _tracked_worktree_state(self.root)
                if current_state is None:
                    log.append("FEHLER · Non-Mutating-Contract konnte den Git-Working-Tree nach dem Command nicht bestimmen.")
                    return _payload(
                        action_id=action_id,
                        command=display_command,
                        exit_code=result.returncode if not result.ok else 409,
                        detail_log="\n".join(log),
                    )
                if current_state != baseline_state:
                    mutation_paths = sorted(
                        rel
                        for rel in set(baseline_state) | set(current_state)
                        if baseline_state.get(rel) != current_state.get(rel)
                    )
                    shown = ", ".join(mutation_paths) if mutation_paths else "getrackter Working Tree"
                    log.append(
                        "FEHLER · Non-Mutating-Contract verletzt: "
                        f"Action {action_id} hat getrackte Dateien verändert: {shown}"
                    )
                    return _payload(
                        action_id=action_id,
                        command=display_command,
                        exit_code=result.returncode if not result.ok else 409,
                        detail_log="\n".join(log),
                        worktree_mutation=mutation_paths,
                    )

            if not result.ok:
                return _payload(
                    action_id=action_id,
                    command=display_command,
                    exit_code=result.returncode,
                    detail_log="\n".join(log),
                )
            if progress:
                progress({
                    "phase": "action-command",
                    "label": spec.progress_label(index),
                    "detail": f"Schritt {index + 1}/{total} abgeschlossen.",
                    "completed": index + 1,
                    "total": total,
                })

        command_text = " && ".join(" ".join(_display_command(c)) for c in spec.commands)
        return _payload(
            action_id=action_id,
            command=command_text,
            exit_code=0,
            detail_log="\n".join(log),
        )


def register_many(registry: ActionRegistry, specs: Iterable[ActionSpec]) -> None:
    for spec in specs:
        registry.register(spec)
