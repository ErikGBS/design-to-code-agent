"""Analyzer agent — extracts design specs from screens in parallel."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.config import MAX_PARALLEL_SCREENS
from core.models import DesignSpec, Screen
from tools.web_tools import fetch_design


def run(screens: list[Screen]) -> dict[str, DesignSpec]:
    """
    Fetch and analyze all screens in parallel.
    Returns a dict keyed by screen name.
    """
    print(f"\n  [analyzer] fetching {len(screens)} screen(s) in parallel (max {MAX_PARALLEL_SCREENS} workers)")
    results: dict[str, DesignSpec] = {}

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_SCREENS) as pool:
        future_to_screen = {pool.submit(fetch_design, s): s for s in screens}
        for future in as_completed(future_to_screen):
            screen = future_to_screen[future]
            try:
                spec = future.result()
                results[screen.name] = spec
            except Exception as exc:
                print(f"  [analyzer] ERROR on '{screen.name}': {exc}")
                results[screen.name] = DesignSpec(screen=screen, raw=str(exc))

    print(f"  [analyzer] done — {len(results)} spec(s) ready\n")
    return results


def to_summary(specs: dict[str, DesignSpec]) -> str:
    """Serialize all design specs to a JSON string for downstream agents."""
    payload = {}
    for name, spec in specs.items():
        payload[name] = {
            "url": spec.screen.url,
            "components": spec.components,
            "colors": spec.colors,
            "typography": spec.typography,
            "layout": spec.layout,
            "interactions": spec.interactions,
            "raw": spec.raw,
        }
    return json.dumps(payload, ensure_ascii=False, indent=2)
