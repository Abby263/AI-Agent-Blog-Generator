"""Abstract model interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class BaseLLMClient(ABC):
    """Minimal abstraction around model calls used by agents."""

    @abstractmethod
    def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
    ) -> str:
        """Generate plain text output."""

    @abstractmethod
    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[SchemaT],
    ) -> SchemaT:
        """Generate structured output validated against a Pydantic schema."""

    def generate_with_tools(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        tools: list[Any],
        max_iterations: int = 6,
    ) -> str:
        """
        Run a ReAct tool-calling loop: the model can call any of *tools* to
        gather information, then synthesises a final text response.

        Default implementation falls back to generate_text (no tool use).
        Override in concrete clients that support function-calling.
        """
        return self.generate_text(system_prompt=system_prompt, user_prompt=user_prompt)
