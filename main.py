"""CLI entry point for the Design-to-Code agent."""

from __future__ import annotations

import argparse
import sys

from agent import build_from_design

SUPPORTED_FRAMEWORKS = ["flutter", "react", "nextjs", "vue", "angular"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Design-to-Code Agent — converts a design URL into a full project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Flutter project from a Figma site (entire flow)
  python main.py https://sway-quest-11958890.figma.site/dashboard ./output/my_app

  # Next.js project
  python main.py https://mydesign.figma.site ./output/my_web --framework nextjs

  # React project
  python main.py https://prototype.figma.com/... ./output/my_react --framework react
""",
    )
    parser.add_argument("url", help="Design site URL (Figma, etc.)")
    parser.add_argument("output_dir", help="Directory to write generated project into")
    parser.add_argument(
        "--framework",
        choices=SUPPORTED_FRAMEWORKS,
        default="flutter",
        help=f"Target framework (default: flutter). Options: {', '.join(SUPPORTED_FRAMEWORKS)}",
    )

    args = parser.parse_args()

    try:
        build_from_design(
            design_url=args.url,
            output_dir=args.output_dir,
            target_framework=args.framework,
        )
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)
    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
