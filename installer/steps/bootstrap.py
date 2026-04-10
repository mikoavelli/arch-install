from installer.config import Config
from installer.runner import run, section


def run_step(config: Config) -> None:
    section("[Bootstrap] Synchronizing package databases...")
    run("sudo pacman -Sy")

    packages = [p.name for p in config.bootstrap.packages]
    section(f"[Bootstrap] Installing {len(packages)} prerequisites...")
    run(["sudo", "pacman", "-S", "--needed", "--noconfirm", *packages])

    section("[Bootstrap] Filtering best mirrors with reflector...")
    run([
        "sudo", "reflector",
        "--country", config.bootstrap.mirrors,
        "--fastest", "10",
        "--protocol", "https",
        "--sort", "rate",
        "--save", "/etc/pacman.d/mirrorlist",
    ])

    section("[Bootstrap] Updating system with new mirrors...")
    run("sudo pacman -Syu --noconfirm")
