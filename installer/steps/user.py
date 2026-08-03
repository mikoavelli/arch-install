from pathlib import Path

from installer.config import Config
from installer.runner import command_exists, run, section, write_file_sudo

IDEAPAD_SUDOERS = (
    r"%wheel ALL=(ALL) NOPASSWD: /usr/bin/tee "
    r"/sys/bus/platform/drivers/ideapad_acpi/VPC????\:??/conservation_mode"
)


def run_step(config: Config) -> None:
    _setup_ideapad()
    _apply_gsettings(config)


def _setup_ideapad() -> None:
    section("[User] Setting up ideapad sudoers rule...")
    write_file_sudo("/etc/sudoers.d/ideapad", IDEAPAD_SUDOERS)

    modules_file = Path("/etc/modules")
    content = modules_file.read_text() if modules_file.exists() else ""
    if "ideapad_laptop" not in content:
        _ = run(
            ["tee", "-a", "/etc/modules"],
            input="ideapad_laptop\n",
            capture=True,
            sudo=True,
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
