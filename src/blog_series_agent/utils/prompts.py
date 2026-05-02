"""Prompt loading utilities."""

from __future__ import annotations

from pathlib import Path
from string import Template


class PromptLoader:
    """Loads prompt templates from disk and renders them with string.Template."""

    def __init__(self, prompt_dir: str | Path | None = None) -> None:
        if prompt_dir is None:
            prompt_dir = Path(__file__).resolve().parents[1] / "prompts"
        self.prompt_dir = Path(prompt_dir)

    def path_for(self, name: str) -> Path:
        return self.prompt_dir / f"{name}.md"

    def load(self, name: str) -> str:
        path = self.path_for(name)
        return path.read_text(encoding="utf-8")

    def render(self, name: str, **context: object) -> str:
        template = Template(self.load(name))
        serialized = {key: self._coerce_value(value) for key, value in context.items()}
        return template.safe_substitute(serialized)

    @staticmethod
    def _coerce_value(value: object) -> str:
        if isinstance(value, list):
            return "\n".join(f"- {item}" for item in value)
        return str(value)

