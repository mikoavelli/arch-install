from pathlib import Path

from installer.config import Config
from installer.runner import run, section


def run_step(config: Config) -> None:
    _install_system_packages(config)
    _install_flatpak_packages(config)
    _configure_flatpaks(config)
    _downgrade_packages(config)


def _install_system_packages(config: Config) -> None:
    packages = config.system_packages()
    section(f"[Packages] Installing {len(packages)} packages via yay...")
    run(["yay", "-S", "--needed", "--noconfirm", *packages])


def _install_flatpak_packages(config: Config) -> None:
    packages = config.flatpak_packages()
    section(f"[Flatpak] Installing {len(packages)} Flatpak packages...")
    run(["flatpak", "install", "flathub", "-y", *[p.name for p in packages]])


def _configure_flatpaks(config: Config) -> None:
    section("[Flatpak] Applying overrides...")

    packages = config.flatpak_packages()

    for pkg in packages:
        # Apply environment variable overrides
        for env_var, value in pkg.env.items():
            run(["sudo", "flatpak", "override", f"--env={env_var}={value}", pkg.name])

        # Apply filesystem overrides
        for path in pkg.fs:
            expanded = str(Path(path).expanduser())
            run(["sudo", "flatpak", "override", f"--filesystem={expanded}", pkg.name])


def _downgrade_packages(config: Config) -> None:
    packages = config.all_downgrade_packages()
    if not packages:
        section("[Downgrade] No packages to downgrade, skipping")
        return

    section(f"[Downgrade] Downgrading {len(packages)} package(s)...")
    for pkg in packages:
        print(f"# {pkg.name}{pkg.version}  ({pkg.description})")

    run([
        "sudo", "downgrade",
        "--latest", "--prefer-cache", "--ignore", "always",
        *[pkg.downgrade_target for pkg in packages],
        "--", "--noconfirm", "--needed",
    ])
