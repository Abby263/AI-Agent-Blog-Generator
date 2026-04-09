"""Per-part blog research agent."""

from __future__ import annotations

from ..config.settings import SeriesRunConfig
from ..schemas.series import BlogResearchPacket, BlogSeriesOutline, BlogSeriesPart
from .base import BaseAgent


class BlogResearchAgent(BaseAgent):
    prompt_name = "blog_research"
    system_prompt = (
        "You are a technical content research specialist. Produce targeted, practical research "
        "for one blog chapter and return valid structured output only."
    )

    def run(
        self,
        config: SeriesRunConfig,
        outline: BlogSeriesOutline,
        part: BlogSeriesPart,
    ) -> BlogResearchPacket:
        prompt = self.context.prompts.render(
            self.prompt_name,
            topic=config.topic,
            audience=config.target_audience,
            part_number=part.part_number,
            part_title=part.title,
            part_purpose=part.purpose,
            series_context=outline.narrative_arc,
        )
        return self.context.llm.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=prompt,
            schema=BlogResearchPacket,
        )

