"""
Tool definitions for the Design-to-Code agent.
Each function decorated with @beta_tool becomes an agent-callable tool.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import anthropic
from anthropic import beta_tool

from prompts.expert_prompts import EXPERT_PROMPTS

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


# ---------------------------------------------------------------------------
# Tool 1 — discover_screens
# ---------------------------------------------------------------------------

@beta_tool
def discover_screens(base_url: str) -> str:
    """
    Crawl a Figma site (or any design-preview site) and return every distinct
    page/screen URL found, plus a one-sentence description of each.

    Returns JSON list:
    [{"url": "...", "name": "...", "description": "..."}, ...]
    """
    print(f"  [discover_screens] crawling {base_url}")
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        tools=[{"type": "web_fetch_20260209", "name": "web_fetch"}],
        messages=[{
            "role": "user",
            "content": (
                f"Fetch the URL {base_url!r} and analyze the page.\n\n"
                "Your goal: find ALL distinct screens / pages in this design site.\n"
                "Look for:\n"
                "  - Navigation links / sidebar links pointing to sub-pages\n"
                "  - Prototype links between frames (Figma preview arrows)\n"
                "  - Tabs or step indicators that reveal other screens\n\n"
                "For each screen found, return a JSON array (no markdown, raw JSON):\n"
                '[\n'
                '  {"url": "<full url>", "name": "<screen name>", "description": "<what this screen is>"}\n'
                ']\n\n'
                "Always include the base URL itself as the first entry.\n"
                "If you cannot navigate further, just return the single base URL entry."
            ),
        }],
    )

    raw = _extract_text(response)
    try:
        screens = json.loads(_extract_json(raw))
        if not isinstance(screens, list):
            raise ValueError("not a list")
    except Exception:
        screens = [{"url": base_url, "name": "Main", "description": "Main screen"}]

    print(f"  [discover_screens] found {len(screens)} screen(s): {[s.get('name') for s in screens]}")
    return json.dumps(screens, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool 2 — fetch_design
# ---------------------------------------------------------------------------

@beta_tool
def fetch_design(screens_json: str) -> str:
    """
    Given the JSON list produced by discover_screens, fetch every screen and
    extract structured design information (components, colors, typography, layout,
    interactions).

    Returns a JSON object keyed by screen name:
    {
      "<screen_name>": {
        "url": "...",
        "components": [...],
        "colors": [...],
        "typography": {...},
        "layout": "...",
        "interactions": [...]
      },
      ...
    }
    """
    screens: list[dict] = json.loads(screens_json)
    all_designs: dict[str, dict] = {}

    for screen in screens:
        url = screen["url"]
        name = screen.get("name", url)
        print(f"  [fetch_design] extracting '{name}' from {url}")

        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=6000,
            tools=[{"type": "web_fetch_20260209", "name": "web_fetch"}],
            messages=[{
                "role": "user",
                "content": (
                    f"Fetch {url!r} and extract a detailed design specification for the screen called {name!r}.\n\n"
                    "Return ONLY raw JSON (no markdown fences) with exactly these keys:\n"
                    "{\n"
                    '  "components": [\n'
                    '    {"name": "...", "type": "button|input|card|list|navbar|...", "properties": {...}}\n'
                    "  ],\n"
                    '  "colors": ["#RRGGBB", ...],\n'
                    '  "typography": {"heading": "...", "body": "...", "caption": "..."},\n'
                    '  "layout": "description of the overall layout",\n'
                    '  "interactions": ["user taps X → navigates to Y", ...]\n'
                    "}"
                ),
            }],
        )

        raw = _extract_text(response)
        try:
            design = json.loads(_extract_json(raw))
        except Exception:
            design = {"raw": raw}

        all_designs[name] = {"url": url, **design}

    print(f"  [fetch_design] done — {len(all_designs)} screen(s) analyzed")
    return json.dumps(all_designs, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool 3 — plan_architecture
# ---------------------------------------------------------------------------

@beta_tool
def plan_architecture(design_analysis: str, target_framework: str) -> str:
    """
    Given the full multi-screen design analysis and target framework, produce a
    complete file architecture plan.

    Returns a JSON array:
    [
      {"path": "lib/main.dart", "purpose": "App entry point"},
      ...
    ]
    """
    print(f"  [plan_architecture] planning {target_framework} project...")
    expert_prompt = EXPERT_PROMPTS.get(target_framework, EXPERT_PROMPTS["flutter"])

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=8000,
        system=[
            {
                "type": "text",
                "text": expert_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{
            "role": "user",
            "content": (
                f"Based on this multi-screen design analysis:\n\n{design_analysis}\n\n"
                f"Create a complete file architecture plan for a {target_framework} project.\n\n"
                "Rules:\n"
                "- One feature folder per screen (use the screen name, snake_case)\n"
                "- Include all necessary files: pages, widgets, BLoC/store, entities, repos, usecases, router, DI\n"
                "- Include shared core files (theme, constants, shared widgets)\n"
                "- Order files from foundation to UI (core first, then features)\n\n"
                "Return ONLY a raw JSON array (no markdown):\n"
                '[\n'
                '  {"path": "lib/main.dart", "purpose": "App entry, runs the app"},\n'
                "  ...\n"
                "]"
            ),
        }],
    )

    raw = _extract_text(response)
    try:
        plan = json.loads(_extract_json(raw))
    except Exception:
        plan = [{"path": "lib/main.dart", "purpose": "App entry point"}]

    print(f"  [plan_architecture] {len(plan)} file(s) planned")
    return json.dumps(plan, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool 4 — generate_file
# ---------------------------------------------------------------------------

@beta_tool
def generate_file(
    file_path: str,
    file_purpose: str,
    design_context: str,
    target_framework: str,
    already_generated: str = "[]",
) -> str:
    """
    Generate the full source code for a single file using the cached expert
    prompt and the complete design context.

    Returns the raw source code (string).
    """
    print(f"  [generate_file] {file_path}")
    expert_prompt = EXPERT_PROMPTS.get(target_framework, EXPERT_PROMPTS["flutter"])
    generated_so_far: list[str] = json.loads(already_generated)

    generated_summary = (
        "\n".join(f"  - {p}" for p in generated_so_far[-20:])
        if generated_so_far
        else "  (none yet)"
    )

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system=[
            {
                "type": "text",
                "text": expert_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{
            "role": "user",
            "content": (
                f"Generate the file: `{file_path}`\n"
                f"Purpose: {file_purpose}\n\n"
                "Full multi-screen design context:\n"
                f"{design_context}\n\n"
                "Files already generated (for import consistency):\n"
                f"{generated_summary}\n\n"
                "Output ONLY the raw source code for this file. No explanations, no markdown fences."
            ),
        }],
    )

    code = ""
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            code = block.text
            break

    return code.strip()


# ---------------------------------------------------------------------------
# Tool 5 — write_file
# ---------------------------------------------------------------------------

@beta_tool
def write_file(path: str, content: str, output_dir: str) -> str:
    """
    Write generated source code to the output directory.
    Creates any missing parent directories.
    Returns the absolute path written.
    """
    full_path = Path(output_dir) / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    print(f"  [write_file] {full_path}")
    return str(full_path)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_text(response: anthropic.types.Message) -> str:
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            return block.text
    return ""


def _extract_json(text: str) -> str:
    """Strip markdown fences and return the inner JSON string."""
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text.strip(), flags=re.MULTILINE)
    return text.strip()
