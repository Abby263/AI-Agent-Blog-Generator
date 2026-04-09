"""Per-blog chapter planning agent."""

from __future__ import annotations

from ..config.settings import SeriesRunConfig
from ..schemas.memory import SkillRetrievalResult
from ..schemas.series import BlogChapterPlan, BlogResearchPacket, BlogSectionPlan, BlogSeriesOutline, BlogSeriesPart
from .base import BaseAgent


class BlogOutlineAgent(BaseAgent):
    MANDATORY_HEADINGS = [
        "Introduction",
        "Mental Model / Simplification Layer",
        "Problem Framing",
        "Detailed Core Sections",
        "System / Architecture Thinking",
        "Real-world Examples",
        "Tradeoffs / Failure Cases",
        "How This Works in Modern Systems",
        "Synthesis / If You Step Back",
        "Key Takeaways",
        "Test Your Learning",
        "Conclusion",
        "References",
    ]

    prompt_name = "blog_outline"
    system_prompt = (
        "You are a technical book editor planning one blog chapter. Return valid structured output only."
    )

    def run(
        self,
        config: SeriesRunConfig,
        outline: BlogSeriesOutline,
        part: BlogSeriesPart,
        research: BlogResearchPacket,
        retrieved_guidance: SkillRetrievalResult,
    ) -> BlogChapterPlan:
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
            part_purpose=part.purpose,
            prerequisite_context=part.prerequisite_context or ["- None"],
            key_concepts=part.key_concepts or ["- None"],
            recommended_diagrams=part.recommended_diagrams or ["- None"],
            dependency_context=part.dependencies_on_previous or ["- None"],
            series_navigation=series_navigation,
            research_summary=research.summary,
            active_skills=retrieved_guidance.retrieved_guidance or ["- None"],
        )
        plan = self.context.llm.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=prompt,
            schema=BlogChapterPlan,
        )
        return self._normalize_plan(plan)

    @classmethod
    def _normalize_plan(cls, plan: BlogChapterPlan) -> BlogChapterPlan:
        existing = {section.heading.strip().lower(): section for section in plan.section_plans}
        normalized_sections: list[BlogSectionPlan] = []
        for heading in cls.MANDATORY_HEADINGS:
            section = existing.get(heading.lower())
            normalized_sections.append(section or cls._default_section_plan(heading))
        return plan.model_copy(update={"section_plans": normalized_sections})

    @staticmethod
    def _default_section_plan(heading: str) -> BlogSectionPlan:
        defaults = {
            "Introduction": (170, False),
            "Mental Model / Simplification Layer": (170, False),
            "Problem Framing": (170, False),
            "Detailed Core Sections": (420, True),
            "System / Architecture Thinking": (220, True),
            "Real-world Examples": (190, False),
            "Tradeoffs / Failure Cases": (190, False),
            "How This Works in Modern Systems": (180, False),
            "Synthesis / If You Step Back": (140, False),
            "Key Takeaways": (110, False),
            "Test Your Learning": (120, False),
            "Conclusion": (130, False),
            "References": (90, False),
        }
        target_words, requires_visual = defaults.get(heading, (150, False))
        subsections = ["Core concept 1", "Core concept 2", "Core concept 3"] if heading == "Detailed Core Sections" else []
        return BlogSectionPlan(
            heading=heading,
            purpose=f"Cover the {heading.lower()} section explicitly and keep it aligned with the chapter.",
            key_points=[f"Deliver the required {heading.lower()} content clearly."],
            target_words=target_words,
            subsections=subsections,
            requires_visual=requires_visual,
        )
