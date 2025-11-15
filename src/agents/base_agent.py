"""
Base agent class for all specialized agents.

All agents should inherit from this base class to ensure consistent
interface and behavior.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langsmith.run_helpers import traceable
from src.schemas.state import BlogState
from src.utils.logger import get_logger
from src.utils.llm_factory import get_llm_factory
from src.utils.config_loader import get_config


class BaseAgent(ABC):
    """
    Base class for all agents in the workflow.
    
    Provides common functionality:
    - LLM initialization
    - Logging
    - Configuration access
    - LangSmith tracing
    """
    
    def __init__(self, agent_name: str):
        """
        Initialize base agent.
        
        Args:
            agent_name: Name of the agent (used for logging and config)
        """
        self.agent_name = agent_name
        self.logger = get_logger()
        self.config = get_config()
        self.llm_factory = get_llm_factory()
        
        # Initialize LLM for this agent
        self.llm = self._initialize_llm()
        
        # Get agent-specific configuration
        self.agent_config = self.config.get_agent_config(agent_name)
        
        self.logger.info(f"✓ Initialized {agent_name} agent")
    
    def _initialize_llm(self) -> ChatOpenAI:
        """
        Initialize LLM for this agent.
        
        Returns:
            ChatOpenAI instance configured for this agent
        """
        return self.llm_factory.create_agent_llm(self.agent_name)
    
    @abstractmethod
    def execute(self, state: BlogState) -> Dict[str, Any]:
        """
        Execute the agent's main logic.
        
        This method must be implemented by all subclasses.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with updates to merge into state
        """
        pass
    
    @traceable
    def invoke(self, state: BlogState) -> Dict[str, Any]:
        """
        Invoke the agent with tracing.
        
        This method wraps execute() with LangSmith tracing and error handling.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with updates to merge into state
        """
        self.logger.info(f"=== Starting {self.agent_name} agent ===")
        
        try:
            # Execute agent logic
            result = self.execute(state)
            
            # Add success message
            if "messages" not in result:
                result["messages"] = []
            result["messages"].append(
                f"✓ {self.agent_name} completed successfully"
            )
            
            self.logger.info(f"=== Completed {self.agent_name} agent ===")
            return result
            
        except Exception as e:
            self.logger.error(
                f"Error in {self.agent_name} agent: {str(e)}",
                exc_info=True
            )
            
            # Return error state
            return {
                "status": "failed",
                "messages": [f"✗ {self.agent_name} failed: {str(e)}"],
                "retry_count": state.retry_count + 1
            }
    
    def _call_llm(self, prompt: str, **kwargs: Any) -> str:
        """
        Call LLM with prompt.
        
        Args:
            prompt: Prompt string
            **kwargs: Additional parameters for LLM
            
        Returns:
            LLM response text
        """
        try:
            response = self.llm.invoke(prompt, **kwargs)
            return response.content
        except Exception as e:
            self.logger.error(f"LLM call error: {str(e)}")
            raise
    
    def _update_state(
        self,
        state: BlogState,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update state with new values.
        
        Args:
            state: Current state
            updates: Dictionary of updates
            
        Returns:
            Dictionary with all updates
        """
        # Ensure messages are added correctly
        if "messages" in updates and state.messages:
            updates["messages"] = state.messages + updates["messages"]
        
        return updates

