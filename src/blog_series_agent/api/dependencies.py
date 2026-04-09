"""API dependencies."""

from __future__ import annotations

from functools import lru_cache

from ..services.background import BackgroundExecutor
from ..services.container import build_application_services
from ..services.pipeline import PipelineService


@lru_cache(maxsize=1)
def get_pipeline_service() -> PipelineService:
    services = build_application_services()
    return PipelineService(**services)


@lru_cache(maxsize=1)
def get_application_services() -> dict[str, object]:
    return build_application_services()


@lru_cache(maxsize=1)
def get_background_executor() -> BackgroundExecutor:
    return BackgroundExecutor(max_workers=2)
