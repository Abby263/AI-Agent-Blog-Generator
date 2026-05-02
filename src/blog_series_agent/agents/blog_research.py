"""Per-part blog research agent — supports memory-only and grounded (tool-call) modes."""

from __future__ import annotations

import logging

from ..config.settings import SeriesRunConfig
from ..schemas.series import BlogResearchPacket, BlogSeriesOutline, BlogSeriesPart
from ..utils.research import count_urls, extract_source_notes_from_evidence, sanitize_research_meta
from .base import BaseAgent

logger = logging.getLogger(__name__)


class BlogResearchAgent(BaseAgent):
    prompt_name = "blog_research"
    system_prompt = (
        "You are a technical content research specialist. Produce targeted, practical research "
        "for one blog chapter and return valid structured output only."
    )
    grounded_system_prompt = (
        "You are a technical content research specialist with access to live web search and URL "
        "fetching tools. Use them to find real, current, specific technical sources for the blog "
        "chapter you are researching. Search first, then fetch promising pages, then synthesise "
        "structured output grounded in what you actually found."
    )

    def run(
        self,
        config: SeriesRunConfig,
        outline: BlogSeriesOutline,
        part: BlogSeriesPart,
    ) -> BlogResearchPacket:
        """Run research — uses grounded tool calls when toolkit is available."""
        toolkit = self.context.research_toolkit
        if toolkit and toolkit.enabled:
            return self._run_grounded(config, outline, part)
        return self._run_memory_only(config, outline, part)

    def _run_memory_only(
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
            deepagent_guidance=self.deepagent_guidance(stage="blog_research", subagent_name="chapter_researcher"),
        )
        return self.context.llm.generate_structured(
            system_prompt=self.system_prompt_with_deepagent(stage="blog_research", subagent_name="chapter_researcher"),
            user_prompt=prompt,
            schema=BlogResearchPacket,
        )

    def _run_grounded(
        self,
        config: SeriesRunConfig,
        outline: BlogSeriesOutline,
        part: BlogSeriesPart,
    ) -> BlogResearchPacket:
        """
        Two-phase grounded research:
          1. ReAct loop: model searches and fetches live sources.
          2. Structured synthesis from collected evidence.
        """
        toolkit = self.context.research_toolkit
        if toolkit is None or not toolkit.enabled:
            return self._run_memory_only(config, outline, part)

        lc_tools = toolkit.as_langchain_tools()
        logger.info("Blog research (grounded) — part %d: %s", part.part_number, part.title)

        # ── Phase 1: live evidence gathering ────────────────────────────
        search_prompt = (
            f"You are researching Part {part.part_number} of a technical blog series: **{part.title}**.\n\n"
            f"**Topic:** {config.topic}\n"
            f"**Audience:** {config.target_audience}\n"
            f"**Part purpose:** {part.purpose}\n"
            f"**Series narrative:** {outline.narrative_arc}\n\n"
            f"Use web_search and fetch_url to find:\n"
            f"  1. Real-world production case studies from engineering blogs (Netflix, Uber, Stripe, Airbnb, Meta, etc.)\n"
            f"  2. Recent academic papers or technical documentation on {part.title}\n"
            f"  3. Concrete numbers, benchmarks, failure stories, architectural patterns\n\n"
            f"Run 3-4 specific search queries, then fetch 2-3 of the best URLs. "
            f"Summarise what you found with exact titles, URLs, and key technical facts. "
            f"Do NOT fabricate sources."
        )
        evidence_text = self.context.llm.generate_with_tools(
            system_prompt=self.system_prompt_with_deepagent(
                stage="blog_research",
                subagent_name="chapter_researcher",
                base_prompt=self.grounded_system_prompt,
            ),
            user_prompt=search_prompt,
            tools=lc_tools,
            max_iterations=8,
        )
        if count_urls(evidence_text) < 2:
            fallback_queries = [
                f"{config.topic} {part.title} engineering blog",
                f"{part.title} official documentation",
                f"{config.topic} {part.title} paper",
            ]
            fallback_result = toolkit.research_queries(fallback_queries, fetch_top_n=2)
            fallback_block = fallback_result.as_context_block()
            if count_urls(fallback_block) > 0:
                evidence_text = f"{evidence_text}\n\n### Deterministic Fallback Evidence\n{fallback_block}".strip()

        # ── Phase 2: structured synthesis ───────────────────────────────
        synthesis_prompt = self.context.prompts.render(
            self.prompt_name,
            topic=config.topic,
            audience=config.target_audience,
            part_number=part.part_number,
            part_title=part.title,
            part_purpose=part.purpose,
            series_context=outline.narrative_arc,
            deepagent_guidance=self.deepagent_guidance(stage="blog_research", subagent_name="chapter_researcher"),
        ) + (
            f"\n\n---\n## Live Research Evidence\n\n{evidence_text}\n---\n\n"
            f"Ground your structured output in the evidence above. "
            f"Extract real source_notes / practical_references (title, exact URL, year, source_type). "
            f"Do not invent facts not present in the evidence."
        )
        packet = self.context.llm.generate_structured(
            system_prompt=self.system_prompt_with_deepagent(stage="blog_research", subagent_name="chapter_researcher"),
            user_prompt=synthesis_prompt,
            schema=BlogResearchPacket,
        )
        evidence_sources = extract_source_notes_from_evidence(evidence_text, limit=8)
        if not packet.practical_references or all(not note.url for note in packet.practical_references):
            packet.practical_references = evidence_sources or packet.practical_references
        else:
            existing_urls = {note.url for note in packet.practical_references if note.url}
            for note in evidence_sources:
                if note.url and note.url not in existing_urls:
                    packet.practical_references.append(note)
                    existing_urls.add(note.url)
        packet.summary = sanitize_research_meta(packet.summary, fallback=part.purpose)
        return packet
