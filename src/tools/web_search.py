"""
Web search tool using Tavily API.

Provides web search capabilities for the research agent.
"""

from typing import List, Dict, Any, Optional
import os
from tavily import TavilyClient
from src.utils.logger import get_logger
from src.utils.config_loader import get_config


class TavilySearchTool:
    """Web search tool using Tavily API."""
    
    def __init__(self):
        """Initialize Tavily search tool."""
        self.logger = get_logger()
        self.config = get_config()
        
        # Get API key
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not found in environment")
        
        self.client = TavilyClient(api_key=api_key)
        
        # Get search configuration
        agent_config = self.config.get_agent_config("research")
        search_config = agent_config.get("web_search", {})
        self.max_results = search_config.get("max_results", 10)
        self.search_depth = search_config.get("search_depth", "advanced")
    
    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        search_depth: Optional[str] = None,
        include_domains: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform web search.
        
        Args:
            query: Search query
            max_results: Maximum number of results (None to use config)
            search_depth: Search depth ('basic' or 'advanced')
            include_domains: List of domains to focus on
            
        Returns:
            List of search results with title, url, content
        """
        self.logger.info(f"Searching for: {query}")
        
        try:
            # Prepare search parameters
            search_params = {
                "query": query,
                "max_results": max_results or self.max_results,
                "search_depth": search_depth or self.search_depth,
            }
            
            if include_domains:
                search_params["include_domains"] = include_domains
            
            # Perform search
            response = self.client.search(**search_params)
            
            # Extract results
            results = []
            for result in response.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0)
                })
            
            self.logger.info(f"Found {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            self.logger.error(f"Search error for query '{query}': {str(e)}")
            return []
    
    def search_engineering_blogs(self, query: str) -> List[Dict[str, Any]]:
        """
        Search specifically in engineering blogs.
        
        Args:
            query: Search query
            
        Returns:
            List of search results from engineering blogs
        """
        # Get engineering blog domains from config
        agent_config = self.config.get_agent_config("research")
        blog_urls = agent_config.get("sources", {}).get("engineering_blogs", [])
        
        # Extract domains from URLs
        domains = [url.replace("https://", "").replace("http://", "") 
                   for url in blog_urls]
        
        return self.search(
            query=query,
            include_domains=domains
        )
    
    def multi_search(self, queries: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform multiple searches.
        
        Args:
            queries: List of search queries
            
        Returns:
            Dictionary mapping queries to their results
        """
        results = {}
        for query in queries:
            results[query] = self.search(query)
        return results

