"""
Orchestrator — coordinates Discovery → Analyzer → Planner → Generator.

                 ┌─────────────┐
                 │ Orchestrator │
                 └──────┬──────┘
                        │
              ┌─────────▼─────────┐
              │  Discovery Agent   │  (finds all screens)
              └─────────┬─────────┘
                        │  list[Screen]
              ┌─────────▼─────────┐
              │  Analyzer Agent    │  (parallel fetch per screen)
              └─────────┬─────────┘
                        │  dict[name, DesignSpec]
              ┌─────────▼─────────┐
              │  Planner (tool)    │  (file architecture)
              └─────────┬─────────┘
                        │  list[FileSpec]
              ┌─────────▼─────────┐
              │  Generator Agent   │  (parallel codegen + write)
              └───────────────────┘
"""

from __future__ import annotations

from pathlib import Path

from agents import analyzer, discovery, generator
from tools.arch_tools import plan_architecture


def build_from_design(
    design_url: str,
    output_dir: str,
    framework: str = "flutter",
) -> None:
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"\n  Design-to-Code Agent")
    print(f"  URL       : {design_url}")
    print(f"  Framework : {framework}")
    print(f"  Output    : {output_dir}")
    print(f"  {'─' * 48}\n")

    # 1. Discovery
    screens = discovery.run(design_url)

    # 2. Analysis (parallel)
    specs = analyzer.run(screens)
    design_context = analyzer.to_summary(specs)

    # 3. Architecture planning
    plan = plan_architecture(design_context, framework)

    # 4. Code generation + write (parallel batches)
    written = generator.run(plan, design_context, framework, output_dir)

    print(f"\n  {'─' * 48}")
    print(f"  Done. {len(written)} file(s) written to {output_dir}")
    for path in written:
        print(f"    {path}")
