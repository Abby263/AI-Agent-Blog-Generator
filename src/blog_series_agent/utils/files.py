"""Filesystem helpers for artifact persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ensure_directory(path: str | Path) -> Path:
    """Ensure a directory exists and return it."""

    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def write_markdown(path: str | Path, content: str) -> Path:
    """Write Markdown content to disk."""

    target = Path(path)
    ensure_directory(target.parent)
    target.write_text(content, encoding="utf-8")
    return target


def write_json(path: str | Path, payload: Any) -> Path:
    """Write JSON content to disk."""

    target = Path(path)
    ensure_directory(target.parent)
    target.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return target


def read_json(path: str | Path) -> Any:
    """Read JSON content from disk."""

    return json.loads(Path(path).read_text(encoding="utf-8"))

