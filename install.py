#!/usr/bin/env python3

import argparse
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import cast

sys.path.insert(0, str(Path(__file__).parent))

from installer.config import ConfigError, load_config
from installer.runner import CommandError, command_exists, run, section, style
from installer.steps import bootstrap, packages, secureboot, system, yay


def _normalize_name(name: str) -> str:
    return name.lower().replace(" ", "").replace("-", "").replace("_", "")


def _filter_steps(
    steps: list[tuple[str, Callable[[], None]]],
    step_filter: str | None,
    skip_filter: str | None,
) -> list[tuple[str, Callable[[], None]]]:
    if step_filter:
        selected = {_normalize_name(s) for s in step_filter.split(",") if s.strip()}
        filtered = [step for step in steps if _normalize_name(step[0]) in selected]
        if not filtered:
            valid = ", ".join(f"'{s[0]}'" for s in steps)
            print(
                style(
                    f"Error: No matching steps found for '{step_filter}'. Valid steps: {valid}",
                    "bold",
                    "red",
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        return filtered

    if skip_filter:
        skipped = {_normalize_name(s) for s in skip_filter.split(",") if s.strip()}
        return [step for step in steps if _normalize_name(step[0]) not in skipped]

    return steps


def main() -> None:
    if os.geteuid() == 0:
        print(
            style(
                "Error: Do not run this script directly as root. "
                + "Run it as a regular user with sudo privileges.",
                "bold",
                "red",
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Arch Linux installation script")
    _ = parser.add_argument(
        "-c", "--config", type=Path, default=None, help="Path to custom config TOML file"
    )
    _ = parser.add_argument(
        "--dry-run", action="store_true", help="Print commands without executing"
    )
    _ = parser.add_argument(
        "--skip-mirrors", action="store_true", help="Skip mirrorlist update using reflector"
    )
    _ = parser.add_argument(
        "--step",
        type=str,
        help="Comma-separated list of steps to run (e.g. 'packages,system'). "
        + "Overrides --skip if both are set.",
    )
    _ = parser.add_argument(
        "--skip",
        type=str,
        help="Comma-separated list of steps to skip (e.g. 'bootstrap,secureboot').",
    )

    args = parser.parse_args()
    config_path = cast("Path | None", args.config)
    dry_run = cast("bool", args.dry_run)
    skip_mirrors = cast("bool", args.skip_mirrors)
    step_arg = cast("str | None", args.step)
    skip_arg = cast("str | None", args.skip)

    if dry_run:
        import installer.runner as runner_mod

        runner_mod.DRY_RUN = True

    print(style("-> Starting Arch Linux Installation", "bold", "green"))

    try:
        config = load_config(config_path)
    except ConfigError as e:
        print(style(f"Error: {e}", "bold", "red"), file=sys.stderr)
        sys.exit(1)

    all_steps: list[tuple[str, Callable[[], None]]] = [
        ("Bootstrap", lambda: bootstrap.run_step(config, skip_mirrors=skip_mirrors)),
        ("Yay", lambda: yay.run_step()),
        ("Packages", lambda: packages.run_step(config)),
        ("System", lambda: system.run_step(config)),
        ("Secure Boot", lambda: secureboot.run_step(config)),
    ]

    steps = _filter_steps(all_steps, step_arg, skip_arg)

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
