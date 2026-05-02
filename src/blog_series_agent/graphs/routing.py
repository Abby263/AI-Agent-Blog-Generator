"""Conditional routing helpers for the LangGraph workflow."""

from __future__ import annotations

from ..config.settings import RunMode
from ..schemas.approval import ApprovalDecision
from .state import BlogWorkflowState


def route_after_length_check(state: BlogWorkflowState) -> str:
    """Route after the length check node: re-expand if still under target, else continue."""
    config = state["config"]
    draft = state.get("final_markdown") or state.get("draft_markdown", "")
    word_count = len(draft.split())
    iteration = state.get("length_expansion_iteration", 0)
    max_expansions = 2

    if word_count < config.min_word_count and iteration < max_expansions:
        return "length_check"

    if config.enable_review:
        return "review"
    if config.enable_asset_plan:
        return "asset"
    if config.enable_evaluation:
        return "evaluation"
    if config.enable_memory:
        return "memory_update"
    if config.enable_human_approval and config.approval_required:
        return "approval"
    return "complete"


def route_after_review(state: BlogWorkflowState) -> str:
    config = state["config"]
    if config.enable_improve:
        return "improve"
    if config.enable_asset_plan:
        return "asset"
    if config.enable_evaluation:
        return "evaluation"
    if config.enable_memory:
        return "memory_update"
    if config.enable_human_approval and config.approval_required:
        return "approval"
    return "complete"


def route_after_improve(state: BlogWorkflowState) -> str:
    config = state["config"]
    if config.enable_asset_plan:
        return "asset"
    if config.enable_evaluation:
        return "evaluation"
    if config.enable_memory:
        return "memory_update"
    if config.enable_human_approval and config.approval_required:
        return "approval"
    return "complete"


def route_after_asset(state: BlogWorkflowState) -> str:
    if state["config"].enable_evaluation:
        return "evaluation"
    if state["config"].enable_memory:
        return "memory_update"
    config = state["config"]
    if config.run_mode == RunMode.DEV and not config.approval_required:
        return "complete"
    if not config.enable_human_approval or not config.approval_required:
        return "complete"
    return "approval"


def route_after_evaluation(state: BlogWorkflowState) -> str:
    if state["config"].enable_memory:
        return "memory_update"
    if state["config"].enable_human_approval and state["config"].approval_required:
        return "approval"
    return "complete"


def route_after_memory(state: BlogWorkflowState) -> str:
    if state["config"].enable_human_approval and state["config"].approval_required:
        return "approval"
    return "complete"


def route_after_approval(state: BlogWorkflowState) -> str:
    record = state.get("approval_record")
    if record is None or record.status == ApprovalDecision.PENDING:
        return "awaiting_human"
    if record.status in {ApprovalDecision.APPROVED, ApprovalDecision.APPROVED_WITH_NOTES}:
        return "complete"
    if record.status == ApprovalDecision.CHANGES_REQUESTED:
        return "improve"
    return "rejected"
