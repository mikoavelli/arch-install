from pathlib import Path

from installer.config import Config
from installer.runner import command_exists, run, section, write_file_sudo

SSH_CONFIG_BLOCK = """\
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github-auth
"""

IDEAPAD_SUDOERS = r"%wheel ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/bus/platform/drivers/ideapad_acpi/VPC????\:??/conservation_mode"


def run_step(config: Config) -> None:
    _setup_ssh_config()
    _setup_ideapad()
    _apply_gsettings(config)


def _setup_ssh_config() -> None:
    section("[User] Creating SSH config for custom key names...")

    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)

    config_file = ssh_dir / "config"
    if config_file.exists() and "Host github.com" in config_file.read_text():
        print("  SSH config already contains github.com entry, skipping")
        return

    with config_file.open("a") as f:
        f.write(SSH_CONFIG_BLOCK)

    config_file.chmod(0o600)


def _setup_ideapad() -> None:
    section("[User] Setting up ideapad sudoers rule...")
    write_file_sudo("/etc/sudoers.d/ideapad", IDEAPAD_SUDOERS)

    modules_file = Path("/etc/modules")
    content = modules_file.read_text() if modules_file.exists() else ""
    if "ideapad_laptop" not in content:
        run(
            ["sudo", "tee", "-a", "/etc/modules"],
            input="ideapad_laptop\n",
            capture=True,
        )


def _apply_gsettings(config: Config) -> None:
    if not command_exists("gsettings"):
        section("[User/Gsettings] Command 'gsettings' is not found, skipping")
        return

    if not config.gschemas:
        return

    section("[User/Gsettings] Applying gsettings...")
    for g in config.gschemas:
        run(["gsettings", "set", g.schema, g.key, g.value])
