"""
Supervisor Agent

Orchestrates the workflow, makes routing decisions, and plans task execution.
"""

from typing import Dict, Any
import json
from src.agents.base_agent import BaseAgent
from src.schemas.state import BlogState, WorkflowPlan
from src.utils.prompt_loader import get_prompt_loader


class SupervisorAgent(BaseAgent):
    """Supervisor agent for workflow orchestration."""
    
    def __init__(self):
        """Initialize supervisor agent."""
        super().__init__("supervisor")
        self.prompt_loader = get_prompt_loader()
    
    def execute(self, state: BlogState) -> Dict[str, Any]:
        """
        Execute supervisor logic: create workflow plan.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with workflow plan and status updates
        """
        self.logger.info(f"Planning workflow for topic: {state.topic}")
        
        # Build planning prompt
        prompt = self._build_planning_prompt(state)
        
        # Call LLM to create plan
        response = self._call_llm(prompt)
        
        # Parse response as JSON
        try:
            plan_data = self._extract_json_from_response(response)
            workflow_plan = WorkflowPlan(**plan_data)
            
            self.logger.info(f"Created workflow plan with {len(workflow_plan.critical_sections)} critical sections")
            
            return {
                "workflow_plan": workflow_plan,
                "status": "researching",
                "current_agent": "research",
                "messages": [
                    f"Workflow planned for topic: {state.topic}",
                    f"Estimated duration: {workflow_plan.estimated_duration_minutes} minutes"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing workflow plan: {str(e)}")
            # Return a default plan
            return self._create_default_plan(state)
    
    def _build_planning_prompt(self, state: BlogState) -> str:
        """Build the planning prompt."""
        content_type = state.content_config.content_type if state.content_config else "blog"
        
        # Detect content domain
        topic_lower = state.topic.lower()
        is_technical = any(keyword in topic_lower for keyword in [
            'system', 'ml', 'ai', 'machine learning', 'design', 'architecture',
            'engineering', 'data', 'algorithm', 'model', 'api', 'infrastructure'
        ])
        
        if is_technical:
            focus_guidance = """Focus on:
1. What engineering blogs to search (Netflix, Uber, Google, etc.)
2. What technical metrics are critical (latency, throughput, scale)
3. What technical sections are most important
4. What diagrams and code examples are needed"""
        else:
            focus_guidance = """Focus on:
1. What sources to research (news sites, expert analysis, official sources)
2. What information is critical (statistics, key facts, expert opinions)
3. What sections are most important for this topic
4. What visual elements (diagrams, charts) would help"""
        
        prompt_template = """You are the Supervisor Agent coordinating a multi-agent workflow to create high-quality {content_type} content.

Topic: {topic}
Content Type: {content_type}
User Requirements: {requirements}

Analyze this topic and create a detailed workflow plan.

{focus_guidance}

Output your plan in this JSON format:
{{
    "research_priorities": ["priority1", "priority2", "priority3"],
    "focus_areas": ["area1", "area2", "area3"],
    "critical_sections": ["section1", "section2"],
    "diagram_types": ["diagram type 1", "diagram type 2"],
    "code_examples_needed": ["example1 (if applicable)", "example2"],
    "estimated_duration_minutes": 45,
    "checkpoints": ["after_research", "after_outline", "after_qa"]
}}

IMPORTANT:
- Adapt your plan to the content type and topic domain
- For non-technical topics, code_examples_needed can be an empty list
- Use appropriate diagram types for the content (not always architecture/flowchart)
- Be specific about what research is needed for THIS specific topic

OUTPUT FORMAT:
- Return ONLY the JSON object, no additional text or explanation
- Ensure valid JSON syntax (no trailing commas, proper quotes)
- You may wrap it in ```json code blocks if you prefer"""
        
        default_requirements = f"Standard {content_type} content" if not is_technical else "Standard ML system design blog"
        
        return prompt_template.format(
            content_type=content_type,
            topic=state.topic,
            requirements=state.requirements or default_requirements,
            focus_guidance=focus_guidance
        )
    
    
    def _create_default_plan(self, state: BlogState) -> Dict[str, Any]:
        """Create a default workflow plan."""
        default_plan = WorkflowPlan(
            research_priorities=[
                f"{state.topic} engineering blog",
                f"{state.topic} production metrics",
                f"{state.topic} architecture"
            ],
            focus_areas=["system design", "scalability", "real-world implementation"],
            critical_sections=["problem_statement", "system_design", "evaluation"],
            diagram_types=["architecture", "flowchart", "data_flow"],
            code_examples_needed=["feature extraction", "model training", "system architecture"],
            estimated_duration_minutes=45,
            checkpoints=["after_research", "after_outline", "after_qa"]
        )
        
        return {
            "workflow_plan": default_plan,
            "status": "researching",
            "current_agent": "research",
            "messages": ["Using default workflow plan"]
        }

