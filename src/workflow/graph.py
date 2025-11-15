"""
LangGraph workflow definition.

Creates and configures the multi-agent blog generation workflow.
"""

from typing import Dict, Any, TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
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
    check_quality_decision,
    route_after_qa
)
from src.utils.logger import get_logger
from src.schemas.state import BlogState

logger = get_logger()


# Define graph state type for LangGraph
class GraphState(TypedDict):
    """State type for LangGraph workflow."""
    
    # Input
    topic: str
    requirements: str
    
    # Workflow management
    status: str
    current_agent: str
    messages: Annotated[list, operator.add]
    
    # All other fields from BlogState
    workflow_plan: Any
    research_summary: Any
    outline: Any
    sections: Annotated[list, operator.add]
    current_section_index: int
    code_blocks: Annotated[list, operator.add]
    diagrams: Annotated[list, operator.add]
    references: list
    quality_report: Any
    final_content: str
    metadata: dict
    retry_count: int


def create_workflow() -> StateGraph:
    """
    Create the LangGraph workflow.
    
    Returns:
        Compiled StateGraph ready to execute
    """
    logger.info("Creating LangGraph workflow")
    
    # Create workflow graph
    workflow = StateGraph(GraphState)
    
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
    
    # Linear flow: supervisor → research → outline
    workflow.add_edge("supervisor_agent", "research_agent")
    workflow.add_edge("research_agent", "outline_agent")
    workflow.add_edge("outline_agent", "content_writer_agent")
    
    # Conditional: check if more sections to write
    workflow.add_conditional_edges(
        "content_writer_agent",
        should_continue_writing,
        {
            "continue_writing": "content_writer_agent",  # Loop back
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
            "content_writer": "content_writer_agent",  # Revision needed
            "human_review": END  # Stop for human review
        }
    )
    
    # Final edge: integration → END
    workflow.add_edge("integration_agent", END)
    
    # Compile workflow
    app = workflow.compile()
    
    logger.info("✓ Workflow created successfully")
    return app


def run_workflow(
    topic: str,
    requirements: str = "",
    author: str = "AI Agent"
) -> Dict[str, Any]:
    """
    Run the blog generation workflow.
    
    Args:
        topic: Blog topic
        requirements: Optional requirements/specifications
        author: Author name
        
    Returns:
        Final state dictionary with completed blog
    """
    logger.info(f"Starting workflow for topic: {topic}")
    
    # Create workflow
    app = create_workflow()
    
    # Initialize state
    initial_state = {
        "topic": topic,
        "requirements": requirements,
        "status": "initialized",
        "current_agent": "supervisor",
        "messages": [f"Starting blog generation for: {topic}"],
        "workflow_plan": None,
        "research_summary": None,
        "outline": None,
        "sections": [],
        "current_section_index": 0,
        "code_blocks": [],
        "diagrams": [],
        "references": [],
        "quality_report": None,
        "final_content": "",
        "metadata": {"author": author},
        "retry_count": 0
    }
    
    try:
        # Run workflow
        logger.info("Executing workflow...")
        result = app.invoke(initial_state)
        
        logger.info("✓ Workflow completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Workflow execution error: {str(e)}", exc_info=True)
        raise


def run_blog_series(
    topics: list,
    author: str = "AI Agent"
) -> list:
    """
    Run workflow for multiple blog topics.
    
    Args:
        topics: List of blog topics
        author: Author name
        
    Returns:
        List of results for each blog
    """
    logger.info(f"Starting blog series generation for {len(topics)} topics")
    
    results = []
    for i, topic in enumerate(topics, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Blog {i}/{len(topics)}: {topic}")
        logger.info(f"{'='*60}\n")
        
        try:
            result = run_workflow(topic=topic, author=author)
            results.append({
                "topic": topic,
                "status": "completed",
                "result": result
            })
        except Exception as e:
            logger.error(f"Failed to generate blog for '{topic}': {str(e)}")
            results.append({
                "topic": topic,
                "status": "failed",
                "error": str(e)
            })
    
    # Summary
    completed = sum(1 for r in results if r["status"] == "completed")
    logger.info(f"\nBlog series completed: {completed}/{len(topics)} successful")
    
    return results

