from installer.config import Config
from installer.runner import run, section, write_file_sudo, command_exists

IWD_CONFIG = """\
[General]
EnableNetworkConfiguration=true

[Network]
NameResolvingService=systemd
"""


def run_step(config: Config) -> None:
    _set_ttl()
    _power_key()
    _bootloader()
    _disable_beep()
    _configure_iwd()
    _configure_ufw(config)
    _enable_services(config)
    _disable_services(config)


def _set_ttl() -> None:
    section("[System] Changing default TTL for mobile hotspot...")
    run(["sudo", "mkdir", "-p", "/etc/sysctl.d/"])
    write_file_sudo(
        "/etc/sysctl.d/99-ttl-mobile-hotspot.conf",
        "net.ipv4.ip_default_ttl = 65\n",
    )


def _power_key() -> None:
    section("[System] Disabling suspend on power key press...")
    run(["sudo", "mkdir", "-p", "/etc/systemd/logind.conf.d"])
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
            "sudo",
            "ln",
            "-sf",
            "/run/systemd/resolve/stub-resolv.conf",
            "/etc/resolv.conf",
        ]
    )
    run(["sudo", "mkdir", "-p", "/etc/iwd"])
    write_file_sudo("/etc/iwd/main.conf", IWD_CONFIG)


def _configure_ufw(config: Config) -> None:
    if not command_exists("ufw"):
        section("[System/Security] Package 'ufw' is not installed, skipping")
        return

    section("[System/Security] Configuring ufw...")
    run("sudo ufw default deny incoming")
    run("sudo ufw default allow outgoing")

    for rule in config.ufw.allow:
        desc = f" ({rule.description})" if rule.description else ""
        print(f"  Allowing {rule.port}/{rule.proto}{desc}")
        run(["sudo", "ufw", "allow", f"{rule.port}/{rule.proto}"])

    run("sudo ufw reload")
    run("sudo ufw enable")


def _enable_services(config: Config) -> None:
    if not config.services.enable:
        return
    section("[System] Enabling services...")
    run(["sudo", "systemctl", "enable", *config.services.enable])


def _disable_services(config: Config) -> None:
    section("[System] Disabling unused services...")
    if config.services.disable:
        run(
            ["sudo", "systemctl", "disable", *config.services.disable],
            check=False,
        )
    if config.services.mask:
        run(["sudo", "systemctl", "mask", *config.services.mask])
