"""Approval workflow schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ApprovalDecision(str, Enum):
    """Supported human approval outcomes."""

    PENDING = "pending"
    APPROVED = "approved"
    APPROVED_WITH_NOTES = "approved_with_notes"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"


class ApprovalRecord(BaseModel):
    """Persisted decision for one blog artifact bundle."""

    part_number: int
    slug: str
    status: ApprovalDecision
    comments: str = ""
    reviewer_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    draft_path: str | None = None
    review_path: str | None = None
    final_path: str | None = None
    asset_plan_path: str | None = None

