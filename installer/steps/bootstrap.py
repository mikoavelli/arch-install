from installer.config import Config
from installer.runner import run, section


def run_step(config: Config) -> None:
    section("[Bootstrap] Synchronizing package databases...")
    run("pacman -Sy", sudo=True)

    packages = [p.name for p in config.bootstrap.packages] + [
        "git",
        "base-devel",
        "reflector",
    ]
    section(f"[Bootstrap] Installing {len(packages)} prerequisites...")
    run(["pacman", "-S", "--needed", "--noconfirm", *packages], sudo=True)

    section("[Bootstrap] Filtering best mirrors with reflector...")
    run(
        [
            "reflector",
            "--country",
            ",".join(config.bootstrap.mirrors),
            "--fastest",
            "10",
            "--protocol",
            "https",
            "--sort",
            "rate",
            "--save",
            "/etc/pacman.d/mirrorlist",
        ],
        sudo=True,
    )

    section("[Bootstrap] Updating system with new mirrors...")
    run("pacman -Syu --noconfirm", sudo=True)
