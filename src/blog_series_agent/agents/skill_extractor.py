"""Skill extraction agent."""

from __future__ import annotations

from ..schemas.memory import SkillExtractionBatch
from .base import BaseAgent


class SkillExtractorAgent(BaseAgent):
    """LLM-based candidate skill extraction from normalized feedback."""

    prompt_name = "skill_extractor"
    system_prompt = (
        "You are distilling repeated editorial feedback into reusable, auditable writing skills. "
        "Return valid structured output only."
    )

    def run(self, normalized_feedback: str) -> SkillExtractionBatch:
        prompt = self.context.prompts.render(self.prompt_name, normalized_feedback=normalized_feedback)
        return self.context.llm.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=prompt,
            schema=SkillExtractionBatch,
        )
