"""Artifact and run manifest schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    """Known artifact kinds."""

    SERIES_OUTLINE = "series_outline"
    PLAN = "plan"
    RESEARCH = "research"
    DRAFT = "draft"
    REVIEW = "review"
    FINAL = "final"
    ASSET = "asset"
    APPROVAL = "approval"
    EVALUATION = "evaluation"
    MEMORY = "memory"
    MANIFEST = "manifest"


class RunStatus(str, Enum):
    """Overall run status."""

    PENDING = "pending"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class PartStatus(str, Enum):
    """Per-part workflow status."""

    PENDING = "pending"
    OUTLINED = "outlined"
    RESEARCHED = "researched"
    DRAFTED = "drafted"
    REVIEWED = "reviewed"
    IMPROVED = "improved"
    ASSET_PLANNED = "asset_planned"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class ArtifactRecord(BaseModel):
    """Persisted artifact metadata."""

    artifact_type: ArtifactType
    path: str
    part_number: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RunManifest(BaseModel):
    """Persisted run manifest for inspection and resumability."""

    run_id: str
    topic: str
    target_audience: str
    num_parts: int
    status: RunStatus = RunStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    selected_parts: list[int] = Field(default_factory=list)
    artifacts: list[ArtifactRecord] = Field(default_factory=list)
    part_statuses: dict[int, PartStatus] = Field(default_factory=dict)
    error: str | None = None
