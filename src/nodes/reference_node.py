"""Reference node for citation management."""

from typing import Dict, Any
from src.agents.reference_agent import ReferenceAgent
from src.nodes.base import execute_node


def reference_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reference node: Manage citations and references.
    
    Collects and formats:
    - Research sources
    - Engineering blogs
    - YouTube videos
    - User-provided references
    - Academic papers
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state with formatted references
    """
    return execute_node("Reference Node", ReferenceAgent, state)

