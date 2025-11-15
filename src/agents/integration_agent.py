"""
Integration Agent

Assembles all components into the final blog post.
"""

from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.schemas.state import BlogState


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
        
        self.logger.info(f"Blog post saved to: {output_path}")
        
        # Create metadata
        metadata = self._create_metadata(state)
        
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
                f"Total references: {len(state.references)}"
            ]
        }
    
    def _assemble_blog(self, state: BlogState) -> str:
        """Assemble all components into complete blog post."""
        parts = []
        
        # Add title
        parts.append(f"# ML System Design: {state.topic}\n")
        
        # Add metadata
        parts.append(f"**Author**: {state.metadata.get('author', 'AI Agent')}")
        parts.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d')}")
        parts.append("")
        
        # Add table of contents
        parts.append("## Table of Contents\n")
        for i, section in enumerate(state.sections, 1):
            parts.append(f"{i}. [{section.title}](#{self._slugify(section.title)})")
        parts.append("")
        
        # Add sections
        for section in state.sections:
            parts.append(f"## {section.title}\n")
            
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
                if diagram.image_path:
                    placeholder = f"[DIAGRAM:{diagram.id}]"
                    if placeholder in content:
                        content = content.replace(
                            placeholder,
                            f"\n![{diagram.description}]({diagram.image_path})\n"
                        )
            
            parts.append(content)
            parts.append("")
        
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
        output_dir = Path(output_config.get("markdown", {}).get("output_dir", "output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        filename = self._slugify(state.topic) + ".md"
        output_path = output_dir / filename
        
        # Save file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(output_path)
    
    def _create_metadata(self, state: BlogState) -> Dict[str, Any]:
        """Create metadata for the blog post."""
        return {
            "title": f"ML System Design: {state.topic}",
            "date": datetime.now().isoformat(),
            "author": state.metadata.get("author", "AI Agent"),
            "topic": state.topic,
            "word_count": sum(s.word_count for s in state.sections),
            "sections": len(state.sections),
            "code_examples": len(state.code_blocks),
            "diagrams": len(state.diagrams),
            "references": len(state.references),
            "quality_score": state.quality_report.overall_score if state.quality_report else 0.0
        }
    
    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        import re
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')

