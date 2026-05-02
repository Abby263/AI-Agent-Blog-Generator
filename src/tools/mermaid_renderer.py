"""Utility helpers to convert Mermaid code blocks in markdown to images."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable, Optional

from src.tools.diagram_generator import DiagramGenerator
from src.utils.logger import get_logger


logger = get_logger()

MERMAID_BLOCK_PATTERN = re.compile(
    r"(?P<meta><!--\s*Diagram\s+(?P<id>[\w-]+)\s*:\s*(?P<description>.*?)\s*-->)?\s*```mermaid\s*(?P<code>.*?)```",
    re.IGNORECASE | re.DOTALL,
)


def render_mermaid_blocks_in_path(
    input_path: Path,
    diagram_generator: Optional[DiagramGenerator] = None,
    dry_run: bool = False
) -> int:
    """Render Mermaid code blocks across a file or directory."""
    generator = diagram_generator or DiagramGenerator()
    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")
    total = 0
    for markdown_file in _iter_markdown_files(input_path):
        total += render_mermaid_blocks_in_file(markdown_file, generator, dry_run=dry_run)
    return total


def render_mermaid_blocks_in_file(
    markdown_file: Path,
    diagram_generator: Optional[DiagramGenerator] = None,
    dry_run: bool = False
) -> int:
    """Render Mermaid code blocks within a single markdown file."""
    generator = diagram_generator or DiagramGenerator()
    if not markdown_file.exists() or markdown_file.suffix.lower() != ".md":
        return 0
    text = markdown_file.read_text(encoding="utf-8")
    replacements = 0
    counter = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal replacements, counter
        counter += 1
        mermaid_code = (match.group("code") or "").strip()
        if not mermaid_code:
            return match.group(0)
        diagram_id = (match.group("id") or f"{markdown_file.stem}_diagram_{counter}").strip()
        description = (match.group("description") or f"{markdown_file.stem} diagram {counter}").strip()
        if dry_run:
            logger.info(
                "[DRY RUN] Would render diagram %s in %s",
                diagram_id,
                markdown_file,
            )
            replacements += 1
            return match.group(0)
        if not generator.is_mermaid_cli_available():
            raise RuntimeError(
                "Mermaid CLI not found. Install '@mermaid-js/mermaid-cli' to render diagrams."
            )
        image_path = generator.generate_diagram(
            mermaid_code=mermaid_code,
            diagram_id=diagram_id,
            description=description,
        )
        if not image_path:
            logger.error("Failed to render diagram %s in %s", diagram_id, markdown_file)
            return match.group(0)
        replacements += 1
        relative_path = _relpath_for_markdown(image_path, markdown_file)
        return f"![{description}]({relative_path})\n"

    new_text = MERMAID_BLOCK_PATTERN.sub(_replace, text)
    if not dry_run and new_text != text and replacements > 0:
        markdown_file.write_text(new_text, encoding="utf-8")
        logger.info("Updated %s (%d diagrams)", markdown_file, replacements)
    return replacements


def _iter_markdown_files(path: Path) -> Iterable[Path]:
    if path.is_file() and path.suffix.lower() == ".md":
        yield path
    elif path.is_dir():
        yield from sorted(path.rglob("*.md"))


def _relpath_for_markdown(image_path: str, markdown_file: Path) -> str:
    relative = os.path.relpath(image_path, start=markdown_file.parent)
    return Path(relative).as_posix()
