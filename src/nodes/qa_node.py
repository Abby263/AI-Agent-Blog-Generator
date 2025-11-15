"""QA node for quality assurance."""

from typing import Dict, Any
from src.agents.qa_agent import QAAgent
from src.nodes.base import execute_node


def qa_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    QA node: Quality assurance checks.
    
    Validates:
    - Technical accuracy
    - Completeness (all template sections present)
    - Consistency (style, tone, formatting)
    - Code quality
    - Reference quality
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state with quality report
    """
    return execute_node("QA Node", QAAgent, state)

