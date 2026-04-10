from installer.config import Config
from installer.runner import run, section


def run_step(config: Config) -> None:
    section("[Secure Boot] Setting up sbctl...")

    run("sudo sbctl create-keys")

    for target in config.secureboot.sign_targets:
        run(["sudo", "sbctl", "sign", target])

    run("sudo sbctl verify")
    run("sudo sbctl enroll-keys")
