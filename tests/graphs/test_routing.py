from blog_series_agent.config.settings import RunMode, SeriesRunConfig
from blog_series_agent.graphs.routing import (
    route_after_approval,
    route_after_asset,
    route_after_improve,
    route_after_length_check,
    route_after_review,
)
from blog_series_agent.schemas.approval import ApprovalDecision, ApprovalRecord


def test_routing_transitions() -> None:
    config = SeriesRunConfig(
        topic="AI Agents",
        audience="intermediate",
        num_parts=10,
        run_mode=RunMode.PRODUCTION,
        approval_required=True,
    )

    # length_check replaces route_after_draft; when word count meets target, it routes to review
    assert route_after_length_check({"config": config, "draft_markdown": " ".join(["word"] * 2500), "length_expansion_iteration": 0}) == "review"
    assert route_after_review({"config": config}) == "improve"
    assert route_after_improve({"config": config}) == "asset"
    assert route_after_asset({"config": config}) == "evaluation"


def test_length_check_routes_to_expansion_when_short() -> None:
    config = SeriesRunConfig(
        topic="AI Agents",
        audience="intermediate",
        num_parts=10,
        run_mode=RunMode.PRODUCTION,
        approval_required=True,
        min_word_count=2000,
    )
    # Short draft should trigger re-expansion
    assert route_after_length_check({"config": config, "draft_markdown": "short draft", "length_expansion_iteration": 0}) == "length_check"
    # But not after max expansions
    assert route_after_length_check({"config": config, "draft_markdown": "short draft", "length_expansion_iteration": 2}) == "review"


def test_approval_routing() -> None:
    pending = ApprovalRecord(part_number=1, slug="intro", status=ApprovalDecision.PENDING, reviewer_name="pending")
    approved = ApprovalRecord(part_number=1, slug="intro", status=ApprovalDecision.APPROVED, reviewer_name="reviewer")
    changes = ApprovalRecord(
        part_number=1,
        slug="intro",
        status=ApprovalDecision.CHANGES_REQUESTED,
        reviewer_name="reviewer",
    )

    assert route_after_approval({"approval_record": pending}) == "awaiting_human"
    assert route_after_approval({"approval_record": approved}) == "complete"
    assert route_after_approval({"approval_record": changes}) == "improve"
