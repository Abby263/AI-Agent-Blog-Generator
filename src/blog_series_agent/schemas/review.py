"""Schemas for blog review reports."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, computed_field, field_validator


class ReviewRecommendation(str, Enum):
    """Final reviewer recommendation."""

    APPROVE = "approve"
    APPROVE_WITH_MINOR_CHANGES = "approve_with_minor_changes"
    REVISE = "revise"
    REJECT = "reject"


class ReviewScorecard(BaseModel):
    """Machine-readable blog scoring."""

    structure_consistency: int
    series_alignment: int
    clarity_of_explanation: int
    technical_accuracy: int
    technical_freshness: int
    depth_and_completeness: int
    readability_and_tone: int
    visuals_and_examples: int
    engagement_and_learning_reinforcement: int
    practical_relevance: int

    @field_validator("*")
    @classmethod
    def validate_score(cls, value: int) -> int:
        if not 0 <= value <= 10:
            raise ValueError("scores must be between 0 and 10")
        return value

    @computed_field
    @property
    def total_score(self) -> int:
        return sum(self.model_dump(exclude={"total_score", "consistency_score", "technical_quality_score"}).values())

    @computed_field
    @property
    def consistency_score(self) -> int:
        return (
            self.structure_consistency
            + self.series_alignment
            + self.clarity_of_explanation
            + self.readability_and_tone
            + self.engagement_and_learning_reinforcement
        )

    @computed_field
    @property
    def technical_quality_score(self) -> int:
        return (
            self.technical_accuracy
            + self.technical_freshness
            + self.depth_and_completeness
            + self.visuals_and_examples
            + self.practical_relevance
        )


class BlogReviewReport(BaseModel):
    """Full review result for a draft blog."""

    part_number: int
    slug: str
    title: str
    scorecard: ReviewScorecard
    strengths: list[str]
    issues: list[str]
    priority_fixes: list[str]
    suggested_additions: list[str]
    final_recommendation: ReviewRecommendation
    summary: str
    freshness_findings: list[str] = Field(default_factory=list)
    active_skills_checked: list[str] = Field(default_factory=list)
    skills_followed: list[str] = Field(default_factory=list)
    skills_violated: list[str] = Field(default_factory=list)
    skill_adherence_score: int = 0
    skill_adherence_notes: list[str] = Field(default_factory=list)
