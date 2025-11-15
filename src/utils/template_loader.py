"""
Template loader for different content types.

Loads templates from YAML files and provides template selection logic.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from src.utils.logger import get_logger

logger = get_logger()


class TemplateLoader:
    """Load and manage content templates."""
    
    def __init__(self, templates_file: str = "src/prompts/templates.yaml"):
        """
        Initialize template loader.
        
        Args:
            templates_file: Path to templates YAML file
        """
        self.templates_file = Path(templates_file)
        self.templates: Dict[str, Any] = {}
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load all templates from YAML file."""
        if not self.templates_file.exists():
            logger.warning(f"Templates file not found: {self.templates_file}")
            return
        
        with open(self.templates_file, 'r') as f:
            self.templates = yaml.safe_load(f) or {}
        
        logger.info(f"Loaded {len([k for k in self.templates.keys() if k != 'template_selection'])} templates")
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get template by name.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Template dictionary or None if not found
        """
        return self.templates.get(template_name)
    
    def select_template(
        self,
        content_type: str,
        topic: str = "",
        user_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Select appropriate template based on content type and topic.
        
        Args:
            content_type: Type of content (blog, news, tutorial, review)
            topic: Content topic
            user_preference: User-specified template (overrides selection)
            
        Returns:
            Selected template dictionary
        """
        # User preference overrides
        if user_preference and user_preference in self.templates:
            logger.info(f"Using user-specified template: {user_preference}")
            return self.templates[user_preference]
        
        # Apply selection rules
        selection_rules = self.templates.get("template_selection", {}).get("rules", [])
        
        for rule in selection_rules:
            condition = rule.get("condition", "")
            
            # Simple rule evaluation
            if self._evaluate_condition(condition, content_type, topic):
                template_name = rule["template"]
                logger.info(f"Selected template: {template_name} (rule: {condition})")
                return self.templates.get(template_name, {})
        
        # Default template
        default_template = "ml_system_design"
        logger.info(f"Using default template: {default_template}")
        return self.templates.get(default_template, {})
    
    def _evaluate_condition(
        self,
        condition: str,
        content_type: str,
        topic: str
    ) -> bool:
        """
        Evaluate template selection condition.
        
        Args:
            condition: Condition string to evaluate
            content_type: Content type
            topic: Topic string
            
        Returns:
            True if condition matches
        """
        condition = condition.lower()
        
        # Default condition
        if condition == "default":
            return True
        
        # Content type matching
        if f"content_type == '{content_type}'" in condition:
            # Check additional conditions
            if "topic contains" in condition:
                # Extract what topic should contain
                start = condition.find("topic contains") + 14
                end = condition.find("'", start)
                required = condition[start:end].strip()
                return required.lower() in topic.lower()
            return True
        
        return False
    
    def get_template_sections(self, template_name: str) -> list:
        """
        Get sections for a template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            List of section dictionaries
        """
        template = self.get_template(template_name)
        if template:
            return template.get("sections", [])
        return []
    
    def get_target_length(self, template_name: str) -> tuple:
        """
        Get target length range for a template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Tuple of (min_length, max_length)
        """
        template = self.get_template(template_name)
        if template:
            length_range = template.get("target_length_range", [5000, 8000])
            return tuple(length_range)
        return (5000, 8000)
    
    def list_templates(self) -> list:
        """
        List all available template names.
        
        Returns:
            List of template names
        """
        return [k for k in self.templates.keys() if k != "template_selection"]


# Global template loader instance
_template_loader: Optional[TemplateLoader] = None


def get_template_loader(
    templates_file: str = "src/prompts/templates.yaml"
) -> TemplateLoader:
    """
    Get or create global template loader instance.
    
    Args:
        templates_file: Path to templates file
        
    Returns:
        TemplateLoader instance
    """
    global _template_loader
    if _template_loader is None:
        _template_loader = TemplateLoader(templates_file)
    return _template_loader

