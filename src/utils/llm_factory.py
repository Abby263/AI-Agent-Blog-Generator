"""
LLM Factory for creating and managing language models.

Centralized LLM initialization following the development guidelines.
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langsmith import Client
from src.utils.config_loader import get_config
import os


class LLMFactory:
    """
    Factory class for creating and managing LLM instances.
    
    All agents should use this factory to ensure consistent LLM configuration
    and tracing setup.
    """
    
    def __init__(self, config_path: str = "config/workflow_config.yaml"):
        """
        Initialize LLM factory.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = get_config(config_path)
        self._langsmith_client: Optional[Client] = None
        self._initialize_langsmith()
    
    def _initialize_langsmith(self) -> None:
        """Initialize LangSmith client for tracing."""
        monitoring_config = self.config.get_monitoring_config()
        langsmith_config = monitoring_config.get("langsmith", {})
        
        if langsmith_config.get("enabled", False):
            api_key = self.config.get_env("LANGSMITH_API_KEY")
            if api_key:
                os.environ["LANGSMITH_TRACING_V2"] = "true"
                os.environ["LANGSMITH_PROJECT"] = langsmith_config.get(
                    "project_name", "ml-blog-generation"
                )
                self._langsmith_client = Client()
                print("✓ LangSmith tracing enabled")
            else:
                print("Warning: LANGSMITH_API_KEY not found")
    
    def create_llm(
        self,
        llm_type: str = "primary",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> ChatOpenAI:
        """
        Create an LLM instance.
        
        Args:
            llm_type: Type of LLM to create ('primary' or 'secondary')
            temperature: Override temperature setting
            max_tokens: Override max tokens setting
            **kwargs: Additional LLM parameters
            
        Returns:
            ChatOpenAI instance configured for use
        """
        llm_config = self.config.get_llm_config(llm_type)
        
        # Get API key from environment
        api_key = self.config.get_env("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        # Build LLM parameters
        llm_params = {
            "model": llm_config.get("model", "gpt-4"),
            "temperature": temperature or llm_config.get("temperature", 0.7),
            "max_tokens": max_tokens or llm_config.get("max_tokens", 4000),
            "openai_api_key": api_key,
            **kwargs
        }
        
        return ChatOpenAI(**llm_params)
    
    def create_agent_llm(
        self,
        agent_name: str,
        **kwargs: Any
    ) -> ChatOpenAI:
        """
        Create LLM for a specific agent.
        
        Args:
            agent_name: Name of the agent (e.g., 'research', 'content_writer')
            **kwargs: Additional LLM parameters to override
            
        Returns:
            ChatOpenAI instance configured for the agent
        """
        agent_config = self.config.get_agent_config(agent_name)
        
        # Determine which LLM type to use
        llm_type = agent_config.get("llm", "primary")
        
        # Get agent-specific overrides
        temperature = agent_config.get("temperature")
        max_tokens = agent_config.get("max_tokens")
        
        return self.create_llm(
            llm_type=llm_type,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    @property
    def langsmith_client(self) -> Optional[Client]:
        """Get LangSmith client."""
        return self._langsmith_client


# Global LLM factory instance
_llm_factory: Optional[LLMFactory] = None


def get_llm_factory(config_path: str = "config/workflow_config.yaml") -> LLMFactory:
    """
    Get or create global LLM factory instance.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        LLMFactory instance
    """
    global _llm_factory
    if _llm_factory is None:
        _llm_factory = LLMFactory(config_path)
    return _llm_factory

