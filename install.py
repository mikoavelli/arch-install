#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from installer.config import load_config
from installer.runner import CommandError, run, section, command_exists
from installer.steps import bootstrap, yay, packages, system, user, secureboot


def main() -> None:
    print("\033[1;32m-> Starting Arch Linux: Niri Installation\033[0m")
    config = load_config()

    steps = [
        ("Bootstrap", lambda: bootstrap.run_step(config)),
        ("Yay", lambda: yay.run_step()),
        ("Packages", lambda: packages.run_step(config)),
        ("System", lambda: system.run_step(config)),
        ("User", lambda: user.run_step(config)),
        ("Secure Boot", lambda: secureboot.run_step(config)),
    ]

    for name, step in steps:
        try:
            step()
        except CommandError as e:
            print(f"\n\033[1;31mStep '{name}' failed: {e}\033[0m", file=sys.stderr)
            sys.exit(1)

    section("[Cleanup] Removing unused dependencies...")
    run("yay -Yc --noconfirm")
    run("yay -Scc --noconfirm")

    if command_exists("flatpak"):
        run("flatpak update -y")
        run("flatpak repair")

    print("\n\033[1;32mSetup complete! Please run the following scripts:\033[0m")
    print(
        "   1) postinstall.py — from the arch-niri directory for post-installation setup."
    )
    print(
        "   2) stow.sh        — from the dotfiles directory to create symlinks for your configs,"
    )


if __name__ == "__main__":
    main()
