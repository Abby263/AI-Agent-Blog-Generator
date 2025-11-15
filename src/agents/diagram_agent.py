"""
Diagram Agent

Generates Mermaid diagrams and converts them to PNG images.
"""

from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent
from src.schemas.state import BlogState, Diagram
from src.tools.diagram_generator import DiagramGenerator


class DiagramAgent(BaseAgent):
    """Diagram agent for creating visual representations."""
    
    def __init__(self):
        """Initialize diagram agent."""
        super().__init__("diagram")
        self.diagram_generator = DiagramGenerator()
    
    def execute(self, state: BlogState) -> Dict[str, Any]:
        """
        Execute diagram generation for all required diagrams.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with generated diagrams
        """
        self.logger.info("Generating diagrams")
        
        # Check if Mermaid CLI is available
        if not self.diagram_generator.is_mermaid_cli_available():
            self.logger.warning(
                "Mermaid CLI not available. Install with: npm install -g @mermaid-js/mermaid-cli"
            )
            return {
                "status": "referencing",
                "current_agent": "reference",
                "messages": ["Skipped diagram generation (Mermaid CLI not available)"]
            }
        
        # Collect all diagram requirements
        diagram_requirements = self._collect_diagram_requirements(state)
        
        if not diagram_requirements:
            self.logger.info("No diagrams needed")
            return {
                "status": "referencing",
                "current_agent": "reference",
                "messages": ["No diagrams needed"]
            }
        
        # Generate diagrams
        diagrams = []
        for i, req in enumerate(diagram_requirements):
            self.logger.info(
                f"Generating diagram {i+1}/{len(diagram_requirements)}: {req['id']}"
            )
            
            diagram = self._generate_diagram(state, req)
            if diagram:
                diagrams.append(diagram)
        
        self.logger.info(f"Generated {len(diagrams)} diagrams")
        
        return {
            "diagrams": diagrams,
            "status": "referencing",
            "current_agent": "reference",
            "messages": [f"Generated {len(diagrams)} diagrams"]
        }
    
    def _collect_diagram_requirements(self, state: BlogState) -> List[Dict[str, Any]]:
        """Collect all diagram requirements from sections."""
        requirements = []
        
        for section in state.sections:
            for diagram_id in section.diagram_placeholders:
                requirements.append({
                    "id": diagram_id,
                    "section": section.title,
                    "type": self._infer_diagram_type(diagram_id),
                    "description": f"Diagram for {diagram_id}"
                })
        
        return requirements
    
    def _infer_diagram_type(self, diagram_id: str) -> str:
        """Infer diagram type from ID."""
        diagram_id_lower = diagram_id.lower()
        
        if "architecture" in diagram_id_lower or "system" in diagram_id_lower:
            return "architecture"
        elif "flow" in diagram_id_lower or "process" in diagram_id_lower:
            return "flowchart"
        elif "pipeline" in diagram_id_lower or "data" in diagram_id_lower:
            return "graph"
        else:
            return "architecture"
    
    def _generate_diagram(
        self,
        state: BlogState,
        requirement: Dict[str, Any]
    ) -> Diagram:
        """Generate a single diagram."""
        # Build Mermaid generation prompt
        prompt = self._build_diagram_prompt(state, requirement)
        
        # Call LLM to generate Mermaid code
        response = self._call_llm(prompt)
        
        # Extract Mermaid code
        mermaid_code = self._extract_mermaid(response)
        
        # Validate Mermaid syntax
        if not self.diagram_generator.validate_mermaid_syntax(mermaid_code):
            self.logger.warning(f"Invalid Mermaid syntax for {requirement['id']}")
        
        # Convert to PNG
        image_path = self.diagram_generator.generate_diagram(
            mermaid_code=mermaid_code,
            diagram_id=requirement["id"],
            description=requirement["description"]
        )
        
        return Diagram(
            id=requirement["id"],
            type=requirement["type"],
            mermaid_code=mermaid_code,
            image_path=image_path,
            description=requirement["description"]
        )
    
    def _build_diagram_prompt(
        self,
        state: BlogState,
        requirement: Dict[str, Any]
    ) -> str:
        """Build diagram generation prompt."""
        prompt = f"""You are a Diagram Agent creating clear, informative diagrams for ML systems.

Create a {requirement['type']} diagram for: {requirement['description']}
Topic Context: {state.topic}
Section: {requirement['section']}

Guidelines:
1. Clear labels on all components
2. Logical flow (left-to-right or top-to-bottom)
3. Show all major components
4. Include data flow arrows
5. Use industry-standard component names

Output only the Mermaid code (no explanations):

```mermaid
[your mermaid code here]
```

Example architecture diagram:
```mermaid
graph LR
    A[User Request] -->|HTTP| B[API Gateway]
    B -->|route| C[Feature Service]
    C -->|features| D[Model Service]
    D -->|prediction| E[Response]
```

Generate the Mermaid diagram code."""
        
        return prompt
    
    def _extract_mermaid(self, response: str) -> str:
        """Extract Mermaid code from LLM response."""
        # Look for mermaid code blocks
        if "```mermaid" in response:
            start = response.find("```mermaid") + 10
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

