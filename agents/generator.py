"""Generator agent — produces source code for all files in parallel."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from core.config import MAX_PARALLEL_FILES
from core.models import FileSpec
from tools.code_tools import generate_file, write_file


def run(
    plan: list[FileSpec],
    design_context: str,
    framework: str,
    output_dir: str,
) -> list[str]:
    """
    Generate and write every file in the plan.
    Files are generated in parallel (MAX_PARALLEL_FILES workers).
    Returns a list of absolute paths written to disk.
    """
    print(f"\n  [generator] generating {len(plan)} file(s) in parallel (max {MAX_PARALLEL_FILES} workers)")
    written: list[str] = []
    generated_paths: list[str] = []

    # We generate in batches to keep `already_generated` context meaningful.
    # Batch size = MAX_PARALLEL_FILES so each batch sees previous batches' output.
    for batch_start in range(0, len(plan), MAX_PARALLEL_FILES):
        batch = plan[batch_start : batch_start + MAX_PARALLEL_FILES]
        snapshot = list(generated_paths)  # snapshot before batch

        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_FILES) as pool:
            future_to_spec = {
                pool.submit(generate_file, spec, design_context, framework, snapshot): spec
                for spec in batch
            }
            for future in as_completed(future_to_spec):
                spec = future_to_spec[future]
                try:
                    spec.content = future.result()
                    path = write_file(spec, output_dir)
                    written.append(path)
                    generated_paths.append(spec.path)
                except Exception as exc:
                    print(f"  [generator] ERROR on '{spec.path}': {exc}")

    print(f"\n  [generator] done — {len(written)} file(s) written")
    return written
