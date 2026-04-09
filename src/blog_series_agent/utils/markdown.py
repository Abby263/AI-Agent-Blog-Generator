"""Markdown normalization helpers."""

from __future__ import annotations


def normalize_markdown_document(markdown: str) -> str:
    """Strip enclosing code fences and surrounding whitespace from model output."""

    text = markdown.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return text
