"""Code generator node for code examples."""

from typing import Dict, Any
from src.agents.code_generator_agent import CodeGeneratorAgent
from src.nodes.base import execute_node


def code_generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Code generator node: Generate code examples.
    
    Creates production-quality code with:
    - Type hints
    - Docstrings
    - Error handling
    - Comments
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state with generated code blocks
    """
    return execute_node("Code Generator Node", CodeGeneratorAgent, state)

