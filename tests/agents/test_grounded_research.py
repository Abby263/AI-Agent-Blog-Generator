"""Tests for grounded (tool-call) research agents.

Verifies that when a ResearchToolkit is present and enabled, the agents
route through generate_with_tools() + generate_structured(), and that
they gracefully fall back to memory-only when the toolkit is disabled.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from blog_series_agent.agents.base import AgentContext
from blog_series_agent.agents.blog_research import BlogResearchAgent
from blog_series_agent.agents.section_research import SectionResearchAgent
from blog_series_agent.agents.topic_research import TopicResearchAgent
from blog_series_agent.config.settings import ModelConfig, SeriesRunConfig
from blog_series_agent.schemas.series import (
    BlogChapterPlan,
    BlogResearchPacket,
    BlogSectionPlan,
    BlogSeriesOutline,
    BlogSeriesPart,
    SectionResearchPacket,
    SourceNote,
    TopicResearchDossier,
)
from blog_series_agent.services.research_tools import ResearchToolkit
from blog_series_agent.utils.prompts import PromptLoader


# ---------------------------------------------------------------------------
# Shared test doubles
# ---------------------------------------------------------------------------

PROMPTS = PromptLoader(Path("src/blog_series_agent/prompts"))

CONFIG = SeriesRunConfig(
    topic="ML System Design",
    audience="intermediate",
    num_parts=3,
    model=ModelConfig(),
)

OUTLINE = BlogSeriesOutline(
    topic="ML System Design",
    target_audience="intermediate",
    narrative_arc="From training to serving.",
    learning_goals=["Understand ML systems end-to-end"],
    parts=[
        BlogSeriesPart(
            part_number=1,
            title="Introduction",
            slug="introduction",
            purpose="Set the scene.",
            prerequisite_context=[],
            key_concepts=[],
            recommended_diagrams=[],
        )
    ],
)

PART = OUTLINE.parts[0]

CHAPTER_PLAN = BlogChapterPlan(
    part_number=1,
    slug="introduction",
    title="Introduction",
    subtitle="Getting started",
    chapter_summary="Overview of ML systems.",
    section_plans=[
        BlogSectionPlan(heading="Overview", purpose="Broad intro"),
        BlogSectionPlan(heading="Architecture", purpose="Key patterns"),
    ],
)

BLOG_RESEARCH = BlogResearchPacket(
    part_number=1,
    slug="introduction",
    title="Introduction",
    summary="ML research summary",
    core_questions=[],
    examples=[],
    system_design_insights=[],
    practical_references=[],
)


def _fake_packet(heading: str = "") -> SectionResearchPacket:
    """Return a packet with empty identity fields so the agent's backfill logic is exercised."""
    return SectionResearchPacket(
        section_heading="",   # deliberately empty — agent must backfill
        section_slug="",      # deliberately empty — agent must backfill
        section_purpose="",   # deliberately empty — agent must backfill
        research_summary="Grounded summary from real evidence.",
        supporting_points=["Point A", "Point B"],
        source_notes=[SourceNote(title="Real Paper", source_type="paper", year=2024, note="Key finding.")],
        visual_spec="Diagram of system.",
    )


def _fake_dossier() -> TopicResearchDossier:
    return TopicResearchDossier(
        topic="ML System Design",
        target_audience="intermediate",
        key_themes=["scalability", "latency"],
        landmark_papers=[],
        industry_applications=[],
        common_misconceptions=[],
        prerequisite_knowledge=[],
        suggested_series_angles=[],
        current_state_summary="State of the art.",
        open_problems=[],
        positioning_summary="Grounded series positioning.",
        glossary=[],
        recent_developments=[],
        recommended_progression=[],
    )


# ---------------------------------------------------------------------------
# Fake LLM that tracks which methods were called
# ---------------------------------------------------------------------------


class _TrackingFakeLLM:
    def __init__(self, structured_result):
        self._structured_result = structured_result
        self.generate_with_tools_called = False
        self.generate_text_called = False
        self.generate_structured_called = False

    def generate_text(self, *, system_prompt: str, user_prompt: str, max_tokens=None) -> str:
        self.generate_text_called = True
        return "Memory-only text response."

    def generate_structured(self, *, system_prompt, user_prompt, schema):
        self.generate_structured_called = True
        # Return a fresh copy each time so mutations in one iteration don't bleed into the next
        result = self._structured_result
        if hasattr(result, "model_copy"):
            return result.model_copy()
        return result

    def generate_with_tools(self, *, system_prompt, user_prompt, tools, max_iterations=6) -> str:
        self.generate_with_tools_called = True
        tool_names = [t.name for t in tools]
        assert "web_search" in tool_names, "web_search tool must be available"
        assert "fetch_url" in tool_names, "fetch_url tool must be available"
        return "Evidence gathered from web search: Paper A (arxiv.org, 2024). Key finding: X."


# ---------------------------------------------------------------------------
# SectionResearchAgent — grounded mode
# ---------------------------------------------------------------------------


class TestSectionResearchAgentGrounded:
    def _make_agent(self, toolkit_enabled: bool = True):
        toolkit = ResearchToolkit(enabled=toolkit_enabled)
        # Mock the langchain tools so they don't need real network
        search_tool = MagicMock()
        search_tool.name = "web_search"
        fetch_tool = MagicMock()
        fetch_tool.name = "fetch_url"
        toolkit.as_langchain_tools = MagicMock(return_value=[search_tool, fetch_tool])
        llm = _TrackingFakeLLM(structured_result=_fake_packet(""))
        ctx = AgentContext(llm=llm, prompts=PROMPTS, research_toolkit=toolkit)
        return SectionResearchAgent(ctx), llm

    def test_grounded_calls_generate_with_tools_and_generate_structured(self):
        agent, llm = self._make_agent(toolkit_enabled=True)
        packets = agent.run(CONFIG, CHAPTER_PLAN, BLOG_RESEARCH)
        assert llm.generate_with_tools_called, "generate_with_tools must be called in grounded mode"
        assert llm.generate_structured_called, "generate_structured must be called to parse evidence"
        assert len(packets) == len(CHAPTER_PLAN.section_plans)

    def test_grounded_backfills_slug_heading_purpose(self):
        agent, _ = self._make_agent(toolkit_enabled=True)
        packets = agent.run(CONFIG, CHAPTER_PLAN, BLOG_RESEARCH)
        for packet, plan in zip(packets, CHAPTER_PLAN.section_plans):
            assert packet.section_heading == plan.heading
            assert packet.section_purpose == plan.purpose
            assert packet.section_slug != ""

    def test_disabled_toolkit_falls_back_to_memory_only(self):
        toolkit = ResearchToolkit(enabled=False)
        llm = _TrackingFakeLLM(structured_result=_fake_packet(""))
        ctx = AgentContext(llm=llm, prompts=PROMPTS, research_toolkit=toolkit)
        agent = SectionResearchAgent(ctx)
        packets = agent.run(CONFIG, CHAPTER_PLAN, BLOG_RESEARCH)
        assert not llm.generate_with_tools_called, "generate_with_tools must NOT be called when toolkit is disabled"
        assert llm.generate_structured_called
        assert len(packets) == len(CHAPTER_PLAN.section_plans)

    def test_no_toolkit_falls_back_to_memory_only(self):
        llm = _TrackingFakeLLM(structured_result=_fake_packet(""))
        ctx = AgentContext(llm=llm, prompts=PROMPTS, research_toolkit=None)
        agent = SectionResearchAgent(ctx)
        packets = agent.run(CONFIG, CHAPTER_PLAN, BLOG_RESEARCH)
        assert not llm.generate_with_tools_called
        assert llm.generate_structured_called


# ---------------------------------------------------------------------------
# BlogResearchAgent — grounded mode
# ---------------------------------------------------------------------------


class TestBlogResearchAgentGrounded:
    def _make_agent(self, toolkit_enabled: bool = True):
        toolkit = ResearchToolkit(enabled=toolkit_enabled)
        search_tool = MagicMock(); search_tool.name = "web_search"
        fetch_tool = MagicMock(); fetch_tool.name = "fetch_url"
        toolkit.as_langchain_tools = MagicMock(return_value=[search_tool, fetch_tool])
        llm = _TrackingFakeLLM(structured_result=BLOG_RESEARCH)
        ctx = AgentContext(llm=llm, prompts=PROMPTS, research_toolkit=toolkit)
        return BlogResearchAgent(ctx), llm

    def test_grounded_calls_generate_with_tools(self):
        agent, llm = self._make_agent(toolkit_enabled=True)
        result = agent.run(CONFIG, OUTLINE, PART)
        assert llm.generate_with_tools_called, "generate_with_tools must be called in grounded mode"
        assert llm.generate_structured_called
        assert isinstance(result, BlogResearchPacket)

    def test_disabled_toolkit_skips_tool_calls(self):
        agent, llm = self._make_agent(toolkit_enabled=False)
        result = agent.run(CONFIG, OUTLINE, PART)
        assert not llm.generate_with_tools_called
        assert llm.generate_structured_called
        assert isinstance(result, BlogResearchPacket)

    def test_no_toolkit_memory_only(self):
        llm = _TrackingFakeLLM(structured_result=BLOG_RESEARCH)
        ctx = AgentContext(llm=llm, prompts=PROMPTS, research_toolkit=None)
        agent = BlogResearchAgent(ctx)
        result = agent.run(CONFIG, OUTLINE, PART)
        assert not llm.generate_with_tools_called
        assert isinstance(result, BlogResearchPacket)


# ---------------------------------------------------------------------------
# TopicResearchAgent — grounded mode
# ---------------------------------------------------------------------------


class TestTopicResearchAgentGrounded:
    def _make_agent(self, toolkit_enabled: bool = True):
        toolkit = ResearchToolkit(enabled=toolkit_enabled)
        search_tool = MagicMock(); search_tool.name = "web_search"
        fetch_tool = MagicMock(); fetch_tool.name = "fetch_url"
        toolkit.as_langchain_tools = MagicMock(return_value=[search_tool, fetch_tool])
        llm = _TrackingFakeLLM(structured_result=_fake_dossier())
        ctx = AgentContext(llm=llm, prompts=PROMPTS, research_toolkit=toolkit)
        return TopicResearchAgent(ctx), llm

    def test_grounded_calls_generate_with_tools(self):
        agent, llm = self._make_agent(toolkit_enabled=True)
        result = agent.run(CONFIG)
        assert llm.generate_with_tools_called
        assert llm.generate_structured_called
        assert isinstance(result, TopicResearchDossier)

    def test_disabled_toolkit_memory_only(self):
        agent, llm = self._make_agent(toolkit_enabled=False)
        result = agent.run(CONFIG)
        assert not llm.generate_with_tools_called
        assert isinstance(result, TopicResearchDossier)

    def test_no_toolkit_memory_only(self):
        llm = _TrackingFakeLLM(structured_result=_fake_dossier())
        ctx = AgentContext(llm=llm, prompts=PROMPTS, research_toolkit=None)
        agent = TopicResearchAgent(ctx)
        result = agent.run(CONFIG)
        assert not llm.generate_with_tools_called


# ---------------------------------------------------------------------------
# OpenAICompatibleLLMClient.generate_with_tools — unit test the ReAct loop
# ---------------------------------------------------------------------------


class TestGenerateWithToolsReActLoop:
    """Test the ReAct loop logic in OpenAICompatibleLLMClient."""

    def test_returns_immediately_when_no_tool_calls(self):
        """If the model produces a direct answer with no tool calls, return it."""
        from blog_series_agent.models.openai_compatible import OpenAICompatibleLLMClient
        from blog_series_agent.config.settings import ModelConfig

        client = OpenAICompatibleLLMClient.__new__(OpenAICompatibleLLMClient)

        # Mock the internal ChatOpenAI client
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Final answer without tool calls."
        mock_response.tool_calls = []
        mock_chat.bind_tools.return_value = mock_chat
        mock_chat.invoke.return_value = mock_response
        client._client = mock_chat

        mock_tool = MagicMock()
        mock_tool.name = "web_search"

        result = client.generate_with_tools(
            system_prompt="You are a researcher.",
            user_prompt="Find papers on ML.",
            tools=[mock_tool],
        )
        assert result == "Final answer without tool calls."
        assert mock_chat.invoke.call_count == 1

    def test_executes_tool_call_and_continues(self):
        """When the model makes a tool call, execute it and continue the loop."""
        from blog_series_agent.models.openai_compatible import OpenAICompatibleLLMClient

        client = OpenAICompatibleLLMClient.__new__(OpenAICompatibleLLMClient)
        mock_chat = MagicMock()

        # First response: tool call; second response: final answer
        tool_call_response = MagicMock()
        tool_call_response.content = ""
        tool_call_response.tool_calls = [
            {"name": "web_search", "args": {"query": "ML papers"}, "id": "call_001"}
        ]
        final_response = MagicMock()
        final_response.content = "Based on search results: key finding X."
        final_response.tool_calls = []

        mock_chat.bind_tools.return_value = mock_chat
        mock_chat.invoke.side_effect = [tool_call_response, final_response]
        client._client = mock_chat

        mock_tool = MagicMock()
        mock_tool.name = "web_search"
        mock_tool.invoke.return_value = "Search results: Paper A (2024), Paper B (2023)"

        result = client.generate_with_tools(
            system_prompt="Research assistant.",
            user_prompt="Find ML papers.",
            tools=[mock_tool],
        )
        assert result == "Based on search results: key finding X."
        assert mock_tool.invoke.call_count == 1
        mock_tool.invoke.assert_called_once_with({"query": "ML papers"})

    def test_unknown_tool_produces_error_message(self):
        """If the model calls a tool that doesn't exist, inject an error ToolMessage."""
        from blog_series_agent.models.openai_compatible import OpenAICompatibleLLMClient

        client = OpenAICompatibleLLMClient.__new__(OpenAICompatibleLLMClient)
        mock_chat = MagicMock()

        call_unknown = MagicMock()
        call_unknown.content = ""
        call_unknown.tool_calls = [
            {"name": "nonexistent_tool", "args": {}, "id": "call_999"}
        ]
        final = MagicMock()
        final.content = "I encountered an error but here is my answer."
        final.tool_calls = []

        mock_chat.bind_tools.return_value = mock_chat
        mock_chat.invoke.side_effect = [call_unknown, final]
        client._client = mock_chat

        mock_tool = MagicMock()
        mock_tool.name = "web_search"

        result = client.generate_with_tools(
            system_prompt="Research.",
            user_prompt="Query.",
            tools=[mock_tool],
        )
        # The loop should not raise — it injects an error message and continues
        assert "answer" in result.lower()

    def test_falls_back_to_generate_text_when_no_tools(self):
        """With an empty tools list, must fall back to generate_text()."""
        from blog_series_agent.models.openai_compatible import OpenAICompatibleLLMClient

        client = OpenAICompatibleLLMClient.__new__(OpenAICompatibleLLMClient)
        mock_chat = MagicMock()
        mock_chat.invoke.return_value = MagicMock(content="Plain text response.")
        client._client = mock_chat

        result = client.generate_with_tools(
            system_prompt="System.",
            user_prompt="User.",
            tools=[],
        )
        assert result == "Plain text response."
        # bind_tools should NOT have been called
        mock_chat.bind_tools.assert_not_called()

    def test_max_iterations_is_respected(self):
        """After max_iterations, return the last available response."""
        from blog_series_agent.models.openai_compatible import OpenAICompatibleLLMClient

        client = OpenAICompatibleLLMClient.__new__(OpenAICompatibleLLMClient)
        mock_chat = MagicMock()

        # Every response keeps requesting the same tool call (infinite loop simulation)
        def _always_calls_tool(*args, **kwargs):
            r = MagicMock()
            r.content = "Intermediate."
            r.tool_calls = [{"name": "web_search", "args": {"query": "x"}, "id": f"call_{id(r)}"}]
            return r

        mock_chat.bind_tools.return_value = mock_chat
        mock_chat.invoke.side_effect = _always_calls_tool
        client._client = mock_chat

        mock_tool = MagicMock()
        mock_tool.name = "web_search"
        mock_tool.invoke.return_value = "Search result."

        result = client.generate_with_tools(
            system_prompt="S.",
            user_prompt="U.",
            tools=[mock_tool],
            max_iterations=3,
        )
        # Should have stopped after 3 iterations without raising
        assert mock_chat.invoke.call_count == 3
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# AgentContext — research_toolkit field
# ---------------------------------------------------------------------------


def test_agent_context_accepts_toolkit():
    llm = _TrackingFakeLLM(structured_result=None)
    toolkit = ResearchToolkit(enabled=True)
    ctx = AgentContext(llm=llm, prompts=PROMPTS, research_toolkit=toolkit)
    assert ctx.research_toolkit is toolkit


def test_agent_context_defaults_to_none_toolkit():
    llm = _TrackingFakeLLM(structured_result=None)
    ctx = AgentContext(llm=llm, prompts=PROMPTS)
    assert ctx.research_toolkit is None
