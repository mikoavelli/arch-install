from pathlib import Path

from installer.config import Config
from installer.runner import command_exists, run, section


def run_step(config: Config) -> None:
    _install_core_packages(config)
    _install_aur_packages(config)
    _downgrade_packages(config)

    if not (command_exists("flatpak") and config.flatpak_packages()):
        section("[Flatpak] Package 'flatpak' is not installed, skipping")
        return

    _install_flatpak_packages(config)
    _configure_flatpaks(config)


def _install_core_packages(config: Config) -> None:
    packages = config.core_packages()
    section(f"[Packages] Installing {len(packages)} core packages...")
    run(["yay", "-S", "--needed", "--noconfirm", *packages])


def _install_aur_packages(config: Config) -> None:
    packages = config.aur_packages()
    if config.all_downgrade_packages():
        packages.append("downgrade")
    if not packages:
        return

    section(f"[Packages] Installing {len(packages)} AUR packages...")
    run(["yay", "-S", "--needed", *packages])


def _downgrade_packages(config: Config) -> None:
    packages = config.all_downgrade_packages()
    if not packages:
        section("[Downgrade] No packages to downgrade, skipping")
        return

    section(f"[Downgrade] Downgrading {len(packages)} package(s)...")
    for pkg in packages:
        print(f"# {pkg.name}{pkg.version}  ({pkg.description})")

    run(
        [
            "downgrade",
            "--latest",
            "--prefer-cache",
            "--ignore",
            "always",
            *[pkg.downgrade_target for pkg in packages],
            "--",
            "--noconfirm",
            "--needed",
        ],
        sudo=True,
    )


def _install_flatpak_packages(config: Config) -> None:
    packages = config.flatpak_packages()
    section(f"[Flatpak] Installing {len(packages)} Flatpak packages...")
    run(["flatpak", "install", "flathub", "-y", *[p.name for p in packages]])


def _configure_flatpaks(config: Config) -> None:
    packages = config.flatpak_packages()
    section("[Flatpak] Applying overrides...")

    for pkg in packages:
        for env_var, value in pkg.env.items():
            run(["flatpak", "override", f"--env={env_var}={value}", pkg.name], sudo=True)

        for path in pkg.fs:
            expanded = str(Path(path).expanduser())
            run(["flatpak", "override", f"--filesystem={expanded}", pkg.name], sudo=True)
