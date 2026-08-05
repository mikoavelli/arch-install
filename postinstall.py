#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from typing import cast

import installer.runner as runner_mod

sys.path.insert(0, str(Path(__file__).parent))

from installer.config import Config, load_config
from installer.runner import command_exists, run, section, style

SSH_CONFIG_BLOCK = """\
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github-auth
"""


def prompt(msg: str) -> str:
    try:
        return input(msg).strip()
    except KeyboardInterrupt, EOFError:
        print(style("\n\nPost-installation cancelled by user.", "bold", "yellow"), file=sys.stderr)
        sys.exit(130)


def _setup_ssh() -> None:
    section("[SSH] Setting up SSH keys and config for GitHub...")

    ssh_dir = Path.home() / ".ssh"
    run(["mkdir", "-p", "-m", "700", str(ssh_dir)])

    for key_name in ("github-sign", "github-auth"):
        key_path = ssh_dir / key_name
        if key_path.exists():
            print(style(f"# Key {key_path} already exists, skipping", "dim", "cyan"))
            continue
        run(
            [
                "ssh-keygen",
                "-t",
                "ed25519",
                "-C",
                "",
                "-f",
                str(key_path),
                "-N",
                "",
            ]
        )

    config_file = ssh_dir / "config"
    if config_file.exists() and "Host github.com" in config_file.read_text():
        print(style("# SSH config already contains github.com entry, skipping", "dim", "cyan"))
    else:
        _ = run(["tee", "-a", str(config_file)], input=SSH_CONFIG_BLOCK, capture=True)
        run(["chmod", "600", str(config_file)])


def _setup_allowed_signers(email: str) -> None:
    section("[SSH] Setting up allowed_signers...")

    sign_pub = Path.home() / ".ssh" / "github-sign.pub"
    allowed = Path.home() / ".ssh" / "allowed_signers"

    if not sign_pub.exists() and not runner_mod.DRY_RUN:
        print(
            style("# SSH public key not found, skipping allowed_signers setup", "bold", "magenta")
        )
        return

    if sign_pub.exists():
        pub_key = sign_pub.read_text().strip()
    else:
        pub_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI_DRY_RUN_PLACEHOLDER_KEY"

    entry = f"{email} {pub_key}"

    if allowed.exists() and entry in allowed.read_text():
        print(style("# Key already exists in allowed_signers, skipping", "dim", "cyan"))
        return

    _ = run(["tee", "-a", str(allowed)], input=entry + "\n", capture=True)


def _configure_git(config: Config, email: str, name: str) -> None:
    section("[Git] Configuring global git settings...")

    sign_key = str(Path.home() / ".ssh" / "github-sign.pub")
    allowed = str(Path.home() / ".ssh" / "allowed_signers")

    placeholders = {
        "{email}": email,
        "{name}": name,
        "{sign_key}": sign_key,
        "{allowed}": allowed,
    }

    for setting in config.git.settings:
        value = setting.value
        for placeholder, replacement in placeholders.items():
            value = value.replace(placeholder, replacement)
        run(["git", "config", "set", "--global", setting.key, value])


def _apply_gsettings(config: Config) -> None:
    if not command_exists("gsettings"):
        section("[User/Gsettings] Command 'gsettings' is not found, skipping")
        return

    if not config.gschemas:
        return

    section("[User/Gsettings] Applying gsettings...")
    for g in config.gschemas:
        run(["gsettings", "set", g.schema, g.key, g.value])


def _update_tldr() -> None:
    if not command_exists("tldr"):
        section("[TLDR] Command 'tldr' is not found, skipping")
        return

    section("[TLDR] Downloading cache...")
    run("tldr --update")


def _setup_rust() -> None:
    if not command_exists("rustup"):
        section("[Rust] Package 'rustup' is not installed, skipping")
        return

    section("[Rust] Installing latest stable toolchain...")
    run("rustup default stable")


def main() -> None:
    parser = argparse.ArgumentParser(description="Post-installation setup for Arch Linux")
    _ = parser.add_argument(
        "--dry-run", action="store_true", help="Print commands without executing"
    )
    args = parser.parse_args()
    dry_run = cast("bool", args.dry_run)

    if dry_run:
        runner_mod.DRY_RUN = True

    try:
        config = load_config()

        if dry_run:
            github_id = "12345"
            name = "user"
            email = f"{github_id}+{name}@users.noreply.github.com"
        else:
            github_id = prompt("Enter your GitHub ID (numeric, from profile URL): ")
            name = prompt("Enter your username for git config: ")
            email = f"{github_id}+{name}@users.noreply.github.com"

        _setup_ssh()
        _setup_allowed_signers(email)
        _configure_git(config, email, name)
        _apply_gsettings(config)
        _update_tldr()
        _setup_rust()

        print(style("\nPost-installation complete!", "bold", "green"))
    except KeyboardInterrupt:
        print(style("\nPost-installation cancelled by user.", "bold", "yellow"), file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
