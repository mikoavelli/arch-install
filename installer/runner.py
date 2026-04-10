from __future__ import annotations

import shlex
import subprocess
import sys
from typing import Sequence


class CommandError(Exception):
    pass


def run(
    cmd: str | Sequence[str],
    *,
    check: bool = True,
    capture: bool = False,
    input: str | None = None,
) -> subprocess.CompletedProcess:
    if isinstance(cmd, str):
        args = shlex.split(cmd)
    else:
        args = list(cmd)

    print(f"$ {shlex.join(args)}", flush=True)

    result = subprocess.run(
        args,
        check=False,
        capture_output=capture,
        text=True,
        input=input,
    )

    if check and result.returncode != 0:
        if capture:
            print(result.stderr, file=sys.stderr)
        raise CommandError(
            f"Command failed (exit {result.returncode}): {shlex.join(args)}"
        )

    return result


def run_shell(cmd: str, *, check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {cmd}", flush=True)
    result = subprocess.run(cmd, shell=True, check=False, text=True)
    if check and result.returncode != 0:
        raise CommandError(f"Shell command failed (exit {result.returncode}): {cmd}")
    return result


def command_exists(name: str) -> bool:
    result = subprocess.run(
        ["which", name], capture_output=True, check=False
    )
    return result.returncode == 0


def write_file_sudo(path: str, content: str) -> None:
    run(["sudo", "tee", path], input=content, capture=True)


def section(title: str) -> None:
    print(f"\n\033[1;34m-> {title}\033[0m", flush=True)
