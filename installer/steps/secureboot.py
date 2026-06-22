import sys

from installer.config import Config
from installer.runner import command_exists, run, section


def run_step(config: Config) -> None:
    if not command_exists("sbctl"):
        section("[Secure Boot] Package 'sbctl' is not installed, skipping")
        return

    section("[Secure Boot] Setting up sbctl...")

    run("sbctl create-keys", sudo=True)

    for target in config.secureboot.sign_targets:
        run(["sbctl", "sign", target], sudo=True)

    run("sbctl verify", sudo=True)

    result = run("sbctl enroll-keys", check=False, capture=True, sudo=True)

    if result.returncode != 0 and result.stderr:
        print(f"\033[1;33m{result.stderr}\033[0m", file=sys.stderr, end="")
