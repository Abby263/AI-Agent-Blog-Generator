"""Supervisor node for workflow orchestration."""

from typing import Dict, Any
from src.agents.supervisor_agent import SupervisorAgent
from src.nodes.base import execute_node


def supervisor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Supervisor node: Plan workflow and route tasks.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state dictionary with workflow plan
    """
    return execute_node("Supervisor Node", SupervisorAgent, state)

