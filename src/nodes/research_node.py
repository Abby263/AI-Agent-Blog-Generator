"""Research node for information gathering."""

from typing import Dict, Any
from src.agents.research_agent import ResearchAgent
from src.nodes.base import execute_node


def research_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Research node: Gather information from multiple sources.
    
    Research sources include:
    - Web search (Tavily)
    - Engineering blogs
    - YouTube videos
    - Academic papers
    - User-provided references
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state with research summary
    """
    return execute_node("Research Node", ResearchAgent, state)

