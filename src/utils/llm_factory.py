"""
LLM Factory for creating and managing language models.

Centralized LLM initialization following the development guidelines.
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langsmith import Client
from src.utils.config_loader import get_config
from src.utils.logger import get_logger
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
        self.logger = get_logger()
    
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
        model_env_key = "PRIMARY_LLM_MODEL" if llm_type == "primary" else "SECONDARY_LLM_MODEL"
        model_name = (
            self.config.get_env(
                model_env_key,
                self.config.get_env(
                    "OPENAI_MODEL_NAME",
                    llm_config.get("model", "gpt-5-nano")
                )
            )
        )

        temp_override = temperature if temperature is not None else llm_config.get("temperature")
        max_tokens_override = max_tokens if max_tokens is not None else llm_config.get("max_tokens")

        if self._model_requires_default_temperature(model_name) and temp_override not in (None, 1):
            self.logger.warning(
                "Model %s requires default temperature. Overriding %s with 1.",
                model_name,
                temp_override,
            )
            temp_override = 1
        llm_params = {
            "model": model_name,
            "openai_api_key": api_key,
            **kwargs
        }
        if temp_override is not None:
            llm_params["temperature"] = temp_override
        if max_tokens_override is not None:
            llm_params["max_tokens"] = max_tokens_override

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

    def _model_requires_default_temperature(self, model_name: str) -> bool:
        """Certain frontier models (e.g., gpt-5-nano) restrict temperature overrides."""
        restricted_models = ["gpt-5-nano", "gpt-5", "o1", "omni", "gpt-4.1"]
        model_lower = model_name.lower()
        return any(tag in model_lower for tag in restricted_models)
    
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
