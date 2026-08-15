from installer.config import Config
from installer.runner import run, section


def run_step(config: Config, skip_mirrors: bool = False) -> None:
    packages = [p.name for p in config.bootstrap.packages] + [
        "git",
        "base-devel",
        "reflector",
    ]
    section(f"[Bootstrap] Installing {len(packages)} prerequisites...")
    run(["pacman", "-S", "--needed", "--noconfirm", *packages], sudo=True)

    if skip_mirrors:
        section("[Bootstrap] Skipping mirror filtering with reflector...")
    else:
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

    section("[Bootstrap] Updating system...")
    run("pacman -Syu --noconfirm", sudo=True)
