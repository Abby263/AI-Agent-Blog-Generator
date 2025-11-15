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
            plan_data = self._extract_json(response)
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
        prompt_template = """You are the Supervisor Agent coordinating a multi-agent workflow to create high-quality ML system design blog posts.

Topic: {topic}
User Requirements: {requirements}

Analyze this topic and create a detailed workflow plan. Focus on:
1. What engineering blogs to search (Netflix, Uber, Google, etc.)
2. What metrics are critical (latency, throughput, scale)
3. What sections are most important for this topic
4. What diagrams and code examples are needed

Output your plan in this JSON format:
{{
    "research_priorities": ["priority1", "priority2", "priority3"],
    "focus_areas": ["area1", "area2", "area3"],
    "critical_sections": ["section1", "section2"],
    "diagram_types": ["architecture", "flowchart", "data_flow"],
    "code_examples_needed": ["example1", "example2"],
    "estimated_duration_minutes": 45,
    "checkpoints": ["after_research", "after_outline", "after_qa"]
}}

Be specific about what research is needed and which sections are critical for this topic."""
        
        return prompt_template.format(
            topic=state.topic,
            requirements=state.requirements or "Standard ML system design blog"
        )
    
    def _extract_json(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        # Try to find JSON in the response
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start >= 0 and end > start:
            json_str = response[start:end]
            return json.loads(json_str)
        else:
            raise ValueError("No JSON found in response")
    
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

