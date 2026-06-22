from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
from collections.abc import Sequence
from subprocess import CompletedProcess
from typing import Literal, overload


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

    print(f"$ {shlex.join(args)}", flush=True)

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
    print(f"\n\033[1;34m-> {title}\033[0m", flush=True)
