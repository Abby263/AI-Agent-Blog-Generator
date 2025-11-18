"""
Research Agent

Performs web search, gathers real-world examples, and synthesizes research findings.
"""

from typing import Dict, Any, List
import json
from src.agents.base_agent import BaseAgent
from src.schemas.state import BlogState, ResearchSummary, RealWorldExample, Statistic, ArchitecturePattern
from src.tools.web_search import TavilySearchTool


class ResearchAgent(BaseAgent):
    """Research agent for gathering information."""
    
    # Hard limits to keep prompts within model context bounds
    MAX_RESULTS_PER_QUERY = 3
    MAX_CONTENT_PER_RESULT = 600  # characters
    MAX_TOTAL_CONTENT = 6000      # characters
    
    def __init__(self):
        """Initialize research agent."""
        super().__init__("research")
        self.search_tool = TavilySearchTool()
        agent_config = self.config.get_agent_config("research")
        max_queries_cfg = agent_config.get("web_search", {}).get("max_queries", 8)
        try:
            self.max_queries = max(1, int(max_queries_cfg))
        except (TypeError, ValueError):
            self.max_queries = 8
    
    def execute(self, state: BlogState) -> Dict[str, Any]:
        """
        Execute research: web search and information gathering.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with research summary
        """
        self.logger.info(f"Researching topic: {state.topic}")
        
        # Generate search queries based on workflow plan
        search_queries = self._generate_search_queries(state)
        
        # Perform web searches
        search_results = {}
        for query in search_queries:
            results = self.search_tool.search(query)
            search_results[query] = results
        
        # Synthesize research findings
        research_summary = self._synthesize_research(state, search_results)
        
        self.logger.info(
            f"Research completed: {len(research_summary.real_world_examples)} examples, "
            f"{len(research_summary.engineering_blogs)} blogs"
        )
        
        return {
            "research_summary": research_summary,
            "status": "outlining",
            "current_agent": "outline",
            "messages": [
                f"Research completed with {len(research_summary.real_world_examples)} real-world examples"
            ]
        }
    
    def _generate_search_queries(self, state: BlogState) -> List[str]:
        """Generate search queries based on topic, content type, and workflow plan."""
        topic = state.topic
        content_type = state.content_config.content_type if state.content_config else "blog"
        
        # Generate context-appropriate queries based on content type
        queries = []
        
        # Always start with the base topic
        queries.append(topic)
        
        # Add queries from workflow plan if available (highest priority)
        if state.workflow_plan and state.workflow_plan.research_priorities:
            for priority in state.workflow_plan.research_priorities[:3]:
                queries.append(priority)
        
        # Add content-type specific queries if we don't have workflow priorities
        else:
            # Detect if this is technical/ML content or general content
            topic_lower = topic.lower()
            is_technical = any(keyword in topic_lower for keyword in [
                'system', 'ml', 'ai', 'machine learning', 'design', 'architecture',
                'engineering', 'data', 'algorithm', 'model', 'api', 'infrastructure'
            ])
            
            if is_technical:
                # Technical content queries
                queries.extend([
                    f"{topic} implementation architecture",
                    f"{topic} real-world examples case studies",
                    f"{topic} best practices",
                ])
            else:
                # General content queries (news, sports, reviews, etc.)
                queries.extend([
                    f"{topic} analysis insights",
                    f"{topic} statistics data",
                    f"{topic} expert opinion",
                ])
        
        # Series-specific context
        series_info = state.metadata.get("series") if state.metadata else None
        if series_info and series_info.get("requirements"):
            requirements = series_info.get("requirements", "")
            if requirements:
                queries.append(f"{topic} {requirements[:50]}")  # First 50 chars
        
        max_queries = max(1, int(self.max_queries))
        queries = queries[:max_queries]
        self.logger.info(f"Using {len(queries)} search queries (limit={max_queries})")
        return queries
    
    def _synthesize_research(
        self,
        state: BlogState,
        search_results: Dict[str, List[Dict[str, Any]]]
    ) -> ResearchSummary:
        """Synthesize search results into structured research summary."""
        # Build synthesis prompt
        prompt = self._build_synthesis_prompt(state, search_results)
        
        # Call LLM to synthesize
        response = self._call_llm(prompt)
        
        # Parse response
        try:
            data = self._extract_json_from_response(response)
            
            # Convert to ResearchSummary
            research_summary = ResearchSummary(
                real_world_examples=[
                    RealWorldExample(**example)
                    for example in data.get("real_world_examples", [])
                ],
                statistics=[
                    Statistic(**stat)
                    for stat in data.get("statistics", [])
                ],
                engineering_blogs=data.get("engineering_blogs", []),
                papers=data.get("papers", []),
                architecture_patterns=[
                    ArchitecturePattern(**pattern)
                    for pattern in data.get("architecture_patterns", [])
                ]
            )
            
            return research_summary
            
        except Exception as e:
            self.logger.error(f"Error synthesizing research: {str(e)}")
            return self._create_fallback_research(state, search_results)
    
    def _build_synthesis_prompt(
        self,
        state: BlogState,
        search_results: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """Build prompt for research synthesis."""
        content_text = self._build_search_context(search_results)
        content_type = state.content_config.content_type if state.content_config else "blog"
        
        # Detect if this is technical content
        topic_lower = state.topic.lower()
        is_technical = any(keyword in topic_lower for keyword in [
            'system', 'ml', 'ai', 'machine learning', 'design', 'architecture',
            'engineering', 'data', 'algorithm', 'model', 'api', 'infrastructure'
        ])
        
        # Adjust schema based on content type
        if is_technical:
            example_schema = """
        {{
            "company": "Company Name or Organization",
            "system": "System/Product Name",
            "scale": "Scale metrics (e.g., '200M+ users', '1B+ requests/day')",
            "latency": "Performance metrics (e.g., '<100ms p95')",
            "architecture": "Brief architecture description",
            "key_technologies": ["tech1", "tech2"],
            "source": "URL",
            "key_insights": ["insight1", "insight2"]
        }}"""
        else:
            example_schema = """
        {{
            "company": "Organization, Team, or Person",
            "system": "Event, Product, or Subject being described",
            "scale": "Relevant metrics or scope (e.g., 'World Cup 2023', '50K+ attendees')",
            "latency": "Time-based metrics if relevant (e.g., 'Match duration: 8 hours')",
            "architecture": "Structure or approach description",
            "key_technologies": ["relevant tools", "methods", "or approaches used"],
            "source": "URL",
            "key_insights": ["key finding 1", "key finding 2"]
        }}"""
        
        prompt = f"""You are a Research Agent analyzing information about: {state.topic}

Content Type: {content_type}

Based on the following search results, extract and structure the relevant information:

{content_text}

Output a JSON object with this structure:
{{
    "real_world_examples": [{example_schema}
    ],
    "statistics": [
        {{"metric": "metric name", "value": "value", "source": "source"}}
    ],
    "engineering_blogs": ["url1", "url2"],
    "papers": [],
    "architecture_patterns": [
        {{
            "pattern": "Pattern/Approach Name",
            "used_by": ["Entity1", "Entity2"],
            "benefits": ["benefit1", "benefit2"]
        }}
    ]
}}

IMPORTANT:
- Adapt the fields to the content type (technical vs general)
- Extract specific, quantitative information where available
- Include at least 2-3 relevant examples from the search results
- If technical terms don't apply, interpret them flexibly (e.g., "system" = subject, "scale" = scope)
- Leave fields empty or use N/A if information is not available

OUTPUT FORMAT:
- Return ONLY the JSON object, no additional text or explanation
- Ensure valid JSON syntax (no trailing commas, proper quotes, etc.)
- You may wrap it in ```json code blocks if you prefer"""
        
        return prompt

    def _build_search_context(
        self,
        search_results: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """Prepare truncated search context to avoid context-length errors."""
        blocks: List[str] = []
        total_chars = 0
        
        for query, results in search_results.items():
            for result in results[: self.MAX_RESULTS_PER_QUERY]:
                content = (result.get("content") or "").strip()
                if len(content) > self.MAX_CONTENT_PER_RESULT:
                    content = content[: self.MAX_CONTENT_PER_RESULT] + "..."
                block = (
                    f"Query: {query}\n"
                    f"Source: {result.get('title', 'Unknown')}\n"
                    f"URL: {result.get('url', '')}\n"
                    f"Summary: {content}\n"
                )
                block_len = len(block)
                if total_chars + block_len > self.MAX_TOTAL_CONTENT:
                    break
                blocks.append(block)
                total_chars += block_len
            else:
                continue
            break
        
        if not blocks:
            return "No search context available."
        
        return "\n---\n".join(blocks)
    
    
    def _create_fallback_research(
        self,
        state: BlogState,
        search_results: Dict[str, List[Dict[str, Any]]]
    ) -> ResearchSummary:
        """Create fallback research summary from raw search results."""
        # Extract basic information from search results
        engineering_blogs = []
        for results in search_results.values():
            for result in results[:2]:
                if result['url'] not in engineering_blogs:
                    engineering_blogs.append(result['url'])
        
        # Create basic research summary
        return ResearchSummary(
            real_world_examples=[],
            statistics=[],
            engineering_blogs=engineering_blogs[:10],
            papers=[],
            architecture_patterns=[]
        )
