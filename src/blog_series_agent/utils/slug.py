"""Slug and file naming helpers."""

from __future__ import annotations

import re


def slugify(value: str) -> str:
    """Return a filesystem-friendly slug."""

    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-{2,}", "-", value).strip("-")


def to_part_filename(part_number: int, slug: str, suffix: str = "", extension: str = "md") -> str:
    """Build a standard part filename."""

    stem = f"Part-{part_number}-{slug}"
    if suffix:
        stem = f"{stem}-{suffix}"
    return f"{stem}.{extension}"

