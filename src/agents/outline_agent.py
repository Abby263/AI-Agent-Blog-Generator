"""
Outline Agent

Creates detailed blog outline following the template structure.
"""

from typing import Dict, Any, List, Tuple
import json
from src.agents.base_agent import BaseAgent
from src.schemas.state import BlogState, BlogOutline, SectionOutline


class OutlineAgent(BaseAgent):
    """Outline agent for creating blog structure."""
    
    def __init__(self):
        """Initialize outline agent."""
        super().__init__("outline")
        self.content_structures: Dict[str, List[Tuple[str, str]]] = {
            "blog": [
                ("Introduction", "Hook readers, set context, and preview the piece"),
                ("Problem Statement", "Explain the challenge or topic focus"),
                ("Key Insights", "Share 3-4 major takeaways"),
                ("Deep Dive", "Discuss the core narrative with evidence"),
                ("Real-World Examples", "Ground the story in concrete cases"),
                ("Implementation / How-To", "Provide actionable steps or frameworks"),
                ("Impact & Metrics", "Explain success criteria and measurements"),
                ("Risks & Mitigation", "Highlight challenges and solutions"),
                ("Future Outlook", "Discuss next steps or evolving trends"),
                ("Conclusion", "Summarize and provide a strong closing"),
            ],
            "news": [
                ("Headline & Lede", "Concise summary of what happened and why it matters"),
                ("Background", "Context or history readers need"),
                ("Key Facts", "Most important details in descending order of significance"),
                ("Official Statements", "Quotes or reactions from stakeholders"),
                ("Impact", "Implications for readers, industry, or community"),
                ("What Happens Next", "Explain ongoing investigations or next steps"),
            ],
            "tutorial": [
                ("Introduction", "Define the skill or outcome readers will achieve"),
                ("Prerequisites", "Tools, knowledge, or datasets required"),
                ("Step-by-Step Guide", "Detailed instructions broken into substeps"),
                ("Validation", "How to verify the results or run tests"),
                ("Common Issues", "Troubleshooting tips"),
                ("Wrap-Up", "Recap and additional exercises"),
            ],
            "review": [
                ("Introduction", "What is being reviewed, release details"),
                ("Setup & Methodology", "How you evaluated the product/topic"),
                ("Highlights", "Strengths and standout features"),
                ("Limitations", "Weaknesses or rough edges"),
                ("Comparison", "Contrast with competitors or previous versions"),
                ("Verdict", "Final rating, who should read/buy"),
            ],
        }
    
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
            outline_data = self._extract_json_from_response(response)
            outline = self._parse_outline(outline_data)
            # Skip deduplication - _parse_outline already handles this
            outline = self._align_to_structure(outline, state)
            outline = self._normalize_word_counts(outline, state)
            
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
        
        content_type = state.content_config.content_type if state.content_config else "blog"
        
        # Use series-specific requirements if available, otherwise use default structure
        series_info = state.metadata.get("series") if state.metadata else None
        requirements = ""
        if series_info:
            series_requirements = series_info.get("requirements", "")
            if series_requirements:
                requirements = f"\nSeries Requirements: {series_requirements}\n"
        
        # Get structure guidance (this can be overridden by series requirements)
        structure_guidance = self._get_structure_guidance(content_type)
        
        prompt = f"""You are an Outline Agent creating a detailed {content_type} outline.

Topic: {state.topic}
Audience: {state.metadata.get('tone', 'professional') if state.metadata else 'general readers'}
{research_summary}
{requirements}

STRUCTURE GUIDELINES:
{structure_guidance}

IMPORTANT: The above structure is a GUIDELINE, not a rigid template. You should:
- Adapt the structure to fit the specific topic and requirements
- Add, remove, or modify sections as needed to best serve the content
- Ensure the structure logically flows and tells a complete story
- Consider what sections are truly necessary for THIS specific topic

CRITICAL REQUIREMENTS:
- Each section MUST have a UNIQUE title
- DO NOT create duplicate section titles
- DO NOT repeat the same section multiple times
- Ensure each section serves a distinct purpose in the content
- Tailor the outline to the specific topic, not a generic template

For each section, provide:
- Objectives (what to cover)
- Key points (3-5 main topics)
- Word count target
- Diagrams needed (IDs)
- Code examples needed (IDs) if relevant
- Real-world references when helpful

OUTPUT FORMAT:
Return a JSON object with this structure:
{{
    "sections": [
        {{
            "title": "Section Title",
            "objectives": ["objective 1", "objective 2"],
            "key_points": ["point 1", "point 2", "point 3"],
            "word_count": 600,
            "diagrams": ["diagram_id_1"],
            "code_examples": ["code_id_1"],
            "real_world_references": ["reference 1"]
        }}
    ],
    "total_words": 5000,
    "total_diagrams": 5,
    "total_code_examples": 10
}}

IMPORTANT:
- Return ONLY the JSON object, no additional text or explanation
- Ensure valid JSON syntax (no trailing commas, proper quotes)
- You may wrap it in ```json code blocks if you prefer"""
        
        return prompt
    
    
    def _parse_outline(self, outline_data: Dict[str, Any]) -> BlogOutline:
        """Parse outline data into BlogOutline object."""
        sections = []
        seen_titles = set()
        for section in outline_data.get("sections", []):
            parsed = SectionOutline(**section)
            normalized = parsed.title.strip().lower()
            if normalized in seen_titles:
                self.logger.warning(
                    "Duplicate section title '%s' detected. Skipping duplicate entry.",
                    parsed.title
                )
                continue
            seen_titles.add(normalized)
            sections.append(parsed)
        
        return BlogOutline(
            sections=sections,
            total_words=outline_data.get("total_words", 9000),
            total_diagrams=outline_data.get("total_diagrams", 12),
            total_code_examples=outline_data.get("total_code_examples", 20)
        )
    
    def _create_default_outline(self, state: BlogState) -> Dict[str, Any]:
        """Create default outline if LLM generation fails."""
        content_type = state.content_config.content_type if state.content_config else "blog"
        structure = self.content_structures.get(content_type, self.content_structures["blog"])
        target_total = state.content_config.target_length if state.content_config else 3000
        per_section = max(200, int(target_total / max(1, len(structure))))

        default_sections = []
        for title, description in structure:
            default_sections.append(
                SectionOutline(
                    title=title,
                    objectives=[description],
                    key_points=[
                        f"{title} insight 1",
                        f"{title} insight 2",
                        f"{title} insight 3",
                    ],
                    word_count=per_section,
                    diagrams=[],
                    code_examples=[],
                    real_world_references=[]
                )
            )
        
        outline = BlogOutline(
            sections=default_sections,
            total_words=target_total,
            total_diagrams=3,
            total_code_examples=5
        )
        
        return {
            "outline": outline,
            "status": "writing",
            "current_agent": "content_writer",
            "messages": ["Using default outline"]
        }

    def _get_structure_guidance(self, content_type: str) -> str:
        structure = self.content_structures.get(content_type, self.content_structures["blog"])
        lines = []
        for idx, (title, description) in enumerate(structure, start=1):
            lines.append(f"{idx}. {title} - {description}")
        return "\n".join(lines)

    def _deduplicate_titles(self, outline: BlogOutline) -> BlogOutline:
        """Ensure section titles are unique."""
        counts = {}
        deduped_sections = []
        for section in outline.sections:
            count = counts.get(section.title, 0)
            counts[section.title] = count + 1
            if count > 0:
                new_title = f"{section.title} (Part {count + 1})"
                section = SectionOutline(**{**section.dict(), "title": new_title})
            deduped_sections.append(section)
        outline.sections = deduped_sections
        return outline

    def _normalize_word_counts(self, outline: BlogOutline, state: BlogState) -> BlogOutline:
        target = 0
        if state.content_config and state.content_config.target_length:
            target = state.content_config.target_length
        if target <= 0:
            return outline
        counts = [section.word_count or 0 for section in outline.sections]
        if not any(counts):
            per_section = max(200, int(target / max(1, len(outline.sections))))
            for section in outline.sections:
                section.word_count = per_section
            outline.total_words = per_section * len(outline.sections)
            return outline
        current_total = sum(count if count > 0 else 0 for count in counts)
        if current_total <= 0:
            return outline
        scale = target / current_total
        adjusted_total = 0
        for section in outline.sections:
            words = section.word_count or 0
            new_words = max(150, int(words * scale))
            section.word_count = new_words
            adjusted_total += new_words
        outline.total_words = adjusted_total
        return outline

    def _align_to_structure(self, outline: BlogOutline, state: BlogState) -> BlogOutline:
        """
        Lightly validate outline structure without forcing rigid adherence.
        
        This method now serves as a light validation pass rather than forcing
        sections to match a predefined template. It simply ensures the outline
        has a reasonable structure.
        """
        # Skip alignment if we have series-specific requirements
        series_info = state.metadata.get("series") if state.metadata else None
        if series_info and series_info.get("requirements"):
            # Series has custom requirements - don't force alignment to default structure
            return outline
        
        # If outline is reasonable length, accept it as-is
        if 5 <= len(outline.sections) <= 15:
            return outline
        
        # Only intervene if outline seems problematic (too few or too many sections)
        if len(outline.sections) < 5:
            self.logger.warning("Outline has very few sections (%d), may need more content", len(outline.sections))
        elif len(outline.sections) > 15:
            self.logger.warning("Outline has many sections (%d), consider consolidating", len(outline.sections))
        
        return outline
