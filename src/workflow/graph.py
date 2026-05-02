"""
LangGraph workflow definition.

Creates and configures the multi-agent blog generation workflow.
"""

from typing import Dict, Any, TypedDict, Annotated, List, Optional, Callable
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
from src.utils.config_loader import get_config
from src.schemas.state import (
    BlogState,
    ContentConfiguration,
    SeriesConfiguration,
    BlogSeriesPlan
)
from src.agents.series_planner_agent import BlogSeriesPlannerAgent

logger = get_logger()
config = get_config()


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
    content_config: Any
    series_config: Any
    series_plan: Any
    previous_blogs: list
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
    author: str = "AI Agent",
    target_length: int = 8000,
    include_code: bool = True,
    include_diagrams: bool = True,
    content_type: str = "blog",
    series_config: Optional[SeriesConfiguration] = None,
    series_plan: Optional[BlogSeriesPlan] = None,
    current_blog_number: Optional[int] = None,
    previous_blogs: Optional[List[Dict[str, Any]]] = None,
    series_metadata: Optional[Dict[str, Any]] = None
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
    
    content_config = ContentConfiguration(
        content_type=content_type,
        target_length=target_length,
        include_code=include_code,
        include_diagrams=include_diagrams
    )
    
    metadata = {
        "author": author,
        "content_type": content_type,
        "target_length": target_length,
        "include_code": include_code,
        "include_diagrams": include_diagrams
    }
    if series_metadata:
        metadata["series"] = series_metadata
    
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
        "metadata": metadata,
        "retry_count": 0,
        "content_config": content_config,
        "series_config": series_config,
        "series_plan": series_plan,
        "current_blog_number": current_blog_number,
        "previous_blogs": previous_blogs or []
    }
    
    try:
        # Run workflow
        logger.info("Executing workflow...")
        workflow_config = config.get_workflow_config()
        langgraph_settings = workflow_config.get("langgraph", {})
        recursion_limit = langgraph_settings.get("recursion_limit", 50)
        result = app.invoke(initial_state, config={"recursion_limit": recursion_limit})
        
        logger.info("✓ Workflow completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Workflow execution error: {str(e)}", exc_info=True)
        raise


def run_blog_series(
    series_name: str,
    number_of_blogs: int,
    author: str = "AI Agent",
    requirements: str = "",
    target_length: int = 8000,
    include_code: bool = True,
    include_diagrams: bool = True,
    content_type: str = "blog",
    topics: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[str], None]] = None
) -> list:
    """Generate a full blog series, planning titles when needed."""
    if number_of_blogs < 1:
        raise ValueError("number_of_blogs must be at least 1")
    
    if topics and len(topics) != number_of_blogs:
        raise ValueError("Number of provided topics must match number_of_blogs")
    
    if topics:
        series_plan, blog_titles = _build_plan_from_topics(series_name, topics)
    else:
        series_plan, blog_titles = _plan_blog_series(
            series_name=series_name,
            number_of_blogs=number_of_blogs,
            author=author,
            requirements=requirements,
            target_length=target_length,
            content_type=content_type
        )
    
    series_config = SeriesConfiguration(
        series_name=series_name,
        number_of_blogs=number_of_blogs,
        topics=blog_titles,
        main_topic=series_name,
        content_type=content_type
    )
    
    start_message = (
        f"Starting blog series generation for '{series_name}' with {number_of_blogs} blogs"
    )
    logger.info(start_message)
    if progress_callback:
        progress_callback(start_message)
    for idx, title in enumerate(blog_titles, 1):
        logger.info(f"  Blog {idx}: {title}")
    
    results = []
    previous_blogs: List[Dict[str, Any]] = []
    for i, blog_title in enumerate(blog_titles, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Blog {i}/{number_of_blogs}: {blog_title}")
        logger.info(f"{'='*60}\n")
        if progress_callback:
            progress_callback(f"Starting blog {i}/{number_of_blogs}: {blog_title}")
        
        try:
            result = run_workflow(
                topic=blog_title,
                requirements=requirements,
                author=author,
                target_length=target_length,
                include_code=include_code,
                include_diagrams=include_diagrams,
                content_type=content_type,
                series_config=series_config,
                series_plan=series_plan,
                current_blog_number=i,
                previous_blogs=previous_blogs,
                series_metadata={
                    "series_name": series_name,
                    "content_type": content_type,
                    "blog_title": blog_title,
                    "current_blog_number": i,
                    "total_blogs": number_of_blogs
                }
            )
            previous_blogs.append({"title": blog_title})
            results.append({
                "topic": blog_title,
                "status": "completed",
                "result": result
            })
            if progress_callback:
                progress_callback(f"Completed blog {i}/{number_of_blogs}: {blog_title}")
        except Exception as e:
            logger.error(f"Failed to generate blog for '{blog_title}': {str(e)}")
            results.append({
                "topic": blog_title,
                "status": "failed",
                "error": str(e)
            })
            if progress_callback:
                progress_callback(
                    f"Failed blog {i}/{number_of_blogs}: {blog_title} ({str(e)})"
                )
    
    completed = sum(1 for r in results if r["status"] == "completed")
    summary_message = (
        f"\nBlog series '{series_name}' completed: {completed}/{number_of_blogs} successful"
    )
    logger.info(summary_message)
    if progress_callback:
        progress_callback(summary_message)

    return results


def _plan_blog_series(
    series_name: str,
    number_of_blogs: int,
    author: str,
    requirements: str,
    target_length: int,
    content_type: str
) -> tuple[BlogSeriesPlan, List[str]]:
    """
    Use the series planner agent to define the series structure.
    
    First does research on the series topic to understand context,
    then generates appropriate blog titles based on findings.
    """
    from src.agents.research_agent import ResearchAgent
    
    logger.info(f"Researching series topic: {series_name}")
    
    # Step 1: Research the series topic to understand what it's about
    research_agent = ResearchAgent()
    research_state = BlogState(
        topic=series_name,
        requirements=requirements,
        metadata={"author": author},
        content_config=ContentConfiguration(
            target_length=target_length,
            content_type=content_type
        )
    )
    
    research_summary = None
    try:
        research_updates = research_agent.invoke(research_state)
        research_summary = research_updates.get("research_summary")
        logger.info(f"✓ Completed research for series planning")
    except Exception as exc:
        logger.warning(f"Research failed for series planning: {exc}")
    
    # Step 2: Use research context to generate appropriate blog titles
    planner = BlogSeriesPlannerAgent()
    try:
        planning_state = BlogState(
            topic=series_name,
            requirements=requirements,
            research_summary=research_summary,  # Pass research context
            metadata={
                "author": author,
                "series_config": {
                    "series_name": series_name,
                    "number_of_blogs": number_of_blogs,
                    "topics": [],
                    "main_topic": series_name,
                    "content_type": content_type
                }
            },
            content_config=ContentConfiguration(
                target_length=target_length,
                content_type=content_type
            )
        )
        updates = planner.invoke(planning_state)
        plan_data = updates.get("metadata", {}).get("series_plan")
        if plan_data:
            plan = BlogSeriesPlan.parse_obj(plan_data)
            topics = _extract_topics_from_plan(plan, series_name, number_of_blogs)
            plan = _ensure_plan_has_topics(plan, topics)
            logger.info(
                f"Series planner generated plan '{plan.series_title}' based on research"
            )
            return plan, topics
    except Exception as exc:
        logger.warning(f"Series planner failed, falling back to default plan: {exc}")
    
    return _build_default_plan(series_name, number_of_blogs)


def _build_plan_from_topics(
    series_name: str,
    topics: List[str]
) -> tuple[BlogSeriesPlan, List[str]]:
    """Create a simple plan using user-provided topics."""
    number_of_blogs = len(topics)
    plan_dict = {
        "series_title": series_name,
        "blogs": [
            {
                "blog_number": idx + 1,
                "title": title,
                "subtitle": f"Part {idx+1} of {number_of_blogs}",
                "main_focus": title,
                "connects_to": [idx + 2] if idx < number_of_blogs - 1 else [],
                "difficulty": "intermediate",
                "prerequisites": [f"Blog {idx}"] if idx > 0 else []
            }
            for idx, title in enumerate(topics)
        ],
        "narrative_arc": f"{series_name} series covering {number_of_blogs} topics",
        "common_themes": [series_name],
        "cross_references": {}
    }
    return BlogSeriesPlan(**plan_dict), topics


def _build_default_plan(
    series_name: str,
    number_of_blogs: int
) -> tuple[BlogSeriesPlan, List[str]]:
    """Fallback series plan when the planner cannot generate one."""
    default_topics = [f"{series_name}: Part {idx+1}" for idx in range(number_of_blogs)]
    return _build_plan_from_topics(series_name, default_topics)


def _extract_topics_from_plan(
    plan: BlogSeriesPlan,
    series_name: str,
    number_of_blogs: int
) -> List[str]:
    """Extract blog titles from a plan with sensible fallbacks."""
    topics: List[str] = []
    for idx in range(number_of_blogs):
        title = None
        if idx < len(plan.blogs):
            blog_entry = plan.blogs[idx]
            if isinstance(blog_entry, dict):
                title = blog_entry.get("title") or blog_entry.get("main_focus")
        if not title:
            title = f"{series_name}: Part {idx+1}"
        topics.append(title)
    return topics


def _ensure_plan_has_topics(
    plan: BlogSeriesPlan,
    topics: List[str]
) -> BlogSeriesPlan:
    """Ensure the plan contains entries for every topic/title."""
    plan_dict = plan.dict()
    blogs = plan_dict.get("blogs", [])
    for idx, title in enumerate(topics):
        if idx < len(blogs):
            blogs[idx]["title"] = title
            blogs[idx].setdefault("blog_number", idx + 1)
        else:
            blogs.append({
                "blog_number": idx + 1,
                "title": title,
                "subtitle": f"Part {idx+1} of {len(topics)}",
                "main_focus": title,
                "connects_to": [idx + 2] if idx < len(topics) - 1 else [],
                "difficulty": "intermediate",
                "prerequisites": [f"Blog {idx}"] if idx > 0 else []
            })
    plan_dict["blogs"] = blogs[: len(topics)]
    return BlogSeriesPlan(**plan_dict)
