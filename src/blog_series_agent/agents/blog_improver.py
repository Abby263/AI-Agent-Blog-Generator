"""Blog improver agent."""

from __future__ import annotations

import textwrap

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
from ..utils.research import sanitize_research_meta
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
            deepagent_guidance=self.deepagent_guidance(stage="final", subagent_name="writer"),
        )
        return self.context.llm.generate_text(
            system_prompt=self.system_prompt_with_deepagent(stage="final", subagent_name="writer"),
            user_prompt=prompt,
        )

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
                source_links=self._source_links(research_packet),
                retrieved_guidance=retrieved_guidance.retrieved_guidance or ["None"],
                violated_skills=review_report.skills_violated or ["None"],
                deepagent_guidance=self.deepagent_guidance(stage="final", subagent_name="writer"),
                review_summary=review_summary,
                lint_findings=lint_summary,
                approval_comments=approval_comments or "None",
                draft_section=draft_section.markdown,
            )
            output = self.context.llm.generate_text(
                system_prompt=self.system_prompt_with_deepagent(stage="final", subagent_name="writer"),
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
        body = BlogImproverAgent._strip_meta_boilerplate(markdown.strip())
        if not body.startswith("#"):
            body = f"## {heading}\n\n{body}"
        if len(body.split()) < 80:
            body = BlogImproverAgent._inject_fallback_content(body, heading=heading, research_packet=research_packet)
        if "![" not in body and "[Image:" not in body:
            body = f"{body}\n\n{BlogImproverAgent._render_visual_block(heading, research_packet)}"
        if BlogImproverAgent._requires_code_example(heading) and not BlogImproverAgent._has_code_block(body):
            body = f"{body}\n\n{BlogImproverAgent._render_code_block(heading, research_packet)}"
        if "![" in body and "_Image credit:" not in body and research_packet.image_url:
            body = f"{body}\n\n_Image credit: [{research_packet.image_credit_text or 'Source'}]({research_packet.image_credit_url or research_packet.image_url})_"
        if "Sources for This Section" not in body:
            lines = ["#### Sources for This Section"]
            for note in research_packet.source_notes:
                title = f"[{note.title}]({note.url})" if note.url else note.title
                descriptor = f"{title} ({note.source_type}"
                if note.year:
                    descriptor += f", {note.year}"
                descriptor += ")"
                lines.append(f"- {descriptor}")
            if len(lines) == 1:
                lines.append("- No explicit sources were captured for this section.")
            body = f"{body}\n\n" + "\n".join(lines)
        elif research_packet.source_notes and not any((note.url and note.url in body) for note in research_packet.source_notes):
            body = f"{body}\n" + "\n".join(
                f"- [{note.title}]({note.url})" if note.url else f"- {note.title}"
                for note in research_packet.source_notes
            )
        return body.strip()

    @staticmethod
    def _inject_fallback_content(markdown: str, *, heading: str, research_packet: SectionResearchPacket) -> str:
        fallback_paragraphs = [
            sanitize_research_meta(
                research_packet.research_summary.strip(),
                fallback=f"This section covers {heading.lower()} using the supporting research packet for the chapter.",
            ),
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
    def _strip_meta_boilerplate(markdown: str) -> str:
        paragraphs = [segment.strip() for segment in markdown.split("\n\n")]
        cleaned: list[str] = []
        for paragraph in paragraphs:
            if (
                paragraph.startswith("#")
                or paragraph.startswith("```")
                or paragraph.startswith("![")
                or paragraph.startswith("[Image:")
                or paragraph.startswith("#### Sources for This Section")
            ):
                cleaned.append(paragraph)
                continue
            sanitized = sanitize_research_meta(paragraph)
            if sanitized:
                cleaned.append(sanitized)
        return "\n\n".join(cleaned).strip()

    @staticmethod
    def _source_links(research_packet: SectionResearchPacket) -> list[str]:
        if not research_packet.source_notes:
            return ["None"]
        return [
            f"{note.title}: {note.url}" if note.url else f"{note.title}: no URL available"
            for note in research_packet.source_notes
        ]

    @staticmethod
    def _render_visual_block(heading: str, research_packet: SectionResearchPacket) -> str:
        if research_packet.image_url:
            alt = research_packet.image_alt_text or heading
            credit_text = research_packet.image_credit_text or "Source"
            credit_url = research_packet.image_credit_url or research_packet.image_url
            return "\n".join(
                [
                    f"![{alt}]({research_packet.image_url})",
                    f"_Image credit: [{credit_text}]({credit_url})_",
                ]
            )
        visual_spec = research_packet.visual_spec or (
            f"[Image: A graph or diagram for {heading} that explains the system behavior, key tradeoffs, and what matters operationally.]"
        )
        if not visual_spec.startswith("[Image:"):
            visual_spec = f"[Image: {visual_spec}]"
        return visual_spec

    @staticmethod
    def _requires_code_example(heading: str) -> bool:
        normalized = heading.strip().lower()
        return normalized in {
            "detailed core sections",
            "system / architecture thinking",
            "how this works in modern systems",
            "real-world examples",
        }

    @staticmethod
    def _has_code_block(markdown: str) -> bool:
        return "```" in markdown

    @staticmethod
    def _render_code_block(heading: str, research_packet: SectionResearchPacket) -> str:
        if research_packet.code_example:
            language = research_packet.code_example_language or "text"
            title = research_packet.code_example_title or f"{heading} example"
            notes = research_packet.code_example_notes or "Illustrative example grounded in the section research."
            return "\n".join(
                [
                    f"**{title}**",
                    f"```{language}",
                    research_packet.code_example.strip(),
                    "```",
                    notes,
                ]
            )

        fallback = textwrap.dedent(
            """
            monitoring_rule:
              name: section_monitor
              window: 1h
              baseline: 7d
              checks:
                - metric: distribution_shift
                  threshold: 0.20
                - metric: missing_value_rate
                  threshold: 0.05
              notify:
                severity: medium
                channel: oncall-ml
            """
        ).strip()
        return "\n".join(
            [
                "**Example monitoring configuration**",
                "```yaml",
                fallback,
                "```",
                "This config is a syntactically valid starting point that the reader can adapt to the section's operational pattern.",
            ]
        )

    @staticmethod
    def _extract_series_navigation(markdown: str) -> str:
        start_marker = "### Posts in this Series"
        end_marker = "### Table of Contents"
        if start_marker not in markdown or end_marker not in markdown:
            return ""
        segment = markdown.split(start_marker, maxsplit=1)[1].split(end_marker, maxsplit=1)[0]
        return segment.strip()
