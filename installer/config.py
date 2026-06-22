from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast


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
    mirrors: list[str]
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

    PACMAN_CORE_GROUPS: tuple[str, ...] = field(
        default=(
            "niri_core",
            "amd_video_drivers",
            "essential",
            "lazyvim_deps",
        ),
        init=False,
        repr=False,
    )

    def core_packages(self) -> list[str]:
        names: list[str] = []
        for group_name in self.PACMAN_CORE_GROUPS:
            group = self.groups.get(group_name)
            if group:
                names.extend(p.name for p in group.regular_packages())
        return names

    def aur_packages(self) -> list[str]:
        group = self.groups.get("aur")
        if group:
            return [p.name for p in group.regular_packages()]
        return []

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
        data: dict[str, object] = tomllib.load(f)

    # Parse bootstrap
    bootstrap_data = cast("dict[str, object]", data.get("bootstrap", {}))
    bootstrap_packages_raw = cast("list[dict[str, object]]", bootstrap_data.get("packages", []))
    bootstrap_packages = [
        Package(
            name=str(p["name"]),
            description=str(p.get("description", "")),
        )
        for p in bootstrap_packages_raw
    ]
    bootstrap = BootstrapConfig(
        description=str(bootstrap_data.get("description", "")),
        mirrors=cast("list[str]", bootstrap_data.get("mirrors", [])),
        packages=bootstrap_packages,
    )

    # Parse package groups
    groups: dict[str, PackageGroup] = {}
    packages_data_raw = cast("dict[str, dict[str, object]]", data.get("packages", {}))
    for group_name, group_data in packages_data_raw.items():
        group_name_str = str(group_name)
        packages_raw = cast("list[dict[str, object]]", group_data.get("packages", []))
        packages = [
            Package(
                name=str(p["name"]),
                description=str(p.get("description", "")),
                version=str(p.get("version", "")),
                env=cast("dict[str, str]", p.get("env", {})),
                fs=cast("list[str]", p.get("fs", [])),
            )
            for p in packages_raw
        ]
        groups[group_name_str] = PackageGroup(
            name=group_name_str,
            description=str(group_data.get("description", "")),
            packages=packages,
        )

    # Parse services
    services_data = cast("dict[str, object]", data.get("services", {}))
    services = Services(
        enable=cast("list[str]", services_data.get("enable", [])),
        disable=cast("list[str]", services_data.get("disable", [])),
        mask=cast("list[str]", services_data.get("mask", [])),
    )

    # Parse UFW config
    ufw_data = cast("dict[str, object]", data.get("ufw", {}))
    ufw_rules_raw = cast("list[dict[str, object]]", ufw_data.get("allow", []))
    ufw_rules = [
        UfwRule(
            port=cast("int", rule["port"]),
            proto=str(rule["proto"]),
            description=str(rule.get("description", "")),
        )
        for rule in ufw_rules_raw
    ]
    ufw = UfwConfig(
        description=str(ufw_data.get("description", "")),
        allow=ufw_rules,
    )

    # Parse Secure Boot config
    secureboot_data = cast("dict[str, object]", data.get("secureboot", {}))
    secureboot = SecureBootConfig(
        description=str(secureboot_data.get("description", "")),
        sign_targets=cast("list[str]", secureboot_data.get("sign_targets", [])),
    )

    # Parse Git config
    git_data = cast("dict[str, object]", data.get("git", {}))
    git_settings_raw = cast("list[dict[str, object]]", git_data.get("settings", []))
    git_settings = [
        GitSetting(
            key=str(s["key"]),
            value=str(s["value"]),
        )
        for s in git_settings_raw
    ]
    git = GitConfig(
        description=str(git_data.get("description", "")),
        settings=git_settings,
    )

    # Parse gschemas
    gschemas_data = cast("dict[str, object]", data.get("gschemas", {}))
    gschemas_raw = cast("list[dict[str, object]]", gschemas_data.get("packages", []))
    gschemas = [
        GSchema(
            schema=str(g["schema"]),
            key=str(g["key"]),
            value=str(g["value"]),
        )
        for g in gschemas_raw
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
