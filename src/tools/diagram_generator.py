"""
Diagram generation tool using Mermaid.

Converts Mermaid diagram code to PNG images.
"""

import subprocess
import hashlib
from pathlib import Path
from typing import Optional
from src.utils.logger import get_logger
from src.utils.config_loader import get_config


class DiagramGenerator:
    """Generate diagrams from Mermaid code."""
    
    def __init__(self):
        """Initialize diagram generator."""
        self.logger = get_logger()
        self.config = get_config()
        
        # Get diagram configuration
        agent_config = self.config.get_agent_config("diagram")
        mermaid_config = agent_config.get("mermaid", {})
        
        self.cli_path = mermaid_config.get("cli_path", "mmdc")
        self.width = mermaid_config.get("width", 1200)
        self.height = mermaid_config.get("height", 800)
        self.background = mermaid_config.get("background", "transparent")
        self.theme = mermaid_config.get("theme", "default")
        self.scale = mermaid_config.get("scale", 2)
        
        # Output directory
        self.output_dir = Path(agent_config.get("output_dir", "images"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_diagram(
        self,
        mermaid_code: str,
        diagram_id: str,
        description: str = ""
    ) -> Optional[str]:
        """
        Generate PNG diagram from Mermaid code.
        
        Args:
            mermaid_code: Mermaid diagram specification
            diagram_id: Unique identifier for the diagram
            description: Diagram description (for filename)
            
        Returns:
            Path to generated PNG file, or None if generation failed
        """
        try:
            # Generate unique filename using hash
            hash_suffix = hashlib.md5(mermaid_code.encode()).hexdigest()[:8]
            filename = f"diagram_{diagram_id}_{hash_suffix}.png"
            output_path = self.output_dir / filename
            
            # Save Mermaid code to temporary file
            temp_mmd = Path(f"/tmp/{filename}.mmd")
            with open(temp_mmd, 'w') as f:
                f.write(mermaid_code)
            
            self.logger.info(f"Generating diagram: {diagram_id}")
            
            # Convert to PNG using Mermaid CLI
            cmd = [
                self.cli_path,
                '-i', str(temp_mmd),
                '-o', str(output_path),
                '-w', str(self.width),
                '-H', str(self.height),
                '-b', self.background,
                '-t', self.theme,
                '-s', str(self.scale)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                self.logger.error(f"Mermaid CLI error: {result.stderr}")
                return None
            
            # Clean up temp file
            temp_mmd.unlink(missing_ok=True)
            
            if output_path.exists():
                self.logger.info(f"✓ Diagram generated: {output_path}")
                return str(output_path)
            else:
                self.logger.error(f"Diagram file not created: {output_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Diagram generation error: {str(e)}")
            return None
    
    def validate_mermaid_syntax(self, mermaid_code: str) -> bool:
        """
        Validate Mermaid syntax (basic check).
        
        Args:
            mermaid_code: Mermaid code to validate
            
        Returns:
            True if syntax appears valid
        """
        # Basic validation - check for required elements
        valid_starts = [
            "graph", "flowchart", "sequenceDiagram",
            "classDiagram", "stateDiagram", "erDiagram",
            "gantt", "pie", "gitGraph"
        ]
        
        lines = mermaid_code.strip().split('\n')
        if not lines:
            return False
        
        first_line = lines[0].strip().lower()
        return any(first_line.startswith(start.lower()) for start in valid_starts)
    
    def is_mermaid_cli_available(self) -> bool:
        """
        Check if Mermaid CLI is available.
        
        Returns:
            True if Mermaid CLI is installed and accessible
        """
        try:
            result = subprocess.run(
                [self.cli_path, '--version'],
                capture_output=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
