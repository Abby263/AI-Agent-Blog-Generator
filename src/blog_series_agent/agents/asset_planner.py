"""Asset planning agent."""

from __future__ import annotations

from ..config.settings import SeriesRunConfig
from ..schemas.series import AssetPlan, BlogSeriesPart
from .base import BaseAgent


class AssetPlannerAgent(BaseAgent):
    prompt_name = "asset_planner"
    system_prompt = (
        "You are a technical visualization planner. Return valid structured output only."
    )

    def run(self, config: SeriesRunConfig, part: BlogSeriesPart, final_markdown: str) -> AssetPlan:
        prompt = self.context.prompts.render(
            self.prompt_name,
            topic=config.topic,
            part_number=part.part_number,
            part_title=part.title,
            final_content=final_markdown,
        )
        return self.context.llm.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=prompt,
            schema=AssetPlan,
        )

