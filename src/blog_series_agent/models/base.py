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

    def as_chat_model(self) -> Any | None:
        """Return the underlying LangChain chat model when one is available."""

        return None
