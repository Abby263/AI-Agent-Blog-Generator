"""
Integration Agent

Assembles all components into the final blog post.
"""

from typing import Dict, Any, Set
from pathlib import Path
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.schemas.state import BlogState, Diagram
from src.tools.mermaid_renderer import render_mermaid_blocks_in_file


class IntegrationAgent(BaseAgent):
    """Integration agent for final blog assembly."""
    
    def __init__(self):
        """Initialize integration agent."""
        super().__init__("integration")
    
    def execute(self, state: BlogState) -> Dict[str, Any]:
        """
        Execute final integration: assemble all parts into complete blog.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with final content and completion status
        """
        self.logger.info("Assembling final blog post")
        
        # Build complete markdown content
        final_content = self._assemble_blog(state)
        
        # Save to file
        output_path = self._save_blog(state, final_content)
        self._render_mermaid_diagrams(output_path)
        
        self.logger.info(f"Blog post saved to: {output_path}")
        
        # Create metadata
        metadata = self._create_metadata(state, output_path)
        
        return {
            "final_content": final_content,
            "metadata": metadata,
            "status": "completed",
            "current_agent": "integration",
            "messages": [
                f"✓ Blog post completed and saved to {output_path}",
                f"Total sections: {len(state.sections)}",
                f"Total code examples: {len(state.code_blocks)}",
                f"Total diagrams: {len(state.diagrams)}",
                f"Total references: {len(state.references)}",
                "Diagrams embedded as Mermaid code blocks (run 'python -m src.utils.render_mermaid_program' to rerender PNGs)"
            ]
        }
    
    def _assemble_blog(self, state: BlogState) -> str:
        """Assemble all components into complete blog post."""
        parts = []
        used_diagrams = set()
        title_counts: Dict[str, int] = {}
        display_titles = [
            self._get_display_title(section.title, title_counts)
            for section in state.sections
        ]

        # Add title
        heading_label = self._get_content_label(state)
        parts.append(f"# {heading_label}: {state.topic}\n")
        
        # Add metadata
        parts.append(f"**Author**: {state.metadata.get('author', 'AI Agent')}")
        parts.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d')}")
        parts.append("")
        
        # Add table of contents
        parts.append("## Table of Contents\n")
        for i, display_title in enumerate(display_titles, 1):
            slug = self._slugify(display_title)
            parts.append(f"{i}. [{display_title}](#{slug})")
        parts.append("")

        # Add sections
        for section, display_title in zip(state.sections, display_titles):
            parts.append(f"## {display_title}\n")
            
            # Replace code placeholders
            content = section.content
            for code_block in state.code_blocks:
                if code_block.section == section.title:
                    placeholder = f"[CODE:{code_block.id}]"
                    if placeholder in content:
                        content = content.replace(
                            placeholder,
                            f"\n```python\n{code_block.code}\n```\n"
                        )
            
            # Replace diagram placeholders
            for diagram in state.diagrams:
                placeholder = f"[DIAGRAM:{diagram.id}]"
                if placeholder in content:
                    content = content.replace(
                        placeholder,
                        self._format_diagram(diagram, used_diagrams)
                    )

            parts.append(content)
            parts.append("")

        self._append_diagram_gallery(parts, state, used_diagrams)

        # Add references
        if state.references:
            parts.append("## References\n")
            for ref in state.references:
                parts.append(f"[{ref.id}] {ref.title} - {ref.url}")
            parts.append("")
        
        return "\n".join(parts)
    
    def _save_blog(self, state: BlogState, content: str) -> str:
        """Save blog post to file."""
        # Get output configuration
        output_config = self.config.get_output_config()
        base_dir = Path(output_config.get("markdown", {}).get("output_dir", "output"))
        series_info = state.metadata.get("series") if state.metadata else None
        if series_info and series_info.get("series_name"):
            output_dir = base_dir / self._slugify(series_info["series_name"])
        else:
            output_dir = base_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        filename = self._slugify(state.topic) + ".md"
        output_path = output_dir / filename
        
        # Save file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(output_path)

    def _render_mermaid_diagrams(self, output_path: str) -> None:
        """Convert Mermaid code blocks to images after saving markdown."""
        try:
            rendered = render_mermaid_blocks_in_file(Path(output_path))
            if rendered:
                self.logger.info(
                    f"Rendered {rendered} Mermaid diagrams for {output_path}"
                )
        except Exception as exc:
            self.logger.warning(
                "Mermaid rendering skipped for %s: %s",
                output_path,
                exc
            )
    
    def _create_metadata(self, state: BlogState, output_path: str) -> Dict[str, Any]:
        """Create metadata for the blog post."""
        metadata = {
            "title": f"ML System Design: {state.topic}",
            "date": datetime.now().isoformat(),
            "author": state.metadata.get("author", "AI Agent"),
            "topic": state.topic,
            "word_count": sum(s.word_count for s in state.sections),
            "sections": len(state.sections),
            "code_examples": len(state.code_blocks),
            "diagrams": len(state.diagrams),
            "references": len(state.references),
            "quality_score": state.quality_report.overall_score if state.quality_report else 0.0,
            "output_path": output_path
        }
        if state.metadata:
            metadata["series"] = state.metadata.get("series")
        return metadata
    
    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        import re
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')

    def _format_diagram(self, diagram: Diagram, used_diagrams: Set[str] | None = None) -> str:
        """Return Markdown snippet for a diagram placeholder."""
        if used_diagrams is not None:
            used_diagrams.add(diagram.id)
        description = diagram.description or f"Diagram {diagram.id}"
        
        if diagram.image_path:
            return f"\n![{description}]({diagram.image_path})\n"
        
        if diagram.mermaid_code:
            return (
                f"\n<!-- Diagram {diagram.id}: {description} -->\n"
                f"```mermaid\n{diagram.mermaid_code}\n```\n"
            )
        
        return f"\n*{description}*\n"

    def _append_diagram_gallery(
        self,
        parts: list,
        state: BlogState,
        used_diagrams: Set[str]
    ) -> None:
        """Append diagrams that were not referenced inline."""
        unused = [d for d in state.diagrams if d.id not in used_diagrams]
        if not unused:
            return
        parts.append("## Diagram Gallery\n")
        for diagram in unused:
            parts.append(self._format_diagram(diagram))
        parts.append("")

    def _get_display_title(self, title: str, counts: Dict[str, int]) -> str:
        """Create a display-safe title that avoids duplicates."""
        count = counts.get(title, 0)
        counts[title] = count + 1
        if count == 0:
            return title
        return f"{title} (Part {count + 1})"

    def _get_content_label(self, state: BlogState) -> str:
        """Create label based on content type."""
        content_type = state.content_config.content_type if state.content_config else "Content"
        mapping = {
            "blog": "Editorial",
            "news": "News Article",
            "tutorial": "Tutorial",
            "review": "Review",
        }
        return mapping.get(content_type, content_type.capitalize())
