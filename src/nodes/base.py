"""
Base utilities for node functions.
"""

from typing import Dict, Any, Type
from src.agents.base_agent import BaseAgent
from src.schemas.state import BlogState
from src.utils.logger import get_logger

logger = get_logger()

# Global agent cache (singleton pattern)
_agents: Dict[str, BaseAgent] = {}


def get_agent(agent_class: Type[BaseAgent]) -> BaseAgent:
    """
    Get or create agent instance (singleton pattern).
    
    Args:
        agent_class: Agent class to instantiate
        
    Returns:
        Agent instance
    """
    agent_name = agent_class.__name__
    if agent_name not in _agents:
        _agents[agent_name] = agent_class()
    return _agents[agent_name]


def execute_node(
    node_name: str,
    agent_class: Type[BaseAgent],
    state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute a node with logging and error handling.
    
    Args:
        node_name: Name of the node for logging
        agent_class: Agent class to execute
        state: Current state dictionary
        
    Returns:
        Updated state dictionary
    """
    logger.info(f"=== {node_name} ===")
    
    try:
        # Convert to BlogState
        blog_state = BlogState(**state)
        
        # Get agent and invoke
        agent = get_agent(agent_class)
        updates = agent.invoke(blog_state)
        
        return updates
        
    except Exception as e:
        logger.error(f"Error in {node_name}: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "messages": [f"✗ {node_name} failed: {str(e)}"]
        }

