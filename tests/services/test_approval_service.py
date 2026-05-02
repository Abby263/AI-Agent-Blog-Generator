from pathlib import Path

from blog_series_agent.schemas.approval import ApprovalDecision
from blog_series_agent.services.approval_service import ApprovalService


def test_approval_service_writes_record(tmp_path: Path) -> None:
    for folder, filename in [
        ("drafts", "Part-1-introduction.md"),
        ("reviews", "Part-1-introduction-review.md"),
        ("final", "Part-1-introduction.md"),
        ("assets", "Part-1-introduction-assets.md"),
    ]:
        target = tmp_path / folder
        target.mkdir(parents=True, exist_ok=True)
        (target / filename).write_text("x", encoding="utf-8")

    service = ApprovalService(tmp_path)
    record = service.submit_approval(
        part_id="Part-1-introduction",
        status=ApprovalDecision.APPROVED,
        reviewer_name="alice",
        comments="Ready to publish.",
    )

    assert record.status == ApprovalDecision.APPROVED
    assert (tmp_path / "approval" / "Part-1-introduction-approval.json").exists()

