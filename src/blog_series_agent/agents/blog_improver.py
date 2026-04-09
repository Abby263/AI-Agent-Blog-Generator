"""Blog improver agent."""

from __future__ import annotations

from ..config.settings import SeriesRunConfig
from ..schemas.memory import SkillRetrievalResult
from ..schemas.review import BlogReviewReport
from ..schemas.series import (
    BlogChapterPlan,
    BlogDraftPackage,
    BlogSeriesPart,
    SectionDraft,
    SectionResearchPacket,
)
from ..utils.markdown import normalize_markdown_document
from ..utils.slug import slugify
from .base import BaseAgent


class BlogImproverAgent(BaseAgent):
    prompt_name = "improver"
    section_prompt_name = "section_improver"
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
        )
        return self.context.llm.generate_text(system_prompt=self.system_prompt, user_prompt=prompt)

    def run_sectioned(
        self,
        config: SeriesRunConfig,
        part: BlogSeriesPart,
        chapter_plan: BlogChapterPlan,
        draft_package: BlogDraftPackage,
        section_research_packets: list[SectionResearchPacket],
        review_report: BlogReviewReport,
        retrieved_guidance: SkillRetrievalResult,
        lint_summary: str,
        approval_comments: str = "",
    ) -> BlogDraftPackage:
        review_summary = "\n".join(
            [
                review_report.summary,
                "Priority fixes:",
                *[f"- {item}" for item in review_report.priority_fixes],
            ]
        )
        research_map = {
            (packet.section_slug or slugify(packet.section_heading)): packet for packet in section_research_packets
        }
        draft_map = {section.section_slug: section for section in draft_package.section_drafts}
        improved_sections: list[SectionDraft] = []

        for section_plan in chapter_plan.section_plans:
            section_slug = slugify(section_plan.heading)
            draft_section = draft_map.get(section_slug) or SectionDraft(
                section_heading=section_plan.heading,
                section_slug=section_slug,
                markdown=f"## {section_plan.heading}",
            )
            research_packet = research_map.get(section_slug) or SectionResearchPacket(
                section_heading=section_plan.heading,
                section_slug=section_slug,
                section_purpose=section_plan.purpose,
                research_summary="",
                supporting_points=section_plan.key_points,
                source_notes=[],
                visual_spec="",
            )
            prompt = self.context.prompts.render(
                self.section_prompt_name,
                topic=config.topic,
                audience=config.target_audience,
                part_number=part.part_number,
                part_title=part.title,
                min_words=config.min_word_count,
                max_words=config.max_word_count,
                section_heading=section_plan.heading,
                section_purpose=section_plan.purpose,
                section_target_words=section_plan.target_words,
                visual_spec=research_packet.visual_spec or "Add one useful image, graph, or diagram.",
                section_research_summary=research_packet.research_summary or "None",
                section_sources=[
                    f"{note.title} ({note.source_type}, {note.year or 'year unknown'})"
                    for note in research_packet.source_notes
                ]
                or ["None"],
                retrieved_guidance=retrieved_guidance.retrieved_guidance or ["None"],
                violated_skills=review_report.skills_violated or ["None"],
                review_summary=review_summary,
                lint_findings=lint_summary,
                approval_comments=approval_comments or "None",
                draft_section=draft_section.markdown,
            )
            output = self.context.llm.generate_text(
                system_prompt=self.system_prompt,
                user_prompt=prompt,
                max_tokens=max(220, min(800, int(max(120, section_plan.target_words) * 1.8))),
            )
            improved_markdown = self._ensure_section_requirements(
                normalize_markdown_document(output) or draft_section.markdown,
                heading=section_plan.heading,
                research_packet=research_packet,
            )
            improved_sections.append(
                SectionDraft(
                    section_heading=section_plan.heading,
                    section_slug=section_slug,
                    markdown=improved_markdown,
                    source_titles=[note.title for note in research_packet.source_notes],
                    visual_spec=research_packet.visual_spec,
                )
            )

        return BlogDraftPackage(
            part_number=draft_package.part_number,
            slug=draft_package.slug,
            title=draft_package.title,
            full_markdown=self._assemble_markdown(
                chapter_plan,
                improved_sections,
                self._extract_series_navigation(draft_package.full_markdown),
            ),
            section_drafts=improved_sections,
        )

    @staticmethod
    def _assemble_markdown(
        chapter_plan: BlogChapterPlan,
        section_drafts: list[SectionDraft],
        series_navigation: str,
    ) -> str:
        toc_lines = [f"{index}. {section.heading}" for index, section in enumerate(chapter_plan.section_plans, start=1)]
        parts = [
            f"# {chapter_plan.title}",
            f"## {chapter_plan.subtitle}",
            "",
            "### Posts in this Series",
            series_navigation or "- Series navigation unavailable.",
            "",
            "### Table of Contents",
            *toc_lines,
            "",
        ]
        for section in section_drafts:
            parts.extend([section.markdown.strip(), ""])
        return "\n".join(parts).strip()

    @staticmethod
    def _ensure_section_requirements(markdown: str, *, heading: str, research_packet: SectionResearchPacket) -> str:
        body = markdown.strip()
        if not body.startswith("#"):
            body = f"## {heading}\n\n{body}"
        if len(body.split()) < 80:
            body = BlogImproverAgent._inject_fallback_content(body, heading=heading, research_packet=research_packet)
        if "[Image:" not in body:
            visual_spec = research_packet.visual_spec or (
                f"[Image: A graph or diagram for {heading} that explains the system behavior, key tradeoffs, and what matters operationally.]"
            )
            if not visual_spec.startswith("[Image:"):
                visual_spec = f"[Image: {visual_spec}]"
            body = f"{body}\n\n{visual_spec}"
        if "Sources for This Section" not in body:
            lines = ["#### Sources for This Section"]
            for note in research_packet.source_notes:
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
    def _inject_fallback_content(markdown: str, *, heading: str, research_packet: SectionResearchPacket) -> str:
        fallback_paragraphs = [
            research_packet.research_summary.strip() or f"This section covers {heading.lower()} using the supporting research packet for the chapter.",
        ]
        for point in research_packet.supporting_points[:4]:
            point = point.strip().rstrip(".")
            if point:
                fallback_paragraphs.append(f"{point}.")
        fallback_body = "\n\n".join(paragraph for paragraph in fallback_paragraphs if paragraph)
        if markdown.startswith("## "):
            _, _, remainder = markdown.partition("\n")
            return f"## {heading}\n\n{fallback_body}\n{remainder}".strip()
        return f"## {heading}\n\n{fallback_body}\n\n{markdown}".strip()

    @staticmethod
    def _extract_series_navigation(markdown: str) -> str:
        start_marker = "### Posts in this Series"
        end_marker = "### Table of Contents"
        if start_marker not in markdown or end_marker not in markdown:
            return ""
        segment = markdown.split(start_marker, maxsplit=1)[1].split(end_marker, maxsplit=1)[0]
        return segment.strip()
