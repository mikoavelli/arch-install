import re
from pathlib import Path

from installer.config import Config
from installer.runner import (
    command_exists,
    replace_in_file_sudo,
    run,
    section,
    style,
    write_file_sudo,
)

IWD_CONFIG = """\
[General]
EnableNetworkConfiguration=true

[Network]
NameResolvingService=systemd
"""

IDEAPAD_SUDOERS = (
    r"%wheel ALL=(ALL) NOPASSWD: /usr/bin/tee "
    r"/sys/bus/platform/drivers/ideapad_acpi/VPC????\:??/conservation_mode"
)


def run_step(config: Config) -> None:
    _set_ttl()
    _power_key()
    _bootloader()
    _disable_beep()
    _configure_iwd()
    _configure_faillock()
    _configure_locale(config)
    _setup_ideapad()
    _configure_ufw(config)
    _enable_services(config)
    _disable_services(config)


def _set_ttl() -> None:
    section("[System] Changing default TTL for mobile hotspot...")
    run(["mkdir", "-p", "/etc/sysctl.d/"], sudo=True)
    write_file_sudo(
        "/etc/sysctl.d/99-ttl-mobile-hotspot.conf",
        "net.ipv4.ip_default_ttl = 65\n",
    )


def _power_key() -> None:
    section("[System] Disabling suspend on power key press...")
    run(["mkdir", "-p", "/etc/systemd/logind.conf.d"], sudo=True)
    write_file_sudo(
        "/etc/systemd/logind.conf.d/99-power-key.conf",
        "[Login]\nHandlePowerKey=ignore\n",
    )


def _bootloader() -> None:
    section("[System] Hiding systemd-boot menu...")
    write_file_sudo("/boot/loader/loader.conf", "timeout 0\n")


def _disable_beep() -> None:
    section("[System] Disabling motherboard speaker beep...")
    write_file_sudo("/etc/modprobe.d/nobeep.conf", "blacklist pcspkr\n")


def _configure_iwd() -> None:
    if not command_exists("iwctl"):
        section("[System/Network] Package 'iwd' is not installed, skipping")
        return

    section("[System/Network] Configuring iwd...")
    run(
        [
            "ln",
            "-sf",
            "/run/systemd/resolve/stub-resolv.conf",
            "/etc/resolv.conf",
        ],
        sudo=True,
    )
    run(["mkdir", "-p", "/etc/iwd"], sudo=True)
    write_file_sudo("/etc/iwd/main.conf", IWD_CONFIG)


def _configure_faillock() -> None:
    section("[System/Security] Configuring faillock deny threshold...")
    replace_in_file_sudo(
        "/etc/security/faillock.conf",
        r"(?m)^#?\s*deny\s*=\s*\d+.*$",
        "deny = 10",
    )


def _configure_locale(config: Config) -> None:
    if not config.locale.gen and not config.locale.conf:
        return

    section("[System/Locale] Configuring system locales...")

    if config.locale.gen:
        for loc in config.locale.gen:
            escaped_loc = re.escape(loc)
            replace_in_file_sudo(
                "/etc/locale.gen",
                rf"(?m)^#\s*({escaped_loc})",
                r"\1",
            )
        run("locale-gen", sudo=True)

    if config.locale.conf:
        locale_content = "\n".join(config.locale.conf) + "\n"
        write_file_sudo("/etc/locale.conf", locale_content)


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


def _configure_ufw(config: Config) -> None:
    if not command_exists("ufw"):
        section("[System/Security] Package 'ufw' is not installed, skipping")
        return

    section("[System/Security] Configuring ufw...")
    run("ufw default deny incoming", sudo=True)
    run("ufw default allow outgoing", sudo=True)

    for rule in config.ufw.allow:
        desc = f" ({rule.description})" if rule.description else ""
        print(style(f"# Allowing {rule.port}/{rule.proto}{desc}", "cyan"))
        run(["ufw", "allow", f"{rule.port}/{rule.proto}"], sudo=True)

    run("ufw reload", sudo=True)
    run("ufw enable", sudo=True)


def _enable_services(config: Config) -> None:
    if not config.services.enable:
        return
    section("[System] Enabling services...")
    run(["systemctl", "enable", *config.services.enable], sudo=True)


def _disable_services(config: Config) -> None:
    section("[System] Disabling unused services...")
    if config.services.disable:
        run(
            ["systemctl", "disable", *config.services.disable],
            check=False,
            sudo=True,
        )
    if config.services.mask:
        run(["systemctl", "mask", *config.services.mask], sudo=True)
