"""Blog improver agent."""

from __future__ import annotations

from ..config.settings import SeriesRunConfig
from ..schemas.memory import SkillRetrievalResult
from ..schemas.review import BlogReviewReport
from ..schemas.series import BlogSeriesPart
from .base import BaseAgent


class BlogImproverAgent(BaseAgent):
    prompt_name = "improver"
    system_prompt = (
        "You are a senior technical editor. Improve the article without making it robotic or shallow."
    )

    def run(
        self,
        config: SeriesRunConfig,
        part: BlogSeriesPart,
        draft_markdown: str,
        review_report: BlogReviewReport,
        retrieved_guidance: SkillRetrievalResult,
        lint_summary: str,
        approval_comments: str = "",
    ) -> str:
        review_summary = "\n".join(
            [
                review_report.summary,
                "Priority fixes:",
                *[f"- {item}" for item in review_report.priority_fixes],
                "Approval comments:",
                approval_comments or "- None",
            ]
        )
        prompt = self.context.prompts.render(
            self.prompt_name,
            topic=config.topic,
            audience=config.target_audience,
            part_number=part.part_number,
            part_title=part.title,
            min_words=config.min_word_count,
            max_words=config.max_word_count,
            review_summary=review_summary,
            draft_content=draft_markdown,
            retrieved_guidance=retrieved_guidance.retrieved_guidance or ["- None"],
            violated_skills=review_report.skills_violated or ["- None"],
            lint_findings=lint_summary,
            deepagent_guidance=self.deepagent_guidance(stage="final", subagent_name="writer"),
        )
        return self.context.llm.generate_text(
            system_prompt=self.system_prompt_with_deepagent(stage="final", subagent_name="writer"),
            user_prompt=prompt,
        )
