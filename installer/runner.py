from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
from collections.abc import Sequence
from subprocess import CompletedProcess
from typing import Literal, overload

DRY_RUN = False


_STYLES = {
    "reset": "0",
    "bold": "1",
    "dim": "2",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
}


def style(text: str, *effects: str) -> str:
    codes = [_STYLES[e] for e in effects if e in _STYLES]
    if not codes:
        return text
    return f"\033[{';'.join(codes)}m{text}\033[0m"


class CommandError(Exception):
    pass


@overload
def run(
    cmd: str | Sequence[str],
    *,
    check: bool = True,
    capture: Literal[False] = False,
    input: str | None = None,
    cwd: str | None = None,
    sudo: bool = False,
) -> None: ...


@overload
def run(
    cmd: str | Sequence[str],
    *,
    check: bool = True,
    capture: Literal[True],
    input: str | None = None,
    cwd: str | None = None,
    sudo: bool = False,
) -> CompletedProcess[str]: ...


def run(
    cmd: str | Sequence[str],
    *,
    check: bool = True,
    capture: bool = False,
    input: str | None = None,
    cwd: str | None = None,
    sudo: bool = False,
) -> CompletedProcess[str] | None:
    if isinstance(cmd, str):
        args = shlex.split(cmd)
    else:
        args = list(cmd)

    if not args:
        raise ValueError("No command provided")

    if sudo:
        args = ["sudo", *args]

    if DRY_RUN:
        print(style(f"$ {shlex.join(args)}", "dim"), flush=True)
        if capture:
            return CompletedProcess(args, 0, "", "")
        return None

    print(style(f"$ {shlex.join(args)}", "bold", "blue"), flush=True)

    result = subprocess.run(  # noqa: S603
        args,
        check=False,
        capture_output=capture,
        text=True,
        input=input,
        cwd=cwd,
    )

    if check and result.returncode != 0:
        if capture:
            print(result.stderr, file=sys.stderr)
        raise CommandError(f"Command failed (exit {result.returncode}): {shlex.join(args)}")

    return result if capture else None


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def write_file_sudo(path: str, content: str) -> None:
    _ = run(["tee", path], input=content, capture=True, sudo=True)


def section(title: str) -> None:
    print(style(f"\n-> {title}", "bold", "green"), flush=True)
