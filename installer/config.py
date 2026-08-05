from __future__ import annotations

import tomllib
import typing
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path


@dataclass
class Package:
    name: str
    description: str = ""
    version: str = ""
    env: dict[str, str] = field(default_factory=dict)
    fs: list[str] = field(default_factory=list)
    devices: list[str] = field(default_factory=list)

    @property
    def needs_downgrade(self) -> bool:
        return bool(self.version)

    @property
    def downgrade_target(self) -> str:
        return f"{self.name}{self.version}"


@dataclass
class PackageGroup:
    name: str
    description: str = ""
    packages: list[Package] = field(default_factory=list)

    def regular_packages(self) -> list[Package]:
        return [p for p in self.packages if not p.needs_downgrade]

    def downgrade_packages(self) -> list[Package]:
        return [p for p in self.packages if p.needs_downgrade]


@dataclass
class BootstrapConfig:
    description: str = ""
    mirrors: list[str] = field(default_factory=list)
    packages: list[Package] = field(default_factory=list)


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
    description: str = ""
    allow: list[UfwRule] = field(default_factory=list)


@dataclass
class SecureBootConfig:
    description: str = ""
    sign_targets: list[str] = field(default_factory=list)


@dataclass
class LocaleConfig:
    description: str = ""
    gen: list[str] = field(default_factory=list)
    conf: list[str] = field(default_factory=list)


@dataclass
class GitSetting:
    key: str
    value: str


@dataclass
class GitConfig:
    description: str = ""
    settings: list[GitSetting] = field(default_factory=list)


@dataclass
class GSchema:
    schema: str
    key: str
    value: str


@dataclass
class Config:
    bootstrap: BootstrapConfig = field(default_factory=BootstrapConfig)
    groups: dict[str, PackageGroup] = field(default_factory=dict)
    services: Services = field(default_factory=Services)
    ufw: UfwConfig = field(default_factory=UfwConfig)
    secureboot: SecureBootConfig = field(default_factory=SecureBootConfig)
    locale: LocaleConfig = field(default_factory=LocaleConfig)
    git: GitConfig = field(default_factory=GitConfig)
    gschemas: list[GSchema] = field(default_factory=list)

    def core_packages(self) -> list[str]:
        names: list[str] = []
        for group_name, group in self.groups.items():
            if group_name not in ("aur", "flatpak"):
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
        for group_name, group in self.groups.items():
            if group_name != "flatpak":
                packages.extend(group.downgrade_packages())
        return packages


class _FieldProtocol(typing.Protocol):
    name: str


def _parse(cls: object, data: object) -> object:
    get_origin_fn = typing.cast(typing.Callable[[object], object | None], typing.get_origin)
    origin = get_origin_fn(cls)
    if origin is None:
        origin = cls

    if is_dataclass(origin):
        origin_type = typing.cast(type[object], origin)
        kwargs: dict[str, object] = {}

        get_hints_fn = typing.cast(
            typing.Callable[[type[object]], dict[str, object]], typing.get_type_hints
        )
        hints = get_hints_fn(origin_type)

        get_fields_fn = typing.cast(
            typing.Callable[[type[object]], tuple[_FieldProtocol, ...]], fields
        )
        for f in get_fields_fn(origin_type):
            if isinstance(data, dict):
                cast_data = typing.cast(dict[str, object], data)
                if f.name in cast_data:
                    field_cls = hints.get(f.name, object)
                    kwargs[f.name] = _parse(field_cls, cast_data[f.name])

        constructor = typing.cast(typing.Callable[..., object], origin_type)
        return constructor(**kwargs)

    get_args_fn = typing.cast(typing.Callable[[object], tuple[object, ...]], typing.get_args)

    if origin is list and isinstance(data, list):
        args = get_args_fn(cls)
        if args:
            list_data = typing.cast(list[object], data)
            result_list: list[object] = []
            for item in list_data:
                result_list.append(_parse(args[0], item))
            return result_list
        return typing.cast(object, data)

    if origin is dict and isinstance(data, dict):
        args = get_args_fn(cls)
        if len(args) == 2:
            dict_data = typing.cast(dict[object, object], data)
            result_dict: dict[object, object] = {}
            for k, v in dict_data.items():
                result_dict[k] = _parse(args[1], v)
            return result_dict
        return typing.cast(object, data)

    return data


def load_config(path: Path | None = None) -> Config:
    if path is None:
        path = Path(__file__).parent.parent / "config.toml"

    load_fn = typing.cast(typing.Callable[[typing.BinaryIO], dict[str, object]], tomllib.load)
    with path.open("rb") as f:
        data = load_fn(f)

    groups_data = data.pop("packages", {})
    if isinstance(groups_data, dict):
        groups_dict = typing.cast(dict[str, object], groups_data)
        for name, group in groups_dict.items():
            if isinstance(group, dict):
                typing.cast(dict[str, object], group)["name"] = name
        data["groups"] = groups_dict

    gschemas_data = data.get("gschemas")
    if isinstance(gschemas_data, dict):
        data["gschemas"] = typing.cast(dict[str, object], gschemas_data).get("packages", [])

    result = _parse(Config, data)
    return typing.cast(Config, result)
