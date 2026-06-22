#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from typing import cast

sys.path.insert(0, str(Path(__file__).parent))

from installer.config import Config, load_config
from installer.runner import command_exists, run, section, style


def prompt(msg: str) -> str:
    try:
        return input(msg).strip()
    except KeyboardInterrupt, EOFError:
        print()
        sys.exit(0)


def _create_ssh_keys(email: str) -> None:
    section("[SSH] Creating SSH keys for GitHub...")

    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)

    for key_name in ("github-sign", "github-auth"):
        key_path = ssh_dir / key_name
        if key_path.exists():
            print(f"  Key {key_path} already exists, skipping")
            continue
        run(
            [
                "ssh-keygen",
                "-t",
                "ed25519",
                "-C",
                email,
                "-f",
                str(key_path),
                "-N",
                "",
            ]
        )


def _configure_git(config: Config, email: str, name: str) -> None:
    section("[Git] Base git configuration...")

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


def _setup_allowed_signers(email: str) -> None:
    section("[SSH] Setting up allowed_signers...")

    sign_pub = Path.home() / ".ssh" / "github-sign.pub"
    allowed = Path.home() / ".ssh" / "allowed_signers"

    if not sign_pub.exists():
        print("  SSH public key not found, skipping allowed_signers setup")
        return

    pub_key = sign_pub.read_text().strip()
    entry = f"{email} {pub_key}"

    if allowed.exists() and entry in allowed.read_text():
        print("  Key already exists in allowed_signers, skipping")
        return

    with allowed.open("a") as f:
        _ = f.write(entry + "\n")
    print("  Key added to allowed_signers")


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


def _custom_flatpak_overrides() -> None:
    if not command_exists("org.telegram.desktop"):
        section("[Flatpak] Flatpak 'org.telegram.desktop' is not installed, skipping")
        return

    section("[Flatpak] Disabling device access to 'org.telegram.desktop' flatpak ")
    run(["flatpak", "override", "--nodevice=all", "org.telegram.desktop"], sudo=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Post-installation setup for Arch Linux: Niri")
    _ = parser.add_argument(
        "--dry-run", action="store_true", help="Print commands without executing"
    )
    args = parser.parse_args()
    dry_run = cast("bool", args.dry_run)

    if dry_run:
        import installer.runner as runner_mod

        runner_mod.DRY_RUN = True

    config = load_config()

    email = prompt("Enter your email for git config and SSH key: ")
    name = prompt("Enter your name for git config: ")

    _create_ssh_keys(email)
    _configure_git(config, email, name)
    _setup_allowed_signers(email)
    _update_tldr()
    _setup_rust()
    _custom_flatpak_overrides()

    print(style("\nPost-installation complete!", "bold", "green"))


if __name__ == "__main__":
    main()
