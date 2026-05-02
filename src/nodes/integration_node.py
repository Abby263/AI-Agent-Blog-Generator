"""Integration node for final assembly."""

from typing import Dict, Any
from src.agents.integration_agent import IntegrationAgent
from src.nodes.base import execute_node


def integration_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Integration node: Final blog assembly.
    
    Assembles all components:
    - Combines sections in order
    - Inserts diagrams and code
    - Generates table of contents
    - Formats markdown
    - Saves to file
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state with final content and metadata
    """
    return execute_node("Integration Node", IntegrationAgent, state)

