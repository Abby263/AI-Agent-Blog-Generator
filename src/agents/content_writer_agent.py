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
                research_info = "\n\nRelevant examples:\n"
                for ex in examples:
                    research_info += f"- {ex.company}: {ex.system} - {ex.scale}\n"

        content_config = state.content_config
        content_type = content_config.content_type if content_config else "blog"
        tone = state.metadata.get("tone", "professional") if state.metadata else "professional"
        code_pref = "Include runnable code snippets where helpful." if content_config.include_code else "Skip code snippets."
        diagram_pref = (
            "Reference diagram placeholders using the format ![Description](images/diagram_X.png)."
            if content_config.include_diagrams
            else "Do not reference diagrams."
        )
        target_words = section_outline.word_count or content_config.target_length // max(1, len(state.outline.sections)) if state.outline else 600

        prompt = f"""You are a Content Writer Agent crafting a {content_type} section.

Topic: "{state.topic}"
Section: "{section_outline.title}"
Tone: {tone}
Desired length: ~{target_words} words (stay within +/- 15%).

Section Outline:
- Objectives: {', '.join(section_outline.objectives)}
- Key Points: {', '.join(section_outline.key_points)}

Continuity:
- Maintain narrative continuity with previous sections.
- Avoid repeating headings verbatim; introduce transitions that reference earlier context.

{research_info}

Style Guidelines:
1. Adapt your voice to the content type ({content_type}). For news, prioritize facts; for tutorials, use stepwise guidance; for reviews, compare pros/cons.
2. Use Markdown headings/subheadings. Avoid duplicate top-level headings.
3. Provide concrete evidence: metrics, dates, sources, or quotes when possible.
4. {code_pref}
5. {diagram_pref}
6. Anchor the writing in real-world scenarios relevant to the section objectives.

Write comprehensive, production-quality Markdown for this section."""
        
        return prompt
