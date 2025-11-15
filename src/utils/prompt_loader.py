"""
Prompt loading and management utilities.

Loads prompts from markdown files dynamically.
"""

from pathlib import Path
from typing import Dict, Optional
import re


class PromptLoader:
    """Load and manage agent prompts from markdown files."""
    
    def __init__(self, prompts_file: str = "src/prompts/agent_prompts.md"):
        """
        Initialize prompt loader.
        
        Args:
            prompts_file: Path to prompts markdown file
        """
        self.prompts_file = Path(prompts_file)
        self.prompts: Dict[str, str] = {}
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Load all prompts from the markdown file."""
        if not self.prompts_file.exists():
            print(f"Warning: Prompts file not found at {self.prompts_file}")
            return
        
        with open(self.prompts_file, 'r') as f:
            content = f.read()
        
        # Parse prompts using section headers
        # Looking for patterns like "### Main Planning Prompt" followed by ```
        pattern = r'###\s+(.+?)\n\n```\n(.+?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for title, prompt_content in matches:
            # Clean up the title to create a key
            key = title.lower().replace(' ', '_').replace('prompt', '').strip('_')
            self.prompts[key] = prompt_content.strip()
    
    def get_prompt(self, prompt_name: str, **kwargs: str) -> str:
        """
        Get a prompt by name and format it with provided variables.
        
        Args:
            prompt_name: Name of the prompt
            **kwargs: Variables to format into the prompt
            
        Returns:
            Formatted prompt string
        """
        if prompt_name not in self.prompts:
            raise ValueError(f"Prompt '{prompt_name}' not found")
        
        prompt = self.prompts[prompt_name]
        
        # Format with provided variables
        try:
            return prompt.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable for prompt: {e}")
    
    def list_prompts(self) -> list:
        """List all available prompt names."""
        return list(self.prompts.keys())


# Global prompt loader instance
_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader(prompts_file: str = "src/prompts/agent_prompts.md") -> PromptLoader:
    """
    Get or create global prompt loader instance.
    
    Args:
        prompts_file: Path to prompts file
        
    Returns:
        PromptLoader instance
    """
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader(prompts_file)
    return _prompt_loader

