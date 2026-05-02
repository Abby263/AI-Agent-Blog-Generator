#!/usr/bin/env python3
"""Render Mermaid code blocks in generated blogs and replace them with images."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is importable when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.tools.diagram_generator import DiagramGenerator
from src.tools.mermaid_renderer import render_mermaid_blocks_in_path
from src.utils.logger import setup_logger

logger = setup_logger("mermaid_renderer")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Convert Mermaid code blocks inside markdown files to PNG images",
    )
    parser.add_argument(
        "--input",
        default="output",
        help="Markdown file or directory to scan (default: output)",
    )
    parser.add_argument(
        "--images-dir",
        help="Override image output directory (default: diagram agent config)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report which diagrams would be rendered without modifying files",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    input_path = Path(args.input).resolve()

    if not input_path.exists():
        raise SystemExit(f"Input path does not exist: {input_path}")

    diagram_generator = DiagramGenerator()
    if args.images_dir:
        diagram_generator.output_dir = Path(args.images_dir)
        diagram_generator.output_dir.mkdir(parents=True, exist_ok=True)

    if not diagram_generator.is_mermaid_cli_available():
        logger.error(
            "Mermaid CLI not found. Install it with 'npm install -g @mermaid-js/mermaid-cli'."
        )
        raise SystemExit(1)

    total_diagrams = render_mermaid_blocks_in_path(
        input_path,
        diagram_generator=diagram_generator,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        logger.info("Dry run complete. %d Mermaid blocks detected.", total_diagrams)
    else:
        logger.info("Finished rendering %d diagrams.", total_diagrams)


if __name__ == "__main__":
    main()
