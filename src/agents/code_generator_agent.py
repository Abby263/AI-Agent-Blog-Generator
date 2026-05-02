"""
Code Generator Agent

Generates Python code examples for the blog.
"""

from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent
from src.schemas.state import BlogState, CodeBlock
from src.tools.code_validator import CodeValidator


class CodeGeneratorAgent(BaseAgent):
    """Code generator agent for creating code examples."""
    
    def __init__(self):
        """Initialize code generator agent."""
        super().__init__("code_generator")
        self.validator = CodeValidator()
    
    def execute(self, state: BlogState) -> Dict[str, Any]:
        """
        Execute code generation for all required code examples.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with generated code blocks
        """
        self.logger.info("Generating code examples")
        
        # Collect all code requirements from sections
        code_requirements = self._collect_code_requirements(state)
        
        if not code_requirements:
            self.logger.info("No code examples needed")
            return {
                "status": "generating_diagrams",
                "current_agent": "diagram",
                "messages": ["No code examples needed"]
            }
        
        # Generate code for each requirement
        code_blocks = []
        for i, req in enumerate(code_requirements):
            self.logger.info(f"Generating code {i+1}/{len(code_requirements)}: {req['id']}")
            
            code_block = self._generate_code(state, req)
            if code_block:
                code_blocks.append(code_block)
        
        self.logger.info(f"Generated {len(code_blocks)} code examples")
        
        return {
            "code_blocks": code_blocks,
            "status": "generating_diagrams",
            "current_agent": "diagram",
            "messages": [f"Generated {len(code_blocks)} code examples"]
        }
    
    def _collect_code_requirements(self, state: BlogState) -> List[Dict[str, Any]]:
        """Collect all code requirements from sections."""
        requirements = []
        
        for section in state.sections:
            for code_id in section.code_placeholders:
                requirements.append({
                    "id": code_id,
                    "section": section.title,
                    "description": f"Code example for {code_id}"
                })
        
        return requirements
    
    def _generate_code(
        self,
        state: BlogState,
        requirement: Dict[str, Any]
    ) -> CodeBlock:
        """Generate code for a specific requirement."""
        # Build code generation prompt
        prompt = self._build_code_prompt(state, requirement)
        
        # Call LLM to generate code
        response = self._call_llm(prompt)
        
        # Extract code from response
        code = self._extract_code(response)
        
        # Validate code
        validation = self.validator.validate_syntax(code)
        
        if not validation["valid"]:
            self.logger.warning(
                f"Generated code has syntax errors: {validation['errors']}"
            )
        
        return CodeBlock(
            id=requirement["id"],
            language="python",
            code=code,
            description=requirement["description"],
            section=requirement["section"]
        )
    
    def _build_code_prompt(
        self,
        state: BlogState,
        requirement: Dict[str, Any]
    ) -> str:
        """Build code generation prompt."""
        prompt = f"""You are a Code Generator Agent creating production-quality Python implementations.

Generate code for: {requirement['description']}
Topic Context: {state.topic}
Section: {requirement['section']}

Requirements:
1. Python 3.8+
2. Follow PEP 8 style guide
3. Add type hints for parameters and return types
4. Include docstrings (Google style)
5. Add inline comments for complex logic
6. Production-ready (no placeholders)
7. Include import statements
8. Handle errors appropriately

Output only the Python code (no explanations before or after):

```python
# Your code here
```

Generate clean, well-documented, production-quality code."""
        
        return prompt
    
    def _extract_code(self, response: str) -> str:
        """Extract code from LLM response."""
        # Look for code blocks
        if "```python" in response:
            start = response.find("```python") + 9
            end = response.find("```", start)
            if end > start:
                return response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end > start:
                return response[start:end].strip()
        
        # Return entire response if no code block markers
        return response.strip()

