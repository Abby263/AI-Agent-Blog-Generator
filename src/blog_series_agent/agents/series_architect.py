"""Series outline agent."""

from __future__ import annotations

from ..config.settings import SeriesRunConfig
from ..schemas.series import BlogSeriesOutline, TopicResearchDossier
from .base import BaseAgent


class SeriesArchitectAgent(BaseAgent):
    prompt_name = "series_architect"
    system_prompt = (
        "You are a technical curriculum architect designing a cohesive book-like blog series. "
        "Return valid structured output only."
    )

    def run(self, config: SeriesRunConfig, dossier: TopicResearchDossier) -> BlogSeriesOutline:
        prompt = self.context.prompts.render(
            self.prompt_name,
            topic=config.topic,
            audience=config.target_audience,
            num_parts=config.num_parts,
            research_summary=dossier.positioning_summary,
            deepagent_guidance=self.deepagent_guidance(stage="series_architect", subagent_name="writer"),
        )
        return self.context.llm.generate_structured(
            system_prompt=self.system_prompt_with_deepagent(stage="series_architect", subagent_name="writer"),
            user_prompt=prompt,
            schema=BlogSeriesOutline,
        )
