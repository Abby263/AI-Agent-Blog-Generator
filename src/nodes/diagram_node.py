"""Diagram node for visual generation."""

from typing import Dict, Any
from src.agents.diagram_agent import DiagramAgent
from src.nodes.base import execute_node


def diagram_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Diagram node: Generate diagrams.
    
    Creates visual diagrams:
    - Architecture diagrams
    - Flowcharts
    - Sequence diagrams
    - Data flow diagrams
    
    Converts Mermaid code to PNG images.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state with generated diagrams
    """
    return execute_node("Diagram Node", DiagramAgent, state)

