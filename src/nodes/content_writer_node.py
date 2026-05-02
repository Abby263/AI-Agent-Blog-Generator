"""Content writer node for section generation."""

from typing import Dict, Any
from src.agents.content_writer_agent import ContentWriterAgent
from src.nodes.base import execute_node


def content_writer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Content writer node: Write blog sections.
    
    Writes one section at a time, maintaining:
    - Consistent style and tone
    - Continuity with previous sections
    - Target word count
    - Template compliance
    
    For series blogs, maintains continuity with previous blogs
    by referencing series context.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state with new section content
    """
    return execute_node("Content Writer Node", ContentWriterAgent, state)

