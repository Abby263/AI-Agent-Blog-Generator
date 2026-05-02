"""Section-level research agent — supports both memory-only and grounded (tool-call) modes."""

from __future__ import annotations

import logging

from ..config.settings import SeriesRunConfig
from ..schemas.series import BlogChapterPlan, BlogResearchPacket, BlogSectionPlan, SectionResearchPacket
from ..utils.research import count_urls, extract_source_notes_from_evidence, sanitize_research_meta, sanitize_supporting_points
from ..utils.slug import slugify
from .base import BaseAgent

logger = logging.getLogger(__name__)


class SectionResearchAgent(BaseAgent):
    prompt_name = "section_research"
    grounded_prompt_name = "section_research_grounded"
    system_prompt = (
        "You are a section-level technical research agent. Return valid structured output only."
    )
    grounded_system_prompt = (
        "You are a section-level technical research agent with access to live web search and URL "
        "fetching tools. Use them to find real, current, specific technical sources for the section "
        "you are researching. Always call web_search first, then fetch the most promising URLs. "
        "After gathering evidence, synthesise structured output grounded in what you actually found."
    )

    # ------------------------------------------------------------------
    # Original: memory-only research (no network calls)
    # ------------------------------------------------------------------

    def run(
        self,
        config: SeriesRunConfig,
        chapter_plan: BlogChapterPlan,
        blog_research: BlogResearchPacket,
    ) -> list[SectionResearchPacket]:
        """Generate section research packets from LLM knowledge only."""
        toolkit = self.context.research_toolkit
        if toolkit and toolkit.enabled:
            return self.run_grounded(config, chapter_plan, blog_research)
        return self._run_memory_only(config, chapter_plan, blog_research)

    # ------------------------------------------------------------------
    # Grounded: real tool calls (web_search + fetch_url)
    # ------------------------------------------------------------------

    def run_grounded(
        self,
        config: SeriesRunConfig,
        chapter_plan: BlogChapterPlan,
        blog_research: BlogResearchPacket,
    ) -> list[SectionResearchPacket]:
        """
        Research each section with live web_search + fetch_url tool calls.

        Flow (mirrors how Claude Code uses Bash/Grep/Read):
          1. Build a research prompt telling the model *what* to look for.
          2. Call generate_with_tools() — the model iteratively calls
             web_search / fetch_url until it has enough evidence.
          3. Feed the gathered evidence text into generate_structured() to
             produce a validated SectionResearchPacket.
        """
        toolkit = self.context.research_toolkit
        if toolkit is None or not toolkit.enabled:
            logger.warning("run_grounded called but toolkit is disabled; falling back to memory-only.")
            return self._run_memory_only(config, chapter_plan, blog_research)

        lc_tools = toolkit.as_langchain_tools()
        packets: list[SectionResearchPacket] = []

        for section in chapter_plan.section_plans:
            section_slug = slugify(section.heading)
            logger.info(
                "Section research (grounded) — part %d / section '%s'",
                chapter_plan.part_number,
                section.heading,
            )

            # ── Step 1: ReAct loop to gather live evidence ──────────────
            search_prompt = self._build_search_prompt(
                config=config,
                chapter_plan=chapter_plan,
                section=section,  # type: ignore[arg-type]
                blog_research=blog_research,
            )
            evidence_text = self.context.llm.generate_with_tools(
                system_prompt=self.system_prompt_with_deepagent(
                    stage="section_research",
                    subagent_name="section_researcher",
                    base_prompt=self.grounded_system_prompt,
                ),
                user_prompt=search_prompt,
                tools=lc_tools,
                max_iterations=6,
            )
            evidence_text = self._augment_evidence_if_needed(
                toolkit=toolkit,
                config=config,
                chapter_plan=chapter_plan,
                section=section,
                blog_research=blog_research,
                evidence_text=evidence_text,
            )

            # ── Step 2: Structured synthesis from gathered evidence ──────
            synthesis_prompt = self._build_synthesis_prompt(
                config=config,
                chapter_plan=chapter_plan,
                section=section,  # type: ignore[arg-type]
                blog_research=blog_research,
                evidence_text=evidence_text,
            )
            packet = self.context.llm.generate_structured(
                system_prompt=self.system_prompt_with_deepagent(stage="section_research", subagent_name="section_researcher"),
                user_prompt=synthesis_prompt,
                schema=SectionResearchPacket,
            )

            # Normalise required fields
            if not packet.section_slug:
                packet.section_slug = section_slug
            if not packet.section_heading:
                packet.section_heading = section.heading
            if not packet.section_purpose:
                packet.section_purpose = section.purpose
            packet = self._repair_packet(
                packet=packet,
                section=section,
                blog_research=blog_research,
                toolkit=toolkit,
                evidence_text=evidence_text,
            )

            packets.append(packet)

        return packets

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_memory_only(
        self,
        config: SeriesRunConfig,
        chapter_plan: BlogChapterPlan,
        blog_research: BlogResearchPacket,
    ) -> list[SectionResearchPacket]:
        packets: list[SectionResearchPacket] = []
        for section in chapter_plan.section_plans:
            prompt = self.context.prompts.render(
                self.prompt_name,
                topic=config.topic,
                audience=config.target_audience,
                part_number=chapter_plan.part_number,
                part_title=chapter_plan.title,
                chapter_summary=chapter_plan.chapter_summary,
                section_heading=section.heading,
                section_purpose=section.purpose,
                section_key_points=section.key_points or ["- None"],
                section_subsections=section.subsections or ["- None"],
                section_requires_visual="Yes" if section.requires_visual else "No",
                blog_research_summary=blog_research.summary,
                blog_references=[
                    f"{note.title} ({note.source_type}, {note.year or 'year unknown'})"
                    for note in blog_research.practical_references
                ]
                or ["- None"],
                citation_anchors=blog_research.citation_anchors or ["- None"],
                deepagent_guidance=self.deepagent_guidance(stage="section_research", subagent_name="section_researcher"),
            )
            packet = self.context.llm.generate_structured(
                system_prompt=self.system_prompt_with_deepagent(stage="section_research", subagent_name="section_researcher"),
                user_prompt=prompt,
                schema=SectionResearchPacket,
            )
            if not packet.section_slug:
                packet.section_slug = slugify(section.heading)
            if not packet.section_heading:
                packet.section_heading = section.heading
            if not packet.section_purpose:
                packet.section_purpose = section.purpose
            packets.append(packet)
        return packets

    @staticmethod
    def _build_search_prompt(*, config: SeriesRunConfig, chapter_plan, section, blog_research: BlogResearchPacket) -> str:  # type: ignore[type-arg]
        key_points_text = "\n".join(f"- {kp}" for kp in (section.key_points or []))
        return (
            f"You are researching the section **'{section.heading}'** for a technical blog post.\n\n"
            f"**Series topic:** {config.topic}\n"
            f"**Target audience:** {config.target_audience}\n"
            f"**Part {chapter_plan.part_number}:** {chapter_plan.title}\n"
            f"**Section purpose:** {section.purpose}\n\n"
            f"**Key points to cover:**\n{key_points_text or '- General technical depth'}\n\n"
            f"**Your task:** Use web_search and fetch_url to find:\n"
            f"  1. Specific real-world production examples from engineering blogs (Netflix, Uber, Stripe, Airbnb, etc.)\n"
            f"  2. Recent papers or documentation on {section.heading.lower()} related to {config.topic}\n"
            f"  3. Quantitative benchmarks, failure modes, or architectural tradeoffs\n\n"
            f"Search for 2-3 specific queries, then fetch the 2-3 most relevant URLs. "
            f"Summarise what you found with exact titles, URLs, and key technical facts. "
            f"Do NOT fabricate sources — only report what you actually retrieved."
        )

    @staticmethod
    def _build_synthesis_prompt(*, config: SeriesRunConfig, chapter_plan, section, blog_research: BlogResearchPacket, evidence_text: str) -> str:  # type: ignore[type-arg]
        return (
            f"Using the research evidence below, produce a SectionResearchPacket for the section "
            f"**'{section.heading}'** (Part {chapter_plan.part_number}: {chapter_plan.title}).\n\n"
            f"**Topic:** {config.topic}  |  **Audience:** {config.target_audience}\n"
            f"**Section purpose:** {section.purpose}\n\n"
            f"---\n## DeepAgent Filesystem Guidance\n\n"
            f"Use the loaded memory, skills, and section_researcher role from the agent context. "
            f"Preserve exact URLs, image evidence, and code examples.\n---\n\n"
            f"---\n## Research Evidence Gathered\n\n{evidence_text}\n---\n\n"
            f"Instructions:\n"
            f"- Extract real source_notes from the evidence (title, URL, year, source_type, credibility). Always keep the exact URL when available.\n"
            f"- Write a research_summary grounded in facts actually found above — no invented claims.\n"
            f"- List supporting_points as specific, concrete bullet points from the evidence.\n"
            f"- Set visual_spec to a specific diagram idea motivated by the technical content found.\n"
            f"- If the evidence includes a usable image, populate image_url, image_credit_url, image_credit_text, and image_alt_text.\n"
            f"- For implementation-heavy sections, provide one original, syntactically valid code or config example via code_example and set code_example_language/code_example_title/code_example_notes.\n"
            f"- If no credible sources were found for a sub-topic, mark it explicitly.\n"
            f"Return valid JSON matching the SectionResearchPacket schema."
        )

    @staticmethod
    def _augment_evidence_if_needed(
        *,
        toolkit,
        config: SeriesRunConfig,
        chapter_plan: BlogChapterPlan,
        section: BlogSectionPlan,
        blog_research: BlogResearchPacket,
        evidence_text: str,
    ) -> str:
        if count_urls(evidence_text) >= 2:
            return evidence_text

        fallback_queries = [
            f"{config.topic} {chapter_plan.title} {section.heading} engineering blog",
            f"{section.heading} {config.topic} official documentation",
            f"{section.heading} {config.topic} paper",
        ]
        fallback_result = toolkit.research_queries(fallback_queries, fetch_top_n=2)
        blocks: list[str] = [evidence_text.strip()] if evidence_text.strip() else []
        fallback_block = fallback_result.as_context_block()
        if count_urls(fallback_block) > 0:
            blocks.append("### Deterministic Fallback Evidence")
            blocks.append(fallback_block)
        if blog_research.practical_references:
            blocks.append("### Chapter-Level References")
            for note in blog_research.practical_references[:4]:
                if note.url:
                    blocks.append(f"- {note.title}\nURL: {note.url}\n{note.note}")
        return "\n\n".join(block for block in blocks if block.strip())

    @staticmethod
    def _repair_packet(
        *,
        packet: SectionResearchPacket,
        section: BlogSectionPlan,
        blog_research: BlogResearchPacket,
        toolkit,
        evidence_text: str,
    ) -> SectionResearchPacket:
        evidence_sources = extract_source_notes_from_evidence(evidence_text, limit=6)
        if not packet.source_notes or all(not note.url for note in packet.source_notes):
            packet.source_notes = evidence_sources or [
                note for note in blog_research.practical_references if note.url
            ][:4] or blog_research.practical_references[:4]
        else:
            existing_urls = {note.url for note in packet.source_notes if note.url}
            for note in evidence_sources:
                if note.url and note.url not in existing_urls:
                    packet.source_notes.append(note)
                    existing_urls.add(note.url)

        packet.research_summary = sanitize_research_meta(
            packet.research_summary,
            fallback=section.purpose,
        )
        packet.supporting_points = sanitize_supporting_points(packet.supporting_points)

        if not packet.image_url:
            for note in packet.source_notes:
                if not note.url:
                    continue
                page = toolkit.fetch(note.url)
                if page.success and page.image_url:
                    packet.image_url = page.image_url
                    packet.image_credit_url = note.url
                    packet.image_credit_text = note.title
                    packet.image_alt_text = page.image_alt_text or section.heading
                    break

        return packet
