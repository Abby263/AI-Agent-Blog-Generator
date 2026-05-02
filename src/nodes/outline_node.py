"""Outline node for content structure."""

from typing import Dict, Any
from src.agents.outline_agent import OutlineAgent
from src.nodes.base import execute_node


def outline_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Outline node: Create blog structure based on template.
    
    Uses the appropriate template based on content type:
    - blog: Standard blog template with TOC, Introduction, Conclusion
    - news: News article template with breaking news format
    - tutorial: Tutorial template with step-by-step structure
    - review: Review template with pros/cons structure
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state with blog outline
    """
    return execute_node("Outline Node", OutlineAgent, state)

