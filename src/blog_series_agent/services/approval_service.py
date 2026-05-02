"""Human approval workflow service."""

from __future__ import annotations

import re
from pathlib import Path

from ..schemas.approval import ApprovalDecision, ApprovalRecord
from ..services.rendering import render_approval_markdown
from ..utils.files import read_json, write_json, write_markdown

PART_ID_PATTERN = re.compile(r"Part-(?P<part_number>\d+)-(?P<slug>.+)")


class ApprovalService:
    """Persists and retrieves human approval decisions."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.approval_dir = self.output_dir / "approval"
        self.drafts_dir = self.output_dir / "drafts"
        self.reviews_dir = self.output_dir / "reviews"
        self.final_dir = self.output_dir / "final"
        self.assets_dir = self.output_dir / "assets"
        self.approval_dir.mkdir(parents=True, exist_ok=True)

    def submit_approval(
        self,
        *,
        part_id: str,
        status: str | ApprovalDecision,
        reviewer_name: str,
        comments: str,
    ) -> ApprovalRecord:
        part_number, slug = self.parse_part_id(part_id)
        record = ApprovalRecord(
            part_number=part_number,
            slug=slug,
            status=ApprovalDecision(status),
            comments=comments,
            reviewer_name=reviewer_name,
            draft_path=self._artifact_path(self.drafts_dir, part_number, slug),
            review_path=self._artifact_path(self.reviews_dir, part_number, slug, suffix="-review"),
            final_path=self._artifact_path(self.final_dir, part_number, slug),
            asset_plan_path=self._artifact_path(self.assets_dir, part_number, slug, suffix="-assets"),
        )
        self._persist(record)
        return record

    def load(self, part_number: int, slug: str) -> ApprovalRecord | None:
        path = self.approval_dir / f"Part-{part_number}-{slug}-approval.json"
        if not path.exists():
            return None
        return ApprovalRecord.model_validate(read_json(path))

    def ensure_pending(self, part_number: int, slug: str) -> ApprovalRecord:
        existing = self.load(part_number, slug)
        if existing is not None:
            return existing
        return self.reset_to_pending(part_number, slug)

    def reset_to_pending(self, part_number: int, slug: str) -> ApprovalRecord:
        record = ApprovalRecord(
            part_number=part_number,
            slug=slug,
            status=ApprovalDecision.PENDING,
            reviewer_name="pending",
            draft_path=self._artifact_path(self.drafts_dir, part_number, slug),
            review_path=self._artifact_path(self.reviews_dir, part_number, slug, suffix="-review"),
            final_path=self._artifact_path(self.final_dir, part_number, slug),
            asset_plan_path=self._artifact_path(self.assets_dir, part_number, slug, suffix="-assets"),
        )
        self._persist(record)
        return record

    def parse_part_id(self, part_id: str) -> tuple[int, str]:
        normalized = part_id.removesuffix(".md").removesuffix(".json")
        match = PART_ID_PATTERN.fullmatch(normalized)
        if not match:
            raise ValueError(f"Invalid part identifier: {part_id}")
        return int(match.group("part_number")), match.group("slug")

    def _persist(self, record: ApprovalRecord) -> None:
        stem = f"Part-{record.part_number}-{record.slug}-approval"
        write_json(self.approval_dir / f"{stem}.json", record.model_dump(mode="json"))
        write_markdown(self.approval_dir / f"{stem}.md", render_approval_markdown(record))

    @staticmethod
    def _artifact_path(folder: Path, part_number: int, slug: str, suffix: str = "") -> str | None:
        stem = f"Part-{part_number}-{slug}{suffix}"
        matches = list(folder.glob(f"{stem}.*"))
        return str(matches[0]) if matches else None
