"""Typer CLI entrypoint."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .config.settings import RunMode, SeriesRunConfig, get_settings, load_run_config
from .schemas.memory import FeedbackSeverity, FeedbackType
from .utils.logging import configure_logging

app = typer.Typer(help="LangGraph-based technical blog series generator.")
feedback_app = typer.Typer(help="Structured feedback commands.")
memory_app = typer.Typer(help="Memory and reusable skill commands.")
app.add_typer(feedback_app, name="feedback")
app.add_typer(memory_app, name="memory")
console = Console()


def _load_or_build_config(
    *,
    config_path: str | None,
    topic: str,
    audience: str,
    parts: int,
    part: int | None = None,
    use_memory: bool | None = None,
    enable_web_search: bool | None = None,
) -> SeriesRunConfig:
    settings = get_settings()
    if config_path:
        loaded = load_run_config(Path(config_path))
        if use_memory is not None:
            loaded.use_memory = use_memory
        if enable_web_search is not None:
            loaded.enable_web_search = enable_web_search
        return loaded
    selected_parts = [part] if part is not None else []
    overrides = settings.default_run_overrides()
    if use_memory is not None:
        overrides["use_memory"] = use_memory
    if enable_web_search is not None:
        overrides["enable_web_search"] = enable_web_search
    return SeriesRunConfig(
        topic=topic,
        audience=audience,
        num_parts=parts,
        selected_parts=selected_parts,
        model=settings.default_model_config(),
        output_dir=settings.blog_series_output_dir,
        run_mode=RunMode.PRODUCTION,
        approval_required=True,
        **overrides,
    )


def _build_pipeline():
    from .services.container import build_application_services
    from .services.pipeline import PipelineService

    return PipelineService(**build_application_services())


def _resolve_part_id(part: int, slug: str = "") -> str:
    outputs = Path(get_settings().blog_series_output_dir)
    pattern = f"Part-{part}-{slug}-*.md" if slug else f"Part-{part}-*.md"
    matches = list((outputs / "final").glob(pattern)) or list((outputs / "drafts").glob(pattern))
    if not matches:
        raise typer.BadParameter(f"Could not resolve a blog artifact for part {part}.")
    stem = matches[0].stem
    for suffix in ("-review", "-eval", "-assets", "-approval"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return stem


@app.command()
def run(
    topic: str = typer.Option(..., help="Series topic."),
    audience: str = typer.Option("intermediate", help="Target audience."),
    parts: int = typer.Option(12, help="Number of parts."),
    config: str = typer.Option("", help="Optional YAML config file."),
    use_memory: bool = typer.Option(True, help="Whether to retrieve approved skills during generation."),
    web_search: bool = typer.Option(False, help="Enable grounded web search/fetch tools."),
) -> None:
    """Generate a full series."""

    configure_logging(get_settings().blog_series_log_level)
    pipeline = _build_pipeline()
    run_config = _load_or_build_config(
        config_path=config,
        topic=topic,
        audience=audience,
        parts=parts,
        use_memory=use_memory,
        enable_web_search=web_search,
    )
    manifest = pipeline.run_series(run_config)
    console.print(f"Run complete: {manifest.run_id} [{manifest.status}]")


@app.command()
def outline(
    topic: str = typer.Option(..., help="Series topic."),
    audience: str = typer.Option("intermediate", help="Target audience."),
    parts: int = typer.Option(12, help="Number of parts."),
    web_search: bool = typer.Option(False, help="Enable grounded web search/fetch tools."),
) -> None:
    """Generate only the series outline."""

    configure_logging(get_settings().blog_series_log_level)
    pipeline = _build_pipeline()
    run_config = _load_or_build_config(
        config_path=None,
        topic=topic,
        audience=audience,
        parts=parts,
        enable_web_search=web_search,
    )
    manifest = pipeline.run_outline(run_config)
    console.print(f"Outline generated: {manifest.run_id}")


@app.command()
def write(
    topic: str = typer.Option(..., help="Series topic."),
    part: int = typer.Option(..., help="Part number."),
    audience: str = typer.Option("intermediate", help="Target audience."),
    parts: int = typer.Option(12, help="Number of parts."),
    use_memory: bool = typer.Option(True, help="Whether to retrieve approved skills during generation."),
    web_search: bool = typer.Option(False, help="Enable grounded web search/fetch tools."),
) -> None:
    """Generate a specific blog."""

    configure_logging(get_settings().blog_series_log_level)
    pipeline = _build_pipeline()
    run_config = _load_or_build_config(
        config_path=None,
        topic=topic,
        audience=audience,
        parts=parts,
        part=part,
        use_memory=use_memory,
        enable_web_search=web_search,
    )
    manifest = pipeline.run_blog(run_config, part_number=part)
    console.print(f"Blog generated: {manifest.run_id}")


@app.command()
def resume(
    run_id: str = typer.Option(..., help="Run ID to resume."),
    topic: str = typer.Option(..., help="Series topic."),
    audience: str = typer.Option("intermediate", help="Target audience."),
    parts: int = typer.Option(12, help="Number of parts."),
    use_memory: bool = typer.Option(True, help="Whether to retrieve approved skills during generation."),
    web_search: bool = typer.Option(False, help="Enable grounded web search/fetch tools."),
) -> None:
    """Resume a previously failed or partially completed series run."""

    configure_logging(get_settings().blog_series_log_level)
    pipeline = _build_pipeline()
    run_config = _load_or_build_config(
        config_path=None,
        topic=topic,
        audience=audience,
        parts=parts,
        use_memory=use_memory,
        enable_web_search=web_search,
    )
    manifest = pipeline.resume_series(run_id, run_config)
    console.print(f"Resume complete: {manifest.run_id} [{manifest.status}]")


@app.command()
def review(file: Path = typer.Option(..., exists=True, help="Draft markdown file to review.")) -> None:
    """Review an existing draft."""

    configure_logging(get_settings().blog_series_log_level)
    manifest = _build_pipeline().review_existing(file)
    console.print(f"Review generated under run: {manifest.run_id}")


@app.command()
def improve(
    draft: Path = typer.Option(..., exists=True, help="Draft markdown file."),
    review: Path = typer.Option(..., exists=True, help="Review JSON file."),
) -> None:
    """Improve an existing draft using a review report."""

    configure_logging(get_settings().blog_series_log_level)
    manifest = _build_pipeline().improve_existing(draft, review)
    console.print(f"Improved blog generated under run: {manifest.run_id}")


@app.command("evaluate")
def evaluate_blog(
    part: int = typer.Option(..., help="Part number."),
    slug: str = typer.Option("", help="Optional slug hint."),
) -> None:
    """Evaluate an existing generated blog artifact."""

    configure_logging(get_settings().blog_series_log_level)
    evaluation = _build_pipeline().evaluate_part(_resolve_part_id(part, slug))
    console.print(f"Blog evaluation score: {evaluation.overall_score}/10")
    console.print(f"Skill adherence: {evaluation.skill_adherence_score}/10")


@app.command("evaluate-series")
def evaluate_series() -> None:
    """Evaluate the latest full series."""

    configure_logging(get_settings().blog_series_log_level)
    evaluation = _build_pipeline().evaluate_series_latest()
    console.print(f"Series evaluation score: {evaluation.overall_score}/10")


@app.command()
def approve(
    part_id: str = typer.Option(..., help="Part identifier, e.g. Part-4-feature-pipelines."),
    status: str = typer.Option(..., help="approved, approved_with_notes, changes_requested, rejected"),
    reviewer: str = typer.Option(..., help="Reviewer name."),
    comments: str = typer.Option("", help="Approval comments."),
) -> None:
    """Submit a human approval decision."""

    configure_logging(get_settings().blog_series_log_level)
    services = _build_pipeline()
    record = services.approval_service.submit_approval(
        part_id=part_id,
        status=status,
        reviewer_name=reviewer,
        comments=comments,
    )
    services.memory_service.capture_approval_feedback(run_id=None, record=record)
    console.print(f"Recorded approval: {record.status}")


@feedback_app.command("add")
def add_feedback(
    part: int = typer.Option(..., help="Part number."),
    type: FeedbackType = typer.Option(..., help="Feedback type."),
    comment: str = typer.Option(..., help="Feedback comment."),
    reviewer: str = typer.Option("user", help="Reviewer name."),
    slug: str = typer.Option("", help="Optional slug hint."),
    severity: FeedbackSeverity = typer.Option(FeedbackSeverity.MEDIUM, help="Feedback severity."),
) -> None:
    """Add explicit normalized feedback for future learning."""

    configure_logging(get_settings().blog_series_log_level)
    pipeline = _build_pipeline()
    part_id = _resolve_part_id(part, slug)
    _, slug_value = pipeline.approval_service.parse_part_id(part_id)
    item = pipeline.memory_service.capture_manual_feedback(
        source_artifact=part_id,
        raw_feedback=comment,
        normalized_issue_type=type,
        severity=severity,
        suggested_fix="Apply this feedback in future generations.",
        reviewer=reviewer,
        part_number=part,
        blog_slug=slug_value,
    )
    console.print(f"Recorded feedback: {item.feedback_id}")


@memory_app.command("build")
def build_memory(
    topic: str = typer.Option(..., help="Topic to scope skill extraction."),
    audience: str = typer.Option("intermediate", help="Audience to scope skill extraction."),
) -> None:
    """Build candidate reusable skills from the raw feedback log."""

    configure_logging(get_settings().blog_series_log_level)
    result = _build_pipeline().build_memory(topic=topic, audience=audience)
    console.print(f"Candidate skills created: {len(result.candidate_skills_created)}")
    if result.auto_approved_skill_ids:
        console.print(f"Auto-approved: {', '.join(result.auto_approved_skill_ids)}")


@memory_app.command("list")
def list_memory() -> None:
    """List candidate and approved reusable skills."""

    configure_logging(get_settings().blog_series_log_level)
    pipeline = _build_pipeline()
    candidates = pipeline.memory_service.list_candidate_skills()
    approved = pipeline.memory_service.list_approved_skills()
    console.print(f"Candidate skills: {len(candidates)}")
    for skill in candidates:
        console.print(f"- {skill.id} [{skill.status}] {skill.title}")
    console.print(f"Approved skills: {len(approved)}")
    for skill in approved:
        console.print(f"- {skill.id} [{skill.status}] {skill.title}")


@memory_app.command("approve")
def approve_memory_skill(skill_id: str = typer.Option(..., help="Candidate skill id.")) -> None:
    """Approve a candidate skill into the active reusable skill store."""

    configure_logging(get_settings().blog_series_log_level)
    skill = _build_pipeline().memory_service.approve_skill(skill_id)
    console.print(f"Approved skill: {skill.id}")


@memory_app.command("reject")
def reject_memory_skill(skill_id: str = typer.Option(..., help="Candidate skill id.")) -> None:
    """Reject a candidate skill."""

    configure_logging(get_settings().blog_series_log_level)
    skill = _build_pipeline().memory_service.reject_skill(skill_id)
    console.print(f"Rejected skill: {skill.id}")


@memory_app.command("retrieve")
def retrieve_memory(
    topic: str = typer.Option(..., help="Topic."),
    part: int = typer.Option(1, help="Part number."),
    audience: str = typer.Option("intermediate", help="Target audience."),
    artifact_type: str = typer.Option("draft", help="Artifact type for retrieval preview."),
) -> None:
    """Preview which approved skills would be retrieved for a run."""

    configure_logging(get_settings().blog_series_log_level)
    retrieval = _build_pipeline().preview_memory_retrieval(
        topic=topic,
        audience=audience,
        part_number=part,
        artifact_type=artifact_type,
    )
    console.print(f"Retrieved skills: {', '.join(retrieval.retrieved_skill_ids) or 'None'}")
    for line in retrieval.retrieved_guidance:
        console.print(f"- {line}")


@app.command()
def api(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Launch the FastAPI service."""

    configure_logging(get_settings().blog_series_log_level)
    import uvicorn

    uvicorn.run("blog_series_agent.api.app:app", host=host, port=port, reload=False)


@app.command()
def dashboard() -> None:
    """Launch the Streamlit dashboard."""

    from .dashboard.app import run_dashboard

    run_dashboard()
