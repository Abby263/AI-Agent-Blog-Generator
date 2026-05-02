from pathlib import Path

from blog_series_agent.agents.base import AgentContext
from blog_series_agent.agents.blog_writer import BlogWriterAgent
from blog_series_agent.config.settings import ModelConfig, SeriesRunConfig
from blog_series_agent.schemas.memory import SkillRetrievalQuery, SkillRetrievalResult
from blog_series_agent.schemas.series import (
    BlogChapterPlan,
    BlogResearchPacket,
    BlogSectionPlan,
    BlogSeriesOutline,
    BlogSeriesPart,
    SectionResearchPacket,
    SourceNote,
)
from blog_series_agent.utils.prompts import PromptLoader


def test_blog_writer_normalizes_section_targets_into_window() -> None:
    sections = [
        BlogSectionPlan(heading="Introduction", purpose="Open", target_words=220),
        BlogSectionPlan(heading="Detailed Core Sections", purpose="Core", target_words=980),
        BlogSectionPlan(heading="Conclusion", purpose="Close", target_words=190),
        BlogSectionPlan(heading="References", purpose="Refs", target_words=90),
    ]

    targets = BlogWriterAgent._normalized_section_targets(sections, 1800, 2600)

    assert sum(targets) <= 2480
    assert max(targets) <= 360
    assert min(targets) >= 70


class _FakeLLM:
    def generate_text(self, *, system_prompt: str, user_prompt: str, max_tokens: int | None = None) -> str:
        return "The section body explains the topic with grounded detail."

    def generate_structured(self, *, system_prompt: str, user_prompt: str, schema):  # pragma: no cover - unused
        raise NotImplementedError


def test_blog_writer_adds_sources_images_links_and_code_per_section() -> None:
    writer = BlogWriterAgent(
        AgentContext(
            llm=_FakeLLM(),
            prompts=PromptLoader(Path("src/blog_series_agent/prompts")),
        )
    )
    config = SeriesRunConfig(
        topic="ML System Design",
        audience="intermediate",
        num_parts=1,
        model=ModelConfig(),
        min_word_count=1800,
        max_word_count=2600,
    )
    part = BlogSeriesPart(
        part_number=1,
        title="Intro to ML System Design",
        slug="intro-to-ml-system-design",
        purpose="Open the series.",
        prerequisite_context=[],
        key_concepts=["requirements"],
        recommended_diagrams=["lifecycle diagram"],
    )
    outline = BlogSeriesOutline(
        topic="ML System Design",
        target_audience="intermediate",
        narrative_arc="Start with requirements, end with operations.",
        learning_goals=["Build production intuition."],
        parts=[part],
    )
    research = BlogResearchPacket(
        part_number=1,
        slug=part.slug,
        title=part.title,
        summary="Part-level summary",
        core_questions=["What changes in production?"],
        examples=["Recommendations"],
        system_design_insights=["Requirements drive architecture."],
        practical_references=[
            SourceNote(
                title="Hidden Technical Debt in Machine Learning Systems",
                source_type="paper",
                url="https://research.google/pubs/pub43146/",
                year=2015,
                note="Foundational production ML paper.",
            )
        ],
    )
    chapter_plan = BlogChapterPlan(
        part_number=1,
        slug=part.slug,
        title=part.title,
        subtitle="Why production ML is a systems problem.",
        chapter_summary="Summary",
        section_plans=[BlogSectionPlan(heading="Detailed Core Sections", purpose="Open strongly.", requires_visual=True)],
    )
    section_research = [
        SectionResearchPacket(
            section_heading="Detailed Core Sections",
            section_slug="detailed-core-sections",
            section_purpose="Open strongly.",
            research_summary="Use a systems framing.",
            source_notes=research.practical_references,
            visual_spec="A simple lifecycle diagram showing data, training, and serving feedback loops.",
            image_url="https://example.org/diagram.png",
            image_credit_url="https://example.org/article",
            image_credit_text="Example Engineering",
            image_alt_text="System lifecycle diagram",
            code_example_title="Minimal monitoring rule",
            code_example_language="yaml",
            code_example="threshold: 0.2\nwindow: 1h",
            code_example_notes="Valid YAML example.",
        )
    ]

    package = writer.run(
        config,
        outline,
        part,
        research,
        chapter_plan,
        section_research,
        SkillRetrievalResult(
            query=SkillRetrievalQuery(
                topic="ML System Design",
                audience="intermediate",
                part_number=1,
                artifact_type="draft",
                max_skills=3,
            ),
            retrieved_skill_ids=[],
            retrieved_guidance=[],
            retrieval_notes=[],
        ),
        [],
    )

    assert package.section_drafts
    section_markdown = package.section_drafts[0].markdown
    assert "![System lifecycle diagram](https://example.org/diagram.png)" in section_markdown
    assert "_Image credit: [Example Engineering](https://example.org/article)_" in section_markdown
    assert "Sources for This Section" in section_markdown
    assert "[Hidden Technical Debt in Machine Learning Systems](https://research.google/pubs/pub43146/)" in section_markdown
    assert "Use a systems framing." in section_markdown
    assert "```yaml" in section_markdown
