"""API request and response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..config.settings import ModelConfig, RunMode
from .approval import ApprovalDecision, ApprovalRecord
from .artifacts import ArtifactRecord, RunManifest, RunStatus
from .evaluation import BlogEvaluation, RunEvaluation, SeriesEvaluation
from .memory import FeedbackItem, FeedbackSeverity, FeedbackType, ReusableSkill, SkillRetrievalResult


class SeriesRunRequest(BaseModel):
    topic: str
    target_audience: str = "intermediate"
    num_parts: int = 12
    selected_parts: list[int] = Field(default_factory=list)
    enable_review: bool = True
    enable_improve: bool = True
    enable_asset_plan: bool = True
    enable_human_approval: bool = True
    enable_evaluation: bool = True
    enable_memory: bool = True
    use_memory: bool = True
    max_retrieved_skills: int = 5
    memory_auto_approve_in_dev: bool = False
    approval_required: bool = True
    run_mode: RunMode = RunMode.PRODUCTION
    min_word_count: int = 2000
    max_word_count: int = 3000
    enable_langsmith: bool = False
    langsmith_project: str = "blog-series-agent"
    langsmith_api_key_env: str = "LANGSMITH_API_KEY"
    langsmith_endpoint: str | None = None
    langsmith_trace_prompts: bool = False
    langsmith_trace_artifacts: bool = False
    enable_web_search: bool = False
    web_search_max_results: int = 6
    web_fetch_max_chars: int = 5000
    web_max_fetches_per_section: int = 3
    model: ModelConfig | None = None


class OutlineRunRequest(BaseModel):
    topic: str
    target_audience: str = "intermediate"
    num_parts: int = 12
    enable_web_search: bool = False
    web_search_max_results: int = 6
    web_fetch_max_chars: int = 5000
    web_max_fetches_per_section: int = 3
    model: ModelConfig | None = None


class BlogRunRequest(BaseModel):
    topic: str
    target_audience: str = "intermediate"
    part: int
    num_parts: int = 12
    enable_web_search: bool = False
    web_search_max_results: int = 6
    web_fetch_max_chars: int = 5000
    web_max_fetches_per_section: int = 3
    model: ModelConfig | None = None


class ReviewRequest(BaseModel):
    file_path: str


class ImproveRequest(BaseModel):
    draft_path: str
    review_path: str


class FeedbackSubmissionRequest(BaseModel):
    part_number: int | None = None
    blog_slug: str | None = None
    source_artifact: str
    raw_feedback: str
    normalized_issue_type: FeedbackType
    severity: FeedbackSeverity = FeedbackSeverity.MEDIUM
    suggested_fix: str = ""
    reviewer: str = "user"
    run_id: str | None = None


class SkillActionResponse(BaseModel):
    skill: ReusableSkill
    approved_skills_count: int
    candidate_skills_count: int


class MemoryBuildResponse(BaseModel):
    candidate_skills: list[ReusableSkill]
    auto_approved_skill_ids: list[str] = Field(default_factory=list)


class MemorySkillsResponse(BaseModel):
    candidate_skills: list[ReusableSkill]
    approved_skills: list[ReusableSkill]


class EvaluationResponse(BaseModel):
    blog_evaluation: BlogEvaluation | None = None
    series_evaluation: SeriesEvaluation | None = None
    run_evaluation: RunEvaluation | None = None


class RetrievalPreviewResponse(BaseModel):
    retrieval: SkillRetrievalResult


class ApprovalSubmissionRequest(BaseModel):
    status: ApprovalDecision
    comments: str = ""
    reviewer_name: str


class RunStatusResponse(BaseModel):
    run_id: str
    status: RunStatus
    manifest: RunManifest


class BlogArtifactsResponse(BaseModel):
    part_id: str
    artifacts: list[ArtifactRecord]
    approval: ApprovalRecord | None = None
    evaluation: BlogEvaluation | None = None


class SeriesLatestResponse(BaseModel):
    latest_outline_path: str | None = None
    latest_manifest: RunManifest | None = None
    latest_series_evaluation: SeriesEvaluation | None = None


class BackgroundTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str = ""
