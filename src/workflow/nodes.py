"""
Node functions for LangGraph workflow.

Each node wraps an agent and handles state updates.
"""

from typing import Dict, Any
from src.schemas.state import BlogState
from src.agents import (
    SupervisorAgent,
    ResearchAgent,
    OutlineAgent,
    ContentWriterAgent,
    CodeGeneratorAgent,
    DiagramAgent,
    ReferenceAgent,
    QAAgent,
    IntegrationAgent
)
from src.utils.logger import get_logger

logger = get_logger()

# Initialize agents (singleton pattern)
_agents = {}


def _get_agent(agent_class):
    """Get or create agent instance."""
    agent_name = agent_class.__name__
    if agent_name not in _agents:
        _agents[agent_name] = agent_class()
    return _agents[agent_name]


def supervisor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Supervisor node: Plan workflow.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state dictionary
    """
    logger.info("=== Supervisor Node ===")
    blog_state = BlogState(**state)
    agent = _get_agent(SupervisorAgent)
    updates = agent.invoke(blog_state)
    return updates


def research_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Research node: Gather information.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state dictionary
    """
    logger.info("=== Research Node ===")
    blog_state = BlogState(**state)
    agent = _get_agent(ResearchAgent)
    updates = agent.invoke(blog_state)
    return updates


def outline_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Outline node: Create blog structure.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state dictionary
    """
    logger.info("=== Outline Node ===")
    blog_state = BlogState(**state)
    agent = _get_agent(OutlineAgent)
    updates = agent.invoke(blog_state)
    return updates


def content_writer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Content writer node: Write blog sections.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state dictionary
    """
    logger.info("=== Content Writer Node ===")
    blog_state = BlogState(**state)
    agent = _get_agent(ContentWriterAgent)
    updates = agent.invoke(blog_state)
    return updates


def code_generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Code generator node: Generate code examples.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state dictionary
    """
    logger.info("=== Code Generator Node ===")
    blog_state = BlogState(**state)
    agent = _get_agent(CodeGeneratorAgent)
    updates = agent.invoke(blog_state)
    return updates


def diagram_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Diagram node: Generate diagrams.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state dictionary
    """
    logger.info("=== Diagram Node ===")
    blog_state = BlogState(**state)
    agent = _get_agent(DiagramAgent)
    updates = agent.invoke(blog_state)
    return updates


def reference_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reference node: Manage citations.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state dictionary
    """
    logger.info("=== Reference Node ===")
    blog_state = BlogState(**state)
    agent = _get_agent(ReferenceAgent)
    updates = agent.invoke(blog_state)
    return updates


def qa_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    QA node: Quality assurance checks.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state dictionary
    """
    logger.info("=== QA Node ===")
    blog_state = BlogState(**state)
    agent = _get_agent(QAAgent)
    updates = agent.invoke(blog_state)
    return updates


def integration_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Integration node: Final assembly.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state dictionary
    """
    logger.info("=== Integration Node ===")
    blog_state = BlogState(**state)
    agent = _get_agent(IntegrationAgent)
    updates = agent.invoke(blog_state)
    return updates

