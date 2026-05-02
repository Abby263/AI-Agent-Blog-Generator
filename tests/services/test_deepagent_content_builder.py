from pathlib import Path

from blog_series_agent.config.settings import ModelConfig, SeriesRunConfig
from blog_series_agent.schemas.memory import SkillRetrievalQuery, SkillRetrievalResult
from blog_series_agent.schemas.series import BlogSeriesOutline, BlogSeriesPart
from blog_series_agent.services.deepagent_content_builder import DeepAgentContentBuilder
from blog_series_agent.services.deepagent_profile import DeepAgentProfileLoader
from blog_series_agent.services.research_tools import ResearchToolkit


class _FakeLLM:
    def as_chat_model(self):
        return object()

    def generate_text(self, *, system_prompt: str, user_prompt: str, max_tokens=None):  # pragma: no cover
        raise NotImplementedError

    def generate_structured(self, *, system_prompt: str, user_prompt: str, schema):  # pragma: no cover
        raise NotImplementedError


class _FakeAgent:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace

    def invoke(self, payload, config):
        (self.workspace / "research.md").write_text("# Research\n\nURL: https://example.org/source", encoding="utf-8")
        (self.workspace / "plan.md").write_text("# Plan\n\n- Intro", encoding="utf-8")
        (self.workspace / "draft.md").write_text(
            "# Test Blog\n\n## Introduction\n\nGrounded section.\n\n#### Sources for This Section\n- [Source](https://example.org/source)",
            encoding="utf-8",
        )
        (self.workspace / "assets.md").write_text("# Assets\n\n- Diagram", encoding="utf-8")
        (self.workspace / "manifest.json").write_text('{"source_urls": ["https://example.org/source"]}', encoding="utf-8")
        return {"messages": []}


class _TestBuilder(DeepAgentContentBuilder):
    def _create_agent(self, workspace: Path):
        return _FakeAgent(workspace)


def test_deepagent_content_builder_reads_expected_files(tmp_path: Path) -> None:
    profile = DeepAgentProfileLoader(Path("src/blog_series_agent/deepagent")).load()
    builder = _TestBuilder(
        llm=_FakeLLM(),
        profile=profile,
        research_toolkit=ResearchToolkit(enabled=False),
    )
    part = BlogSeriesPart(
        part_number=1,
        title="Introduction",
        slug="introduction",
        purpose="Open the series.",
        prerequisite_context=[],
        key_concepts=[],
        recommended_diagrams=[],
    )
    outline = BlogSeriesOutline(
        topic="ML System Design",
        target_audience="intermediate",
        narrative_arc="Start with fundamentals.",
        learning_goals=["Learn ML systems"],
        parts=[part],
    )
    config = SeriesRunConfig(
        topic="ML System Design",
        audience="intermediate",
        num_parts=1,
        output_dir=tmp_path,
        model=ModelConfig(),
    )
    retrieval = SkillRetrievalResult(
        query=SkillRetrievalQuery(
            topic=config.topic,
            audience=config.target_audience,
            part_number=1,
            artifact_type="draft",
            max_skills=3,
        ),
        retrieved_skill_ids=[],
        retrieved_guidance=["Open with a concrete production problem."],
        retrieval_notes=[],
    )

    result = builder.build_blog(
        config=config,
        outline=outline,
        part=part,
        retrieved_guidance=retrieval,
        run_id="run-test",
    )

    assert "https://example.org/source" in result.research_markdown
    assert "Sources for This Section" in result.draft_markdown
    assert result.manifest["source_urls"] == ["https://example.org/source"]
    assert result.workspace is not None
    assert (result.workspace / ".deepagent_profile" / "AGENTS.md").exists()


def test_deepagent_content_builder_loads_subagent_tools() -> None:
    profile = DeepAgentProfileLoader(Path("src/blog_series_agent/deepagent")).load()
    toolkit = ResearchToolkit(enabled=True)
    builder = DeepAgentContentBuilder(llm=_FakeLLM(), profile=profile, research_toolkit=toolkit)

    subagents = builder._subagents(toolkit.as_langchain_tools())

    section = next(item for item in subagents if item["name"] == "section_researcher")
    assert {tool.name for tool in section["tools"]} == {"research_sources", "web_search", "fetch_url"}

    visual = next(item for item in subagents if item["name"] == "visual_planner")
    assert {tool.name for tool in visual["tools"]} == {"research_sources", "web_search", "fetch_url"}


def test_deepagent_task_exposes_active_skill_ids() -> None:
    part = BlogSeriesPart(
        part_number=1,
        title="Introduction",
        slug="introduction",
        purpose="Open the series.",
        prerequisite_context=[],
        key_concepts=[],
        recommended_diagrams=[],
    )
    outline = BlogSeriesOutline(
        topic="ML System Design",
        target_audience="intermediate",
        narrative_arc="Start with fundamentals.",
        learning_goals=["Learn ML systems"],
        parts=[part],
    )
    config = SeriesRunConfig(
        topic="ML System Design",
        audience="intermediate",
        num_parts=1,
        model=ModelConfig(),
    )
    retrieval = SkillRetrievalResult(
        query=SkillRetrievalQuery(
            topic=config.topic,
            audience=config.target_audience,
            part_number=1,
            artifact_type="draft",
            max_skills=3,
        ),
        retrieved_skill_ids=["skill-a", "skill-b"],
        retrieved_guidance=["[skill-a] Use synthesis paragraphs."],
        retrieval_notes=[],
    )

    task = DeepAgentContentBuilder._render_task(
        config=config,
        outline=outline,
        part=part,
        retrieved_guidance=retrieval,
    )

    assert '"skill-a"' in task
    assert '"skill-b"' in task
    assert "research_sources" in task
    assert "missing_evidence" in task
