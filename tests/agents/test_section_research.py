from pathlib import Path

from blog_series_agent.agents.base import AgentContext
from blog_series_agent.agents.section_research import SectionResearchAgent
from blog_series_agent.config.settings import ModelConfig, SeriesRunConfig
from blog_series_agent.schemas.series import (
    BlogChapterPlan,
    BlogResearchPacket,
    BlogSectionPlan,
    SectionResearchPacket,
    SourceNote,
)
from blog_series_agent.utils.prompts import PromptLoader


class _StructuredFakeLLM:
    def generate_text(self, *, system_prompt: str, user_prompt: str, max_tokens: int | None = None) -> str:  # pragma: no cover - unused
        raise NotImplementedError

    def generate_structured(self, *, system_prompt: str, user_prompt: str, schema):
        return SectionResearchPacket(
            section_heading="",
            section_slug="",
            section_purpose="",
            research_summary="Summarized section research.",
            supporting_points=["Anchor the section in a concrete production problem."],
            source_notes=[
                SourceNote(
                    title="Rules of Machine Learning",
                    source_type="engineering blog",
                    year=2016,
                    note="Strong practical guidance.",
                )
            ],
            visual_spec="A comparison diagram that contrasts offline and online system constraints.",
        )


def test_section_research_agent_backfills_slug_heading_and_purpose() -> None:
    agent = SectionResearchAgent(
        AgentContext(
            llm=_StructuredFakeLLM(),
            prompts=PromptLoader(Path("src/blog_series_agent/prompts")),
        )
    )
    config = SeriesRunConfig(
        topic="ML System Design",
        audience="intermediate",
        num_parts=1,
        model=ModelConfig(),
    )
    plan = BlogChapterPlan(
        part_number=1,
        slug="intro",
        title="Intro",
        subtitle="Sub",
        chapter_summary="Summary",
        section_plans=[BlogSectionPlan(heading="Introduction", purpose="Open strongly.")],
    )
    research = BlogResearchPacket(
        part_number=1,
        slug="intro",
        title="Intro",
        summary="Part-level summary",
        core_questions=[],
        examples=[],
        system_design_insights=[],
        practical_references=[],
    )

    packets = agent.run(config, plan, research)

    assert packets[0].section_heading == "Introduction"
    assert packets[0].section_slug == "introduction"
    assert packets[0].section_purpose == "Open strongly."
