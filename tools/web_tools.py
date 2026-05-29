"""Web tools: screen discovery and design extraction via web_fetch."""

from __future__ import annotations

import json
import re

import anthropic

from core.config import ANTHROPIC_API_KEY, MODEL
from core.models import DesignSpec, Screen
from prompts.agent_prompts import ANALYZER_PROMPT, DISCOVERY_PROMPT

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
WEB_FETCH_TOOL = {"type": "web_fetch_20260209", "name": "web_fetch"}


def discover_screens(base_url: str) -> list[Screen]:
    """Crawl the design site and return all distinct screens."""
    print(f"  [discovery] crawling {base_url}")
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=DISCOVERY_PROMPT,
        tools=[WEB_FETCH_TOOL],
        messages=[{"role": "user", "content": f"Find all screens at: {base_url}"}],
    )
    raw = _text(response)
    try:
        data = json.loads(_strip_fences(raw))
        screens = [Screen(**s) for s in data if isinstance(s, dict)]
    except Exception:
        screens = [Screen(url=base_url, name="Main", description="Main screen")]

    print(f"  [discovery] {len(screens)} screen(s): {[s.name for s in screens]}")
    return screens


def fetch_design(screen: Screen) -> DesignSpec:
    """Fetch one screen and extract its design specification."""
    print(f"  [analyzer] extracting '{screen.name}'")
    response = client.messages.create(
        model=MODEL,
        max_tokens=6000,
        system=ANALYZER_PROMPT,
        tools=[WEB_FETCH_TOOL],
        messages=[{"role": "user", "content": f"Analyze this screen: {screen.url}"}],
    )
    raw = _text(response)
    try:
        data = json.loads(_strip_fences(raw))
        return DesignSpec(
            screen=screen,
            components=data.get("components", []),
            colors=data.get("colors", []),
            typography=data.get("typography", {}),
            layout=data.get("layout", ""),
            interactions=data.get("interactions", []),
        )
    except Exception:
        return DesignSpec(screen=screen, raw=raw)


# ---------------------------------------------------------------------------

def _text(response: anthropic.types.Message) -> str:
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            return block.text
    return ""


def _strip_fences(text: str) -> str:
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text.strip(), flags=re.MULTILINE)
    return text.strip()
