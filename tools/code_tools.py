"""Code generation and file writing tools."""

from __future__ import annotations

from pathlib import Path

import anthropic

from core.config import ANTHROPIC_API_KEY, MODEL
from core.models import FileSpec
from prompts.expert_prompts import EXPERT_PROMPTS

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def generate_file(spec: FileSpec, design_context: str, framework: str, generated_paths: list[str]) -> str:
    """Generate source code for a single file using the cached expert prompt."""
    print(f"  [generator] {spec.path}")
    expert_prompt = EXPERT_PROMPTS.get(framework, EXPERT_PROMPTS["flutter"])

    already = "\n".join(f"  - {p}" for p in generated_paths[-20:]) or "  (none yet)"

    response = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system=[{"type": "text", "text": expert_prompt, "cache_control": {"type": "ephemeral"}}],
        messages=[{
            "role": "user",
            "content": (
                f"Generate file: `{spec.path}`\n"
                f"Purpose: {spec.purpose}\n\n"
                f"Design context (all screens):\n{design_context}\n\n"
                f"Already generated:\n{already}\n\n"
                "Return ONLY raw source code — no markdown, no explanations."
            ),
        }],
    )

    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            return block.text.strip()
    return ""


def write_file(spec: FileSpec, output_dir: str) -> str:
    """Write a FileSpec (with content) to disk. Returns the absolute path."""
    full_path = Path(output_dir) / spec.path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(spec.content, encoding="utf-8")
    return str(full_path)
