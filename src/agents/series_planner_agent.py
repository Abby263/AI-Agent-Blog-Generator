"""
Blog Series Planner Agent

Plans all blog titles in a series upfront to ensure continuity and progression.
"""

from typing import Dict, Any, List
import json
from src.agents.base_agent import BaseAgent
from src.schemas.state import BlogState
from src.utils.yaml_prompt_loader import get_yaml_prompt_loader


class BlogSeriesPlannerAgent(BaseAgent):
    """Agent for planning blog series with continuity."""
    
    def __init__(self):
        """Initialize blog series planner agent."""
        super().__init__("series_planner")
        self.prompt_loader = get_yaml_prompt_loader()
    
    def execute(self, state: BlogState) -> Dict[str, Any]:
        """
        Plan all blog titles in the series upfront.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with series plan including all blog titles
        """
        # Check if this is a series generation
        series_config = state.metadata.get("series_config")
        
        if not series_config:
            # Not a series, skip this agent
            self.logger.info("Not a series generation, skipping planner")
            return {
                "status": "researching",
                "current_agent": "research",
                "messages": ["Single blog mode, skipping series planner"]
            }
        
        self.logger.info(f"Planning series: {series_config.get('series_name')}")
        
        # Build series planning prompt
        prompt = self._build_series_plan_prompt(state, series_config)
        
        # Call LLM to create series plan
        response = self._call_llm(prompt)
        
        # Parse series plan
        try:
            plan_data = self._extract_json_from_response(response)
            
            self.logger.info(
                f"Created series plan with {len(plan_data.get('blogs', []))} blogs"
            )
            
            # Store series plan in metadata
            return {
                "metadata": {
                    **state.metadata,
                    "series_plan": plan_data
                },
                "status": "researching",
                "current_agent": "research",
                "messages": [
                    f"Series plan created: {plan_data.get('series_title')}",
                    f"Planned {len(plan_data.get('blogs', []))} blogs"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error creating series plan: {str(e)}")
            # Proceed with default titles
            return self._create_default_series_plan(state, series_config)
    
    def _build_series_plan_prompt(
        self,
        state: BlogState,
        series_config: Dict[str, Any]
    ) -> str:
        """Build the series planning prompt using YAML template."""
        # Build research context if available
        research_context = ""
        if state.research_summary:
            research_context = "\n\nRESEARCH FINDINGS:\n"
            if state.research_summary.real_world_examples:
                research_context += "Key Examples Found:\n"
                for ex in state.research_summary.real_world_examples[:3]:
                    research_context += f"- {ex.company}: {ex.system} ({ex.scale})\n"
            if state.research_summary.statistics:
                research_context += "\nRelevant Statistics:\n"
                for stat in state.research_summary.statistics[:3]:
                    research_context += f"- {stat.metric}: {stat.value}\n"
            research_context += "\nUse this research to create contextually appropriate, accurate blog titles."
        
        prompt = self.prompt_loader.get_prompt(
            agent_name="series_planner",
            prompt_type="planning",
            series_name=series_config.get("series_name", "Blog Series"),
            number_of_blogs=series_config.get("number_of_blogs", 3),
            main_topic=series_config.get("main_topic", state.topic),
            target_audience=series_config.get("target_audience", "General readers"),
            content_type=series_config.get("content_type", "blog"),
            provided_topics=", ".join(series_config.get("topics", []))
        )
        
        # Append research context to the prompt
        if research_context:
            prompt += research_context
        
        return prompt
    
    
    def _create_default_series_plan(
        self,
        state: BlogState,
        series_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create default series plan if LLM generation fails."""
        topics = series_config.get("topics", [])
        number_of_blogs = series_config.get("number_of_blogs", len(topics))
        
        blogs = []
        for i in range(number_of_blogs):
            topic = topics[i] if i < len(topics) else f"Topic {i+1}"
            blogs.append({
                "blog_number": i + 1,
                "title": topic,
                "subtitle": f"Part {i+1} of {number_of_blogs}",
                "main_focus": topic,
                "connects_to": [i+2] if i < number_of_blogs - 1 else [],
                "difficulty": "intermediate",
                "prerequisites": [f"Blog {i}"] if i > 0 else []
            })
        
        default_plan = {
            "series_title": series_config.get("series_name", "Blog Series"),
            "blogs": blogs,
            "narrative_arc": "Progressive series covering key topics",
            "common_themes": ["Technical depth", "Practical examples"],
            "cross_references": {}
        }
        
        return {
            "metadata": {
                **state.metadata,
                "series_plan": default_plan
            },
            "status": "researching",
            "current_agent": "research",
            "messages": ["Using default series plan"]
        }

