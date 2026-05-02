"""
Routing logic for conditional edges in the workflow.
"""

from typing import Literal, Dict, Any
from src.utils.logger import get_logger
from src.utils.config_loader import get_config

logger = get_logger()
config = get_config()


def should_continue_writing(state: Dict[str, Any]) -> Literal["continue_writing", "generate_code"]:
    """
    Determine if more sections need to be written.
    
    Args:
        state: Current state
        
    Returns:
        Next node to execute
    """
    sections_completed = len(state.get("sections", []))
    
    if state.get("outline"):
        total_sections = len(state["outline"].sections)
        
        if sections_completed < total_sections:
            logger.info(f"Continuing writing: {sections_completed}/{total_sections} sections done")
            return "continue_writing"
    
    logger.info("All sections written, moving to code generation")
    return "generate_code"


def check_quality_decision(
    state: Dict[str, Any]
) -> Literal["pass", "fail", "human_review"]:
    """
    Make routing decision based on quality check results.
    
    Args:
        state: Current state
        
    Returns:
        Routing decision: pass, fail, or human_review
    """
    quality_report = state.get("quality_report")
    
    if not quality_report:
        logger.warning("No quality report found, requesting human review")
        return "human_review"
    
    decision = quality_report.decision
    critical_issues = len(quality_report.critical_issues)
    
    logger.info(
        f"Quality decision: {decision}, "
        f"score: {quality_report.overall_score:.2f}, "
        f"critical issues: {critical_issues}"
    )
    
    if decision in ["pass", "pass_with_minor_revisions"]:
        return "pass"
    elif decision in ["needs_revision", "reject"]:
        if critical_issues > 0:
            return "fail"
        else:
            return "human_review"
    else:
        return "human_review"


def route_from_supervisor(state: Dict[str, Any]) -> Literal["research"]:
    """
    Route from supervisor (always goes to research).
    
    Args:
        state: Current state
        
    Returns:
        Next node
    """
    return "research"


def route_after_qa(state: Dict[str, Any]) -> str:
    """
    Route after QA based on quality check.
    
    Args:
        state: Current state
        
    Returns:
        Next node name
    """
    decision = check_quality_decision(state)
    
    if decision == "pass":
        return "integration"
    elif decision == "fail":
        # Revise content - go back to content writer, but avoid infinite loops
        workflow_config = config.get_workflow_config()
        langgraph_settings = workflow_config.get("langgraph", {})
        max_revision_loops = langgraph_settings.get("max_revision_loops", 3)
        state["retry_count"] = state.get("retry_count", 0) + 1
        if state["retry_count"] >= max_revision_loops:
            logger.warning(
                "Reached max revision loops (%s). Routing to human review.",
                max_revision_loops,
            )
            return "human_review"
        logger.warning(
            "Quality check failed, needs revision (attempt %s/%s)",
            state["retry_count"],
            max_revision_loops,
        )
        return "content_writer"
    else:
        # Human review needed
        logger.info("Human review needed")
        return "human_review"
