"""Schemas for topic research, outlines, and blog artifacts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SourceNote(BaseModel):
    """A research note backed by a source."""

    title: str
    source_type: str
    url: str | None = None
    note: str
    recency: str | None = None
    year: int | None = None
    credibility: str = "unknown"


class TopicResearchDossier(BaseModel):
    """High-level topic research for the full series."""

    topic: str
    target_audience: str
    positioning_summary: str
    key_themes: list[str]
    glossary: list[str]
    recent_developments: list[str]
    recommended_progression: list[str]
    source_notes: list[SourceNote] = Field(default_factory=list)
    citation_summary: str = ""
    freshness_notes: list[str] = Field(default_factory=list)


class BlogSeriesPart(BaseModel):
    """One planned part in a blog series."""

    part_number: int
    title: str
    slug: str
    purpose: str
    prerequisite_context: list[str]
    key_concepts: list[str]
    recommended_diagrams: list[str]
    dependencies_on_previous: list[int] = Field(default_factory=list)


class BlogSeriesOutline(BaseModel):
    """The full outline for a technical blog series."""

    topic: str
    target_audience: str
    narrative_arc: str
    learning_goals: list[str]
    parts: list[BlogSeriesPart]


class BlogResearchPacket(BaseModel):
    """Part-specific research dossier used by the writer."""

    part_number: int
    slug: str
    title: str
    summary: str
    core_questions: list[str]
    examples: list[str]
    system_design_insights: list[str]
    practical_references: list[SourceNote]
    freshness_notes: list[str] = Field(default_factory=list)
    citation_anchors: list[str] = Field(default_factory=list)


class SectionResearchPacket(BaseModel):
    """Section-specific research packet used by the section writer."""

    section_heading: str
    section_slug: str = ""
    section_purpose: str
    research_summary: str
    supporting_points: list[str] = Field(default_factory=list)
    source_notes: list[SourceNote] = Field(default_factory=list)
    visual_spec: str = ""


class SectionDraft(BaseModel):
    """Section-level draft artifact."""

    section_heading: str
    section_slug: str
    markdown: str
    source_titles: list[str] = Field(default_factory=list)
    visual_spec: str = ""


class BlogDraftPackage(BaseModel):
    """Assembled draft plus section-level outputs."""

    part_number: int
    slug: str
    title: str
    full_markdown: str
    section_drafts: list[SectionDraft] = Field(default_factory=list)


class BlogSectionPlan(BaseModel):
    """One planned section inside a chapter-style blog post."""

    heading: str
    purpose: str
    key_points: list[str] = Field(default_factory=list)
    target_words: int = 150
    subsections: list[str] = Field(default_factory=list)
    requires_visual: bool = False


class BlogChapterPlan(BaseModel):
    """Structured table of contents and section plan for a single blog."""

    part_number: int
    slug: str
    title: str
    subtitle: str
    chapter_summary: str
    previous_part_callback: str = ""
    next_part_teaser: str = ""
    section_plans: list[BlogSectionPlan] = Field(default_factory=list)


class AssetPlan(BaseModel):
    """Diagram and visual plan for a blog post."""

    part_number: int
    slug: str
    summary: str
    visuals: list[str]
    chart_ideas: list[str]
    table_ideas: list[str]
    callout_opportunities: list[str]
