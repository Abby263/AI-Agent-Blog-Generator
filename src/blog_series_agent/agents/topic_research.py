"""Topic research agent."""

from __future__ import annotations

from ..config.settings import SeriesRunConfig
from ..schemas.series import TopicResearchDossier
from .base import BaseAgent


class TopicResearchAgent(BaseAgent):
    prompt_name = "topic_research"
    system_prompt = (
        "You are a senior technical research strategist. Produce a precise research dossier and "
        "return valid structured output only."
    )

    def run(self, config: SeriesRunConfig) -> TopicResearchDossier:
        prompt = self.context.prompts.render(
            self.prompt_name,
            topic=config.topic,
            audience=config.target_audience,
            num_parts=config.num_parts,
        )
        return self.context.llm.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=prompt,
            schema=TopicResearchDossier,
        )

