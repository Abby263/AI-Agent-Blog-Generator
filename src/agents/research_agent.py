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
        """Generate search queries based on topic and workflow plan."""
        topic = state.topic
        queries = [
            f"{topic} system design architecture",
            f"{topic} production metrics latency scale",
            f"{topic} ML engineering blog",
        ]
        
        # Add queries from workflow plan if available
        if state.workflow_plan:
            for priority in state.workflow_plan.research_priorities[:3]:
                queries.append(priority)
        
        # Add company-specific queries
        companies = ["Netflix", "Uber", "Google"]
        for company in companies:
            queries.append(f"{company} {topic} engineering blog")
        
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
            data = self._extract_json(response)
            
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
        
        prompt = f"""You are a Research Agent analyzing information about {state.topic}.

Based on the following search results, extract and structure the information:

{content_text}

Output a JSON object with this structure:
{{
    "real_world_examples": [
        {{
            "company": "Company Name",
            "system": "System Name",
            "scale": "Scale metrics (e.g., '200M+ users')",
            "latency": "Latency metrics (e.g., '<100ms p95')",
            "architecture": "Brief architecture description",
            "key_technologies": ["tech1", "tech2"],
            "source": "URL",
            "key_insights": ["insight1", "insight2"]
        }}
    ],
    "statistics": [
        {{"metric": "metric name", "value": "value", "source": "source"}}
    ],
    "engineering_blogs": ["url1", "url2"],
    "papers": [],
    "architecture_patterns": [
        {{
            "pattern": "Pattern Name",
            "used_by": ["Company1", "Company2"],
            "benefits": ["benefit1", "benefit2"]
        }}
    ]
}}

Extract specific, quantitative information. Include at least 2-3 real-world examples."""
        
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
    
    def _extract_json(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start >= 0 and end > start:
            json_str = response[start:end]
            return json.loads(json_str)
        else:
            raise ValueError("No JSON found in response")
    
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
