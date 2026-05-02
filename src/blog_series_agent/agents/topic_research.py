"""Topic research agent — supports memory-only and grounded (tool-call) modes."""

from __future__ import annotations

import logging

from ..config.settings import SeriesRunConfig
from ..schemas.series import TopicResearchDossier
from ..utils.research import count_urls, extract_source_notes_from_evidence
from .base import BaseAgent

logger = logging.getLogger(__name__)


class TopicResearchAgent(BaseAgent):
    prompt_name = "topic_research"
    system_prompt = (
        "You are a senior technical research strategist. Produce a precise research dossier and "
        "return valid structured output only."
    )
    grounded_system_prompt = (
        "You are a senior technical research strategist with access to live web search and URL "
        "fetching tools. Search for the most current, credible information on the topic before "
        "producing your research dossier. Ground all claims in what you actually retrieve."
    )

    def run(self, config: SeriesRunConfig) -> TopicResearchDossier:
        """Run topic research — uses grounded tool calls when toolkit is available."""
        toolkit = self.context.research_toolkit
        if toolkit and toolkit.enabled:
            return self._run_grounded(config)
        return self._run_memory_only(config)

    def _run_memory_only(self, config: SeriesRunConfig) -> TopicResearchDossier:
        prompt = self.context.prompts.render(
            self.prompt_name,
            topic=config.topic,
            audience=config.target_audience,
            num_parts=config.num_parts,
            deepagent_guidance=self.deepagent_guidance(stage="topic_research", subagent_name="topic_researcher"),
        )
        return self.context.llm.generate_structured(
            system_prompt=self.system_prompt_with_deepagent(stage="topic_research", subagent_name="topic_researcher"),
            user_prompt=prompt,
            schema=TopicResearchDossier,
        )

    def _run_grounded(self, config: SeriesRunConfig) -> TopicResearchDossier:
        """
        Two-phase grounded research:
          1. ReAct loop: model searches for landscape overview, recent papers, and production examples.
          2. Structured synthesis from gathered evidence.
        """
        toolkit = self.context.research_toolkit
        if toolkit is None or not toolkit.enabled:
            return self._run_memory_only(config)

        lc_tools = toolkit.as_langchain_tools()
        logger.info("Topic research (grounded) — topic: %s", config.topic)

        # ── Phase 1: live evidence gathering ────────────────────────────
        search_prompt = (
            f"You are building a comprehensive research dossier on: **{config.topic}**\n\n"
            f"**Target audience:** {config.target_audience}\n"
            f"**Series length:** {config.num_parts} parts\n\n"
            f"Use web_search and fetch_url to gather:\n"
            f"  1. Overview of the current state-of-the-art for {config.topic}\n"
            f"  2. 3-5 recent papers, benchmark results, or major developments (2022-2025)\n"
            f"  3. Production engineering blog posts from top tech companies about {config.topic}\n"
            f"  4. Known open problems, active debates, and emerging directions\n\n"
            f"Run 4-5 specific searches. Fetch 3-4 of the most informative pages. "
            f"Summarise all findings with exact titles, URLs, dates, and key technical points. "
            f"Do not fabricate any sources."
        )
        evidence_text = self.context.llm.generate_with_tools(
            system_prompt=self.system_prompt_with_deepagent(
                stage="topic_research",
                subagent_name="topic_researcher",
                base_prompt=self.grounded_system_prompt,
            ),
            user_prompt=search_prompt,
            tools=lc_tools,
            max_iterations=10,
        )
        if count_urls(evidence_text) < 3:
            fallback_queries = [
                f"{config.topic} engineering blog",
                f"{config.topic} official documentation",
                f"{config.topic} paper",
            ]
            fallback_result = toolkit.research_queries(fallback_queries, fetch_top_n=3)
            fallback_block = fallback_result.as_context_block()
            if count_urls(fallback_block) > 0:
                evidence_text = f"{evidence_text}\n\n### Deterministic Fallback Evidence\n{fallback_block}".strip()

        # ── Phase 2: structured synthesis ───────────────────────────────
        synthesis_prompt = self.context.prompts.render(
            self.prompt_name,
            topic=config.topic,
            audience=config.target_audience,
            num_parts=config.num_parts,
            deepagent_guidance=self.deepagent_guidance(stage="topic_research", subagent_name="topic_researcher"),
        ) + (
            f"\n\n---\n## Live Research Evidence\n\n{evidence_text}\n---\n\n"
            f"Use the evidence above to populate your dossier. "
            f"Extract real source references with titles, URLs, and years. "
            f"All claims about current state, benchmarks, or production systems must come from the evidence. "
            f"If the evidence does not cover a required field, mark it as 'not found in search results'."
        )
        dossier = self.context.llm.generate_structured(
            system_prompt=self.system_prompt_with_deepagent(stage="topic_research", subagent_name="topic_researcher"),
            user_prompt=synthesis_prompt,
            schema=TopicResearchDossier,
        )
        evidence_sources = extract_source_notes_from_evidence(evidence_text, limit=10)
        if not dossier.source_notes or all(not note.url for note in dossier.source_notes):
            dossier.source_notes = evidence_sources or dossier.source_notes
        return dossier
