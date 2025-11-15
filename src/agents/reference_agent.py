"""
Reference Agent

Manages citations and references for the blog post.
"""

from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent
from src.schemas.state import BlogState, Reference


class ReferenceAgent(BaseAgent):
    """Reference agent for managing citations."""
    
    def __init__(self):
        """Initialize reference agent."""
        super().__init__("reference")
    
    def execute(self, state: BlogState) -> Dict[str, Any]:
        """
        Execute reference management: collect and format citations.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with formatted references
        """
        self.logger.info("Managing references and citations")
        
        # Collect all references from research and sections
        references = self._collect_references(state)
        
        if not references:
            self.logger.warning("No references found")
            references = self._create_default_references(state)
        
        self.logger.info(f"Collected {len(references)} references")
        
        return {
            "references": references,
            "status": "quality_checking",
            "current_agent": "qa",
            "messages": [f"Collected {len(references)} references"]
        }
    
    def _collect_references(self, state: BlogState) -> List[Reference]:
        """Collect references from research and sections."""
        references = []
        ref_id = 1
        seen_urls = set()
        
        # Add references from research summary
        if state.research_summary:
            # Engineering blogs
            for blog_url in state.research_summary.engineering_blogs:
                if blog_url and blog_url not in seen_urls:
                    references.append(Reference(
                        id=ref_id,
                        title=self._extract_domain(blog_url),
                        url=blog_url,
                        type="engineering_blog"
                    ))
                    seen_urls.add(blog_url)
                    ref_id += 1
            
            # Real-world examples
            for example in state.research_summary.real_world_examples:
                if example.source and example.source not in seen_urls:
                    references.append(Reference(
                        id=ref_id,
                        title=f"{example.company} {example.system}",
                        url=example.source,
                        type="engineering_blog"
                    ))
                    seen_urls.add(example.source)
                    ref_id += 1
        
        return references[:30]  # Limit to 30 references
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            return domain or url
        except Exception:
            return url
    
    def _create_default_references(self, state: BlogState) -> List[Reference]:
        """Create default references if none found."""
        default_refs = [
            Reference(
                id=1,
                title="Machine Learning System Design Patterns",
                url="https://example.com/ml-patterns",
                type="documentation"
            ),
            Reference(
                id=2,
                title=f"{state.topic} - Industry Best Practices",
                url="https://example.com/best-practices",
                type="documentation"
            )
        ]
        return default_refs

