import sys

from installer.config import Config
from installer.runner import run, section, command_exists


def run_step(config: Config) -> None:
    if not command_exists("sbctl"):
        section("[Secure Boot] Package 'sbctl' is not installed, skipping")
        return

    section("[Secure Boot] Setting up sbctl...")

    run("sudo sbctl create-keys")

    for target in config.secureboot.sign_targets:
        run(["sudo", "sbctl", "sign", target])

    run("sudo sbctl verify")

    result = run("sudo sbctl enroll-keys", check=False, capture=True)

    if result.returncode != 0 and result.stderr:
        print(f"\033[1;33m{result.stderr}\033[0m", file=sys.stderr, end="")
