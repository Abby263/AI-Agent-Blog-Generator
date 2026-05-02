"""Markdown renderers for structured artifacts."""

from __future__ import annotations

from ..schemas.approval import ApprovalRecord
from ..schemas.memory import ReusableSkill
from ..schemas.review import BlogReviewReport
from ..schemas.series import (
    AssetPlan,
    BlogChapterPlan,
    BlogDraftPackage,
    BlogResearchPacket,
    SectionResearchPacket,
    BlogSeriesOutline,
    TopicResearchDossier,
)


def _format_source_markdown(title: str, url: str | None, suffix: str = "") -> str:
    label = f"[{title}]({url})" if url else title
    return f"{label}{suffix}"


def render_topic_research_markdown(dossier: TopicResearchDossier) -> str:
    return "\n".join(
        [
            f"# Topic Research: {dossier.topic}",
            "",
            f"**Audience:** {dossier.target_audience}",
            "",
            "## Positioning Summary",
            dossier.positioning_summary,
            "",
            "## Key Themes",
            *[f"- {item}" for item in dossier.key_themes],
            "",
            "## Recent Developments",
            *[f"- {item}" for item in dossier.recent_developments],
            "",
            "## Recommended Progression",
            *[f"- {item}" for item in dossier.recommended_progression],
            "",
            "## Source Notes",
            *[
                "- "
                + _format_source_markdown(note.title, note.url, f" ({note.source_type})")
                + f": {note.note}"
                for note in dossier.source_notes
            ],
        ]
    )


def render_outline_markdown(outline: BlogSeriesOutline) -> str:
    lines = [
        f"# Blog Series Outline: {outline.topic}",
        "",
        f"**Audience:** {outline.target_audience}",
        "",
        "## Narrative Arc",
        outline.narrative_arc,
        "",
        "## Learning Goals",
        *[f"- {goal}" for goal in outline.learning_goals],
        "",
        "## Parts",
    ]
    for part in outline.parts:
        lines.extend(
            [
                f"### Part {part.part_number}: {part.title}",
                f"- **Slug:** {part.slug}",
                f"- **Purpose:** {part.purpose}",
                f"- **Prerequisite Context:** {', '.join(part.prerequisite_context) or 'None'}",
                f"- **Key Concepts:** {', '.join(part.key_concepts)}",
                f"- **Recommended Diagrams:** {', '.join(part.recommended_diagrams)}",
                f"- **Dependencies:** {', '.join(str(dep) for dep in part.dependencies_on_previous) or 'None'}",
                "",
            ]
        )
    return "\n".join(lines)


def render_blog_research_markdown(packet: BlogResearchPacket) -> str:
    return "\n".join(
        [
            f"# Blog Research: Part {packet.part_number} - {packet.title}",
            "",
            "## Summary",
            packet.summary,
            "",
            "## Core Questions",
            *[f"- {item}" for item in packet.core_questions],
            "",
            "## Examples",
            *[f"- {item}" for item in packet.examples],
            "",
            "## System Design Insights",
            *[f"- {item}" for item in packet.system_design_insights],
            "",
            "## Practical References",
            *[
                "- "
                + _format_source_markdown(note.title, note.url, f" ({note.source_type})")
                + f": {note.note}"
                for note in packet.practical_references
            ],
        ]
    )


def render_section_research_markdown(packet: SectionResearchPacket) -> str:
    return "\n".join(
        [
            f"# Section Research: {packet.section_heading}",
            "",
            "## Purpose",
            packet.section_purpose,
            "",
            "## Summary",
            packet.research_summary,
            "",
            "## Supporting Points",
            *[f"- {item}" for item in packet.supporting_points],
            "",
            "## Sources",
            *[
                "- "
                + _format_source_markdown(
                    note.title,
                    note.url,
                    f" ({note.source_type}, {note.year or 'year unknown'})",
                )
                + f": {note.note}"
                for note in packet.source_notes
            ],
            "",
            "## Visual Spec",
            packet.visual_spec or "None",
            "",
            "## Image Asset",
            f"- **Image URL:** {packet.image_url or 'None'}",
            f"- **Image Credit URL:** {packet.image_credit_url or 'None'}",
            f"- **Image Credit Text:** {packet.image_credit_text or 'None'}",
            f"- **Image Alt Text:** {packet.image_alt_text or 'None'}",
            "",
            "## Code Example",
            f"- **Title:** {packet.code_example_title or 'None'}",
            f"- **Language:** {packet.code_example_language or 'None'}",
            packet.code_example or "None",
            f"- **Notes:** {packet.code_example_notes or 'None'}",
        ]
    )


def render_blog_plan_markdown(plan: BlogChapterPlan) -> str:
    lines = [
        f"# Blog Plan: Part {plan.part_number} - {plan.title}",
        "",
        f"**Subtitle:** {plan.subtitle}",
        "",
        "## Chapter Summary",
        plan.chapter_summary,
        "",
        "## Series Continuity",
        f"- Previous callback: {plan.previous_part_callback or 'None'}",
        f"- Next teaser: {plan.next_part_teaser or 'None'}",
        "",
        "## Table of Contents Plan",
    ]
    for section in plan.section_plans:
        lines.extend(
            [
                f"### {section.heading}",
                f"- **Purpose:** {section.purpose}",
                f"- **Target Words:** {section.target_words}",
                f"- **Requires Visual:** {section.requires_visual}",
                f"- **Key Points:** {', '.join(section.key_points) or 'None'}",
                f"- **Subsections:** {', '.join(section.subsections) or 'None'}",
                "",
            ]
        )
    return "\n".join(lines)


def render_section_draft_markdown(draft: BlogDraftPackage, section_slug: str) -> str:
    for section in draft.section_drafts:
        if section.section_slug == section_slug:
            return section.markdown
    return ""


def render_review_markdown(report: BlogReviewReport) -> str:
    scorecard = report.scorecard
    return "\n".join(
        [
            f"# Review Report: Part {report.part_number} - {report.title}",
            "",
            f"**Total Score:** {scorecard.total_score}/100",
            f"**Consistency Score:** {scorecard.consistency_score}/50",
            f"**Technical Quality Score:** {scorecard.technical_quality_score}/50",
            f"**Recommendation:** {report.final_recommendation}",
            "",
            "## Summary",
            report.summary,
            "",
            "## Strengths",
            *[f"- {item}" for item in report.strengths],
            "",
            "## Issues",
            *[f"- {item}" for item in report.issues],
            "",
            "## Priority Fixes",
            *[f"- {item}" for item in report.priority_fixes],
            "",
            "## Suggested Additions",
            *[f"- {item}" for item in report.suggested_additions],
            "",
            "## Freshness Findings",
            *[f"- {item}" for item in report.freshness_findings],
            "",
            "## Skill Adherence",
            f"- **Active Skills Checked:** {', '.join(report.active_skills_checked) or 'None'}",
            f"- **Skills Followed:** {', '.join(report.skills_followed) or 'None'}",
            f"- **Skills Violated:** {', '.join(report.skills_violated) or 'None'}",
            f"- **Skill Adherence Score:** {report.skill_adherence_score}/10",
            *[f"- {item}" for item in report.skill_adherence_notes],
        ]
    )


def render_asset_plan_markdown(plan: AssetPlan) -> str:
    return "\n".join(
        [
            f"# Asset Plan: Part {plan.part_number} - {plan.slug}",
            "",
            "## Summary",
            plan.summary,
            "",
            "## Visuals",
            *[f"- {item}" for item in plan.visuals],
            "",
            "## Chart Ideas",
            *[f"- {item}" for item in plan.chart_ideas],
            "",
            "## Table Ideas",
            *[f"- {item}" for item in plan.table_ideas],
            "",
            "## Callout Opportunities",
            *[f"- {item}" for item in plan.callout_opportunities],
        ]
    )


def render_approval_markdown(record: ApprovalRecord) -> str:
    return "\n".join(
        [
            f"# Approval Record: Part {record.part_number} - {record.slug}",
            "",
            f"**Status:** {record.status}",
            f"**Reviewer:** {record.reviewer_name}",
            f"**Timestamp:** {record.timestamp.isoformat()}",
            "",
            "## Comments",
            record.comments or "No comments provided.",
            "",
            "## Linked Artifacts",
            f"- Draft: {record.draft_path or 'N/A'}",
            f"- Review: {record.review_path or 'N/A'}",
            f"- Final: {record.final_path or 'N/A'}",
            f"- Asset Plan: {record.asset_plan_path or 'N/A'}",
        ]
    )


def render_skills_markdown(title: str, skills: list[ReusableSkill]) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            *(
                [
                    "\n".join(
                        [
                            f"## {skill.title}",
                            f"- **ID:** {skill.id}",
                            f"- **Category:** {skill.category}",
                            f"- **Status:** {skill.status}",
                            f"- **Active:** {skill.active}",
                            f"- **Usage Count:** {skill.usage_count}",
                            f"- **Confidence:** {skill.confidence_score}",
                            f"- **Guidance:** {skill.guidance_text}",
                            f"- **Source Feedback IDs:** {', '.join(skill.source_feedback_ids) or 'None'}",
                        ]
                    )
                    for skill in skills
                ]
                if skills
                else ["No skills available."]
            ),
        ]
    )
