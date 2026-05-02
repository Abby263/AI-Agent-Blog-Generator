"""
Configuration loader utility.

Loads configuration from YAML files and environment variables.
"""

import os
import yaml
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv


class ConfigLoader:
    """Load and manage configuration from various sources."""
    
    def __init__(self, config_path: str = "config/workflow_config.yaml"):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load_env()
        self._load_yaml()
    
    def _load_env(self) -> None:
        """Load environment variables from .env file."""
        load_dotenv()
    
    def _load_yaml(self) -> None:
        """Load configuration from YAML file."""
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        else:
            print(f"Warning: Config file not found at {self.config_path}")
            self.config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'llm.primary.model')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_env(self, key: str, default: Any = None) -> Any:
        """
        Get environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)
    
    def get_llm_config(self, llm_type: str = "primary") -> Dict[str, Any]:
        """
        Get LLM configuration.
        
        Args:
            llm_type: Type of LLM (primary or secondary)
            
        Returns:
            LLM configuration dictionary
        """
        return self.get(f"llm.{llm_type}", {})
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get agent configuration.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent configuration dictionary
        """
        return self.get(f"agents.{agent_name}", {})
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """Get workflow configuration."""
        return self.get("workflow", {})
    
    def get_template_config(self) -> Dict[str, Any]:
        """Get template configuration."""
        return self.get("template", {})
    
    def get_quality_config(self) -> Dict[str, Any]:
        """Get quality standards configuration."""
        return self.get("quality", {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration."""
        return self.get("output", {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return self.get("monitoring", {})


# Global configuration instance
_config = None


def get_config(config_path: str = "config/workflow_config.yaml") -> ConfigLoader:
    """
    Get or create global configuration instance.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        ConfigLoader instance
    """
    global _config
    if _config is None:
        _config = ConfigLoader(config_path)
    return _config

