"""Application dependency wiring."""

from __future__ import annotations

from ..config.settings import get_settings
from ..services.approval_service import ApprovalService
from ..services.artifact_service import ArtifactService
from ..services.content_lint import ContentLintService
from ..services.evaluation_service import EvaluationService
from ..services.memory_service import MemoryService
from ..services.observability import ObservabilityService
from ..utils.prompts import PromptLoader


def build_application_services() -> dict[str, object]:
    """Build shared services used by CLI, API, and dashboard."""

    settings = get_settings()
    artifact_service = ArtifactService(settings.blog_series_output_dir)
    memory_service = MemoryService()
    return {
        "settings": settings,
        "prompt_loader": PromptLoader(),
        "artifact_service": artifact_service,
        "approval_service": ApprovalService(settings.blog_series_output_dir),
        "content_lint_service": ContentLintService(),
        "evaluation_service": EvaluationService(artifact_service),
        "memory_service": memory_service,
        "observability_service": ObservabilityService(),
    }
