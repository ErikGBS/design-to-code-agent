"""CLI entry point for the Design-to-Code agent."""

from __future__ import annotations

import argparse
import sys

from agents.orchestrator import build_from_design

SUPPORTED_FRAMEWORKS = ["flutter", "react", "nextjs", "vue", "angular"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Design-to-Code Agent — converts a design URL into a full project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py https://figma.site/my-app ./output/my_app
  python main.py https://figma.site/my-app ./output/my_web --framework nextjs
  python main.py https://figma.site/my-app ./output/my_react --framework react
""",
    )
    parser.add_argument("url", help="Design site URL (Figma, etc.)")
    parser.add_argument("output_dir", help="Directory to write generated project into")
    parser.add_argument(
        "--framework",
        choices=SUPPORTED_FRAMEWORKS,
        default="flutter",
        help=f"Target framework (default: flutter)",
    )
    args = parser.parse_args()

    try:
        build_from_design(
            design_url=args.url,
            output_dir=args.output_dir,
            framework=args.framework,
        )
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
