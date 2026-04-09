"""Blog writer agent."""

from __future__ import annotations

from ..config.settings import SeriesRunConfig
from ..schemas.memory import SkillRetrievalResult
from ..schemas.series import (
    BlogChapterPlan,
    BlogDraftPackage,
    BlogResearchPacket,
    BlogSectionPlan,
    BlogSeriesOutline,
    BlogSeriesPart,
    SectionDraft,
    SectionResearchPacket,
)
from ..utils.markdown import normalize_markdown_document
from ..utils.slug import slugify
from .base import BaseAgent


class BlogWriterAgent(BaseAgent):
    prompt_name = "blog_section_writer"
    system_prompt = (
        "You are a senior technical educator writing polished, human, deep, Medium-ready articles."
    )

    def run(
        self,
        config: SeriesRunConfig,
        outline: BlogSeriesOutline,
        part: BlogSeriesPart,
        research: BlogResearchPacket,
        chapter_plan: BlogChapterPlan,
        section_research_packets: list[SectionResearchPacket],
        retrieved_guidance: SkillRetrievalResult,
        recent_mistakes_to_avoid: list[str],
    ) -> BlogDraftPackage:
        series_navigation = "\n".join(
            f"- Part {series_part.part_number}: {series_part.title}"
            + (" (This Post)" if series_part.part_number == part.part_number else "")
            for series_part in outline.parts
        )
        section_targets = self._normalized_section_targets(
            chapter_plan.section_plans,
            config.min_word_count,
            config.max_word_count,
        )
        section_outputs: list[SectionDraft] = []
        completed_sections: list[str] = []
        section_research_map = {
            (packet.section_slug or slugify(packet.section_heading)): packet for packet in section_research_packets
        }

        for section, target_words in zip(chapter_plan.section_plans, section_targets, strict=False):
            section_max_words = max(target_words + 40, int(target_words * 1.2))
            section_slug = slugify(section.heading)
            section_research = section_research_map.get(section_slug) or self._fallback_research(section, research)
            prompt = self.context.prompts.render(
                self.prompt_name,
                topic=config.topic,
                audience=config.target_audience,
                part_number=part.part_number,
                part_title=chapter_plan.title,
                part_subtitle=chapter_plan.subtitle,
                section_heading=section.heading,
                section_purpose=section.purpose,
                section_key_points=section.key_points or ["- None"],
                section_subsections=section.subsections or ["- None"],
                target_words=target_words,
                section_max_words=section_max_words,
                chapter_summary=chapter_plan.chapter_summary,
                previous_part_callback=chapter_plan.previous_part_callback or "None",
                next_part_teaser=chapter_plan.next_part_teaser or "None",
                series_navigation=series_navigation,
                research_summary=section_research.research_summary or research.summary,
                practical_references=[
                    f"{note.title} ({note.source_type}, {note.year or 'year unknown'})"
                    for note in section_research.source_notes
                ]
                or [
                    f"{note.title} ({note.source_type}, {note.year or 'year unknown'})"
                    for note in research.practical_references
                ]
                or ["None"],
                citation_anchors=research.citation_anchors or ["None"],
                active_skills=retrieved_guidance.retrieved_guidance or ["- None"],
                recent_mistakes=recent_mistakes_to_avoid or ["- None"],
                completed_sections=completed_sections or ["- None"],
                visual_requirement="Yes" if section.requires_visual else "No",
                visual_spec=section_research.visual_spec or "Add one purposeful visual for this section.",
                supporting_points=section_research.supporting_points or ["None"],
            )
            output = self.context.llm.generate_text(
                system_prompt=self.system_prompt,
                user_prompt=prompt,
                max_tokens=max(180, min(700, int(section_max_words * 1.8))),
            )
            section_markdown = self._ensure_section_requirements(
                normalize_markdown_document(output),
                section=section,
                section_research=section_research,
            )
            section_outputs.append(
                SectionDraft(
                    section_heading=section.heading,
                    section_slug=section_slug,
                    markdown=section_markdown,
                    source_titles=[note.title for note in section_research.source_notes],
                    visual_spec=section_research.visual_spec,
                )
            )
            completed_sections.append(section.heading)

        full_markdown = self._assemble_markdown(
            chapter_plan=chapter_plan,
            series_navigation=series_navigation,
            section_outputs=[section.markdown for section in section_outputs],
        )
        return BlogDraftPackage(
            part_number=part.part_number,
            slug=part.slug,
            title=chapter_plan.title,
            full_markdown=full_markdown,
            section_drafts=section_outputs,
        )

    @staticmethod
    def _normalized_section_targets(
        section_plans: list[BlogSectionPlan],
        minimum_words: int,
        maximum_words: int,
    ) -> list[int]:
        if not section_plans:
            return []
        heading_caps = {
            "detailed core sections": 360,
            "system / architecture thinking": 220,
            "references": 110,
            "key takeaways": 120,
            "test your learning": 130,
        }
        raw_targets = [
            min(
                heading_caps.get(section.heading.strip().lower(), 180),
                max(80, section.target_words),
            )
            for section in section_plans
        ]
        total = sum(raw_targets)
        desired_total = max(minimum_words + 80, min((minimum_words + maximum_words) // 2, maximum_words - 120))
        if total == 0:
            return [120 for _ in section_plans]
        scale = desired_total / total
        normalized = [
            min(
                heading_caps.get(section.heading.strip().lower(), 180),
                max(70, int(target * scale)),
            )
            for section, target in zip(section_plans, raw_targets, strict=False)
        ]
        return normalized

    @staticmethod
    def _assemble_markdown(
        *,
        chapter_plan: BlogChapterPlan,
        series_navigation: str,
        section_outputs: list[str],
    ) -> str:
        toc_lines = [f"{index}. {section.heading}" for index, section in enumerate(chapter_plan.section_plans, start=1)]
        parts = [
            f"# {chapter_plan.title}",
            f"## {chapter_plan.subtitle}",
            "",
            "### Posts in this Series",
            series_navigation,
            "",
            "### Table of Contents",
            *toc_lines,
            "",
        ]
        for section_output in section_outputs:
            parts.extend([section_output.strip(), ""])
        return "\n".join(parts).strip()

    @staticmethod
    def _fallback_research(section: BlogSectionPlan, research: BlogResearchPacket) -> SectionResearchPacket:
        return SectionResearchPacket(
            section_heading=section.heading,
            section_slug=slugify(section.heading),
            section_purpose=section.purpose,
            research_summary=research.summary,
            supporting_points=section.key_points,
            source_notes=research.practical_references[:3],
            visual_spec=f"Diagram or graph for {section.heading} showing the main system relationship and teaching point.",
        )

    @staticmethod
    def _ensure_section_requirements(
        markdown: str,
        *,
        section: BlogSectionPlan,
        section_research: SectionResearchPacket,
    ) -> str:
        body = markdown.strip()
        if not body.startswith("#"):
            body = f"## {section.heading}\n\n{body}"
        if len(body.split()) < 80:
            body = BlogWriterAgent._inject_fallback_content(
                body,
                heading=section.heading,
                section_purpose=section.purpose,
                section_research=section_research,
            )

        if "[Image:" not in body:
            visual_spec = section_research.visual_spec or (
                f"[Image: A diagram for {section.heading} that explains the main mechanism, key tradeoffs, and what the reader should notice.]"
            )
            if not visual_spec.startswith("[Image:"):
                visual_spec = f"[Image: {visual_spec}]"
            body = f"{body}\n\n{visual_spec}"

        if "Sources for This Section" not in body:
            lines = ["#### Sources for This Section"]
            for note in section_research.source_notes:
                descriptor = f"{note.title} ({note.source_type}"
                if note.year:
                    descriptor += f", {note.year}"
                descriptor += ")"
                lines.append(f"- {descriptor}")
            if len(lines) == 1:
                lines.append("- No explicit sources were captured for this section.")
            body = f"{body}\n\n" + "\n".join(lines)
        return body.strip()

    @staticmethod
    def _inject_fallback_content(
        markdown: str,
        *,
        heading: str,
        section_purpose: str,
        section_research: SectionResearchPacket,
    ) -> str:
        fallback_paragraphs = [
            section_research.research_summary.strip() or section_purpose.strip() or f"This section explains {heading.lower()} in practical system-design terms.",
        ]
        for point in section_research.supporting_points[:4]:
            point = point.strip().rstrip(".")
            if point:
                fallback_paragraphs.append(f"{point}.")
        fallback_body = "\n\n".join(paragraph for paragraph in fallback_paragraphs if paragraph)
        if markdown.startswith("## "):
            _, _, remainder = markdown.partition("\n")
            return f"## {heading}\n\n{fallback_body}\n{remainder}".strip()
        return f"## {heading}\n\n{fallback_body}\n\n{markdown}".strip()
