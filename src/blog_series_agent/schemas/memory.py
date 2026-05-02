"""Schemas for structured feedback and reusable skill memory."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class FeedbackType(str, Enum):
    STRUCTURAL_ISSUE = "structural_issue"
    CLARITY_ISSUE = "clarity_issue"
    STYLE_ISSUE = "style_issue"
    TECHNICAL_ISSUE = "technical_issue"
    FRESHNESS_ISSUE = "freshness_issue"
    REPETITION_ISSUE = "repetition_issue"
    TONE_ISSUE = "tone_issue"
    EXAMPLE_QUALITY_ISSUE = "example_quality_issue"
    CITATION_ISSUE = "citation_issue"
    VISUAL_ISSUE = "visual_issue"
    SERIES_CONTINUITY_ISSUE = "series_continuity_issue"
    SKILL_VIOLATION = "skill_violation"


class FeedbackSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackSourceType(str, Enum):
    REVIEWER = "reviewer"
    APPROVAL = "approval"
    USER = "user"
    EVALUATION = "evaluation"


class SkillStatus(str, Enum):
    CANDIDATE = "candidate"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class FeedbackItem(BaseModel):
    """Normalized feedback item stored in the raw feedback log."""

    feedback_id: str
    source_type: FeedbackSourceType
    source_artifact: str
    part_number: int | None = None
    blog_slug: str | None = None
    raw_feedback: str
    normalized_issue_type: FeedbackType
    severity: FeedbackSeverity
    suggested_fix: str
    reviewer: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    run_id: str | None = None


class SkillTriggerConditions(BaseModel):
    """Conditions used to determine when a skill is relevant."""

    topic_keywords: list[str] = Field(default_factory=list)
    audience_levels: list[str] = Field(default_factory=list)
    part_numbers: list[int] = Field(default_factory=list)
    blog_types: list[str] = Field(default_factory=list)
    issue_types: list[str] = Field(default_factory=list)
    artifact_types: list[str] = Field(default_factory=list)


class ReusableSkill(BaseModel):
    """Candidate or approved reusable guidance distilled from feedback."""

    id: str
    title: str
    category: str
    trigger_conditions: SkillTriggerConditions = Field(default_factory=SkillTriggerConditions)
    guidance_text: str
    source_feedback_ids: list[str] = Field(default_factory=list)
    confidence_score: float
    usage_count: int = 0
    status: SkillStatus = SkillStatus.CANDIDATE
    active: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SkillRetrievalQuery(BaseModel):
    """Query used to retrieve relevant approved skills."""

    topic: str
    audience: str
    part_number: int | None = None
    blog_type: str = "technical_blog"
    issue_types: list[str] = Field(default_factory=list)
    artifact_type: str = "draft"
    max_skills: int = 5


class SkillRetrievalResult(BaseModel):
    """Inspectable retrieval result used in prompts."""

    query: SkillRetrievalQuery
    retrieved_skill_ids: list[str] = Field(default_factory=list)
    retrieved_guidance: list[str] = Field(default_factory=list)
    retrieval_notes: list[str] = Field(default_factory=list)


class MemoryUpdateResult(BaseModel):
    """Result of one memory update cycle."""

    feedback_items_logged: list[FeedbackItem] = Field(default_factory=list)
    candidate_skills_created: list[ReusableSkill] = Field(default_factory=list)
    auto_approved_skill_ids: list[str] = Field(default_factory=list)


class SkillExtractionBatch(BaseModel):
    """Structured response for extracted candidate skills."""

    candidate_skills: list[ReusableSkill] = Field(default_factory=list)
