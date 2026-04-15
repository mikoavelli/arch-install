from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import tomllib


@dataclass
class Package:
    name: str
    description: str = ""
    version: str = ""
    env: dict[str, str] = field(default_factory=dict)
    fs: list[str] = field(default_factory=list)

    @property
    def needs_downgrade(self) -> bool:
        return bool(self.version)

    @property
    def downgrade_target(self) -> str:
        return f"{self.name}{self.version}"


@dataclass
class PackageGroup:
    name: str
    description: str
    packages: list[Package]

    def regular_packages(self) -> list[Package]:
        return [p for p in self.packages if not p.needs_downgrade]

    def downgrade_packages(self) -> list[Package]:
        return [p for p in self.packages if p.needs_downgrade]


@dataclass
class BootstrapConfig:
    description: str
    mirrors: str
    packages: list[Package]


@dataclass
class Services:
    enable: list[str] = field(default_factory=list)
    disable: list[str] = field(default_factory=list)
    mask: list[str] = field(default_factory=list)


@dataclass
class UfwRule:
    port: int
    proto: str
    description: str = ""


@dataclass
class UfwConfig:
    description: str
    allow: list[UfwRule]


@dataclass
class SecureBootConfig:
    description: str
    sign_targets: list[str]


@dataclass
class GitSetting:
    key: str
    value: str


@dataclass
class GitConfig:
    description: str
    settings: list[GitSetting]


@dataclass
class GSchema:
    schema: str
    key: str
    value: str


@dataclass
class Config:
    bootstrap: BootstrapConfig
    groups: dict[str, PackageGroup]
    services: Services
    ufw: UfwConfig
    secureboot: SecureBootConfig
    git: GitConfig
    gschemas: list[GSchema]

    PACMAN_GROUPS: tuple[str, ...] = field(
        default=(
            "niri_core",
            "amd_video_drivers",
            "essential",
            "lazyvim_deps",
            "aur",
        ),
        init=False,
        repr=False,
    )

    def system_packages(self) -> list[str]:
        names: list[str] = []
        for group_name in self.PACMAN_GROUPS:
            group = self.groups.get(group_name)
            if group:
                names.extend(p.name for p in group.regular_packages())
        return names

    def flatpak_packages(self) -> list[Package]:
        group = self.groups.get("flatpak")
        return group.packages if group else []

    def all_downgrade_packages(self) -> list[Package]:
        packages: list[Package] = []
        for group_name in self.PACMAN_GROUPS:
            group = self.groups.get(group_name)
            if group:
                packages.extend(group.downgrade_packages())
        return packages


def load_config(path: Path | None = None) -> Config:
    if path is None:
        path = Path(__file__).parent.parent / "config.toml"

    with path.open("rb") as f:
        data = tomllib.load(f)

    # Parse bootstrap
    bootstrap_data = data.get("bootstrap", {})
    bootstrap_packages = [
        Package(
            name=p["name"],
            description=p.get("description", ""),
        )
        for p in bootstrap_data.get("packages", [])
    ]
    bootstrap = BootstrapConfig(
        description=bootstrap_data.get("description", ""),
        mirrors=bootstrap_data.get("mirrors", ""),
        packages=bootstrap_packages,
    )

    # Parse package groups
    groups: dict[str, PackageGroup] = {}
    for group_name, group_data in data.get("packages", {}).items():
        packages = [
            Package(
                name=p["name"],
                description=p.get("description", ""),
                version=p.get("version", ""),
                env=p.get("env", {}),
                fs=p.get("fs", []),
            )
            for p in group_data.get("packages", [])
        ]
        groups[group_name] = PackageGroup(
            name=group_name,
            description=group_data.get("description", ""),
            packages=packages,
        )

    # Parse services
    services_data = data.get("services", {})
    services = Services(
        enable=services_data.get("enable", []),
        disable=services_data.get("disable", []),
        mask=services_data.get("mask", []),
    )

    # Parse UFW config
    ufw_data = data.get("ufw", {})
    ufw_rules = [
        UfwRule(
            port=rule["port"],
            proto=rule["proto"],
            description=rule.get("description", ""),
        )
        for rule in ufw_data.get("allow", [])
    ]
    ufw = UfwConfig(
        description=ufw_data.get("description", ""),
        allow=ufw_rules,
    )

    # Parse Secure Boot config
    secureboot_data = data.get("secureboot", {})
    secureboot = SecureBootConfig(
        description=secureboot_data.get("description", ""),
        sign_targets=secureboot_data.get("sign_targets", []),
    )

    # Parse Git config
    git_data = data.get("git", {})
    git_settings = [
        GitSetting(
            key=s["key"],
            value=s["value"],
        )
        for s in git_data.get("settings", [])
    ]
    git = GitConfig(
        description=git_data.get("description", ""),
        settings=git_settings,
    )

    # Parse gschemas
    gschemas_data = data.get("gschemas", {})
    gschemas = [
        GSchema(
            schema=g["schema"],
            key=g["key"],
            value=g["value"],
        )
        for g in gschemas_data.get("packages", [])
    ]

    return Config(
        bootstrap=bootstrap,
        groups=groups,
        services=services,
        ufw=ufw,
        secureboot=secureboot,
        git=git,
        gschemas=gschemas,
    )
