"""Architecture planning tool."""

from __future__ import annotations

import json
import re

import anthropic

from core.config import ANTHROPIC_API_KEY, MODEL
from core.models import FileSpec
from prompts.agent_prompts import PLANNER_PROMPT
from prompts.expert_prompts import EXPERT_PROMPTS

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def plan_architecture(design_summary: str, framework: str) -> list[FileSpec]:
    """Produce the ordered list of files to generate for the project."""
    print(f"  [planner] planning {framework} architecture...")
    expert_prompt = EXPERT_PROMPTS.get(framework, EXPERT_PROMPTS["flutter"])

    response = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=[
            {"type": "text", "text": expert_prompt, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": PLANNER_PROMPT},
        ],
        messages=[{
            "role": "user",
            "content": (
                f"Design analysis (all screens):\n{design_summary}\n\n"
                f"Target framework: {framework}\n"
                "Return the complete file list."
            ),
        }],
    )

    raw = _text(response)
    try:
        data = json.loads(_strip_fences(raw))
        files = [FileSpec(path=f["path"], purpose=f.get("purpose", "")) for f in data]
    except Exception:
        files = [FileSpec(path="lib/main.dart", purpose="App entry point")]

    print(f"  [planner] {len(files)} file(s) planned")
    return files


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
