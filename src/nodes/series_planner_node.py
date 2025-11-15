"""Blog series planner node."""

from typing import Dict, Any
from src.agents.series_planner_agent import BlogSeriesPlannerAgent
from src.nodes.base import execute_node


def series_planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Series planner node: Define all blog titles in the series.
    
    This node runs first for series generation to:
    - Define titles for all blogs in the series
    - Ensure continuity between blogs
    - Plan the narrative arc
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state with planned blog titles
    """
    return execute_node("Series Planner Node", BlogSeriesPlannerAgent, state)

