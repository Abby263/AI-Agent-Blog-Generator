"""
LangSmith UI Integration for AI Agent Blog Series Generator.

This module exposes the workflow graph for LangSmith Studio UI.
Run with: langgraph dev --no-browser

The graph can be triggered and monitored through LangSmith Studio.
"""

from typing import Annotated, Any, Dict, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from src.workflow.graph import create_workflow
from src.utils.config_loader import get_config
from dotenv import load_dotenv
import operator

# Load environment variables
load_dotenv()

# Load configuration
config = get_config()


class UserInputState(TypedDict):
    """
    Clean user input schema for LangSmith Studio UI.
    Only shows the fields users should configure.
    """
    
    topic: Annotated[
        str,
        ...,
        "Blog topic to generate content about. Example: 'Real-Time Fraud Detection'"
    ]
    
    requirements: Annotated[
        str,
        "",
        "System requirements/specifications. Example: 'Scale: 1M TPS, Latency: <50ms'"
    ]
    
    author: Annotated[
        str,
        "AI Agent",
        "Author name for the blog"
    ]
    
    target_length: Annotated[
        int,
        8000,
        "Target word count for the blog post (500-50000)"
    ]
    
    include_code: Annotated[
        bool,
        True,
        "Whether to include code examples in the blog"
    ]
    
    include_diagrams: Annotated[
        bool,
        True,
        "Whether to include diagrams in the blog"
    ]
    
    tone: Annotated[
        str,
        "professional",
        "Writing tone: professional, casual, or academic"
    ]
    
    content_type: Annotated[
        str,
        "blog",
        "Type of content: blog, news, tutorial, or review"
    ]


class WorkflowState(TypedDict):
    """
    Complete workflow state - includes user inputs plus all internal state.
    """
    
    # User inputs
    topic: str
    requirements: str
    author: str
    target_length: int
    include_code: bool
    include_diagrams: bool
    tone: str
    content_type: str
    
    # Workflow management
    status: str
    current_agent: str
    messages: Annotated[List[str], operator.add]
    
    # Workflow data
    workflow_plan: Any
    research_summary: Any
    outline: Any
    sections: Annotated[List, operator.add]
    current_section_index: int
    code_blocks: Annotated[List, operator.add]
    diagrams: Annotated[List, operator.add]
    references: List
    quality_report: Any
    final_content: str
    metadata: Dict
    retry_count: int


def transform_input_to_workflow_state(user_input: UserInputState) -> WorkflowState:
    """Transform user input to complete workflow state with defaults."""
    return WorkflowState(
        # User inputs
        topic=user_input["topic"],
        requirements=user_input.get("requirements", ""),
        author=user_input.get("author", "AI Agent"),
        target_length=user_input.get("target_length", 8000),
        include_code=user_input.get("include_code", True),
        include_diagrams=user_input.get("include_diagrams", True),
        tone=user_input.get("tone", "professional"),
        content_type=user_input.get("content_type", "blog"),
        
        # Initialize workflow state
        status="initialized",
        current_agent="supervisor_agent",
        messages=[f"Starting {user_input.get('content_type', 'blog')} generation for: {user_input['topic']}"],
        
        # Initialize empty workflow data
        workflow_plan=None,
        research_summary=None,
        outline=None,
        sections=[],
        current_section_index=0,
        code_blocks=[],
        diagrams=[],
        references=[],
        quality_report=None,
        final_content="",
        metadata={
            "author": user_input.get("author", "AI Agent"),
            "target_length": user_input.get("target_length", 8000),
            "tone": user_input.get("tone", "professional"),
            "content_type": user_input.get("content_type", "blog"),
            "include_code": user_input.get("include_code", True),
            "include_diagrams": user_input.get("include_diagrams", True)
        },
        retry_count=0
    )


# Import the workflow nodes and routing
from src.workflow.nodes import (
    supervisor_node,
    research_node,
    outline_node,
    content_writer_node,
    code_generator_node,
    diagram_node,
    reference_node,
    qa_node,
    integration_node
)
from src.workflow.routing import (
    should_continue_writing,
    route_after_qa
)


def create_ui_workflow():
    """Create workflow with clean user input interface."""
    
    # Create workflow with clean input state
    workflow = StateGraph(WorkflowState, input=UserInputState)
    
    # Add nodes (agents) - using "_agent" suffix to avoid state key conflicts
    workflow.add_node("supervisor_agent", supervisor_node)
    workflow.add_node("research_agent", research_node)
    workflow.add_node("outline_agent", outline_node)
    workflow.add_node("content_writer_agent", content_writer_node)
    workflow.add_node("code_generator_agent", code_generator_node)
    workflow.add_node("diagram_agent", diagram_node)
    workflow.add_node("reference_agent", reference_node)
    workflow.add_node("qa_agent", qa_node)
    workflow.add_node("integration_agent", integration_node)
    
    # Set entry point
    workflow.set_entry_point("supervisor_agent")
    
    # Define edges (workflow flow)
    workflow.add_edge("supervisor_agent", "research_agent")
    workflow.add_edge("research_agent", "outline_agent")
    workflow.add_edge("outline_agent", "content_writer_agent")
    
    # Conditional: check if more sections to write
    workflow.add_conditional_edges(
        "content_writer_agent",
        should_continue_writing,
        {
            "continue_writing": "content_writer_agent",
            "generate_code": "code_generator_agent"
        }
    )
    
    # Linear flow: code → diagrams → references → QA
    workflow.add_edge("code_generator_agent", "diagram_agent")
    workflow.add_edge("diagram_agent", "reference_agent")
    workflow.add_edge("reference_agent", "qa_agent")
    
    # Conditional: QA decision
    workflow.add_conditional_edges(
        "qa_agent",
        route_after_qa,
        {
            "integration": "integration_agent",
            "content_writer": "content_writer_agent",
            "human_review": END
        }
    )
    
    # Final edge: integration → END
    workflow.add_edge("integration_agent", END)
    
    return workflow.compile()


# Create the graph for LangSmith Studio
graph = create_ui_workflow()

# Export for LangSmith Studio
__all__ = ["graph", "UserInputState"]

