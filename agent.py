"""
Design-to-Code Agent — orchestrator.

Flow:
  1. discover_screens  — find ALL pages/screens in the design URL
  2. fetch_design      — extract design spec for every screen
  3. plan_architecture — produce the full file list for the target framework
  4. generate_file     — generate code for each file (with cached expert prompt)
  5. write_file        — persist each file to the output directory

Handles the ENTIRE multi-screen flow, not just a single page.
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import anthropic

from tools import discover_screens, fetch_design, generate_file, plan_architecture, write_file

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


ORCHESTRATOR_SYSTEM = textwrap.dedent("""\
    You are an expert software architect orchestrating a Design-to-Code pipeline.
    Your job is to convert a design URL into a complete, production-quality project.
    Always follow the steps in order, use ALL the tools provided, and do not stop
    until every file in the architecture plan has been generated and written.
""")


def build_from_design(
    design_url: str,
    output_dir: str,
    target_framework: str = "flutter",
) -> None:
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"\n  Design-to-Code Agent starting")
    print(f"    URL       : {design_url}")
    print(f"    Framework : {target_framework}")
    print(f"    Output    : {output_dir}\n")

    user_message = textwrap.dedent(f"""\
        Build a complete {target_framework} project from this design: {design_url}
        Save all generated files to the output directory: {output_dir}

        Follow these steps IN ORDER:

        STEP 1 — Call discover_screens(base_url="{design_url}")
          Find every distinct screen / page in the design site.

        STEP 2 — Call fetch_design(screens_json=<result from step 1>)
          Extract the full design specification for EVERY screen.

        STEP 3 — Call plan_architecture(
            design_analysis=<result from step 2>,
            target_framework="{target_framework}"
          )
          Get the complete list of files to generate.

        STEP 4 — For EACH file in the plan, call:
          a. generate_file(
               file_path=<path>,
               file_purpose=<purpose>,
               design_context=<result from step 2>,
               target_framework="{target_framework}",
               already_generated=<JSON list of paths already written so far>
             )
          b. write_file(path=<file_path>, content=<code>, output_dir="{output_dir}")

        Do NOT stop until every file in the plan is generated and written.
        When done, list all files created.
    """)

    runner = client.beta.messages.tool_runner(
        model="claude-opus-4-7",
        max_tokens=64000,
        thinking={"type": "adaptive"},
        system=ORCHESTRATOR_SYSTEM,
        tools=[discover_screens, fetch_design, plan_architecture, generate_file, write_file],
        messages=[{"role": "user", "content": user_message}],
    )

    final_message = runner.until_done()

    print("\n  Agent finished.\n")
    for block in final_message.content:
        if hasattr(block, "type") and block.type == "text":
            print(block.text)
            break
