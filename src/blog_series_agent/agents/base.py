"""Shared agent base classes."""

from __future__ import annotations

from dataclasses import dataclass

from ..models.base import BaseLLMClient
from ..utils.prompts import PromptLoader


@dataclass(slots=True)
class AgentContext:
    """Shared dependencies passed to agents."""

    llm: BaseLLMClient
    prompts: PromptLoader


class BaseAgent:
    """Small base class for prompt-driven agents."""

    prompt_name: str = ""
    system_prompt: str = "You are a careful technical content workflow agent."

    def __init__(self, context: AgentContext) -> None:
        self.context = context

