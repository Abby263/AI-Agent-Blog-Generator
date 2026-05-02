"""
YAML-based prompt loader.

Loads prompts from YAML files for better organization and maintainability.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from src.utils.logger import get_logger

logger = get_logger()


class YAMLPromptLoader:
    """Load and manage prompts from YAML files."""
    
    def __init__(self, prompts_dir: str = "src/prompts"):
        """
        Initialize YAML prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt YAML files
        """
        self.prompts_dir = Path(prompts_dir)
        self.prompts: Dict[str, Dict[str, Any]] = {}
        self._load_all_prompts()
    
    def _load_all_prompts(self) -> None:
        """Load all YAML prompt files from the prompts directory."""
        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory not found: {self.prompts_dir}")
            return
        
        # Load each YAML file
        for yaml_file in self.prompts_dir.glob("*.yaml"):
            if yaml_file.stem not in ["templates", "workflow_config"]:
                agent_name = yaml_file.stem
                with open(yaml_file, 'r') as f:
                    self.prompts[agent_name] = yaml.safe_load(f) or {}
                logger.debug(f"Loaded prompts for: {agent_name}")
        
        logger.info(f"Loaded prompts for {len(self.prompts)} agents")
    
    def get_prompt(
        self,
        agent_name: str,
        prompt_type: str,
        **kwargs: Any
    ) -> str:
        """
        Get a prompt for an agent and format it with variables.
        
        Args:
            agent_name: Name of the agent (e.g., 'supervisor', 'research')
            prompt_type: Type of prompt (e.g., 'planning', 'synthesis')
            **kwargs: Variables to format into the prompt
            
        Returns:
            Formatted prompt string
        """
        if agent_name not in self.prompts:
            raise ValueError(f"No prompts found for agent: {agent_name}")
        
        agent_prompts = self.prompts[agent_name]
        
        if prompt_type not in agent_prompts:
            raise ValueError(
                f"Prompt type '{prompt_type}' not found for agent '{agent_name}'"
            )
        
        prompt_config = agent_prompts[prompt_type]
        
        # Build full prompt from system + user template
        system_prompt = prompt_config.get("system", "")
        user_template = prompt_config.get("user_template", "")
        
        # Format user template with provided variables
        try:
            user_prompt = user_template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing variable in prompt: {e}")
            # Use template as-is if variable missing
            user_prompt = user_template
        
        # Combine system and user prompts
        if system_prompt and user_prompt:
            return f"{system_prompt}\n\n{user_prompt}"
        elif user_prompt:
            return user_prompt
        else:
            return system_prompt
    
    def get_system_prompt(self, agent_name: str, prompt_type: str) -> str:
        """
        Get system prompt only.
        
        Args:
            agent_name: Name of the agent
            prompt_type: Type of prompt
            
        Returns:
            System prompt string
        """
        if agent_name in self.prompts and prompt_type in self.prompts[agent_name]:
            return self.prompts[agent_name][prompt_type].get("system", "")
        return ""
    
    def get_examples(self, agent_name: str, prompt_type: str) -> list:
        """
        Get example inputs/outputs for a prompt.
        
        Args:
            agent_name: Name of the agent
            prompt_type: Type of prompt
            
        Returns:
            List of example dictionaries
        """
        if agent_name in self.prompts and prompt_type in self.prompts[agent_name]:
            return self.prompts[agent_name][prompt_type].get("examples", [])
        return []
    
    def list_agents(self) -> list:
        """
        List all agents with loaded prompts.
        
        Returns:
            List of agent names
        """
        return list(self.prompts.keys())
    
    def list_prompt_types(self, agent_name: str) -> list:
        """
        List all prompt types for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            List of prompt type names
        """
        if agent_name in self.prompts:
            return list(self.prompts[agent_name].keys())
        return []


# Global YAML prompt loader instance
_yaml_prompt_loader: Optional[YAMLPromptLoader] = None


def get_yaml_prompt_loader(prompts_dir: str = "src/prompts") -> YAMLPromptLoader:
    """
    Get or create global YAML prompt loader instance.
    
    Args:
        prompts_dir: Directory containing prompt files
        
    Returns:
        YAMLPromptLoader instance
    """
    global _yaml_prompt_loader
    if _yaml_prompt_loader is None:
        _yaml_prompt_loader = YAMLPromptLoader(prompts_dir)
    return _yaml_prompt_loader

