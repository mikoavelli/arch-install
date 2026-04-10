import subprocess
from pathlib import Path

from installer.runner import CommandError, command_exists, run, section


def run_step() -> None:
    if command_exists("yay"):
        section("[AUR] yay is already installed, skipping")
        return

    section("[AUR] Installing yay...")

    tmp = Path("/tmp/yay")
    if tmp.exists():
        run(["rm", "-rf", str(tmp)])

    run(["git", "clone", "https://aur.archlinux.org/yay.git", str(tmp)])

    result = subprocess.run(
        ["makepkg", "-si", "--noconfirm"],
        cwd=tmp,
        check=False,
    )
    if result.returncode != 0:
        raise CommandError("makepkg failed while building yay")

    run(["rm", "-rf", str(tmp)])
