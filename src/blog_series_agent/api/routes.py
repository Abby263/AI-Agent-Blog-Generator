"""FastAPI routes."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from ..config.settings import SeriesRunConfig
from ..schemas.api import (
    ApprovalSubmissionRequest,
    BackgroundTaskResponse,
    BlogArtifactsResponse,
    BlogRunRequest,
    EvaluationResponse,
    FeedbackSubmissionRequest,
    ImproveRequest,
    MemoryBuildResponse,
    MemorySkillsResponse,
    OutlineRunRequest,
    RetrievalPreviewResponse,
    ReviewRequest,
    RunStatusResponse,
    SeriesLatestResponse,
    SeriesRunRequest,
    SkillActionResponse,
)
from ..schemas.memory import SkillRetrievalQuery
from ..services.background import BackgroundExecutor
from ..services.pipeline import PipelineService
from .dependencies import get_application_services, get_background_executor, get_pipeline_service

router = APIRouter()


@router.get("/health")
def health() -> dict:
    """Lightweight liveness probe used by the UI and orchestrators."""
    return {"status": "ok"}


def _to_run_config(request: SeriesRunRequest | OutlineRunRequest | BlogRunRequest) -> SeriesRunConfig:
    payload = request.model_dump()
    if payload.get("model") is None:
        payload.pop("model", None)
    if "target_audience" in payload:
        payload["audience"] = payload.pop("target_audience")
    return SeriesRunConfig.model_validate(payload)


@router.post("/runs/series", response_model=RunStatusResponse)
def create_series_run(
    request: SeriesRunRequest,
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> RunStatusResponse:
    config = _to_run_config(request)
    manifest = pipeline.run_series(config)
    return RunStatusResponse(run_id=manifest.run_id, status=manifest.status, manifest=manifest)


@router.post("/runs/outline", response_model=RunStatusResponse)
def create_outline_run(
    request: OutlineRunRequest,
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> RunStatusResponse:
    config = _to_run_config(request)
    manifest = pipeline.run_outline(config)
    return RunStatusResponse(run_id=manifest.run_id, status=manifest.status, manifest=manifest)


@router.post("/runs/blog", response_model=RunStatusResponse)
def create_blog_run(
    request: BlogRunRequest,
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> RunStatusResponse:
    config = _to_run_config(request)
    manifest = pipeline.run_blog(config, request.part)
    return RunStatusResponse(run_id=manifest.run_id, status=manifest.status, manifest=manifest)


@router.post("/runs/{run_id}/resume", response_model=RunStatusResponse)
def resume_series_run(
    run_id: str,
    request: SeriesRunRequest,
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> RunStatusResponse:
    config = _to_run_config(request)
    manifest = pipeline.resume_series(run_id, config)
    return RunStatusResponse(run_id=manifest.run_id, status=manifest.status, manifest=manifest)


@router.post("/runs/review", response_model=RunStatusResponse)
def create_review_run(
    request: ReviewRequest,
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> RunStatusResponse:
    manifest = pipeline.review_existing(request.file_path)
    return RunStatusResponse(run_id=manifest.run_id, status=manifest.status, manifest=manifest)


@router.post("/runs/improve", response_model=RunStatusResponse)
def create_improve_run(
    request: ImproveRequest,
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> RunStatusResponse:
    manifest = pipeline.improve_existing(request.draft_path, request.review_path)
    return RunStatusResponse(run_id=manifest.run_id, status=manifest.status, manifest=manifest)


@router.get("/runs/{run_id}", response_model=RunStatusResponse)
def get_run(
    run_id: str,
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> RunStatusResponse:
    try:
        manifest = pipeline.artifact_service.load_manifest(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RunStatusResponse(run_id=run_id, status=manifest.status, manifest=manifest)


@router.get("/runs/{run_id}/artifacts")
def list_artifacts(
    run_id: str,
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> dict[str, object]:
    manifest = pipeline.artifact_service.load_manifest(run_id)
    return {"run_id": run_id, "artifacts": [artifact.model_dump(mode="json") for artifact in manifest.artifacts]}


@router.get("/blogs/{part_id}", response_model=BlogArtifactsResponse)
def get_blog_artifacts(
    part_id: str,
    app_services: dict[str, object] = Depends(get_application_services),
) -> BlogArtifactsResponse:
    artifact_service = app_services["artifact_service"]
    approval_service = app_services["approval_service"]
    evaluation_service = app_services["evaluation_service"]
    artifacts = artifact_service.artifacts_for_part(part_id)
    part_number, slug = approval_service.parse_part_id(part_id)
    approval = approval_service.load(part_number, slug)
    evaluation = evaluation_service.load_blog_evaluation(part_id)
    return BlogArtifactsResponse(part_id=part_id, artifacts=artifacts, approval=approval, evaluation=evaluation)


@router.post("/approval/{part_id}", response_model=BlogArtifactsResponse)
def submit_approval(
    part_id: str,
    request: ApprovalSubmissionRequest,
    app_services: dict[str, object] = Depends(get_application_services),
) -> BlogArtifactsResponse:
    approval_service = app_services["approval_service"]
    artifact_service = app_services["artifact_service"]
    evaluation_service = app_services["evaluation_service"]
    memory_service = app_services["memory_service"]
    approval = approval_service.submit_approval(
        part_id=part_id,
        status=request.status,
        reviewer_name=request.reviewer_name,
        comments=request.comments,
    )
    memory_service.capture_approval_feedback(run_id=None, record=approval)
    return BlogArtifactsResponse(
        part_id=part_id,
        artifacts=artifact_service.artifacts_for_part(part_id),
        approval=approval,
        evaluation=evaluation_service.load_blog_evaluation(part_id),
    )


@router.post("/evaluation/blog/{part_id}", response_model=EvaluationResponse)
def evaluate_blog(
    part_id: str,
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> EvaluationResponse:
    evaluation = pipeline.evaluate_part(part_id)
    return EvaluationResponse(blog_evaluation=evaluation)


@router.get("/evaluation/blog/{part_id}", response_model=EvaluationResponse)
def get_blog_evaluation(
    part_id: str,
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> EvaluationResponse:
    evaluation = pipeline.get_blog_evaluation(part_id)
    if evaluation is None:
        raise HTTPException(status_code=404, detail=f"No evaluation found for {part_id}")
    return EvaluationResponse(blog_evaluation=evaluation)


@router.post("/evaluation/series", response_model=EvaluationResponse)
def evaluate_series(
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> EvaluationResponse:
    evaluation = pipeline.evaluate_series_latest()
    return EvaluationResponse(series_evaluation=evaluation)


@router.post("/feedback")
def add_feedback(
    request: FeedbackSubmissionRequest,
    app_services: dict[str, object] = Depends(get_application_services),
) -> dict[str, object]:
    memory_service = app_services["memory_service"]
    item = memory_service.capture_manual_feedback(
        source_artifact=request.source_artifact,
        raw_feedback=request.raw_feedback,
        normalized_issue_type=request.normalized_issue_type,
        severity=request.severity,
        suggested_fix=request.suggested_fix or "Apply this feedback in future generations.",
        reviewer=request.reviewer,
        run_id=request.run_id,
        part_number=request.part_number,
        blog_slug=request.blog_slug,
    )
    return {"feedback": item.model_dump(mode="json")}


@router.get("/feedback")
def list_feedback(
    app_services: dict[str, object] = Depends(get_application_services),
) -> dict[str, object]:
    memory_service = app_services["memory_service"]
    return {"feedback": [item.model_dump(mode="json") for item in memory_service.list_feedback()]}


@router.post("/memory/build", response_model=MemoryBuildResponse)
def build_memory(
    topic: str = "ML System Design",
    audience: str = "intermediate",
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> MemoryBuildResponse:
    result = pipeline.build_memory(topic=topic, audience=audience)
    return MemoryBuildResponse(
        candidate_skills=result.candidate_skills_created,
        auto_approved_skill_ids=result.auto_approved_skill_ids,
    )


@router.get("/memory/raw-feedback")
def get_raw_feedback(
    app_services: dict[str, object] = Depends(get_application_services),
) -> dict[str, object]:
    memory_service = app_services["memory_service"]
    return {"feedback": [item.model_dump(mode="json") for item in memory_service.list_feedback()]}


@router.get("/memory/skills", response_model=MemorySkillsResponse)
def get_memory_skills(
    app_services: dict[str, object] = Depends(get_application_services),
) -> MemorySkillsResponse:
    memory_service = app_services["memory_service"]
    return MemorySkillsResponse(
        candidate_skills=memory_service.list_candidate_skills(),
        approved_skills=memory_service.list_approved_skills(),
    )


@router.post("/memory/{skill_id}/approve", response_model=SkillActionResponse)
def approve_skill(
    skill_id: str,
    app_services: dict[str, object] = Depends(get_application_services),
) -> SkillActionResponse:
    memory_service = app_services["memory_service"]
    skill = memory_service.approve_skill(skill_id)
    return SkillActionResponse(
        skill=skill,
        approved_skills_count=len(memory_service.list_approved_skills()),
        candidate_skills_count=len(memory_service.list_candidate_skills()),
    )


@router.post("/memory/{skill_id}/reject", response_model=SkillActionResponse)
def reject_skill(
    skill_id: str,
    app_services: dict[str, object] = Depends(get_application_services),
) -> SkillActionResponse:
    memory_service = app_services["memory_service"]
    skill = memory_service.reject_skill(skill_id)
    return SkillActionResponse(
        skill=skill,
        approved_skills_count=len(memory_service.list_approved_skills()),
        candidate_skills_count=len(memory_service.list_candidate_skills()),
    )


@router.get("/memory/retrieval-preview", response_model=RetrievalPreviewResponse)
def retrieval_preview(
    topic: str,
    audience: str = "intermediate",
    part_number: int | None = None,
    artifact_type: str = "draft",
    app_services: dict[str, object] = Depends(get_application_services),
) -> RetrievalPreviewResponse:
    memory_service = app_services["memory_service"]
    retrieval = memory_service.retrieve_skills(
        SkillRetrievalQuery(
            topic=topic,
            audience=audience,
            part_number=part_number,
            artifact_type=artifact_type,
            max_skills=5,
        ),
        record_usage=False,
    )
    return RetrievalPreviewResponse(retrieval=retrieval)


@router.get("/series/latest", response_model=SeriesLatestResponse)
def latest_series(
    app_services: dict[str, object] = Depends(get_application_services),
) -> SeriesLatestResponse:
    artifact_service = app_services["artifact_service"]
    evaluation_service = app_services["evaluation_service"]
    manifests = artifact_service.list_manifests()
    return SeriesLatestResponse(
        latest_outline_path=str(artifact_service.latest_outline_path()) if artifact_service.latest_outline_path() else None,
        latest_manifest=manifests[-1] if manifests else None,
        latest_series_evaluation=evaluation_service.latest_series_evaluation(),
    )


# --- Background / async run endpoints ---


@router.post("/runs/series/async", response_model=BackgroundTaskResponse)
def create_series_run_async(
    request: SeriesRunRequest,
    pipeline: PipelineService = Depends(get_pipeline_service),
    executor: BackgroundExecutor = Depends(get_background_executor),
) -> BackgroundTaskResponse:
    config = _to_run_config(request)
    task_id = f"series-{uuid4().hex[:8]}"
    executor.submit(task_id, pipeline.run_series, config)
    return BackgroundTaskResponse(task_id=task_id, status="running", message="Series run started in background.")


@router.post("/runs/outline/async", response_model=BackgroundTaskResponse)
def create_outline_run_async(
    request: OutlineRunRequest,
    pipeline: PipelineService = Depends(get_pipeline_service),
    executor: BackgroundExecutor = Depends(get_background_executor),
) -> BackgroundTaskResponse:
    config = _to_run_config(request)
    task_id = f"outline-{uuid4().hex[:8]}"
    executor.submit(task_id, pipeline.run_outline, config)
    return BackgroundTaskResponse(task_id=task_id, status="running", message="Outline run started in background.")


@router.post("/runs/blog/async", response_model=BackgroundTaskResponse)
def create_blog_run_async(
    request: BlogRunRequest,
    pipeline: PipelineService = Depends(get_pipeline_service),
    executor: BackgroundExecutor = Depends(get_background_executor),
) -> BackgroundTaskResponse:
    config = _to_run_config(request)
    task_id = f"blog-{uuid4().hex[:8]}"
    executor.submit(task_id, pipeline.run_blog, config, request.part)
    return BackgroundTaskResponse(task_id=task_id, status="running", message="Blog run started in background.")


@router.get("/tasks/{task_id}", response_model=BackgroundTaskResponse)
def get_task_status(
    task_id: str,
    executor: BackgroundExecutor = Depends(get_background_executor),
) -> BackgroundTaskResponse:
    task = executor.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return BackgroundTaskResponse(
        task_id=task.task_id,
        status=task.status.value,
        message=task.error or "",
    )


@router.get("/tasks")
def list_tasks(
    executor: BackgroundExecutor = Depends(get_background_executor),
) -> dict[str, object]:
    tasks = executor.list_tasks()
    return {
        "tasks": [
            {
                "task_id": t.task_id,
                "status": t.status.value,
                "created_at": t.created_at.isoformat(),
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "error": t.error,
            }
            for t in tasks
        ]
    }
