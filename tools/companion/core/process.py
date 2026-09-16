from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    output: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out


def run_command(root: Path, command: Sequence[str], timeout: int = 3600) -> CommandResult:
    argv = [str(x) for x in command]
    try:
        result = subprocess.run(
            argv,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
        )
        return CommandResult(argv, result.returncode, result.stdout or "")
    except subprocess.TimeoutExpired as exc:
        output = ""
        if exc.stdout:
            output = exc.stdout.decode() if isinstance(exc.stdout, bytes) else str(exc.stdout)
        return CommandResult(argv, 408, output + "\nZeitlimit überschritten.", timed_out=True)
    except OSError as exc:
        return CommandResult(argv, 127, str(exc))
