"""Typed graph state definitions."""

from __future__ import annotations

from typing import TypedDict

from ..config.settings import SeriesRunConfig
from ..schemas.approval import ApprovalRecord
from ..schemas.evaluation import BlogEvaluation, ContentLintReport
from ..schemas.memory import FeedbackItem, MemoryUpdateResult, ReusableSkill, SkillRetrievalResult
from ..schemas.review import BlogReviewReport
from ..schemas.series import (
    AssetPlan,
    BlogSeriesOutline,
    BlogSeriesPart,
    TopicResearchDossier,
)


class OutlineWorkflowState(TypedDict, total=False):
    config: SeriesRunConfig
    topic_dossier: TopicResearchDossier
    series_outline: BlogSeriesOutline


class BlogWorkflowState(TypedDict, total=False):
    config: SeriesRunConfig
    series_outline: BlogSeriesOutline
    current_part: BlogSeriesPart
    draft_markdown: str
    draft_lint_report: ContentLintReport
    review_report: BlogReviewReport
    final_markdown: str
    final_lint_report: ContentLintReport
    asset_plan: AssetPlan
    blog_evaluation: BlogEvaluation
    approval_record: ApprovalRecord
    retrieved_skills: SkillRetrievalResult
    approved_skills: list[ReusableSkill]
    feedback_items: list[FeedbackItem]
    candidate_skills: list[ReusableSkill]
    memory_update_result: MemoryUpdateResult
    approval_iteration: int
    length_expansion_iteration: int
    publish_ready: bool
    rejected: bool
