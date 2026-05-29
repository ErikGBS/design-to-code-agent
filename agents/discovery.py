"""Discovery agent — finds all screens in a design site."""

from __future__ import annotations

from core.models import Screen
from tools.web_tools import discover_screens


def run(base_url: str) -> list[Screen]:
    """Entry point: returns every screen found in the design site."""
    return discover_screens(base_url)
