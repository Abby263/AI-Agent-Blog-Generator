"""Shared agent base classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..models.base import BaseLLMClient
from ..utils.prompts import PromptLoader

if TYPE_CHECKING:
    from ..services.deepagent_profile import DeepAgentProfile
    from ..services.research_tools import ResearchToolkit


@dataclass(slots=True)
class AgentContext:
    """Shared dependencies passed to agents."""

    llm: BaseLLMClient
    prompts: PromptLoader
    research_toolkit: "ResearchToolkit | None" = field(default=None)
    deepagent_profile: "DeepAgentProfile | None" = field(default=None)


class BaseAgent:
    """Small base class for prompt-driven agents."""

    prompt_name: str = ""
    system_prompt: str = "You are a careful technical content workflow agent."

    def __init__(self, context: AgentContext) -> None:
        self.context = context

    def deepagent_guidance(self, *, stage: str, subagent_name: str | None = None) -> str:
        """Return explicit DeepAgents-style memory/skill guidance for a stage."""
        if self.context.deepagent_profile is None:
            return "No DeepAgent filesystem profile loaded."
        return self.context.deepagent_profile.guidance_for(stage=stage, subagent_name=subagent_name)

    def system_prompt_with_deepagent(
        self,
        *,
        stage: str,
        subagent_name: str | None = None,
        base_prompt: str | None = None,
    ) -> str:
        """Append visible DeepAgents profile guidance to a system prompt."""
        prompt = base_prompt or self.system_prompt
        return "\n\n".join(
            [
                prompt.strip(),
                "## DeepAgent Filesystem Profile",
                self.deepagent_guidance(stage=stage, subagent_name=subagent_name),
            ]
        )
