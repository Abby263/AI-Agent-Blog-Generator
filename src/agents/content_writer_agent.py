"""
Content Writer Agent

Writes blog sections following the outline and style guidelines.
"""

from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.schemas.state import BlogState, SectionContent


class ContentWriterAgent(BaseAgent):
    """Content writer agent for generating blog sections."""
    
    def __init__(self):
        """Initialize content writer agent."""
        super().__init__("content_writer")
    
    def execute(self, state: BlogState) -> Dict[str, Any]:
        """
        Execute content writing for current section.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with section content
        """
        if not state.outline or state.current_section_index >= len(state.outline.sections):
            # All sections completed
            self.logger.info("All sections completed")
            return {
                "status": "generating_code",
                "current_agent": "code_generator",
                "messages": ["All sections written"]
            }
        
        # Get current section outline
        section_outline = state.outline.sections[state.current_section_index]
        self.logger.info(f"Writing section: {section_outline.title}")
        
        # Build writing prompt
        prompt = self._build_writing_prompt(state, section_outline)
        
        # Call LLM to write section
        response = self._call_llm(prompt)
        
        # Create section content
        section_content = SectionContent(
            title=section_outline.title,
            content=response,
            word_count=len(response.split()),
            code_placeholders=section_outline.code_examples,
            diagram_placeholders=section_outline.diagrams,
            citations=[]
        )
        
        self.logger.info(
            f"Completed section: {section_outline.title} "
            f"({section_content.word_count} words)"
        )
        
        # Prepare updates
        updates = {
            "sections": state.sections + [section_content],
            "current_section_index": state.current_section_index + 1,
            "messages": [
                f"Completed section {state.current_section_index + 1}/{len(state.outline.sections)}: {section_outline.title}"
            ]
        }
        
        # Check if more sections to write
        if state.current_section_index + 1 >= len(state.outline.sections):
            updates["status"] = "generating_code"
            updates["current_agent"] = "code_generator"
        
        return updates
    
    def _build_writing_prompt(
        self,
        state: BlogState,
        section_outline: Any
    ) -> str:
        """Build the content writing prompt."""
        # Get research summary info
        research_info = ""
        if state.research_summary:
            examples = state.research_summary.real_world_examples[:3]
            if examples:
                research_info = "\n\nReal-world examples:\n"
                for ex in examples:
                    research_info += f"- {ex.company}: {ex.system} - {ex.scale}\n"
        
        prompt = f"""You are a Content Writer Agent specializing in ML system design blog posts.

Write the "{section_outline.title}" section for a blog post about "{state.topic}".

Section Outline:
- Objectives: {', '.join(section_outline.objectives)}
- Key Points: {', '.join(section_outline.key_points)}
- Target Word Count: {section_outline.word_count}

{research_info}

Style Guidelines:
1. Technical but accessible - explain complex concepts clearly
2. Real-world focus - cite specific companies (Netflix, Uber, Google)
3. Conversational tone - use "we", "you", rhetorical questions
4. Evidence-based - include statistics and metrics
5. Include code examples where appropriate
6. Add diagram placeholders: ![Description](images/diagram_X.png)

Write comprehensive, production-quality content in markdown format.

Focus on practical, real-world implementation details with specific examples and metrics."""
        
        return prompt

