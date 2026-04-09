"""Evaluation schemas for blog, series, and run quality assessment."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, computed_field, field_validator


class EvaluationSeverity(str, Enum):
    """Severity or priority level for an evaluation issue or action."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CriterionScore(BaseModel):
    """One scored evaluation criterion."""

    name: str
    score: float
    rationale: str
    evidence: list[str] = Field(default_factory=list)
    severity: EvaluationSeverity = EvaluationSeverity.LOW
    recommended_action: str = ""

    @field_validator("score")
    @classmethod
    def validate_score(cls, value: float) -> float:
        if not 0 <= value <= 10:
            raise ValueError("criterion score must be between 0 and 10")
        return value


class EvaluationIssue(BaseModel):
    """A concrete issue found by evaluation."""

    issue_id: str
    issue_type: str
    severity: EvaluationSeverity
    description: str
    evidence: list[str] = Field(default_factory=list)
    recommended_action: str
    frequency: int = 1
    related_skill_ids: list[str] = Field(default_factory=list)


class EvaluationTrend(BaseModel):
    """Trend observed across a run or a set of outputs."""

    name: str
    direction: str
    evidence: list[str] = Field(default_factory=list)
    summary: str


class RepeatedFailurePattern(BaseModel):
    """A repeated issue pattern across outputs."""

    pattern_id: str
    issue_type: str
    frequency: int
    affected_parts: list[int] = Field(default_factory=list)
    summary: str
    recommended_action: str
    related_feedback_ids: list[str] = Field(default_factory=list)


class ImprovementOpportunity(BaseModel):
    """A suggested improvement opportunity surfaced by evaluation."""

    title: str
    priority: EvaluationSeverity
    target_scope: str
    rationale: str
    recommended_action: str
    related_issues: list[str] = Field(default_factory=list)


class ContentLintFinding(BaseModel):
    """Deterministic content quality finding."""

    finding_type: str
    severity: EvaluationSeverity
    message: str
    recommended_action: str


class ContentLintReport(BaseModel):
    """Deterministic quality gate report for generated Markdown."""

    word_count: int
    missing_sections: list[str] = Field(default_factory=list)
    placeholder_visuals: list[str] = Field(default_factory=list)
    weak_references: list[str] = Field(default_factory=list)
    findings: list[ContentLintFinding] = Field(default_factory=list)


class BlogEvaluation(BaseModel):
    """Evaluation of a single blog artifact."""

    part_number: int
    slug: str
    title: str
    criteria: list[CriterionScore]
    summary: str
    strengths: list[str] = Field(default_factory=list)
    issues: list[EvaluationIssue] = Field(default_factory=list)
    improvement_opportunities: list[ImprovementOpportunity] = Field(default_factory=list)
    active_skills_checked: list[str] = Field(default_factory=list)
    skills_followed: list[str] = Field(default_factory=list)
    skills_violated: list[str] = Field(default_factory=list)
    skill_adherence_score: int = 0
    skill_adherence_notes: list[str] = Field(default_factory=list)

    @field_validator("skill_adherence_score")
    @classmethod
    def validate_adherence_score(cls, value: int) -> int:
        if not 0 <= value <= 10:
            raise ValueError("skill_adherence_score must be between 0 and 10")
        return value

    @computed_field
    @property
    def overall_score(self) -> float:
        if not self.criteria:
            return 0.0
        return round(sum(item.score for item in self.criteria) / len(self.criteria), 2)


class SeriesEvaluation(BaseModel):
    """Evaluation of the series as a learning journey."""

    topic: str
    criteria: list[CriterionScore]
    summary: str
    coverage_gaps: list[str] = Field(default_factory=list)
    repeated_patterns: list[RepeatedFailurePattern] = Field(default_factory=list)
    improvement_opportunities: list[ImprovementOpportunity] = Field(default_factory=list)

    @computed_field
    @property
    def overall_score(self) -> float:
        if not self.criteria:
            return 0.0
        return round(sum(item.score for item in self.criteria) / len(self.criteria), 2)


class RunEvaluation(BaseModel):
    """Evaluation of a run across generated artifacts and human outcomes."""

    run_id: str
    topic: str
    num_parts_requested: int
    num_parts_completed: int
    average_review_score: float
    approval_outcomes: dict[str, int] = Field(default_factory=dict)
    repeated_issue_patterns: list[RepeatedFailurePattern] = Field(default_factory=list)
    retry_counts: dict[str, int] = Field(default_factory=dict)
    human_revision_load: int = 0
    trends: list[EvaluationTrend] = Field(default_factory=list)
    improvement_opportunities: list[ImprovementOpportunity] = Field(default_factory=list)
    summary: str = ""
