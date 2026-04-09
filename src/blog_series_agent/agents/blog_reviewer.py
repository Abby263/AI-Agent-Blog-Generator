"""Blog reviewer agent."""

from __future__ import annotations

from ..config.settings import SeriesRunConfig
from ..schemas.memory import SkillRetrievalResult
from ..schemas.review import BlogReviewReport
from ..schemas.series import BlogSeriesPart
from .base import BaseAgent


class BlogReviewerAgent(BaseAgent):
    prompt_name = "reviewer"
    system_prompt = (
        "You are a strict technical content reviewer. Score honestly and return valid structured output only."
    )

    def run(
        self,
        config: SeriesRunConfig,
        part: BlogSeriesPart,
        draft_markdown: str,
        retrieved_guidance: SkillRetrievalResult,
        lint_summary: str,
    ) -> BlogReviewReport:
        prompt = self.context.prompts.render(
            self.prompt_name,
            topic=config.topic,
            audience=config.target_audience,
            part_number=part.part_number,
            part_title=part.title,
            min_words=config.min_word_count,
            max_words=config.max_word_count,
            draft_content=draft_markdown,
            active_skills=retrieved_guidance.retrieved_guidance or ["- None"],
            active_skill_ids=retrieved_guidance.retrieved_skill_ids or ["- None"],
            lint_findings=lint_summary,
        )
        report = self.context.llm.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=prompt,
            schema=BlogReviewReport,
        )
        if not report.slug:
            report.slug = part.slug
        if not report.title:
            report.title = part.title
        if not report.part_number:
            report.part_number = part.part_number
        return report
