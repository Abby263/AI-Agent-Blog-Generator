"""
Diagram Agent

Generates Mermaid diagrams for the blog. Mermaid code is saved alongside PNG
renders (when Mermaid CLI is available) so the Integration agent can embed the
images directly and still fall back to Mermaid blocks.
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
        self._warned_mermaid_cli = False
    
    def execute(self, state: BlogState) -> Dict[str, Any]:
        """
        Execute diagram generation for all required diagrams.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with generated diagrams
        """
        self.logger.info("Generating diagrams")

        # Collect all diagram requirements
        diagram_requirements = self._collect_diagram_requirements(state)

        if not diagram_requirements and self._should_generate_defaults(state):
            self.logger.info("No diagram placeholders found. Generating defaults.")
            diagram_requirements = self._default_diagram_requirements(state)

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
        template_code = requirement.get("template_code")
        if template_code:
            mermaid_code = template_code
        else:
            # Build Mermaid generation prompt
            prompt = self._build_diagram_prompt(state, requirement)
            # Call LLM to generate Mermaid code
            response = self._call_llm(prompt)
            # Extract Mermaid code
            mermaid_code = self._extract_mermaid(response)
        
        # Validate Mermaid syntax
        if not self.diagram_generator.validate_mermaid_syntax(mermaid_code):
            self.logger.warning(f"Invalid Mermaid syntax for {requirement['id']}")
        
        image_path = None
        if self.diagram_generator.is_mermaid_cli_available():
            image_path = self.diagram_generator.generate_diagram(
                mermaid_code=mermaid_code,
                diagram_id=requirement["id"],
                description=requirement["description"],
            )
        elif not self._warned_mermaid_cli:
            self.logger.warning(
                "Mermaid CLI not available; diagrams will remain as Mermaid code blocks."
            )
            self._warned_mermaid_cli = True

        return Diagram(
            id=requirement["id"],
            type=requirement["type"],
            mermaid_code=mermaid_code,
            image_path=image_path,
            description=requirement["description"]
        )

    def _should_generate_defaults(self, state: BlogState) -> bool:
        """Return True if we should synthesize default diagrams."""
        include_flag = True
        metadata_include = state.metadata.get("include_diagrams") if state.metadata else None
        if metadata_include is not None:
            include_flag = metadata_include
        return include_flag

    def _default_diagram_requirements(self, state: BlogState) -> List[Dict[str, Any]]:
        """Generate fallback diagram requirements when none are provided."""
        topic = state.topic
        return [
            {
                "id": "core_architecture",
                "section": "System Overview",
                "type": "architecture",
                "description": f"End-to-end architecture for {topic}",
                "template_code": (
                    "graph LR\n"
                    "    User -->|Requests| API_Gateway\n"
                    "    API_Gateway-->FeatureService\n"
                    "    FeatureService-->ModelService\n"
                    "    ModelService-->ScoringStore\n"
                    "    ScoringStore-->Monitoring\n"
                    "    Monitoring-->FeedbackQueue\n"
                    "    FeedbackQueue-->FeatureService\n"
                )
            },
            {
                "id": "data_pipeline",
                "section": "Data & Features",
                "type": "flowchart",
                "description": f"Data pipeline and feature store for {topic}",
                "template_code": (
                    "flowchart TD\n"
                    "    Raw[Raw Events]-->Ingest[Streaming Ingest]\n"
                    "    Ingest-->Lake[Data Lake]\n"
                    "    Lake-->BatchFeat[Batch Feature Jobs]\n"
                    "    Lake-->StreamFeat[Streaming Feature Jobs]\n"
                    "    BatchFeat-->Store[Feature Store]\n"
                    "    StreamFeat-->Store\n"
                    "    Store-->ModelService[Model Serving]\n"
                )
            },
            {
                "id": "feedback_monitoring",
                "section": "Monitoring",
                "type": "graph",
                "description": f"Feedback loop and monitoring design for {topic}",
                "template_code": (
                    "graph LR\n"
                    "    Requests --> Predictions\n"
                    "    Predictions --> Observability\n"
                    "    Observability --> Drift[Drift Detection]\n"
                    "    Drift --> Alerts\n"
                    "    Alerts --> Retraining\n"
                    "    Retraining --> FeatureUpdates\n"
                    "    FeatureUpdates --> Predictions\n"
                )
            },
        ]
    
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
