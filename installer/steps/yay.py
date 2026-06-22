import tempfile

from installer.runner import command_exists, run, section


def run_step() -> None:
    if command_exists("yay"):
        section("[AUR] yay is already installed, skipping")
        return

    section("[AUR] Installing yay...")

    with tempfile.TemporaryDirectory(prefix="yay-") as tmp:
        run(["git", "clone", "https://aur.archlinux.org/yay.git", tmp])
        run(["makepkg", "-si", "--noconfirm"], cwd=tmp)
