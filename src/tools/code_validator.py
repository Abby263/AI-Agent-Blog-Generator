"""
Code validation tool.

Validates Python code syntax and quality.
"""

import ast
from typing import List, Dict, Any
from src.utils.logger import get_logger


class CodeValidator:
    """Validate Python code syntax and quality."""
    
    def __init__(self):
        """Initialize code validator."""
        self.logger = get_logger()
    
    def validate_syntax(self, code: str) -> Dict[str, Any]:
        """
        Validate Python code syntax.
        
        Args:
            code: Python code to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Try to parse the code
            ast.parse(code)
            result["valid"] = True
            self.logger.debug("Code syntax validation passed")
            
        except SyntaxError as e:
            result["errors"].append({
                "type": "SyntaxError",
                "message": str(e),
                "line": e.lineno,
                "offset": e.offset
            })
            self.logger.warning(f"Code syntax error: {str(e)}")
            
        except Exception as e:
            result["errors"].append({
                "type": type(e).__name__,
                "message": str(e)
            })
            self.logger.warning(f"Code validation error: {str(e)}")
        
        return result
    
    def check_imports(self, code: str) -> List[str]:
        """
        Extract import statements from code.
        
        Args:
            code: Python code
            
        Returns:
            List of imported module names
        """
        imports = []
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except Exception as e:
            self.logger.warning(f"Error extracting imports: {str(e)}")
        
        return imports
    
    def check_functions(self, code: str) -> List[Dict[str, Any]]:
        """
        Extract function definitions from code.
        
        Args:
            code: Python code
            
        Returns:
            List of function information dictionaries
        """
        functions = []
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "has_docstring": ast.get_docstring(node) is not None,
                        "line": node.lineno
                    }
                    functions.append(func_info)
        except Exception as e:
            self.logger.warning(f"Error extracting functions: {str(e)}")
        
        return functions
    
    def check_code_quality(self, code: str) -> Dict[str, Any]:
        """
        Perform comprehensive code quality checks.
        
        Args:
            code: Python code to check
            
        Returns:
            Dictionary with quality metrics and issues
        """
        quality = {
            "syntax_valid": False,
            "has_imports": False,
            "has_functions": False,
            "functions_documented": 0,
            "total_functions": 0,
            "issues": []
        }
        
        # Check syntax
        syntax_result = self.validate_syntax(code)
        quality["syntax_valid"] = syntax_result["valid"]
        quality["issues"].extend(syntax_result["errors"])
        
        if not syntax_result["valid"]:
            return quality
        
        # Check imports
        imports = self.check_imports(code)
        quality["has_imports"] = len(imports) > 0
        
        # Check functions
        functions = self.check_functions(code)
        quality["has_functions"] = len(functions) > 0
        quality["total_functions"] = len(functions)
        quality["functions_documented"] = sum(
            1 for f in functions if f["has_docstring"]
        )
        
        # Check for common issues
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 120:
                quality["issues"].append({
                    "type": "StyleWarning",
                    "message": f"Line too long ({len(line)} > 120 chars)",
                    "line": i,
                    "severity": "minor"
                })
        
        # Check documentation coverage
        if quality["total_functions"] > 0:
            doc_coverage = quality["functions_documented"] / quality["total_functions"]
            if doc_coverage < 0.8:
                quality["issues"].append({
                    "type": "DocumentationWarning",
                    "message": f"Low documentation coverage ({doc_coverage:.0%})",
                    "severity": "minor"
                })
        
        return quality
    
    def format_validation_report(self, validation_result: Dict[str, Any]) -> str:
        """
        Format validation results as a readable report.
        
        Args:
            validation_result: Validation result dictionary
            
        Returns:
            Formatted report string
        """
        report = ["Code Quality Report", "=" * 50, ""]
        
        if validation_result["syntax_valid"]:
            report.append("✓ Syntax: Valid")
        else:
            report.append("✗ Syntax: Invalid")
        
        report.append(f"✓ Imports: {validation_result.get('has_imports', False)}")
        report.append(f"✓ Functions: {validation_result.get('total_functions', 0)}")
        report.append(
            f"✓ Documented: {validation_result.get('functions_documented', 0)}/"
            f"{validation_result.get('total_functions', 0)}"
        )
        
        if validation_result.get("issues"):
            report.append("\nIssues:")
            for issue in validation_result["issues"]:
                severity = issue.get("severity", "error")
                line = issue.get("line", "?")
                message = issue.get("message", "")
                report.append(f"  [{severity.upper()}] Line {line}: {message}")
        else:
            report.append("\n✓ No issues found")
        
        return "\n".join(report)

