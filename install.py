#!/usr/bin/env python3

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import cast

sys.path.insert(0, str(Path(__file__).parent))

from installer.config import load_config
from installer.runner import CommandError, command_exists, run, section, style
from installer.steps import bootstrap, packages, secureboot, system, user, yay


def main() -> None:
    parser = argparse.ArgumentParser(description="Arch Linux installation script")
    _ = parser.add_argument(
        "--dry-run", action="store_true", help="Print commands without executing"
    )
    _ = parser.add_argument(
        "--skip-mirrors", action="store_true", help="Skip mirrorlist update using reflector"
    )
    args = parser.parse_args()
    dry_run = cast("bool", args.dry_run)
    skip_mirrors = cast("bool", args.skip_mirrors)

    if dry_run:
        import installer.runner as runner_mod

        runner_mod.DRY_RUN = True

    print(style("-> Starting Arch Linux Installation", "bold", "green"))
    config = load_config()

    steps: list[tuple[str, Callable[[], None]]] = [
        ("Bootstrap", lambda: bootstrap.run_step(config, skip_mirrors=skip_mirrors)),
        ("Yay", lambda: yay.run_step()),
        ("Packages", lambda: packages.run_step(config)),
        ("System", lambda: system.run_step(config)),
        ("User", lambda: user.run_step(config)),
        ("Secure Boot", lambda: secureboot.run_step(config)),
    ]

    try:
        for name, step in steps:
            try:
                step()
            except CommandError as e:
                print(style(f"\nStep '{name}' failed: {e}", "bold", "red"), file=sys.stderr)
                sys.exit(1)

        section("[Cleanup] Removing unused dependencies...")
        run("yay -Yc --noconfirm")
        run("yay -Scc --noconfirm")

        if command_exists("flatpak"):
            run("flatpak update -y")
            run("flatpak repair")

        print(style("\nSetup complete! Please run the following scripts:", "bold", "green"))
        print("   1) postinstall.py — post-installation user setup.")
        print("   2) stow           — create symlinks for your configs.")

    except KeyboardInterrupt:
        print(style("\nInstallation cancelled by user.", "bold", "yellow"), file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
