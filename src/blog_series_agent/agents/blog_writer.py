"""Blog writer agent."""

from __future__ import annotations

from ..config.settings import SeriesRunConfig
from ..schemas.memory import SkillRetrievalResult
from ..schemas.series import BlogResearchPacket, BlogSeriesOutline, BlogSeriesPart
from .base import BaseAgent


class BlogWriterAgent(BaseAgent):
    prompt_name = "blog_writer"
    system_prompt = (
        "You are a senior technical educator writing polished, human, deep, Medium-ready articles."
    )

    def run(
        self,
        config: SeriesRunConfig,
        outline: BlogSeriesOutline,
        part: BlogSeriesPart,
        research: BlogResearchPacket,
        retrieved_guidance: SkillRetrievalResult,
        recent_mistakes_to_avoid: list[str],
    ) -> str:
        series_navigation = "\n".join(
            f"- Part {series_part.part_number}: {series_part.title}"
            + (" (This Post)" if series_part.part_number == part.part_number else "")
            for series_part in outline.parts
        )
        prompt = self.context.prompts.render(
            self.prompt_name,
            topic=config.topic,
            audience=config.target_audience,
            part_number=part.part_number,
            part_title=part.title,
            min_words=config.min_word_count,
            max_words=config.max_word_count,
            series_navigation=series_navigation,
            research_summary=research.summary,
            part_purpose=part.purpose,
            prerequisite_context=part.prerequisite_context or ["- None"],
            key_concepts=part.key_concepts or ["- None"],
            recommended_diagrams=part.recommended_diagrams or ["- None"],
            dependency_context=part.dependencies_on_previous or ["- None"],
            retrieved_guidance=retrieved_guidance.retrieved_guidance or ["- None"],
            recent_mistakes=recent_mistakes_to_avoid or ["- None"],
        )
        return self.context.llm.generate_text(system_prompt=self.system_prompt, user_prompt=prompt)
