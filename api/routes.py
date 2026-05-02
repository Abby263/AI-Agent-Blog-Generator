"""FastAPI routes for blog generation."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, conint

from src.workflow.graph import run_workflow, run_blog_series
from src.utils.logger import get_logger
from api.job_manager import series_job_manager

router = APIRouter(prefix="/api", tags=["blog-generation"])
logger = get_logger()


class BlogRequest(BaseModel):
    topic: str = Field(..., description="Blog topic to generate")
    requirements: str = Field(
        default="",
        description="System requirements or additional instructions"
    )
    author: str = Field(default="AI Agent", description="Author attribution")
    target_length: conint(ge=500, le=50000) = 8000
    include_code: bool = True
    include_diagrams: bool = True
    content_type: str = Field(
        default="blog",
        description="Type of content to generate (blog, news, tutorial, review)"
    )


class SeriesRequest(BaseModel):
    series_name: str = Field(..., description="Name of the blog series")
    number_of_blogs: conint(ge=1) = 1
    requirements: str = ""
    author: str = "AI Agent"
    target_length: conint(ge=500, le=50000) = 8000
    include_code: bool = True
    include_diagrams: bool = True
    content_type: str = Field(
        default="blog",
        description="Type of content to generate (blog, news, tutorial, review)"
    )
    topics: Optional[List[str]] = Field(
        default=None,
        description="Optional explicit titles/topics for each blog"
    )


class BlogResponse(BaseModel):
    status: str
    result: dict


class BlogResult(BaseModel):
    topic: Optional[str]
    status: str
    file_path: Optional[str]
    word_count: Optional[int]
    final_content: str = ""
    messages: List[str] = []


class SeriesResponse(BaseModel):
    status: str
    series_name: str
    number_of_blogs: int
    results: List[BlogResult]


class SeriesJobCreateResponse(BaseModel):
    job_id: str


class JobProgress(BaseModel):
    timestamp: str
    message: str


class SeriesJobStatusResponse(BaseModel):
    job_id: str
    status: str
    series_name: Optional[str]
    number_of_blogs: Optional[int]
    progress: List[JobProgress]
    result: Optional[List[BlogResult]] = None
    error: Optional[str] = None


def _build_series_results(raw_results: List[dict]) -> List[BlogResult]:
    formatted: List[BlogResult] = []
    for item in raw_results:
        state = item.get("result") or {}
        metadata = state.get("metadata") or {}
        formatted.append(
            BlogResult(
                topic=item.get("topic"),
                status=item.get("status", "completed"),
                file_path=metadata.get("output_path"),
                word_count=metadata.get("word_count"),
                final_content=state.get("final_content", ""),
                messages=state.get("messages", []),
            )
        )
    return formatted


@router.get("/health", tags=["health"])
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok"}


@router.post("/blogs", response_model=BlogResponse)
def generate_blog(payload: BlogRequest) -> BlogResponse:
    """Trigger single blog generation."""
    try:
        logger.info("API request: generating blog for topic '%s'", payload.topic)
        result = run_workflow(
            topic=payload.topic,
            requirements=payload.requirements,
            author=payload.author,
            target_length=payload.target_length,
            include_code=payload.include_code,
            include_diagrams=payload.include_diagrams,
            content_type=payload.content_type
        )
        return BlogResponse(status=result.get("status", "completed"), result=result)
    except Exception as exc:  # pragma: no cover - runtime errors bubbled up
        logger.error("Blog generation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/series", response_model=SeriesResponse)
def generate_series(payload: SeriesRequest) -> SeriesResponse:
    """Trigger blog series generation."""
    try:
        logger.info(
            "API request: generating series '%s' (%s blogs)",
            payload.series_name,
            payload.number_of_blogs,
        )
        results = run_blog_series(
            series_name=payload.series_name,
            number_of_blogs=payload.number_of_blogs,
            author=payload.author,
            requirements=payload.requirements,
            target_length=payload.target_length,
            include_code=payload.include_code,
            include_diagrams=payload.include_diagrams,
            content_type=payload.content_type,
            topics=payload.topics
        )
        formatted = _build_series_results(results)
        return SeriesResponse(
            status="completed",
            series_name=payload.series_name,
            number_of_blogs=len(formatted),
            results=formatted
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Series generation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/series/jobs", response_model=SeriesJobCreateResponse)
def enqueue_series_job(payload: SeriesRequest) -> SeriesJobCreateResponse:
    """Start an asynchronous job for blog series generation."""
    job_id = series_job_manager.start_job(
        series_name=payload.series_name,
        number_of_blogs=payload.number_of_blogs,
        author=payload.author,
        requirements=payload.requirements,
        target_length=payload.target_length,
        include_code=payload.include_code,
        include_diagrams=payload.include_diagrams,
        content_type=payload.content_type,
        topics=payload.topics,
    )
    return SeriesJobCreateResponse(job_id=job_id)


@router.get("/series/jobs/{job_id}", response_model=SeriesJobStatusResponse)
def get_series_job_status(job_id: str) -> SeriesJobStatusResponse:
    """Fetch status and progress for a running or completed job."""
    job = series_job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    progress = [JobProgress(**entry) for entry in job.get("progress", [])]
    result_data = None
    if job.get("result"):
        result_data = [BlogResult(**entry) for entry in job["result"]]
    return SeriesJobStatusResponse(
        job_id=job_id,
        status=job.get("status", "unknown"),
        series_name=job.get("series_name"),
        number_of_blogs=job.get("number_of_blogs"),
        progress=progress,
        result=result_data,
        error=job.get("error"),
    )
