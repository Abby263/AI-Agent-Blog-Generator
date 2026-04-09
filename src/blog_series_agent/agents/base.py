"""Shared agent base classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..models.base import BaseLLMClient
from ..utils.prompts import PromptLoader

if TYPE_CHECKING:
    from ..services.research_tools import ResearchToolkit


@dataclass(slots=True)
class AgentContext:
    """Shared dependencies passed to agents."""

    llm: BaseLLMClient
    prompts: PromptLoader
    research_toolkit: "ResearchToolkit | None" = field(default=None)


class BaseAgent:
    """Small base class for prompt-driven agents."""

    prompt_name: str = ""
    system_prompt: str = "You are a careful technical content workflow agent."

    def __init__(self, context: AgentContext) -> None:
        self.context = context

