"""
Outline Agent

Creates detailed blog outline following the template structure.
"""

from typing import Dict, Any
import json
from src.agents.base_agent import BaseAgent
from src.schemas.state import BlogState, BlogOutline, SectionOutline


class OutlineAgent(BaseAgent):
    """Outline agent for creating blog structure."""
    
    def __init__(self):
        """Initialize outline agent."""
        super().__init__("outline")
    
    def execute(self, state: BlogState) -> Dict[str, Any]:
        """
        Execute outline generation.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with blog outline
        """
        self.logger.info(f"Creating outline for: {state.topic}")
        
        # Build outline prompt
        prompt = self._build_outline_prompt(state)
        
        # Call LLM to generate outline
        response = self._call_llm(prompt)
        
        # Parse outline
        try:
            outline_data = self._extract_json(response)
            outline = self._parse_outline(outline_data)
            
            self.logger.info(
                f"Created outline with {len(outline.sections)} sections, "
                f"~{outline.total_words} words"
            )
            
            return {
                "outline": outline,
                "status": "writing",
                "current_agent": "content_writer",
                "current_section_index": 0,
                "messages": [
                    f"Outline created with {len(outline.sections)} sections"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error creating outline: {str(e)}")
            return self._create_default_outline(state)
    
    def _build_outline_prompt(self, state: BlogState) -> str:
        """Build the outline generation prompt."""
        research_summary = ""
        if state.research_summary:
            examples = [ex.company for ex in state.research_summary.real_world_examples[:3]]
            research_summary = f"Real-world examples found: {', '.join(examples)}"
        
        prompt = f"""You are an Outline Agent creating a detailed blog outline for ML system design.

Topic: {state.topic}
{research_summary}

Create a comprehensive outline following this structure:

Required Sections:
1. Introduction (500-800 words) - Context, real-world examples, problem importance
2. Problem Statement (800-1200 words) - Use case, requirements, problem formulation
3. Feature Engineering (2000-3000 words) - Multiple feature categories, implementations
4. Models (1500-2000 words) - Baseline approaches, ML models, real-world deployments
5. System Design (1500-2000 words) - Architecture, components, scalability
6. Evaluation (1000-1500 words) - Metrics, monitoring
7. Case Study (800-1000 words) - Concrete example with metrics
8. Best Practices (300-400 words)
9. Common Mistakes (300-400 words)
10. Conclusion (200-300 words)
11. Test Your Learning (10-15 Q&A)
12. References (20-30 citations)

For each section, provide:
- Objectives (what to cover)
- Key points (3-5 main topics)
- Word count target
- Diagrams needed (IDs)
- Code examples needed (IDs)

Output JSON:
{{
    "sections": [
        {{
            "title": "Introduction",
            "objectives": ["objective1", "objective2"],
            "key_points": ["point1", "point2", "point3"],
            "word_count": 600,
            "diagrams": [],
            "code_examples": [],
            "real_world_references": ["Netflix", "Uber"]
        }}
    ],
    "total_words": 9000,
    "total_diagrams": 12,
    "total_code_examples": 20
}}

Create detailed objectives and key points for each section specific to {state.topic}."""
        
        return prompt
    
    def _extract_json(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start >= 0 and end > start:
            json_str = response[start:end]
            return json.loads(json_str)
        else:
            raise ValueError("No JSON found in response")
    
    def _parse_outline(self, outline_data: Dict[str, Any]) -> BlogOutline:
        """Parse outline data into BlogOutline object."""
        sections = [
            SectionOutline(**section)
            for section in outline_data.get("sections", [])
        ]
        
        return BlogOutline(
            sections=sections,
            total_words=outline_data.get("total_words", 9000),
            total_diagrams=outline_data.get("total_diagrams", 12),
            total_code_examples=outline_data.get("total_code_examples", 20)
        )
    
    def _create_default_outline(self, state: BlogState) -> Dict[str, Any]:
        """Create default outline if LLM generation fails."""
        default_sections = [
            SectionOutline(
                title="Introduction",
                objectives=["Set context", "Explain importance"],
                key_points=["Real-world context", "Problem complexity", "Blog overview"],
                word_count=600,
                diagrams=[],
                code_examples=[],
                real_world_references=["Netflix", "Uber"]
            ),
            SectionOutline(
                title="Problem Statement",
                objectives=["Define use case", "List requirements"],
                key_points=["Use case", "Functional requirements", "Non-functional requirements"],
                word_count=1000,
                diagrams=[],
                code_examples=[],
                real_world_references=[]
            ),
            # Add more default sections...
        ]
        
        outline = BlogOutline(
            sections=default_sections,
            total_words=9000,
            total_diagrams=12,
            total_code_examples=20
        )
        
        return {
            "outline": outline,
            "status": "writing",
            "current_agent": "content_writer",
            "messages": ["Using default outline"]
        }

