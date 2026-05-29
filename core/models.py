from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Screen:
    url: str
    name: str
    description: str = ""


@dataclass
class DesignSpec:
    screen: Screen
    components: list[dict] = field(default_factory=list)
    colors: list[str] = field(default_factory=list)
    typography: dict = field(default_factory=dict)
    layout: str = ""
    interactions: list[str] = field(default_factory=list)
    raw: str = ""


@dataclass
class FileSpec:
    path: str
    purpose: str
    content: str = ""
